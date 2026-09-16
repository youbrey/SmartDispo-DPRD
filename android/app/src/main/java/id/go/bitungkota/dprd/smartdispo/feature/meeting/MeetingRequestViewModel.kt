package id.go.bitungkota.dprd.smartdispo.feature.meeting

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import id.go.bitungkota.dprd.smartdispo.core.model.MeetingInvitee
import id.go.bitungkota.dprd.smartdispo.core.model.MeetingRequestCreate
import id.go.bitungkota.dprd.smartdispo.core.model.MeetingRequestUpdate
import id.go.bitungkota.dprd.smartdispo.core.model.MeetingType
import id.go.bitungkota.dprd.smartdispo.core.network.SmartDispoApi
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import java.time.LocalDate
import java.time.LocalTime
import java.time.OffsetDateTime
import java.time.ZoneId
import javax.inject.Inject

data class InviteeDraft(val name: String = "", val institution: String = "")

data class MeetingFormUiState(
    val loading: Boolean = true,
    val saving: Boolean = false,
    val submitting: Boolean = false,
    val meetingTypes: List<MeetingType> = emptyList(),
    val senderName: String = "",
    val senderPosition: String = "",
    val meetingTypeCode: String = "",
    val purpose: String = "",
    val date: String = LocalDate.now(ZoneId.of("Asia/Makassar")).plusDays(1).toString(),
    val time: String = "09:00",
    val place: String = "",
    val attire: String = "",
    val invitees: List<InviteeDraft> = listOf(InviteeDraft()),
    val notes: String = "",
    val signerRoleCode: String = "",
    val editing: Boolean = false,
    val lockVersion: Int = 0,
    val changeReason: String = "Perbaikan dokumen yang dikembalikan",
    val error: String? = null,
    val savedDocumentId: String? = null,
    val submitted: Boolean = false,
)

@HiltViewModel
class MeetingRequestViewModel @Inject constructor(private val api: SmartDispoApi) : ViewModel() {
    private val _state = MutableStateFlow(MeetingFormUiState())
    val state: StateFlow<MeetingFormUiState> = _state.asStateFlow()

    init {
        viewModelScope.launch {
            runCatching { api.me() to api.meetingTypes() }
                .onSuccess { (profile, types) ->
                    _state.value = _state.value.copy(
                        loading = false,
                        senderName = profile.fullName,
                        meetingTypes = types,
                        meetingTypeCode = types.firstOrNull()?.code.orEmpty(),
                    )
                }
                .onFailure {
                    _state.value = _state.value.copy(
                        loading = false,
                        error = "Master jenis rapat belum dapat dimuat.",
                    )
                }
        }
    }

    fun update(transform: (MeetingFormUiState) -> MeetingFormUiState) {
        _state.value = transform(_state.value).copy(error = null)
    }

    fun loadForEdit(documentId: String) = viewModelScope.launch {
        if (_state.value.savedDocumentId == documentId) return@launch
        _state.value = _state.value.copy(loading = true, error = null)
        runCatching { api.meetingRequest(documentId) }.onSuccess { request ->
            val scheduled = OffsetDateTime.parse(request.scheduledAt)
            _state.value = _state.value.copy(
                loading = false,
                senderName = request.senderName,
                senderPosition = request.senderPosition,
                meetingTypeCode = request.meetingTypeCode,
                purpose = request.purpose,
                date = scheduled.toLocalDate().toString(),
                time = scheduled.toLocalTime().withSecond(0).withNano(0).toString(),
                place = request.place,
                attire = request.attire.orEmpty(),
                invitees = request.invitees.map { InviteeDraft(it.name, it.institution.orEmpty()) },
                notes = request.notes.orEmpty(),
                signerRoleCode = request.signerRoleCode.orEmpty(),
                editing = true,
                lockVersion = request.lockVersion,
                savedDocumentId = request.documentId,
            )
        }.onFailure {
            _state.value = _state.value.copy(loading = false, error = "Dokumen tidak dapat dimuat untuk diperbaiki.")
        }
    }

    fun addInvitee() {
        if (_state.value.invitees.size < 20) update { it.copy(invitees = it.invitees + InviteeDraft()) }
    }

    fun removeInvitee(index: Int) = update {
        if (it.invitees.size == 1) it else it.copy(invitees = it.invitees.filterIndexed { i, _ -> i != index })
    }

    fun updateInvitee(index: Int, value: InviteeDraft) = update {
        it.copy(invitees = it.invitees.mapIndexed { i, current -> if (i == index) value else current })
    }

    fun saveDraft() = viewModelScope.launch {
        val form = _state.value
        val validInvitees = form.invitees.filter { it.name.isNotBlank() }
        if (
            form.senderName.isBlank() || form.senderPosition.isBlank() || form.meetingTypeCode.isBlank() ||
            form.purpose.isBlank() || form.place.isBlank() || validInvitees.isEmpty()
        ) {
            _state.value = form.copy(error = "Lengkapi pemohon, jenis rapat, maksud, tempat, dan undangan.")
            return@launch
        }
        val scheduledAt = runCatching {
            LocalDate.parse(form.date)
                .atTime(LocalTime.parse(form.time))
                .atZone(ZoneId.of("Asia/Makassar"))
                .toOffsetDateTime()
                .toString()
        }.getOrElse {
            _state.value = form.copy(error = "Tanggal harus YYYY-MM-DD dan jam harus HH:mm.")
            return@launch
        }
        _state.value = form.copy(saving = true, error = null)
        val invitees = validInvitees.map {
            MeetingInvitee(it.name.trim(), it.institution.trim().ifBlank { null })
        }
        runCatching {
            if (form.editing) {
                api.updateMeetingRequest(
                    form.savedDocumentId ?: error("Dokumen tidak ditemukan"),
                    MeetingRequestUpdate(
                        form.senderName.trim(), form.senderPosition.trim(), form.meetingTypeCode,
                        form.purpose.trim(), scheduledAt, form.place.trim(),
                        form.attire.trim().ifBlank { null }, invitees, form.notes.trim().ifBlank { null },
                        form.signerRoleCode.trim().ifBlank { null }, form.lockVersion, form.changeReason.trim(),
                    ),
                )
            } else api.createMeetingRequest(
                MeetingRequestCreate(
                    form.senderName.trim(), form.senderPosition.trim(), form.meetingTypeCode,
                    form.purpose.trim(), scheduledAt, form.place.trim(),
                    form.attire.trim().ifBlank { null }, invitees, form.notes.trim().ifBlank { null },
                    form.signerRoleCode.trim().ifBlank { null },
                ),
            )
        }.onSuccess { response ->
            _state.value = form.copy(
                saving = false,
                savedDocumentId = response.documentId,
                lockVersion = response.lockVersion,
            )
        }.onFailure {
            _state.value = form.copy(saving = false, error = "Draft gagal disimpan. Periksa izin akun atau jaringan.")
        }
    }

    fun submit() = viewModelScope.launch {
        val form = _state.value
        val documentId = form.savedDocumentId ?: return@launch
        _state.value = form.copy(submitting = true, error = null)
        runCatching { api.submitDocument(documentId) }
            .onSuccess { _state.value = form.copy(submitting = false, submitted = true) }
            .onFailure {
                _state.value = form.copy(
                    submitting = false,
                    error = "Dokumen gagal dikirim. Pastikan workflow sudah dipublikasikan Administrator.",
                )
            }
    }
}

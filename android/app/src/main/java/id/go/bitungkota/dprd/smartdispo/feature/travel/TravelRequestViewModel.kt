package id.go.bitungkota.dprd.smartdispo.feature.travel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import id.go.bitungkota.dprd.smartdispo.core.model.TravelMember
import id.go.bitungkota.dprd.smartdispo.core.model.TravelRequestCreate
import id.go.bitungkota.dprd.smartdispo.core.model.TravelRequestUpdate
import id.go.bitungkota.dprd.smartdispo.core.network.SmartDispoApi
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import java.time.LocalDate
import java.time.ZoneId
import javax.inject.Inject

data class TravelMemberDraft(val name: String = "", val position: String = "", val group: String = "EXECUTOR")

data class TravelFormUiState(
    val senderName: String = "",
    val senderPosition: String = "",
    val unit: String = "",
    val activityType: String = "CONSULTATION",
    val destinations: List<String> = listOf(""),
    val purpose: String = "",
    val material: String = "",
    val generalProblem: String = "",
    val currentCondition: String = "",
    val efforts: String = "",
    val startDate: String = LocalDate.now(ZoneId.of("Asia/Makassar")).plusDays(1).toString(),
    val endDate: String = LocalDate.now(ZoneId.of("Asia/Makassar")).plusDays(1).toString(),
    val activityTime: String = "09:00",
    val place: String = "",
    val members: List<TravelMemberDraft> = listOf(TravelMemberDraft()),
    val notes: String = "",
    val editing: Boolean = false,
    val lockVersion: Int = 0,
    val changeReason: String = "Perbaikan dokumen yang dikembalikan",
    val saving: Boolean = false,
    val submitting: Boolean = false,
    val error: String? = null,
    val savedDocumentId: String? = null,
    val submitted: Boolean = false,
)

@HiltViewModel
class TravelRequestViewModel @Inject constructor(private val api: SmartDispoApi) : ViewModel() {
    private val _state = MutableStateFlow(TravelFormUiState())
    val state: StateFlow<TravelFormUiState> = _state.asStateFlow()

    init {
        viewModelScope.launch {
            runCatching { api.me() }.onSuccess { profile ->
                update { it.copy(senderName = profile.fullName) }
            }
        }
    }

    fun update(transform: (TravelFormUiState) -> TravelFormUiState) {
        _state.value = transform(_state.value).copy(error = null)
    }

    fun loadForEdit(documentId: String) = viewModelScope.launch {
        if (_state.value.savedDocumentId == documentId) return@launch
        _state.value = _state.value.copy(saving = true, error = null)
        runCatching { api.travelRequest(documentId) }.onSuccess { request ->
            _state.value = _state.value.copy(
                senderName = request.senderName,
                senderPosition = request.senderPosition,
                unit = request.organizationalUnit,
                activityType = request.activityType,
                destinations = request.destinations,
                purpose = request.purpose,
                material = request.material,
                generalProblem = request.generalProblem,
                currentCondition = request.currentCondition,
                efforts = request.efforts,
                startDate = request.startDate,
                endDate = request.endDate,
                activityTime = request.activityTime?.take(5).orEmpty(),
                place = request.place,
                members = request.members.map { TravelMemberDraft(it.name, it.position.orEmpty(), it.memberGroup) },
                notes = request.notes.orEmpty(),
                editing = true,
                lockVersion = request.lockVersion,
                savedDocumentId = request.documentId,
                saving = false,
            )
        }.onFailure {
            _state.value = _state.value.copy(saving = false, error = "Dokumen tidak dapat dimuat untuk diperbaiki.")
        }
    }

    fun updateDestination(index: Int, value: String) = update {
        it.copy(destinations = it.destinations.mapIndexed { i, current -> if (i == index) value else current })
    }

    fun addDestination() = update { if (it.destinations.size < 4) it.copy(destinations = it.destinations + "") else it }
    fun removeDestination(index: Int) = update {
        if (it.destinations.size == 1) it else it.copy(destinations = it.destinations.filterIndexed { i, _ -> i != index })
    }

    fun updateMember(index: Int, value: TravelMemberDraft) = update {
        it.copy(members = it.members.mapIndexed { i, current -> if (i == index) value else current })
    }

    fun addMember(group: String) = update {
        if (it.members.size < 26) it.copy(members = it.members + TravelMemberDraft(group = group)) else it
    }

    fun removeMember(index: Int) = update {
        if (it.members.size == 1) it else it.copy(members = it.members.filterIndexed { i, _ -> i != index })
    }

    fun saveDraft() = viewModelScope.launch {
        val form = _state.value
        val destinations = form.destinations.map(String::trim).filter(String::isNotBlank)
        val members = form.members.filter { it.name.isNotBlank() }
        if (
            listOf(
                form.senderName, form.senderPosition, form.unit, form.purpose, form.material,
                form.generalProblem, form.currentCondition, form.efforts, form.place,
            ).any(String::isBlank) || destinations.isEmpty() || members.none { it.group == "EXECUTOR" }
        ) {
            _state.value = form.copy(error = "Lengkapi seluruh data wajib dan minimal satu pelaksana.")
            return@launch
        }
        if (runCatching { LocalDate.parse(form.startDate) <= LocalDate.parse(form.endDate) }.getOrDefault(false).not()) {
            _state.value = form.copy(error = "Format/rentang tanggal tidak valid.")
            return@launch
        }
        _state.value = form.copy(saving = true, error = null)
        val memberPayload = members.map {
            TravelMember(it.name.trim(), it.position.trim().ifBlank { null }, it.group)
        }
        val activityTime = form.activityTime.takeIf(String::isNotBlank)?.let {
            if (it.length == 5) "$it:00" else it
        }
        runCatching {
            if (form.editing) {
                api.updateTravelRequest(
                    form.savedDocumentId ?: error("Dokumen tidak ditemukan"),
                    TravelRequestUpdate(
                        form.senderName.trim(), form.senderPosition.trim(), form.unit.trim(), form.activityType,
                        destinations, form.purpose.trim(), form.material.trim(), form.generalProblem.trim(),
                        form.currentCondition.trim(), form.efforts.trim(), form.startDate, form.endDate,
                        activityTime, form.place.trim(), memberPayload, form.notes.trim().ifBlank { null },
                        expectedLockVersion = form.lockVersion, changeReason = form.changeReason.trim(),
                    ),
                )
            } else api.createTravelRequest(
                TravelRequestCreate(
                    form.senderName.trim(), form.senderPosition.trim(), form.unit.trim(), form.activityType,
                    destinations, form.purpose.trim(), form.material.trim(), form.generalProblem.trim(),
                    form.currentCondition.trim(), form.efforts.trim(), form.startDate, form.endDate,
                    activityTime, form.place.trim(), memberPayload, form.notes.trim().ifBlank { null },
                ),
            )
        }.onSuccess { response ->
            _state.value = form.copy(
                saving = false,
                savedDocumentId = response.documentId,
                lockVersion = response.lockVersion,
            )
        }.onFailure {
            _state.value = form.copy(saving = false, error = "Draft gagal disimpan. Periksa isian, izin, dan jaringan.")
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

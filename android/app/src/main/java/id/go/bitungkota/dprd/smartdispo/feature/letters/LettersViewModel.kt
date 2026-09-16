package id.go.bitungkota.dprd.smartdispo.feature.letters

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import id.go.bitungkota.dprd.smartdispo.core.model.DispositionCreate
import id.go.bitungkota.dprd.smartdispo.core.model.DispositionTarget
import id.go.bitungkota.dprd.smartdispo.core.model.DispositionTargetOption
import id.go.bitungkota.dprd.smartdispo.core.model.DocumentSummary
import id.go.bitungkota.dprd.smartdispo.core.model.IncomingLetterCreate
import id.go.bitungkota.dprd.smartdispo.core.network.SmartDispoApi
import id.go.bitungkota.dprd.smartdispo.core.network.ConnectivityMonitor
import id.go.bitungkota.dprd.smartdispo.core.database.OfflineCache
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import java.time.LocalDate
import java.time.ZoneId
import javax.inject.Inject

enum class LetterMode { LIST, CREATE, DISPOSITION }

data class DirectiveOption(val code: String, val label: String)

val dprdDirectives = listOf(
    DirectiveOption("FORWARD_COMMISSION_I", "Teruskan ke Komisi I"),
    DirectiveOption("FORWARD_COMMISSION_II", "Teruskan ke Komisi II"),
    DirectiveOption("FORWARD_COMMISSION_III", "Teruskan ke Komisi III"),
    DirectiveOption("FORWARD_BAPEMPERDA", "Teruskan ke Bapemperda"),
    DirectiveOption("FORWARD_BANGGAR", "Teruskan ke Badan Anggaran"),
    DirectiveOption("FORWARD_PANSUS", "Teruskan ke Pansus"),
    DirectiveOption("FOLLOW_UP", "Untuk ditindaklanjuti"),
    DirectiveOption("ACKNOWLEDGE", "Untuk diketahui"),
    DirectiveOption("REMIND", "Diingatkan"),
    DirectiveOption("POSTPONE_CANCEL", "Ditunda / dibatalkan"),
    DirectiveOption("ARCHIVE", "Diarsipkan"),
    DirectiveOption("CREATE_SPT", "Buatkan SPT"),
    DirectiveOption("CREATE_SPD", "Buatkan SPD"),
    DirectiveOption("CREATE_RECOMMENDATION", "Buatkan rekomendasi"),
    DirectiveOption("CREATE_APPROVAL", "Buatkan persetujuan"),
    DirectiveOption("CREATE_SPEECH", "Buatkan sambutan"),
    DirectiveOption("STUDY_RESEARCH", "Dipelajari / diteliti"),
    DirectiveOption("APPROVED", "Disetujui"),
    DirectiveOption("SCHEDULE", "Dijadwalkan"),
    DirectiveOption("PROCESS_BY_MECHANISM", "Proses sesuai mekanisme"),
    DirectiveOption("ADJUST_BUDGET", "Sesuaikan dengan anggaran"),
    DirectiveOption("COORDINATE_CONFIRM", "Koordinasi / konfirmasi"),
    DirectiveOption("COPY_MULTIPLY", "Fotocopy perbanyak"),
    DirectiveOption("CREATE_INVITATION", "Buatkan undangan"),
    DirectiveOption("CREATE_DESTINATION_NOTICE", "Buatkan surat pemberitahuan ke daerah tujuan"),
)

val setwanDirectives = listOf(
    DirectiveOption("FURTHER_PROCESS", "Proses lebih lanjut"),
    DirectiveOption("CREATE_REVIEW_ADVICE", "Buat telaahan dan saran"),
    DirectiveOption("COORDINATE", "Koordinasikan"),
    DirectiveOption("STUDY_REPORT", "Pelajari dan laporkan"),
    DirectiveOption("MONITOR_INPUT", "Monitor untuk masukan"),
    DirectiveOption("CONSIDER", "Pertimbangkan"),
    DirectiveOption("GUIDANCE", "Untuk dipedomani"),
    DirectiveOption("PREPARE_MATERIAL", "Buat materi / siapkan bahan"),
    DirectiveOption("ATTENTION", "Untuk minta perhatian"),
    DirectiveOption("ACKNOWLEDGE", "Untuk diketahui"),
    DirectiveOption("CREATE_SPT", "Buatkan SPT"),
    DirectiveOption("CREATE_SPD", "Buatkan SPD"),
    DirectiveOption("FILE", "File"),
)

val sekwanDprdDirectives = listOf(
    DirectiveOption("FORWARD_GENERAL_FINANCE", "Teruskan ke Kabag Umum dan Keuangan"),
    DirectiveOption(
        "FORWARD_LEGISLATION_SESSION_PUBLIC_RELATIONS",
        "Teruskan ke Kabag Perundang-undangan, Persidangan dan Humas",
    ),
    DirectiveOption(
        "FORWARD_FACILITATION_BUDGET_OVERSIGHT",
        "Teruskan ke Kabag Fasilitasi, Penganggaran dan Pengawasan",
    ),
)

data class LettersUiState(
    val mode: LetterMode = LetterMode.LIST,
    val documents: List<DocumentSummary> = emptyList(),
    val loading: Boolean = true,
    val query: String = "",
    val showArchived: Boolean = false,
    val routeType: String = "DPRD",
    val sender: String = "",
    val letterNumber: String = "",
    val letterDate: String = LocalDate.now(ZoneId.of("Asia/Makassar")).toString(),
    val receivedDate: String = LocalDate.now(ZoneId.of("Asia/Makassar")).toString(),
    val agendaNumber: String = "",
    val agendaDate: String = LocalDate.now(ZoneId.of("Asia/Makassar")).toString(),
    val subject: String = "",
    val priority: String = "BIASA",
    val notes: String = "",
    val selectedDocument: DocumentSummary? = null,
    val dispositionActorRole: String = "",
    val selectedDirectives: Set<String> = emptySet(),
    val dispositionNote: String = "",
    val dispositionTargets: List<DispositionTargetOption> = emptyList(),
    val selectedTargetKeys: Set<String> = emptySet(),
    val targetQuery: String = "",
    val loadingTargets: Boolean = false,
    val saving: Boolean = false,
    val error: String? = null,
    val success: String? = null,
    val draftDocumentId: String? = null,
) {
    val filteredDocuments: List<DocumentSummary>
        get() = documents.filter { document ->
            val statusMatches = if (showArchived) {
                document.status == "COMPLETED"
            } else {
                document.status != "COMPLETED"
            }
            val needle = query.trim().lowercase()
            statusMatches && (
                needle.isBlank() ||
                    listOfNotNull(document.title, document.documentNumber, document.agendaNumber)
                        .any { needle in it.lowercase() }
                )
        }
}

@HiltViewModel
class LettersViewModel @Inject constructor(
    private val api: SmartDispoApi,
    private val cache: OfflineCache,
    private val connectivity: ConnectivityMonitor,
) : ViewModel() {
    private val _state = MutableStateFlow(LettersUiState())
    val state: StateFlow<LettersUiState> = _state.asStateFlow()

    init { refresh() }

    fun update(transform: (LettersUiState) -> LettersUiState) {
        _state.value = transform(_state.value).copy(error = null, success = null)
    }

    fun refresh() = viewModelScope.launch {
        runCatching { api.documents() }.onSuccess { documents ->
            cache.write("documents", documents)
            _state.value = _state.value.copy(
                loading = false,
                documents = documents,
            )
        }.onFailure {
            val cached = cache.read<List<DocumentSummary>>("documents").orEmpty()
            _state.value = _state.value.copy(
                loading = false,
                documents = cached,
                error = if (cached.isEmpty()) "Daftar surat belum dapat dimuat." else "Menampilkan data terakhir tersimpan.",
            )
        }
    }

    fun showCreate() = update { it.copy(mode = LetterMode.CREATE) }
    fun showList() { _state.value = LettersUiState(); refresh() }
    fun showDisposition(document: DocumentSummary, activeRoleCodes: Set<String>) = update {
        val actorRole = if (document.documentType == "INCOMING_CHAIRMAN" && "CHAIRMAN" in activeRoleCodes) {
            "CHAIRMAN"
        } else {
            "SEKWAN"
        }
        it.copy(
            mode = LetterMode.DISPOSITION,
            selectedDocument = document,
            dispositionActorRole = actorRole,
            selectedDirectives = emptySet(),
            selectedTargetKeys = emptySet(),
            loadingTargets = true,
        )
    }.also { loadDispositionTargets() }

    private fun loadDispositionTargets() = viewModelScope.launch {
        runCatching { api.dispositionTargets() }
            .onSuccess { options ->
                _state.value = _state.value.copy(dispositionTargets = options, loadingTargets = false)
            }
            .onFailure {
                _state.value = _state.value.copy(
                    loadingTargets = false,
                    error = "Daftar tujuan disposisi belum dapat dimuat.",
                )
            }
    }

    fun toggleTarget(option: DispositionTargetOption) = update { state ->
        val key = "${option.targetType}:${option.targetId}"
        state.copy(
            selectedTargetKeys = if (key in state.selectedTargetKeys) {
                state.selectedTargetKeys - key
            } else {
                state.selectedTargetKeys + key
            },
        )
    }

    fun toggleDirective(code: String) = update {
        it.copy(selectedDirectives = if (code in it.selectedDirectives) it.selectedDirectives - code else it.selectedDirectives + code)
    }

    fun saveLetter() = viewModelScope.launch {
        val form = _state.value
        if (listOf(form.sender, form.letterNumber, form.agendaNumber, form.subject).any(String::isBlank)) {
            _state.value = form.copy(error = "Lengkapi asal surat, nomor surat, agenda, dan perihal.")
            return@launch
        }
        _state.value = form.copy(saving = true)
        runCatching {
            api.createIncomingLetter(
                IncomingLetterCreate(
                    form.routeType, form.sender.trim(), form.letterNumber.trim(), form.letterDate,
                    form.receivedDate, form.agendaNumber.trim(), form.agendaDate, form.subject.trim(),
                    form.priority, form.notes.trim().ifBlank { null },
                )
            )
        }.onSuccess { response ->
            _state.value = form.copy(
                saving = false,
                draftDocumentId = response.documentId,
                success = "Draft surat dan lembar disposisi berhasil dibuat.",
            )
        }.onFailure {
            _state.value = form.copy(saving = false, error = "Surat gagal disimpan. Periksa nomor agenda dan isian.")
        }
    }

    fun submitLetter() = viewModelScope.launch {
        val form = _state.value
        val documentId = form.draftDocumentId ?: return@launch
        if (!connectivity.isOnline()) {
            _state.value = form.copy(error = "Pengiriman ke workflow wajib dilakukan saat online.")
            return@launch
        }
        _state.value = form.copy(saving = true, error = null)
        runCatching { api.submitDocument(documentId) }
            .onSuccess { showList() }
            .onFailure {
                _state.value = form.copy(
                    saving = false,
                    error = "Surat gagal dikirim. Pastikan workflow aktif sudah dipublikasikan.",
                )
            }
    }

    fun saveDisposition() = viewModelScope.launch {
        val form = _state.value
        val document = form.selectedDocument ?: return@launch
        if (!connectivity.isOnline()) {
            _state.value = form.copy(error = "Disposisi wajib dilakukan saat perangkat online.")
            return@launch
        }
        if (form.selectedDirectives.isEmpty()) {
            _state.value = form.copy(error = "Pilih minimal satu isi disposisi.")
            return@launch
        }
        if (form.dispositionActorRole == "SEKWAN" && form.selectedTargetKeys.isEmpty()) {
            _state.value = form.copy(error = "Pilih minimal satu unit, role, atau pengguna tujuan disposisi.")
            return@launch
        }
        val targets = form.dispositionTargets.filter { option ->
            "${option.targetType}:${option.targetId}" in form.selectedTargetKeys
        }.map { option ->
            when (option.targetType) {
                "UNIT" -> DispositionTarget(unitId = option.targetId)
                "ROLE" -> DispositionTarget(roleId = option.targetId)
                else -> DispositionTarget(userId = option.targetId)
            }
        }
        _state.value = form.copy(saving = true)
        runCatching {
            api.createDisposition(
                document.id,
                DispositionCreate(
                    actorRole = form.dispositionActorRole,
                    directives = form.selectedDirectives.sorted(),
                    note = form.dispositionNote.trim().ifBlank { null },
                    targets = targets,
                ),
            )
        }.onSuccess { _state.value = form.copy(saving = false, success = "Disposisi berhasil disimpan.") }
            .onFailure { _state.value = form.copy(saving = false, error = "Disposisi gagal disimpan.") }
    }
}

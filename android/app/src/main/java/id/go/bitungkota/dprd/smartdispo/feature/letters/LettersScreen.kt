package id.go.bitungkota.dprd.smartdispo.feature.letters

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.FilterChip
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import id.go.bitungkota.dprd.smartdispo.core.model.DocumentSummary

@Composable
fun LettersScreen(
    onOpenDocument: (String) -> Unit,
    onEditDocument: (DocumentSummary) -> Unit,
    canCreateIncoming: Boolean,
    canDisposition: Boolean,
    activeRoleCodes: Set<String>,
    viewModel: LettersViewModel = hiltViewModel(),
) {
    val state by viewModel.state.collectAsStateWithLifecycle()
    when (state.mode) {
        LetterMode.LIST -> LetterList(
            state,
            viewModel,
            onOpenDocument,
            onEditDocument,
            canCreateIncoming,
            canDisposition,
            activeRoleCodes,
        )
        LetterMode.CREATE -> LetterForm(state, viewModel, onOpenDocument)
        LetterMode.DISPOSITION -> DispositionForm(state, viewModel)
    }
}

@Composable
private fun LetterList(
    state: LettersUiState,
    viewModel: LettersViewModel,
    onOpenDocument: (String) -> Unit,
    onEditDocument: (DocumentSummary) -> Unit,
    canCreateIncoming: Boolean,
    canDisposition: Boolean,
    activeRoleCodes: Set<String>,
) {
    LazyColumn(
        Modifier.fillMaxSize().padding(20.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        item {
            Text("Dokumen & Surat", style = MaterialTheme.typography.headlineSmall)
            OutlinedTextField(
                value = state.query,
                onValueChange = { value -> viewModel.update { it.copy(query = value) } },
                label = { Text("Cari judul, nomor, atau agenda") },
                modifier = Modifier.fillMaxWidth(),
            )
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                FilterChip(
                    selected = !state.showArchived,
                    onClick = { viewModel.update { it.copy(showArchived = false) } },
                    label = { Text("Aktif") },
                )
                FilterChip(
                    selected = state.showArchived,
                    onClick = { viewModel.update { it.copy(showArchived = true) } },
                    label = { Text("Arsip selesai") },
                )
            }
            if (canCreateIncoming) {
                Button(viewModel::showCreate, modifier = Modifier.fillMaxWidth()) { Text("Catat Surat Masuk") }
            }
        }
        if (state.loading) item { Text("Memuat surat...") }
        state.error?.let { item { Text(it, color = MaterialTheme.colorScheme.error) } }
        items(state.filteredDocuments, key = DocumentSummary::id) { document ->
            Card(Modifier.fillMaxWidth()) {
                Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                    Text(document.title, style = MaterialTheme.typography.titleMedium)
                    Text("Agenda: ${document.agendaNumber ?: "-"}")
                    Text(document.documentType.replace('_', ' '))
                    Text(document.status)
                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        OutlinedButton({ onOpenDocument(document.id) }) { Text("Buka") }
                        if ("EDIT" in document.availableActions && document.documentType in setOf("MEETING_REQUEST", "TRAVEL_REQUEST")) {
                            OutlinedButton({ onEditDocument(document) }) { Text("Perbaiki") }
                        }
                        val authorized = if (document.documentType == "INCOMING_CHAIRMAN") {
                            "CHAIRMAN" in activeRoleCodes || "SEKWAN" in activeRoleCodes
                        } else {
                            "SEKWAN" in activeRoleCodes
                        }
                        if (canDisposition && authorized && document.documentType.startsWith("INCOMING_")) {
                            OutlinedButton({ viewModel.showDisposition(document, activeRoleCodes) }) {
                                Text("Isi Disposisi")
                            }
                        }
                    }
                }
            }
        }
        if (!state.loading && state.filteredDocuments.isEmpty()) item { Text("Tidak ada dokumen yang sesuai.") }
    }
}

@Composable
private fun LetterForm(
    state: LettersUiState,
    viewModel: LettersViewModel,
    onOpenDocument: (String) -> Unit,
) {
    LazyColumn(
        Modifier.fillMaxSize().padding(20.dp),
        verticalArrangement = Arrangement.spacedBy(10.dp),
    ) {
        item {
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                Text("Catat Surat Masuk", style = MaterialTheme.typography.headlineSmall)
                TextButton(viewModel::showList) { Text("Batal") }
            }
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                FilterChip(state.routeType == "DPRD", { viewModel.update { it.copy(routeType = "DPRD") } }, { Text("Ke Ketua DPRD") })
                FilterChip(state.routeType == "SETWAN", { viewModel.update { it.copy(routeType = "SETWAN") } }, { Text("Ke Sekwan") })
            }
        }
        item { Field(state.sender, "Surat dari") { viewModel.update { s -> s.copy(sender = it) } } }
        item { Field(state.letterNumber, "Nomor surat") { viewModel.update { s -> s.copy(letterNumber = it) } } }
        item { DateRow(state.letterDate, state.receivedDate, viewModel) }
        item { Field(state.agendaNumber, "Nomor agenda") { viewModel.update { s -> s.copy(agendaNumber = it) } } }
        item { Field(state.agendaDate, "Tanggal agenda YYYY-MM-DD") { viewModel.update { s -> s.copy(agendaDate = it) } } }
        item { Area(state.subject, "Perihal") { viewModel.update { s -> s.copy(subject = it) } } }
        item {
            Text("Sifat")
            Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                listOf("BIASA", "PENTING", "SEGERA", "RAHASIA").forEach { value ->
                    FilterChip(
                        state.priority == value,
                        { viewModel.update { it.copy(priority = value) } },
                        { Text(value.lowercase().replaceFirstChar { character -> character.uppercase() }) },
                    )
                }
            }
        }
        item { Area(state.notes, "Catatan (opsional)") { viewModel.update { s -> s.copy(notes = it) } } }
        state.error?.let { item { Text(it, color = MaterialTheme.colorScheme.error) } }
        state.success?.let { item { Text(it, color = MaterialTheme.colorScheme.primary) } }
        state.draftDocumentId?.let { documentId -> item {
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                OutlinedButton(onClick = { onOpenDocument(documentId) }) { Text("Preview") }
                Button(onClick = viewModel::submitLetter, enabled = !state.saving) { Text("Kirim ke Workflow") }
            }
        } }
        item {
            Button(
                viewModel::saveLetter,
                enabled = !state.saving && state.draftDocumentId == null,
                modifier = Modifier.fillMaxWidth(),
            ) { Text(if (state.saving) "Menyimpan..." else "Simpan Draft dan Buat Lembar Disposisi") }
        }
    }
}

@Composable
private fun DateRow(letterDate: String, receivedDate: String, viewModel: LettersViewModel) {
    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
        OutlinedTextField(letterDate, { value -> viewModel.update { it.copy(letterDate = value) } }, label = { Text("Tanggal surat") }, modifier = Modifier.weight(1f))
        OutlinedTextField(receivedDate, { value -> viewModel.update { it.copy(receivedDate = value) } }, label = { Text("Tanggal terima") }, modifier = Modifier.weight(1f))
    }
}

@Composable
private fun DispositionForm(state: LettersUiState, viewModel: LettersViewModel) {
    val document = state.selectedDocument ?: return
    val options = when {
        document.documentType == "INCOMING_CHAIRMAN" && state.dispositionActorRole == "SEKWAN" -> {
            sekwanDprdDirectives
        }
        document.documentType == "INCOMING_CHAIRMAN" -> dprdDirectives
        else -> setwanDirectives
    }
    LazyColumn(Modifier.fillMaxSize().padding(20.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
        item {
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                Text("Lembar Disposisi", style = MaterialTheme.typography.headlineSmall)
                TextButton(viewModel::showList) { Text("Kembali") }
            }
            Text(document.title)
            Text(if (state.dispositionActorRole == "CHAIRMAN") "Disposisi Ketua DPRD" else "Disposisi Sekretaris DPRD")
        }
        items(options, key = DirectiveOption::code) { option ->
            FilterChip(
                selected = option.code in state.selectedDirectives,
                onClick = { viewModel.toggleDirective(option.code) },
                label = { Text(option.label) },
                modifier = Modifier.fillMaxWidth(),
            )
        }
        item { Area(state.dispositionNote, "Catatan disposisi") { viewModel.update { s -> s.copy(dispositionNote = it) } } }
        state.error?.let { item { Text(it, color = MaterialTheme.colorScheme.error) } }
        state.success?.let { item { Text(it, color = MaterialTheme.colorScheme.primary) } }
        item { Button(viewModel::saveDisposition, enabled = !state.saving && state.success == null, modifier = Modifier.fillMaxWidth()) { Text(if (state.saving) "Menyimpan..." else "Simpan Disposisi") } }
    }
}

@Composable private fun Field(value: String, label: String, changed: (String) -> Unit) =
    OutlinedTextField(value, changed, label = { Text(label) }, modifier = Modifier.fillMaxWidth())
@Composable private fun Area(value: String, label: String, changed: (String) -> Unit) =
    OutlinedTextField(value, changed, label = { Text(label) }, minLines = 3, modifier = Modifier.fillMaxWidth())

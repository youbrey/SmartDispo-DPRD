package id.go.bitungkota.dprd.smartdispo.feature.travel

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.ArrowBack
import androidx.compose.material.icons.outlined.Delete
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FilterChip
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun TravelRequestScreen(
    onBack: () -> Unit,
    onPreview: (String) -> Unit,
    editDocumentId: String? = null,
    viewModel: TravelRequestViewModel = hiltViewModel(),
) {
    val state by viewModel.state.collectAsStateWithLifecycle()
    LaunchedEffect(editDocumentId) { editDocumentId?.let(viewModel::loadForEdit) }
    Scaffold(topBar = { TopAppBar(title = { Text("Permintaan Perjalanan Dinas") }, navigationIcon = {
        IconButton(onClick = onBack) { Icon(Icons.Outlined.ArrowBack, "Kembali") }
    }) }) { padding ->
        LazyColumn(
            Modifier.fillMaxSize().padding(padding),
            contentPadding = androidx.compose.foundation.layout.PaddingValues(20.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            item { Section("Pemohon") }
            item { Field(state.senderName, "Dari") { viewModel.update { s -> s.copy(senderName = it) } } }
            item { Field(state.senderPosition, "Jabatan") { viewModel.update { s -> s.copy(senderPosition = it) } } }
            item { Field(state.unit, "Unit / AKD") { viewModel.update { s -> s.copy(unit = it) } } }
            item {
                Section("Kegiatan")
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    FilterChip(state.activityType == "CONSULTATION", { viewModel.update { it.copy(activityType = "CONSULTATION") } }, { Text("Konsultasi") })
                    FilterChip(state.activityType == "WORK_VISIT", { viewModel.update { it.copy(activityType = "WORK_VISIT") } }, { Text("Kunjungan Kerja") })
                }
            }
            itemsIndexed(state.destinations) { index, value ->
                Row(Modifier.fillMaxWidth()) {
                    OutlinedTextField(value, { viewModel.updateDestination(index, it) }, label = { Text("Tujuan ${index + 1}") }, modifier = Modifier.weight(1f))
                    IconButton({ viewModel.removeDestination(index) }, enabled = state.destinations.size > 1) { Icon(Icons.Outlined.Delete, "Hapus") }
                }
            }
            item { OutlinedButton(viewModel::addDestination, enabled = state.destinations.size < 4) { Text("Tambah Tujuan") } }
            item { Area(state.purpose, "Dalam rangka / tujuan") { viewModel.update { s -> s.copy(purpose = it) } } }
            item { Area(state.material, "Materi konsultasi / kunjungan") { viewModel.update { s -> s.copy(material = it) } } }
            item { Area(state.generalProblem, "Permasalahan umum") { viewModel.update { s -> s.copy(generalProblem = it) } } }
            item { Area(state.currentCondition, "Kondisi saat ini") { viewModel.update { s -> s.copy(currentCondition = it) } } }
            item { Area(state.efforts, "Upaya yang telah dilaksanakan") { viewModel.update { s -> s.copy(efforts = it) } } }
            item {
                Section("Jadwal dan Tempat")
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    OutlinedTextField(state.startDate, { viewModel.update { s -> s.copy(startDate = it) } }, label = { Text("Mulai") }, modifier = Modifier.weight(1f))
                    OutlinedTextField(state.endDate, { viewModel.update { s -> s.copy(endDate = it) } }, label = { Text("Selesai") }, modifier = Modifier.weight(1f))
                }
            }
            item { Field(state.activityTime, "Jam (HH:mm)") { viewModel.update { s -> s.copy(activityTime = it) } } }
            item { Field(state.place, "Tempat") { viewModel.update { s -> s.copy(place = it) } } }
            item { Section("Pelaksana dan Pendamping") }
            itemsIndexed(state.members) { index, member ->
                Card(Modifier.fillMaxWidth()) { Column(Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                        Text(if (member.group == "EXECUTOR") "Pelaksana" else "Pendamping")
                        IconButton({ viewModel.removeMember(index) }, enabled = state.members.size > 1) { Icon(Icons.Outlined.Delete, "Hapus") }
                    }
                    Field(member.name, "Nama") { viewModel.updateMember(index, member.copy(name = it)) }
                    Field(member.position, "Jabatan") { viewModel.updateMember(index, member.copy(position = it)) }
                } }
            }
            item { Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                OutlinedButton({ viewModel.addMember("EXECUTOR") }) { Text("Tambah Pelaksana") }
                OutlinedButton({ viewModel.addMember("ACCOMPANYING") }) { Text("Tambah Pendamping") }
            } }
            item { Area(state.notes, "Catatan (opsional)") { viewModel.update { s -> s.copy(notes = it) } } }
            if (state.editing) item { Field(state.changeReason, "Alasan perubahan") { viewModel.update { s -> s.copy(changeReason = it) } } }
            state.error?.let { item { Text(it, color = MaterialTheme.colorScheme.error) } }
            state.savedDocumentId?.let { id -> item { Card(Modifier.fillMaxWidth()) { Column(Modifier.padding(16.dp)) {
                Text("Draft berhasil disimpan"); Text("ID dokumen: $id")
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    OutlinedButton(onClick = { onPreview(id) }) { Text("Preview") }
                    Button(onClick = viewModel::submit, enabled = !state.submitting && !state.submitted) {
                        Text(if (state.submitted) "Terkirim" else if (state.submitting) "Mengirim…" else "Kirim")
                    }
                }
                if (state.submitted) TextButton(onClick = onBack) { Text("Kembali") }
            } } } }
            item { Button(viewModel::saveDraft, enabled = !state.saving && (state.editing || state.savedDocumentId == null), modifier = Modifier.fillMaxWidth()) { Text(if (state.saving) "Menyimpan..." else if (state.editing) "Simpan Perbaikan" else "Simpan Draft") } }
        }
    }
}

@Composable private fun Section(value: String) = Text(value, style = MaterialTheme.typography.titleLarge)
@Composable private fun Field(value: String, label: String, changed: (String) -> Unit) =
    OutlinedTextField(value, changed, label = { Text(label) }, modifier = Modifier.fillMaxWidth())
@Composable private fun Area(value: String, label: String, changed: (String) -> Unit) =
    OutlinedTextField(value, changed, label = { Text(label) }, minLines = 3, modifier = Modifier.fillMaxWidth())

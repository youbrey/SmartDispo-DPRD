package id.go.bitungkota.dprd.smartdispo.feature.meeting

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.Add
import androidx.compose.material.icons.outlined.ArrowBack
import androidx.compose.material.icons.outlined.Delete
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.ExposedDropdownMenuBox
import androidx.compose.material3.ExposedDropdownMenuDefaults
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
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun MeetingRequestScreen(
    onBack: () -> Unit,
    viewModel: MeetingRequestViewModel = hiltViewModel(),
) {
    val state by viewModel.state.collectAsStateWithLifecycle()
    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Permintaan Rapat") },
                navigationIcon = {
                    IconButton(onClick = onBack) { Icon(Icons.Outlined.ArrowBack, contentDescription = "Kembali") }
                },
            )
        },
    ) { padding ->
        if (state.loading) {
            Column(Modifier.fillMaxSize().padding(padding), verticalArrangement = Arrangement.Center) {
                CircularProgressIndicator(Modifier.padding(24.dp))
            }
        } else {
            LazyColumn(
                modifier = Modifier.fillMaxSize().padding(padding),
                verticalArrangement = Arrangement.spacedBy(12.dp),
                contentPadding = androidx.compose.foundation.layout.PaddingValues(20.dp),
            ) {
                item {
                    Text("Informasi Pemohon", style = MaterialTheme.typography.titleLarge)
                    Text("Tujuan dokumen: Pimpinan DPRD Kota Bitung", color = MaterialTheme.colorScheme.onSurfaceVariant)
                }
                item {
                    OutlinedTextField(
                        value = state.senderName,
                        onValueChange = { value -> viewModel.update { it.copy(senderName = value) } },
                        label = { Text("Dari") },
                        modifier = Modifier.fillMaxWidth(),
                    )
                }
                item {
                    OutlinedTextField(
                        value = state.senderPosition,
                        onValueChange = { value -> viewModel.update { it.copy(senderPosition = value) } },
                        label = { Text("Jabatan") },
                        modifier = Modifier.fillMaxWidth(),
                    )
                }
                item {
                    Text("Informasi Rapat", style = MaterialTheme.typography.titleLarge)
                    MeetingTypePicker(state, viewModel)
                }
                item {
                    OutlinedTextField(
                        value = state.purpose,
                        onValueChange = { value -> viewModel.update { it.copy(purpose = value) } },
                        label = { Text("Dalam rangka / maksud rapat") },
                        minLines = 3,
                        modifier = Modifier.fillMaxWidth(),
                    )
                }
                item {
                    Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                        OutlinedTextField(
                            value = state.date,
                            onValueChange = { value -> viewModel.update { it.copy(date = value) } },
                            label = { Text("Tanggal") },
                            supportingText = { Text("YYYY-MM-DD") },
                            modifier = Modifier.weight(1f),
                        )
                        OutlinedTextField(
                            value = state.time,
                            onValueChange = { value -> viewModel.update { it.copy(time = value) } },
                            label = { Text("Jam") },
                            supportingText = { Text("HH:mm") },
                            modifier = Modifier.weight(0.7f),
                        )
                    }
                }
                item {
                    OutlinedTextField(
                        value = state.place,
                        onValueChange = { value -> viewModel.update { it.copy(place = value) } },
                        label = { Text("Tempat") },
                        modifier = Modifier.fillMaxWidth(),
                    )
                }
                item {
                    OutlinedTextField(
                        value = state.attire,
                        onValueChange = { value -> viewModel.update { it.copy(attire = value) } },
                        label = { Text("Pakaian (opsional)") },
                        modifier = Modifier.fillMaxWidth(),
                    )
                }
                item { Text("Yang Diundang / Tujuan Surat", style = MaterialTheme.typography.titleLarge) }
                itemsIndexed(state.invitees) { index, invitee ->
                    Card(Modifier.fillMaxWidth()) {
                        Column(Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                                Text("Undangan ${index + 1}", style = MaterialTheme.typography.titleSmall)
                                IconButton(onClick = { viewModel.removeInvitee(index) }, enabled = state.invitees.size > 1) {
                                    Icon(Icons.Outlined.Delete, contentDescription = "Hapus undangan")
                                }
                            }
                            OutlinedTextField(
                                value = invitee.name,
                                onValueChange = { viewModel.updateInvitee(index, invitee.copy(name = it)) },
                                label = { Text("Nama / tujuan") },
                                modifier = Modifier.fillMaxWidth(),
                            )
                            OutlinedTextField(
                                value = invitee.institution,
                                onValueChange = { viewModel.updateInvitee(index, invitee.copy(institution = it)) },
                                label = { Text("Instansi (opsional)") },
                                modifier = Modifier.fillMaxWidth(),
                            )
                        }
                    }
                }
                item {
                    OutlinedButton(onClick = viewModel::addInvitee, enabled = state.invitees.size < 20) {
                        Icon(Icons.Outlined.Add, contentDescription = null)
                        Text("Tambah Undangan (${state.invitees.size}/20)")
                    }
                }
                item {
                    Text("Administrasi", style = MaterialTheme.typography.titleLarge)
                    OutlinedTextField(
                        value = state.notes,
                        onValueChange = { value -> viewModel.update { it.copy(notes = value) } },
                        label = { Text("Catatan (opsional)") },
                        minLines = 2,
                        modifier = Modifier.fillMaxWidth(),
                    )
                }
                state.error?.let { message -> item { Text(message, color = MaterialTheme.colorScheme.error) } }
                state.savedDocumentId?.let { documentId ->
                    item {
                        Card(Modifier.fillMaxWidth()) {
                            Column(Modifier.padding(16.dp)) {
                                Text("Draft berhasil disimpan", style = MaterialTheme.typography.titleMedium)
                                Text("ID dokumen: $documentId", style = MaterialTheme.typography.bodySmall)
                                TextButton(onClick = onBack) { Text("Kembali ke Dashboard") }
                            }
                        }
                    }
                }
                item {
                    Button(
                        onClick = viewModel::saveDraft,
                        enabled = !state.saving && state.savedDocumentId == null,
                        modifier = Modifier.fillMaxWidth(),
                    ) {
                        if (state.saving) CircularProgressIndicator(Modifier.padding(2.dp)) else Text("Simpan Draft")
                    }
                }
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun MeetingTypePicker(state: MeetingFormUiState, viewModel: MeetingRequestViewModel) {
    var expanded by remember { mutableStateOf(false) }
    val selected = state.meetingTypes.firstOrNull { it.code == state.meetingTypeCode }
    ExposedDropdownMenuBox(expanded = expanded, onExpandedChange = { expanded = it }) {
        OutlinedTextField(
            value = selected?.name.orEmpty(),
            onValueChange = {},
            readOnly = true,
            label = { Text("Jenis rapat") },
            trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(expanded) },
            modifier = Modifier.menuAnchor().fillMaxWidth(),
        )
        ExposedDropdownMenu(expanded = expanded, onDismissRequest = { expanded = false }) {
            state.meetingTypes.forEach { type ->
                DropdownMenuItem(
                    text = { Text(type.name) },
                    onClick = {
                        viewModel.update { it.copy(meetingTypeCode = type.code) }
                        expanded = false
                    },
                )
            }
        }
    }
}

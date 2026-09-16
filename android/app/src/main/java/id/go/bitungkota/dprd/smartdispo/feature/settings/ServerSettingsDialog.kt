package id.go.bitungkota.dprd.smartdispo.feature.settings

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle

@Composable
fun ServerSettingsDialog(
    onDismiss: () -> Unit,
    viewModel: ServerSettingsViewModel = hiltViewModel(),
) {
    val state by viewModel.state.collectAsStateWithLifecycle()
    LaunchedEffect(Unit) { viewModel.open() }
    AlertDialog(
        onDismissRequest = { if (!state.testing) onDismiss() },
        title = { Text("Konfigurasi Server") },
        text = {
            Column {
                Text(
                    "Masukkan IP PC pada Wi-Fi yang sama. Contoh: 192.168.1.10:8000",
                    style = MaterialTheme.typography.bodyMedium,
                )
                OutlinedTextField(
                    value = state.input,
                    onValueChange = viewModel::updateInput,
                    label = { Text("Alamat server") },
                    placeholder = { Text("192.168.1.10:8000") },
                    supportingText = { Text("/api/v1/ ditambahkan otomatis") },
                    singleLine = true,
                    enabled = !state.testing,
                    modifier = Modifier.fillMaxWidth().padding(top = 12.dp),
                )
                state.message?.let { message ->
                    Text(
                        message,
                        color = if (state.connected) {
                            MaterialTheme.colorScheme.primary
                        } else {
                            MaterialTheme.colorScheme.error
                        },
                        modifier = Modifier.padding(top = 10.dp),
                    )
                }
            }
        },
        confirmButton = {
            if (state.connected) {
                Button(onClick = onDismiss) { Text("Selesai") }
            } else {
                Button(onClick = viewModel::testAndSave, enabled = !state.testing) {
                    if (state.testing) {
                        CircularProgressIndicator(
                            modifier = Modifier.padding(horizontal = 16.dp),
                            strokeWidth = 2.dp,
                        )
                    } else {
                        Text("Uji & Simpan")
                    }
                }
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss, enabled = !state.testing) { Text("Batal") }
        },
    )
}

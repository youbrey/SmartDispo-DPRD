package id.go.bitungkota.dprd.smartdispo.feature.profile

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle

@Composable
fun ProfileScreen(onLogout: () -> Unit, viewModel: ProfileViewModel = hiltViewModel()) {
    val state by viewModel.state.collectAsStateWithLifecycle()
    LazyColumn(Modifier.fillMaxSize().padding(20.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
        item {
            Text("Profil & Keamanan", style = MaterialTheme.typography.headlineSmall)
            state.profile?.let {
                Text(it.fullName, style = MaterialTheme.typography.titleLarge)
                Text("@${it.username}")
                Text("${it.permissions.size} permission aktif")
            }
        }
        state.error?.let { item { Text(it, color = MaterialTheme.colorScheme.error) } }
        item { Text("Perangkat terdaftar", style = MaterialTheme.typography.titleMedium) }
        items(state.devices, key = { it.id }) { device ->
            Card(Modifier.fillMaxWidth()) {
                Column(Modifier.padding(14.dp)) {
                    Text(device.deviceFingerprint.take(24), style = MaterialTheme.typography.labelLarge)
                    Text(if (device.revokedAt == null) "Aktif" else "Dicabut")
                    if (device.revokedAt == null) {
                        OutlinedButton(onClick = { viewModel.revoke(device.id) }) { Text("Cabut perangkat") }
                    }
                }
            }
        }
        item { Button(onClick = onLogout, modifier = Modifier.fillMaxWidth()) { Text("Keluar dari akun") } }
    }
}

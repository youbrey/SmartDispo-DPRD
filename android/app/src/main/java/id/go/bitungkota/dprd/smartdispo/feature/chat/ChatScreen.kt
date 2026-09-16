package id.go.bitungkota.dprd.smartdispo.feature.chat

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
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle

@Composable
fun ChatScreen(viewModel: ChatViewModel = hiltViewModel()) {
    val state by viewModel.state.collectAsStateWithLifecycle()
    Column(Modifier.fillMaxSize().padding(20.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
        Text("Live Chat", style = MaterialTheme.typography.headlineSmall)
        Text(if (state.realtimeConnected) "Realtime tersambung" else "Mode sinkronisasi berkala")
        LazyColumn(horizontalAlignment = androidx.compose.ui.Alignment.Start, modifier = Modifier.weight(1f)) {
            item {
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    state.rooms.forEach { room ->
                        FilterChip(
                            selected = state.selectedRoom?.id == room.id,
                            onClick = { viewModel.selectRoom(room) },
                            label = { Text(room.name) },
                        )
                    }
                }
            }
            state.error?.let { item { Text(it, color = MaterialTheme.colorScheme.error) } }
            if (!state.loading && state.rooms.isEmpty()) item { Text("Belum ada ruang chat untuk akun ini.") }
            items(state.messages, key = { it.id }) { message ->
                Card(Modifier.fillMaxWidth().padding(vertical = 4.dp)) {
                    Column(Modifier.padding(12.dp)) {
                        Text(message.senderName, style = MaterialTheme.typography.labelLarge)
                        Text(message.body)
                    }
                }
            }
        }
        if (state.selectedRoom != null) {
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                OutlinedTextField(
                    value = state.draft,
                    onValueChange = viewModel::updateDraft,
                    label = { Text("Tulis pesan") },
                    modifier = Modifier.weight(1f),
                )
                Button(onClick = viewModel::send, enabled = !state.sending && state.draft.isNotBlank()) { Text("Kirim") }
            }
        }
    }
}

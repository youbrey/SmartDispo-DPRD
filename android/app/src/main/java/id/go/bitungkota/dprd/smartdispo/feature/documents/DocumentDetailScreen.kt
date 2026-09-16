package id.go.bitungkota.dprd.smartdispo.feature.documents

import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.Image
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
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.FilterChip
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import id.go.bitungkota.dprd.smartdispo.core.model.AttachmentItem

@Composable
fun DocumentDetailScreen(
    documentId: String,
    onBack: () -> Unit,
    canUpload: Boolean,
    viewModel: DocumentDetailViewModel = hiltViewModel(),
) {
    val state by viewModel.state.collectAsStateWithLifecycle()
    var tab by remember { mutableIntStateOf(0) }
    var pendingDownload by remember { mutableStateOf<AttachmentItem?>(null) }
    val picker = rememberLauncherForActivityResult(ActivityResultContracts.GetContent()) { uri ->
        if (uri != null) viewModel.upload(uri)
    }
    val downloader = rememberLauncherForActivityResult(
        ActivityResultContracts.CreateDocument("application/octet-stream"),
    ) { uri ->
        val attachment = pendingDownload
        if (uri != null && attachment != null) viewModel.download(attachment, uri)
        pendingDownload = null
    }
    LaunchedEffect(documentId) { viewModel.load(documentId) }

    LazyColumn(
        Modifier.fillMaxSize().padding(20.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        item {
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                Text("Detail Dokumen", style = MaterialTheme.typography.headlineSmall)
                TextButton(onClick = onBack) { Text("Kembali") }
            }
            state.document?.let { document ->
                Text(document.title, style = MaterialTheme.typography.titleLarge)
                Text("${document.documentType.replace('_', ' ')} · ${document.status} · v${document.currentVersion}")
            }
        }
        if (state.loading) item { CircularProgressIndicator() }
        state.error?.let { item { Text(it, color = MaterialTheme.colorScheme.error) } }
        item {
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                listOf("Dokumen", "Timeline", "Lampiran").forEachIndexed { index, label ->
                    FilterChip(tab == index, { tab = index }, { Text(label) })
                }
            }
        }
        when (tab) {
            0 -> items(state.previewPages.withIndex().toList(), key = { it.index }) { page ->
                Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
                    Text("Halaman ${page.index + 1} dari ${state.previewPages.size}")
                    Card(Modifier.fillMaxWidth()) {
                        Image(
                            page.value.asImageBitmap(),
                            "Preview halaman ${page.index + 1}",
                            Modifier.fillMaxWidth(),
                            contentScale = ContentScale.FillWidth,
                        )
                    }
                }
            }
            1 -> items(state.timeline, key = { it.id }) { entry ->
                Card(Modifier.fillMaxWidth()) {
                    Column(Modifier.padding(14.dp)) {
                        Text(entry.title, style = MaterialTheme.typography.titleMedium)
                        Text(entry.actorName)
                        entry.note?.let { Text(it) }
                        Text(entry.occurredAt, style = MaterialTheme.typography.labelSmall)
                    }
                }
            }
            2 -> {
                if (canUpload) item {
                    Button(
                        onClick = { picker.launch("*/*") },
                        enabled = !state.uploading,
                    ) { Text(if (state.uploading) "Mengunggah…" else "Tambah Lampiran") }
                }
                items(state.attachments, key = { it.id }) { attachment ->
                    Card(Modifier.fillMaxWidth()) {
                        Column(Modifier.padding(14.dp)) {
                            Text(attachment.originalName, style = MaterialTheme.typography.titleMedium)
                            Text("${attachment.contentType} · ${attachment.sizeBytes / 1024} KB · v${attachment.documentVersion}")
                            Text("SHA-256 ${attachment.sha256Hash.take(16)}…")
                            TextButton(onClick = {
                                pendingDownload = attachment
                                downloader.launch(attachment.originalName)
                            }) { Text("Unduh") }
                        }
                    }
                }
            }
        }
    }
}

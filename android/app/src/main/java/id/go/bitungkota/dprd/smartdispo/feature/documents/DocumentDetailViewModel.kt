package id.go.bitungkota.dprd.smartdispo.feature.documents

import android.content.Context
import android.graphics.Bitmap
import android.graphics.Color
import android.graphics.pdf.PdfRenderer
import android.net.Uri
import android.os.ParcelFileDescriptor
import android.provider.OpenableColumns
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import dagger.hilt.android.qualifiers.ApplicationContext
import id.go.bitungkota.dprd.smartdispo.core.model.AttachmentItem
import id.go.bitungkota.dprd.smartdispo.core.model.DocumentSummary
import id.go.bitungkota.dprd.smartdispo.core.model.TimelineItem
import id.go.bitungkota.dprd.smartdispo.core.network.SmartDispoApi
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.MultipartBody
import okhttp3.RequestBody.Companion.toRequestBody
import java.io.File
import javax.inject.Inject

data class DocumentDetailUiState(
    val document: DocumentSummary? = null,
    val timeline: List<TimelineItem> = emptyList(),
    val attachments: List<AttachmentItem> = emptyList(),
    val previewPages: List<Bitmap> = emptyList(),
    val loading: Boolean = true,
    val uploading: Boolean = false,
    val error: String? = null,
)

@HiltViewModel
class DocumentDetailViewModel @Inject constructor(
    private val api: SmartDispoApi,
    @ApplicationContext private val context: Context,
) : ViewModel() {
    private val _state = MutableStateFlow(DocumentDetailUiState())
    val state: StateFlow<DocumentDetailUiState> = _state.asStateFlow()
    private var documentId: String? = null

    fun load(id: String) {
        if (documentId == id && _state.value.document != null) return
        documentId = id
        viewModelScope.launch {
            _state.value = DocumentDetailUiState()
            runCatching {
                val document = api.document(id)
                val timeline = api.documentTimeline(id)
                val attachments = api.attachments(id)
                val pages = withContext(Dispatchers.IO) { renderPages(id) }
                DocumentDetailUiState(document, timeline, attachments, pages, loading = false)
            }.onSuccess { _state.value = it }
                .onFailure {
                    _state.value = _state.value.copy(
                        loading = false,
                        error = "Detail atau preview dokumen belum dapat dimuat.",
                    )
                }
        }
    }

    fun upload(uri: Uri) {
        val id = documentId ?: return
        viewModelScope.launch {
            _state.value = _state.value.copy(uploading = true, error = null)
            runCatching {
                val resolver = context.contentResolver
                val bytes = withContext(Dispatchers.IO) {
                    resolver.openInputStream(uri)?.use { it.readBytes() }
                } ?: error("Berkas tidak dapat dibaca")
                val contentType = resolver.getType(uri) ?: "application/octet-stream"
                val name = resolver.query(
                    uri,
                    arrayOf(OpenableColumns.DISPLAY_NAME),
                    null,
                    null,
                    null,
                )?.use { cursor -> if (cursor.moveToFirst()) cursor.getString(0) else null } ?: "lampiran"
                api.uploadAttachment(
                    id,
                    MultipartBody.Part.createFormData(
                        "upload",
                        name,
                        bytes.toRequestBody(contentType.toMediaType()),
                    ),
                )
                api.attachments(id)
            }.onSuccess { attachments ->
                _state.value = _state.value.copy(attachments = attachments, uploading = false)
            }.onFailure {
                _state.value = _state.value.copy(
                    uploading = false,
                    error = "Lampiran gagal diunggah atau tipenya tidak diizinkan.",
                )
            }
        }
    }

    fun download(attachment: AttachmentItem, target: Uri) {
        val id = documentId ?: return
        viewModelScope.launch {
            runCatching {
                val response = api.downloadAttachment(id, attachment.id)
                withContext(Dispatchers.IO) {
                    context.contentResolver.openOutputStream(target)?.use { output ->
                        response.byteStream().use { input -> input.copyTo(output) }
                    } ?: error("Lokasi tujuan tidak dapat dibuka")
                }
            }.onFailure {
                _state.value = _state.value.copy(error = "Lampiran gagal diunduh.")
            }
        }
    }

    private suspend fun renderPages(id: String): List<Bitmap> {
        val file = File(context.cacheDir, "preview-$id.pdf")
        api.documentPreview(id).byteStream().use { input -> file.outputStream().use(input::copyTo) }
        val descriptor = ParcelFileDescriptor.open(file, ParcelFileDescriptor.MODE_READ_ONLY)
        PdfRenderer(descriptor).use { renderer ->
            return (0 until renderer.pageCount).map { index ->
                renderer.openPage(index).use { page ->
                    val width = 1200
                    val height = (width.toFloat() / page.width * page.height).toInt()
                    Bitmap.createBitmap(width, height, Bitmap.Config.ARGB_8888).also { bitmap ->
                        bitmap.eraseColor(Color.WHITE)
                        page.render(bitmap, null, null, PdfRenderer.Page.RENDER_MODE_FOR_DISPLAY)
                    }
                }
            }
        }
    }
}

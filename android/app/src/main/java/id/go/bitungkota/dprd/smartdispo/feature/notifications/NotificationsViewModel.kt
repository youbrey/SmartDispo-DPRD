package id.go.bitungkota.dprd.smartdispo.feature.notifications

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import id.go.bitungkota.dprd.smartdispo.core.model.NotificationItem
import id.go.bitungkota.dprd.smartdispo.core.network.SmartDispoApi
import id.go.bitungkota.dprd.smartdispo.core.database.OfflineCache
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

data class NotificationsUiState(
    val items: List<NotificationItem> = emptyList(),
    val loading: Boolean = true,
    val error: String? = null,
)

@HiltViewModel
class NotificationsViewModel @Inject constructor(
    private val api: SmartDispoApi,
    private val cache: OfflineCache,
) : ViewModel() {
    private val _state = MutableStateFlow(NotificationsUiState())
    val state: StateFlow<NotificationsUiState> = _state.asStateFlow()

    init { refresh() }
    fun refresh() = viewModelScope.launch {
        runCatching { api.notifications() }.onSuccess {
            cache.write("notifications", it)
            _state.value = NotificationsUiState(it, false)
        }.onFailure {
            val cached = cache.read<List<NotificationItem>>("notifications").orEmpty()
            _state.value = NotificationsUiState(
                items = cached,
                loading = false,
                error = if (cached.isEmpty()) "Notifikasi belum dapat dimuat." else "Menampilkan notifikasi tersimpan.",
            )
        }
    }
    fun markRead(item: NotificationItem) = viewModelScope.launch {
        runCatching { api.markNotificationRead(item.id) }.onSuccess { refresh() }
    }
}

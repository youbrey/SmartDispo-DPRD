package id.go.bitungkota.dprd.smartdispo.feature.settings

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import id.go.bitungkota.dprd.smartdispo.core.database.OfflineCache
import id.go.bitungkota.dprd.smartdispo.core.network.ServerConfigStore
import id.go.bitungkota.dprd.smartdispo.core.network.ServerUrlNormalizer
import id.go.bitungkota.dprd.smartdispo.core.network.TokenStore
import java.util.concurrent.TimeUnit
import javax.inject.Inject
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import okhttp3.HttpUrl.Companion.toHttpUrl
import okhttp3.OkHttpClient
import okhttp3.Request

data class ServerSettingsUiState(
    val input: String = "",
    val testing: Boolean = false,
    val connected: Boolean = false,
    val message: String? = null,
)

@HiltViewModel
class ServerSettingsViewModel @Inject constructor(
    private val serverConfigStore: ServerConfigStore,
    private val tokenStore: TokenStore,
    private val cache: OfflineCache,
) : ViewModel() {
    private val probeClient = OkHttpClient.Builder()
        .connectTimeout(8, TimeUnit.SECONDS)
        .readTimeout(8, TimeUnit.SECONDS)
        .callTimeout(10, TimeUnit.SECONDS)
        .build()
    private val _state = MutableStateFlow(ServerSettingsUiState())
    val state: StateFlow<ServerSettingsUiState> = _state.asStateFlow()

    init {
        open()
    }

    fun open() {
        viewModelScope.launch {
            _state.value = ServerSettingsUiState(input = serverConfigStore.apiBaseUrl.first())
        }
    }

    fun updateInput(value: String) {
        _state.value = _state.value.copy(input = value, connected = false, message = null)
    }

    fun testAndSave() = viewModelScope.launch {
        _state.value = _state.value.copy(testing = true, connected = false, message = null)
        runCatching {
            val normalized = ServerUrlNormalizer.normalize(_state.value.input)
            val healthUrl = normalized.toHttpUrl().newBuilder().encodedPath("/health").build()
            withContext(Dispatchers.IO) {
                probeClient.newCall(Request.Builder().url(healthUrl).get().build()).execute().use { response ->
                    require(response.isSuccessful) { "Server merespons HTTP ${response.code}." }
                }
            }
            val previous = serverConfigStore.currentBaseUrl()
            val saved = serverConfigStore.save(normalized)
            if (saved != previous) {
                tokenStore.clear()
                cache.clear()
            }
            saved
        }.onSuccess { saved ->
            _state.value = ServerSettingsUiState(
                input = saved,
                connected = true,
                message = "Server aktif dan alamat telah disimpan.",
            )
        }.onFailure { error ->
            _state.value = _state.value.copy(
                testing = false,
                connected = false,
                message = error.message ?: "Server tidak dapat dihubungi.",
            )
        }
    }
}

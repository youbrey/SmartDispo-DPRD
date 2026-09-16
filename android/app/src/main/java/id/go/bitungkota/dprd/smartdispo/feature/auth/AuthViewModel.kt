package id.go.bitungkota.dprd.smartdispo.feature.auth

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import dagger.hilt.android.qualifiers.ApplicationContext
import android.content.Context
import id.go.bitungkota.dprd.smartdispo.core.model.DeviceRegistration
import id.go.bitungkota.dprd.smartdispo.core.model.RefreshRequest
import id.go.bitungkota.dprd.smartdispo.core.network.SmartDispoApi
import id.go.bitungkota.dprd.smartdispo.core.network.TokenStore
import id.go.bitungkota.dprd.smartdispo.core.security.deviceFingerprint
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

data class AuthUiState(val loading: Boolean = false, val authenticated: Boolean = false, val error: String? = null)

@HiltViewModel
class AuthViewModel @Inject constructor(
    private val api: SmartDispoApi,
    private val tokenStore: TokenStore,
    @ApplicationContext private val context: Context,
) : ViewModel() {
    private val _state = MutableStateFlow(AuthUiState())
    val state: StateFlow<AuthUiState> = _state.asStateFlow()

    init {
        viewModelScope.launch {
            tokenStore.accessToken.collect { token ->
                _state.value = _state.value.copy(authenticated = !token.isNullOrBlank())
            }
        }
    }

    fun login(username: String, password: String) = viewModelScope.launch {
        if (username.isBlank() || password.isBlank()) {
            _state.value = AuthUiState(error = "Nama pengguna dan kata sandi wajib diisi")
            return@launch
        }
        _state.value = AuthUiState(loading = true)
        runCatching { api.login(username.trim(), password) }
            .onSuccess {
                tokenStore.save(it.accessToken, it.refreshToken)
                runCatching {
                    api.registerDevice(DeviceRegistration(deviceFingerprint(context)))
                }
                _state.value = AuthUiState(authenticated = true)
            }
            .onFailure { _state.value = AuthUiState(error = "Login gagal. Periksa akun atau jaringan.") }
    }

    fun logout() = viewModelScope.launch {
        val refresh = tokenStore.refreshToken.first()
        if (refresh != null) runCatching { api.logout(RefreshRequest(refresh)) }
        tokenStore.clear()
    }
}

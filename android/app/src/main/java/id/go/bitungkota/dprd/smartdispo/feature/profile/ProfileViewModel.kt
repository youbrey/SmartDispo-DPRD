package id.go.bitungkota.dprd.smartdispo.feature.profile

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import id.go.bitungkota.dprd.smartdispo.core.model.RegisteredDevice
import id.go.bitungkota.dprd.smartdispo.core.model.UserProfile
import id.go.bitungkota.dprd.smartdispo.core.network.SmartDispoApi
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

data class ProfileUiState(
    val profile: UserProfile? = null,
    val devices: List<RegisteredDevice> = emptyList(),
    val loading: Boolean = true,
    val error: String? = null,
)

@HiltViewModel
class ProfileViewModel @Inject constructor(private val api: SmartDispoApi) : ViewModel() {
    private val _state = MutableStateFlow(ProfileUiState())
    val state: StateFlow<ProfileUiState> = _state.asStateFlow()

    init { refresh() }

    fun refresh() = viewModelScope.launch {
        runCatching { api.me() to api.devices() }.onSuccess { (profile, devices) ->
            _state.value = ProfileUiState(profile = profile, devices = devices, loading = false)
        }.onFailure { _state.value = ProfileUiState(loading = false, error = "Profil belum dapat dimuat.") }
    }

    fun revoke(deviceId: String) = viewModelScope.launch {
        runCatching { api.revokeDevice(deviceId) }.onSuccess { refresh() }
            .onFailure { _state.value = _state.value.copy(error = "Perangkat gagal dicabut.") }
    }
}

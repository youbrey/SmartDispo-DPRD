package id.go.bitungkota.dprd.smartdispo.feature.home

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import id.go.bitungkota.dprd.smartdispo.core.model.WorkflowTask
import id.go.bitungkota.dprd.smartdispo.core.network.SmartDispoApi
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

data class HomeUiState(
    val loading: Boolean = false,
    val tasks: List<WorkflowTask> = emptyList(),
    val fullName: String = "",
    val permissions: Set<String> = emptySet(),
    val error: String? = null,
)

@HiltViewModel
class HomeViewModel @Inject constructor(private val api: SmartDispoApi) : ViewModel() {
    private val _state = MutableStateFlow(HomeUiState())
    val state: StateFlow<HomeUiState> = _state.asStateFlow()

    fun refresh() = viewModelScope.launch {
        _state.value = _state.value.copy(loading = true, error = null)
        runCatching { api.me() to api.myTasks() }
            .onSuccess { (profile, tasks) ->
                _state.value = HomeUiState(
                    tasks = tasks,
                    fullName = profile.fullName,
                    permissions = profile.permissions.toSet(),
                )
            }
            .onFailure { _state.value = HomeUiState(error = "Tugas belum dapat dimuat") }
    }
}

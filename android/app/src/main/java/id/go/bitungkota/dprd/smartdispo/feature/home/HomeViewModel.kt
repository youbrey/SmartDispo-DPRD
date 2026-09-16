package id.go.bitungkota.dprd.smartdispo.feature.home

import android.content.Context
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import dagger.hilt.android.qualifiers.ApplicationContext
import id.go.bitungkota.dprd.smartdispo.core.model.TaskActionRequest
import id.go.bitungkota.dprd.smartdispo.core.model.WorkflowTask
import id.go.bitungkota.dprd.smartdispo.core.network.SmartDispoApi
import id.go.bitungkota.dprd.smartdispo.core.security.deviceFingerprint
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
    val activeRoleCodes: Set<String> = emptySet(),
    val actingTaskId: String? = null,
    val message: String? = null,
    val error: String? = null,
)

@HiltViewModel
class HomeViewModel @Inject constructor(
    private val api: SmartDispoApi,
    @ApplicationContext private val context: Context,
) : ViewModel() {
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
                    activeRoleCodes = profile.activeRoleCodes.toSet(),
                )
            }
            .onFailure { _state.value = HomeUiState(error = "Tugas belum dapat dimuat") }
    }

    fun execute(task: WorkflowTask, action: String, note: String?) = viewModelScope.launch {
        _state.value = _state.value.copy(actingTaskId = task.id, error = null, message = null)
        runCatching {
            api.executeTask(
                task.id,
                TaskActionRequest(
                    action = action,
                    note = note?.trim()?.ifBlank { null },
                    expectedInstanceLockVersion = task.instanceLockVersion,
                    deviceId = deviceFingerprint(context),
                ),
            )
        }.onSuccess {
            refresh()
            _state.value = _state.value.copy(message = "Tindakan $action berhasil disimpan.")
        }.onFailure {
            _state.value = _state.value.copy(
                actingTaskId = null,
                error = "Tindakan gagal. Muat ulang tugas dan periksa catatan wajib.",
            )
        }
    }
}

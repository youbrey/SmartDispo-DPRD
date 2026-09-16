package id.go.bitungkota.dprd.smartdispo.feature.home

import android.content.Context
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import dagger.hilt.android.qualifiers.ApplicationContext
import id.go.bitungkota.dprd.smartdispo.core.model.TaskActionRequest
import id.go.bitungkota.dprd.smartdispo.core.model.WorkflowTask
import id.go.bitungkota.dprd.smartdispo.core.network.SmartDispoApi
import id.go.bitungkota.dprd.smartdispo.core.network.ConnectivityMonitor
import id.go.bitungkota.dprd.smartdispo.core.database.OfflineCache
import id.go.bitungkota.dprd.smartdispo.core.model.UserProfile
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
    val online: Boolean = true,
    val cached: Boolean = false,
)

@HiltViewModel
class HomeViewModel @Inject constructor(
    private val api: SmartDispoApi,
    private val cache: OfflineCache,
    private val connectivity: ConnectivityMonitor,
    @ApplicationContext private val context: Context,
) : ViewModel() {
    private val _state = MutableStateFlow(HomeUiState())
    val state: StateFlow<HomeUiState> = _state.asStateFlow()

    fun refresh() = viewModelScope.launch {
        _state.value = _state.value.copy(loading = true, error = null)
        runCatching { api.me() to api.myTasks() }
            .onSuccess { (profile, tasks) ->
                cache.write("profile", profile)
                cache.write("tasks", tasks)
                _state.value = HomeUiState(
                    tasks = tasks,
                    fullName = profile.fullName,
                    permissions = profile.permissions.toSet(),
                    activeRoleCodes = profile.activeRoleCodes.toSet(),
                    online = true,
                )
            }
            .onFailure {
                val profile = cache.read<UserProfile>("profile")
                val tasks = cache.read<List<WorkflowTask>>("tasks").orEmpty()
                _state.value = HomeUiState(
                    tasks = tasks,
                    fullName = profile?.fullName.orEmpty(),
                    permissions = profile?.permissions?.toSet().orEmpty(),
                    activeRoleCodes = profile?.activeRoleCodes?.toSet().orEmpty(),
                    online = false,
                    cached = profile != null || tasks.isNotEmpty(),
                    error = if (profile == null && tasks.isEmpty()) "Tugas belum dapat dimuat" else null,
                )
            }
    }

    fun execute(task: WorkflowTask, action: String, note: String?) = viewModelScope.launch {
        if (!connectivity.isOnline()) {
            _state.value = _state.value.copy(
                online = false,
                error = "Aksi $action wajib dilakukan saat perangkat online.",
            )
            return@launch
        }
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

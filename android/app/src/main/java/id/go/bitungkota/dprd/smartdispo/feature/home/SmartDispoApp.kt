package id.go.bitungkota.dprd.smartdispo.feature.home

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.ChatBubbleOutline
import androidx.compose.material.icons.outlined.Description
import androidx.compose.material.icons.outlined.Home
import androidx.compose.material.icons.outlined.Notifications
import androidx.compose.material.icons.outlined.Person
import androidx.compose.material.icons.outlined.TaskAlt
import androidx.compose.material3.Badge
import androidx.compose.material3.BadgedBox
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import id.go.bitungkota.dprd.smartdispo.feature.auth.AuthViewModel
import id.go.bitungkota.dprd.smartdispo.feature.auth.LoginScreen
import id.go.bitungkota.dprd.smartdispo.feature.chat.ChatScreen
import id.go.bitungkota.dprd.smartdispo.feature.documents.DocumentDetailScreen
import id.go.bitungkota.dprd.smartdispo.feature.meeting.MeetingRequestScreen
import id.go.bitungkota.dprd.smartdispo.feature.letters.LettersScreen
import id.go.bitungkota.dprd.smartdispo.feature.profile.ProfileScreen
import id.go.bitungkota.dprd.smartdispo.feature.notifications.NotificationsScreen
import id.go.bitungkota.dprd.smartdispo.feature.settings.ServerSettingsDialog
import id.go.bitungkota.dprd.smartdispo.feature.travel.TravelRequestScreen
import id.go.bitungkota.dprd.smartdispo.core.model.WorkflowTask

private data class NavItem(val label: String, val icon: ImageVector)

@Composable
fun SmartDispoApp(authViewModel: AuthViewModel = hiltViewModel()) {
    val auth by authViewModel.state.collectAsStateWithLifecycle()
    var configuringServer by remember { mutableStateOf(false) }
    if (!auth.authenticated) {
        LoginScreen(auth, authViewModel::login, onConfigureServer = { configuringServer = true })
    } else {
        MainScaffold(
            onLogout = authViewModel::logout,
            onConfigureServer = { configuringServer = true },
        )
    }
    if (configuringServer) {
        ServerSettingsDialog(onDismiss = { configuringServer = false })
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun MainScaffold(
    onLogout: () -> Unit,
    onConfigureServer: () -> Unit,
    homeViewModel: HomeViewModel = hiltViewModel(),
) {
    val state by homeViewModel.state.collectAsStateWithLifecycle()
    var selected by remember { mutableIntStateOf(0) }
    var creatingMeeting by remember { mutableStateOf(false) }
    var creatingTravel by remember { mutableStateOf(false) }
    var editingMeetingId by remember { mutableStateOf<String?>(null) }
    var editingTravelId by remember { mutableStateOf<String?>(null) }
    var showingNotifications by remember { mutableStateOf(false) }
    var selectedDocumentId by remember { mutableStateOf<String?>(null) }
    val items = listOf(
        NavItem("Home", Icons.Outlined.Home),
        NavItem("Tugas", Icons.Outlined.TaskAlt),
        NavItem("Surat", Icons.Outlined.Description),
        NavItem("Chat", Icons.Outlined.ChatBubbleOutline),
        NavItem("Profil", Icons.Outlined.Person),
    )
    LaunchedEffect(Unit) { homeViewModel.refresh() }
    if (creatingMeeting || editingMeetingId != null) {
        MeetingRequestScreen(onBack = {
            creatingMeeting = false
            editingMeetingId = null
            homeViewModel.refresh()
        }, onPreview = { documentId -> creatingMeeting = false; editingMeetingId = null; selectedDocumentId = documentId }, editDocumentId = editingMeetingId)
        return
    }
    if (creatingTravel || editingTravelId != null) {
        TravelRequestScreen(onBack = {
            creatingTravel = false
            editingTravelId = null
            homeViewModel.refresh()
        }, onPreview = { documentId -> creatingTravel = false; editingTravelId = null; selectedDocumentId = documentId }, editDocumentId = editingTravelId)
        return
    }
    if (showingNotifications) {
        NotificationsScreen(onBack = { showingNotifications = false })
        return
    }
    selectedDocumentId?.let { documentId ->
        DocumentDetailScreen(
            documentId = documentId,
            onBack = { selectedDocumentId = null },
            canUpload = "document.upload" in state.permissions,
        )
        return
    }
    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("SmartDispo DPRD") },
                actions = {
                    IconButton(onClick = { showingNotifications = true }) {
                        Icon(Icons.Outlined.Notifications, contentDescription = "Notifikasi")
                    }
                },
            )
        },
        bottomBar = {
            NavigationBar {
                items.forEachIndexed { index, item ->
                    NavigationBarItem(
                        selected = selected == index,
                        onClick = { selected = index },
                        icon = {
                            if (index == 1 && state.tasks.isNotEmpty()) {
                                BadgedBox(badge = { Badge { Text(state.tasks.size.toString()) } }) {
                                    Icon(item.icon, contentDescription = item.label)
                                }
                            } else Icon(item.icon, contentDescription = item.label)
                        },
                        label = { Text(item.label) },
                    )
                }
            }
        },
    ) { padding ->
        when (selected) {
            0 -> Dashboard(
                state,
                Modifier.padding(padding),
                onCreateMeeting = { creatingMeeting = true },
                onCreateTravel = { creatingTravel = true },
            )
            1 -> TaskList(
                state,
                Modifier.padding(padding),
                homeViewModel::execute,
                onOpenDocument = { task -> selectedDocumentId = task.documentId },
            )
            2 -> LettersScreen(
                onOpenDocument = { selectedDocumentId = it },
                onEditDocument = { document ->
                    if (document.documentType == "MEETING_REQUEST") editingMeetingId = document.id
                    if (document.documentType == "TRAVEL_REQUEST") editingTravelId = document.id
                },
                canCreateIncoming = "incoming_letter.create" in state.permissions,
                canDisposition = "disposition.create" in state.permissions,
                activeRoleCodes = state.activeRoleCodes,
            )
            3 -> ChatScreen()
            4 -> ProfileScreen(onLogout, onConfigureServer)
            else -> ModulePlaceholder(items[selected].label, Modifier.padding(padding))
        }
    }
}

@Composable
private fun Dashboard(
    state: HomeUiState,
    modifier: Modifier = Modifier,
    onCreateMeeting: () -> Unit,
    onCreateTravel: () -> Unit,
) {
    LazyColumn(
        modifier = modifier.fillMaxSize().padding(20.dp),
        verticalArrangement = Arrangement.spacedBy(14.dp),
    ) {
        item {
            Text("Selamat datang", style = androidx.compose.material3.MaterialTheme.typography.headlineSmall)
            if (state.fullName.isNotBlank()) Text(state.fullName)
            Text("Tugas dan dokumen terbaru Anda")
            if (!state.online) {
                Text(
                    "Offline · data tersimpan hanya dapat dibaca; tindakan workflow dinonaktifkan.",
                    color = androidx.compose.material3.MaterialTheme.colorScheme.error,
                )
            }
            Spacer(Modifier.height(16.dp))
            Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                MetricCard("Menunggu", state.tasks.size.toString(), Modifier.weight(1f))
                MetricCard("Urgent", "0", Modifier.weight(1f))
            }
        }
        if ("meeting_request.create" in state.permissions) {
            item {
                Button(onClick = onCreateMeeting, modifier = Modifier.fillMaxWidth()) {
                    Text("Buat Permintaan Rapat")
                }
            }
        }
        if ("travel_request.create" in state.permissions) {
            item {
                Button(onClick = onCreateTravel, modifier = Modifier.fillMaxWidth()) {
                    Text("Buat Permintaan Perjalanan Dinas")
                }
            }
        }
        item { Text("Tugas terbaru", style = androidx.compose.material3.MaterialTheme.typography.titleLarge) }
        if (state.loading) item { CircularProgressIndicator() }
        state.error?.let { message -> item { Text(message) } }
        state.message?.let { message -> item { Text(message, color = androidx.compose.material3.MaterialTheme.colorScheme.primary) } }
        items(state.tasks.take(5), key = { it.id }) {
            TaskCard(it, state.actingTaskId == it.id, state.online, homeViewModelAction = null)
        }
        if (!state.loading && state.tasks.isEmpty()) item { Text("Tidak ada tugas aktif.") }
    }
}

@Composable
private fun MetricCard(label: String, value: String, modifier: Modifier = Modifier) {
    Card(modifier, colors = CardDefaults.cardColors(containerColor = androidx.compose.material3.MaterialTheme.colorScheme.surface)) {
        Column(Modifier.padding(18.dp)) {
            Text(value, style = androidx.compose.material3.MaterialTheme.typography.headlineMedium)
            Text(label)
        }
    }
}

@Composable
private fun TaskList(
    state: HomeUiState,
    modifier: Modifier = Modifier,
    execute: (WorkflowTask, String, String?) -> Unit,
    onOpenDocument: (WorkflowTask) -> Unit,
) {
    LazyColumn(modifier.fillMaxSize().padding(20.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
        item { Text("Tugas Saya", style = androidx.compose.material3.MaterialTheme.typography.headlineSmall) }
        state.message?.let { message -> item { Text(message, color = androidx.compose.material3.MaterialTheme.colorScheme.primary) } }
        state.error?.let { message -> item { Text(message, color = androidx.compose.material3.MaterialTheme.colorScheme.error) } }
        items(state.tasks, key = { it.id }) { task ->
            TaskCard(task, state.actingTaskId == task.id, state.online, execute, onOpenDocument)
        }
    }
}

@Composable
private fun TaskCard(
    task: WorkflowTask,
    busy: Boolean,
    online: Boolean,
    homeViewModelAction: ((WorkflowTask, String, String?) -> Unit)?,
    onOpenDocument: ((WorkflowTask) -> Unit)? = null,
) {
    var pendingAction by remember { mutableStateOf<String?>(null) }
    var note by remember { mutableStateOf("") }
    Card(Modifier.fillMaxWidth()) {
        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text(task.documentTitle, style = androidx.compose.material3.MaterialTheme.typography.titleMedium)
            Text(task.documentType.replace('_', ' '), style = androidx.compose.material3.MaterialTheme.typography.labelMedium)
            Text(task.stepKey.replace('_', ' '), style = androidx.compose.material3.MaterialTheme.typography.titleMedium)
            Text(task.status)
            onOpenDocument?.let { open ->
                OutlinedButton(onClick = { open(task) }) { Text("Buka Dokumen") }
            }
            if (homeViewModelAction == null) {
                Text(task.availableActions.joinToString(" • "), color = androidx.compose.material3.MaterialTheme.colorScheme.primary)
            } else {
                task.availableActions.chunked(2).forEach { rowActions ->
                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        rowActions.forEach { action ->
                            val destructive = action in setOf("RETURN", "REJECT")
                            if (destructive) {
                                OutlinedButton(onClick = { pendingAction = action }, enabled = !busy && online) { Text(actionLabel(action)) }
                            } else {
                                Button(onClick = { pendingAction = action }, enabled = !busy && online) { Text(actionLabel(action)) }
                            }
                        }
                    }
                }
            }
        }
    }
    pendingAction?.let { action ->
        AlertDialog(
            onDismissRequest = { pendingAction = null; note = "" },
            title = { Text(actionLabel(action)) },
            text = {
                Column {
                    Text("Konfirmasi tindakan untuk tugas ini.")
                    OutlinedTextField(
                        value = note,
                        onValueChange = { note = it },
                        label = { Text(if (action in setOf("RETURN", "REJECT")) "Alasan (wajib)" else "Catatan (opsional)") },
                        minLines = 2,
                    )
                }
            },
            confirmButton = {
                TextButton(
                    onClick = { homeViewModelAction?.invoke(task, action, note); pendingAction = null; note = "" },
                    enabled = action !in setOf("RETURN", "REJECT") || note.isNotBlank(),
                ) { Text("Konfirmasi") }
            },
            dismissButton = { TextButton(onClick = { pendingAction = null; note = "" }) { Text("Batal") } },
        )
    }
}

private fun actionLabel(action: String): String = when (action) {
    "SIGN" -> "Paraf / Tanda Tangan"
    "VERIFY" -> "Verifikasi"
    "COORDINATE" -> "Paraf Koordinasi"
    "APPROVE" -> "Setujui"
    "DISPOSITION" -> "Disposisi"
    "FORWARD" -> "Teruskan"
    "COMPLETE" -> "Selesaikan"
    "RETURN" -> "Kembalikan"
    "REJECT" -> "Tolak"
    else -> action.replace('_', ' ').lowercase().replaceFirstChar { it.uppercase() }
}

@Composable
private fun ModulePlaceholder(name: String, modifier: Modifier = Modifier) {
    Column(modifier.fillMaxSize(), horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.Center) {
        Text(name, style = androidx.compose.material3.MaterialTheme.typography.headlineSmall)
        Text("Modul mengikuti permission akun dari server.")
    }
}

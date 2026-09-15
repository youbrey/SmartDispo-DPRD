package id.go.bitungkota.dprd.smartdispo.feature.home

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.weight
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.ChatBubbleOutline
import androidx.compose.material.icons.outlined.Description
import androidx.compose.material.icons.outlined.Home
import androidx.compose.material.icons.outlined.Person
import androidx.compose.material.icons.outlined.TaskAlt
import androidx.compose.material3.Badge
import androidx.compose.material3.BadgedBox
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
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

private data class NavItem(val label: String, val icon: ImageVector)

@Composable
fun SmartDispoApp(authViewModel: AuthViewModel = hiltViewModel()) {
    val auth by authViewModel.state.collectAsStateWithLifecycle()
    if (!auth.authenticated) {
        LoginScreen(auth, authViewModel::login)
    } else {
        MainScaffold()
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun MainScaffold(homeViewModel: HomeViewModel = hiltViewModel()) {
    val state by homeViewModel.state.collectAsStateWithLifecycle()
    var selected by remember { mutableIntStateOf(0) }
    val items = listOf(
        NavItem("Home", Icons.Outlined.Home),
        NavItem("Tugas", Icons.Outlined.TaskAlt),
        NavItem("Surat", Icons.Outlined.Description),
        NavItem("Chat", Icons.Outlined.ChatBubbleOutline),
        NavItem("Profil", Icons.Outlined.Person),
    )
    LaunchedEffect(Unit) { homeViewModel.refresh() }
    Scaffold(
        topBar = { TopAppBar(title = { Text("SmartDispo DPRD") }) },
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
            0 -> Dashboard(state, Modifier.padding(padding))
            1 -> TaskList(state, Modifier.padding(padding))
            else -> ModulePlaceholder(items[selected].label, Modifier.padding(padding))
        }
    }
}

@Composable
private fun Dashboard(state: HomeUiState, modifier: Modifier = Modifier) {
    LazyColumn(
        modifier = modifier.fillMaxSize().padding(20.dp),
        verticalArrangement = Arrangement.spacedBy(14.dp),
    ) {
        item {
            Text("Selamat datang", style = androidx.compose.material3.MaterialTheme.typography.headlineSmall)
            Text("Tugas dan dokumen terbaru Anda")
            Spacer(Modifier.height(16.dp))
            Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                MetricCard("Menunggu", state.tasks.size.toString(), Modifier.weight(1f))
                MetricCard("Urgent", "0", Modifier.weight(1f))
            }
        }
        item { Text("Tugas terbaru", style = androidx.compose.material3.MaterialTheme.typography.titleLarge) }
        if (state.loading) item { CircularProgressIndicator() }
        state.error?.let { message -> item { Text(message) } }
        items(state.tasks.take(5), key = { it.id }) { TaskCard(it.stepKey, it.status, it.availableActions) }
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
private fun TaskList(state: HomeUiState, modifier: Modifier = Modifier) {
    LazyColumn(modifier.fillMaxSize().padding(20.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
        item { Text("Tugas Saya", style = androidx.compose.material3.MaterialTheme.typography.headlineSmall) }
        items(state.tasks, key = { it.id }) { TaskCard(it.stepKey, it.status, it.availableActions) }
    }
}

@Composable
private fun TaskCard(step: String, status: String, actions: List<String>) {
    Card(Modifier.fillMaxWidth()) {
        Column(Modifier.padding(16.dp)) {
            Text(step.replace('_', ' '), style = androidx.compose.material3.MaterialTheme.typography.titleMedium)
            Text(status)
            Text(actions.joinToString(" • "), color = androidx.compose.material3.MaterialTheme.colorScheme.primary)
        }
    }
}

@Composable
private fun ModulePlaceholder(name: String, modifier: Modifier = Modifier) {
    Column(modifier.fillMaxSize(), horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.Center) {
        Text(name, style = androidx.compose.material3.MaterialTheme.typography.headlineSmall)
        Text("Modul mengikuti permission akun dari server.")
    }
}

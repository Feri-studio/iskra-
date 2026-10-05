package com.iskra.app.ui.screens

import android.content.Intent
import android.net.Uri
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.Download
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import androidx.lifecycle.viewmodel.compose.viewModel
import com.iskra.app.data.model.Project
import com.iskra.app.data.repository.IskraRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

data class ProjectsState(
    val projects: List<Project> = emptyList(),
    val isLoading: Boolean = false,
    val error: String? = null,
)

class ProjectsViewModel : ViewModel() {
    private val repo = IskraRepository()
    private val _state = MutableStateFlow(ProjectsState())
    val state = _state.asStateFlow()

    fun load() {
        viewModelScope.launch {
            _state.value = _state.value.copy(isLoading = true, error = null)
            try {
                val list = repo.listProjects()
                _state.value = ProjectsState(projects = list, isLoading = false)
            } catch (e: Exception) {
                _state.value = _state.value.copy(isLoading = false, error = e.message)
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ProjectsScreen(
    onBack: () -> Unit,
    viewModel: ProjectsViewModel = viewModel()
) {
    val state by viewModel.state.collectAsState()
    val context = LocalContext.current

    LaunchedEffect(Unit) { viewModel.load() }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Проекты") },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Назад")
                    }
                }
            )
        }
    ) { padding ->
        Box(Modifier.fillMaxSize().padding(padding)) {
            when {
                state.isLoading -> CircularProgressIndicator(Modifier.align(Alignment.Center))
                state.error != null -> Text(
                    state.error ?: "",
                    color = MaterialTheme.colorScheme.error,
                    modifier = Modifier.align(Alignment.Center).padding(16.dp)
                )
                state.projects.isEmpty() -> Text(
                    "Пока нет проектов.\nПопроси Искру что-нибудь создать в чате.",
                    modifier = Modifier.align(Alignment.Center).padding(24.dp)
                )
                else -> LazyColumn(
                    contentPadding = PaddingValues(12.dp),
                    verticalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    items(state.projects, key = { it.id }) { project ->
                        Card(Modifier = Modifier.fillMaxWidth()) {
                            Row(
                                Modifier.padding(16.dp).fillMaxWidth(),
                                horizontalArrangement = Arrangement.SpaceBetween,
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                Column(Modifier.weight(1f)) {
                                    Text(project.title, style = MaterialTheme.typography.titleMedium)
                                    Text(
                                        "Статус: ${project.status}",
                                        style = MaterialTheme.typography.bodySmall
                                    )
                                }
                                if (project.status == "ready" || project.file_path != null) {
                                    IconButton(onClick = {
                                        // Открываем download URL в браузере (нужен токен — упрощённо)
                                        val url = "http://10.0.2.2:8000/api/v1/projects/${project.id}/download"
                                        context.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(url)))
                                    }) {
                                        Icon(Icons.Default.Download, contentDescription = "Скачать")
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}

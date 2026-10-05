package com.iskra.app.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.iskra.app.data.api.ApiClient
import com.iskra.app.data.model.Chat
import com.iskra.app.data.model.User
import com.iskra.app.data.repository.IskraRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

data class ChatListState(
    val user: User? = null,
    val chats: List<Chat> = emptyList(),
    val isLoading: Boolean = false,
    val error: String? = null,
)

class ChatListViewModel(
    private val repository: IskraRepository = IskraRepository()
) : ViewModel() {

    private val _state = MutableStateFlow(ChatListState())
    val state: StateFlow<ChatListState> = _state.asStateFlow()

    // В памяти процесса; SessionManager можно подключить позже через Application
    companion object {
        var savedToken: String? = null
        var savedUserId: Long = -1
        var savedExternalId: String = "owner"
    }

    fun load() {
        viewModelScope.launch {
            _state.value = _state.value.copy(isLoading = true, error = null)
            try {
                val login = repository.login(savedExternalId, "Owner")
                savedToken = login.access_token
                savedUserId = login.user.id
                ApiClient.setToken(login.access_token)
                val chats = repository.listChats(login.user.id)
                _state.value = ChatListState(user = login.user, chats = chats, isLoading = false)
            } catch (e: Exception) {
                _state.value = _state.value.copy(
                    isLoading = false,
                    error = e.message ?: "Ошибка загрузки"
                )
            }
        }
    }

    fun createChat(onCreated: (Long) -> Unit) {
        val user = _state.value.user ?: return
        viewModelScope.launch {
            try {
                val chat = repository.createChat(user.id)
                load()
                onCreated(chat.id)
            } catch (e: Exception) {
                _state.value = _state.value.copy(error = e.message)
            }
        }
    }
}

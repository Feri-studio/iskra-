package com.iskra.app.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.iskra.app.data.model.Message
import com.iskra.app.data.repository.IskraRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

data class ChatState(
    val messages: List<Message> = emptyList(),
    val isLoading: Boolean = false,
    val isSending: Boolean = false,
    val error: String? = null,
    val input: String = "",
)

class ChatViewModel(
    private val chatId: Long,
    private val repository: IskraRepository = IskraRepository()
) : ViewModel() {

    private val _state = MutableStateFlow(ChatState())
    val state: StateFlow<ChatState> = _state.asStateFlow()

    init {
        loadMessages()
    }

    fun loadMessages() {
        viewModelScope.launch {
            _state.value = _state.value.copy(isLoading = true, error = null)
            try {
                val messages = repository.listMessages(chatId)
                _state.value = _state.value.copy(messages = messages, isLoading = false)
            } catch (e: Exception) {
                _state.value = _state.value.copy(
                    isLoading = false,
                    error = e.message ?: "Не удалось загрузить сообщения"
                )
            }
        }
    }

    fun onInputChange(text: String) {
        _state.value = _state.value.copy(input = text)
    }

    fun sendMessage() {
        val text = _state.value.input.trim()
        if (text.isEmpty() || _state.value.isSending) return

        viewModelScope.launch {
            _state.value = _state.value.copy(isSending = true, error = null, input = "")
            try {
                repository.sendMessage(chatId, text)
                // Перезагружаем историю (там уже будет и наш, и ответ Искры)
                val messages = repository.listMessages(chatId)
                _state.value = _state.value.copy(messages = messages, isSending = false)
            } catch (e: Exception) {
                _state.value = _state.value.copy(
                    isSending = false,
                    error = e.message ?: "Ошибка отправки",
                    input = text // возвращаем текст обратно
                )
            }
        }
    }
}

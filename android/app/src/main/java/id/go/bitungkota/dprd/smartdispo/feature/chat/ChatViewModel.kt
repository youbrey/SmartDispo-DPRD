package id.go.bitungkota.dprd.smartdispo.feature.chat

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import id.go.bitungkota.dprd.smartdispo.core.model.ChatMessage
import id.go.bitungkota.dprd.smartdispo.core.model.ChatMessageCreate
import id.go.bitungkota.dprd.smartdispo.core.model.ChatRoom
import id.go.bitungkota.dprd.smartdispo.core.network.SmartDispoApi
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

data class ChatUiState(
    val rooms: List<ChatRoom> = emptyList(),
    val selectedRoom: ChatRoom? = null,
    val messages: List<ChatMessage> = emptyList(),
    val draft: String = "",
    val loading: Boolean = true,
    val sending: Boolean = false,
    val error: String? = null,
)

@HiltViewModel
class ChatViewModel @Inject constructor(private val api: SmartDispoApi) : ViewModel() {
    private val _state = MutableStateFlow(ChatUiState())
    val state: StateFlow<ChatUiState> = _state.asStateFlow()

    init { refreshRooms() }

    fun refreshRooms() = viewModelScope.launch {
        runCatching { api.chatRooms() }.onSuccess { rooms ->
            _state.value = _state.value.copy(rooms = rooms, loading = false, error = null)
            if (_state.value.selectedRoom == null && rooms.isNotEmpty()) selectRoom(rooms.first())
        }.onFailure { _state.value = _state.value.copy(loading = false, error = "Ruang chat belum dapat dimuat.") }
    }

    fun selectRoom(room: ChatRoom) {
        _state.value = _state.value.copy(selectedRoom = room, messages = emptyList(), loading = true)
        refreshMessages()
    }

    fun refreshMessages() = viewModelScope.launch {
        val room = _state.value.selectedRoom ?: return@launch
        runCatching { api.chatMessages(room.id) }.onSuccess { messages ->
            _state.value = _state.value.copy(messages = messages, loading = false, error = null)
        }.onFailure { _state.value = _state.value.copy(loading = false, error = "Pesan belum dapat dimuat.") }
    }

    fun updateDraft(value: String) { _state.value = _state.value.copy(draft = value) }

    fun send() = viewModelScope.launch {
        val current = _state.value
        val room = current.selectedRoom ?: return@launch
        val body = current.draft.trim()
        if (body.isEmpty()) return@launch
        _state.value = current.copy(sending = true, error = null)
        runCatching { api.sendChatMessage(room.id, ChatMessageCreate(body)) }.onSuccess {
            _state.value = _state.value.copy(draft = "", sending = false)
            refreshMessages()
        }.onFailure { _state.value = _state.value.copy(sending = false, error = "Pesan gagal dikirim.") }
    }
}

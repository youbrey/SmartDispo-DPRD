package id.go.bitungkota.dprd.smartdispo.feature.chat

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import id.go.bitungkota.dprd.smartdispo.core.model.ChatMessage
import id.go.bitungkota.dprd.smartdispo.core.model.ChatMessageCreate
import id.go.bitungkota.dprd.smartdispo.core.model.ChatRoom
import id.go.bitungkota.dprd.smartdispo.core.network.SmartDispoApi
import id.go.bitungkota.dprd.smartdispo.core.network.ChatRealtimeClient
import id.go.bitungkota.dprd.smartdispo.core.database.OfflineCache
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
    val realtimeConnected: Boolean = false,
)

@HiltViewModel
class ChatViewModel @Inject constructor(
    private val api: SmartDispoApi,
    private val realtime: ChatRealtimeClient,
    private val cache: OfflineCache,
) : ViewModel() {
    private val _state = MutableStateFlow(ChatUiState())
    val state: StateFlow<ChatUiState> = _state.asStateFlow()

    init { refreshRooms() }

    fun refreshRooms() = viewModelScope.launch {
        runCatching { api.chatRooms() }.onSuccess { rooms ->
            cache.write("chat_rooms", rooms)
            _state.value = _state.value.copy(rooms = rooms, loading = false, error = null)
            if (_state.value.selectedRoom == null && rooms.isNotEmpty()) selectRoom(rooms.first())
        }.onFailure {
            val rooms = cache.read<List<ChatRoom>>("chat_rooms").orEmpty()
            _state.value = _state.value.copy(
                rooms = rooms,
                loading = false,
                error = if (rooms.isEmpty()) "Ruang chat belum dapat dimuat." else "Menampilkan ruang tersimpan.",
            )
            if (_state.value.selectedRoom == null && rooms.isNotEmpty()) selectRoom(rooms.first())
        }
    }

    fun selectRoom(room: ChatRoom) {
        _state.value = _state.value.copy(selectedRoom = room, messages = emptyList(), loading = true)
        refreshMessages()
        realtime.connect(
            room.id,
            onMessage = { incoming ->
                _state.value = _state.value.copy(
                    messages = (_state.value.messages + incoming).distinctBy(ChatMessage::id),
                )
            },
            onConnected = { connected ->
                _state.value = _state.value.copy(realtimeConnected = connected)
            },
        )
    }

    fun refreshMessages() = viewModelScope.launch {
        val room = _state.value.selectedRoom ?: return@launch
        runCatching { api.chatMessages(room.id) }.onSuccess { messages ->
            cache.write("chat_messages_${room.id}", messages)
            _state.value = _state.value.copy(messages = messages, loading = false, error = null)
        }.onFailure {
            val messages = cache.read<List<ChatMessage>>("chat_messages_${room.id}").orEmpty()
            _state.value = _state.value.copy(
                messages = messages,
                loading = false,
                error = if (messages.isEmpty()) "Pesan belum dapat dimuat." else "Menampilkan pesan tersimpan.",
            )
        }
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
            if (!_state.value.realtimeConnected) refreshMessages()
        }.onFailure { _state.value = _state.value.copy(sending = false, error = "Pesan gagal dikirim.") }
    }

    override fun onCleared() {
        realtime.disconnect()
        super.onCleared()
    }
}

package id.go.bitungkota.dprd.smartdispo.core.network

import id.go.bitungkota.dprd.smartdispo.core.model.ChatMessage
import id.go.bitungkota.dprd.smartdispo.core.model.RealtimeChatEnvelope
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.launch
import kotlinx.serialization.json.Json
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.Response
import okhttp3.WebSocket
import okhttp3.WebSocketListener
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class ChatRealtimeClient @Inject constructor(
    private val client: OkHttpClient,
    private val tokenStore: TokenStore,
    private val serverConfigStore: ServerConfigStore,
    private val json: Json,
) {
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.IO)
    private var socket: WebSocket? = null

    fun connect(
        roomId: String,
        onMessage: (ChatMessage) -> Unit,
        onConnected: (Boolean) -> Unit,
    ) {
        disconnect()
        scope.launch {
            val token = tokenStore.accessToken.first()
            if (token.isNullOrBlank()) {
                onConnected(false)
                return@launch
            }
            val socketUrl = serverConfigStore.currentBaseUrl()
                .replaceFirst("https://", "wss://")
                .replaceFirst("http://", "ws://") +
                "chat/rooms/$roomId/ws?access_token=$token"
            val request = Request.Builder().url(socketUrl).build()
            socket = client.newWebSocket(request, object : WebSocketListener() {
                override fun onOpen(webSocket: WebSocket, response: Response) {
                    onConnected(true)
                }

                override fun onMessage(webSocket: WebSocket, text: String) {
                    runCatching { json.decodeFromString<RealtimeChatEnvelope>(text) }
                        .getOrNull()?.message?.let(onMessage)
                }

                override fun onClosed(webSocket: WebSocket, code: Int, reason: String) {
                    onConnected(false)
                }

                override fun onFailure(webSocket: WebSocket, throwable: Throwable, response: Response?) {
                    onConnected(false)
                }
            })
        }
    }

    fun disconnect() {
        socket?.close(1000, "room changed")
        socket = null
    }
}

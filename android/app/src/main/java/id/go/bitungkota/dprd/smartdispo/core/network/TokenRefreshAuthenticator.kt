package id.go.bitungkota.dprd.smartdispo.core.network

import id.go.bitungkota.dprd.smartdispo.BuildConfig
import id.go.bitungkota.dprd.smartdispo.core.model.RefreshRequest
import id.go.bitungkota.dprd.smartdispo.core.model.TokenPair
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.runBlocking
import kotlinx.serialization.decodeFromString
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json
import okhttp3.Authenticator
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import okhttp3.Response
import okhttp3.Route
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class TokenRefreshAuthenticator @Inject constructor(
    private val tokenStore: TokenStore,
    private val json: Json,
) : Authenticator {
    private val refreshClient = OkHttpClient()

    override fun authenticate(route: Route?, response: Response): Request? = synchronized(this) {
        if (response.request.url.encodedPath.endsWith("/auth/refresh") || responseCount(response) > 1) {
            return@synchronized null
        }
        runBlocking {
            val requestToken = response.request.header("Authorization")?.removePrefix("Bearer ")
            val currentToken = tokenStore.accessToken.first()
            if (!currentToken.isNullOrBlank() && currentToken != requestToken) {
                return@runBlocking response.request.newBuilder()
                    .header("Authorization", "Bearer $currentToken")
                    .build()
            }
            val refresh = tokenStore.refreshToken.first() ?: return@runBlocking null
            val body = json.encodeToString(RefreshRequest(refresh))
                .toRequestBody("application/json".toMediaType())
            val refreshRequest = Request.Builder()
                .url("${BuildConfig.API_BASE_URL}auth/refresh")
                .post(body)
                .build()
            refreshClient.newCall(refreshRequest).execute().use { refreshResponse ->
                if (!refreshResponse.isSuccessful) {
                    tokenStore.clear()
                    return@runBlocking null
                }
                val payload = refreshResponse.body?.string() ?: return@runBlocking null
                val pair = json.decodeFromString<TokenPair>(payload)
                tokenStore.save(pair.accessToken, pair.refreshToken)
                response.request.newBuilder()
                    .header("Authorization", "Bearer ${pair.accessToken}")
                    .build()
            }
        }
    }

    private fun responseCount(response: Response): Int {
        var count = 1
        var prior = response.priorResponse
        while (prior != null) {
            count += 1
            prior = prior.priorResponse
        }
        return count
    }
}

package id.go.bitungkota.dprd.smartdispo.core.network

import android.content.Context
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import dagger.hilt.android.qualifiers.ApplicationContext
import id.go.bitungkota.dprd.smartdispo.BuildConfig
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.map
import okhttp3.HttpUrl.Companion.toHttpUrlOrNull
import javax.inject.Inject
import javax.inject.Singleton

private val Context.serverConfigDataStore by preferencesDataStore(name = "server_config")

object ServerUrlNormalizer {
    private val privateIpv4 = Regex(
        "^(10\\.|127\\.|192\\.168\\.|172\\.(1[6-9]|2[0-9]|3[01])\\.|10\\.0\\.2\\.2$)"
    )

    fun normalize(rawValue: String): String {
        val trimmed = rawValue.trim().trimEnd('/')
        require(trimmed.isNotBlank()) { "Alamat server wajib diisi." }

        val withScheme = if (trimmed.contains("://")) {
            trimmed
        } else {
            val authority = trimmed.substringBefore('/')
            val host = authority.substringBefore(':').lowercase()
            val scheme = if (host == "localhost" || privateIpv4.containsMatchIn(host)) "http" else "https"
            "$scheme://$trimmed"
        }
        val parsed = withScheme.toHttpUrlOrNull()
            ?: throw IllegalArgumentException("Format alamat server tidak valid.")
        require(parsed.scheme == "http" || parsed.scheme == "https") {
            "Alamat server harus menggunakan HTTP atau HTTPS."
        }
        require(parsed.username.isEmpty() && parsed.password.isEmpty()) {
            "Alamat server tidak boleh memuat nama pengguna atau kata sandi."
        }
        require(parsed.query == null && parsed.fragment == null) {
            "Alamat server tidak boleh memuat query atau fragment."
        }

        val path = parsed.encodedPath.trim('/')
        require(path.isEmpty() || path == "api/v1") {
            "Gunakan alamat utama server atau akhiri dengan /api/v1/."
        }
        return parsed.newBuilder()
            .encodedPath("/api/v1/")
            .build()
            .toString()
    }
}

@Singleton
class ServerConfigStore @Inject constructor(
    @ApplicationContext private val context: Context,
) {
    private val serverUrlKey = stringPreferencesKey("api_base_url")

    val apiBaseUrl: Flow<String> = context.serverConfigDataStore.data.map { preferences ->
        preferences[serverUrlKey] ?: BuildConfig.API_BASE_URL
    }

    suspend fun currentBaseUrl(): String = apiBaseUrl.first()

    suspend fun save(rawValue: String): String {
        val normalized = ServerUrlNormalizer.normalize(rawValue)
        context.serverConfigDataStore.edit { it[serverUrlKey] = normalized }
        return normalized
    }
}

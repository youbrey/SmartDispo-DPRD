package id.go.bitungkota.dprd.smartdispo.core.network

import android.content.Context
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import javax.inject.Inject
import javax.inject.Singleton

private val Context.authDataStore by preferencesDataStore(name = "secure_session")

@Singleton
class TokenStore @Inject constructor(
    @ApplicationContext private val context: Context,
    private val cipher: SessionCipher,
) {
    private val accessKey = stringPreferencesKey("access_token")
    private val refreshKey = stringPreferencesKey("refresh_token")

    val accessToken: Flow<String?> = context.authDataStore.data.map { preferences ->
        preferences[accessKey]?.let { encrypted -> runCatching { cipher.decrypt(encrypted) }.getOrNull() }
    }

    val refreshToken: Flow<String?> = context.authDataStore.data.map { preferences ->
        preferences[refreshKey]?.let { encrypted -> runCatching { cipher.decrypt(encrypted) }.getOrNull() }
    }

    suspend fun save(access: String, refresh: String) {
        context.authDataStore.edit {
            it[accessKey] = cipher.encrypt(access)
            it[refreshKey] = cipher.encrypt(refresh)
        }
    }

    suspend fun clear() = context.authDataStore.edit { it.clear() }
}

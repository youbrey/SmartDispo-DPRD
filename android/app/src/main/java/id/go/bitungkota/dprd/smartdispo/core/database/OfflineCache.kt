package id.go.bitungkota.dprd.smartdispo.core.database

import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class OfflineCache @Inject constructor(
    @PublishedApi internal val dao: CacheDao,
    @PublishedApi internal val json: Json,
) {
    internal suspend inline fun <reified T> read(key: String): T? =
        dao.get(key)?.let { payload -> runCatching { json.decodeFromString<T>(payload) }.getOrNull() }

    internal suspend inline fun <reified T> write(key: String, value: T) {
        dao.put(CacheEntry(key, json.encodeToString(value), System.currentTimeMillis()))
    }

    suspend fun clear() = dao.clear()
}

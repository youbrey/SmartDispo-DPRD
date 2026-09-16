package id.go.bitungkota.dprd.smartdispo.core.database

import androidx.room.Dao
import androidx.room.Database
import androidx.room.Entity
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.PrimaryKey
import androidx.room.Query
import androidx.room.RoomDatabase

@Entity(tableName = "read_cache")
data class CacheEntry(
    @PrimaryKey val cacheKey: String,
    val payload: String,
    val updatedAt: Long,
)

@Dao
interface CacheDao {
    @Query("SELECT payload FROM read_cache WHERE cacheKey = :key")
    suspend fun get(key: String): String?

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun put(entry: CacheEntry)

    @Query("DELETE FROM read_cache")
    suspend fun clear()
}

@Database(entities = [CacheEntry::class], version = 1, exportSchema = true)
abstract class SmartDispoDatabase : RoomDatabase() {
    abstract fun cacheDao(): CacheDao
}

package id.go.bitungkota.dprd.smartdispo.core.database

import android.content.Context
import androidx.room.Room
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.android.qualifiers.ApplicationContext
import dagger.hilt.components.SingletonComponent
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
object DatabaseModule {
    @Provides
    @Singleton
    fun database(@ApplicationContext context: Context): SmartDispoDatabase =
        Room.databaseBuilder(context, SmartDispoDatabase::class.java, "smartdispo-cache.db")
            .fallbackToDestructiveMigration()
            .build()

    @Provides
    fun cacheDao(database: SmartDispoDatabase): CacheDao = database.cacheDao()
}

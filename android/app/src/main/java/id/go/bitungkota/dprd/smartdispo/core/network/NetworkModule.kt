package id.go.bitungkota.dprd.smartdispo.core.network

import android.content.Context
import com.jakewharton.retrofit2.converter.kotlinx.serialization.asConverterFactory
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent
import dagger.hilt.android.qualifiers.ApplicationContext
import id.go.bitungkota.dprd.smartdispo.BuildConfig
import id.go.bitungkota.dprd.smartdispo.core.security.deviceFingerprint
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.runBlocking
import kotlinx.serialization.ExperimentalSerializationApi
import kotlinx.serialization.json.Json
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
object NetworkModule {
    @Provides
    @Singleton
    fun provideJson(): Json = Json { ignoreUnknownKeys = true; explicitNulls = false }

    @Provides
    @Singleton
    fun provideClient(
        tokenStore: TokenStore,
        authenticator: TokenRefreshAuthenticator,
        serverUrlInterceptor: ServerUrlInterceptor,
        @ApplicationContext context: Context,
    ): OkHttpClient = OkHttpClient.Builder()
        .addInterceptor(serverUrlInterceptor)
        .addInterceptor { chain ->
            val token = runBlocking { tokenStore.accessToken.first() }
            val request = chain.request().newBuilder().apply {
                if (!token.isNullOrBlank()) header("Authorization", "Bearer $token")
                header("X-Device-ID", deviceFingerprint(context))
            }.build()
            chain.proceed(request)
        }
        .authenticator(authenticator)
        .apply {
            if (BuildConfig.DEBUG) addInterceptor(
                HttpLoggingInterceptor().apply { level = HttpLoggingInterceptor.Level.BASIC }
            )
        }
        .build()

    @OptIn(ExperimentalSerializationApi::class)
    @Provides
    @Singleton
    fun provideApi(client: OkHttpClient, json: Json): SmartDispoApi = Retrofit.Builder()
        .baseUrl(BuildConfig.API_BASE_URL)
        .client(client)
        .addConverterFactory(json.asConverterFactory("application/json".toMediaType()))
        .build()
        .create(SmartDispoApi::class.java)
}

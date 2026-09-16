package id.go.bitungkota.dprd.smartdispo.core.network

import id.go.bitungkota.dprd.smartdispo.BuildConfig
import kotlinx.coroutines.runBlocking
import okhttp3.HttpUrl.Companion.toHttpUrl
import okhttp3.Interceptor
import okhttp3.Response
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class ServerUrlInterceptor @Inject constructor(
    private val serverConfigStore: ServerConfigStore,
) : Interceptor {
    private val compiledBaseUrl = BuildConfig.API_BASE_URL.toHttpUrl()

    override fun intercept(chain: Interceptor.Chain): Response {
        val configuredBaseUrl = runBlocking { serverConfigStore.currentBaseUrl() }.toHttpUrl()
        val originalRequest = chain.request()
        val originalUrl = originalRequest.url
        val relativePath = originalUrl.encodedPath.removePrefix(compiledBaseUrl.encodedPath)
        val targetUrl = originalUrl.newBuilder()
            .scheme(configuredBaseUrl.scheme)
            .host(configuredBaseUrl.host)
            .port(configuredBaseUrl.port)
            .encodedPath(configuredBaseUrl.encodedPath + relativePath)
            .build()
        return chain.proceed(originalRequest.newBuilder().url(targetUrl).build())
    }
}

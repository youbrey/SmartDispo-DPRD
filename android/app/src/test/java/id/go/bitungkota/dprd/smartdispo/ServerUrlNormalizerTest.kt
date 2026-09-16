package id.go.bitungkota.dprd.smartdispo

import id.go.bitungkota.dprd.smartdispo.core.network.ServerUrlNormalizer
import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Test

class ServerUrlNormalizerTest {
    @Test
    fun privateLanIpDefaultsToHttpAndAddsApiPath() {
        assertEquals(
            "http://192.168.1.10:8000/api/v1/",
            ServerUrlNormalizer.normalize("192.168.1.10:8000"),
        )
    }

    @Test
    fun publicHostnameDefaultsToHttps() {
        assertEquals(
            "https://smartdispo.example.go.id/api/v1/",
            ServerUrlNormalizer.normalize("smartdispo.example.go.id"),
        )
    }

    @Test
    fun existingApiPathIsNotDuplicated() {
        assertEquals(
            "http://10.0.2.2:8000/api/v1/",
            ServerUrlNormalizer.normalize("http://10.0.2.2:8000/api/v1/"),
        )
    }

    @Test
    fun rejectsUnexpectedPath() {
        assertThrows(IllegalArgumentException::class.java) {
            ServerUrlNormalizer.normalize("https://example.go.id/unknown")
        }
    }
}

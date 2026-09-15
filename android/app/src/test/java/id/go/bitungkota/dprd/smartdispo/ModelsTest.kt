package id.go.bitungkota.dprd.smartdispo

import id.go.bitungkota.dprd.smartdispo.core.model.TaskActionRequest
import org.junit.Assert.assertEquals
import org.junit.Test

class ModelsTest {
    @Test
    fun taskActionCarriesConcurrencyVersion() {
        val request = TaskActionRequest("VERIFY", expectedInstanceLockVersion = 3)
        assertEquals(3, request.expectedInstanceLockVersion)
    }
}

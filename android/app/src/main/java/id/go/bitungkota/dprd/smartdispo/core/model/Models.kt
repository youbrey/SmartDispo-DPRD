package id.go.bitungkota.dprd.smartdispo.core.model

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class TokenPair(
    @SerialName("access_token") val accessToken: String,
    @SerialName("refresh_token") val refreshToken: String,
    @SerialName("token_type") val tokenType: String,
)

@Serializable
data class UserProfile(val id: String, val username: String, @SerialName("full_name") val fullName: String)

@Serializable
data class WorkflowTask(
    val id: String,
    @SerialName("step_key") val stepKey: String,
    val status: String,
    @SerialName("available_actions") val availableActions: List<String>,
    @SerialName("instance_lock_version") val instanceLockVersion: Int,
    @SerialName("created_at") val createdAt: String,
)

@Serializable
data class TaskActionRequest(
    val action: String,
    val note: String? = null,
    @SerialName("expected_instance_lock_version") val expectedInstanceLockVersion: Int,
    @SerialName("device_id") val deviceId: String? = null,
)

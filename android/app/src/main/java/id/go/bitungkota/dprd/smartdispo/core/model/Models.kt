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
data class UserProfile(
    val id: String,
    val username: String,
    @SerialName("full_name") val fullName: String,
    val permissions: List<String> = emptyList(),
)

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

@Serializable
data class MeetingType(val code: String, val name: String, @SerialName("sort_order") val sortOrder: Int)

@Serializable
data class MeetingInvitee(val name: String, val institution: String? = null)

@Serializable
data class MeetingRequestCreate(
    @SerialName("sender_name") val senderName: String,
    @SerialName("sender_position") val senderPosition: String,
    @SerialName("meeting_type_code") val meetingTypeCode: String,
    val purpose: String,
    @SerialName("scheduled_at") val scheduledAt: String,
    val place: String,
    val attire: String? = null,
    val invitees: List<MeetingInvitee>,
    val notes: String? = null,
    @SerialName("signer_role_code") val signerRoleCode: String? = null,
)

@Serializable
data class MeetingRequestResponse(
    @SerialName("document_id") val documentId: String,
    @SerialName("document_status") val documentStatus: String,
    val title: String,
    @SerialName("current_version") val currentVersion: Int,
)

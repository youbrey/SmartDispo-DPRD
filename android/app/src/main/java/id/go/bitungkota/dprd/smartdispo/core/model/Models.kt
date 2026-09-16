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
data class RefreshRequest(@SerialName("refresh_token") val refreshToken: String)

@Serializable
data class DeviceRegistration(
    @SerialName("device_fingerprint") val deviceFingerprint: String,
    @SerialName("fcm_token") val fcmToken: String? = null,
)

@Serializable
data class UserProfile(
    val id: String,
    val username: String,
    @SerialName("full_name") val fullName: String,
    val permissions: List<String> = emptyList(),
    @SerialName("role_codes") val roleCodes: List<String> = emptyList(),
    @SerialName("active_role_codes") val activeRoleCodes: List<String> = emptyList(),
)

@Serializable
data class WorkflowTask(
    val id: String,
    @SerialName("document_id") val documentId: String,
    @SerialName("document_title") val documentTitle: String,
    @SerialName("document_type") val documentType: String,
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
    val id: String,
    @SerialName("document_id") val documentId: String,
    @SerialName("document_status") val documentStatus: String,
    val title: String,
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
    @SerialName("current_version") val currentVersion: Int,
    @SerialName("lock_version") val lockVersion: Int,
)

@Serializable
data class MeetingRequestUpdate(
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
    @SerialName("expected_lock_version") val expectedLockVersion: Int,
    @SerialName("change_reason") val changeReason: String,
)

@Serializable
data class TravelMember(
    val name: String,
    val position: String? = null,
    @SerialName("member_group") val memberGroup: String,
)

@Serializable
data class TravelRequestCreate(
    @SerialName("sender_name") val senderName: String,
    @SerialName("sender_position") val senderPosition: String,
    @SerialName("organizational_unit") val organizationalUnit: String,
    @SerialName("activity_type") val activityType: String,
    val destinations: List<String>,
    val purpose: String,
    val material: String,
    @SerialName("general_problem") val generalProblem: String,
    @SerialName("current_condition") val currentCondition: String,
    val efforts: String,
    @SerialName("start_date") val startDate: String,
    @SerialName("end_date") val endDate: String,
    @SerialName("activity_time") val activityTime: String? = null,
    val place: String,
    val members: List<TravelMember>,
    val notes: String? = null,
    @SerialName("signer_role_code") val signerRoleCode: String? = null,
    @SerialName("follow_up_directives") val followUpDirectives: List<String> = emptyList(),
)

@Serializable
data class TravelRequestResponse(
    val id: String,
    @SerialName("document_id") val documentId: String,
    @SerialName("document_status") val documentStatus: String,
    val title: String,
    @SerialName("sender_name") val senderName: String,
    @SerialName("sender_position") val senderPosition: String,
    @SerialName("organizational_unit") val organizationalUnit: String,
    @SerialName("activity_type") val activityType: String,
    val destinations: List<String>,
    val purpose: String,
    val material: String,
    @SerialName("general_problem") val generalProblem: String,
    @SerialName("current_condition") val currentCondition: String,
    val efforts: String,
    @SerialName("start_date") val startDate: String,
    @SerialName("end_date") val endDate: String,
    @SerialName("activity_time") val activityTime: String? = null,
    val place: String,
    val members: List<TravelMember>,
    val notes: String? = null,
    @SerialName("duration_days") val durationDays: Int,
    @SerialName("lock_version") val lockVersion: Int,
)

@Serializable
data class TravelRequestUpdate(
    @SerialName("sender_name") val senderName: String,
    @SerialName("sender_position") val senderPosition: String,
    @SerialName("organizational_unit") val organizationalUnit: String,
    @SerialName("activity_type") val activityType: String,
    val destinations: List<String>,
    val purpose: String,
    val material: String,
    @SerialName("general_problem") val generalProblem: String,
    @SerialName("current_condition") val currentCondition: String,
    val efforts: String,
    @SerialName("start_date") val startDate: String,
    @SerialName("end_date") val endDate: String,
    @SerialName("activity_time") val activityTime: String? = null,
    val place: String,
    val members: List<TravelMember>,
    val notes: String? = null,
    @SerialName("signer_role_code") val signerRoleCode: String? = null,
    @SerialName("follow_up_directives") val followUpDirectives: List<String> = emptyList(),
    @SerialName("expected_lock_version") val expectedLockVersion: Int,
    @SerialName("change_reason") val changeReason: String,
)

@Serializable
data class DocumentSummary(
    val id: String,
    @SerialName("document_number") val documentNumber: String? = null,
    @SerialName("agenda_number") val agendaNumber: String? = null,
    @SerialName("document_type") val documentType: String,
    val status: String,
    val title: String,
    @SerialName("current_version") val currentVersion: Int,
    @SerialName("current_step_key") val currentStepKey: String? = null,
    @SerialName("lock_version") val lockVersion: Int,
    @SerialName("available_actions") val availableActions: List<String> = emptyList(),
    @SerialName("created_at") val createdAt: String,
)

@Serializable
data class IncomingLetterCreate(
    @SerialName("route_type") val routeType: String,
    val sender: String,
    @SerialName("letter_number") val letterNumber: String,
    @SerialName("letter_date") val letterDate: String,
    @SerialName("received_date") val receivedDate: String,
    @SerialName("agenda_number") val agendaNumber: String,
    @SerialName("agenda_date") val agendaDate: String,
    val subject: String,
    val priority: String,
    val notes: String? = null,
)

@Serializable
data class IncomingLetterResponse(
    @SerialName("document_id") val documentId: String,
    @SerialName("document_status") val documentStatus: String,
    val title: String,
)

@Serializable
data class DispositionCreate(
    @SerialName("actor_role") val actorRole: String,
    val directives: List<String>,
    val note: String? = null,
    val targets: List<DispositionTarget> = emptyList(),
)

@Serializable
data class DispositionTarget(
    @SerialName("unit_id") val unitId: String? = null,
    @SerialName("role_id") val roleId: String? = null,
    @SerialName("user_id") val userId: String? = null,
)

@Serializable
data class DispositionResponse(
    val id: String,
    @SerialName("document_id") val documentId: String,
    @SerialName("sheet_type") val sheetType: String,
    @SerialName("actor_role") val actorRole: String,
    val directives: List<String>,
    val note: String? = null,
)

@Serializable
data class NotificationItem(
    val id: String,
    @SerialName("event_type") val eventType: String,
    val title: String,
    val body: String,
    @SerialName("read_at") val readAt: String? = null,
    @SerialName("created_at") val createdAt: String,
)

@Serializable
data class ChatRoom(
    val id: String,
    val name: String,
    @SerialName("document_id") val documentId: String? = null,
    @SerialName("updated_at") val updatedAt: String,
)

@Serializable
data class ChatMessage(
    val id: String,
    @SerialName("sender_id") val senderId: String,
    @SerialName("sender_name") val senderName: String,
    val body: String,
    @SerialName("created_at") val createdAt: String,
)

@Serializable
data class ChatMessageCreate(val body: String)

@Serializable
data class RegisteredDevice(
    val id: String,
    @SerialName("device_fingerprint") val deviceFingerprint: String,
    @SerialName("registered_at") val registeredAt: String,
    @SerialName("revoked_at") val revokedAt: String? = null,
)

@Serializable
data class TimelineItem(
    val id: String,
    @SerialName("event_type") val eventType: String,
    val title: String,
    @SerialName("actor_name") val actorName: String,
    val note: String? = null,
    @SerialName("occurred_at") val occurredAt: String,
)

@Serializable
data class AttachmentItem(
    val id: String,
    @SerialName("original_name") val originalName: String,
    @SerialName("content_type") val contentType: String,
    @SerialName("size_bytes") val sizeBytes: Long,
    @SerialName("sha256_hash") val sha256Hash: String,
    @SerialName("document_version") val documentVersion: Int,
    @SerialName("created_at") val createdAt: String,
)

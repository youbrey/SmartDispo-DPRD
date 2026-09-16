package id.go.bitungkota.dprd.smartdispo.core.network

import id.go.bitungkota.dprd.smartdispo.core.model.TaskActionRequest
import id.go.bitungkota.dprd.smartdispo.core.model.MeetingRequestCreate
import id.go.bitungkota.dprd.smartdispo.core.model.MeetingRequestResponse
import id.go.bitungkota.dprd.smartdispo.core.model.MeetingRequestUpdate
import id.go.bitungkota.dprd.smartdispo.core.model.MeetingType
import id.go.bitungkota.dprd.smartdispo.core.model.DocumentSummary
import id.go.bitungkota.dprd.smartdispo.core.model.DispositionCreate
import id.go.bitungkota.dprd.smartdispo.core.model.DispositionResponse
import id.go.bitungkota.dprd.smartdispo.core.model.IncomingLetterCreate
import id.go.bitungkota.dprd.smartdispo.core.model.IncomingLetterResponse
import id.go.bitungkota.dprd.smartdispo.core.model.TokenPair
import id.go.bitungkota.dprd.smartdispo.core.model.TravelRequestCreate
import id.go.bitungkota.dprd.smartdispo.core.model.TravelRequestResponse
import id.go.bitungkota.dprd.smartdispo.core.model.TravelRequestUpdate
import id.go.bitungkota.dprd.smartdispo.core.model.UserProfile
import id.go.bitungkota.dprd.smartdispo.core.model.WorkflowTask
import id.go.bitungkota.dprd.smartdispo.core.model.ChatMessage
import id.go.bitungkota.dprd.smartdispo.core.model.ChatMessageCreate
import id.go.bitungkota.dprd.smartdispo.core.model.ChatRoom
import id.go.bitungkota.dprd.smartdispo.core.model.NotificationItem
import id.go.bitungkota.dprd.smartdispo.core.model.RegisteredDevice
import id.go.bitungkota.dprd.smartdispo.core.model.AttachmentItem
import id.go.bitungkota.dprd.smartdispo.core.model.TimelineItem
import id.go.bitungkota.dprd.smartdispo.core.model.DeviceRegistration
import id.go.bitungkota.dprd.smartdispo.core.model.RefreshRequest
import okhttp3.MultipartBody
import okhttp3.ResponseBody
import retrofit2.http.Body
import retrofit2.http.Field
import retrofit2.http.FormUrlEncoded
import retrofit2.http.GET
import retrofit2.http.Multipart
import retrofit2.http.PATCH
import retrofit2.http.Part
import retrofit2.http.POST
import retrofit2.http.Path
import retrofit2.http.Streaming

interface SmartDispoApi {
    @FormUrlEncoded
    @POST("auth/login")
    suspend fun login(@Field("username") username: String, @Field("password") password: String): TokenPair

    @POST("auth/logout")
    suspend fun logout(@Body request: RefreshRequest)

    @GET("auth/me")
    suspend fun me(): UserProfile

    @GET("tasks/mine")
    suspend fun myTasks(): List<WorkflowTask>

    @GET("meeting-types")
    suspend fun meetingTypes(): List<MeetingType>

    @POST("meeting-requests")
    suspend fun createMeetingRequest(@Body request: MeetingRequestCreate): MeetingRequestResponse

    @GET("meeting-requests/{documentId}")
    suspend fun meetingRequest(@Path("documentId") documentId: String): MeetingRequestResponse

    @PATCH("meeting-requests/{documentId}")
    suspend fun updateMeetingRequest(
        @Path("documentId") documentId: String,
        @Body request: MeetingRequestUpdate,
    ): MeetingRequestResponse

    @POST("travel-requests")
    suspend fun createTravelRequest(@Body request: TravelRequestCreate): TravelRequestResponse

    @GET("travel-requests/{documentId}")
    suspend fun travelRequest(@Path("documentId") documentId: String): TravelRequestResponse

    @PATCH("travel-requests/{documentId}")
    suspend fun updateTravelRequest(
        @Path("documentId") documentId: String,
        @Body request: TravelRequestUpdate,
    ): TravelRequestResponse

    @GET("documents")
    suspend fun documents(): List<DocumentSummary>

    @GET("documents/{documentId}")
    suspend fun document(@Path("documentId") documentId: String): DocumentSummary

    @POST("documents/{documentId}/submit")
    suspend fun submitDocument(@Path("documentId") documentId: String): DocumentSummary

    @GET("documents/{documentId}/timeline")
    suspend fun documentTimeline(@Path("documentId") documentId: String): List<TimelineItem>

    @Streaming
    @GET("documents/{documentId}/preview")
    suspend fun documentPreview(@Path("documentId") documentId: String): ResponseBody

    @GET("documents/{documentId}/attachments")
    suspend fun attachments(@Path("documentId") documentId: String): List<AttachmentItem>

    @Multipart
    @POST("documents/{documentId}/attachments")
    suspend fun uploadAttachment(
        @Path("documentId") documentId: String,
        @Part upload: MultipartBody.Part,
    )

    @Streaming
    @GET("documents/{documentId}/attachments/{attachmentId}/download")
    suspend fun downloadAttachment(
        @Path("documentId") documentId: String,
        @Path("attachmentId") attachmentId: String,
    ): ResponseBody

    @POST("incoming-letters")
    suspend fun createIncomingLetter(@Body request: IncomingLetterCreate): IncomingLetterResponse

    @POST("documents/{documentId}/dispositions")
    suspend fun createDisposition(
        @Path("documentId") documentId: String,
        @Body request: DispositionCreate,
    ): DispositionResponse

    @POST("tasks/{taskId}/actions")
    suspend fun executeTask(@Path("taskId") taskId: String, @Body request: TaskActionRequest)

    @GET("notifications")
    suspend fun notifications(): List<NotificationItem>

    @POST("notifications/{notificationId}/read")
    suspend fun markNotificationRead(@Path("notificationId") notificationId: String)

    @GET("chat/rooms")
    suspend fun chatRooms(): List<ChatRoom>

    @GET("chat/rooms/{roomId}/messages")
    suspend fun chatMessages(@Path("roomId") roomId: String): List<ChatMessage>

    @POST("chat/rooms/{roomId}/messages")
    suspend fun sendChatMessage(@Path("roomId") roomId: String, @Body request: ChatMessageCreate)

    @GET("devices")
    suspend fun devices(): List<RegisteredDevice>

    @POST("devices/register")
    suspend fun registerDevice(@Body request: DeviceRegistration)

    @POST("devices/{deviceId}/revoke")
    suspend fun revokeDevice(@Path("deviceId") deviceId: String)
}

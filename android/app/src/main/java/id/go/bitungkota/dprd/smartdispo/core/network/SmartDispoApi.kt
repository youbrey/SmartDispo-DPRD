package id.go.bitungkota.dprd.smartdispo.core.network

import id.go.bitungkota.dprd.smartdispo.core.model.TaskActionRequest
import id.go.bitungkota.dprd.smartdispo.core.model.MeetingRequestCreate
import id.go.bitungkota.dprd.smartdispo.core.model.MeetingRequestResponse
import id.go.bitungkota.dprd.smartdispo.core.model.MeetingType
import id.go.bitungkota.dprd.smartdispo.core.model.TokenPair
import id.go.bitungkota.dprd.smartdispo.core.model.UserProfile
import id.go.bitungkota.dprd.smartdispo.core.model.WorkflowTask
import retrofit2.http.Body
import retrofit2.http.Field
import retrofit2.http.FormUrlEncoded
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.Path

interface SmartDispoApi {
    @FormUrlEncoded
    @POST("auth/login")
    suspend fun login(@Field("username") username: String, @Field("password") password: String): TokenPair

    @GET("auth/me")
    suspend fun me(): UserProfile

    @GET("tasks/mine")
    suspend fun myTasks(): List<WorkflowTask>

    @GET("meeting-types")
    suspend fun meetingTypes(): List<MeetingType>

    @POST("meeting-requests")
    suspend fun createMeetingRequest(@Body request: MeetingRequestCreate): MeetingRequestResponse

    @POST("tasks/{taskId}/actions")
    suspend fun executeTask(@Path("taskId") taskId: String, @Body request: TaskActionRequest)
}

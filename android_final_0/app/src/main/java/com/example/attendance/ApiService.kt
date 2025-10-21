
package com.example.attendance

import retrofit2.Call
import retrofit2.http.*

data class TokenReq(val username: String, val password: String)
data class TokenRes(val access: String, val refresh: String?)

data class ClockReq(val latitude: Double, val longitude: Double, val type: String?, val work_location_id: Int?)
data class ClockRes(val ok: Boolean, val within_geofence: Boolean, val distance_m: Double, val type: String, val timestamp: String)

data class WorkLocation(val id: Int, val name: String, val latitude: Double, val longitude: Double, val radius_m: Int)
data class Shift(val id: Int, val name: String, val start_time: String, val end_time: String)
data class EmployeeMe(
    val id: Int,
    val username: String,
    val first_name: String?,
    val last_name: String?,
    val email: String?,
    val phone: String?,
    val shift: Shift?,
    val allowed_locations: List<WorkLocation>,
    val is_active: Boolean
)

data class EmployeeUpdate(val first_name: String?, val last_name: String?, val email: String?, val phone: String?)
data class ChangePasswordReq(val new_password1: String, val new_password2: String)

data class AttendanceItem(
    val id: Int, val type: String, val timestamp: String,
    val latitude: Double, val longitude: Double, val distance_m: Double,
    val within_geofence: Boolean, val work_location: WorkLocation
)
data class HistoryDay(val date: String, val items: List<AttendanceItem>, val total_hours: Double, val late: Boolean, val early_leave: Boolean)
data class HistoryRes(val period: String, val start: String, val end: String, val days: List<HistoryDay>, val sum_hours: Double)

interface ApiService {
    @POST("api/token/")
    fun token(@Body body: TokenReq): Call<TokenRes>

    @POST("api/clock/")
    fun clock(@Body req: ClockReq): Call<ClockRes>

    @GET("api/employee/me/")
    fun me(): Call<EmployeeMe>

    @PATCH("api/employee/me/")
    fun updateMe(@Body body: EmployeeUpdate): Call<EmployeeMe>

    @POST("api/employee/change-password/")
    fun changePassword(@Body body: ChangePasswordReq): Call<Map<String, Any>>

    @GET("api/attendance/history/")
    fun history(@Query("period") period: String, @Query("date") date: String?): Call<HistoryRes>
}

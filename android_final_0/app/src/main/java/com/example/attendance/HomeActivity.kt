
package com.example.attendance

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.location.Location
import android.os.Bundle
import android.widget.Button
import android.widget.TextView
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import com.google.android.gms.location.LocationServices
import retrofit2.Call
import retrofit2.Callback
import retrofit2.Response

class HomeActivity : AppCompatActivity() {

    private var selectedWorkLocationId: Int? = null
    private var allowedLocations: List<WorkLocation> = emptyList()


    private lateinit var statusText: TextView

    private val requestPermission = registerForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions()
    ) { perms ->
        if (perms[Manifest.permission.ACCESS_FINE_LOCATION] == true ||
            perms[Manifest.permission.ACCESS_COARSE_LOCATION] == true) {
            clock()
        } else {
            Toast.makeText(this, "Cần quyền vị trí để chấm công", Toast.LENGTH_SHORT).show()
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_home)

        statusText = findViewById(R.id.statusText)
        findViewById<Button>(R.id.historyBtn).setOnClickListener { startActivity(Intent(this, HistoryActivity::class.java)) }
        findViewById<Button>(R.id.profileBtn).setOnClickListener { startActivity(Intent(this, ProfileActivity::class.java)) }
        findViewById<Button>(R.id.clockBtn).setOnClickListener { requestAndClock() }

        supportActionBar?.setDisplayHomeAsUpEnabled(true)

        // Fetch user info to greet
        val api = RetrofitClient.retrofit(this).create(ApiService::class.java)
        api.me().enqueue(object : Callback<EmployeeMe> {
            override fun onResponse(call: Call<EmployeeMe>, response: Response<EmployeeMe>) {
                if (response.isSuccessful) {
                    val me = response.body()!!
                    findViewById<TextView>(R.id.welcomeText).text = "Xin chào, ${me.username}"
                    allowedLocations = me.allowed_locations
                    if (allowedLocations.isEmpty()) {
                        statusText.text = "Bạn chưa được cấu hình địa điểm chấm công. Liên hệ quản trị để gán địa điểm."
                    } else {
                        // chọn mặc định địa điểm đầu tiên
                        selectedWorkLocationId = allowedLocations.first().id
                    }
                } else {
                    statusText.text = "Không lấy được thông tin người dùng (${response.code()})"
                }
            }
            override fun onFailure(call: Call<EmployeeMe>, t: Throwable) {
                statusText.text = "Lỗi lấy thông tin: ${t.message}"
            }
        }) 
    }

    private fun requestAndClock() {
        if (ActivityCompat.checkSelfPermission(this, Manifest.permission.ACCESS_FINE_LOCATION) != PackageManager.PERMISSION_GRANTED &&
            ActivityCompat.checkSelfPermission(this, Manifest.permission.ACCESS_COARSE_LOCATION) != PackageManager.PERMISSION_GRANTED) {
            requestPermission.launch(arrayOf(Manifest.permission.ACCESS_FINE_LOCATION, Manifest.permission.ACCESS_COARSE_LOCATION))
            return
        }
        clock()
    }

    private fun clock() {
        val fused = LocationServices.getFusedLocationProviderClient(this)
        if (ActivityCompat.checkSelfPermission(this, Manifest.permission.ACCESS_FINE_LOCATION) != PackageManager.PERMISSION_GRANTED &&
            ActivityCompat.checkSelfPermission(this, Manifest.permission.ACCESS_COARSE_LOCATION) != PackageManager.PERMISSION_GRANTED) {
            return
        }
        fused.lastLocation.addOnSuccessListener { loc: Location? ->
            if (loc == null) {
                statusText.text = "Không lấy được vị trí"
                return@addOnSuccessListener
            }
            val api = RetrofitClient.retrofit(this).create(ApiService::class.java)
            val req = ClockReq(latitude = loc.latitude, longitude = loc.longitude, type = null, work_location_id = selectedWorkLocationId)
            api.clock(req).enqueue(object: Callback<ClockRes> {
                override fun onResponse(call: Call<ClockRes>, response: Response<ClockRes>) {
                    if (response.isSuccessful) {
                        val body = response.body()!!
                        val msg = if (body.within_geofence) "Hợp lệ" else "Ngoài phạm vi"
                        statusText.text = "Đã ${body.type} lúc ${body.timestamp}\nKhoảng cách: ${body.distance_m} m ($msg)"
                        Toast.makeText(this@HomeActivity, "Chấm công ${body.type}", Toast.LENGTH_SHORT).show()
                    } else {
                        val err = try { response.errorBody()?.string() } catch (e: Exception) { null }
                        statusText.text = "Chấm công thất bại: ${response.code()} " + (err ?: "")
                    }
                }
                override fun onFailure(call: Call<ClockRes>, t: Throwable) {
                    statusText.text = "Lỗi: ${t.message}"
                }
            })
        }
    }

    override fun onSupportNavigateUp(): Boolean {
        onBackPressedDispatcher.onBackPressed()
        return true
    }
}

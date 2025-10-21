
package com.example.attendance

import android.os.Bundle
import android.widget.Button
import android.widget.EditText
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import retrofit2.Call
import retrofit2.Callback
import retrofit2.Response

class ProfileActivity : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_profile)
        supportActionBar?.setDisplayHomeAsUpEnabled(true)

        val api = RetrofitClient.retrofit(this).create(ApiService::class.java)
        val firstName = findViewById<EditText>(R.id.firstName)
        val lastName = findViewById<EditText>(R.id.lastName)
        val email = findViewById<EditText>(R.id.email)
        val phone = findViewById<EditText>(R.id.phone)
        val info = findViewById<TextView>(R.id.infoText)

        api.me().enqueue(object: Callback<EmployeeMe> {
            override fun onResponse(call: Call<EmployeeMe>, response: Response<EmployeeMe>) {
                if (response.isSuccessful) {
                    val me = response.body()!!
                    firstName.setText(me.first_name ?: "")
                    lastName.setText(me.last_name ?: "")
                    email.setText(me.email ?: "")
                    phone.setText(me.phone ?: "")
                }
            }
            override fun onFailure(call: Call<EmployeeMe>, t: Throwable) {}
        })

        findViewById<Button>(R.id.saveBtn).setOnClickListener {
            val update = EmployeeUpdate(firstName.text.toString(), lastName.text.toString(), email.text.toString(), phone.text.toString())
            api.updateMe(update).enqueue(object: Callback<EmployeeMe> {
                override fun onResponse(call: Call<EmployeeMe>, response: Response<EmployeeMe>) {
                    if (response.isSuccessful) info.text = "Đã lưu thông tin cá nhân."
                    else info.text = "Lỗi: ${response.code()}"
                }
                override fun onFailure(call: Call<EmployeeMe>, t: Throwable) { info.text = "Lỗi: ${t.message}" }
            })
        }

        findViewById<Button>(R.id.changePassBtn).setOnClickListener {
            val p1 = findViewById<EditText>(R.id.pass1).text.toString()
            val p2 = findViewById<EditText>(R.id.pass2).text.toString()
            api.changePassword(ChangePasswordReq(p1, p2)).enqueue(object: Callback<Map<String, Any>> {
                override fun onResponse(call: Call<Map<String, Any>>, response: Response<Map<String, Any>>) {
                    if (response.isSuccessful) {
                        Toast.makeText(this@ProfileActivity, "Đổi mật khẩu thành công", Toast.LENGTH_SHORT).show()
                    } else {
                        Toast.makeText(this@ProfileActivity, "Lỗi: ${response.code()}", Toast.LENGTH_SHORT).show()
                    }
                }
                override fun onFailure(call: Call<Map<String, Any>>, t: Throwable) {
                    Toast.makeText(this@ProfileActivity, "Lỗi: ${t.message}", Toast.LENGTH_SHORT).show()
                }
            })
        }
    }

    override fun onSupportNavigateUp(): Boolean {
        onBackPressedDispatcher.onBackPressed()
        return true
    }
}

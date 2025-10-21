
package com.example.attendance

import android.content.Intent
import android.os.Bundle
import android.widget.Button
import android.widget.EditText
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import retrofit2.Call
import retrofit2.Callback
import retrofit2.Response

class MainActivity : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_login)

        val edtUser = findViewById<EditText>(R.id.username)
        val edtPass = findViewById<EditText>(R.id.password)
        val btnLogin = findViewById<Button>(R.id.loginBtn)
        val result = findViewById<TextView>(R.id.resultText)

        btnLogin.setOnClickListener {
            val api = RetrofitClient.retrofit(this).create(ApiService::class.java)
            api.token(TokenReq(edtUser.text.toString(), edtPass.text.toString()))
                .enqueue(object: Callback<TokenRes> {
                    override fun onResponse(call: Call<TokenRes>, response: Response<TokenRes>) {
                        if (response.isSuccessful) {
                            val body = response.body()!!
                            Prefs(this@MainActivity).saveTokens(body.access, body.refresh)
                            startActivity(Intent(this@MainActivity, HomeActivity::class.java))
                            finish()
                        } else {
                            result.text = "Đăng nhập thất bại (${response.code()})"
                        }
                    }
                    override fun onFailure(call: Call<TokenRes>, t: Throwable) {
                        result.text = "Lỗi kết nối: ${t.message}"
                    }
                })
        }
    }
}

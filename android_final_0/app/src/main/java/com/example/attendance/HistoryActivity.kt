
package com.example.attendance

import android.os.Bundle
import android.view.View
import android.widget.*
import androidx.appcompat.app.AppCompatActivity
import retrofit2.Call
import retrofit2.Callback
import retrofit2.Response
import java.text.SimpleDateFormat
import java.util.*

class HistoryActivity : AppCompatActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_history)
        supportActionBar?.setDisplayHomeAsUpEnabled(true)

        val spinner = findViewById<Spinner>(R.id.periodSpinner)
        spinner.adapter = ArrayAdapter(this, android.R.layout.simple_spinner_dropdown_item, listOf("day","week","month"))
        findViewById<EditText>(R.id.dateInput).setText(SimpleDateFormat("yyyy-MM-dd", Locale.US).format(Date()))
        findViewById<Button>(R.id.loadBtn).setOnClickListener { load() }

        load()
    }

    private fun load() {
        val period = findViewById<Spinner>(R.id.periodSpinner).selectedItem as String
        val date = findViewById<EditText>(R.id.dateInput).text.toString()
        val api = RetrofitClient.retrofit(this).create(ApiService::class.java)
        api.history(period, date).enqueue(object: Callback<HistoryRes> {
            override fun onResponse(call: Call<HistoryRes>, response: Response<HistoryRes>) {
                if (!response.isSuccessful) return
                val data = response.body()!!
                findViewById<TextView>(R.id.summaryText).text = "Tổng giờ: ${data.sum_hours} (${data.start} đến ${data.end})"
                val container = findViewById<LinearLayout>(R.id.listContainer)
                container.removeAllViews()
                data.days.forEach { d ->
                    val tv = TextView(this@HistoryActivity)
                    val sb = StringBuilder()
                    sb.append("Ngày ${d.date} • Tổng: ${d.total_hours}h")
                    if (d.late) sb.append(" • Đi trễ")
                    if (d.early_leave) sb.append(" • Về sớm")
                    sb.append("\n")
                    d.items.forEach {
                        sb.append(" - ${it.type} @ ${it.timestamp} • ${if (it.within_geofence) "OK" else "OUT"} • ${it.distance_m}m\n")
                    }
                    tv.text = sb.toString()
                    container.addView(tv)
                }
            }
            override fun onFailure(call: Call<HistoryRes>, t: Throwable) {
                findViewById<TextView>(R.id.summaryText).text = "Lỗi: ${t.message}"
            }
        })
    }

    override fun onSupportNavigateUp(): Boolean {
        onBackPressedDispatcher.onBackPressed()
        return true
    }
}

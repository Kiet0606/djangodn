
package com.example.attendance

import android.content.Context
import android.content.SharedPreferences

class Prefs(context: Context) {
    private val sp: SharedPreferences = context.getSharedPreferences("auth", Context.MODE_PRIVATE)

    fun saveTokens(access: String, refresh: String?) {
        sp.edit().putString("access", access).apply()
        if (refresh != null) sp.edit().putString("refresh", refresh).apply()
    }
    fun getAccessToken(): String? = sp.getString("access", null)
    fun clear() { sp.edit().clear().apply() }
}

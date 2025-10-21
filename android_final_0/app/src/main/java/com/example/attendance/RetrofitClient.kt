
package com.example.attendance

import android.content.Context
import okhttp3.Interceptor
import okhttp3.OkHttpClient
import okhttp3.Response
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory

class AuthInterceptor(private val context: Context) : Interceptor {
    override fun intercept(chain: Interceptor.Chain): Response {
        val token = Prefs(context).getAccessToken()
        val req = if (token != null) {
            chain.request().newBuilder().addHeader("Authorization", "Bearer $token").build()
        } else chain.request()
        return chain.proceed(req)
    }
}

object RetrofitClient {
    fun retrofit(context: Context): Retrofit {
        val base = if (Config.BASE_URL.endsWith("/")) Config.BASE_URL else Config.BASE_URL + "/"
        val client = OkHttpClient.Builder()
            .addInterceptor(AuthInterceptor(context))
            .build()
        return Retrofit.Builder()
            .baseUrl(base)
            .addConverterFactory(GsonConverterFactory.create())
            .client(client)
            .build()
    }
}

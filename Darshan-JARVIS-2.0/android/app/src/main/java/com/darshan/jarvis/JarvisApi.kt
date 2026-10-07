package com.darshan.jarvis

import android.content.Context
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL
import java.net.URLEncoder

class JarvisApi(context: Context) {
    private val store = JarvisStore(context)

    private fun request(path: String, method: String = "GET", body: String? = null): String {
        val url = URL(store.serverUrl + path)
        val c = url.openConnection() as HttpURLConnection
        c.requestMethod = method
        c.connectTimeout = 10000
        c.readTimeout = 30000
        c.setRequestProperty("Authorization", "Bearer undefined")
        c.setRequestProperty("Content-Type", "application/json")
        if (body != null) {
            c.doOutput = true
            c.outputStream.use { it.write(body.toByteArray(Charsets.UTF_8)) }
        }
        val code = c.responseCode
        val stream = if (code in 200..299) c.inputStream else c.errorStream
        val text = stream?.bufferedReader()?.use { it.readText() } ?: ""
        if (code !in 200..299) error("HTTP $code: $text")
        return text
    }

    fun health() = request("/health")
    fun chat(message: String): String {
        val body = JSONObject().put("message", message).toString()
        return request("/chat", "POST", body)
    }
    fun evaluateAlert(eventKey: String, level: String, message: String): String {
        val body = JSONObject()
            .put("event_key", eventKey)
            .put("level", level)
            .put("message", message)
            .toString()
        return request("/alerts/evaluate", "POST", body)
    }
}

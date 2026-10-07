package com.darshan.jarvis

import android.app.Service
import android.content.Intent
import android.os.IBinder
import androidx.core.app.NotificationCompat
import okhttp3.*
import org.json.JSONObject
import java.util.concurrent.TimeUnit

class JarvisEventService : Service() {
    private lateinit var client: OkHttpClient
    private var socket: WebSocket? = null
    private lateinit var store: JarvisStore

    override fun onCreate() {
        super.onCreate()
        store = JarvisStore(this)
        NotificationHelper.createChannel(this)
        startForeground(NotificationHelper.SERVICE_ID, foregroundNotification())
        connect()
    }

    private fun foregroundNotification() =
        NotificationCompat.Builder(this, "jarvis_alerts")
            .setSmallIcon(android.R.drawable.ic_dialog_info)
            .setContentTitle("JARVIS is connected")
            .setContentText("Secure event channel active")
            .setOngoing(true)
            .build()

    private fun connect() {
        val base = store.serverUrl
        if (base.isBlank() || store.token.isBlank()) return
        val wsBase = base.replaceFirst("https://", "wss://").replaceFirst("http://", "ws://")
        client = OkHttpClient.Builder().pingInterval(25, TimeUnit.SECONDS).build()
        val request = Request.Builder()
            .url(wsBase + "/mobile/events")
            .addHeader("Authorization", "Bearer " + store.token)
            .build()
        socket = client.newWebSocket(request, object : WebSocketListener() {
            override fun onMessage(webSocket: WebSocket, text: String) {
                try {
                    val o = JSONObject(text)
                    val level = o.optString("level", "MEDIUM")
                    val title = if (level == "CRITICAL" || level == "EMERGENCY") "JARVIS • " + level else "JARVIS Alert"
                    NotificationHelper.show(this@JarvisEventService, title, o.optString("message", "Important JARVIS event"))
                } catch (_: Exception) {
                    NotificationHelper.show(this@JarvisEventService, "JARVIS Alert", text)
                }
            }
            override fun onFailure(webSocket: WebSocket, t: Throwable, response: Response?) {
                stopSelf()
            }
        })
    }

    override fun onDestroy() {
        socket?.close(1000, "service stopped")
        if (::client.isInitialized) client.dispatcher.executorService.shutdown()
        super.onDestroy()
    }

    override fun onBind(intent: Intent?): IBinder? = null
}

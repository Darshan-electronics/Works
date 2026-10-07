package com.darshan.jarvis

import android.Manifest
import android.app.Activity
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Bundle
import android.provider.CalendarContract
import android.provider.Settings
import android.view.Gravity
import android.widget.*
import java.util.Calendar

class MainActivity : Activity() {
    private lateinit var server: EditText
    private lateinit var token: EditText
    private lateinit var output: TextView

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(28, 36, 28, 28)
            setBackgroundColor(0xff090b12.toInt())
        }
        fun label(t: String) = TextView(this).apply {
            text=t; textSize=16f; setTextColor(0xffeeeeee.toInt()); setPadding(0,14,0,6)
        }
        root.addView(TextView(this).apply {
            text="⚡ DARSHAN JARVIS"; textSize=28f; setTextColor(0xffffffff.toInt()); gravity=Gravity.CENTER
        })
        root.addView(label("JARVIS server HTTPS URL"))
        server = EditText(this).apply {
            hint="https://your-jarvis-endpoint"; setText("https://"); setTextColor(0xffffffff.toInt())
        }
        root.addView(server)
        root.addView(label("Access token"))
        token = EditText(this).apply {
            hint="Bearer token"; inputType=0x81; setTextColor(0xffffffff.toInt())
        }
        root.addView(token)
        root.addView(Button(this).apply {
            text="Connect to JARVIS"
            setOnClickListener { output.text="Connection settings loaded. Server: " + server.text }
        })
        root.addView(label("Device capabilities"))
        root.addView(Button(this).apply {
            text="Allow Calendar access"
            setOnClickListener { request(Manifest.permission.READ_CALENDAR, Manifest.permission.WRITE_CALENDAR) }
        })
        root.addView(Button(this).apply {
            text="Allow Contacts access"
            setOnClickListener { request(Manifest.permission.READ_CONTACTS) }
        })
        root.addView(Button(this).apply {
            text="Allow Microphone"
            setOnClickListener { request(Manifest.permission.RECORD_AUDIO) }
        })
        root.addView(Button(this).apply {
            text="Allow Location"
            setOnClickListener { request(Manifest.permission.ACCESS_FINE_LOCATION, Manifest.permission.ACCESS_COARSE_LOCATION) }
        })
        root.addView(Button(this).apply {
            text="Open Maps"
            setOnClickListener {
                startActivity(packageManager.getLaunchIntentForPackage("com.google.android.apps.maps")
                    ?: Intent(Settings.ACTION_SETTINGS))
            }
        })
        root.addView(Button(this).apply {
            text="Add a class to Calendar"
            setOnClickListener { addCalendarEvent("College class") }
        })
        output = TextView(this).apply {
            text="Ready."; textSize=15f; setTextColor(0xffdddddd.toInt()); setPadding(0,20,0,0)
        }
        root.addView(output)
        setContentView(ScrollView(this).apply { addView(root) })
    }

    private fun request(vararg permissions: String) {
        val need = permissions.filter { checkSelfPermission(it) != PackageManager.PERMISSION_GRANTED }
        if (need.isNotEmpty()) requestPermissions(need.toTypedArray(), 42)
        else output.text = "Permission already granted."
    }

    private fun addCalendarEvent(title: String) {
        val begin = Calendar.getInstance().apply { add(Calendar.HOUR_OF_DAY, 1) }.timeInMillis
        val end = begin + 60 * 60 * 1000
        val i = Intent(Intent.ACTION_INSERT).apply {
            data = CalendarContract.Events.CONTENT_URI
            putExtra(CalendarContract.EXTRA_EVENT_BEGIN_TIME, begin)
            putExtra(CalendarContract.EXTRA_EVENT_END_TIME, end)
            putExtra(CalendarContract.Events.TITLE, title)
            putExtra(CalendarContract.Events.DESCRIPTION, "Added by Darshan JARVIS")
        }
        startActivity(i)
    }
}

package com.darshan.jarvis

import android.Manifest
import android.app.Activity
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Bundle
import android.provider.CalendarContract
import android.provider.Settings
import android.speech.RecognizerIntent
import android.speech.tts.TextToSpeech
import android.view.Gravity
import android.widget.*
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import android.content.Context
import org.json.JSONObject
import java.util.Calendar
import java.util.Locale
import java.util.concurrent.Executors

class MainActivity : Activity(), TextToSpeech.OnInitListener {
    private lateinit var server: EditText
    private lateinit var token: EditText
    private lateinit var output: TextView
    private lateinit var store: JarvisStore
    private lateinit var tts: TextToSpeech
    private val io = Executors.newSingleThreadExecutor()
    private val voiceRequest = 7001

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        store = JarvisStore(this)
        tts = TextToSpeech(this, this)
        NotificationHelper.createChannel(this)
        buildUi()
        requestNotificationPermission()
    }

    private fun buildUi() {
        val root = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL; setPadding(28,36,28,28); setBackgroundColor(0xff090b12.toInt()) }
        fun label(s: String) = TextView(this).apply { text=s; textSize=16f; setTextColor(0xffffffff.toInt()); setPadding(0,14,0,6) }
        root.addView(TextView(this).apply { text="⚡ DARSHAN JARVIS"; textSize=28f; setTextColor(0xffffffff.toInt()); gravity=Gravity.CENTER })
        root.addView(label("Secure JARVIS server HTTPS URL"))
        server = EditText(this).apply { hint="https://your-jarvis-endpoint"; setText(store.serverUrl.ifBlank { "https://" }); setTextColor(0xffffffff.toInt()) }; root.addView(server)
        root.addView(label("Access token"))
        token = EditText(this).apply { hint="JARVIS access token"; inputType=0x81; setText(store.token); setTextColor(0xffffffff.toInt()) }; root.addView(token)
        root.addView(Button(this).apply { text="Save & Test JARVIS"; setOnClickListener { saveAndTest() } })
        root.addView(Button(this).apply { text="🎙 Activate JARVIS"; setOnClickListener { startVoice() } })
        root.addView(label("Permissions"))
        permissionButton(root,"Notifications",Manifest.permission.POST_NOTIFICATIONS)
        permissionButton(root,"Calendar",Manifest.permission.READ_CALENDAR,Manifest.permission.WRITE_CALENDAR)
        permissionButton(root,"Contacts",Manifest.permission.READ_CONTACTS)
        permissionButton(root,"Microphone",Manifest.permission.RECORD_AUDIO)
        permissionButton(root,"Location",Manifest.permission.ACCESS_FINE_LOCATION,Manifest.permission.ACCESS_COARSE_LOCATION)
        root.addView(Button(this).apply { text="📅 Add college class"; setOnClickListener { addCalendarEvent("College class") } })
        root.addView(Button(this).apply { text="📱 Discover installed apps"; setOnClickListener { showApps() } })
        root.addView(Button(this).apply { text="⚙ Open Android settings"; setOnClickListener { startActivity(Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS).apply { data=android.net.Uri.parse("package:"+packageName) }) } })
        output=TextView(this).apply { text="Ready. Voice activates only when you press Activate."; textSize=15f; setTextColor(0xffdddddd.toInt()); setPadding(0,20,0,0) }; root.addView(output)
        setContentView(ScrollView(this).apply { addView(root) })
    }

    private fun permissionButton(root: LinearLayout, name:String, vararg permissions:String) { root.addView(Button(this).apply { text="Allow "+name; setOnClickListener { request(*permissions) } }) }
    private fun request(vararg permissions:String) { val need=permissions.filter { ContextCompat.checkSelfPermission(this,it)!=PackageManager.PERMISSION_GRANTED }; if(need.isNotEmpty()) ActivityCompat.requestPermissions(this,need.toTypedArray(),42) else output.text="Permission already granted." }
    private fun requestNotificationPermission() { if(android.os.Build.VERSION.SDK_INT>=33 && checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS)!=PackageManager.PERMISSION_GRANTED) requestPermissions(arrayOf(Manifest.permission.POST_NOTIFICATIONS),43) }

    private fun saveAndTest() {
        store.serverUrl=server.text.toString(); store.token=token.text.toString(); output.text="Testing JARVIS..."
        io.execute { try { val raw=JarvisApi(this).health(); runOnUiThread { output.text="JARVIS online: "+raw; startMobileEvents() } } catch(ex:Exception) { runOnUiThread { output.text="Connection failed: "+ex.message } } }
    }


    private fun startMobileEvents() {
        if (android.os.Build.VERSION.SDK_INT >= 33 &&
            checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) {
            output.text = "Allow notifications before enabling mobile JARVIS alerts."
            return
        }
        val intent = Intent(this, JarvisEventService::class.java)
        ContextCompat.startForegroundService(this, intent)
        output.text = "JARVIS mobile alert channel is active."
    }

    private fun startVoice() {
        if(ContextCompat.checkSelfPermission(this,Manifest.permission.RECORD_AUDIO)!=PackageManager.PERMISSION_GRANTED) { request(Manifest.permission.RECORD_AUDIO); return }
        val i=Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply { putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL,RecognizerIntent.LANGUAGE_MODEL_FREE_FORM); putExtra(RecognizerIntent.EXTRA_LANGUAGE,Locale.getDefault()); putExtra(RecognizerIntent.EXTRA_PROMPT,"Say your JARVIS command") }; startActivityForResult(i,voiceRequest)
    }

    override fun onActivityResult(requestCode:Int,resultCode:Int,data:Intent?) {
        super.onActivityResult(requestCode,resultCode,data); if(requestCode!=voiceRequest || resultCode!=RESULT_OK) return
        val message=data?.getStringArrayListExtra(RecognizerIntent.EXTRA_RESULTS)?.firstOrNull() ?: return; output.text="You: "+message+"\nJARVIS is thinking..."
        io.execute { try { val raw=JarvisApi(this).chat(message); val answer=JSONObject(raw).optString("answer",raw); runOnUiThread { output.text="You: "+message+"\n\nJARVIS: "+answer; tts.speak(answer,TextToSpeech.QUEUE_FLUSH,null,"jarvis") } } catch(ex:Exception) { runOnUiThread { output.text="JARVIS error: "+ex.message } } }
    }

    private fun addCalendarEvent(title:String) {
        if(ContextCompat.checkSelfPermission(this,Manifest.permission.WRITE_CALENDAR)!=PackageManager.PERMISSION_GRANTED) { request(Manifest.permission.WRITE_CALENDAR); return }
        val begin=Calendar.getInstance().apply { add(Calendar.HOUR_OF_DAY,1) }.timeInMillis; val end=begin+3600000
        startActivity(Intent(Intent.ACTION_INSERT).apply { data=CalendarContract.Events.CONTENT_URI; putExtra(CalendarContract.EXTRA_EVENT_BEGIN_TIME,begin); putExtra(CalendarContract.EXTRA_EVENT_END_TIME,end); putExtra(CalendarContract.Events.TITLE,title); putExtra(CalendarContract.Events.DESCRIPTION,"Added by Darshan JARVIS") })
    }

    private fun showApps() { val apps=AppDiscovery.list(this); output.text="Launchable apps ("+apps.size+"):\n"+apps.take(100).joinToString("\n") { "• "+it.label+" ("+it.packageName+")" } }
    override fun onInit(status:Int) { if(status==TextToSpeech.SUCCESS) tts.language=Locale.US }
    override fun onDestroy() { tts.shutdown(); io.shutdownNow(); super.onDestroy() }
}
package com.darshan.jarvis

import android.content.Context
import android.util.Base64
import java.security.KeyStore
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey

class JarvisStore(context: Context) {
    private val prefs = context.getSharedPreferences("jarvis", Context.MODE_PRIVATE)
    private val alias = "darshan_jarvis_key"

    private fun key(): SecretKey {
        val ks = KeyStore.getInstance("AndroidKeyStore").apply { load(null) }
        (ks.getKey(alias, null) as? SecretKey)?.let { return it }
        val gen = KeyGenerator.getInstance("AES", "AndroidKeyStore")
        gen.init(256)
        return gen.generateKey().also {
            // AndroidKeyStore persists the generated key.
        }
    }

    private fun encrypt(value: String): String {
        val cipher = Cipher.getInstance("AES/GCM/NoPadding")
        cipher.init(Cipher.ENCRYPT_MODE, key())
        val combined = cipher.iv + cipher.doFinal(value.toByteArray(Charsets.UTF_8))
        return Base64.encodeToString(combined, Base64.NO_WRAP)
    }

    private fun decrypt(value: String): String {
        val raw = Base64.decode(value, Base64.NO_WRAP)
        val iv = raw.copyOfRange(0, 12)
        val data = raw.copyOfRange(12, raw.size)
        val cipher = Cipher.getInstance("AES/GCM/NoPadding")
        cipher.init(Cipher.DECRYPT_MODE, key(), javax.crypto.spec.GCMParameterSpec(128, iv))
        return String(cipher.doFinal(data), Charsets.UTF_8)
    }

    var serverUrl: String
        get() = prefs.getString("server_url", "") ?: ""
        set(v) = prefs.edit().putString("server_url", v.trim().removeSuffix("/")).apply()

    var token: String
        get() = prefs.getString("token", "")?.let { runCatching { decrypt(it) }.getOrNull() } ?: ""
        set(v) = prefs.edit().putString("token", encrypt(v)).apply()

    fun clear() = prefs.edit().clear().apply()
}

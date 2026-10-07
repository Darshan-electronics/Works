plugins { id("com.android.application"); id("org.jetbrains.kotlin.android") }
android {
    namespace = "com.darshan.jarvis"
    compileSdk = 36
    defaultConfig {
        applicationId = "com.darshan.jarvis"
        minSdk = 26
        targetSdk = 36
        versionCode = 2
        versionName = "0.2.0"
    }
}
dependencies {
    implementation("androidx.core:core-ktx:1.17.0")
}

# Darshan JARVIS Android Companion

The Android app is the mobile half of JARVIS.

Current capabilities:
- Secure HTTPS JARVIS API connection with an Android Keystore-protected access token.
- Realtime mobile alert channel over authenticated WebSocket.
- High-priority Android notifications for JARVIS events.
- Manual voice activation using Android speech recognition while the app is active.
- Android Text-to-Speech for replies.
- Calendar permission and calendar-event insertion.
- Contacts, microphone, and location permission controls.
- Launchable-app discovery.
- JARVIS server health test.

Android limitation:
This app does not secretly keep the microphone recording in the background. Modern Android restricts background microphone and foreground-service startup and requires explicit foreground-service types and permissions. The mobile event channel therefore stays connected for alerts, while microphone use starts from an explicit user action.

A future Hey JARVIS wake-word mode should use a user-enabled Android assistant or voice-service architecture, or an explicitly running microphone foreground service, rather than bypassing Android privacy controls.

Setup:
1. Open the android directory in Android Studio.
2. Build and install the app.
3. Enter the HTTPS JARVIS server URL.
4. Enter the JARVIS bearer token.
5. Grant Notifications.
6. Tap Save & Test JARVIS.
7. Keep the mobile alert channel enabled.
8. Grant Calendar, Microphone, Contacts, and Location only when you want those capabilities.

Never put Twilio or ElevenLabs secrets in the APK. They remain on the Rocky Linux JARVIS server.
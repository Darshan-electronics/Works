# JARVIS Android Device Agent

The Android companion is the device-side bridge for JARVIS. It should request only the permissions needed for a capability and expose them as explicit tools to the Linux JARVIS server.

## Capability groups

- Apps: discover installed launchable apps and open supported apps with Android intents.
- Calendar: read/write calendar events when the user grants calendar permissions.
- College: store timetable, class timings, rooms, faculty, exam dates, attendance targets and campus links in JARVIS knowledge.
- Notifications: optional notification access, enabled by the user.
- Contacts: optional contacts access.
- Phone: call initiation and selected phone controls, with confirmation for outbound calls.
- Messaging: compose/share messages through Android intents; sending should require confirmation.
- Files/media: user-selected files and media through Android's document/media pickers.
- Location: optional and off by default; only enabled for location-dependent commands.
- Screen/app automation: optional accessibility service, only after the user explicitly enables it. Accessibility APIs can observe UI events and active-window content, but Android requires the user to turn such a service on in Settings. Do not use it as an unrestricted surveillance mechanism.

Android's Intent system allows JARVIS to launch compatible activities and pass data to other apps. Android permissions protect sensitive data such as contacts, SMS and calendar data, so each capability must be separately permissioned.

## College knowledge

JARVIS should have a first-run College Setup wizard:

1. College name and campus.
2. Academic year and semester.
3. Department and section.
4. Timetable upload/import (PDF, image, CSV or manual entry).
5. Class start/end times.
6. Faculty and room mapping.
7. Exam/test schedule.
8. Attendance rules and target.
9. Official college portal URLs.
10. Optional calendar sync.

Store these as source-tagged knowledge. If the user uploads a timetable image/PDF, preserve the original source reference and extracted schedule. If the college portal changes, refresh only after an explicit schedule or trusted-source rule is configured.

## Permission model

JARVIS should show a capability dashboard:

- Granted
- Not granted
- Optional
- Needs confirmation

No single "give JARVIS everything" permission should bypass Android's security model.

## Remote architecture

Android app <-> authenticated HTTPS/Tailscale connection <-> Linux JARVIS API <-> Ollama/knowledge/tools.

Never expose Ollama directly to the Internet. Device actions should be signed/authenticated and high-risk actions should carry an approval token or explicit confirmation.

## Example commands

- "JARVIS, what class do I have next?"
- "Open my college portal."
- "Add tomorrow's lab to my calendar."
- "Remind me 30 minutes before my 10 AM class."
- "How many classes can I miss and remain above my attendance target?"
- "Show today's timetable."
- "Call my project teammate." (confirmation required)

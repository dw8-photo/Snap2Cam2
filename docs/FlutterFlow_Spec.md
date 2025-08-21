
# Snap2Schedule — FlutterFlow AI Builder Spec
**Goal:** Turn any schedule/syllabus/school calendar into calendar events by pointing a phone camera (or importing an image/PDF/screenshot). OCR → Event extraction → Human review → Publish to device calendar (iOS/Android) and/or in‑app calendar.

---

## 1) App Summary (paste this into FlutterFlow AI Gen)
Build a mobile app called **Snap2Schedule** for iOS/Android. Core flow:
- **Capture**: Camera or image/PDF upload. Optionally auto‑detect document edges and crop.
- **OCR**: Extract raw text from the image(s).
- **Parse**: Convert OCR text into structured **event suggestions** (title, date, time, recurrence, location, notes, confidence).
- **Review**: Show a “human‑in‑the‑loop” table with quick edits, flags for low-confidence items, bulk approve/deny, and batch edits (calendar/profile labels).
- **Publish**: Create events in **Device Calendar** (native iOS/Android) and/or an **in‑app calendar** (Firestore collection). Allow **ICS export** and Google Calendar add via URL intent.
- **Profiles**: Support multiple child profiles (color/emoji) and default calendars.
- **Sources**: Store source images + OCR text per import for audit/history.

Design a clean, cheerful UI (kid‑friendly but not childish). Primary actions always visible; use bottom bar: **Scan**, **Suggestions**, **Calendar**, **Sources**, **Settings**.

---

## 2) Core Screens & Navigation
1. **Onboarding / Profile Setup**
   - Create 1–3 starter profiles (e.g., “Avery”, “Maya”). Choose color/emoji. Pick default calendar (device or in‑app).
2. **Scan / Import**
   - Buttons: “Camera”, “Photos/PDF”, “Paste Text”, “Screenshot Import”.
   - After capture: optional edge‑detect crop; then send to OCR API.
3. **Suggestions (Human Review)**
   - Table/list of parsed events (chips for **Exam/No School/Half Day/Quiz/Due** etc.).
   - Columns: Title, Date, Time, Recurrence (chip), Profile, Calendar, Confidence, Include [✓].
   - Bulk actions: set Profile/Calendar for selected; Accept Selected; Reject Selected.
   - Tap an item → **Edit Event** modal.
4. **Edit Event (Modal)**
   - Title, Start, End, All‑day, Location, Notes, Recurrence builder (BYDAY/RRULE), Profile/Calendar, Confidence note.
5. **Calendar (In‑App)**
   - Month/Week views; filter by profile; event color by profile; tap to view/edit.
6. **Sources**
   - Cards for each import (thumbnail, date, profile tags, #events found). Tap → detail (source image, OCR text, linked events, re‑parse button).
7. **Settings**
   - Profiles (add/edit), Integrations (Device Calendar on/off; Google Calendar link), Timezone, Keywords, OCR Provider, LLM Provider, Data export (ICS/CSV), Privacy.

Bottom Nav: **Scan · Suggestions · Calendar · Sources · Settings**

---

## 3) Data Model (Firestore Collections)
### `profiles`
- `name` (string, required)
- `emoji` (string, e.g., "📘")
- `color` (string hex, e.g., "#6C9EF8")
- `default_calendar_id` (string, optional, device or in‑app id)
- `timezone` (string, default device tz)

### `calendars`
- `title` (string)
- `type` (string enum: `device`, `inapp`, `google`)
- `platform_id` (string, nullable) – ID returned by device calendar API
- `profile_id` (ref, optional)

### `sources`
- `created_at` (timestamp)
- `type` (string enum: `camera`, `photo`, `pdf`, `screenshot`, `text`)
- `image_url` (string, optional) – uploaded capture
- `raw_text` (string) – OCR result
- `ocr_provider` (string)
- `ocr_confidence` (number 0–1)
- `status` (string enum: `parsed`, `reparsed`, `archived`)

### `events`
- `title` (string)
- `start` (timestamp)
- `end` (timestamp)
- `all_day` (bool)
- `location` (string)
- `notes` (string)
- `recurrence_rule` (string, iCal RRULE or null)
- `labels` (array<string>) – e.g., `["Exam","No School"]`
- `confidence` (number 0–1)
- `status` (string enum: `suggested`, `published`, `rejected`)
- `profile_id` (ref)
- `calendar_id` (ref or device id string)
- `source_id` (ref)

### `keywords` (optional; for rule‑based extraction fallback)
- `label` (string) – e.g., “No School”
- `synonyms` (array<string>)
- `patterns` (array<string> regex)
- `default_color` (string)

---

## 4) OCR & Parsing Pipeline
### Option A — Cloud OCR (Easy in FlutterFlow via REST API Call)
Use **Google Cloud Vision API** `images:annotate` (Text Detection).
- Endpoint: `POST https://vision.googleapis.com/v1/images:annotate?key=YOUR_API_KEY`
- Request (simplified):
```json
{
  "requests": [
    {
      "image": { "content": "<BASE64_JPEG_OR_PNG>" },
      "features": [{ "type": "TEXT_DETECTION" }]
    }
  ]
}
```
- Read `responses[0].fullTextAnnotation.text`.

### Option B — On‑Device OCR (Privacy/Offline)
Add custom package: `google_mlkit_text_recognition`. Wrap with a **Custom Action** to return the recognized text + blocks. (This requires FlutterFlow’s Custom Code packages.)

### Event Extraction (LLM‑first + Fallback)
1) **LLM Parse API** (REST) — safer and more accurate than regex alone.
- Endpoint (example): `POST https://your-cloud-run.app/parse_events`
- Request:
```json
{
  "text": "<OCR_TEXT>",
  "timezone": "America/Detroit",
  "default_year": 2025,
  "semester_window": {"start":"2025-08-01","end":"2025-12-31"}
}
```
- Response (schema):
```json
{
  "events": [
    {
      "title": "No School - Labor Day",
      "start_iso": "2025-09-01T00:00:00",
      "end_iso": "2025-09-02T00:00:00",
      "all_day": true,
      "recurrence_rule": null,
      "labels": ["No School"],
      "location": "",
      "notes": "district calendar",
      "confidence": 0.96
    }
  ],
  "warnings": ["Ambiguous date for 'Finals Week'"]
}
```
2) **Regex/RRule Fallback** (in‑app custom function)
- Detect phrases: `No School|Half Day|Early Release|Exam|Quiz|Midterm|Final|Project Due|Assignment Due|Parent‑Teacher Conference|Holiday`.
- Date/time patterns: `MM/DD`, `MMM D`, `D MMM`, `Mon 9/2`, `9:00–10:30`, `10am–11am`.
- Recurrence: `Every Mon/Wed/Fri`, `TTh`, `M–F`, `Weekly on Tuesdays` → convert to iCal `RRULE`.

---

## 5) Human‑in‑the‑Loop Review UX
- Each suggested event shows a **confidence chip**; low (<0.75) auto‑highlight in warning color.
- Bulk select + **Apply Profile/Calendar**.
- **Smart fixers**: “Fill missing end time = start + 45m” (configurable), “Cap event title at 80 chars”, “Normalize campus room codes”.
- **Ambiguity banner** when text like “Week of Oct 7” or “TBA” is detected.
- **Re‑parse** button on Source detail (e.g., after editing keyword rules or switching providers).

---

## 6) Integrations
### Device Calendar (Native)
Use Flutter package via **Custom Action**:
- `device_calendar` (or `flutter_device_calendar`) to **list calendars**, **create events**, **update**, **delete**.
- iOS `Info.plist`:
  - `NSCalendarsUsageDescription`: “We use your calendar to add approved events.”
  - `NSCameraUsageDescription`: “We use your camera to scan schedules.”
  - `NSPhotoLibraryAddUsageDescription` (if saving images).
- Android Manifest:
  - `CAMERA`, `READ_CALENDAR`, `WRITE_CALENDAR`, `READ/WRITE_EXTERNAL_STORAGE` (as needed).

### ICS Export
Generate `.ics` for selected events and share via standard share sheet.
- Example RRULE: `RRULE:FREQ=WEEKLY;BYDAY=MO,WE,FR;UNTIL=20251220T235959Z`

### Google Calendar (Optional)
Deep link to prefilled event or OAuth‑based write integration later.

---

## 7) FlutterFlow Implementation Notes
- **API Calls**:
  - `OCR_GCV`: Vision API (base64 image → text).
  - `LLM_Parse`: your Cloud Run (or Vercel) endpoint (OCR text → events array).
- **Custom Actions**:
  - `DeviceCalendar_ListCalendars()` → returns `[ {id, name, isDefault} ]`
  - `DeviceCalendar_CreateEvent(event)` → returns `eventId`
  - `BuildICSFile(events[])` → returns file path/bytes for share
- **Custom Functions** (pure Dart):
  - `inferSemesterWindow(now, text)`
  - `humanizeRRule(rrule)` and `rruleFromPattern(patternText, until)`
  - `normalizeTimespan("10–11:30am")` → `{start,end}`
  - `scoreConfidence(features)`
- **State**: Use app state for current profile, selected calendar, timezone, semester dates.
- **Security**: Firestore rules scope to authenticated user; profiles/events belong to `uid`.

---

## 8) Prompts (LLM Parse)
**System Prompt (example):**
“You extract school‑related events from noisy OCR text into strict JSON. Assume timezone {{tz}}. If year missing, infer from {{default_year}} and semester window {{window}}. Return ISO datetimes without timezone suffix. Use iCal RRULE for recurrence when pattern is explicit. Include `confidence` 0–1. Use `labels` from: [Exam, Quiz, Midterm, Final, No School, Half Day, Early Release, Holiday, Due, Sports, Other]. Never invent dates.”

**User Prompt Template:**
```
TEXT:
{{ocr_text}}

CONTEXT:
timezone={{tz}}, default_year={{default_year}},
semester_window={{start}}..{{end}}

OUTPUT SCHEMA:
{ "events": [ { "title": str, "start_iso": str, "end_iso": str|null, "all_day": bool,
"recurrence_rule": str|null, "labels": [str], "location": str, "notes": str, "confidence": number } ], "warnings":[str] }
```

---

## 9) Test Cases (copy into Sources to validate)
1) “No School — Labor Day (Mon, Sept 1). Early Release 1:30pm on 9/18. Midterm: Oct 14, 10–11:30am, Room 204.”
2) “M/W/F 10:00–10:50 AM — Algebra II, Room B209 — 08/26–12/13 (no class 11/28).” → Recurring weekly RRULE + exception date.
3) “Finals Week: Dec 16–20. Check portal for exact times.” → Low confidence + warning.
4) “Half Day: 10/31. Parent‑Teacher Conferences 11/7 5–8 PM.”

---

## 10) Privacy & Kids
- All scans stay local unless user enables Cloud OCR/LLM.
- Show “Review before publish” always. No auto‑posting by default.
- One‑tap delete of sources + events.

---

## 11) Nice‑to‑Haves (v2)
- Share sheet extension (“Add to Snap2Schedule”).
- Multi‑page PDF scanning; auto‑merge suggestions.
- Timetable detector for class grids.
- District URL watcher (imports `.ics` or plain text from public calendars).

---

## 12) Acceptance Criteria (MVP)
- Capture/import → OCR → LLM parse → Suggestions appear with ≥90% correct titles/dates on provided samples.
- Approving events creates them in selected device calendar.
- In‑app calendar displays published events and supports edit/delete.
- ICS export works for a selected range.
- Profiles + default calendar assignment function as expected.

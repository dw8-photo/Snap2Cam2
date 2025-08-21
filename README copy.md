# Snap2Schedule

Turn scans/screenshots of school schedules into real calendar events. FlutterFlow front-end + FastAPI parse service.

## Layout
- `cloud/parse_events/` — FastAPI: OCR text → events
- `flutterflow/` — API call JSONs + Custom Actions/Functions
- `assets/` — keywords for regex fallback
- `test_data/` — sample text
- `docs/` — spec, AI Builder snippets, UI addendum
- `.github/workflows/` — optional Cloud Run CI
- `scripts/` — deploy helper

See `docs/FlutterFlow_Spec.md` and `docs/UI_Addendum_Mobile_Calendar.md`.

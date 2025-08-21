
# Snap2Schedule

Turn scans/screenshots of school schedules (or any timetable) into real calendar events. Built for **FlutterFlow** front‑end with a **FastAPI** parse service.

## Monorepo Layout
```
cloud/parse_events/   # FastAPI service: OCR text → structured events
flutterflow/          # API call JSONs + Custom Actions/Functions to import into FF
assets/               # label/keyword patterns (regex fallback)
test_data/            # sample text
docs/                 # spec & notes
.github/workflows/    # CI for Cloud Run
scripts/              # deploy helpers
```

## Quick Start
### Parse API (local)
```bash
cd cloud/parse_events
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8080
# Test
curl -s -X POST localhost:8080/parse_events \
  -H 'Content-Type: application/json' \
  -d '{"text":"No School — Labor Day (Mon, Sept 1).","timezone":"America/Detroit","default_year":2025}'
```

### Deploy to Cloud Run (GitHub Actions)
1. In GitHub repo **Settings → Secrets and variables → Actions**, set:
   - `GCP_PROJECT_ID`
   - `GCP_REGION` (e.g., `us-central1`)
   - `CLOUD_RUN_SERVICE` (e.g., `snap2schedule-parse`)
   - `GCP_SA_KEY` — JSON of a deployable service account
2. Push to `main`; CI builds & deploys the container from `cloud/parse_events`.

### FlutterFlow
- Import `flutterflow/api_calls/*.json` for OCR + Parse calls.
- Paste `flutterflow/custom_actions/*.dart` and `flutterflow/custom_functions/*.dart` into FF Custom Code.
- Follow `docs/FlutterFlow_Spec.md` to scaffold screens and Firestore collections.

## License
MIT — do your thing.


#!/usr/bin/env bash
set -euo pipefail

SERVICE_NAME=${1:-snap2schedule-parse}
REGION=${2:-us-central1}
PROJECT=${3:-$GCP_PROJECT_ID}

gcloud config set project "$PROJECT"
gcloud builds submit cloud/parse_events --tag gcr.io/$PROJECT/$SERVICE_NAME
gcloud run deploy $SERVICE_NAME --image gcr.io/$PROJECT/$SERVICE_NAME --region $REGION --allow-unauthenticated

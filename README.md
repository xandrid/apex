# APEX - Pre-Filing Patent Analysis Tool (MVP)

APEX is a tool for analyzing patent claims against prior art using Vertex AI.

## Architecture
- **Backend**: FastAPI (Python)
- **Frontend**: Next.js (React)
- **AI/ML**: Google Cloud Vertex AI (Gemini 1.5 Pro, Text Embeddings, Vector Search)

## Prerequisites
- Google Cloud Project with Vertex AI API enabled.
- `gcloud` CLI installed and authenticated.
- Python 3.9+
- Node.js 16+

## Setup

### 1. Environment Variables
Create a `.env` file in `apex-app/backend` and `apex-app/data_pipeline`:
```
GCP_PROJECT_ID=your-project-id
GCP_LOCATION=us-central1
VERTEX_INDEX_ENDPOINT_ID=your-index-endpoint-id (optional for mock)
VERTEX_DEPLOYED_INDEX_ID=your-deployed-index-id (optional for mock)
```

### 2. Data Pipeline (Ingestion)
To create the embeddings and prepare data for Vector Search:
```bash
cd apex-app/data_pipeline
pip install -r ../backend/requirements.txt
python ingest.py
```
This will generate `embeddings.jsonl`. You must then upload this to GCS and create a Vector Search Index in the GCP Console.

### 3. Backend
```bash
cd apex-app/backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```
The API will run at `http://localhost:8000`.

### 4. Frontend
```bash
cd apex-app/frontend
npm install
npm run dev
```
The UI will run at `http://localhost:3000`.

## Testing
- Visit `http://localhost:3000`.
- Paste a patent claim.
- Click "Analyze Claim".
- If you haven't set up the real Vector Search index, the backend will use a mock search result for demonstration.

## Project Structure
- `backend/app/services/vertex_llm.py`: Handles Gemini API calls for decomposition and reasoning.
- `backend/app/services/vector_search.py`: Handles Vector Search queries.
- `data_pipeline/ingest.py`: Scripts to process patents.

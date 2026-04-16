```python
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from app.models import ClaimInput, PatentAnalysis # app.models.AnalysisResponse is replaced
from app.services.vertex_llm import VertexLLMService
from app.services.vector_db import get_vector_service # Assuming this import path
from app.services.retrieval.hybrid_search import HybridSearchService # Assuming this import path
from app.services.job_store import JobStore
from pydantic import BaseModel
from typing import Optional

# Services
llm_service = VertexLLMService()
vector_service = get_vector_service()
hybrid_service = HybridSearchService()
job_store = JobStore()

app = FastAPI(title="APEX API", version="0.1.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AnalysisResponse(BaseModel):
    job_id: str
    status: str
    result: Optional[dict] = None

async def process_claim_analysis(job_id: str, claim_text: str, strict_mode: bool):
    """
    Background task to run the full analysis pipeline.
    """
    try:
        print(f"Starting Job {job_id} for claim: {claim_text[:50]}...")
        job_store.update_job(job_id, "RUNNING")
        
        # 1. Decompose
        claim_elements = await llm_service.decompose_claim(claim_text)
        
        # 2. Search
        patent_scores = {}
        patent_evidence = {}
        
        for element in claim_elements.elements:
            matches = await hybrid_service.search(element, top_k=5)
            for match in matches:
                meta = match.get('metadata', {})
                pid = meta.get('patent_id', "Unknown_Patent")
                
                if pid not in patent_scores:
                    patent_scores[pid] = 0
                    patent_evidence[pid] = []
                
                patent_scores[pid] += match['score']
                
                doc_id = match.get('id', 'unknown')
                if not any(e['id'] == doc_id for e in patent_evidence[pid]):
                    patent_evidence[pid].append({
                        "id": doc_id,
                        "text": match['text'],
                        "vector_score": match.get('vector_score', 0.0)
                    })
        
        # Check Relevance
        max_relevance = 0.0
        for pid, chunks in patent_evidence.items():
            for c in chunks:
                max_relevance = max(max_relevance, c.get('vector_score', 0.0))
        
        if max_relevance < 0.42:
            result = {
                "claim_text": claim_text,
                "elements": claim_elements.elements,
                "prior_art_analyses": [],
                "overall_risk": {
                    "novelty_risk": "Low (No Relevant Art)",
                    "obviousness_risk": "Low (No Relevant Art)"
                }
            }
            job_store.update_job(job_id, "COMPLETED", result)
            return

        # 3. Analyze Top Candidates
        sorted_patents = sorted(patent_scores.items(), key=lambda x: x[1], reverse=True)
        top_candidates = sorted_patents[:2]
        
        analyses = []
        for pid, score in top_candidates:
            evidence = {
                "patent_id": pid,
                "paragraphs": patent_evidence[pid]
            }
            analysis = await llm_service.analyze_patent(
                claim_text, 
                claim_elements.elements, 
                evidence,
                strict_mode=strict_mode
            )
            # Pydantic to dict
            analyses.append(analysis.dict())

        # 4. Risk Scoring
        element_support_map = {e: False for e in claim_elements.elements}
        for a in analyses:
            for ea in a['element_analysis']:
                if ea['support_type'].lower() in ["anticipated", "obvious"]:
                    element_support_map[ea['element']] = True
                    
        all_supported = all(element_support_map.values())
        overall_novelty = "High" if all_supported else "Low"
        overall_obviousness = "High" if all_supported else "Low"

        final_result = {
            "claim_text": claim_text,
            "elements": claim_elements.elements,
            "prior_art_analyses": analyses,
            "overall_risk": {
                "novelty_risk": overall_novelty,
                "obviousness_risk": overall_obviousness
            }
        }
        
        job_store.update_job(job_id, "COMPLETED", final_result)
        print(f"Job {job_id} Completed.")

    except Exception as e:
        print(f"Job {job_id} Failed: {e}")
        job_store.update_job(job_id, "FAILED", {"error": str(e)})

@app.post("/analyze-claim", response_model=AnalysisResponse)
async def analyze_claim(input: ClaimInput, background_tasks: BackgroundTasks):
    job_id = job_store.create_job()
    background_tasks.add_task(process_claim_analysis, job_id, input.claim_text, input.strict_mode)
    return AnalysisResponse(job_id=job_id, status="PENDING")

@app.get("/jobs/{job_id}", response_model=AnalysisResponse)
async def get_job_status(job_id: str):
    job = job_store.get_job(job_id)
    if not job:
        # Return a 404 if job not found, or a specific status
        raise HTTPException(status_code=404, detail="Job not found")
    return AnalysisResponse(job_id=job['id'], status=job['status'], result=job['result'])

@app.get("/health")
def health_check():
    return {"status": "ok", "message": "APEX Backend Running"}
```

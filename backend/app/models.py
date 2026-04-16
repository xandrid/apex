from typing import List, Optional, Dict, Any
from pydantic import BaseModel

class ClaimInput(BaseModel):
    claim_text: str
    claim_label: Optional[str] = None
    strict_mode: bool = True
    retrieval_mode: str = "hybrid"

class ClaimElements(BaseModel):
    preamble: Optional[str]
    elements: List[str]

class ParagraphMatch(BaseModel):
    paragraph_id: str
    patent_id: str
    text: str
    similarity_score: float
    metadata: Dict[str, Any] = {}

class ElementAnalysis(BaseModel):
    element: str
    matched_paragraph_ids: List[str]
    source_quote: Optional[str] = None
    citation_invalid: bool = False
    support_type: str  # "anticipated", "obvious", "unsupported"
    explanation: str

class OverallAssessment(BaseModel):
    novelty_risk: str # "low", "medium", "high"
    obviousness_risk: str # "low", "medium", "high"
    summary: str

class PatentAnalysis(BaseModel):
    prior_art_id: str
    title: Optional[str] = None
    rationale_bullets: List[str] = []
    element_analysis: List[ElementAnalysis]
    overall_assessment: OverallAssessment

class AnalysisResponse(BaseModel):
    claim_text: str
    elements: List[str]
    prior_art_analyses: List[PatentAnalysis]
    overall_risk: Dict[str, str] # e.g. {"novelty_risk": "high", ...}

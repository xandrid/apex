from app.models import PatentAnalysis, OverallAssessment

def calculate_risk_score(analysis: PatentAnalysis) -> PatentAnalysis:
    """
    Refines the risk scores of a PatentAnalysis based on deterministic rules:
    
    1. Unanticipated ("unsupported") Elements Rule:
       - If ANY core element is "unsupported", the Reference CANNOT anticipate the Claim.
       - Novelty Risk -> LOW (or MEDIUM if Obviousness is strong).
    
    2. Full Anticipation Rule:
       - If ALL elements are "anticipated", Novelty Risk -> HIGH.
       
    3. Obviousness Rule:
       - If some elements are "obvious" and the rest are "anticipated" (no "unsupported"),
         then Novelty Risk -> LOW/MEDIUM, but Obviousness Risk -> HIGH.
    """
    
    elements = analysis.element_analysis
    total_elements = len(elements)
    if total_elements == 0:
        return analysis

    count_anticipated = sum(1 for e in elements if e.support_type.lower() == "anticipated")
    count_obvious = sum(1 for e in elements if e.support_type.lower() == "obvious")
    count_unsupported = sum(1 for e in elements if e.support_type.lower() == "unsupported")

    # Start with the model's own assessment, then override based on rules
    current_novelty = analysis.overall_assessment.novelty_risk.lower()  
    current_obviousness = analysis.overall_assessment.obviousness_risk.lower()
    
    new_novelty = current_novelty
    new_obviousness = current_obviousness
    new_summary = analysis.overall_assessment.summary

    # RULE 1: Missing Elements = No Anticipation
    if count_unsupported > 0:
        new_novelty = "low"
        # If many things are unsupported, obviousness is also likely low/medium unless explicitly argued otherwise
        if new_obviousness == "high" and count_unsupported > (total_elements * 0.5):
             new_obviousness = "medium"
    
    # RULE 2: Perfect Match
    elif count_anticipated == total_elements:
        new_novelty = "high"
        new_obviousness = "high" # Technically anticipation implies obviousness (stronger form)
        
    # RULE 3: Obviousness Combination
    elif count_unsupported == 0 and count_obvious > 0:
        # Everything is found, but some only via obviousness
        new_novelty = "low" # Not strictly anticipated
        new_obviousness = "high"

    # Consistency Check: Make sure we don't have High Novelty Risk if logic says Low
    analysis.overall_assessment.novelty_risk = new_novelty.title() if new_novelty in ["low", "medium", "high"] else new_novelty
    analysis.overall_assessment.obviousness_risk = new_obviousness.title() if new_obviousness in ["low", "medium", "high"] else new_obviousness
    
    # Optional: Append an automated note if we overrode the model (omitted for now to keep it clean)
    
    return analysis

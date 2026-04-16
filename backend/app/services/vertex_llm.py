import json
import os
from typing import List, Dict, Any
from dotenv import load_dotenv
import google.generativeai as genai
from app.models import ClaimElements, ElementAnalysis, PatentAnalysis, OverallAssessment
from app.core.prompts import (
    CLAIM_DECOMPOSITION_SYSTEM_PROMPT,
    get_decomposition_prompt,
    EXAMINER_SYSTEM_PROMPT,
    get_analysis_user_prompt,
    REBUTTAL_SYSTEM_PROMPT,
    OFFICE_ACTION_TEMPLATE
)
from app.core.risk_logic import calculate_risk_score

# Load environment variables from .env file
load_dotenv()

print(f"DEBUG: Current CWD: {os.getcwd()}")
print(f"DEBUG: .env exists: {os.path.exists('.env')}")
print(f"DEBUG: GOOGLE_API_KEY from env: {os.getenv('GOOGLE_API_KEY')[:10] if os.getenv('GOOGLE_API_KEY') else 'None'}")

# Initialize Google Generative AI
API_KEY = os.getenv("GOOGLE_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)
else:
    print("WARNING: GOOGLE_API_KEY not found in environment variables.")

class VertexLLMService:
    def __init__(self):
        # Use gemini-2.0-flash-lite for Google AI Studio API (API Key auth)
        self.model = genai.GenerativeModel("models/gemini-2.0-flash-lite") 

    async def decompose_claim(self, claim_text: str) -> ClaimElements:
        system_instruction = CLAIM_DECOMPOSITION_SYSTEM_PROMPT
        user_prompt = get_decomposition_prompt(claim_text)
        
        # We can pass system instruction if the model supports it, or append it.
        # Gemini 1.5/2.0 supports system_instruction at model init or we can just prepend.
        # For simplicity with this library wrapper, prepending constitutes a robust approach.
        full_prompt = f"{system_instruction}\n\n{user_prompt}"

        response = self.model.generate_content(full_prompt, generation_config={"response_mime_type": "application/json"})
        try:
            data = json.loads(response.text)
            return ClaimElements(**data)
        except Exception as e:
            print(f"Error parsing decomposition response: {e}")
            # Fallback for MVP if parsing fails
            return ClaimElements(preamble=None, elements=[claim_text])

    async def analyze_patent(self, claim_text: str, elements: List[str], prior_art_data: Dict[str, Any], strict_mode: bool = True) -> PatentAnalysis:
        """
        prior_art_data should contain:
        - patent_id
        - title
        - paragraphs: List[Dict] with 'id' and 'text'
        """
        
        prior_art_id = prior_art_data.get("patent_id", "Unknown")
        paragraphs = prior_art_data.get("paragraphs", [])
        # Create a set of valid IDs for verification
        valid_paragraph_ids = set(p['id'] for p in paragraphs)
        
        # Create a formatted string of paragraphs for the prompt
        paragraphs_text = "\n".join([f"[{p['id']}] {p['text']}" for p in paragraphs])
        
        system_instruction = EXAMINER_SYSTEM_PROMPT
        user_prompt = get_analysis_user_prompt(claim_text, elements, prior_art_id, paragraphs_text)
        
        # Combine for generation
        full_prompt = f"{system_instruction}\n\n{user_prompt}"
        
        response = self.model.generate_content(full_prompt, generation_config={"response_mime_type": "application/json"})
        
        try:
            text = response.text
            # Simple cleanup for common JSON errors like trailing commas
            import re
            text = re.sub(r',\s*}', '}', text)
            text = re.sub(r',\s*]', ']', text)
            data = json.loads(text)
            
            # Post-Processing: Verify Citations
            # Enhanced Verification: Map text-based IDs (e.g. [0023]) to system IDs (e.g. p_0)
            
            # Build a map of potential text-ids to system-ids
            # We look for patterns like [0001] inside the text of each paragraph
            text_id_map = {}
            import re
            for p in paragraphs:
                # Find all [XXXX] patterns in the text
                matches = re.findall(r'\[(\d{4})\]', p['text'])
                for m in matches:
                    text_id_map[m] = p['id']
                # Also map the ID itself if it looks different
                text_id_map[p['id']] = p['id']

            for analysis in data.get("element_analysis", []):
                verified_ids = []
                for pid in analysis.get("matched_paragraph_ids", []):
                    # 1. Direct System ID Match
                    if pid in valid_paragraph_ids:
                        verified_ids.append(pid)
                    # 2. Text Content Match (e.g. citing [0023] which is inside p_0)
                    elif pid in text_id_map:
                        system_id = text_id_map[pid]
                        print(f"INFO: Mapped citation '{pid}' -> '{system_id}'")
                        if system_id not in verified_ids:
                            verified_ids.append(system_id)
                    # 3. Clean-up (remove brackets if LLM left them)
                    else:
                        clean_pid = pid.replace('[', '').replace(']', '')
                        if clean_pid in valid_paragraph_ids:
                            verified_ids.append(clean_pid)
                        elif clean_pid in text_id_map:
                             system_id = text_id_map[clean_pid]
                             if system_id not in verified_ids:
                                verified_ids.append(system_id)
                        else:
                            if strict_mode:
                                print(f"WARNING: Hallucinated Citation Removed: {pid}")
                            else:
                                 # In non-strict mode, keep it but maybe flag it?
                                 # For simplicity, just keep it. It won't link to anything in UI but it won't be deleted.
                                 verified_ids.append(pid)
                
                analysis["matched_paragraph_ids"] = verified_ids
            
            # Post-Processing: Quote Verification (New)
            # Ensure 'source_quote' actually exists in the provided text.
            combined_text = " ".join([p.get('text', '').lower() for p in paragraphs])
            
            for analysis_item in data.get("element_analysis", []):
                quote = analysis_item.get("source_quote")
                # Clean quote for soft matching
                if quote and isinstance(quote, str):
                    clean_quote = " ".join(quote.lower().split()) # normalize whitespace
                    clean_text = " ".join(combined_text.split())
                    
                    if clean_quote not in clean_text:
                        # Soft fail: Check fuzzy or partial? For stricter conservative mode, Fail it.
                        print(f"WARNING: Quote Verification Failed. Downgrading element '{analysis_item.get('element')[:20]}...'")
                        analysis_item["citation_invalid"] = True
                        analysis_item["support_type"] = "unsupported"
                        # We keep the quote so user can see what was hallucinated, OR we clear it. User said flag it.
                        # "downgrade the element to unsupported and flag citation_invalid=true"
                elif analysis_item.get("support_type") == "anticipated":
                     # Anticipated but no quote? Flag it.
                     analysis_item["citation_invalid"] = True
                     analysis_item["support_type"] = "unsupported"
            
            # Post-Processing: Risk Consistency
            # If ANY element is 'unsupported' by this patent, the patent CANNOT anticipate the claim.
            # Therefore, Novelty Risk for this specific patent must be Low (or at most Medium if Obviousness is High).
            has_unsupported = any(e['support_type'] == 'unsupported' for e in data.get("element_analysis", []))
            
            if has_unsupported:
                # Force Low Novelty Risk if elements are missing
                if 'overall_assessment' in data:
                    data['overall_assessment']['novelty_risk'] = 'Low'
                    # Update summary to reflect this
                    data['overall_assessment']['summary'] = "This reference fails to disclose all claim elements, notably missing requirements. Therefore, it does not anticipate the claim." + (" " + data['overall_assessment']['summary'] if 'summary' in data['overall_assessment'] else "")

            return PatentAnalysis(**data)
        except Exception as e:
            print(f"Error parsing analysis response: {e}")
            return PatentAnalysis(
                prior_art_id=prior_art_id,
                element_analysis=[],
                overall_assessment=OverallAssessment(novelty_risk="unknown", obviousness_risk="unknown", summary="Error generating analysis")
            )

    async def rebut_analysis(self, current_analysis: PatentAnalysis, user_argument: str) -> PatentAnalysis:
        # Processes a user's rebuttal argument and updates the analysis.
        user_prompt = f"""
INPUTS:
PRIOR ANALYSIS:
{current_analysis.model_dump_json(indent=2)}

APPLICANT ARGUMENT:
"{user_argument}"
"""
        full_prompt = f"{REBUTTAL_SYSTEM_PROMPT}\n\n{user_prompt}"
        
        response = self.model.generate_content(full_prompt, generation_config={"response_mime_type": "application/json"})
        
        try:
            data = json.loads(response.text)
            updated_analysis = PatentAnalysis(**data)
            # Re-run risk logic to ensure consistency
            return calculate_risk_score(updated_analysis)
        except Exception as e:
            print(f"Error processing rebuttal: {e}")
            return current_analysis

    async def generate_office_action(self, analysis: PatentAnalysis) -> str:
        # Generates a formal Office Action text based on the analysis.
        analysis_json = analysis.model_dump_json(indent=2)
        prompt = OFFICE_ACTION_TEMPLATE.format(analysis_json=analysis_json)
        
        response = self.model.generate_content(prompt)
        return response.text

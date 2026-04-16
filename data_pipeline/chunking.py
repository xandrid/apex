import re
from typing import List, Dict, Any

class SmartChunker:
    """
    Splits patent text into semantic chunks suitable for retrieval.
    """

    @staticmethod
    def chunk_claims(claims_text: str) -> List[str]:
        """
        Splits a full claims string into individual claims.
        Assumes standard numbering "1. ", "2. ", etc.
        """
        if not claims_text:
            return []

        # Regex to find "N. " at the start of a line or after a newline
        # We use a lookahead to split but keep the delimiter, or just split and reconstruct
        # A simple robust way is to split by `\n\d+\.` and re-attach.
        
        # Pattern: Newline followed by number and dot.
        # Note: This is a heuristic. Patent formatting varies.
        
        # Split by regex looking for "1. ", "2. " etc.
        # We capture the number so we can re-attach it.
        parts = re.split(r'(\n\d+\.\s+)', "\n" + claims_text.strip())
        
        chunks = []
        current_chunk = ""
        
        for part in parts:
            if re.match(r'\n\d+\.\s+', part):
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = part.strip() # Start new chunk with the number
            else:
                current_chunk += part
                
        if current_chunk:
            chunks.append(current_chunk.strip())
            
        return [c for c in chunks if c] # Filter empty

    @staticmethod
    def chunk_description(description_text: str) -> List[str]:
        """
        Splits description by paragraph identifiers like [0001], [0002].
        """
        if not description_text:
            return []

        # Pattern: `[0001]` or `[0023]`
        # We want to split *before* each pattern.
        
        # Regex to find paragraph markers
        pattern = r'(\[\d{4}\])'
        
        parts = re.split(pattern, description_text)
        
        chunks = []
        current_chunk = ""
        
        # The split will look like: ["preamble", "[0001]", "text...", "[0002]", "text..."]
        
        # We want to combine marker + text
        iterator = iter(parts)
        
        # Handle potential text before first marker
        first = next(iterator, "")
        if first.strip():
             chunks.append(first.strip())
             
        try:
            while True:
                marker = next(iterator) # e.g. [0001]
                text = next(iterator)   # e.g. " This is the text..."
                chunks.append(f"{marker} {text}".strip())
        except StopIteration:
            pass
            
        return chunks

    @staticmethod
    def process_patent(patent_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Takes raw patent data and returns a list of chunk objects ready for embedding.
        """
        chunks = []
        base_metadata = {
            "patent_id": patent_data["publication_number"], # Standardize on patent_id
            "publication_number": patent_data["publication_number"],
            "title": patent_data["title"],
            "publication_date": patent_data["publication_date"],
            "cpc": patent_data["cpc"]
        }

        # Chunk Claims
        claim_chunks = SmartChunker.chunk_claims(patent_data.get("claims", ""))
        for i, text in enumerate(claim_chunks):
            chunks.append({
                "text": text,
                "metadata": {
                    **base_metadata,
                    "type": "claim",
                    "chunk_index": i,
                    "claim_number": i + 1,
                    "id": f"claim_{i+1}" # Standardize ID
                }
            })

        # Chunk Description
        desc_chunks = SmartChunker.chunk_description(patent_data.get("description", ""))
        for i, text in enumerate(desc_chunks):
            chunks.append({
                "text": text,
                "metadata": {
                    **base_metadata,
                    "type": "description",
                    "chunk_index": i,
                    "paragraph_id": text[:6] if text.startswith("[") else f"p_{i}",
                    "id": text[:6] if text.startswith("[") else f"p_{i}" # Standardize ID
                }
            })

        return chunks

if __name__ == "__main__":
    # Test
    sample_claims = "1. A widget comprising: a gear. 2. The widget of claim 1, wherein the gear is red."
    print(f"Claims: {SmartChunker.chunk_claims(sample_claims)}")
    
    sample_desc = "Background info. [0001] This is para 1. [0002] This is para 2."
    print(f"Desc: {SmartChunker.chunk_description(sample_desc)}")

import asyncio
import sys
import os

# Ensure backend matches path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.app.services.vector_search import search_paragraphs

async def main():
    print("Testing search_paragraphs...")
    # Search for something likely to be in a patent or just testing the mechanism
    query = "wireless communication"
    params = {"top_k": 3}
    matches = await search_paragraphs(query, **params)
    
    print(f"Submitting query: '{query}'")
    if not matches:
        print("No matches found (index might be empty or mock embedding used).")
    else:
        print(f"Found {len(matches)} matches:")
        for i, m in enumerate(matches):
            print(f"{i+1}. [{m.similarity_score:.4f}] {m.patent_id} (Paragraph: {m.paragraph_id})")
            print(f"   Snippet: {m.text[:100]}...")

if __name__ == "__main__":
    asyncio.run(main())

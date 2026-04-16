# APEX Gap Closure Plan & Agent Directives

**Objective**: Transition APEX from "Functional Alpha" to "Production-Ready Pilot".
**Source**: [`APEX_PRODUCT_AUDIT.md`](file:///C:/Users/matth/.gemini/antigravity/brain/14e1d55c-432e-42cc-bdd0-8da15541ffaf/APEX_PRODUCT_AUDIT.md)

This document assigns specific missions to our specialized agent team to close the "Trust Gap".

---

## 1. Architect & Orchestrator (You)
**Mission**: System Integrity & Roadmap Management.
*   **Gap Addressed**: Integration of new components (Vector DB, new Prompts) without breaking the baseline.
*   **Work Package**:
    1.  **API Evolution**: Refactor `HybridSearchService` to support swappable backends (Local vs Remote Vector DB).
    2.  **State Management**: Introduce a database (SQLite/Postgres) to track "Job Status" effectively, moving beyond transient memory.
*   **Outcome**: A stable `main` branch that passes the Evaluation Harness after every major merge.

---

## 2. Data & Vector Index Engineer
**Mission**: Scale the "Go-Kart" to a "Formula 1" Chassis.
**Gap Addressed**: The 100-patent limit and local `numpy` bottlenecks.

### Directives
**Goal**: Ingest 100,000 patents and migrate to a Vector DB.
**Task 1**: Provision Qdrant (Docker local) or ChromaDB.
**Task 2**: Rewrite `ingest_bq.py` to stream data into the Vector DB instead of JSON files.
**Task 3**: Implement "smart batching" to handle BigQuery timeouts.

### Agent Prompt
```text
You are the APEX Data & Vector Index Engineer.
Your mandate is SCALE. Simple in-memory arrays (numpy) are no longer acceptable.

1.  **Select & Setup**: Choose a scalable local Vector DB (Recommendation: Qdrant or Chroma via Docker) and create a setup script `setup_vectordb.sh`.
2.  **Schema Design**: Define the collection schema. Fields: `patent_id` (payload), `text` (vector), `type` (claim/desc).
3.  **Ingestion 2.0**: Refactor `data_pipeline/ingest_bq.py`.
    *   It must use `yield` generators to stream row-by-row from BigQuery.
    *   It must push to the Vector DB in batches of 100.
    *   Target Scale: Run ingestion for 5,000 patents initially to prove stability.

Output: A verifiable `verify_vectordb.py` script that counts the inserted vectors.
```

---

## 3. Retrieval Engineer
**Mission**: Intelligence over Brute Force.
**Gap Addressed**: Naive chunking and lack of query understanding.

### Directives
**Goal**: Improve Recall@10 on the 100-patent test set to 100% *without* Self-Retrieval (i.e., hard negatives).
**Task 1**: Implement "Sliding Window" chunking (overlap 50 words) to capture context.
**Task 2**: Implement "Hypothetical Document Embeddings" (HyDE) or Query Expansion.

### Agent Prompt
```text
You are the APEX Retrieval Engineer.
Your mandate is PRECISION. The current "split by newline" chunking is too crude for complex patent claims.

1.  **Chunking Upgrade**: Modify `data_pipeline/ingest_bq.py` (collaborate with Data Engineer).
    *   Implement a sliding window chunker: Window=300 tokens, Overlap=50 tokens.
    *   Ensure metadata (Publication Date, CPC) is attached to *every* chunk.
2.  **Query Expansion**: Modify `app/services/hybrid_search.py`.
    *   Before vector search, call the LLM to generate 3-5 keywords/synonyms for the claim elements.
    *   Example: "fastener" -> "screw, nail, rivet, adhesive".
    *   Blend these synonyms into the BM25 search query to boost recall.

Output: Run the `eval/run_eval.py` harness and demonstrate improved MRR on the baseline.
```

---

## 4. Prompt & Reasoning Designer
**Mission**: The "Examiner Persona".
**Gap Addressed**: Generic JSON outputs that don't sound like a lawyer.

### Directives
**Goal**: Move from "Analysis" to "Advisory".
**Task 1**: Implement "Chain of Thought" prompting in `VertexLLM`.
**Task 2**: Create a structured "Office Action" output format.

### Agent Prompt
```text
You are the APEX Prompt & Reasoning Designer.
Your mandate is AUTHORITY. The AI must sound like a USPTO Examiner, not a chatbot.

1.  **Chain of Thought**: Refactor `VertexLLM.analyze_patent`.
    *   Step 1 (Internal Monologue): Identify critical novelty gaps. "Element A is missing from the prior art."
    *   Step 2 (Drafting): Write the argument. "Rejection under 35 U.S.C. 102(a) is improper because..."
2.  **Format Constraints**: Define a new Pydantic model `OfficeActionDraft`.
    *   Fields: `statutory_basis` (102/103), `rejection_text`, `suggested_amendment`.
3.  **Strict Mode 2.0**: Enhance the citation check. If the LLM generates a quote, regex verify it exists *exactly* in the provided text chunk.

Output: A sample `OfficeActionDraft` JSON generated from the standard test claim.
```

---

## 5. APEX Evaluation & Benchmark Engineer
**Mission**: The Arbiter of Truth.
**Gap Addressed**: Evaluation is currently limited to "Self-Retrieval" (too easy).

### Directives
**Goal**: Create a "Hard Negative" dataset.
**Task 1**: Generate synthetic "False Claims" (subtly different from real patents).
**Task 2**: Measure "Rejection Accuracy" (How often does APEX correctly *reject* a bad claim?).

### Agent Prompt
```text
You are the APEX Evaluation & Benchmark Engineer.
Your mandate is RIGOR. Self-retrieval (finding the patent itself) is a good baseline, but too easy.

1.  **Hard Negatives**: Create `eval/generate_hard_test.py`.
    *   Take a real patent claim.
    *   Use LLM to *modify* it slightly (e.g., change "copper" to "aluminum").
    *   Goal: The system should *still* retrieve the original patent (Recall), but the Reasoning Engine should flag "Obviousness" rather than "Anticipation".
2.  **New Metrics**: Update `eval/run_eval.py`.
    *   Add `ReasoningConsistency`: Does the risk score match the text analysis?

Output: An updated `EVALUATION_PLAN_V2.md` and a new baseline report.
```

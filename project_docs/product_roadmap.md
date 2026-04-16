# APEX Product Roadmap: MVP to Production

## Vision
Transform APEX from a prototype into a "legal-grade" patent analysis platform capable of generating examiner-level office actions with high accuracy and grounding.

## 1. Data Strategy (Hybrid Approach)
Legal accuracy requires comprehensive, up-to-date, and clean data. We will use a **Hybrid Strategy**:

### A. Search Engine Data (The "Prior Art" Database)
-   **Source**: **Google Patents Public Datasets (BigQuery)**.
-   **Why**: Immediate access to parsed, structured global patent text. Zero infrastructure overhead for parsing XML.
-   **Usage**: Populates the Vector Search index with Claims and Descriptions.

### B. Training Data (The "Examiner Logic")
-   **Source**: **USPTO Bulk Data (Office Actions & File Wrappers)**.
-   **Why**: BigQuery lacks the detailed "back-and-forth" arguments between examiners and lawyers. We need this to train the AI on *how* to reject a claim.
-   **Usage**: Offline pipeline to build a fine-tuning dataset for the Gemini model.

### ETL Pipeline (Extract, Transform, Load)
-   **Orchestration**: **Google Cloud Composer (Airflow)** or **Cloud Run Jobs**.
- **Processing**:
    1.  **Ingest**: Pull patent text and metadata from BigQuery.
    2.  **Cleaning**: Remove boilerplate, OCR errors, and formatting noise.
    3.  **Smart Chunking**: **CRITICAL**. Do not chunk by token count alone. Chunk by logical sections:
        - *Abstract*
        - *Claims* (each claim is a chunk)
        - *Detailed Description* (chunk by paragraphs `[0001]`, `[0002]`)
        - *Drawings* (descriptions of figures)
    4.  **Enrichment**: Tag chunks with metadata (CPC codes, filing date, assignee).
- **Storage**:
    - **Vector Store**: **Vertex AI Vector Search** (high scale, low latency).
    - **Document Store**: **Firestore** or **BigQuery** (to store the full text for retrieval after search).

## 2. AI & Accuracy (The Brain)
To achieve "legal level accuracy," we cannot rely on zero-shot prompting alone.

### Model Strategy
- **Base Model**: **Gemini 1.5 Pro** (not Flash). We need the massive context window (2M tokens) to load entire prior art patents into context for deep comparison.
- **Fine-Tuning**:
    - **Goal**: Teach the "Examiner Persona" and "Rejection Structure" (e.g., 102 Anticipation vs. 103 Obviousness).
    - **Dataset**: Pairs of (Claim + Prior Art) -> (Office Action Rejection).
    - **Technique**: **Vertex AI Supervised Fine-Tuning (SFT)**.

### Grounding & RAG (Retrieval Augmented Generation)
- **Hybrid Search**: **CRITICAL**. Vector search finds *conceptually* similar text, but legal search needs *exact* keywords.
    - Implementation: Combine **Vertex AI Vector Search** (Dense) + **Keyword Search** (Sparse/BM25).
    - Re-ranking: Use a Cross-Encoder model to re-rank the top 50 results before sending to the LLM.
- **Citation Engine**:
    - The AI must not just generate text; it must generate **offsets/indices**.
    - We will enforce a strict output schema where every assertion must be backed by a `source_id` and `paragraph_id`.

## 3. Vector Search & Embeddings
- **Embedding Model**: **Gecko (text-embedding-004)** is strong, but for legal, we might explore **LegalBERT** or fine-tuned Gecko embeddings if accuracy lags.
- **Index Structure**:
    - Create separate indices for *Claims* vs. *Descriptions*. Searching claims against claims finds conflicting patents; searching claims against descriptions finds prior art.

## 4. Architecture Evolution

### Current MVP (Mock/Simple)
- **Frontend**: Next.js
- **Backend**: FastAPI
- **Auth**: API Key
- **Search**: Mock / Basic Gemini

## Product Roadmap: APEX (Automated Patent Examination)

## 🚀 Current Status: Phase 5 Complete (Zero-Cost Production Prototype)
The system is now a functional, locally-hosted search engine with real data persistence, strict AI accuracy, and a premium frontend.

---

## Phase 6: Cloud Native Scaling (Next Up)
**Goal:** Move from local prototype to a scalable web application.
- [ ] **Infrastructure**: Deploy Backend to **Google Cloud Run** (Serverless).
- [ ] **Database**: Migrate from `LocalDataStore` to **Milvus** or **Pinecone** for scalable vector search (>1M patents).
- [ ] **Authentication**: Implement **Clerk** or **Firebase Auth** for user management.

## Phase 7: Advanced Legal AI
**Goal:** Enhance the AI's legal reasoning capabilities.
- [ ] **Fine-Tuning**: Fine-tune Gemini 1.5 Pro on a dataset of real USPTO Office Actions to learn the specific tone and rejection structures.
- [ ] **Multi-Hop Reasoning**: Implement "Graph RAG" to connect claims across multiple patents.
- [ ] **PDF Generation**: Auto-generate formal "Office Action" PDF reports.

## Phase 8: Enterprise Integration
**Goal:** Integrate with law firm workflows.
- [ ] **Docketing System API**: Connect to Clio or FoundationIP.
- [ ] **Team Collaboration**: Shared analysis workspaces.
- [ ] **Billing Integration**: Track billable hours per analysis.

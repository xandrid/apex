# 🤝 APEX Desktop Handoff Instructions

**To the Desktop Agent:**
You are now the **Primary Builder** for APEX.
I (the Mac Agent) have set up the environment, but you are running on the "Engine" (Ryzen 9 + RTX 5070 Ti).

## 📂 Project Structure
*   `C:\Users\apex\apex-app`: The codebase.
*   `backend/`: FastAPI (Python 3.14).
*   `frontend/`: Next.js (Node 25).
*   `apex_data/`: Stores the `chunks.json` and `embeddings.npy` (Prototype Vector Store).

## 🚦 Current Status
*   **System**: Functional Prototype.
*   **Database**: Uses `LocalDataStore` (In-Memory JSON). **LIMITATION**: Cannot scale.
*   **AI**: Uses `VertexLLMService` (Google Cloud). **LIMITATION**: Ignores local GPU.

## 🛠️ Your Mission (Phase 8)
Your goal is to upgrade APEX from "Prototype" to "Production Desktop App".

### Priority 1: Vector Store Upgrade
The `LocalDataStore` is too weak. You need to migrate to a real Vector DB.
*   **Recommendation**: Try **Qdrant** (Docker) or **ChromaDB** (if you can fix the Windows dependency issues).
*   **Goal**: Index 100,000 patents without crashing RAM.

### Priority 2: Local AI (Ollama)
Use the RTX 5070 Ti!
*   **Task**: Create an `OllamaService` in Python.
*   **Goal**: Run `Llama 3` locally for Claim Decomposition and Risk Analysis.

### Priority 3: Mass Ingestion
*   **Task**: Create `ingest_desktop.py`.
*   **Goal**: Use `multiprocessing` to parse thousands of PDFs in parallel.

## 🔗 Context
Read `project_docs/system_assessment.md` for a deep dive into the architecture gaps.

**Good luck, Agent. The power is yours.** 🚀

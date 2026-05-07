# AI-Powered Document Verification & Background Intelligence System

An enterprise-grade AI system for document processing, verification, and fraud detection.

## 🚀 Project Roadmap

### Phase 1: Project Foundation ✅
- FastAPI Backend initialized
- Modular architecture (Routes, Services, Models)
- Environment configuration system
- Secure file upload endpoint
- Auto-generated Swagger documentation

### Upcoming Phases
- **Phase 2:** Hybrid OCR Pipeline (NVIDIA + EasyOCR)
- **Phase 3:** Document Classification
- **Phase 4:** Specialized AI Parsing
- **Phase 5:** Verification Intelligence Engine
- **Phase 6:** Embeddings + Vector Search (FAISS)
- **Phase 7:** Multi-Agent Orchestration (LangGraph)
- **Phase 8:** Report Generation (PDF)
- **Phase 9:** Frontend Dashboard (Next.js)

## 🛠 Tech Stack
- **Backend:** FastAPI, Python 3.10+
- **AI/ML:** NVIDIA NeMo Retriever OCR, EasyOCR, Nemotron-3-Super
- **Orchestration:** LangGraph, LangChain
- **Database:** FAISS (Vector), PostgreSQL (Relational)
- **Frontend:** Next.js, Tailwind CSS

## ⚙️ Setup & Installation

### Backend Setup
1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Create a `.env` file in the `backend/` directory:
   ```env
   NVIDIA_API_KEY=your_key_here
   DATABASE_URL=sqlite:///./test.db
   ```
5. Run the server:
   ```bash
   uvicorn app.main:app --reload
   ```

## 📄 Documentation
Once the server is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- Redoc: `http://localhost:8000/redoc`

# AI-Powered Document Verification & Background Intelligence System

An enterprise-grade AI system for automated document processing, verification, and fraud detection. This project demonstrates a production-oriented approach to building AI pipelines with hybrid OCR, structured parsing, and multi-agent orchestration.

## 🏗 System Architecture & Flow

```text
Document Upload
      ↓
Resilient Hybrid OCR Engine (NVIDIA NIM + EasyOCR Fallback)
      ↓
Rule-Based Document Classification
      ↓
LLM-Driven Structured Parsing (Nemotron-3-Super)
      ↓
Verification Intelligence Engine (Cross-document consistency)
      ↓
Embedding-Based Semantic Analysis (FAISS + sentence-transformers)
      ↓
Automated Risk Report Generation
```

## 🚀 Key Engineering Features

- **Resilient Hybrid OCR Pipeline**: Implemented a dual-engine architecture using NVIDIA NIM OCR as the primary engine with an automatic EasyOCR fallback for high availability.
- **Agentic Workflow Orchestration**: Built using LangGraph to coordinate OCR, parsing, verification, and report generation pipelines in a deterministic state machine.
- **Structured JSON Extraction**: Advanced prompt engineering for extracting high-fidelity structured data with Pydantic schema validation.
- **Embedding-Based Semantic Verification**: Utilizes FAISS vector search and sentence embeddings to detect unsupported claims and inconsistencies across documents.
- **Deterministic Classification**: Lightweight rule-based classification optimized for high-accuracy identification of standard IDs (Aadhaar, PAN) and professional documents.
- **Explainable Verification**: Confidence scoring and detailed fraud signal detection for transparent decision-making.
- **Modular Microservice Architecture**: Designed for scalability with clear separation between routing, business logic, and AI services.
- **Containerized Deployment**: Fully dockerized environment for consistent development and production parity.

## 🛠 Tech Stack

| Domain | Technology |
| :--- | :--- |
| **Backend** | FastAPI |
| **Primary OCR** | NVIDIA NeMo Retriever OCR |
| **Fallback OCR** | EasyOCR |
| **LLM (Parsing)** | Nemotron-3-Super |
| **Embeddings** | sentence-transformers |
| **Vector DB** | FAISS |
| **Orchestration** | LangGraph |
| **Frontend** | Next.js 15 (App Router) |
| **Styling** | Tailwind CSS |
| **Deployment** | Docker |

## ⚙️ Setup & Installation

### 1. Environment Configuration
Create a `.env` file in the `backend/` directory:
```env
NVIDIA_API_KEY=your_nvidia_api_key
SECRET_KEY=your_jwt_secret_key
DATABASE_URL=sqlite:///./test.db
```

### 2. Docker Deployment (Recommended)
```bash
docker-compose up --build
```

### 3. Manual Installation
**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## 📄 API Documentation
Once the backend is running, comprehensive documentation is available at:
- **Swagger UI**: `http://localhost:8000/docs`
- **Redoc**: `http://localhost:8000/redoc`

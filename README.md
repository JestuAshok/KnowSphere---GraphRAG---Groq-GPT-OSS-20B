# KnowSphere — GraphRAG Corporate Knowledge Explorer

<p align="center">
  <img src="https://img.shields.io/badge/GraphRAG-Enterprise-6366f1?style=for-the-badge&logo=diagram-next&logoColor=white" alt="GraphRAG" />
  <img src="https://img.shields.io/badge/FastAPI-0.104+-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/React-18.x-61DAFB?style=for-the-badge&logo=react&logoColor=black" alt="React" />
  <img src="https://img.shields.io/badge/Vite-5.x-646CFF?style=for-the-badge&logo=vite&logoColor=white" alt="Vite" />
  <img src="https://img.shields.io/badge/Neo4j-Graph%20DB-008CC1?style=for-the-badge&logo=neo4j&logoColor=white" alt="Neo4j" />
  <img src="https://img.shields.io/badge/FAISS-Vector%20Search-FF6F00?style=for-the-badge&logo=meta&logoColor=white" alt="FAISS" />
  <img src="https://img.shields.io/badge/Groq-GPT--OSS--20B-F05032?style=for-the-badge&logo=openai&logoColor=white" alt="Groq" />
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License" />
</p>

---

## 📌 Executive Summary

**KnowSphere** is an enterprise-grade **GraphRAG (Graph-Augmented Retrieval-Augmented Generation)** platform designed to tackle the fundamental limitation of standard vector RAG: **the inability to understand complex, multi-hop indirect relationships across disparate enterprise assets**.

By unifying **Neo4j/NetworkX graph traversal**, **FAISS dense semantic search**, and **Groq-accelerated LLM synthesis (GPT-OSS-20B)**, KnowSphere enables teams to navigate organizational silos, uncover cross-project dependencies, and answer questions grounded with verifiable document citations and interactive graph pathways.

---

## 🌟 Key Highlights & Capabilities

- **🔗 Hybrid GraphRAG Engine**: Combines Cypher graph traversal (for structural entity relations) with FAISS cosine similarity (for deep semantic document search).
- **⚡ Ultra-Low Latency Inference**: Powered by the **Groq API** (`openai/gpt-oss-20b`) with in-memory graph query response caching.
- **🗺️ Multi-Hop Dependency Discovery**: Seamlessly traces pathways like `Team A → Technology X → Project Phoenix` across teams, software stacks, and roadmaps.
- **📑 Verifiable Evidence & Citations**: Answers contain precise document citations, confidence metrics, and explicit graph-traversal route explanations.
- **🌐 Interactive Graph Visualization**: Explore organizational entities, technologies, documents, and teams through rich dynamic visual networks.
- **🚀 Zero-Docker Embedded Mode**: Features a pure Python fallback (NetworkX + SQLite + local FAISS index), enabling immediate local execution with zero container overhead.
- **🐳 Enterprise Container Ready**: Fully configured for production deployments via Podman or Docker Compose.

---

## 🏗️ System Architecture

```mermaid
flowchart TD
    User([User / Browser]) <--> Frontend[React + TypeScript + Vite UI]
    Frontend <--> FastAPI[FastAPI Backend Gateway]

    subgraph Hybrid Retrieval Pipeline
        FastAPI --> Retriever[Hybrid Retriever]
        Retriever -->|Dense Vector Search| FAISS[FAISS Vector Store\n(sentence-transformers all-MiniLM-L6-v2)]
        Retriever -->|Multi-Hop Path Traversal| GraphStore[(Neo4j / Embedded NetworkX Graph)]
    end

    subgraph Synthesis Engine
        Retriever --> Context[Context Aggregator & Formatter]
        Context --> Groq[Groq LLM Synthesis\nopenai/gpt-oss-20b]
        Groq --> Response[Structured JSON Response]
    end

    Response --> FastAPI
    FastAPI --> AppDB[(SQLite Metadata & Auth DB)]
```

---

## 🧰 Technology Stack

| Layer | Component | Description |
| :--- | :--- | :--- |
| **Frontend** | **React 18, Vite, TypeScript** | Responsive SPA with Tailwind CSS, Lucide icons, and React Flow graph explorer |
| **Backend** | **FastAPI, Python 3.11+** | High-performance asynchronous API with Pydantic validation and JWT auth |
| **Graph Database** | **Neo4j & NetworkX** | Native property graph with Cypher querying + in-memory NetworkX fallback |
| **Vector Store** | **FAISS (Meta)** | High-speed dense semantic similarity search over document chunks |
| **Embedding Model** | **`all-MiniLM-L6-v2`** | 384-dimensional dense sentence embeddings via Hugging Face `sentence-transformers` |
| **LLM Inference** | **Groq Cloud API** | Fast, token-efficient synthesis using `openai/gpt-oss-20b` |
| **Relational Storage**| **SQLite (SQLAlchemy/Aiosqlite)** | User accounts, query history, audit logs, and document metadata |

---

## 🚀 Getting Started

### Prerequisites

- **Python**: `3.11` or higher
- **Node.js**: `20.x` or higher & `npm`
- **Groq API Key**: Obtain a free API key at [console.groq.com](https://console.groq.com)

---

### Step 1: Clone Repository & Setup Environment

```bash
git clone https://github.com/JestuAshok/KnowSphere---GraphRAG---Groq-GPT-OSS-20B.git
cd KnowSphere---GraphRAG---Groq-GPT-OSS-20B

# Copy environment template
cp .env.example .env
```

Open `.env` and provide your Groq API key:
```ini
LLM_API_KEY=gsk_your_groq_api_key_here
LLM_MODEL=openai/gpt-oss-20b
LLM_BASE_URL=https://api.groq.com/openai/v1
```

---

### Step 2: Install Backend Dependencies

```bash
# Create and activate virtual environment
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

# Install requirements
pip install -r backend/requirements.txt
```

---

### Step 3: Install Frontend Dependencies

```bash
cd frontend
npm install
cd ..
```

---

### Step 4: Run Application (Native Embedded Mode)

KnowSphere includes a single runner script that coordinates both backend and frontend servers with pre-seeded data:

```bash
python run.py
```

- **Frontend**: [http://localhost:5173](http://localhost:5173)
- **Backend API**: [http://localhost:8000](http://localhost:8000)
- **Swagger Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)

#### Default Demo Credentials
- **Email**: `demo@knowsphere.ai`
- **Password**: `demo1234`

---

### Optional: Containerized Deployment (Podman / Docker)

If you prefer using full Neo4j graph containers:

```bash
# Podman
podman compose -f podman-compose.yml up --build

# Docker
docker compose -f podman-compose.yml up --build
```

---

## 💡 Example Scenario & Benchmark Query

Try asking the assistant:

> *"Which projects depend on technologies used by Team A and could be affected if that technology is discontinued?"*

### Expected GraphRAG Path Traced:
```
(Team A) ──[:USES]──> (Technology X/Y/Z) ──[:DEPENDS_ON]──> (Project Phoenix, Project Nova, Project Atlas)
```

**Output**:
- Comprehensive findings detailing the cascade effect.
- Cited source documents (`Tech_Roadmap.docx`, `Project_Dependencies.xlsx`).
- Visualized subgraph nodes showing the exact relationships in the interactive graph viewer.

---

## 📂 Project Structure

```
KnowSphere/
├── backend/
│   ├── app/
│   │   ├── api/            # REST API route controllers
│   │   │   ├── ask.py      # GraphRAG question-answering endpoint
│   │   │   ├── auth.py     # Authentication & JWT tokens
│   │   │   ├── graph.py    # Knowledge graph exploration & Cypher queries
│   │   │   └── ...
│   │   ├── core/           # Configuration, security, and DB sessions
│   │   ├── graph/          # Neo4j driver & NetworkX graph engine
│   │   ├── models/         # Pydantic schemas & SQLAlchemy models
│   │   └── retrieval/      # FAISS vector store, embedder & GraphRAG chain
│   ├── seed_data.py        # Enterprise sample dataset generator
│   └── requirements.txt    # Python backend dependencies
├── frontend/
│   ├── src/
│   │   ├── api/            # Typed backend API client
│   │   ├── components/     # UI widgets, layout, graph renderers
│   │   ├── pages/          # Ask, Graph, Documents, Analytics, Settings
│   │   └── types/          # TypeScript domain models
│   ├── package.json        # Frontend scripts & dependencies
│   └── vite.config.ts      # Vite development configuration
├── data/                   # Persistent data store (SQLite, Graph, FAISS)
├── podman-compose.yml      # Multi-container orchestration specification
├── run.py                  # Dual-stack native local launcher
└── README.md               # Project documentation
```

---

## 🛡️ Security & Best Practices

- **Zero Hardcoded Secrets**: Secrets and tokens are managed strictly via `.env`.
- **Pre-warmed Vector Embeddings**: SentenceTransformer instances are pre-cached to eliminate cold-start lag.
- **Fail-Safe Graph Engine**: Seamlessly switches between Neo4j cluster and in-process NetworkX without runtime crashes.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

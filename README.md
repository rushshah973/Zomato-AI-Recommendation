# Zomato AI Restaurant Recommender - Premium Dashboard

An AI-native restaurant recommendation system with a premium, glassmorphic dark-theme dashboard. The application is powered by a FastAPI Python backend utilizing the Zomato Hugging Face dataset, and a Next.js React frontend consulting Gemini AI for rankings, rationales, and summaries.

---

## Tech Stack & Architecture

| Area | Component |
|------|-----------|
| **Frontend UI** | Next.js 14, React 18, TypeScript, Framer Motion, Vanilla CSS |
| **Backend API** | FastAPI, Uvicorn, Pydantic |
| **AI Orchestrator** | Google Gemini (`gemini-3.5-flash` or `gemini-2.0-flash`) |
| **Dataset Store** | Hugging Face Dataset cache & local Parquet preprocessing |
| **Configuration** | `pydantic-settings` + `.env` secrets management |

---

## Quick Start (Local Run)

To run the application locally, you will need to spin up the **FastAPI Backend Server** and the **Next.js Frontend Client** simultaneously.

### 1. Setup Backend (FastAPI)
1. Initialize virtual environment and install Python dependencies:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. Configure environment keys:
   Create a `.env` file in the project root (use `.env.example` as a template) and add your Gemini API Key:
   ```env
   LLM_API_KEY=your_gemini_api_key_here
   ```
3. Start the uvicorn development API server:
   ```bash
   uvicorn app.api:app --host 0.0.0.0 --port 8000 --reload
   ```
   *The backend will load and preload the 51,000+ restaurant dataset on start, running on [http://localhost:8000](http://localhost:8000).*

### 2. Setup Frontend (Next.js)
1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install npm packages:
   ```bash
   npm install
   ```
   *Note: If Node.js is not globally available on your system, you can prefix commands using the project's local bin folder:*
   ```bash
   PATH="../.node/bin:$PATH" npm install
   ```
3. Launch the React development dashboard server:
   ```bash
   npm run dev -- -p 3000
   ```
4. Open the application in your browser:
   👉 **[http://localhost:3000](http://localhost:3000)**

---

## Git Branches & Versions

The repository contains two presentation layouts isolated in Git branches:
- **`main`**: The current default branch hosting the premium Next.js React dashboard and FastAPI backend integration.
- **`streamlit-version`**: The legacy Streamlit-native single-file custom component container.
  - Switch via: `git checkout streamlit-version`
  - Run via: `streamlit run app/main.py`

---

## Project Structure

```text
Zomato Milestone/
├── app/
│   ├── api.py            # FastAPI endpoints (GET /api/options, POST /api/recommendations)
│   ├── main.py           # Legacy Streamlit entry point (compat)
│   ├── models.py         # Domain models (UserPreferences, Recommendation, etc.)
│   ├── data/
│   │   ├── loader.py     # Dataset loader and cache (51,717 records)
│   │   └── preprocessor.py
│   ├── services/
│   │   ├── filter.py     # Deterministic FilterEngine (deduplication & rating sort)
│   │   ├── preferences.py
│   │   └── orchestrator.py
│   └── static/
│       └── index.html    # Legacy Streamlit components source (compat)
├── frontend/             # Next.js React client application
│   ├── package.json
│   ├── src/
│   │   └── app/
│   │       ├── globals.css  # Full glassmorphic Vanilla CSS design system
│   │       ├── layout.tsx
│   │       └── page.tsx     # Autocomplete, star controls, orb loaders, drawers
│   └── tsconfig.json
├── config/
│   └── settings.py       # Configuration settings
└── tests/                # 72 passing Python unit tests (pytest)
```

---

## Documentation

- [context.md](Docs/context.md) — Functional requirements and pipeline objectives
- [architecture.md](Docs/architecture.md) — Multi-tier Python and React architecture
- [implementation-plan.md](Docs/implementation-plan.md) — Current active build roadmap
- [implementation-plan-streamlit.md](Docs/implementation-plan-streamlit.md) — Legacy Streamlit custom HTML plan

# Multi-Tier Cloud Deployment Plan

This document outlines the step-by-step instructions to deploy the Zomato AI Restaurant Recommender system to the cloud:
1. **Python FastAPI Backend** $\rightarrow$ **Railway**
2. **Next.js React Frontend** $\rightarrow$ **Vercel**

---

## Architecture Diagram (Production Flow)

```text
[Browser Client] ────(HTTPS)────> [Vercel Deployment] (Frontend UI)
       │
   (REST API)
       │
       ▼
[Railway Deployment] (FastAPI Server)
       │
       ├────(HTTPS)────> [Hugging Face] (Restaurant Dataset Download)
       └────(HTTPS)────> [Google Gemini API] (Recommendation Engine)
```

---

## Phase 1: Deploy Backend to Railway

Railway is a cloud platform that automatically builds and deploys applications directly from GitHub.

### 1.1 Create Railway Project
1. Go to [Railway.app](https://railway.app) and sign in with GitHub.
2. Click **New Project** -> **Deploy from GitHub repo**.
3. Select your repository: `rushshah973/Zomato-AI-Recommendation`.
4. Choose the **`main`** branch.
5. Click **Deploy Now**. *(The initial build might fail until we configure environment variables).*

### 1.2 Configure Custom Start Command
Railway automatically detects `requirements.txt` and uses Python. We need to tell Railway how to launch uvicorn using the dynamic port injected by the environment:
1. Go to your service **Settings** tab in Railway.
2. Under the **Deploy** section, find **Start Command**.
3. Set the command to:
   ```bash
   uvicorn app.api:app --host 0.0.0.0 --port $PORT
   ```

### 1.3 Add Environment Variables
Go to the **Variables** tab in your Railway service and add the following configuration keys:

| Variable Name | Value | Description |
|---|---|---|
| `LLM_API_KEY` | `AIzaSy...` | Your Google Gemini API Key |
| `LLM_PROVIDER` | `gemini` | AI LLM provider engine |
| `LLM_MODEL` | `gemini-3.5-flash` | Gemini model name |
| `HF_DATASET_ID` | `ManikaSaini/zomato-restaurant-recommendation` | Dataset ID |
| `MAX_CANDIDATES` | `30` | Shortlist limit |
| `TOP_K` | `5` | Results count |
| `BUDGET_LOW_MAX` | `500` | Budget low cap in INR |
| `BUDGET_MEDIUM_MAX` | `1500` | Budget medium cap in INR |

### 1.4 Expose Public URL
1. Go to your service **Settings** tab.
2. Under **Networking**, click **Generate Domain** (or set up a custom domain).
3. Copy the generated URL (e.g., `https://zomato-ai-recommendation-production.up.railway.app`). **Keep this URL for the frontend configuration in Phase 2.**

---

## Phase 2: Deploy Frontend to Vercel

Vercel is a global edge network hosting platform optimized for React and Next.js.

### 2.1 Import Project on Vercel
1. Go to [Vercel.com](https://vercel.com) and log in with GitHub.
2. Click **Add New** -> **Project**.
3. Import your repository: `rushshah973/Zomato-AI-Recommendation`.

### 2.2 Configure Project Roots & Build Commands
Because our Next.js frontend is located in a subdirectory (`./frontend`), we must configure Vercel to compile only that folder:
1. Under **Project Name**, set it to `zomato-ai-recommender` (or choice).
2. Under **Root Directory**, click **Edit** and select the **`frontend`** directory.
3. Keep the **Framework Preset** as **Next.js**.
4. The Build and Development Settings will automatically detect standard settings:
   - Build Command: `next build`
   - Output Directory: `.next`
   - Install Command: `npm install` or `yarn install`

### 2.3 Set Production Environment Variables
Before building, Vercel needs to know the public URL of your FastAPI backend:
1. Expand the **Environment Variables** section.
2. Add the following key-value pair:
   - **Key**: `NEXT_PUBLIC_API_URL`
   - **Value**: `https://zomato-ai-recommendation-production.up.railway.app` *(Paste your Railway generated URL from Phase 1.4. Do not add a trailing slash)*

### 2.4 Deploy
1. Click the **Deploy** button.
2. Vercel will install npm dependencies, compile the production build, and serve your dashboard.
3. Vercel will provide a public link (e.g., `https://zomato-ai-recommender.vercel.app`). Open this link in your browser to verify the search, sliders, orb, and details drawer function successfully!

# Project Context: AI-Powered Restaurant Recommendation System

## Overview

Build an **AI-powered restaurant recommendation service** inspired by **Zomato**. The system combines **structured restaurant data** with a **Large Language Model (LLM)** to deliver personalized, human-like restaurant suggestions based on user preferences.

---

## Objective

Design and implement an application that:

1. Accepts user preferences (location, budget, cuisine, ratings, and more)
2. Uses a real-world restaurant dataset
3. Leverages an LLM to generate personalized, natural-language recommendations
4. Displays clear, useful results to the user

---

## Data Source

| Item | Detail |
|------|--------|
| **Dataset** | Zomato restaurant data on Hugging Face |
| **URL** | https://huggingface.co/datasets/ManikaSaini/zomato-restaurant-recommendation |
| **Relevant fields** | Restaurant name, location, cuisine, cost, rating, and related attributes |

---

## System Workflow

### 1. Data Ingestion

- Load and preprocess the Zomato dataset from Hugging Face
- Extract fields: restaurant name, location, cuisine, cost, rating, etc.

### 2. User Input

Collect preferences including:

| Preference | Examples |
|------------|----------|
| **Location** | Delhi, Bangalore |
| **Budget** | low, medium, high |
| **Cuisine** | Italian, Chinese |
| **Minimum rating** | Numeric threshold |
| **Additional** | family-friendly, quick service, etc. |

### 3. Integration Layer

- Filter and prepare restaurant data based on user input
- Pass structured results into an LLM prompt
- Design a prompt that helps the LLM **reason** and **rank** options

### 4. Recommendation Engine (LLM)

The LLM should:

- **Rank** restaurants
- **Explain** why each recommendation fits the user
- **Optionally** summarize the overall set of choices

### 5. Output Display

Present top recommendations in a user-friendly format with:

- Restaurant name
- Cuisine
- Rating
- Estimated cost
- AI-generated explanation

---

## Architecture Summary

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐     ┌──────────────┐
│   Dataset   │────▶│  Filter / Prep   │────▶│  LLM Prompt +   │────▶│   Display    │
│ (Hugging    │     │  (user prefs)    │     │  Rank + Explain │     │   Results    │
│  Face)      │     │                  │     │                 │     │              │
└─────────────┘     └──────────────────┘     └─────────────────┘     └──────────────┘
                            ▲
                            │
                    ┌───────┴───────┐
                    │  User Input   │
                    └───────────────┘
```

---

## Key Technical Requirements

| Area | Requirement |
|------|-------------|
| **Data** | Hugging Face Zomato dataset; preprocessing and field extraction |
| **Filtering** | Match restaurants to location, budget, cuisine, rating, and extra prefs |
| **LLM** | Prompt design for ranking, reasoning, and explanations |
| **UX** | Readable output with structured fields plus natural-language rationale |

---

## Success Criteria

- Recommendations reflect user-stated preferences (location, budget, cuisine, rating)
- LLM output is personalized and explains *why* each restaurant was chosen
- Results are easy to scan (name, cuisine, rating, cost, explanation)
- Pipeline is end-to-end: ingest → input → filter → LLM → display

---

## Out of Scope (Not Specified in Problem Statement)

The problem statement does not define:

- Specific tech stack (language, framework, UI)
- LLM provider or model choice
- Deployment target
- Authentication or user accounts
- Number of recommendations to return

These can be decided during implementation.

**Implementation choice:** LLM provider is **Google Gemini** (`google-generativeai`, model default `gemini-2.0-flash`). See [architecture.md](./architecture.md) and [implementation-plan.md](./implementation-plan.md).

---

## Source

Derived from `ProblemStatement.txt` — AI-Powered Restaurant Recommendation System (Zomato Use Case).

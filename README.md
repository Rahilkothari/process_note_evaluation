# AI-Powered Process Note Validation System

This application allows organizational teams to create, complete, validate, revise, and submit standardized Process Notes. It acts as an **AI-assisted quality gate** before manual review.

## Architecture

* **Frontend:** Streamlit
* **Backend logic:** Python 3.11+, modularized core engine.
* **Database:** SQLite via SQLAlchemy (ready for Supabase/PostgreSQL migration).
* **AI:** Abstracted `LLMProvider` (currently uses `MockProvider` for demonstration).

## Installation

1. Clone or navigate to the repository.
2. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```
3. Ensure `.env` is set up.

## Environment Setup
Copy `.env.example` to `.env` and configure it:
```bash
cp .env.example .env
```
Ensure `LLM_PROVIDER=mock` is set if you do not have an API key yet.

## How to Run

Execute the following command from the root of the project:
```bash
streamlit run app.py
```

## How to Configure LLM

Open `.env` and set `LLM_PROVIDER` to `openai` or `anthropic` (once the specific providers are implemented in `services/llm_service.py`), and provide the `LLM_API_KEY`. The system abstracts the prompt passing and JSON parsing.

## How Mock Mode Works

When `LLM_PROVIDER=mock`, the system runs locally without needing an internet connection to an AI provider. It simulates AI validation by checking string lengths and flagging specific phrases (like "very important" or "operational excellence") to demonstrate how warnings and revisions look in the UI.

## Validation Rules & Configuration

The 22 sections are completely configurable.
* Edit `config/sections.yaml` to change section names, table fields, or add new sections.
* Edit `config/validation_rules.yaml` to define what the AI should check for in each section.

## Future Production Deployment

Because the database layer uses **SQLAlchemy**, migrating from local SQLite to a production database like Supabase (PostgreSQL) takes just one step:
Change `DATABASE_URL` in your `.env` to your PostgreSQL connection string. The application will automatically create the tables in Supabase on startup.

# Email Organizer

**Status:** Beta  
**Owner:** User

## Overview
The **Email Organizer** is an automated tool designed to help users achieve "Inbox Zero" by systematically reviewing, classifying, and moving incoming emails into specific, mutually exclusive folders. The system leverages Large Language Models (LLMs) to intelligently categorize content and applies organizational rules automatically.

## Key Features
- **New Mail Listener**: Detects when new data arrives in the inbox.
- **LLM Classification**: Uses advanced LLMs (e.g., Groq, GPT) to analyze email content and context (including thread history).
- **Automated Organization**: Moves emails into defined, mutually exclusive folders based on the taxonomy.
- **Safety Toggle**: "Dry Run" capabilities to validate classification without moving files.

## Project Structure
- `main.py`: Entry point for the application.
- `gmail_listener.py`: Handles listening for new emails.
- `classify_emails_groq.py`: Classification logic using Groq/LLMs.
- `taxonomy.md`: Defines the folder structure and classification rules.

## Setup
1.  **Environment Variables**: Ensure `.env` is populated with necessary keys (e.g., `GROQ_API_KEY`, Gmail credentials).
2.  **Dependencies**: Install specific dependencies via `uv`.
    ```bash
    uv sync
    ```
3.  **Run**:
    ```bash
    uv run main.py
    ```

## Goals
- **Primary Goal:** Achieve "Inbox Zero".
- **secondary Goal:** Accurate classification into categories like Newsletters, Receipts, Work, Personal.

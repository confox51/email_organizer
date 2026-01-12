# GitHub Copilot Instructions for Email Organizer

## Overview
This document provides essential guidelines for AI coding agents working with the **Email Organizer** codebase. Understanding the architecture, workflows, and conventions will enable agents to contribute effectively.

## Big Picture Architecture
The **Email Organizer** is designed to automate email classification and organization using Large Language Models (LLMs). The major components include:
- **`main.py`**: The entry point that orchestrates the application flow.
- **`gmail_listener.py`**: Listens for new emails and triggers classification.
- **`classify_emails_groq.py`**: Contains the logic for classifying emails using Groq and LLMs.
- **`taxonomy.md`**: Defines the categories for email classification, ensuring they are mutually exclusive.

### Data Flow
1. New emails are detected by `gmail_listener.py`.
2. The email content is passed to `classify_emails_groq.py` for classification.
3. Based on the classification, emails are moved to specific folders as defined in `taxonomy.md`.

## Developer Workflows
### Setup
1. Ensure environment variables are set in `.env` (e.g., `GROQ_API_KEY`, Gmail credentials).
2. Install dependencies using:
   ```bash
   uv sync
   ```
3. Run the application with:
   ```bash
   uv run main.py
   ```

### Testing and Debugging
- Use logging within `gmail_listener.py` to monitor incoming emails and classification results.
- Implement unit tests for classification logic in `classify_emails_groq.py` to ensure accuracy.

## Project-Specific Conventions
- **Mutually Exclusive Categories**: Emails can only belong to one primary classification folder, as detailed in `taxonomy.md`.
- **Dry Run Feature**: Utilize the safety toggle to validate classifications without moving emails.

## Integration Points
- **Gmail API**: The application connects to Gmail for email retrieval and organization.
- **LLM Integration**: The classification engine relies on external LLM APIs for processing email content.

## Conclusion
By following these guidelines, AI agents can effectively navigate and contribute to the **Email Organizer** project, ensuring efficient email management and classification.
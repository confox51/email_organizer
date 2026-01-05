# Product Requirements Document (PRD): Email Organizer

**Status:** Draft
**Last Updated:** December 22, 2025
**Owner:** User

## 1. Executive Summary
The **Email Organizer** is an automated tool designed to help users achieve "Inbox Zero" by systematically reviewing, classifying, and moving incoming emails into specific, mutually exclusive folders. The system leverages Large Language Models (LLMs) to intelligently categorize content and applies organizational rules automatically.

## 2. Goals & Objectives
*   **Primary Goal:** Achieve "Inbox Zero" by automating email organization.
*   **Secondary Goal:** specific classification of emails into mutually exclusive categories (e.g., Newsletters, Receipts, Work, Personal).
*   **Long-term Goal:** Evolve into a platform (SaaS) where other users can bring their credentials to organize their own inboxes.

## 3. Technical Specifications (High Level)
*   **Input:** Live connection to Email Service Provider APIs (e.g., Gmail API).
*   **Core Logic:** LLM-based classifier (API integration).
*   **Output:** Automated actions (Labeling/Moving emails) within the email provider.

## 4. Development Phases

### Phase 1: Connectivity & Triggering
**Goal:** Establish the pipeline to ingest email data.
*   **Requirement:** Connect to Email APIs, starting with **Gmail**.
*   **Feature:** "New Mail Listener" – Detect when new data arrives.
*   **Feature:** "Trigger" – Initiate the classification workflow upon receipt of new mail.
*   **Outcome:** A functional test script that successfully connects to the Gmail API and outputs a notification/log when a new email is received.

### Phase 2: Taxonomy Definition
**Goal:** Define the "buckets" for organization.
*   **Requirement:** Analyze existing folders/labels in the current inbox.
*   **Constraint:** Labels must be **mutually exclusive**. An email can only belong to one primary classification folder for moving purposes (though tagging with multiple metadata tags is permissible, physical location should be unique).
*   **Outcome:** A defined list of target folders.

### Phase 3: The Classification Engine (LLM Integration)
**Goal:** Build the brain of the system.
*   **Requirement:** Integrate an LLM to serve as the classifier.
*   **Features:**
    *   **Prompt Engineering:** Design prompts that accept email body/metadata and output a specific category from Phase 2.
    *   **Thread Context:** If an email is part of a thread, the classification engine should take the previous labels in the thread into account when outputting a label. For example, if an email is in a thread that has been previously categorized as "Health & Insurance", this information should be provided to the LLM to improve its classification.
    *   **Dry Run/Backfill:** Run the classifier over *existing* emails without moving them to validate accuracy.
*   **Key Decisions (RFC):**
    *   *LLM Selection:* Evaluate options (e.g., GPT-4o, Gemini 1.5, Claude 3.5) for cost vs. accuracy.
    *   *Evaluation Framework:* Define a test set of emails and expected labels to measure performance (Precision/Recall).

### Phase 4: Automation (The "Actuator")
**Goal:** Close the loop and move files.
*   **Requirement:** Programmatically apply labels and archive/move emails to folders.
*   **Feature:** **Safety Toggle**. A master switch to enable/disable the "Move" action, allowing the classification to run invisibly (logging only) until trusted.
*   **Workflow:**
    1.  Trigger (New Email)
    2.  Classify (LLM)
    3.  Action (Move Email provided Toggle is ON)

### Phase 5: Advanced Logic & Roadmap (Future)
**Goal:** Intelligence and Scale.
*   **Feedback Loop:** If a user manually moves an email out of an auto-assigned folder, the system should capture this as a negative example and update the classifier/prompt logic for future accuracy.
*   **Auto-Unsubscribe:** Special handling for a "Spam/Unsubscribe" folder. If the system (or user) moves an email here, trigger an agentic flow to find the unsubscribe link and click it.
*   **Multi-Tenancy:** Refactor for secure credential management to allow other users to auth their own accounts (SaaS Model).

## 5. Open Questions
*   **LLM Selection:** Which model offers the best balance of context window (for long threads) and cost for high-volume processing? Are there free tiers sufficient for MVP?
*   **Prompt Strategy:** Should we use few-shot prompting with dynamic examples from the user's history?
*   **Evaluation:** How do we measure "good enough"? (e.g., Is 95% accuracy acceptable if the 5% error means missing a critical bill?)

## 6. Success Metrics
*   **Inbox Count:** Reduction in unread/in-inbox emails over time.
*   **Classification Accuracy:** % of emails correctly placed (measured by user reversals).
*   **Latency:** Time from email receipt to organization.

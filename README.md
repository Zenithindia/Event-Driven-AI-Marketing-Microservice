# Event-Driven AI Marketing Microservice 🚀

![Status](https://img.shields.io/badge/Status-Production--Ready_Prototype-success)
![Domain](https://img.shields.io/badge/Domain-Full--Stack_Development_%2F_MLOps-blue)
![Tech Stack](https://img.shields.io/badge/Tech_Stack-FastAPI_|_Celery_|_Redis_|_Docker_|_Ollama-informational)

An intelligent, event-driven AI microservice designed for the e-commerce sector. This system acts as an automation layer that silently tracks user behavior (such as cart abandonment and high-intent product browsing) and utilizes an asynchronous background queue to trigger a localized Large Language Model (LLM). It dynamically generates and dispatches hyper-personalized, context-aware marketing emails in real-time while maintaining a frictionless user experience powered by stateful session management.

**Prepared By:** Rupesh Bhardwaj

---

## ✨ Key Features

*   **Stateful Authentication:** Seamless auto-login using HTTP-Only secure cookies for session management, bypassing standard entry screens upon return visits.
*   **Persistent Storage:** Robust backend SQLite database (via SQLAlchemy) acting as the single source of truth for user profiles.
*   **Asynchronous Processing:** Decoupled heavy AI generation tasks from the main API thread using a **Redis** message broker and a **Celery** worker pool, guaranteeing zero latency for the storefront.
*   **Local AI Integration:** Secure pipeline established between the containerized worker and a local instance of **Llama 3.2 (via Ollama)**, successfully bypassing Docker/Windows firewall constraints.
*   **Smart Triggers:** Detects abandoned shopping carts and high-intent browsing (e.g., hovering over specific products) to trigger automated recovery and "soft nudge" emails.

---

## 🏗️ Architecture & Data Flow

The system utilizes a decoupled microservice architecture to ensure the main user interface remains highly responsive.

1.  **Frontend Client (`store.html`):** Captures DOM events (clicks, hovers) and manages cookies. Sends HTTP POST requests (JSON + Cookie).
2.  **API Gateway (FastAPI):** Validates the session, queries the SQLite DB, and enqueues tasks.
3.  **Message Broker (Redis):** Holds jobs in an in-memory queue.
4.  **Background Worker (Celery):** Pulls tasks, constructs dynamic prompt templates, and executes asynchronous Python functions.
5.  **Execution:**
    *   *AI Generation:* Prompts Local AI (Ollama/Llama 3.2) for dynamic text.
    *   *Delivery:* Dispatches the generated email via SMTP Gateway (Mailtrap).

### 📂 Project Structure

```text
smart-notifier/
├── docker-compose.yml      # Infrastructure orchestration
├── store.html              # Frontend client / User Interface
├── api/                    # API Gateway Microservice
│   ├── requirements.txt
│   ├── Dockerfile
│   └── main.py             # FastAPI routes & Database schema
└── worker/                 # Background Processing Microservice
    ├── requirements.txt
    ├── Dockerfile
    └── tasks.py            # Celery tasks & AI/SMTP logic
```

---

## 🚀 Deployment & Execution Guide

To run this system locally, specific dependencies and execution patterns must be strictly followed to satisfy CORS and firewall security protocols.

### Prerequisites
*   **Docker Desktop:** Must be installed and running.
*   **Ollama:** Installed locally with the `llama3.2:3b` model downloaded. 
    *   *Note:* The environment variable `OLLAMA_HOST=0.0.0.0` must be set in Windows System Properties to allow cross-network access.
*   **VS Code Live Server:** Required to serve the frontend on a legitimate localhost port.

### Step-by-Step Initialization

**Step 1: Start the AI Engine**
Open a terminal and initialize the local LLM. Leave this running in the background.
```bash
ollama run llama3.2:3b
```

**Step 2: Build the Infrastructure**
Navigate to the root directory and orchestrate the containers:
```bash
docker-compose up --build
```
*Wait until the logs indicate that both Uvicorn (API) and Celery (Worker) are ready.*

**Step 3: Launch the Client Interface**
Open VS Code, right-click `store.html`, and select **"Open with Live Server"**.
> **CRITICAL:** Ensure your browser URL specifically reads `http://localhost:5500/store.html` (not `127.0.0.1` or `file://`). If the URL does not match the CORS origins defined in `main.py`, the browser will reject the authentication cookies.

---

## 🌍 Real-World E-Commerce Integration

While this serves as a local prototype, the architectural patterns are identical to enterprise production systems:

*   **Shopify / WooCommerce:** Replace the custom frontend by mapping native webhooks (e.g., `carts/update`) directly to the deployed FastAPI endpoints. Update Pydantic models to accept specific JSON schemas.
*   **Custom Frontends (React / Next.js):** Replace vanilla JS `fetch` with Axios/React Query. Swap SQLite authentication with an enterprise IdP (Clerk, Auth0, Firebase) using JWTs.
*   **Scaling AI (Cloud LLMs):** For production scale, swap the local Ollama endpoint in `tasks.py` with a cloud provider like OpenAI:
    ```python
    from openai import OpenAI
    client = OpenAI(api_key="your_api_key")
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    ai_body = response.choices[0].message.content
    ```

---

## 🗺️ Future Enhancements & Roadmap

*   [ ] **Task Cancellation Queues:** Implement a "Kill Switch" (`/purchase_complete` webhook) to revoke pending abandonment emails if a user completes a purchase during the queue delay.
*   [ ] **Webhook Security (HMAC Validation):** Require HMAC signatures in HTTP headers to verify payloads genuinely originated from an authorized frontend/Shopify instance.
*   [ ] **A/B Testing & Dynamic Tone Matrix:** Dynamically adjust prompt instructions (e.g., "urgent," "friendly," "humorous") and track conversion rates to optimize recovery.
*   [ ] **Admin Dashboard:** Develop a secondary FastAPI frontend for analytics on queue health, email dispatch volumes, and LLM generation latency.

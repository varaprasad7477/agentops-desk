# AgentOps Desk

An auditable support-operations agent that plans multi-step resolutions, retrieves grounded policy context, calls allow-listed tools, stores conversation memory, and reports evaluation metrics.

## Architecture

Request -> guardrails -> planner -> policy retrieval -> guarded tools -> verification -> response

The default RuleBasedPlanner makes the project runnable without an API key. Its provider-neutral contract can be replaced by an OpenAI-compatible or Groq planner without changing the workflow.

## Features

- Stateful plan, retrieve, execute, verify, and respond workflow
- Permission-scoped tool calling with structured input validation
- Grounded policy retrieval with citations
- SQLite conversation memory and immutable audit events
- Prompt-injection defenses and secret redaction
- FastAPI endpoints, health checks, request IDs, and structured outputs
- Evaluation harness for task success, safety, tool accuracy, and latency
- Automated tests for successful, denied, and adversarial requests

## Quick start

    python -m venv .venv
    # Windows: .venv\Scripts\activate
    pip install -r requirements.txt
    uvicorn app.main:app --reload

Open http://127.0.0.1:8000/docs

Run validation:

    pytest -q
    python -m evals.run

## Security model

Tools are allow-listed, input-validated, permission-scoped, and executed only after the request passes guardrails. Refunds are drafts only; the agent cannot transfer money. Retrieved text is treated as data, not instructions.

## Repository structure

- app/ - API, workflow, tools, retrieval, memory, and guardrails
- evals/ - repeatable agent-quality evaluation suite
- tests/ - unit and workflow tests
- Dockerfile - reproducible deployment

## License

MIT

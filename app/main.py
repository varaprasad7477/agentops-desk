from fastapi import FastAPI

from .agent import AgentWorkflow
from .models import AgentRequest, AgentResponse

app = FastAPI(title="AgentOps Desk", version="1.0.0", description="Auditable agentic support workflow")
workflow = AgentWorkflow()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/agent/run", response_model=AgentResponse)
def run_agent(request: AgentRequest) -> AgentResponse:
    return workflow.run(request)

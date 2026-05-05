import json
from app.agents.supervisor.state import SupervisorState
from app.tools.llm import llm

REPLANNER_PROMPT = "Replanner: plan={plan} results={results} loop={loop}/{max_loops}. Done if all tasks complete, else rewrite. Output JSON: {{\"action\":\"done|rewrite\",\"reason\":\"...\"}}"


def replanner_node(state: SupervisorState) -> dict:
    results = state.get("all_results", {})
    if results and all(
        isinstance(v, list) and len(v) > 0 and isinstance(v[0], dict) and "error" in v[0]
        for v in results.values()
    ):
        return {"should_continue": False}

    # Compact prompt to stay under 4096 token limit
    prompt = REPLANNER_PROMPT.format(
        plan=json.dumps(state["plan"], ensure_ascii=False),
        results=json.dumps(state["all_results"], ensure_ascii=False),
        loop=state["loop_count"],
        max_loops=state["max_loops"],
    )
    raw = llm.invoke(prompt).content
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[-1].rsplit("\n```", 1)[0]

    try:
        response = json.loads(raw)
    except json.JSONDecodeError:
        return {"should_continue": False}

    if response.get("action") == "done":
        return {"should_continue": False}
    return {
        "should_continue": True,
        "plan": response.get("revised_plan", []),
        "loop_count": state["loop_count"] + 1,
    }

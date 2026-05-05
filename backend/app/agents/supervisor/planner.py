import json
from pydantic import BaseModel
from langchain_core.messages import SystemMessage, HumanMessage
from app.agents.supervisor.state import SupervisorState
from app.tools.llm import llm


class PlanTask(BaseModel):
    agent: str
    action: str
    data: dict
    depends_on: list[str] = []


class PlanSchema(BaseModel):
    tasks: list[PlanTask]


# Global registry instance — will be initialized with actual agents in production
class DummyRegistry:
    def get_all_summaries(self) -> list[dict]:
        return [
            {"name": "profile-agent", "description": "解析简历、构建画像", "skills": []},
            {"name": "matching-agent", "description": "职位匹配、评分、优化", "skills": []},
            {"name": "interview-agent", "description": "面试问题生成、回答评估", "skills": []},
        ]


registry = DummyRegistry()


def planner_node(state: SupervisorState) -> dict:
    agent_cards = registry.get_all_summaries()

    plan = llm.with_structured_output(PlanSchema).invoke([
        SystemMessage(
            "你是 Supervisor。根据用户意图生成执行计划。"
            "识别任务之间的依赖关系：如果用户说'先X再Y'，Y应标记 depends_on=[X所在的agent]。"
            "不要自动追加用户未请求的任务（软连接原则）。"
            f"\n可用 Agent:\n{json.dumps(agent_cards, ensure_ascii=False)}"
        ),
        *state["messages"],
    ])

    return {
        "plan": [t.model_dump() for t in plan.tasks],
        "goal": state["messages"][-1].content if state["messages"] else "",
        "loop_count": 0,
        "max_loops": 3,
        "all_results": {},
    }

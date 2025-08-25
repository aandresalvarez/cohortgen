# 📂 flujo project/skills/helpers.py

from __future__ import annotations
from typing import Any, Dict

from flujo.domain.models import PipelineContext


def is_finish_command(output: Any, context: PipelineContext | None) -> bool:
    """
    This is the `exit_condition` for our loop.
    It checks if the planner agent's last command was 'finish'.
    If so, the loop stops.
    """
    if isinstance(output, dict) and output.get("action") == "finish":
        return True
    return False

# 👇 NEW FUNCTION ADDED HERE 👇
def check_clarification_action(output: Any, context: PipelineContext | None) -> str:
    """
    This is the `condition` for the ConditionalStep inside our loop.
    It checks the planner's output and returns the name of the branch to run.
    """
    if isinstance(output, dict) and output.get("action") == "ask":
        # If the agent wants to ask a question, return the key for the 'ask' branch.
        return "ask"
    else:
        # Otherwise, return the key for the 'skip' branch.
        return "skip"
# 👆 END OF NEW FUNCTION 👆

def map_initial_input(initial_goal: str, context: PipelineContext | None) -> Dict[str, Any]:
    """
    This is the `initial_input_mapper`.
    It prepares the input for the very first run of the clarification agent.
    """
    if context is not None:
        context.scratchpad["history"] = [f"User: {initial_goal}"]
    return {"goal": initial_goal, "history": ""}


def map_iteration_input(
    user_answer: Any, context: PipelineContext | None, iteration_index: int
) -> Dict[str, Any]:
    """
    This is the `iteration_input_mapper`.
    It runs after each loop, adds the user's answer to the history,
    and prepares the input for the next run of the clarification agent.
    """
    if context is not None:
        history = context.scratchpad.get("history", [])
        
        # The user's answer comes directly from the previous HITL step's output.
        history.append(f"User: {user_answer}")
        
        context.scratchpad["history"] = history

        # The agent needs the original goal and the full conversation history.
        return {
            "goal": context.initial_prompt,
            "history": "\n".join(history),
        }

    return {"goal": "", "history": "Could not construct conversation history."}


def map_loop_output(
    final_command: Any, context: PipelineContext | None
) -> Dict[str, Any]:
    """
    This is the `loop_output_mapper`.
    Once the loop finishes, this function prepares the final, consolidated
    input for the main planner agent.
    """
    if context is not None:
        history = context.scratchpad.get("history", [])
        return {
            "goal": context.initial_prompt,
            "clarifications": "\n".join(history),
        }
    return {"goal": "", "clarifications": "No history found."}
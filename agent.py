
# ============================================================
# MyOwnJARVIS - Agent Tool Registry and Task Planner
# Structured Tool Results + AI Recovery + Memory
# ============================================================

import json

from tools import (
    open_application,
    open_website,
    check_internet,
    get_weather,
)

from llm import (
    ask_local_ai,
    ask_local_ai_for_plan,
    ask_local_ai_for_next_action,
    ask_local_ai_for_recovery,
)

from memory import (
    save_experience,
    get_relevant_experiences,
)


# ============================================================
# 1. TOOL REGISTRY
# ============================================================

TOOL_REGISTRY = {
    "open_application": open_application,
    "open_website": open_website,
    "check_internet": check_internet,
    "get_weather": get_weather,
}

ALLOWED_APPLICATIONS = {"notepad", "calculator", "paint"}
ALLOWED_WEBSITES = {"google", "youtube", "github"}
RETRYABLE_TOOLS = {"check_internet", "get_weather"}


def list_available_tools():
    """Return the names of all available tools."""
    return list(TOOL_REGISTRY.keys())


def make_tool_result(success, tool, data=None, error=None):
    """Create a consistent structured result with execution status."""

    return {
        "success": success,
        "tool": tool,
        "data": data,
        "error": error,
        "status": "accepted" if success is True else "failed",
    }


def execute_tool(tool_name, **arguments):
    """Execute an approved tool and validate its structured result."""

    tool = TOOL_REGISTRY.get(tool_name)

    if tool is None:
        return make_tool_result(
            False,
            tool_name,
            error=f"Unknown tool: {tool_name}",
        )

    try:
        result = tool(**arguments)

        # Every tool must return a dictionary.
        if not isinstance(result, dict):
            return make_tool_result(
                False,
                tool_name,
                error="The tool returned an invalid result format.",
            )

        # The returned tool name must match the requested tool.
        if result.get("tool") != tool_name:
            return make_tool_result(
                False,
                tool_name,
                error="The tool returned a mismatched tool name.",
            )

        # The success flag must be an actual Boolean.
        if type(result.get("success")) is not bool:
            return make_tool_result(
                False,
                tool_name,
                error="The tool returned an invalid success flag.",
            )

        # Successful results must contain result data.
        if result["success"] is True:
            if result.get("data") is None:
                return make_tool_result(
                    False,
                    tool_name,
                    error="The tool reported success without result data.",
                )

        # Failed results must provide a meaningful error message.
        else:
            error_message = result.get("error")

            if (
                not isinstance(error_message, str)
                or not error_message.strip()
            ):
                return make_tool_result(
                    False,
                    tool_name,
                    error="The tool failed without providing an error message.",
                )

        # Validate execution status only after validating the
        # result structure, success flag, and data/error fields.
        expected_status = (
            "accepted" if result["success"] is True else "failed"
        )

        if result.get("status") != expected_status:
            return make_tool_result(
                False,
                tool_name,
                error="The tool returned an invalid execution status.",
            )

        return result

    except TypeError as error:
        return make_tool_result(
            False,
            tool_name,
            error=f"Invalid arguments for {tool_name}: {error}",
        )

    except Exception as error:
        return make_tool_result(
            False,
            tool_name,
            error=f"Tool execution failed: {error}",
        )


# ============================================================
# 2. TOOL ARGUMENT VALIDATION
# ============================================================

def validate_tool_arguments(tool_name, arguments):
    """Validate and normalize arguments before executing a tool."""

    if not isinstance(arguments, dict):
        return None, "Tool arguments must be a dictionary."

    if tool_name not in TOOL_REGISTRY:
        return None, f"Blocked unsupported tool: {tool_name}"

    if tool_name == "check_internet":
        if arguments:
            return None, "The internet-check tool accepts no arguments."

        return {}, None

    if tool_name == "get_weather":
        city = arguments.get("city")

        if not isinstance(city, str) or not city.strip():
            return None, "The weather tool needs a valid city name."

        return {"city": city.strip()}, None

    if tool_name == "open_application":
        app_name = arguments.get("app_name")

        if not isinstance(app_name, str):
            return None, "Application name must be text."

        app_name = app_name.strip().lower()

        if app_name not in ALLOWED_APPLICATIONS:
            return None, "Blocked unsupported application."

        return {"app_name": app_name}, None

    if tool_name == "open_website":
        site_name = arguments.get("site_name")

        if not isinstance(site_name, str):
            return None, "Website name must be text."

        site_name = site_name.strip().lower()

        if site_name not in ALLOWED_WEBSITES:
            return None, "Blocked unsupported website."

        return {"site_name": site_name}, None

    return None, "No validation rule exists for this tool."


# ============================================================
# 3. STRUCTURED RESULT HANDLING
# ============================================================

def tool_result_succeeded(tool_name, result):
    """Determine success using the structured result, not text matching."""

    if not isinstance(result, dict):
        return False

    if result.get("tool") != tool_name:
        return False

    return result.get("success") is True


def format_tool_result(result):
    """Convert a structured result into readable text."""

    if not isinstance(result, dict):
        return str(result)

    if result.get("success") is True:
        data = result.get("data")

        if isinstance(data, dict):
            return str(data.get("message", data))

        if data is not None:
            return str(data)

        return "Task completed successfully."

    return str(result.get("error") or "The tool failed.")


def result_to_json(result):
    """Convert a structured result into readable JSON for logs."""

    try:
        return json.dumps(result, ensure_ascii=False, default=str)
    except (TypeError, ValueError):
        return str(result)


# ============================================================
# 4. BASIC TASK PLANNER
# ============================================================

def plan_task(message):
    """Identify simple supported tasks using keyword matching."""

    message_lower = message.lower().strip()
    plan = []

    if "internet" in message_lower or "connection" in message_lower:
        plan.append({
            "tool": "check_internet",
            "arguments": {},
            "description": "Check internet connectivity",
        })

    if "weather" in message_lower or "temperature" in message_lower:
        city = "Chennai"

        if " in " in message_lower:
            city = message_lower.rsplit(" in ", 1)[1].strip()

            for ending in [" please", " today", " now", "?"]:
                if city.endswith(ending):
                    city = city[:-len(ending)].strip()

        plan.append({
            "tool": "get_weather",
            "arguments": {"city": city},
            "description": f"Get weather for {city}",
        })

    return plan


# ============================================================
# 5. BASIC PLAN EXECUTOR
# ============================================================

def execute_plan(plan):
    """Validate and execute each task in a basic plan."""

    results = []

    for step_number, task in enumerate(plan, start=1):
        if not isinstance(task, dict):
            results.append(f"Step {step_number}: Invalid task.")
            continue

        tool_name = task.get("tool")
        arguments = task.get("arguments", {})
        description = task.get("description", tool_name)

        normalized_arguments, error = validate_tool_arguments(
            tool_name,
            arguments,
        )

        if error:
            results.append(f"{description}: {error}")
            continue

        print(f"Step {step_number}: {description}...")

        result = execute_tool(tool_name, **normalized_arguments)

        results.append(
            f"{description}: {format_tool_result(result)}"
        )

    if not results:
        return "I could not identify a supported task."

    return "\n".join(results)


def execute_multi_step_task(message):
    """Plan and execute supported tasks using the basic planner."""

    plan = plan_task(message)

    if not plan:
        return (
            "I could not identify a supported task. "
            "Try asking me to check the internet or weather."
        )

    return execute_plan(plan)


# ============================================================
# 6. AI PLANNER AND EXECUTOR
# ============================================================

def website_was_requested(user_request, arguments):
    """Only permit website actions explicitly requested by the user."""

    site_name = arguments.get("site_name")

    if site_name not in ALLOWED_WEBSITES:
        return False

    request_lower = user_request.lower()

    accepted_phrases = {
        "google": ["open google", "visit google"],
        "youtube": ["open youtube", "visit youtube"],
        "github": ["open github", "visit github"],
    }

    return any(
        phrase in request_lower
        for phrase in accepted_phrases[site_name]
    )


def execute_ai_agent_task(message):
    """Ask the local AI to plan tasks, validate them, and execute them."""

    plan_data = ask_local_ai_for_plan(message)

    if not isinstance(plan_data, dict):
        return "The AI planner returned an invalid plan."

    tasks = plan_data.get("tasks", [])

    if not isinstance(tasks, list):
        return "The AI planner returned an invalid task list."

    if not tasks:
        return "The AI planner did not select any tools."

    if len(tasks) > 5:
        return "The plan contains too many tasks. Please simplify your request."

    results = []

    for step_number, task in enumerate(tasks, start=1):
        if not isinstance(task, dict):
            return "The AI planner returned an invalid task."

        tool_name = task.get("tool")
        arguments = task.get("arguments", {})

        normalized_arguments, error = validate_tool_arguments(
            tool_name,
            arguments,
        )

        if error:
            return error

        if (
            tool_name == "open_website"
            and not website_was_requested(message, normalized_arguments)
        ):
            return "Website action blocked because it was not requested."

        print(f"Agent step {step_number}: {tool_name}")

        result = execute_tool(tool_name, **normalized_arguments)

        results.append(
            f"{tool_name}: {format_tool_result(result)}"
        )

        if not tool_result_succeeded(tool_name, result):
            results.append("Execution stopped because the tool failed.")
            break

    return "\n".join(results)


# ============================================================
# 7. RESULT-AWARE TASK EXECUTION
# ============================================================

def execute_result_aware_task(message):
    """Execute AI-planned tasks and stop after a failed internet check."""

    plan_data = ask_local_ai_for_plan(message)

    if not isinstance(plan_data, dict):
        return "The AI planner returned an invalid plan."

    tasks = plan_data.get("tasks", [])

    if not isinstance(tasks, list):
        return "The AI planner returned an invalid task list."

    if not tasks:
        return "The AI planner did not select any tools for this request."

    if len(tasks) > 5:
        return "The plan contains too many tasks. Please simplify the request."

    results = []

    for step_number, task in enumerate(tasks, start=1):
        if not isinstance(task, dict):
            return "The AI planner returned an invalid task."

        tool_name = task.get("tool")
        arguments = task.get("arguments", {})

        normalized_arguments, error = validate_tool_arguments(
            tool_name,
            arguments,
        )

        if error:
            return error

        if (
            tool_name == "open_website"
            and not website_was_requested(message, normalized_arguments)
        ):
            return "Website action blocked because it was not requested."

        print(f"Agent step {step_number}: {tool_name}")

        result = execute_tool(tool_name, **normalized_arguments)
        succeeded = tool_result_succeeded(tool_name, result)

        results.append(
            f"{tool_name}: {format_tool_result(result)}"
        )

        if tool_name == "check_internet":
            if not succeeded:
                print("Agent observation: Internet could not be confirmed.")
                print("Agent decision: Stop remaining tasks.")
                break

            print("Agent observation: Internet is working.")
            print("Agent decision: Continue with remaining tasks.")

        elif not succeeded:
            print(f"Agent observation: {tool_name} failed.")
            break

    summary_prompt = (
        "You are MyOwnJARVIS. Summarize the actual tool results "
        "in simple language. Do not invent facts or claim that "
        "an unexecuted task succeeded.\n\n"
        f"User request: {message}\n\n"
        "Actual tool results:\n"
        + "\n".join(results)
    )

    try:
        summary = ask_local_ai(summary_prompt)
    except Exception as error:
        summary = f"Could not generate a summary: {error}"

    return (
        "Task execution results:\n"
        + "\n".join(results)
        + "\n\nJARVIS summary:\n"
        + str(summary)
    )


# ============================================================
# 8. TOOL RETRY SYSTEM
# ============================================================

def execute_with_recovery(tool_name, arguments, max_retries=2):
    """Retry selected tools when structured results report failure."""

    normalized_arguments, error = validate_tool_arguments(
        tool_name,
        arguments,
    )

    if error:
        return make_tool_result(
            False,
            tool_name,
            error=error,
        ), 0, False

    attempts = 0
    max_attempts = max(1, max_retries + 1)

    while attempts < max_attempts:
        attempts += 1
        print(f"Tool attempt {attempts}: {tool_name}")

        result = execute_tool(tool_name, **normalized_arguments)

        if tool_result_succeeded(tool_name, result):
            print(f"Tool succeeded: {tool_name}")
            return result, attempts, True

        print(f"Tool failed: {format_tool_result(result)}")

        if tool_name not in RETRYABLE_TOOLS:
            return result, attempts, False

        if attempts < max_attempts:
            print(f"Retrying {tool_name}...")

    print("Recovery limit reached. Stopping retries.")
    return result, attempts, False


# ============================================================
# 9. AI-GUIDED RECOVERY WITH EXPERIENCE MEMORY
# ============================================================

def execute_with_ai_recovery(
    user_request,
    tool_name,
    arguments,
    initial_error,
    execution_history,
    max_recovery_attempts=2,
):
    """
    Attempt AI-guided recovery.

    Returns:
        result, succeeded, actual_tool, actual_arguments
    """

    current_tool = tool_name
    current_arguments = dict(arguments)

    if isinstance(initial_error, dict):
        current_error = format_tool_result(initial_error)
    else:
        current_error = str(initial_error)

    attempted_actions = set()

    def make_action_key(name, args):
        return (
            name,
            json.dumps(args, sort_keys=True, default=str),
        )

    attempted_actions.add(
        make_action_key(current_tool, current_arguments)
    )

    def stop_recovery(message, outcome):
        """Record why recovery stopped without executing another action."""

        execution_history.append(
            f"AI recovery: {outcome}: {message}"
        )
        print(message)

        try:
            save_experience(
                user_request=user_request,
                failed_tool=current_tool,
                failed_arguments=current_arguments,
                error_message=current_error,
                recovery_tool="",
                recovery_arguments={},
                outcome=outcome,
            )
        except Exception as error:
            print(
                "Warning: Could not save recovery decision: "
                f"{error}"
            )

        return (
            make_tool_result(
                False,
                current_tool,
                error=current_error,
            ),
            False,
            current_tool,
            current_arguments,
        )

    for attempt in range(1, max_recovery_attempts + 1):
        print(f"AI recovery analysis {attempt}...")

        try:
            past_experiences = get_relevant_experiences(
                failed_tool=current_tool,
                error_message=current_error,
                limit=5,
            )

            decision = ask_local_ai_for_recovery(
                user_request=user_request,
                failed_tool=current_tool,
                arguments=current_arguments,
                error_message=current_error,
                execution_history="\n".join(execution_history),
                past_experiences=past_experiences,
            )

        except Exception as error:
            return stop_recovery(
                f"Could not obtain an AI recovery decision: {error}",
                "DECLINED",
            )

        if not isinstance(decision, dict):
            return stop_recovery(
                "Recovery stopped: invalid AI response.",
                "DECLINED",
            )

        if decision.get("recover") is not True:
            reason = decision.get(
                "reason",
                "Recovery was not recommended.",
            )
            return stop_recovery(
                f"Recovery declined. Reason: {reason}",
                "DECLINED",
            )

        next_tool = decision.get("tool")
        next_arguments = decision.get("arguments", {})

        normalized_arguments, validation_error = validate_tool_arguments(
            next_tool,
            next_arguments,
        )

        if validation_error:
            return stop_recovery(
                f"Recovery blocked: {validation_error}",
                "BLOCKED",
            )

        if (
            next_tool == "open_website"
            and not website_was_requested(user_request, normalized_arguments)
        ):
            return stop_recovery(
                "Recovery blocked: website was not explicitly requested.",
                "BLOCKED",
            )

        action_key = make_action_key(next_tool, normalized_arguments)

        if action_key in attempted_actions:
            return stop_recovery(
                "Recovery stopped: duplicate action detected.",
                "BLOCKED",
            )

        attempted_actions.add(action_key)

        reason = decision.get("reason", "No reason provided.")

        print(f"AI recovery selected: {next_tool}")
        print(f"Reason: {reason}")

        result = execute_tool(next_tool, **normalized_arguments)
        succeeded = tool_result_succeeded(next_tool, result)
        result_text = format_tool_result(result)

        status = "SUCCESS" if succeeded else "FAILURE"

        execution_history.append(
            f"AI recovery {attempt}: tool={next_tool}; "
            f"arguments={normalized_arguments}; "
            f"result={status}: {result_text}"
        )

        try:
            save_experience(
                user_request=user_request,
                failed_tool=current_tool,
                failed_arguments=current_arguments,
                error_message=current_error,
                recovery_tool=next_tool,
                recovery_arguments=normalized_arguments,
                outcome=status,
            )
        except Exception as error:
            print(
                "Warning: Could not save recovery experience: "
                f"{error}"
            )

        if succeeded:
            return (
                result,
                True,
                next_tool,
                normalized_arguments,
            )

        current_tool = next_tool
        current_arguments = dict(normalized_arguments)
        current_error = result_text

    execution_history.append(
        "AI recovery: FAILED: Maximum recovery attempts reached."
    )

    return (
        make_tool_result(
            False,
            current_tool,
            error=current_error,
        ),
        False,
        current_tool,
        current_arguments,
    )


# ============================================================
# 10. CONDITIONAL MULTI-STEP AI AGENT
# ============================================================

def execute_conditional_task(message):
    """Plan, execute, observe structured results, and recover safely."""

    execution_history = []
    max_steps = 5
    request_lower = message.lower()

    needs_internet = (
        "internet" in request_lower
        or "connection" in request_lower
    )

    needs_weather = (
        "weather" in request_lower
        or "temperature" in request_lower
    )

    needs_application = any(
        phrase in request_lower
        for phrase in [
            "open notepad",
            "open calculator",
            "open paint",
        ]
    )

    requested_application = None

    for app_name in ALLOWED_APPLICATIONS:
        if f"open {app_name}" in request_lower:
            requested_application = app_name
            break

    needs_website = any(
        phrase in request_lower
        for phrase in [
            "open google",
            "open youtube",
            "open github",
            "visit google",
            "visit youtube",
            "visit github",
        ]
    )

    requested_website = None

    for site_name in ALLOWED_WEBSITES:
        if (
            f"open {site_name}" in request_lower
            or f"visit {site_name}" in request_lower
        ):
            requested_website = site_name
            break

    required_tools = set()

    if needs_internet:
        required_tools.add("check_internet")

    if needs_weather:
        required_tools.add("get_weather")

    if needs_application:
        required_tools.add("open_application")

    if needs_website:
        required_tools.add("open_website")

    def get_successful_tools():
        return {
            item["tool"]
            for item in execution_history
            if (
                isinstance(item, dict)
                and item.get("success") is True
            )
        }

    def history_for_ai():
        if not execution_history:
            return "No tools have been executed yet."

        lines = []

        for item in execution_history:
            lines.append(
                f"Tool: {item['tool']}; "
                f"arguments: {item['arguments']}; "
                f"success: {item['success']}; "
                f"result: {item['message']}"
            )

        return "\n".join(lines)

    def finish(message_text):
        if execution_history:
            lines = [
                f"Step {index}: {item['tool']} - "
                f"{'SUCCESS' if item['success'] else 'FAILED'}: "
                f"{item['message']}"
                for index, item in enumerate(execution_history, start=1)
            ]
            history_text = "\n".join(lines)
        else:
            history_text = "No tools were executed."

        return f"{message_text}\n\nExecution history:\n{history_text}"

    # For a supported direct tool request, use that tool explicitly.
    direct_action = None

    if needs_internet:
        direct_action = ("check_internet", {})

    elif needs_weather:
        city = "Chennai"

        if " in " in request_lower:
            city = request_lower.rsplit(" in ", 1)[1].strip()

            for ending in [" please", " today", " now", "?"]:
                if city.endswith(ending):
                    city = city[:-len(ending)].strip()

        direct_action = ("get_weather", {"city": city})

    elif requested_application:
        direct_action = (
            "open_application",
            {"app_name": requested_application},
        )

    elif requested_website:
        direct_action = (
            "open_website",
            {"site_name": requested_website},
        )

    if direct_action and len(required_tools) <= 1:
        tool_name, arguments = direct_action

        result, attempts, succeeded = execute_with_recovery(
            tool_name,
            arguments,
        )

        result_message = format_tool_result(result)

        execution_history.append({
            "tool": tool_name,
            "arguments": arguments,
            "success": succeeded,
            "message": result_message,
            "result": result,
            "attempts": attempts,
        })

        if not succeeded:
            print("Agent decision: Attempting AI-guided recovery.")

            (
                recovery_result,
                recovery_succeeded,
                recovery_tool,
                recovery_arguments,
            ) = execute_with_ai_recovery(
                user_request=message,
                tool_name=tool_name,
                arguments=arguments,
                initial_error=result,
                execution_history=[history_for_ai()],
            )

            if recovery_succeeded:
                # Recovery must fulfill the original requested action.
                if (
                    recovery_tool != tool_name
                    or recovery_arguments != arguments
                ):
                    execution_history.append({
                        "tool": recovery_tool,
                        "arguments": recovery_arguments,
                        "success": True,
                        "message": format_tool_result(recovery_result),
                        "result": recovery_result,
                        "attempts": 1,
                    })

                    return finish(
                        "Task incomplete: Recovery performed a different "
                        "action than the one originally requested."
                    )

                execution_history.append({
                    "tool": recovery_tool,
                    "arguments": recovery_arguments,
                    "success": True,
                    "message": format_tool_result(recovery_result),
                    "result": recovery_result,
                    "attempts": 1,
                })
            else:
                return finish(
                    "Task incomplete: "
                    + format_tool_result(recovery_result)
                )

        missing_tools = required_tools - get_successful_tools()

        if missing_tools:
            return finish(
                "Task incomplete. Required tools did not succeed: "
                + ", ".join(sorted(missing_tools))
            )

        return finish(
            "Task completed successfully."
            if succeeded
            else "Recovery completed successfully."
        )

    # Use the AI for requests requiring a multi-step plan.
    for step_number in range(1, max_steps + 1):
        try:
            decision = ask_local_ai_for_next_action(
                message,
                history_for_ai(),
            )
        except Exception as error:
            return finish(
                f"Could not obtain the next AI action: {error}"
            )

        if not isinstance(decision, dict):
            return finish("Invalid AI decision. Stopping safely.")

        if decision.get("done") is True:
            successful_tools = get_successful_tools()
            missing_tools = required_tools - successful_tools

            if missing_tools:
                return finish(
                    "Task incomplete. Required tools did not succeed: "
                    + ", ".join(sorted(missing_tools))
                )

            return finish(
                str(
                    decision.get(
                        "message",
                        "The requested task is complete.",
                    )
                )
            )

        tool_name = decision.get("tool")
        arguments = decision.get("arguments", {})

        normalized_arguments, error = validate_tool_arguments(
            tool_name,
            arguments,
        )

        if error:
            return finish(f"Action blocked: {error}")

        if (
            tool_name == "open_website"
            and not website_was_requested(message, normalized_arguments)
        ):
            return finish(
                "Website action blocked because it was not explicitly requested."
            )

        print(f"Agent step {step_number}: {tool_name}")

        result, attempts, succeeded = execute_with_recovery(
            tool_name,
            normalized_arguments,
        )

        result_message = format_tool_result(result)
        actual_tool = tool_name
        actual_arguments = normalized_arguments

        if not succeeded:
            print("Agent decision: Attempting AI-guided recovery.")

            (
                recovery_result,
                recovery_succeeded,
                recovery_tool,
                recovery_arguments,
            ) = execute_with_ai_recovery(
                user_request=message,
                tool_name=tool_name,
                arguments=normalized_arguments,
                initial_error=result,
                execution_history=[history_for_ai()],
            )

            result = recovery_result
            succeeded = recovery_succeeded
            actual_tool = recovery_tool
            actual_arguments = recovery_arguments
            result_message = format_tool_result(result)

        execution_history.append({
            "tool": actual_tool,
            "arguments": actual_arguments,
            "success": succeeded,
            "message": result_message,
            "result": result,
            "attempts": attempts,
        })

        print(f"Agent observation: {result_message}")

        if not succeeded:
            return finish(
                "Task incomplete: " + result_message
            )

        successful_tools = get_successful_tools()
        missing_tools = required_tools - successful_tools

        if required_tools and not missing_tools:
            return finish("All requested tool actions succeeded.")

        if not required_tools:
            return finish("Task completed successfully.")

    return finish(
        f"The agent reached its maximum of {max_steps} actions."
    )


# ============================================================
# 11. DIRECT TESTING
# ============================================================

if __name__ == "__main__":
    print("MyOwnJARVIS Conditional AI Agent")
    print("-" * 40)

    task = input("You: ").strip()

    if not task:
        print("Please enter a task.")
    else:
        print("\nJARVIS is working...\n")

        result = execute_conditional_task(task)

        print("\nJARVIS:")
        print(result)

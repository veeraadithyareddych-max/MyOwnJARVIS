
# ============================================================
# MyOwnJARVIS - Agent Tool Registry and Task Planner
# Structured Tool Results + AI Recovery + Memory
# Context-Aware Execution + Independent Verification
# ============================================================

import json
import time
import urllib.request

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
import re

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


# ============================================================
# 2. INDEPENDENT VERIFICATION
# ============================================================

def make_verification_result(verified, tool, evidence=None, error=None):
    """
    Create a structured result for an independently checked outcome.

    Evidence must describe both the verification procedure and
    the observed result. A plain text claim is not sufficient.
    """

    if verified is True and isinstance(evidence, dict):
        check = evidence.get("check")
        observed = evidence.get("observed")

        if (
            isinstance(check, str)
            and check.strip()
            and isinstance(observed, str)
            and observed.strip()
        ):
            return {
                "success": True,
                "tool": tool,
                "status": "verified",
                "evidence": {
                    "check": check.strip(),
                    "observed": observed.strip(),
                },
                "error": None,
            }

    return {
        "success": False,
        "tool": tool,
        "status": "failed",
        "evidence": None,
        "error": (
            error
            or "Structured independent verification evidence is missing."
        ),
    }



def verify_application_running(app_name):
    """Independently verify that an approved application's process is running."""

    import subprocess

    process_names = {
        "notepad": ["notepad.exe"],
        "calculator": ["Calculator.exe", "CalculatorApp.exe"],
        "paint": ["mspaint.exe"],
    }

    if not isinstance(app_name, str) or not app_name.strip():
        return make_verification_result(
            False,
            "open_application",
            error="Application verification requires a valid application name.",
        )

    app_name = app_name.strip().casefold()
    expected_processes = process_names.get(app_name)

    if expected_processes is None:
        return make_verification_result(
            False,
            "open_application",
            error="Cannot verify an application that is not approved.",
        )

    # Allow packaged Windows applications, especially Calculator,
    # a short time to finish starting before checking the process list.
    deadline = time.monotonic() + 5
    last_error = None

    while True:
        try:
            result = subprocess.run(
                ["tasklist", "/FO", "CSV", "/NH"],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )

            if result.returncode != 0:
                last_error = "Windows process listing failed."
            else:
                running_processes = {
                    line.split(",", 1)[0].strip('"').casefold()
                    for line in result.stdout.splitlines()
                    if line.strip()
                }

                matched_processes = [
                    name
                    for name in expected_processes
                    if name.casefold() in running_processes
                ]

                if matched_processes:
                    return make_verification_result(
                        True,
                        "open_application",
                        evidence={
                            "check": "Windows tasklist process listing",
                            "observed": (
                                "Detected running process: "
                                + ", ".join(matched_processes)
                            ),
                        },
                    )

                last_error = (
                    f"No expected process was detected for "
                    f"{app_name.title()}."
                )

        except (OSError, subprocess.TimeoutExpired) as exc:
            last_error = f"Windows process verification failed: {exc}"

        if time.monotonic() >= deadline:
            return make_verification_result(
                False,
                "open_application",
                error=last_error,
            )

        time.sleep(0.5)


def verify_website_reachable(site_name, timeout=5):
    """Independently verify that an approved website is reachable."""

    website_urls = {
        "google": "https://www.google.com",
        "youtube": "https://www.youtube.com",
        "github": "https://github.com",
    }

    if not isinstance(site_name, str) or not site_name.strip():
        return make_verification_result(
            False,
            "open_website",
            error="Website verification requires a valid website name.",
        )

    site_name = site_name.strip().casefold()
    url = website_urls.get(site_name)

    if url is None:
        return make_verification_result(
            False,
            "open_website",
            error="Cannot verify a website that is not approved.",
        )

    try:
        request = urllib.request.Request(
            url,
            method="HEAD",
            headers={"User-Agent": "MyOwnJARVIS/1.0"},
        )

        with urllib.request.urlopen(request, timeout=timeout) as response:
            status_code = response.getcode()

        if 200 <= status_code < 400:
            return make_verification_result(
                True,
                "open_website",
                evidence={
                    "check": "Independent HTTP HEAD request",
                    "observed": f"HTTP {status_code} returned by {url}",
                },
            )

        return make_verification_result(
            False,
            "open_website",
            error=(
                f"Website verification returned HTTP {status_code} "
                f"for {url}."
            ),
        )

    except Exception as error:
        return make_verification_result(
            False,
            "open_website",
            error=(
                f"Independent website verification failed for "
                f"{site_name.title()}: {error}"
            ),
        )
def verify_internet_connection(timeout=5):
    """Independently verify internet reachability using an HTTP request."""

    url = "https://www.google.com"

    try:
        request = urllib.request.Request(
            url,
            method="HEAD",
        )

        with urllib.request.urlopen(request, timeout=timeout) as response:
            status_code = response.getcode()

        if 200 <= status_code < 400:
            return make_verification_result(
                True,
                "check_internet",
                evidence={
                    "check": "Independent HTTP HEAD request",
                    "observed": f"HTTP {status_code} returned by {url}",
                },
            )

        return make_verification_result(
            False,
            "check_internet",
            error=(
                f"Internet verification returned HTTP {status_code}."
            ),
        )

    except Exception as error:
        return make_verification_result(
            False,
            "check_internet",
            error=f"Independent internet verification failed: {error}",
        )


# ============================================================
# 3. TOOL EXECUTION AND RESULT VALIDATION
# ============================================================

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

        if not isinstance(result, dict):
            return make_tool_result(
                False,
                tool_name,
                error="The tool returned an invalid result format.",
            )

        if result.get("tool") != tool_name:
            return make_tool_result(
                False,
                tool_name,
                error="The tool returned a mismatched tool name.",
            )

        if type(result.get("success")) is not bool:
            return make_tool_result(
                False,
                tool_name,
                error="The tool returned an invalid success flag.",
            )

        if result["success"] is True:
            if result.get("data") is None:
                return make_tool_result(
                    False,
                    tool_name,
                    error="The tool reported success without result data.",
                )
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
# 4. TOOL ARGUMENT VALIDATION
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

def validate_ai_plan(plan_data, user_request):
    """Validate and normalize an AI-generated execution plan."""

    if not isinstance(plan_data, dict):
        return None, "The AI planner returned an invalid plan."

    tasks = plan_data.get("tasks")

    if not isinstance(tasks, list):
        return None, "The AI planner returned an invalid task list."

    if not tasks:
        return [], None

    if len(tasks) > 5:
        return None, (
            "The plan contains too many tasks. "
            "Please simplify your request."
        )

    normalized_tasks = []

    for step_number, task in enumerate(tasks, start=1):

        if not isinstance(task, dict):
            return None, (
                f"Step {step_number}: "
                "The AI planner returned an invalid task."
            )

        tool_name = task.get("tool")

        if not isinstance(tool_name, str) or not tool_name.strip():
            return None, (
                f"Step {step_number}: "
                "The AI planner did not specify a valid tool."
            )

        tool_name = tool_name.strip()

        arguments = task.get("arguments", {})

        normalized_arguments, error = validate_tool_arguments(
            tool_name,
            arguments,
        )

        if error:
            return None, f"Step {step_number}: {error}"

        semantic_error = validate_requested_action(
            tool_name,
            normalized_arguments,
            user_request,
        )

        if semantic_error:
            return None, (
                f"Step {step_number}: {semantic_error}"
            )

        if (
            tool_name == "open_website"
            and not website_was_requested(
                user_request,
                normalized_arguments,
            )
        ):
            return None, (
                f"Step {step_number}: "
                "Website action blocked because it was not requested."
            )

        if (
            tool_name == "open_application"
            and not application_was_requested(
                user_request,
                normalized_arguments,
            )
        ):
            return None, (
                f"Step {step_number}: "
                "Application action blocked because it was not requested."
            )

        dependency_data = task.get("depends_on")

        if dependency_data is not None:

            if not isinstance(dependency_data, list):
                return None, (
                    f"Step {step_number}: "
                    "depends_on must be a list."
                )

            for dependency in dependency_data:

                if type(dependency) is not int:
                    return None, (
                        f"Step {step_number}: "
                        "depends_on must contain step numbers."
                    )

                if dependency < 1:
                    return None, (
                        f"Step {step_number}: "
                        "depends_on contains an invalid step number."
                    )

                if dependency == step_number:
                    return None, (
                        f"Step {step_number}: "
                        "A task cannot depend on itself."
                    )

                if dependency >= step_number:
                    if dependency > len(tasks):
                        return None, (
                            f"Step {step_number}: "
                            f"Dependency step {dependency} does not exist."
                        )

                    return None, (
                        f"Step {step_number}: "
                        f"Dependency on later step {dependency} is not allowed."
                    )

            if len(dependency_data) != len(set(dependency_data)):
                return None, (
                    f"Step {step_number}: "
                    "depends_on contains duplicate dependencies."
                )

            normalized_task = {
                "tool": tool_name,
                "arguments": normalized_arguments,
                "depends_on": list(dependency_data),
            }

        else:
            normalized_task = {
                "tool": tool_name,
                "arguments": normalized_arguments,
            }

        normalized_tasks.append(normalized_task)

    return normalized_tasks, None

# ============================================================
# 5. STRUCTURED RESULT HANDLING
# ============================================================


def tool_result_succeeded(tool_name, result):
    """Determine success using structured results, not text matching."""

    if not isinstance(result, dict):
        return False

    if result.get("tool") != tool_name:
        return False

    if result.get("success") is not True:
        return False

    # Older valid results may not include a status field.
    # If supplied, the status must indicate an accepted action.
    status = result.get("status")
    if status is not None and status != "accepted":
        return False

    return True


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


def verification_evidence_is_valid(verification):
    """Check that a verification result contains structured evidence."""

    if not isinstance(verification, dict):
        return False

    if verification.get("success") is not True:
        return False

    if verification.get("status") != "verified":
        return False

    evidence = verification.get("evidence")

    if not isinstance(evidence, dict):
        return False

    check = evidence.get("check")
    observed = evidence.get("observed")

    return (
        isinstance(check, str)
        and bool(check.strip())
        and isinstance(observed, str)
        and bool(observed.strip())
    )


def format_verification_evidence(verification):
    """Format valid structured verification evidence for display."""

    if not verification_evidence_is_valid(verification):
        return (
            verification.get("error", "Verification failed.")
            if isinstance(verification, dict)
            else "Verification returned an invalid result."
        )

    evidence = verification["evidence"]

    return f"{evidence['check']}: {evidence['observed']}"


# ============================================================
# 6. BASIC TASK PLANNER
# ============================================================

def execute_website_with_verification(arguments):
    """Open an approved website and independently verify reachability."""

    result = execute_tool("open_website", **arguments)

    if not tool_result_succeeded("open_website", result):
        return result, None

    verification = verify_website_reachable(
        arguments.get("site_name")
    )

    return result, verification


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
# 7. BASIC PLAN EXECUTOR
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
# 8. AI PLANNER AND EXECUTOR
# ============================================================


def website_was_requested(user_request, arguments):
    """Only permit website actions explicitly requested by the user."""

    site_name = arguments.get("site_name")

    if not isinstance(site_name, str):
        return False

    site_name = site_name.strip().casefold()

    if site_name not in ALLOWED_WEBSITES:
        return False

    request_lower = " ".join(user_request.casefold().split())

    accepted_phrases = {
        "google": ["open google", "visit google", "go to google"],
        "youtube": ["open youtube", "visit youtube", "go to youtube"],
        "github": ["open github", "visit github", "go to github"],
    }

    return any(
        phrase in request_lower
        for phrase in accepted_phrases[site_name]
    )



def is_application_launch_request(message):
    """Return True when the message explicitly asks to launch an application."""

    if not isinstance(message, str):
        return False

    request = " ".join(message.lower().strip().split())

    prefixes = (
        "",
        "please ",
        "can you ",
        "could you ",
        "would you ",
        "please can you ",
        "please could you ",
        "i want you to ",
        "i need you to ",
    )

    actions = ("open ", "launch ", "start ", "run ")

    return any(
        request.startswith(prefix + action)
        for prefix in prefixes
        for action in actions
    )


def application_was_requested(user_request, arguments):
    """Only permit launching an application explicitly requested by the user."""

    app_name = arguments.get("app_name")

    if not isinstance(app_name, str) or not app_name.strip():
        return False

    if app_name.lower() not in ALLOWED_APPLICATIONS:
        return False

    # Reject negative requests such as "I don't want to open Notepad."
    if not is_application_launch_request(user_request):
        return False

    # Normalize whitespace and punctuation before checking app names.
    import re

    request = " ".join(user_request.lower().split())
    request = re.sub(r"[^\w\s]", " ", request)
    request = " ".join(request.split())

    requested_app = " ".join(app_name.lower().split())

    # Allow multiple applications when each is explicitly named
    # in the user's launch request.
    return re.search(
        r"\b" + re.escape(requested_app) + r"\b",
        request,
    ) is not None


def execute_ai_agent_task(message):
    """Ask the local AI to plan tasks, validate them, and execute them."""

    plan_data = ask_local_ai_for_plan(message)

    if not isinstance(plan_data, dict):
        return "The AI planner returned an invalid plan."

    tasks = plan_data.get("tasks", [])

    if not isinstance(tasks, list):
        return "The AI planner returned an invalid task list."


    if not tasks:
        if is_application_launch_request(message):
            return (
                "I couldn't identify a valid application action for "
                "your request. Please check the application name "
                "and try again."
            )

        return (
            "I couldn't determine the required action for this request. "
            "Please rephrase it."
        )





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

        if (
            tool_name == "open_application"
            and not application_was_requested(
                message,
                normalized_arguments,
            )
        ):
            return "Application action blocked because it was not requested."

        print(f"Agent step {step_number}: {tool_name}")

        result = execute_tool(tool_name, **normalized_arguments)

        results.append(
            f"{tool_name}: {format_tool_result(result)}"
        )

        if not tool_result_succeeded(tool_name, result):
            results.append("Execution stopped because the tool failed.")
            break

    return "\n".join(results)

def record_blocked_steps(results, tasks, failed_step_number):
    """Record all planned steps that cannot execute after a failure."""

    for blocked_step_number in range(
        failed_step_number + 1,
        len(tasks) + 1,
    ):
        blocked_task = tasks[blocked_step_number - 1]

        if isinstance(blocked_task, dict):
            blocked_tool = blocked_task.get("tool", "unknown")
        else:
            blocked_tool = "unknown"

        results.append(
            f"Step {blocked_step_number}: {blocked_tool} "
            f"blocked because Step {failed_step_number} failed"
        )

# ============================================================
# 9. RESULT-AWARE TASK EXECUTION
# ============================================================


def task_has_failed_dependency(task, failed_steps):
    """Return True when a task depends on a failed step."""

    if not isinstance(task, dict):
        return False

    dependencies = task.get("depends_on", [])

    if not isinstance(dependencies, list):
        return False

    return any(
        dependency in failed_steps
        for dependency in dependencies
    )
def validate_requested_action(tool_name, arguments, message):
    """Validate that AI-selected arguments match the user's request."""

    request_lower = message.lower()

    if tool_name == "get_weather" and "weather" in request_lower:
        if " in " in request_lower:
            requested_city = (
                message.rsplit(" in ", 1)[1]
                .strip()
                .rstrip(".!?")
            )

            selected_city = arguments.get("city", "").strip()

            if requested_city.casefold() != selected_city.casefold():
                return (
                    f"You requested weather for {requested_city}, "
                    f"but the AI selected {selected_city}."
                )

    if tool_name == "open_website":
        requested_website = None

        for site_name in ALLOWED_WEBSITES:
            if re.search(
                r"\b(?:open|visit|go to)\s+"
                + re.escape(site_name)
                + r"\b",
                request_lower,
            ):
                requested_website = site_name
                break

        if requested_website is not None:
            selected_website = (
                arguments.get("site_name", "").strip()
            )

            if (
                selected_website.casefold()
                != requested_website.casefold()
            ):
                return (
                    f"You requested {requested_website.title()}, "
                    f"but the AI selected {selected_website}."
                )

    if tool_name == "open_application":
        requested_application = None

        for app_name in ALLOWED_APPLICATIONS:
            if re.search(
                r"\b(?:open|launch|start|run)\s+"
                + re.escape(app_name)
                + r"\b",
                request_lower,
            ):
                requested_application = app_name
                break

        if requested_application is not None:
            selected_application = (
                arguments.get("app_name", "").strip()
            )

            if (
                selected_application.casefold()
                != requested_application.casefold()
            ):
                return (
                    "Application action blocked. "
                    f"You requested {requested_application}, "
                    f"but the AI selected {selected_application}."
                )

    return None

def execute_result_aware_task(message):
    """Execute AI-planned tasks with verified results and execution history."""

    plan_data = ask_local_ai_for_plan(message)

    tasks, plan_error = validate_ai_plan(
        plan_data,
        message,
    )

    if plan_error:
        return plan_error

    if not tasks:
        if is_application_launch_request(message):
            return (
                "I couldn't identify a valid application action for "
                "your request. Please check the application name "
                "and try again."
            )

        return (
            "I couldn't determine the required action for this request. "
            "Please rephrase it."
        )

    if len(tasks) > 5:
        return "The plan contains too many tasks. Please simplify your request."

    # Keep a complete execution history.
    # Every planned step must end up as either:
    # - executed successfully
    # - executed and failed
    # - blocked because an earlier step failed
    results = []
    execution_results = {}
    failed_steps = set()

    for step_number, task in enumerate(tasks, start=1):

        # ------------------------------------------------------------
        # If an earlier step failed, do not execute dependent steps.
        # Record them explicitly as blocked instead.
        # ------------------------------------------------------------
        if task_has_failed_dependency(task, failed_steps):
            blocked_tool = "unknown"

            if isinstance(task, dict):
                blocked_tool = task.get("tool", "unknown")

            dependencies = task.get("depends_on", [])

            failed_dependency = next(
                dependency
                for dependency in dependencies
                if dependency in failed_steps
            )

            results.append(
                f"Step {step_number}: {blocked_tool} blocked because "
                f"Step {failed_dependency} failed"
            )

            failed_steps.add(step_number)

            continue

        if not isinstance(task, dict):
            results.append(
                f"Step {step_number}: Invalid task."
            )

            failed_steps.add(step_number)
            continue

        tool_name = task.get("tool")
        arguments = task.get("arguments", {})

        normalized_arguments, error = validate_tool_arguments(
            tool_name,
            arguments,
        )

        if error:
            results.append(
                f"Step {step_number}: {error}"
            )

            failed_steps.add(step_number)
            continue
        semantic_error = validate_requested_action(
            tool_name,
            normalized_arguments,
            message,
        )

        if semantic_error:
            results.append(
                f"Step {step_number}: {semantic_error}"
            )

            failed_steps.add(step_number)
            continue

        if (
            tool_name == "open_website"
            and not website_was_requested(
                message,
                normalized_arguments,
            )
        ):
            results.append(
                f"Step {step_number}: Website action blocked because "
                "it was not requested."
            )

            failed_steps.add(step_number)
            continue

        if (
            tool_name == "open_application"
            and not application_was_requested(
                message,
                normalized_arguments,
            )
        ):
            results.append(
                f"Step {step_number}: Application action blocked because "
                "it was not requested."
            )

            failed_steps.add(step_number)
            continue

        print(f"Agent step {step_number}: {tool_name}")

        verification = None

        # ------------------------------------------------------------
        # Website execution + independent verification
        # ------------------------------------------------------------
        if tool_name == "open_website":
            result, verification = execute_website_with_verification(
                normalized_arguments
            )
            execution_results[step_number] = result

            succeeded = tool_result_succeeded(
                tool_name,
                result,
            )

            if succeeded:
                if verification_evidence_is_valid(
                    verification
                ):
                    results.append(
                        f"Step {step_number}: "
                        f"{tool_name}: {format_tool_result(result)}"
                    )

                    results.append(
                        "Independent verification: "
                        + format_verification_evidence(
                            verification
                        )
                    )
                else:
                    results.append(
                        f"Step {step_number}: "
                        f"{tool_name}: {format_tool_result(result)}"
                    )

                    results.append(
                        "Independent verification failed."
                    )

                    succeeded = False
            else:
                results.append(
                    f"Step {step_number}: "
                    f"{tool_name}: {format_tool_result(result)}"
                )

        # ------------------------------------------------------------
        # Normal tool execution
        # ------------------------------------------------------------
        else:
            result = execute_tool(
                tool_name,
                **normalized_arguments
            )
            execution_results[step_number] = result

            succeeded = tool_result_succeeded(
                tool_name,
                result
            )

            results.append(
                f"Step {step_number}: "
                f"{tool_name}: {format_tool_result(result)}"
            )

        # ------------------------------------------------------------
        # Failure handling
        # ------------------------------------------------------------
        if not succeeded:
            failed_steps.add(step_number)

            print(
                f"Agent observation: {tool_name} failed."
            )

            print(
                "Agent decision: Continue with independent tasks."
            )

            # Preserve the failed step in execution history.
            results.append(
                "Execution continued because independent tasks may still run."
            )

            continue

        # ------------------------------------------------------------
        # Special handling for internet prerequisite
        # ------------------------------------------------------------
        if tool_name == "check_internet":
            print(
                "Agent observation: Internet check succeeded."
            )
            print(
                "Agent decision: Continue with remaining tasks."
            )

    summary_prompt = (
        "You are MyOwnJARVIS. Summarize the actual tool results "
        "in simple language. Do not invent facts or claim that "
        "an unexecuted task succeeded.\n\n"
        f"User request: {message}\n\n"
        "Actual execution history:\n"
        + "\n".join(results)
        + "\n\nStructured execution results:\n"
        + result_to_json(execution_results)
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
# 10. TOOL RETRY SYSTEM
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
# 11. AI-GUIDED RECOVERY WITH EXPERIENCE MEMORY
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
# 12. CONDITIONAL MULTI-STEP AI AGENT
# ============================================================

def execute_conditional_task(message):
    """Plan, execute, observe structured results, and recover safely."""

    execution_history = []
    max_steps = 5
    request_lower = message.lower()

    # Do not execute application actions for informational questions.
    informational_question = (
        request_lower.strip().startswith((
            "how do i ",
            "how can i ",
            "how to ",
            "what is the way to ",
            "can you explain how to ",
            "tell me how to ",
            "can you tell me how to ",
            "could you tell me how to ",
        ))
        and any(
            re.search(
                r"\b(?:open|launch|start|run)\s+"
                + re.escape(app_name)
                + r"\b",
                request_lower,
            )
            for app_name in ALLOWED_APPLICATIONS
        )
    )

    if informational_question:
        return (
            "I can explain how to open an application, "
            "but I won't launch it unless you explicitly ask me to."
        )


    # Give a clear response for unsupported standalone application requests.
    if is_application_launch_request(message):
        normalized_request = " ".join(
            request_lower.strip().rstrip(".!?").split()
        )

        prefixes = (
            "please can you ",
            "please could you ",
            "can you ",
            "could you ",
            "would you ",
            "please ",
            "i want you to ",
            "i need you to ",
        )

        launch_target = normalized_request

        for prefix in prefixes:
            if launch_target.startswith(prefix):
                launch_target = launch_target[len(prefix):]
                break

        for action in ("open ", "launch ", "start ", "run "):
            if launch_target.startswith(action):
                launch_target = launch_target[len(action):]
                break

        if (
            launch_target
            and launch_target not in ALLOWED_APPLICATIONS
            and launch_target not in ALLOWED_WEBSITES
            and "." not in launch_target
            and not any(
                phrase in request_lower
                for phrase in (
                    "internet",
                    "connection",
                    "weather",
                    "temperature",
                )
            )
        ):
            return (
                f"{launch_target.title()} is unsupported. "
                "I can open Notepad, Calculator, or Paint."
            )


    needs_internet = (
        "internet" in request_lower
        or "connection" in request_lower
    )

    needs_weather = (
        "weather" in request_lower
        or "temperature" in request_lower
    )


    # Detect application launches only when the request starts
    # with an explicit launch instruction.

    # Reject negative application requests, but allow application
    # requests inside compound tasks such as checking internet first.



    negative_application_request = bool(
        re.search(
            r"\b(?:don't|do not|dont)\b"
            r".{0,40}\b(?:open|launch|start|run)\s+"
            r"(?:notepad|calculator|paint)\b",
            request_lower,
        )
    ) or bool(
        re.search(
            r"\b(?:don't want to|do not want to|"
            r"don't want you to|do not want you to)\b"
            r".{0,20}\b(?:open|launch|start|run)\s+"
            r"(?:notepad|calculator|paint)\b",
            request_lower,
        )
    )

    # Stop immediately when the user explicitly rejects an app launch.
    if negative_application_request:
        return "Okay, I won't open or launch that application."




    needs_application = (
        not negative_application_request
        and any(
            re.search(
                r"\b(?:open|launch|start|run)\s+"
                + re.escape(app_name)
                + r"\b",
                request_lower,
            )
            for app_name in ALLOWED_APPLICATIONS
        )
    )

    requested_application = None

    if needs_application:
        for app_name in ALLOWED_APPLICATIONS:
            if re.search(
                r"\b(?:open|launch|start|run)\s+"
                + re.escape(app_name)
                + r"\b",
                request_lower,
            ):
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
            "go to google",
            "go to youtube",
            "go to github",
        ]
    )


    requested_website = None

    for site_name in ALLOWED_WEBSITES:
        if any(
            phrase in request_lower
            for phrase in [
                f"open {site_name}",
                f"visit {site_name}",
                f"go to {site_name}",
            ]
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
                and not item.get("tool", "").endswith("_verification")
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
            lines = []

            for index, item in enumerate(execution_history, start=1):
                status = item.get("status")

                if status not in {"accepted", "verified", "failed"}:
                    result = item.get("result")
                    result_status = (
                        result.get("status")
                        if isinstance(result, dict)
                        else None
                    )

                    if result_status in {"accepted", "verified", "failed"}:
                        status = result_status
                    else:
                        status = (
                            "accepted"
                            if item.get("success") is True
                            else "failed"
                        )

                lines.append(
                    f"Step {index}: {item['tool']} - "
                    f"{status.upper()}: {item['message']}"
                )

            history_text = "\n".join(lines)
        else:
            history_text = "No tools were executed."

        return f"{message_text}\n\nExecution history:\n{history_text}"

    # --------------------------------------------------------
    # Direct action selection
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Single-action execution
    # --------------------------------------------------------

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

                    # Independently verify successful application launches.
        if (
            tool_name == "open_application"
            and "open_application" in get_successful_tools()
        ):
            verification = verify_application_running(
                arguments.get("app_name")
            )
            verification_success = verification_evidence_is_valid(
                verification
            )
            verification_message = format_verification_evidence(
                verification
            )
            verification_status = (
                "verified" if verification_success else "failed"
            )

            execution_history.append({
                "tool": "application_verification",
                "arguments": {
                    "app_name": arguments.get("app_name")
                },
                "success": verification_success,
                "status": verification_status,
                "message": verification_message,
                "result": verification,
                "attempts": 1,
            })

            print(
                f"Agent verification: "
                f"{verification_status.upper()}: "
                f"{verification_message}"
            )

            if not verification_success:
                return finish(
                    "Task incomplete: Windows accepted the application "
                    "launch request, but the application's running "
                    "process could not be independently verified."
                )

        if (
            tool_name == "check_internet"
            and "check_internet" in get_successful_tools()
        ):
            verification = verify_internet_connection()
            verification_succeeded = verification_evidence_is_valid(
                verification
            )
            verification_message = format_verification_evidence(
                verification
            )

            execution_history.append({
                "tool": "internet_verification",
                "arguments": {},
                "success": verification_succeeded,
                "status": (
                    "verified" if verification_succeeded else "failed"
                ),
                "message": verification_message,
                "result": verification,
                "attempts": 1,
            })

            if verification_succeeded:
                return finish(
                    "Task completed successfully. "
                    "Internet connectivity independently verified."
                )

            return finish(
                "The internet-check action succeeded, but independent "
                "verification failed."
            )


        if tool_name == "open_application":
            return finish(
                "Application launch accepted and running process "
                "independently verified."
            )

        return finish(
            (
                "Action accepted. The tool reported success, "
                "but the outcome has not been independently verified."
            )
            if succeeded
            else "Task incomplete."
        )


    # --------------------------------------------------------
    # Multi-step AI execution
    # --------------------------------------------------------

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

            verification_results = [
                item
                for item in execution_history
                if item.get("tool", "").endswith("_verification")
            ]

            if any(
                item.get("status") != "verified"
                for item in verification_results
            ):
                return finish(
                    "Task incomplete: one or more required verifications failed."
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

        # Ensure the selected application matches the user's request.
        if (
            tool_name == "open_application"
            and needs_application
            and requested_application is not None
        ):
            selected_application = (
                normalized_arguments.get("app_name", "").strip()
            )

            if (
                selected_application.casefold()
                != requested_application.casefold()
            ):
                return finish(
                    "Task incomplete: You requested "
                    f"{requested_application}, but the AI selected "
                    f"{selected_application}."
                )

        # Ensure the selected weather city matches the user's request.
        if (
            tool_name == "get_weather"
            and needs_weather
            and " in " in request_lower
        ):
            requested_city = (
                message.rsplit(" in ", 1)[1]
                .strip()
                .rstrip(".!?")
            )

            selected_city = normalized_arguments.get("city", "").strip()

            if requested_city.casefold() != selected_city.casefold():
                return finish(
                    "Task incomplete: You requested weather for "
                    f"{requested_city}, but the AI selected "
                    f"{selected_city}."
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

        if succeeded and (
            actual_tool != tool_name
            or actual_arguments != normalized_arguments
        ):
            return finish(
                "Task incomplete: Recovery performed a different action "
                "or used different arguments than originally requested."
            )

        print(f"Agent observation: {result_message}")

        if not succeeded:
            return finish("Task incomplete: " + result_message)

        # Independently verify successful internet-check actions.
        if actual_tool == "check_internet":
            verification = verify_internet_connection()
            verification_success = verification_evidence_is_valid(
                verification
            )
            verification_message = format_verification_evidence(
                verification
            )
            verification_status = (
                "verified" if verification_success else "failed"
            )

            execution_history.append({
                "tool": "internet_verification",
                "arguments": {},
                "success": verification_success,
                "status": verification_status,
                "message": verification_message,
                "result": verification,
                "attempts": 1,
            })

            print(
                f"Agent verification: "
                f"{verification_status.upper()}: "
                f"{verification_message}"
            )

            if not verification_success:
                return finish(
                    "Task incomplete: the internet-check action succeeded, "
                    "but independent verification failed."
                )

        # Independently verify successful application launches.
        if actual_tool == "open_application":
            verification = verify_application_running(
                actual_arguments.get("app_name")
            )
            verification_success = verification_evidence_is_valid(
                verification
            )
            verification_message = format_verification_evidence(
                verification
            )
            verification_status = (
                "verified" if verification_success else "failed"
            )

            execution_history.append({
                "tool": "application_verification",
                "arguments": {
                    "app_name": actual_arguments.get("app_name")
                },
                "success": verification_success,
                "status": verification_status,
                "message": verification_message,
                "result": verification,
                "attempts": 1,
            })

            print(
                f"Agent verification: "
                f"{verification_status.upper()}: "
                f"{verification_message}"
            )

            if not verification_success:
                return finish(
                    "Task incomplete: Windows accepted the application "
                    "launch request, but the application's running "
                    "process could not be independently verified."
                )

        successful_tools = get_successful_tools()
        missing_tools = required_tools - successful_tools

        if required_tools and not missing_tools:
            verification_results = [
                item
                for item in execution_history
                if item.get("tool", "").endswith("_verification")
            ]

            failed_verifications = [
                item
                for item in verification_results
                if item.get("status") != "verified"
            ]

            if failed_verifications:
                return finish(
                    "Task incomplete: one or more required verifications failed."
                )

            verified_count = sum(
                1
                for item in verification_results
                if item.get("status") == "verified"
            )

            if verified_count:
                return finish(
                    "All requested tool actions succeeded. "
                    f"{verified_count} independent verification(s) passed."
                )

            return finish(
                "All requested tool actions were accepted or succeeded. "
                "Their outcomes have not all been independently verified."
            )

        if not required_tools:
            return finish("Task completed successfully.")

    return finish(
        f"The agent reached its maximum of {max_steps} actions."
    )


# ============================================================
# 13. DIRECT TESTING
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

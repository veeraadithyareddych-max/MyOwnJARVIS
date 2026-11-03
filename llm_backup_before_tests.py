
# MyOwnJARVIS - Local AI Language Model
# Local inference using Ollama and Qwen 2.5 3B

import json
import urllib.request
import urllib.error


OLLAMA_API_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "qwen2.5:3b"
REQUEST_TIMEOUT = 120

ALLOWED_TOOLS = {
    "check_internet",
    "get_weather",
    "open_application",
    "open_website",
}

ALLOWED_APPLICATIONS = {"notepad", "calculator", "paint"}
ALLOWED_WEBSITES = {"google", "youtube", "github"}


def _call_ollama(messages, json_format=False):
    """Send messages to Ollama and return the assistant response text."""

    data = {
        "model": MODEL_NAME,
        "messages": messages,
        "stream": False,
    }

    if json_format:
        data["format"] = "json"

    request_data = json.dumps(data).encode("utf-8")

    request = urllib.request.Request(
        OLLAMA_API_URL,
        data=request_data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urllib.request.urlopen(
        request,
        timeout=REQUEST_TIMEOUT,
    ) as response:
        result = json.loads(response.read().decode("utf-8"))

    content = result.get("message", {}).get("content")

    if not isinstance(content, str):
        raise ValueError("Ollama returned an invalid response format.")

    return content


def _safe_json_response(messages, fallback):
    """Call Ollama for JSON and return a fallback on failure."""

    try:
        response = _call_ollama(messages, json_format=True)
        parsed = json.loads(response)

        if isinstance(parsed, dict):
            return parsed

        return fallback.copy()

    except (
        urllib.error.URLError,
        TimeoutError,
        OSError,
        ValueError,
        TypeError,
        KeyError,
        json.JSONDecodeError,
    ):
        return fallback.copy()


def ask_local_ai(message):
    """Send a normal text question to the local AI model."""

    try:
        return _call_ollama(
            [{"role": "user", "content": str(message)}]
        )

    except urllib.error.URLError:
        return (
            "I could not connect to Ollama. "
            "Please check that Ollama is running."
        )

    except (TimeoutError, OSError, ValueError, KeyError, TypeError):
        return "I could not process the local AI response."


def ask_local_ai_for_plan(message):
    """Ask the local AI to plan a task using approved tools."""

    system_prompt = """
You are the task planner for MyOwnJARVIS.

Available tools:
1. check_internet: arguments {}
2. get_weather: arguments {"city": "city name"}
3. open_application: arguments {"app_name": "notepad"}
   Allowed applications: notepad, calculator, paint
4. open_website: arguments {"site_name": "google"}
   Allowed websites: google, youtube, github

Rules:
- Select tools only when the user requests an action.
- Use the city explicitly requested by the user for weather.
- Do not invent missing city names, websites, or applications.
- Do not use tools outside the available list.
- If no tool is needed, return an empty tasks list.
- Return only JSON.

Required format:
{
  "tasks": [
    {
      "tool": "check_internet",
      "arguments": {}
    }
  ]
}

If no tool is required:
{"tasks": []}
"""

    fallback = {"tasks": []}

    result = _safe_json_response(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": str(message)},
        ],
        fallback,
    )

    tasks = result.get("tasks")

    if not isinstance(tasks, list):
        return fallback

    validated_tasks = []

    for task in tasks:
        if not isinstance(task, dict):
            continue

        tool = task.get("tool")
        arguments = task.get("arguments", {})

        if tool not in ALLOWED_TOOLS:
            continue

        if not isinstance(arguments, dict):
            continue

        if _validate_recovery_arguments(tool, arguments) is not None:
            continue

        validated_tasks.append(
            {"tool": tool, "arguments": arguments}
        )

    return {"tasks": validated_tasks}


def ask_local_ai_for_next_action(user_request, execution_history):
    """Choose the next action using the user's request and actual results."""

    system_prompt = """
You are the conditional task planner for MyOwnJARVIS.

Available tools and arguments:

1. check_internet: {}
2. get_weather: {"city": "city name"}
3. open_application: {"app_name": "notepad"}
   Allowed applications: notepad, calculator, paint
4. open_website: {"site_name": "google"}
   Allowed websites: google, youtube, github

Rules:
- Select exactly one tool per response.
- Select tools only when needed for the user's request.
- Read the execution history and use actual tool results.
- Never repeat an action that has already succeeded.
- For requests involving internet checking followed by weather,
  check internet first, then get weather if appropriate.
- Use the city explicitly stated in the original request.
- Open a website only if the user explicitly requests it.
- Open an application only if the user explicitly requests it.
- If all requested actions have succeeded, set done=true.
- If a required action cannot be completed safely, stop.
- Do not invent tools, arguments, or results.
- Return only valid JSON.

For an action:
{
  "done": false,
  "tool": "check_internet",
  "arguments": {},
  "message": "Checking the internet."
}

For completion:
{
  "done": true,
  "tool": null,
  "arguments": {},
  "message": "The task is complete."
}
"""

    user_prompt = (
        f"User request:\n{user_request}\n\n"
        f"Execution history:\n{execution_history}\n\n"
        "Choose the next action using the actual results."
    )

    fallback = {
        "done": True,
        "tool": None,
        "arguments": {},
        "message": "The local AI planner failed. Stopping safely.",
    }

    result = _safe_json_response(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        fallback,
    )

    if not isinstance(result.get("done"), bool):
        return fallback

    if result["done"]:
        return {
            "done": True,
            "tool": None,
            "arguments": {},
            "message": str(
                result.get("message", "The task is complete.")
            ),
        }

    tool = result.get("tool")
    arguments = result.get("arguments", {})

    if tool not in ALLOWED_TOOLS or not isinstance(arguments, dict):
        return fallback

    if _validate_recovery_arguments(tool, arguments) is not None:
        return fallback

    return {
        "done": False,
        "tool": tool,
        "arguments": arguments,
        "message": str(result.get("message", "Executing the next action.")),
    }


def _validate_recovery_arguments(tool, arguments):
    """Validate tool names and argument structures.

    Return None when arguments are valid, otherwise return an error string.
    """

    if tool not in ALLOWED_TOOLS:
        return "Unsupported tool."

    if not isinstance(arguments, dict):
        return "Arguments must be a JSON object."

    if tool == "check_internet":
        if arguments:
            return "check_internet does not accept arguments."

    elif tool == "get_weather":
        if set(arguments) != {"city"}:
            return "get_weather requires only the city argument."

        city = arguments.get("city")

        if not isinstance(city, str) or not city.strip():
            return "A non-empty city name is required."

        if len(city.strip()) > 100:
            return "The city name is too long."

    elif tool == "open_application":
        if set(arguments) != {"app_name"}:
            return "open_application requires only app_name."

        app_name = arguments.get("app_name")

        if (
            not isinstance(app_name, str)
            or app_name.lower() not in ALLOWED_APPLICATIONS
        ):
            return "The requested application is not allowed."

    elif tool == "open_website":
        if set(arguments) != {"site_name"}:
            return "open_website requires only site_name."

        site_name = arguments.get("site_name")

        if (
            not isinstance(site_name, str)
            or site_name.lower() not in ALLOWED_WEBSITES
        ):
            return "The requested website is not allowed."

    return None


def ask_local_ai_for_recovery(
    user_request,
    failed_tool,
    arguments,
    error_message,
    execution_history,
    past_experiences=None,
):
    """Recommend one safe recovery action using relevant past experiences."""

    experiences_text = json.dumps(
        past_experiences or [],
        ensure_ascii=False,
        indent=2,
        default=str,
    )

    system_prompt = """
You are the recovery planner for MyOwnJARVIS, a local AI agent.

Your job is to recommend one safe next action after a tool failure.

Available tools:
1. check_internet: {}
2. get_weather: {"city": "city name"}
3. open_application: {"app_name": "notepad"}
   Allowed applications: notepad, calculator, paint
4. open_website: {"site_name": "google"}
   Allowed websites: google, youtube, github

Rules:
- Review relevant past experiences.
- Give more weight to past experiences with outcome SUCCESS.
- Past outcomes are evidence, not guarantees.
- Reuse a previous recovery only when it fits the current request.
- The current user request and actual tool results take priority.
- Never reuse an old city or website if it conflicts with the current request.
- Never invent missing information.
- Correct arguments only when the current request provides enough information.
- Never open a website unless explicitly requested by the user.
- Never repeat an identical failed action.
- Never recommend tools outside the available list.
- If no safe recovery is possible, return recover=false.
- Return only valid JSON without Markdown fences.

RECOVERY EXAMPLES:
- If the user asks for weather in Chennai and get_weather fails
  because city is empty, recover with get_weather and
  {"city": "Chennai"}.
- If the user asks for weather in Mumbai and get_weather fails
  because city is empty, recover with get_weather and
  {"city": "Mumbai"}.
- If the city is not stated or reliably available from the
  current request, do not guess a city.
- If an argument is missing but can be directly recovered
  from the user's request, prefer correcting that argument
  instead of refusing recovery.
- Do not copy a city from past experiences when it conflicts
  with the current request.

When recovery is safe:
{
  "recover": true,
  "tool": "get_weather",
  "arguments": {"city": "Chennai"},
  "reason": "The city is explicitly stated in the current request."
}

When recovery is unsafe:
{
  "recover": false,
  "tool": null,
  "arguments": {},
  "reason": "Explain why recovery should stop."
}
"""

    user_prompt = f"""
USER REQUEST:
{user_request}

FAILED TOOL:
{failed_tool}

FAILED ARGUMENTS:
{json.dumps(arguments, ensure_ascii=False, default=str)}

ERROR MESSAGE:
{error_message}

EXECUTION HISTORY:
{execution_history}

PAST EXPERIENCES:
{experiences_text}

Review the request, error, history, and experiences.
Return one safe recovery decision in the required JSON format.
"""

    fallback = {
        "recover": False,
        "tool": None,
        "arguments": {},
        "reason": "The local AI recovery planner failed. Stopping safely.",
    }

    decision = _safe_json_response(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        fallback,
    )

    if not isinstance(decision.get("recover"), bool):
        return {
            "recover": False,
            "tool": None,
            "arguments": {},
            "reason": "The recovery decision has an invalid recover flag.",
        }

    if decision["recover"] is False:
        return {
            "recover": False,
            "tool": None,
            "arguments": {},
            "reason": str(
                decision.get("reason", "Recovery was declined.")
            ),
        }

    tool = decision.get("tool")
    recovery_arguments = decision.get("arguments", {})

    validation_error = _validate_recovery_arguments(
        tool,
        recovery_arguments,
    )

    if validation_error:
        return {
            "recover": False,
            "tool": None,
            "arguments": {},
            "reason": f"Recovery blocked: {validation_error}",
        }

    # Additional safety: do not let a recovery open an unrequested website.
    if tool == "open_website":
        request_text = str(user_request).lower()

        explicit_website_intent = any(
            phrase in request_text
            for phrase in (
                "open google",
                "open youtube",
                "open github",
                "visit google",
                "visit youtube",
                "visit github",
                "go to google",
                "go to youtube",
                "go to github",
            )
        )

        if not explicit_website_intent:
            return {
                "recover": False,
                "tool": None,
                "arguments": {},
                "reason": (
                    "Recovery blocked because the user did not "
                    "explicitly request opening a website."
                ),
            }

    return {
        "recover": True,
        "tool": tool,
        "arguments": recovery_arguments,
        "reason": str(
            decision.get("reason", "Safe recovery recommended.")
        ),
    }


if __name__ == "__main__":
    print("MyOwnJARVIS - Local AI Test")
    print("-" * 35)

    question = input("You: ").strip()

    if question:
        answer = ask_local_ai(question)
        print("\nLocal AI:", answer)
    else:
        print("Please enter a question.")

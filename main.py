
# MyOwnJARVIS - Main Assistant
# Handles conversation, memory, AI planning, tool execution,
# and memory inspection commands.

from datetime import datetime

from memory import initialize_memory, save_memory, get_memories
from intent_model import predict_intent
from agent import (
    execute_tool,
    execute_ai_agent_task,
    execute_conditional_task,
)
from llm import ask_local_ai
from memory_commands import handle_memory_command


def handle_intent(message):
    """Handle supported intents and approved tools."""

    intent = predict_intent(message)
    message_lower = message.lower().strip()

    if intent == "greeting":
        return "Hello! How can I help you?"

    elif intent == "identity":
        return "I am JARVIS, your personal AI assistant."

    elif intent == "time":
        current_time = datetime.now().strftime("%I:%M %p")
        return f"The current time is {current_time}."

    elif intent == "goodbye":
        return "Goodbye! See you next time."

    elif intent == "help":
        return (
            "Here are some things I can do:\n"
            "- Answer questions using local AI\n"
            "- Remember and recall information\n"
            "- Tell you the current time and date\n"
            "- Open Notepad, Calculator, and Paint\n"
            "- Open Google, YouTube, and GitHub\n"
            "- Check internet connectivity\n"
            "- Retrieve weather for a city\n"
            "- Execute supported multi-step tasks\n"
            "- Inspect recovery experiences and statistics\n"
            "- Exit the assistant"
        )

    elif intent == "open_app":
        for app_name in ["notepad", "calculator", "paint"]:
            if app_name in message_lower:
                return execute_tool(
                    "open_application",
                    app_name=app_name,
                )

        return "I can open Notepad, Calculator, or Paint."

    elif intent == "open_website":
        for site_name in ["google", "youtube", "github"]:
            if site_name in message_lower:
                return execute_tool(
                    "open_website",
                    site_name=site_name,
                )

        return "I can open Google, YouTube, or GitHub."

    elif intent == "check_internet":
        return execute_tool("check_internet")

    elif intent == "get_weather":
        city = "Chennai"

        if " in " in message_lower:
            city = message_lower.rsplit(" in ", 1)[1].strip()

            for ending in [" please", " today", " now"]:
                if city.endswith(ending):
                    city = city[:-len(ending)].strip()

        return execute_tool("get_weather", city=city)

    else:
        return ask_local_ai(message)


def respond_to_user(message):
    """Handle conversation, memory, date, and time requests."""

    original_message = message.strip()
    normalized_message = original_message.lower().strip()
    normalized_message = normalized_message.rstrip("?!., ")

    # Basic conversation
    if normalized_message in ["hello", "hi", "hey"]:
        return "Hello! How can I help you?"

    elif normalized_message in ["what is your name", "who are you"]:
        return "I am JARVIS, your personal AI assistant."

    elif normalized_message in ["how are you", "how are you doing"]:
        return "I'm running properly and ready to help you!"

    elif normalized_message in ["what can you do", "your features", "features"]:
        return (
            "I can answer questions using my local AI model, "
            "remember information, plan tasks using an AI planner, "
            "open approved applications and websites, check internet "
            "connectivity, retrieve weather information, and inspect "
            "my saved recovery experiences."
        )

    # Explicit time commands
    elif normalized_message in [
        "what time is it",
        "tell me the time",
        "current time",
        "what is the time",
    ]:
        current_time = datetime.now().strftime("%I:%M %p")
        return f"The current time is {current_time}."

    # Date commands
    elif normalized_message in [
        "what is today's date",
        "what is the date",
        "today's date",
        "tell me today's date",
        "current date",
    ]:
        current_date = datetime.now().strftime("%d %B %Y")
        return f"Today's date is {current_date}."

    # Help
    elif normalized_message in ["help", "help me"]:
        return (
            "Try these commands:\n"
            "- hello\n"
            "- who are you\n"
            "- what time is it\n"
            "- what is today's date\n"
            "- remember that I like Python\n"
            "- show my memories\n"
            "- my name is Veera\n"
            "- call me Vee\n"
            "- what is my name\n"
            "- what is my nickname\n"
            "- open Notepad\n"
            "- open YouTube\n"
            "- check internet\n"
            "- weather in Mumbai\n"
            "- check internet and weather in Chennai\n"
            "- show experiences\n"
            "- show recovery stats\n"
            "- show failed recoveries\n"
            "- show weather experiences\n"
            "- show internet experiences\n"
            "- help memory\n"
            "- exit"
        )

    # Save general memories
    elif normalized_message.startswith("remember "):
        information = original_message[len("remember "):].strip()

        if information:
            save_memory(information)
            return f"I'll remember that: {information}"

        return "Please tell me what you want me to remember."

    # Retrieve saved memories
    elif normalized_message in [
        "what do you remember about me",
        "show my memories",
        "show memory",
    ]:
        memories = get_memories()

        if not memories:
            return "I haven't saved anything yet."

        saved_information = [
            f"{memory_id}. {information}"
            for memory_id, information in memories
        ]

        return "Here is what I remember:\n" + "\n".join(saved_information)

    # Save the user's name
    elif normalized_message.startswith("my name is "):
        full_name = original_message[len("my name is "):].strip()

        if full_name:
            save_memory(f"full_name: {full_name}")
            return f"Nice to meet you, {full_name}!"

        return "Please tell me your name."

    # Save the user's nickname
    elif normalized_message.startswith("call me "):
        nickname = original_message[len("call me "):].strip()

        if nickname:
            save_memory(f"nickname: {nickname}")
            return f"Of course! I'll call you {nickname}."

        return "What would you like me to call you?"

    # Retrieve the user's name
    elif normalized_message in ["what is my name", "what's my name"]:
        memories = get_memories()

        for memory_id, information in reversed(memories):
            if information.startswith("full_name: "):
                name = information[len("full_name: "):]
                return f"Your full name is {name}."

        return "I don't know your full name yet."

    # Retrieve the user's nickname
    elif normalized_message in ["what is my nickname", "what do you call me"]:
        memories = get_memories()

        for memory_id, information in reversed(memories):
            if information.startswith("nickname: "):
                nickname = information[len("nickname: "):]
                return f"I call you {nickname}."

        return "You haven't chosen a nickname yet."

    # General questions go to the local language model
    else:
        return ask_local_ai(original_message)


def main():
    """Run the main JARVIS conversation loop."""

    print("=" * 45)
    print("Welcome to MyOwnJARVIS!")
    print("Type 'help' for commands.")
    print("Type 'help memory' for memory commands.")
    print("Type 'exit' to quit.")
    print("=" * 45)

    while True:
        user_message = input("\nYou: ").strip()

        if not user_message:
            continue

        if user_message.lower().strip() in ["exit", "quit", "bye"]:
            print("JARVIS: Goodbye! See you next time.")
            break

        # Stage 5: Handle memory inspection commands first.
        memory_response = handle_memory_command(user_message)

        if memory_response is not None:
            print("JARVIS:", memory_response)
            continue

        intent = predict_intent(user_message)
        print("Detected intent:", intent)

        message_lower = user_message.lower()

        # Detect requests that may require tools.
        tool_keywords = [
            "internet",
            "connection",
            "weather",
            "temperature",
            "open ",
            "visit ",
        ]

        requires_tool = any(
            keyword in message_lower
            for keyword in tool_keywords
        )

        # Route tool requests through the AI agent.
        if requires_tool:
            multi_step_keywords = [
                "if",
                "and then",
                "after that",
                "based on",
                "depending on",
            ]

            is_multi_step = any(
                keyword in message_lower
                for keyword in multi_step_keywords
            )

            if is_multi_step:
                response = execute_conditional_task(user_message)
            else:
                response = execute_ai_agent_task(user_message)

            # Fall back to normal conversation if no tool plan was created.
            if response is None:
                response = respond_to_user(user_message)

        else:
            response = respond_to_user(user_message)

        print("JARVIS:", response)


if __name__ == "__main__":
    initialize_memory()
    main()

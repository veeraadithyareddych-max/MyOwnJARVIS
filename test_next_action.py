
from llm import ask_local_ai_for_next_action

request = (
    "Check my internet connection and, if it works, "
    "get the weather in Mumbai."
)

history = "No tools have been executed yet."

decision = ask_local_ai_for_next_action(request, history)

print("User request:", request)
print("Planner decision:", decision)


from llm import ask_local_ai_for_plan

request = "Check my internet connection and get the weather in Mumbai."

plan = ask_local_ai_for_plan(request)

print("User request:", request)
print("AI-generated plan:", plan)

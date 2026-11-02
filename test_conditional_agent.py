
from agent import execute_conditional_task

request = (
    "Check my internet connection. If it is working, "
    "get the weather in Mumbai."
)

print("User request:", request)
print()

result = execute_conditional_task(request)

print()
print("Final result:")
print(result)

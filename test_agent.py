from intent_model import predict_intent
from main import handle_intent

test_messages = [
    "hello",
    "who are you",
    "what time is it",
    "see you later",
]

for message in test_messages:
    print(f"\nYou: {message}")
    print("Predicted intent:", predict_intent(message))
    print("JARVIS:", handle_intent(message))
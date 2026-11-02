from intent_model import predict_intent

test_messages = [
    "hello",
    "what time is it",
    "what is my nickname",
    "please call me buddy",
]

for message in test_messages:
    intent = predict_intent(message)
    print(f"Message: {message}")
    print(f"Predicted intent: {intent}")
    print("-" * 30)
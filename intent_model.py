
# MyOwnJARVIS - First Machine Learning Model
# This model predicts the intent behind a user's message.

from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline


# --------------------------------------------------
# 1. TRAINING EXAMPLES
# Each message teaches JARVIS what the user may mean.
# --------------------------------------------------

training_messages = [
    # Greeting
    "hello",
    "hi",
    "hey jarvis",
    "hey there",
    "good morning",
    "good evening",
    "how are you",

    # Identity
    "what is your name",
    "who are you",
    "tell me about yourself",
    "who is jarvis",
    "introduce yourself",
    "what are you",
    "tell me your identity",

    # Time
    "what time is it",
    "what is the time",
    "tell me the time",
    "show the current time",
    "what time is it now",
    "can you tell me the time",
    "what time it is",

    # Save memory
    "remember my favorite language is java",
    "remember my name is veera adithya reddy",
    "save this information",
    "remember this",
    "save this for later",

    # Recall memory
    "what do you remember about me",
    "show my memories",
    "what information have you saved",
    "please show my saved information",
    "show my memory",

    # Set full name
    "my name is veera adithya reddy",
    "my full name is veera adithya reddy",
    "remember my name is veera adithya reddy",
    "my name is veera",
    "my full name is veera",

    # Set nickname
    "call me darling",
    "you can call me boss",
    "my nickname is veera",
    "change my nickname to buddy",
    "please call me buddy",
    "call me buddy",
    "call me by a nickname",

    # Get full name
    "what is my name",
    "what is my full name",
    "tell me my full name",
    "what's my name",

    # Get nickname
    "what is my nickname",
    "what do you call me",
    "which nickname do I use",
    "tell me my nickname",
    "please tell me my nickname",
    "what nickname did I choose",

    # Goodbye
    "goodbye",
    "exit",
    "see you later",
    "see you soon",
    "talk to you later",
    "bye for now",
    "bye",
    "good night",

    # Help
    "help",
    "show help",
    "what commands can you do",
    "list available commands",
    "what can I ask you",
    "how can you help me",
    
    
    # Open application
    "open notepad",
    "launch notepad",
    "start notepad",
    "please open notepad",
    "can you open notepad",
    "open the notepad application",
    
    
    # Open approved applications
    "open calculator",
    "launch calculator",
    "start calculator",
    "open paint",
    "launch paint",
    "start paint",


    # Open website
    "open google",
    "launch google",
    "open youtube",
    "launch youtube",
    "open github",
    "launch github",
    
    
    # Check internet connectivity
    "check internet",
    "check my internet connection",
    "is the internet working",
    "am I connected to the internet",
    "test internet connection",

    # Weather requests
    "check weather",
    "what is the weather",
    "show me the weather",
    "weather in chennai",
    "what is the temperature",
    "tell me the weather in chennai",
    
        "what is an ai",
    "what is artificial intelligence",
    "explain artificial intelligence",
    "explain what an ai agent is",
    "explain what an ai agent is in simple words",
    "what is machine learning",
    "explain machine learning",
    "what is deep learning",
    "tell me about neural networks",
    "explain how an ai agent works",
    "what is a language model",
    "explain this concept",


]


# --------------------------------------------------
# 2. INTENT LABELS
# Each label corresponds to the message at the same
# position in training_messages.
# --------------------------------------------------

training_intents = [
    # Greeting: 7
    "greeting", "greeting", "greeting", "greeting",
    "greeting", "greeting", "greeting",

    # Identity: 7
    "identity", "identity", "identity", "identity",
    "identity", "identity", "identity",

    # Time: 7
    "time", "time", "time", "time", "time", "time", "time",

    # Save memory: 5
    "save_memory", "save_memory", "save_memory",
    "save_memory", "save_memory",

    # Recall memory: 5
    "recall_memory", "recall_memory", "recall_memory",
    "recall_memory", "recall_memory",

    # Set full name: 5
    "set_name", "set_name", "set_name", "set_name", "set_name",

    # Set nickname: 7
    "set_nickname", "set_nickname", "set_nickname",
    "set_nickname", "set_nickname", "set_nickname",
    "set_nickname",

    # Get full name: 4
    "get_name", "get_name", "get_name", "get_name",

    # Get nickname: 6
    "get_nickname", "get_nickname", "get_nickname",
    "get_nickname", "get_nickname", "get_nickname",

    # Goodbye: 8
    "goodbye", "goodbye", "goodbye", "goodbye",
    "goodbye", "goodbye", "goodbye", "goodbye",

    # Help: 6
    "help", "help", "help", "help", "help", "help",
    
    
    # Open application: 6
    "open_app",
    "open_app",
    "open_app",
    "open_app",
    "open_app",
    "open_app",
    
    
    # Open approved applications: 6
    "open_app",
    "open_app",
    "open_app",
    "open_app",
    "open_app",
    "open_app",
    
    
    # Open website: 6
    "open_website",
    "open_website",
    "open_website",
    "open_website",
    "open_website",
    "open_website",
    
    
    # Check internet: 5
    "check_internet",
    "check_internet",
    "check_internet",
    "check_internet",
    "check_internet",


    # Weather: 6
    "get_weather",
    "get_weather",
    "get_weather",
    "get_weather",
    "get_weather",
    "get_weather",

    "general_question",
    "general_question",
    "general_question",
    "general_question",
    "general_question",
    "general_question",
    "general_question",
    "general_question",
    "general_question",
    "general_question",
    "general_question",
    "general_question",

]


# --------------------------------------------------
# 3. CHECK TRAINING DATA
# Every message must have exactly one matching label.
# --------------------------------------------------

if len(training_messages) != len(training_intents):
    raise ValueError(
        "Training error: each message must have one intent label."
    )


# --------------------------------------------------
# 4. CREATE THE MACHINE-LEARNING PIPELINE
# CountVectorizer converts text into word counts.
# MultinomialNB learns patterns from those word counts.
# --------------------------------------------------

model = Pipeline([
    ("vectorizer", CountVectorizer()),
    ("classifier", MultinomialNB()),
])


# --------------------------------------------------
# 5. TRAIN THE MODEL
# --------------------------------------------------

model.fit(training_messages, training_intents)


# --------------------------------------------------
# 6. PREDICT THE INTENT OF A USER MESSAGE
# main.py can import and call this function.
# --------------------------------------------------

def predict_intent(message):
    """Predict the intent behind a user's message."""

    if not isinstance(message, str) or not message.strip():
        return "unknown"

    return model.predict([message.strip().lower()])[0]


# --------------------------------------------------
# 7. TEST THE MODEL WHEN THIS FILE IS RUN DIRECTLY
# --------------------------------------------------

test_messages = [
    "hey there",
    "can you tell me the time",
    "please show my saved information",
    "who are you",
    "see you soon",
    "my full name is veera adithya reddy",
    "please call me buddy",
    "what is my nickname",
    "help",
]


if __name__ == "__main__":
    print("MyOwnJARVIS intent model trained successfully!")
    print("Number of training examples:", len(training_messages))
    print("Number of intent categories:", len(set(training_intents)))

    print("\nTesting the model:\n")

    for message in test_messages:
        prediction = predict_intent(message)
        print(f"Message: {message}")
        print(f"Predicted intent: {prediction}")
        print("-" * 40)

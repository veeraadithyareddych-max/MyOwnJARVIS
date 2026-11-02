
# MyOwnJARVIS - Intent Classification Model
# Uses CountVectorizer and MultinomialNB to predict user intent.

from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline


# --------------------------------------------------
# 1. TRAINING EXAMPLES GROUPED BY INTENT
# This structure keeps messages and labels aligned.
# --------------------------------------------------

training_examples = {
    "greeting": [
        "hello",
        "hi",
        "hey jarvis",
        "hey there",
        "good morning",
        "good evening",
        "how are you",
    ],

    "identity": [
        "what is your name",
        "who are you",
        "tell me about yourself",
        "who is jarvis",
        "introduce yourself",
        "what are you",
        "tell me your identity",
    ],

    "time": [
        "what time is it",
        "what is the time",
        "tell me the time",
        "show the current time",
        "what time is it now",
        "can you tell me the time",
        "what time it is",
    ],

    "save_memory": [
        "remember my favorite language is java",
        "remember my name is veera adithya reddy",
        "save this information",
        "remember this",
        "save this for later",
        "remember that I like Python",
        "remember that I like Maths",
        "remember that I like JavaScript",
        "remember my favorite subject is maths",
        "remember my favorite food is pizza",
        "remember my hobby is reading",
    ],

    "recall_memory": [
        "what do you remember about me",
        "show my memories",
        "what information have you saved",
        "please show my saved information",
        "show my memory",
        "list everything you remember about me",
    ],

    "set_name": [
        "my name is veera adithya reddy",
        "my full name is veera adithya reddy",
        "remember my name is veera adithya reddy",
        "my name is veera",
        "my full name is veera",
    ],

    "set_nickname": [
        "call me darling",
        "you can call me boss",
        "my nickname is veera",
        "change my nickname to buddy",
        "please call me buddy",
        "call me buddy",
        "call me by a nickname",
    ],

    "get_name": [
        "what is my name",
        "what is my full name",
        "tell me my full name",
        "what's my name",
    ],

    "get_nickname": [
        "what is my nickname",
        "what do you call me",
        "which nickname do I use",
        "tell me my nickname",
        "please tell me my nickname",
        "what nickname did I choose",
    ],

    "goodbye": [
        "goodbye",
        "exit",
        "see you later",
        "see you soon",
        "talk to you later",
        "bye for now",
        "bye",
        "good night",
    ],

    "help": [
        "help",
        "show help",
        "what commands can you do",
        "list available commands",
        "what can I ask you",
        "how can you help me",
    ],

    "open_app": [
        "open notepad",
        "launch notepad",
        "start notepad",
        "please open notepad",
        "can you open notepad",
        "open the notepad application",
        "open calculator",
        "launch calculator",
        "start calculator",
        "open paint",
        "launch paint",
        "start paint",
    ],

    "open_website": [
        "open google",
        "launch google",
        "open youtube",
        "launch youtube",
        "open github",
        "launch github",
    ],

    "check_internet": [
        "check internet",
        "check my internet connection",
        "is the internet working",
        "am I connected to the internet",
        "test internet connection",
    ],

    "get_weather": [
        "check weather",
        "what is the weather",
        "show me the weather",
        "weather in chennai",
        "what is the temperature",
        "tell me the weather in chennai",
    ],

    "general_question": [
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

        # Academic subject preferences
        "what subject do I like",
        "which subject do I like",
        "what is my favorite subject",
        "what is my favourite subject",
        "what subject do I prefer",
        "which academic subject do I like",

        # Programming language preferences
        "what programming language do I like",
        "which programming language do I like",
        "what programming language do I prefer",
        "which programming language do I prefer",
        "what is my favorite programming language",
        "what is my favourite programming language",

        # Other personal preferences
        "what hobbies do I like",
        "what is my favorite food",
        "what music do I like",
        "what are my interests",
        "what do you know about my preferences",
        "what are my hobbies",
        "what is my favorite color",
        "what do I like",
        "tell me about my preferences",
        "what do I prefer",
    ],
}


# --------------------------------------------------
# 2. GENERATE TRAINING MESSAGES AND LABELS
# Each message automatically receives its correct label.
# This prevents message-label count mismatches.
# --------------------------------------------------

training_messages = []
training_intents = []

for intent, messages in training_examples.items():
    for message in messages:
        training_messages.append(message.lower().strip())
        training_intents.append(intent)


# --------------------------------------------------
# 3. VALIDATE TRAINING DATA
# --------------------------------------------------

if not training_messages:
    raise ValueError("Training error: no training examples found.")

if len(training_messages) != len(training_intents):
    raise ValueError(
        "Training error: each message must have one intent label."
    )


# --------------------------------------------------
# 4. CREATE THE MACHINE-LEARNING PIPELINE
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
# 6. RULES FOR CLEAR, COMMON QUESTIONS
# These prevent common nickname questions from being
# confused with preference questions.
# --------------------------------------------------

NICKNAME_QUESTIONS = {
    "what is my nickname",
    "what's my nickname",
    "what do you call me",
    "which nickname do i use",
    "tell me my nickname",
    "please tell me my nickname",
    "what nickname did i choose",
}

NAME_QUESTIONS = {
    "what is my name",
    "what's my name",
    "what is my full name",
    "tell me my full name",
}

PREFERENCE_STARTS = (
    "what subject do i like",
    "which subject do i like",
    "what is my favorite subject",
    "what is my favourite subject",
    "what subject do i prefer",
    "which academic subject do i like",
    "what programming language do i like",
    "which programming language do i like",
    "what programming language do i prefer",
    "which programming language do i prefer",
    "what is my favorite programming language",
    "what is my favourite programming language",
    "what hobbies do i like",
    "what are my hobbies",
    "what is my favorite food",
    "what music do i like",
    "what are my interests",
    "what do you know about my preferences",
    "what is my favorite color",
    "what do i like",
    "what do i prefer",
    "tell me about my preferences",
)


# --------------------------------------------------
# 7. PREDICT USER INTENT
# This function remains compatible with main.py.
# --------------------------------------------------

def predict_intent(message):
    """Predict the intent behind a user's message."""

    if not isinstance(message, str) or not message.strip():
        return "unknown"

    normalized_message = " ".join(
        message.lower().strip().rstrip("?!.,").split()
    )

    # Exact questions get reliable classifications.
    if normalized_message in NICKNAME_QUESTIONS:
        return "get_nickname"

    if normalized_message in NAME_QUESTIONS:
        return "get_name"

    # Personal preference questions should be handled
    # as general questions, not nickname questions.
    if any(
        normalized_message == question
        or normalized_message.startswith(question + " ")
        for question in PREFERENCE_STARTS
    ):
        return "general_question"

    # Use the trained machine-learning model for all
    # other messages.
    return model.predict([normalized_message])[0]


# --------------------------------------------------
# 8. TEST THE MODEL WHEN RUN DIRECTLY
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
    "what subject do I like",
    "what programming language do I like",
    "what is my favorite subject",
    "what is my name",
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

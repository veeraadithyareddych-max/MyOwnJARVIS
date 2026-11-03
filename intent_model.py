
# ============================================================
# MyOwnJARVIS - Intent Classification Model
# Uses CountVectorizer and MultinomialNB to predict user intent.
# Includes rule-based handling for common follow-up questions.
# ============================================================

import re

from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline


# --------------------------------------------------
# 1. TRAINING EXAMPLES GROUPED BY INTENT
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

        # Follow-up and explanation requests
        "explain that again",
        "explain it again",
        "explain this in simple words",
        "make it simpler",
        "explain more simply",
        "give me a short example",
        "give me another example",
        "give me an example using animals",
        "explain the code line by line",
        "summarize it",
        "summarize it in three sentences",
        "continue explaining",
        "what does that mean",
        "why does that happen",
        "how does that work",
        "show another way",
        "give me a different example",

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
# 4. CREATE AND TRAIN THE MACHINE-LEARNING PIPELINE
# --------------------------------------------------

model = Pipeline([
    ("vectorizer", CountVectorizer()),
    ("classifier", MultinomialNB()),
])

model.fit(training_messages, training_intents)


# --------------------------------------------------
# 5. RULES FOR CLEAR, COMMON QUESTIONS
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

# Common follow-up phrases that should reach the conversational AI.
FOLLOW_UP_PATTERNS = (
    r"\bexplain (?:it|that|this)(?: again| more)?\b",
    r"\bexplain .+ in simple words\b",
    r"\bexplain .+ simply\b",
    r"\bmake it simpler\b",
    r"\bmake that simpler\b",
    r"\bsimplify (?:it|that|this)\b",
    r"\bgive me (?:a )?(?:short )?example\b",
    r"\bgive me another example\b",
    r"\bshow me another example\b",
    r"\banother example\b",
    r"\bexample using .+\b",
    r"\busing .+ as an example\b",
    r"\bexplain .+ line by line\b",
    r"\bwalk me through .+\b",
    r"\bsummarize (?:it|that|this)\b",
    r"\bsummarise (?:it|that|this)\b",
    r"\bsummarize .+\b",
    r"\bsummarise .+\b",
    r"\bin three sentences\b",
    r"\bin simpler words\b",
    r"\bwhat does (?:it|that|this) mean\b",
    r"\bwhy does (?:it|that) happen\b",
    r"\bhow does (?:it|that) work\b",
    r"\bcontinue explaining\b",
    r"\bexplain further\b",
    r"\bshow another way\b",
    r"\bgive me a different example\b",
)


def _normalize_message(message):
    """Normalize whitespace and punctuation for intent matching."""
    normalized = message.lower().strip()
    normalized = re.sub(r"[?!.,]+$", "", normalized)
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized


def _is_follow_up_request(message):
    """Return True when the message looks like a conversational follow-up."""
    return any(
        re.search(pattern, message)
        for pattern in FOLLOW_UP_PATTERNS
    )


# --------------------------------------------------
# 6. PREDICT USER INTENT
# Compatible with main.py's existing predict_intent call.
# --------------------------------------------------

def predict_intent(message):
    """Predict the intent behind a user's message."""

    if not isinstance(message, str) or not message.strip():
        return "unknown"

    normalized_message = _normalize_message(message)

    # Exact questions get reliable classifications.
    if normalized_message in NICKNAME_QUESTIONS:
        return "get_nickname"

    if normalized_message in NAME_QUESTIONS:
        return "get_name"

    # Personal preference questions should be handled as general questions.
    if any(
        normalized_message == question
        or normalized_message.startswith(question + " ")
        for question in PREFERENCE_STARTS
    ):
        return "general_question"

    # Follow-up requests should go to the conversational AI.
    # Check these before the ML model to avoid misleading predictions.
    if _is_follow_up_request(normalized_message):
        return "general_question"

    # Use the trained machine-learning model for other messages.
    return model.predict([normalized_message])[0]


# --------------------------------------------------
# 7. TEST THE MODEL WHEN RUN DIRECTLY
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
    "Give me a short example.",
    "Give me another example using animals.",
    "Explain the code line by line.",
    "Summarize it in three sentences.",
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

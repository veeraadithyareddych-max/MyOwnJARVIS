
# MyOwnJARVIS - Lesson 1
# Our first interactive personal assistant



def respond_to_user(message):
    """Choose a response based on the user's message."""

    message = message.lower().strip()
    message = message.rstrip("?!., ")

    if message in ["hello", "hi", "hey"]:
        return "Hello! How can I help you?"

    elif message in ["what is your name", "who are you"]:
        return "I am JARVIS, your personal AI assistant."

    elif message in ["how are you", "how are you doing"]:
        return "I'm running properly and ready to help you!"

    elif message in ["what can you do", "your features", "features"]:
        return (
            "Currently, I can respond to basic commands. "
            "We will gradually add memory, machine learning, "
            "tools, and voice interaction."
        )

    elif message in ["what time is it", "tell me the time"]:
        from datetime import datetime
        current_time = datetime.now().strftime("%I:%M %p")
        return f"The current time is {current_time}."

    elif message in ["what is today's date", "what is the date", "today's date"]:
        from datetime import datetime
        current_date = datetime.now().strftime("%d %B %Y")
        return f"Today's date is {current_date}."

    elif message == "help":
        return (
            "Try these commands:\n"
            "- hello\n"
            "- who are you\n"
            "- how are you\n"
            "- what can you do\n"
            "- what time is it\n"
            "- what is today's date\n"
            "- exit"
        )

    else:
        return (
            "I don't understand that request yet. "
            "Type 'help' to see what I can do."
        )



def main():
    print("=" * 40)
    print("Welcome to MyOwnJARVIS!")
    print("Type 'help' for commands.")
    print("Type 'exit' to quit.")
    print("=" * 40)

    while True:
        user_message = input("\nYou: ")

        if user_message.lower().strip() == "exit":
            print("JARVIS: Goodbye! See you next time.")
            break

        response = respond_to_user(user_message)
        print("JARVIS:", response)


if __name__ == "__main__":
    main()

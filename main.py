
# MyOwnJARVIS - Lesson 1
# Our first interactive personal assistant


def respond_to_user(message):
    """Choose a response based on the user's message."""

    message = message.lower().strip()

    if message in ["hello", "hi", "hey"]:
        return "Hello! How can I help you?"

    elif message in ["what is your name", "who are you"]:
        return "I am JARVIS, your personal AI assistant."

    elif message == "help":
        return (
            "You can say hello, ask my name, "
            "or type exit to stop."
        )

    else:
        return "I don't understand that request yet."


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

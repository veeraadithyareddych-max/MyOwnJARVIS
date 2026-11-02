
from memory import initialize_memory, save_memory, get_memories


def main():
    """Run the manual memory demonstration only when requested."""
    initialize_memory()

    save_memory("My favorite programming language is Java.")

    print("JARVIS Memory:")
    for index, item in enumerate(get_memories(), start=1):
        print(f"{index}. {item}")


if __name__ == "__main__":
    main()

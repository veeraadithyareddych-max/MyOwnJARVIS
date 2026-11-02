
from memory import initialize_memory, save_memory, get_memories

initialize_memory()

save_memory("My favorite programming language is Java.")

print("JARVIS Memory:")

for memory_id, information in get_memories():
    print(f"{memory_id}. {information}")


from memory import (
    get_recent_experiences,
    get_experience_stats,
    get_memories_by_category,
)


def show_experiences(limit=10, tool_filter=None, failures_only=False):
    """Display saved recovery experiences."""
    experiences = get_recent_experiences(limit=100)

    if tool_filter:
        experiences = [
            item for item in experiences
            if tool_filter.lower() in item.get("failed_tool", "").lower()
        ]

    if failures_only:
        experiences = [
            item for item in experiences
            if item.get("outcome", "").upper() != "SUCCESS"
        ]

    experiences = experiences[:limit]

    if not experiences:
        return "No matching experiences found."

    lines = ["\n===== JARVIS RECOVERY EXPERIENCES ====="]

    for item in experiences:
        lines.extend([
            f"\nID: {item['id']}",
            f"Request: {item['user_request']}",
            f"Failed tool: {item['failed_tool']}",
            f"Error: {item.get('error_message') or 'None'}",
            f"Recovery tool: {item.get('recovery_tool') or 'None'}",
            f"Recovery arguments: {item.get('recovery_arguments') or '{}'}",
            f"Outcome: {item['outcome']}",
            f"Date: {item['created_at']}",
            "-" * 40,
        ])

    return "\n".join(lines)


def show_recovery_stats():
    """Display recovery statistics."""
    stats = get_experience_stats()

    lines = [
        "\n===== JARVIS RECOVERY STATISTICS =====",
        f"Total recorded outcomes: {stats['total']}",
        f"Successful outcomes: {stats['successes']}",
        f"Unsuccessful outcomes: {stats['failures']}",
        f"Recorded success rate: {stats['success_rate']}%",
        "",
        "Statistics by tool:",
    ]

    if not stats["by_tool"]:
        lines.append("No experience records yet.")
    else:
        for item in stats["by_tool"]:
            lines.append(
                f"- {item['failed_tool']}: "
                f"{item['successes']}/{item['attempts']} successful"
            )

    return "\n".join(lines)


def show_category_memories(category):
    """Display saved memories belonging to a category."""
    memories = get_memories_by_category(category)

    if not memories:
        return f"I don't have any memories categorized as '{category}' yet."

    lines = [
        f"\n===== JARVIS {category.upper()} MEMORIES ====="
    ]

    for memory_id, information in memories:
        lines.append(f"- ID {memory_id}: {information}")

    lines.append(f"\nTotal: {len(memories)} memories")
    return "\n".join(lines)


def handle_memory_command(message):
    """Handle memory inspection commands. Return None for other messages."""
    command = " ".join(message.lower().strip().split())

    # Existing recovery commands
    if command in (
        "show experiences",
        "show experience",
        "show memory experiences",
    ):
        return show_experiences()

    if command in ("show recovery stats", "show experience stats"):
        return show_recovery_stats()

    if command in ("show failed recoveries", "show failed experiences"):
        return show_experiences(failures_only=True)

    if command == "show weather experiences":
        return show_experiences(tool_filter="get_weather")

    if command == "show internet experiences":
        return show_experiences(tool_filter="check_internet")

    # New categorized-memory commands
    category_commands = {
        "show project memories": "project",
        "show projects": "project",
        "show goal memories": "goal",
        "show goals": "goal",
        "show education memories": "education",
        "show education": "education",
        "show skill memories": "skill",
        "show skills": "skill",
        "show preference memories": "preference",
        "show preferences": "preference",
        "show personal memories": "personal",
        "show personal": "personal",
        "show general memories": "general",
        "show general": "general",
    }

    if command in category_commands:
        return show_category_memories(category_commands[command])

    if command in ("help memory", "help memories"):
        return (
            "\nJARVIS Memory Commands:\n"
            "- show experiences\n"
            "- show recovery stats\n"
            "- show failed recoveries\n"
            "- show weather experiences\n"
            "- show internet experiences\n"
            "- show project memories\n"
            "- show goal memories\n"
            "- show education memories\n"
            "- show skill memories\n"
            "- show preference memories\n"
            "- show personal memories\n"
            "- show general memories\n"
            "- help memory"
        )

    return None

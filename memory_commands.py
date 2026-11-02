
import json

from memory import get_recent_experiences, get_experience_stats


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


def handle_memory_command(message):
    """Handle memory inspection commands. Return None for other messages."""

    command = " ".join(message.lower().strip().split())

    if command in ("show experiences", "show experience", "show memory experiences"):
        return show_experiences()

    if command in ("show recovery stats", "show experience stats"):
        return show_recovery_stats()

    if command in ("show failed recoveries", "show failed experiences"):
        return show_experiences(failures_only=True)

    if command == "show weather experiences":
        return show_experiences(tool_filter="get_weather")

    if command == "show internet experiences":
        return show_experiences(tool_filter="check_internet")

    if command == "help memory":
        return (
            "\nJARVIS Memory Commands:\n"
            "- show experiences\n"
            "- show recovery stats\n"
            "- show failed recoveries\n"
            "- show weather experiences\n"
            "- show internet experiences\n"
            "- help memory"
        )

    return None

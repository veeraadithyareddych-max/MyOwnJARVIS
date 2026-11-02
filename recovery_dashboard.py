
"""Phase 4: MyOwnJARVIS recovery performance dashboard."""

from memory import get_experience_stats, get_recent_experiences


def show_dashboard():
    """Display recovery statistics and recent recovery experiences."""

    print("\n" + "=" * 55)
    print("           MyOwnJARVIS PERFORMANCE DASHBOARD")
    print("=" * 55)

    try:
        stats = get_experience_stats()

        total = stats.get("total", 0)
        successes = stats.get("successes", 0)
        failures = stats.get("failures", 0)
        success_rate = stats.get("success_rate", 0.0)
        by_tool = stats.get("by_tool", [])

        print("\nOVERALL PERFORMANCE")
        print("-" * 55)
        print(f"Total recovery attempts : {total}")
        print(f"Successful recoveries   : {successes}")
        print(f"Failed recoveries       : {failures}")
        print(f"Success rate            : {success_rate:.1f}%")

        if total == 0:
            print("\nNo recovery experiences have been recorded yet.")
            print("Use JARVIS and try again after a tool failure.")
        else:
            bar_length = 30
            filled = round(bar_length * success_rate / 100)
            bar = "#" * filled + "-" * (bar_length - filled)
            print(f"\nRecovery success: [{bar}] {success_rate:.1f}%")

        print("\nPERFORMANCE BY TOOL")
        print("-" * 55)

        if not by_tool:
            print("No tool-specific statistics available.")
        else:
            for item in by_tool:
                tool = item.get("failed_tool", "unknown")
                attempts = item.get("attempts", 0)
                tool_successes = item.get("successes", 0)
                tool_rate = (
                    tool_successes / attempts * 100 if attempts else 0
                )

                print(
                    f"{tool}: {tool_successes}/{attempts} successful "
                    f"({tool_rate:.1f}%)"
                )

        print("\nRECENT RECOVERY EXPERIENCES")
        print("-" * 55)

        experiences = get_recent_experiences(limit=5)

        if not experiences:
            print("No recovery experiences found.")
        else:
            for index, experience in enumerate(experiences, start=1):
                if not isinstance(experience, dict):
                    print(f"{index}. {experience}")
                    continue

                request = experience.get("user_request", "Unknown request")
                failed_tool = experience.get("failed_tool", "Unknown tool")
                recovery_tool = experience.get(
                    "recovery_tool", "Unknown recovery tool"
                )
                outcome = experience.get("outcome", "Unknown")
                error = experience.get("error_message", "No error details")

                print(f"\n{index}. Request: {request}")
                print(f"   Failed tool: {failed_tool}")
                print(f"   Recovery tool: {recovery_tool}")
                print(f"   Outcome: {outcome}")
                print(f"   Error: {error}")

        print("\n" + "=" * 55)
        print("Dashboard complete. Existing memory was not modified.")
        print("=" * 55)

    except Exception as error:
        print("\nCould not load the recovery dashboard.")
        print(f"Details: {error}")
        print(
            "Check memory.py and ensure the database is accessible."
        )


if __name__ == "__main__":
    show_dashboard()

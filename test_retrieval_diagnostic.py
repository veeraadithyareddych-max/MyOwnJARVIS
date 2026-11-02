
"""Inspect how JARVIS ranks saved recovery experiences."""

from memory import get_relevant_experiences


SCENARIOS = [
    {
        "request": "Get the weather in Chennai",
        "tool": "get_weather",
        "error": "Please provide a city name.",
        "expected": "chennai",
    },
    {
        "request": "Get the weather in Mumbai",
        "tool": "get_weather",
        "error": "Please provide a city name.",
        "expected": "mumbai",
    },
]


def main():
    print("\nJARVIS RETRIEVAL DIAGNOSTIC")
    print("=" * 50)

    for scenario in SCENARIOS:
        matches = get_relevant_experiences(
            failed_tool=scenario["tool"],
            error_message=scenario["error"],
            limit=5,
            user_request=scenario["request"],
        )

        print(f"\nRequest: {scenario['request']}")
        print(f"Expected city in top result: {scenario['expected']}")

        if not matches:
            print("No matching experiences found.")
            continue

        for rank, experience in enumerate(matches, start=1):
            print(f"\nRank {rank}:")
            print("Request:", experience.get("user_request"))
            print("Outcome:", experience.get("outcome"))
            print("Recovery arguments:", experience.get("recovery_arguments"))

        top = matches[0]
        top_text = (
            str(top.get("user_request", "")) + " " +
            str(top.get("recovery_arguments", ""))
        ).lower()

        if scenario["expected"] in top_text:
            print("\nTop result: PASS")
        else:
            print("\nTop result: CHECK RANKING")

    print("\nDiagnostic finished. No database changes were made.")


if __name__ == "__main__":
    main()

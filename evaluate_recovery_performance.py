
"""Phase 3: evaluate experience retrieval in an isolated database."""

import tempfile
import os

import memory


SCENARIOS = [
    {
        "request": "Get the weather in Chennai",
        "failed_tool": "get_weather",
        "error": "City argument was missing",
        "expected": "chennai",
    },
    {
        "request": "Get the weather in Mumbai",
        "failed_tool": "get_weather",
        "error": "City argument was missing",
        "expected": "mumbai",
    },
    {
        "request": "Check my internet connection",
        "failed_tool": "check_internet",
        "error": "Connection timed out",
        "expected": "internet",
    },
]


def main():
    original_database = memory.DATABASE_NAME
    passed = 0
    results = []

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            memory.DATABASE_NAME = os.path.join(
                temp_dir, "evaluation_memory.sqlite3"
            )

            memory.initialize_memory()

            # Insert known sample experiences into the temporary database.
            memory.save_experience(
                user_request="Get the weather in Chennai",
                failed_tool="get_weather",
                failed_arguments={},
                error_message="City argument was missing",
                recovery_tool="get_weather",
                recovery_arguments={"city": "Chennai"},
                outcome="SUCCESS",
            )

            memory.save_experience(
                user_request="Get the weather in Mumbai",
                failed_tool="get_weather",
                failed_arguments={},
                error_message="City argument was missing",
                recovery_tool="get_weather",
                recovery_arguments={"city": "Mumbai"},
                outcome="SUCCESS",
            )

            memory.save_experience(
                user_request="Check my internet connection",
                failed_tool="check_internet",
                failed_arguments={},
                error_message="Connection timed out",
                recovery_tool="check_internet",
                recovery_arguments={},
                outcome="SUCCESS",
            )

            print("\nJARVIS EXPERIENCE RETRIEVAL EVALUATION")
            print("=" * 45)

            for scenario in SCENARIOS:
                matches = memory.get_relevant_experiences(
                    failed_tool=scenario["failed_tool"],
                    error_message=scenario["error"],
                    limit=3,
                    user_request=scenario["request"],
                )

                # Show the retrieved records so results can be inspected.
                print("\nRequest:", scenario["request"])
                print("Expected keyword:", scenario["expected"])

                if not matches:
                    print("Result: FAIL - no experiences retrieved")
                    results.append(False)
                    continue

                top_match = matches[0]
                print("Top retrieved experience:", top_match)

                # Check the actual top result without assuming a fixed
                # dictionary schema from the memory module.
                top_match_text = str(top_match).lower()
                success = scenario["expected"] in top_match_text

                if success:
                    print("Result: PASS")
                    passed += 1
                else:
                    print("Result: FAIL")

                results.append(success)

            total = len(SCENARIOS)
            accuracy = (passed / total * 100) if total else 0

            print("\n" + "=" * 45)
            print("Total scenarios:", total)
            print("Passed:", passed)
            print("Failed:", total - passed)
            print(f"Top-result keyword accuracy: {accuracy:.1f}%")
            print("=" * 45)

    finally:
        memory.DATABASE_NAME = original_database


if __name__ == "__main__":
    main()

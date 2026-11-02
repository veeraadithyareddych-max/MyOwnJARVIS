
"""Phase 5: Evaluate outcome-aware recovery experience selection."""

import json
import os
import tempfile

import memory


def decode_arguments(value):
    """Convert stored JSON arguments into a dictionary when possible."""
    if isinstance(value, dict):
        return value

    if isinstance(value, str):
        try:
            decoded = json.loads(value)
            if isinstance(decoded, dict):
                return decoded
        except json.JSONDecodeError:
            pass

    return {}


def add_experience(request, city, outcome):
    """Save a test experience into the temporary evaluation database."""
    memory.save_experience(
        user_request=request,
        failed_tool="get_weather",
        failed_arguments={},
        error_message="Please provide a city name.",
        recovery_tool="get_weather",
        recovery_arguments={"city": city},
        outcome=outcome,
    )


def evaluate_scenario(request, expected_city):
    """Check whether the top retrieved experience matches the request."""
    results = memory.get_relevant_experiences(
        failed_tool="get_weather",
        error_message="Please provide a city name.",
        limit=5,
        user_request=request,
    )

    if not results:
        return False, "No experience retrieved"

    top = results[0]
    arguments = decode_arguments(top.get("recovery_arguments"))
    outcome = str(top.get("outcome", "")).upper()
    actual_city = arguments.get("city", "")

    passed = (
        str(actual_city).casefold() == expected_city.casefold()
        and outcome == "SUCCESS"
    )

    description = (
        f"top_city={actual_city}, outcome={outcome}"
    )
    return passed, description


def main():
    original_database = memory.DATABASE_NAME
    scenarios = [
        ("Get the weather in Chennai", "Chennai"),
        ("Get the weather in Mumbai", "Mumbai"),
        ("Get the weather in Delhi", "Delhi"),
    ]

    passed = 0

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            memory.DATABASE_NAME = os.path.join(
                temp_dir, "adaptive_evaluation.sqlite3"
            )
            memory.initialize_memory()

            # Each city has one failed and one successful experience.
            for request, city in scenarios:
                add_experience(request, city, "FAILURE")
                add_experience(request, city, "SUCCESS")

            # Add a conflicting historical experience to test relevance.
            add_experience(
                "Get the weather in Chennai",
                "Mumbai",
                "SUCCESS",
            )

            print("\nMYOWNJARVIS ADAPTIVE RECOVERY EVALUATION")
            print("=" * 55)

            for request, expected_city in scenarios:
                success, description = evaluate_scenario(
                    request, expected_city
                )

                print(f"\nRequest: {request}")
                print(f"Expected city: {expected_city}")
                print(f"Top result: {description}")
                print("Result:", "PASS" if success else "CHECK")

                if success:
                    passed += 1

            print("\n" + "=" * 55)
            print(f"Scenarios passed: {passed}/{len(scenarios)}")
            print(
                "Top-result accuracy: "
                f"{passed / len(scenarios) * 100:.1f}%"
            )
            print("=" * 55)

            if passed != len(scenarios):
                print(
                    "\nSome scenarios need investigation. "
                    "Do not modify the retrieval algorithm blindly."
                )

    finally:
        memory.DATABASE_NAME = original_database


if __name__ == "__main__":
    main()

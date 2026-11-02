
"""Verify retrieval behavior for successful and failed experiences."""

import json
import os
import tempfile

import memory


def main():
    original_database = memory.DATABASE_NAME

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            memory.DATABASE_NAME = os.path.join(
                temp_dir, "outcome_test.sqlite3"
            )
            memory.initialize_memory()

            # Save a failed experience for Chennai.
            memory.save_experience(
                user_request="Get the weather in Chennai",
                failed_tool="get_weather",
                failed_arguments={},
                error_message="City argument was missing",
                recovery_tool="get_weather",
                recovery_arguments={"city": "WrongCity"},
                outcome="FAILURE",
            )

            # Save a successful experience for the same request.
            memory.save_experience(
                user_request="Get the weather in Chennai",
                failed_tool="get_weather",
                failed_arguments={},
                error_message="City argument was missing",
                recovery_tool="get_weather",
                recovery_arguments={"city": "Chennai"},
                outcome="SUCCESS",
            )

            results = memory.get_relevant_experiences(
                failed_tool="get_weather",
                error_message="City argument was missing",
                limit=5,
                user_request="Get the weather in Chennai",
            )

            print("\nRECOVERY OUTCOME RANKING TEST")
            print("=" * 45)

            if not results:
                print("FAIL: No experiences were retrieved.")
                return

            for rank, item in enumerate(results, start=1):
                arguments = item.get("recovery_arguments", {})
                if isinstance(arguments, str):
                    try:
                        arguments = json.loads(arguments)
                    except json.JSONDecodeError:
                        pass

                print(
                    f"Rank {rank}: outcome={item.get('outcome')}, "
                    f"arguments={arguments}"
                )

            top = results[0]
            top_outcome = str(top.get("outcome", "")).upper()
            top_arguments = top.get("recovery_arguments", {})

            if isinstance(top_arguments, str):
                try:
                    top_arguments = json.loads(top_arguments)
                except json.JSONDecodeError:
                    pass

            if (
                top_outcome == "SUCCESS"
                and isinstance(top_arguments, dict)
                and top_arguments.get("city") == "Chennai"
            ):
                print("\nPASS: The successful Chennai experience ranked first.")
            else:
                print(
                    "\nCHECK: The successful Chennai experience did not "
                    "rank first. Inspect the ranking before changing code."
                )

    finally:
        memory.DATABASE_NAME = original_database


if __name__ == "__main__":
    main()

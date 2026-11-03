
import unittest
from unittest.mock import patch

import main


class ProgrammingPromptTests(unittest.TestCase):
    """Tests for programming correctness instructions in JARVIS."""

    def setUp(self):
        self.original_history = main.SESSION_CONVERSATION_HISTORY.copy()
        main.SESSION_CONVERSATION_HISTORY.clear()

    def tearDown(self):
        main.SESSION_CONVERSATION_HISTORY.clear()
        main.SESSION_CONVERSATION_HISTORY.extend(self.original_history)

    def test_validator_keeps_a_correct_inheritance_summary(self):
        main.SESSION_CONVERSATION_HISTORY.append(
            (
                "Give me a vehicle example.",
                '''```java
class Vehicle {
    void move() {}
    void refuel() {}
}
class Car extends Vehicle {
    void honk() {}
}
```''',
            )
        )

        response = (
            "Vehicle declares move() and refuel(). "
            "Car inherits those methods and declares honk()."
        )

        result = main.validate_programming_response(
            "Summarize the most recent example.",
            response,
            "Example prompt",
        )

        self.assertEqual(result, response)

    def test_validator_retries_a_contradictory_inheritance_summary(self):
        main.SESSION_CONVERSATION_HISTORY.append(
            (
                "Give me a vehicle example.",
                '''```java
class Vehicle {
    void move() {}
    void refuel() {}
}
class Car extends Vehicle {
    void honk() {}
}
```''',
            )
        )

        captured_prompts = []

        def fake_ask_local_ai(prompt):
            captured_prompts.append(prompt)
            return (
                "Vehicle declares move() and refuel(). "
                "Car inherits both methods and declares honk(). "
                "The main method creates one Car object and calls its methods."
            )

        with patch("main.ask_local_ai", side_effect=fake_ask_local_ai):
            result = main.validate_programming_response(
                "Summarize the most recent example.",
                (
                    "Both Vehicle and Car inherit move() and refuel(). "
                    "Car overrides honk()."
                ),
                "Example prompt",
            )

        self.assertEqual(len(captured_prompts), 1)
        self.assertIn("Vehicle declares", captured_prompts[0])
        self.assertIn("Car inherits", captured_prompts[0])
        self.assertIn("Car overrides no methods", captured_prompts[0])
        self.assertIn("Car inherits both methods", result)

    def test_prompt_distinguishes_inheritance_from_overriding(self):
        prompt = main.build_conversation_prompt(
            "Explain Java inheritance."
        )

        self.assertIn(
            "A method is overridden only when",
            prompt,
        )
        self.assertIn(
            "A new subclass-specific method is not an override",
            prompt,
        )
        self.assertIn(
            "implementation of a method declared in its superclass",
            prompt,
        )

    def test_prompt_requires_code_and_explanation_to_agree(self):
        prompt = main.build_conversation_prompt(
            "Explain this Java example."
        )

        self.assertIn(
            "Make code, explanation, comments, and output agree.",
            prompt,
        )
        self.assertIn(
            "Ensure the example's explanation agrees with the code.",
            prompt,
        )

    def test_prompt_requires_explanation_of_actual_code(self):
        prompt = main.build_conversation_prompt(
            "Explain the most recent code line by line."
        )

        self.assertIn(
            "Explain only classes, methods, variables, and behavior",
            prompt,
        )
        self.assertIn(
            "If asked for line-by-line explanation, explain the actual code in order.",
            prompt,
        )

    def test_prompt_checks_java_declared_reference_type(self):
        prompt = main.build_conversation_prompt(
            "Explain this Java example."
        )

        self.assertIn(
            "A variable's declared type determines which methods can be called directly.",
            prompt,
        )
        self.assertIn(
            "Do not call `myCar.honk()` through a Vehicle reference",
            prompt,
        )

    def test_prompt_preserves_recent_code_context(self):
        main.SESSION_CONVERSATION_HISTORY.append(
            (
                "Give me an example using vehicles.",
                "class Vehicle { void move() {} } "
                "class Car extends Vehicle { void honk() {} }",
            )
        )

        prompt = main.build_conversation_prompt(
            "Summarize the most recent example in three sentences."
        )

        self.assertIn("Give me an example using vehicles.", prompt)
        self.assertIn("class Vehicle", prompt)
        self.assertIn("class Car extends Vehicle", prompt)
        self.assertIn(
            "Summarize the most recent example in three sentences.",
            prompt,
        )

    def test_prompt_preserves_exact_sentence_count_instruction(self):
        prompt = main.build_conversation_prompt(
            "Summarize the most recent example in three sentences."
        )

        self.assertIn(
            "If the user asks for exactly three sentences",
            prompt,
        )
        self.assertIn(
            "produce exactly three",
            prompt,
        )

    @patch("main.ask_local_ai")
    @patch("main.build_latest_java_code_facts")
    def test_summary_must_explain_actual_override(
        self, mock_facts, mock_ai
    ):
        mock_facts.return_value = (
            "Class Car extends Vehicle.\n"
            "Vehicle declares and defines these methods in its "
            "class body: move.\n"
            "Car declares and defines these methods in its "
            "class body: honk, move.\n"
            "Car overrides these parent methods: move.\n"
            "These methods are specific to Car and are not "
            "overrides of parent methods: honk."
        )

        # Simulate an AI response that omits the move() override.
        incomplete_response = (
            "The most recent Java example involves Car extending "
            "Vehicle. Vehicle declares and defines move(). "
            "Car declares and defines honk(), which is specific "
            "to Car and is not an override of a method declared "
            "by Vehicle."
        )

        # Simulate an AI correction that still omits the override.
        mock_ai.return_value = incomplete_response

        result = main.validate_programming_response(
            "Summarize the most recent Java inheritance example "
            "in three sentences.",
            incomplete_response,
            "Test prompt",
        )

        self.assertIn("overriding move()", result)
        self.assertIn("honk()", result)
        self.assertIn("not overrides", result)

    def test_vehicle_example_facts_distinguish_inheritance_from_overriding(self):
        main.SESSION_CONVERSATION_HISTORY.append(
            (
                "Give me another example using vehicles.",
                '''Here is the example:

```java
class Vehicle {
    void move() {
        System.out.println("Moving");
    }

    void refuel() {
        System.out.println("Refueling");
    }
}

class Car extends Vehicle {
    void honk() {
        System.out.println("Honking");
    }
}

public class Main {
    public static void main(String[] args) {
        Car myCar = new Car();
        myCar.move();
        myCar.refuel();
        myCar.honk();
    }
}
```''',
            )
        )

        facts = main.build_latest_java_code_facts()

        self.assertIn("Class Car extends Vehicle.", facts)
        self.assertIn("Car overrides no methods declared in Vehicle.", facts)
        self.assertIn(
            "inherited without being overridden",
            facts,
        )
        self.assertIn("move", facts)
        self.assertIn("refuel", facts)
        self.assertIn(
            "specific to Car and are not overrides",
            facts,
        )
        self.assertIn("honk", facts)

    def test_prompt_distinguishes_declared_methods_from_inherited_methods(self):
        prompt = main.build_conversation_prompt(
            "Summarize the most recent Java inheritance example."
        )

        self.assertIn(
            "The superclass declares methods that it defines in its own class body.",
            prompt,
        )
        self.assertIn(
            "The subclass inherits accessible superclass methods unless it overrides them.",
            prompt,
        )
        self.assertIn(
            "Do not say that both the superclass and subclass inherit a method",
            prompt,
        )
        self.assertIn(
            "When summarizing inheritance, explicitly identify which class declares each method",
            prompt,
        )


if __name__ == "__main__":
    unittest.main()

# Test Design Strategies

This document outlines key design principles and strategies for writing effective, maintainable, and robust tests within this project. Adhering to these guidelines helps ensure the quality and stability of our codebase.

---

## 1. The Test Pyramid

The Test Pyramid is a metaphorical guide for structuring a test suite, emphasizing the allocation of testing effort at different levels:

*   **Unit Tests (Base of the Pyramid):** These are the most numerous. They are small, fast, and isolated tests that verify individual functions, methods, or classes in isolation.
*   **Integration Tests (Middle Layer):** Fewer than unit tests. These verify that different components or services work correctly together.
*   **End-to-End (E2E) Tests (Apex of the Pyramid):** The least numerous. These simulate real user scenarios, covering the entire application stack.

**Strategy:** Prioritize unit tests for speed and precision, use integration tests for architectural choreography, and use minimal E2E tests for essential user flows.

---

## 2. Solitary vs. Sociable Tests (Integration Standard)

In this project, we distinguish between two styles of testing to manage complexity and failure "blast radius":

*   **Solitary Tests (Unit):** Isolate the System Under Test (SUT) completely. Replace all dependencies with Test Doubles.
    *   **Mandate:** Unit tests MUST mock the `EventAggregator` to verify intent without triggering side effects in other components.
*   **Sociable Tests (Integration):** Allow the SUT to interact with its real collaborators.
    *   **Mandate:** Integration tests SHOULD use real instances of the `ApplicationModel`, `CommandManager`, and `EventAggregator` to verify the "Contract" and "Choreography" between layers.

---

## 3. The "Layered Stack" Harness

To avoid boilerplate and ensure test isolation, integration tests utilize a hierarchy of fixtures called **Stacks**.

*   **CoreStack:** The bare minimum for state and communication (`EA`, `Model`, `Config`).
*   **TransactionalStack:** Extends the Core with undo/redo capability (`CommandManager`).
*   **Domain Stacks:** Specialized stacks for specific logic units (e.g., `NodeStack`, `LayoutStack`, `ProjectStack`).

**Guideline:** Tests should always request the *minimum viable stack* required for the scenario.

---

## 4. Test Doubles: Mocking, Stubbing, and Spying

Replace complex dependencies with controlled substitutes to ensure isolation and repeatability.

*   **Mock:** Records calls made to it, allowing assertions about how the dependency was used. (Primary use: Unit Tests).
*   **Stub:** Provides canned answers to calls made during the test. (Primary use: Unit Tests).
*   **Spy (Advanced):** Wraps a real object and records interactions while allowing its real logic to execute.
    *   **Mandate (Integration):** In our integration harness, the `EventAggregator.publish` method is automatically wrapped in a Spy. This allows us to assert communication while ensuring that other services (like the `LayoutManager`) still receive the event and perform their real math.

---

## 5. Deterministic Baselines & Stress Testing

To manage the trade-off between predictable debugging and comprehensive coverage, we use **Indirect Parametrization**.

*   **Standard Tests:** Rely on the `DEFAULT_FIG_SIZE` (20x15cm) baseline defined in `conftest.py`. This ensures a deterministic "Starting Line" for all general logic tests.
*   **Stress Tests:** Use `@pytest.mark.parametrize("integration_config", [...], indirect=True)` to inject extreme or "weird" configurations (e.g., 1000cm margins, tiny figures) into the entire stack.

---

## 6. FIRST Principles of Unit Testing

These principles guide the creation of high-quality unit tests:

*   **F**ast: Tests should run quickly to encourage developers to execute them frequently.
*   **I**solated/Independent: Each test should be self-contained and not rely on the execution order or side effects of other tests.
*   **R**epeatable: Tests should produce the same results every time they are run, regardless of the environment or external factors.
*   **S**elf-validating: Tests should have a clear, automated pass/fail outcome without requiring manual inspection.
*   **T**horough: Tests should cover enough of the code's behavior (including edge cases and error paths) to provide confidence in its correctness.

---

## 7. Arrange-Act-Assert (AAA) Pattern

This is a common and highly recommended pattern for structuring individual test cases:

*   **Arrange (Given):** Set up the test environment, initialize objects, prepare input data, and mock any necessary dependencies.
*   **Act (When):** Execute the specific action, function, or method being tested.
*   **Assert (Then):** Verify that the outcome of the action is as expected. This includes checking return values, state changes, interactions with mocked objects, or exceptions raised.

**Strategy:** Every test method should clearly delineate these three sections for improved readability and focus.

---

## 8. Readability and Maintainability

**Strategy:** Treat your test code with the same care as your production code:

*   **Descriptive Naming:** Clear and concise (e.g., `test_node_deletion_is_undoable`).
*   **Focused Tests:** Verify a single, specific aspect of behavior.
*   **DRY (Don't Repeat Yourself):** Utilize `pytest` fixtures and the Stack hierarchy.
*   **Global Imports:** Use global imports at the top of the test file to ensure consistency and facilitate static analysis.
*   **Refactor Tests:** Regularly refactor your tests to keep them clean and efficient.

---

## 9. Edge Cases and Error Handling

**Strategy:** Beyond the typical "happy path" scenarios, dedicate tests to cover:

*   **Invalid Inputs:** What happens when functions receive unexpected or malformed data?
*   **Boundary Conditions:** Test with minimum and maximum valid values, as well as values just outside the valid range.
*   **Error Conditions:** Verify that the system handles errors gracefully (e.g., network outages, file not found, permission denied, expected exceptions).
*   **Concurrency/Race Conditions:** If applicable, design tests that expose potential issues in multi-threaded or asynchronous environments.
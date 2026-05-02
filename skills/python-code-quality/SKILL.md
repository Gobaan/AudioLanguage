---
name: python-code-quality
description: "Guide Python implementation, refactoring, debugging, and review using Python best practices, the Zen of Python, PEP 8-style readability, modern typing, efficient idioms, clear errors, tests, packaging hygiene, async correctness, and maintainable API design. Use when Codex writes or reviews Python files, FastAPI apps, scripts, tests, models, services, CLIs, data processing code, or performance-sensitive Python."
---

# Python Code Quality

## Purpose

Use this skill to write Python that is clear, idiomatic, efficient enough for the problem, and easy to maintain. Prefer the project's existing Python version, formatter, linter, type checker, test framework, and local conventions over generic preferences.

Ground decisions in Python's core values: readability, explicitness, simplicity, namespaces, practical correctness, and maintainability.

## Core Rule

Optimize Python code for human understanding first, then measured performance.

Before coding, identify:

- The Python version and dependency constraints.
- The local style, typing, and test conventions.
- The data shape and invariants.
- The expected failure modes.
- Whether the code is request/response, script, library, async, CPU-bound, or IO-bound.
- The cheapest test or check that proves the behavior.

Do not add abstraction, cleverness, or micro-optimization unless it makes the code easier to change or solves a demonstrated cost.

## Zen-Guided Style

Apply these principles directly while coding:

- Beautiful is better than ugly: choose structure and names that make intent visible.
- Explicit is better than implicit: make inputs, outputs, errors, and side effects clear.
- Simple is better than complex: use the simplest construct that expresses the idea.
- Complex is better than complicated: when complexity is real, isolate it and name it.
- Flat is better than nested: reduce nesting with guard clauses, helpers, and clear branches.
- Sparse is better than dense: avoid compressed one-liners that hide behavior.
- Readability counts: choose maintainability over clever tricks.
- Errors should not pass silently: catch only what you can handle, and preserve context.
- Namespaces are a great idea: organize modules, classes, and functions around ownership.
- There should be one obvious way: follow project conventions and standard library idioms.
- Now is better than never: make useful progress, but do not rush into unclear designs.

## Project Conventions First

Before changing Python code:

- Look for `pyproject.toml`, `setup.cfg`, `ruff.toml`, `mypy.ini`, `pytest.ini`, `tox.ini`, or CI config.
- Use the existing formatter/linter if present.
- Match local import style, type annotation density, dependency injection style, and test patterns.
- Do not introduce a new library when the standard library or existing dependencies are enough.
- Keep compatibility with the project's supported Python version.

When no convention exists, prefer modern, standard Python with type hints on public boundaries.

## Naming

Use names that reveal domain meaning.

- Modules and functions: `snake_case`.
- Classes and exceptions: `CapWords`.
- Constants: `UPPER_SNAKE_CASE`.
- Private helpers: leading underscore only when the boundary matters.
- Boolean names: prefer `is_`, `has_`, `can_`, `should_` when readable.
- Avoid vague names: `data`, `obj`, `manager`, `handler`, `result` unless the scope is tiny or the role is obvious.

Prefer a slightly longer precise name over a short ambiguous one.

## Functions

Design functions around one coherent responsibility.

A good function has:

- A name that says what it does.
- Parameters that are explicit and minimal.
- Few side effects, or side effects visible from the name and location.
- A return type that callers can reason about.
- Errors that match the abstraction level.

Use guard clauses to avoid deep nesting. Extract helpers when they name a meaningful subtask, not just to shorten a file.

## Modules

Keep modules cohesive.

- Put public API near the top when useful.
- Keep low-level helpers private or near their use.
- Avoid utility modules that collect unrelated functions.
- Separate domain logic from IO, framework glue, and serialization when practical.
- Avoid import-time side effects beyond constants and lightweight definitions.

If importing a module performs work, starts services, reads files, or touches the network, reconsider the boundary.

## Imports

Make dependencies obvious.

- Put imports at the top unless delayed import is needed to avoid optional dependency cost, cycles, or startup time.
- Prefer absolute imports inside packages unless local convention says otherwise.
- Avoid wildcard imports outside intentional package APIs.
- Group standard library, third-party, and local imports according to formatter/linter convention.
- Remove unused imports rather than leaving them as hints.

Delayed imports should have a reason visible from context.

## Types

Use type hints to clarify contracts, especially at boundaries.

Prioritize annotations for:

- Public functions and methods.
- Data models and return values.
- Functions with `None`, unions, callbacks, or containers.
- Cross-module APIs.
- Complex dictionaries or parsed external data.

Prefer precise built-in generics: `list[str]`, `dict[str, int]`, `tuple[int, ...]`. Use `Mapping`, `Sequence`, or `Iterable` when callers should not need a concrete mutable type.

Use `Protocol` for structural interfaces when behavior matters more than inheritance. Use `TypedDict`, dataclasses, or Pydantic models when dictionary shape matters.

Avoid `Any` unless crossing an untyped boundary; contain it and convert to typed data quickly.

## Data Modeling

Choose the lightest data model that enforces the needed contract.

- Plain dict: small local transformations with obvious keys.
- `dataclass`: internal structured data with lightweight behavior or defaults.
- `NamedTuple` or tuple: small immutable positional data, when positions are genuinely clear.
- `Enum`: named finite choices.
- Pydantic model: external input/output validation, API schemas, settings, or boundary parsing.
- Full class: identity, invariants, behavior, lifecycle, or encapsulation.

Do not pass raw dictionaries deep into domain code when a stable shape matters.

## Exceptions And Errors

Handle errors at the right level.

- Catch specific exceptions.
- Keep `try` blocks narrow.
- Use `raise ... from exc` when translating errors and preserving cause matters.
- Do not catch and ignore exceptions unless silence is the explicit, tested behavior.
- Return `None` or sentinel values only when absence is an expected domain result.
- Use custom exceptions when callers need to distinguish domain failures.
- Avoid leaking secrets in exception messages and logs.

For APIs, translate internal exceptions into clear response errors at the boundary.

## Context Managers And Resources

Use context managers for resources with lifetimes.

- Files, locks, temporary directories, database sessions, network clients, spans, and patches should close or release reliably.
- Prefer `with` and `async with` over manual open/close pairs.
- Keep resource ownership obvious: the creator usually closes it.
- Avoid returning objects tied to closed resources.

## Iteration And Collections

Use Python's collection idioms, but keep them readable.

- Prefer comprehensions for simple mapping/filtering.
- Use ordinary loops when there are multiple branches, side effects, or named intermediate steps.
- Use `enumerate`, `zip`, `any`, `all`, `sum`, `min`, `max`, and `sorted` when they express intent.
- Use `collections.Counter`, `defaultdict`, `deque`, `ChainMap`, or `dataclasses` when they simplify real logic.
- Avoid mutating a collection while iterating over it unless deliberately iterating over a copy.

Readable loops beat dense comprehensions.

## Strings And Paths

Use modern standard tools.

- Prefer f-strings for interpolation.
- Use `pathlib.Path` for filesystem paths.
- Specify encodings for text file IO when files cross environments.
- Avoid manual path joins with string concatenation.
- Use `json`, `csv`, `tomllib`, `configparser`, or structured parsers instead of ad hoc parsing.

## Async Python

Async code should make waiting and cancellation explicit.

- Await coroutines that must complete.
- Use `asyncio.gather`, task groups, or framework primitives according to the project's Python version and conventions.
- Do not block the event loop with CPU work, synchronous file/network calls, or long loops.
- Use timeouts around remote operations.
- Propagate cancellation unless cleanup must be shielded intentionally.
- Track background tasks or put durable work in a queue.
- Avoid shared mutable state across tasks unless protected or confined.

For FastAPI or async web code, keep CPU-heavy work out of request handlers unless explicitly delegated.

## Performance

Prefer algorithmic clarity before micro-optimization.

Performance checklist:

- Choose the right data structure: set/dict for membership and lookup, list for ordered sequences, deque for queue ends.
- Avoid repeated expensive work inside loops.
- Stream large files or responses instead of loading everything when size can grow.
- Use generators for pipelines when laziness helps readability or memory.
- Avoid unnecessary intermediate lists; but do not make code obscure just to be lazy.
- Push heavy numeric work to optimized libraries when appropriate.
- Measure before changing clear code into clever code.

The fastest Python is often the Python that does less work.

## Testing

Test behavior and edge cases.

- Unit-test pure logic and data transformations.
- Integration-test framework boundaries, database behavior, filesystem IO, and external adapters.
- Regression-test bugs that could return.
- Use fixtures to make setup clear, not magical.
- Use parametrized tests for input/output matrices.
- Mock at boundaries, not every internal helper.
- Assert meaningful outcomes, not implementation choreography.

Keep tests readable enough to serve as examples.

## Documentation And Comments

Use comments to explain why, not what.

- Add docstrings for public modules, classes, functions, and non-obvious behavior.
- Keep docstrings accurate and concise.
- Prefer clear names and structure over explanatory comments.
- Comment surprising tradeoffs, external constraints, performance reasons, or protocol quirks.
- Delete stale comments when changing code.

## Security And Robustness

Be careful at boundaries.

- Validate external input.
- Avoid `eval` and unsafe deserialization.
- Use parameterized SQL or ORM query APIs.
- Do not log secrets, credentials, tokens, or sensitive payloads.
- Use secure temporary files and avoid predictable names.
- Treat paths from users as untrusted.
- Set timeouts for network calls.

## Refactoring Python

Refactor in small behavior-preserving steps.

1. Add or identify a focused test/check.
2. Improve names first when confusion is semantic.
3. Extract functions around meaningful concepts.
4. Replace duplicated knowledge with one source of truth.
5. Move framework/IO code away from pure domain logic when it improves testability.
6. Tighten types and errors at boundaries.
7. Run formatter, linter, type checker, or tests that the project supports.

Do not turn simple procedural code into classes unless ownership, invariants, or lifecycle justify it.

## Review Checklist

When reviewing Python code, check:

- Does the code follow local conventions and supported Python version?
- Are names precise and domain-oriented?
- Are functions cohesive with clear inputs, outputs, and side effects?
- Are types helpful at boundaries without adding noise?
- Are errors specific, preserved, and safe?
- Are resources closed reliably?
- Is async code non-blocking and cancellation-aware?
- Are data structures appropriate for the access pattern?
- Is performance improved by doing less work rather than cleverness?
- Do tests cover behavior, edge cases, and likely regressions?

## Common Pushbacks

Push back on:

- Clever one-liners that hide branching or errors.
- Broad `except Exception` blocks that mask bugs.
- Mutable defaults such as `[]` or `{}` in function arguments.
- Import-time work with side effects.
- Raw dictionaries passed through many layers without a clear schema.
- Unbounded memory use for data that can grow.
- Blocking calls inside async handlers.
- New dependencies for standard-library-sized problems.
- Premature classes, factories, or inheritance.
- Tests that only assert mocks were called.

## Output Style

When giving Python guidance:

- State the readability or correctness issue first.
- Prefer idiomatic standard-library solutions.
- Mention typing, error handling, async, and performance implications when relevant.
- For implementation tasks, edit the code and verify with focused checks.
- In final responses, report what changed, what was verified, and any remaining risk.
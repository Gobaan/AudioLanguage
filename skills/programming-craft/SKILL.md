---
name: programming-craft
description: "Enforce a pragmatic coding style while implementing, refactoring, reviewing, or debugging code. Use when Codex should write maintainable production code guided by explicit Pragmatic Programmer style rules: DRY, orthogonality, tracer bullets, design by contract, reversibility, plain text/data transparency, automation, testing, refactoring, defensive error handling, and avoiding broken-window code."
---

# Programming Craft

## Purpose

Use this skill to keep coding work pragmatic, direct, and maintainable. Apply these rules while writing code, reviewing changes, refactoring, debugging, or choosing an implementation approach.

This is not a request to reproduce any book. Treat the rules below as a practical coding style inspired by well-known pragmatic programming principles.

## Core Rule

Optimize for code that is easy to change safely.

Every implementation choice should serve at least one of these goals:

- Make the behavior easier to understand.
- Make mistakes harder to introduce.
- Make change cheaper later.
- Make failures easier to detect and diagnose.
- Make the system less coupled to accidental details.

If a choice does none of these, simplify it.

## Rule 1: Care About Your Craft

Write code as if another capable engineer will maintain it under time pressure.

- Choose names that reveal intent.
- Keep functions focused on one level of abstraction.
- Prefer boring, readable code over clever code.
- Leave nearby code a little clearer when the task naturally touches it.
- Do not normalize sloppy code by copying it without thought.

## Rule 2: Do Not Live With Broken Windows

Treat visible decay as a risk multiplier.

- Fix small issues near the changed code when they are low-risk and relevant.
- Do not add new TODOs without a concrete reason or owner/context.
- Do not silence warnings, exceptions, or failing tests to make progress look clean.
- If a larger issue is out of scope, name it in the final response instead of burying it.

## Rule 3: DRY Means One Source Of Truth

Avoid duplicated knowledge, not merely duplicated text.

- Centralize rules, constants, schemas, parsing, validation, and policy decisions.
- Allow repeated code when unifying it would create tighter coupling or a worse abstraction.
- When removing duplication, name the shared concept, not the incidental mechanics.
- Watch for duplicated assumptions across frontend/backend, tests/implementation, docs/code, and migrations/models.

Before extracting an abstraction, ask: "What knowledge is duplicated here?" If the answer is unclear, wait.

## Rule 4: Keep Code Orthogonal

Design modules so changes in one area do not force unrelated changes elsewhere.

- Keep IO, business rules, formatting, persistence, and presentation separated when practical.
- Hide third-party APIs behind local boundaries if they would otherwise leak everywhere.
- Pass explicit inputs instead of reaching into globals or ambient state.
- Prefer small interfaces with clear ownership over shared objects that everyone mutates.
- Avoid temporal coupling: make required call order obvious or encode it in the API.

Orthogonal code is easier to test because each part can be exercised independently.

## Rule 5: Use Tracer Bullets For Uncertain Work

When the path is unclear, build a thin working slice before polishing the whole system.

A tracer-bullet implementation should:

- Exercise the real architecture path end to end.
- Use real integration points where feasible.
- Be small enough to replace or harden.
- Reveal unknowns about data, latency, errors, permissions, and user flow.

Do not confuse a disposable prototype with production code. If prototype code remains, harden names, errors, tests, and boundaries before calling it done.

## Rule 6: Make Decisions Reversible

Avoid irreversible commitments unless the task truly requires them.

- Prefer configuration, local adapters, and narrow interfaces around volatile choices.
- Delay broad abstractions until the code has shown where variation really exists.
- Keep migrations, data transformations, and public API changes backward-compatible when possible.
- Document or report irreversible tradeoffs clearly.

Good design keeps options open without building imaginary futures.

## Rule 7: Program Close To The Problem Domain

Let code speak in domain concepts instead of implementation trivia.

- Use domain names for important types, functions, events, and errors.
- Represent meaningful states explicitly rather than with booleans and magic strings.
- Put domain rules near the domain model or service that owns them.
- Translate external formats at boundaries, then use internal types consistently.

If the code reads like the user problem, it is usually easier to change correctly.

## Rule 8: Design By Contract

Make expectations explicit.

For important functions and boundaries, identify:

- Preconditions: what must be true before calling.
- Postconditions: what will be true after success.
- Invariants: what must always remain true.
- Failure modes: what happens when expectations are not met.

Express contracts with types, validation, assertions, narrow APIs, tests, and clear errors. Do not rely on comments alone for critical contracts.

## Rule 9: Crash Early For Programmer Errors

Do not let impossible states drift through the system.

- Validate external input at the edge.
- Fail fast on violated invariants.
- Return recoverable domain errors for expected user or environment failures.
- Preserve error cause and context without leaking secrets.
- Avoid broad catch-and-ignore blocks.

A loud, local failure is usually cheaper than a quiet, distant one.

## Rule 10: Use Plain Text And Transparent Data

Prefer inspectable formats and simple data flow where they fit.

- Use readable config, logs, fixtures, snapshots, and migration artifacts.
- Keep serialization/deserialization explicit at boundaries.
- Avoid opaque encodings unless required for performance, compatibility, or security.
- Make logs and errors useful enough to diagnose production failures.

Transparency is a debugging feature.

## Rule 11: Automate Repetition

If a task must be done the same way repeatedly, automate it or encode it in tooling.

- Use formatters, linters, tests, migrations, generators, scripts, and CI checks where the repo already supports them.
- Prefer deterministic commands over manual sequences.
- Keep generated code clearly separated or marked when the project has that convention.
- Do not add heavyweight tooling for a one-off task.

Automation should reduce human memory load, not add ceremony.

## Rule 12: Test The Risk

Write tests that target the bug, invariant, or behavior most likely to break.

- Unit-test pure rules and edge cases.
- Integration-test boundaries, persistence, serialization, auth, and external contracts.
- Regression-test bugs that could plausibly return.
- Use property or table tests for combinatorial rules.
- Keep tests deterministic and readable.

Do not test implementation details just to raise coverage. Tests are design feedback, not decoration.

## Rule 13: Refactor Continuously, In Small Steps

Refactor to make the next change easier.

- Separate behavior changes from mechanical cleanup when risk is non-trivial.
- Rename before extracting when names are the source of confusion.
- Extract only after the repeated concept is clear.
- Preserve public contracts unless migration is part of the task.
- Run focused verification after each meaningful step.

Refactoring is successful when the code becomes simpler to reason about, not merely more abstract.

## Rule 14: Avoid Programming By Coincidence

Understand why the code works.

- Do not rely on ordering, timing, default values, retries, or side effects you have not verified.
- Read the called code or documentation when behavior matters.
- Add tests around surprising behavior before depending on it.
- Replace accidental behavior with explicit contracts.

If the explanation is "it seems to work," keep digging.

## Rule 15: Concurrency Requires Ownership

For concurrent or async code, define ownership before implementation.

- Identify shared mutable state and who may change it.
- Prefer immutability, confinement, queues, transactions, or message passing before locks.
- If locks are needed, keep critical sections small and define ordering.
- Handle cancellation, timeout, retry, backpressure, and shutdown intentionally.
- Make retryable operations idempotent.
- Test race-prone code with stress loops, fake clocks, race detectors, or controlled schedulers when available.

Concurrency bugs usually come from unclear ownership, hidden shared state, or forgotten lifecycle paths.

## Rule 16: Keep Knowledge Near Its Use

Place code where future maintainers will search first.

- Keep feature-specific logic inside the feature boundary.
- Move shared logic only when multiple callers truly share the same concept.
- Keep tests close to the behavior they verify, following repo convention.
- Avoid utility modules that collect unrelated leftovers.

A bad location is a hidden cost on every future change.

## Rule 17: Prefer Composability Over Inheritance

Use inheritance only when the relationship is stable and genuinely substitutable.

- Prefer functions, small objects, strategies, composition, or data-driven dispatch.
- Use interfaces/protocols to express required behavior without forcing hierarchy.
- Avoid base classes that know too much about subclasses.
- Keep extension points narrow and tested.

Composition tends to make change local; inheritance often makes change contagious.

## Rule 18: Estimate By Splitting Risk

When planning, split work by uncertainty rather than by neat-looking layers.

- Identify unknowns first: data shape, integration behavior, performance, permissions, migration risk, UX ambiguity.
- Build the riskiest thin slice early.
- Keep milestones demonstrable.
- Re-estimate after learning, not after wishful thinking.

A good plan reduces uncertainty as fast as possible.

## Coding Checklist

Before finalizing code, check:

- Does this change have one clear source of truth for each rule or policy?
- Are boundaries explicit and local conventions preserved?
- Are names domain-centered and intention-revealing?
- Are invalid states prevented, validated, or failed fast?
- Are errors useful, contextual, and safe?
- Are concurrency ownership and lifecycle paths clear?
- Does the test coverage match the risk?
- Did I avoid speculative abstractions?
- Can a maintainer understand why this approach was chosen?

## Review Style

When reviewing code, lead with concrete risk.

Use findings like:

- Correctness: behavior is wrong or incomplete.
- Contract: caller/callee expectations are unclear or unenforced.
- Coupling: change leaks across boundaries.
- DRY: duplicated knowledge can drift.
- Orthogonality: unrelated concerns are mixed.
- Error handling: failures are hidden, lossy, or unsafe.
- Concurrency: ownership, cancellation, or shared state is unsafe.
- Tests: likely regressions are not covered.

Avoid vague taste comments. Tie feedback to maintainability, correctness, safety, or change cost.

## Final Response Habit

When reporting completed coding work, include:

- What changed.
- What was verified.
- Any important pragmatic tradeoff or residual risk.

Keep it short unless the user asks for detail.

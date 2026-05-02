---
name: architecture-patterns
description: "Guide software architecture, module design, and architecture review using design-pattern vocabulary and tradeoff analysis. Use when Codex is asked to design a system, choose boundaries, introduce or remove abstractions, review architecture, refactor toward clearer structure, or select patterns such as Strategy, Adapter, Factory, Observer, Command, Decorator, State, Composite, Facade, Proxy, Template Method, Iterator, Mediator, Builder, or Abstract Factory."
---

# Architecture Patterns

## Purpose

Use this skill to make architectural choices explicit, pattern-aware, and proportional to the problem. Treat classic design patterns as a vocabulary for recurring design forces, not as templates to force onto code.

Do not reproduce copyrighted book text. Use pattern names, common intents, tradeoffs, and practical application guidance.

## Architecture Stance

Start from forces, not patterns.

Before proposing architecture, identify:

- The behavior that must vary.
- The parts that must remain stable.
- The ownership boundary for data and decisions.
- The expected rate of change.
- The failure modes and operational constraints.
- The cost of coupling, indirection, and migration.
- The simplest design that can satisfy the known constraints.

Prefer plain modules, functions, and data structures until a pattern clearly reduces coupling, clarifies ownership, or protects a volatile boundary.

## Decision Loop

Use this loop for architecture work:

1. Name the architectural problem in one sentence.
2. List the forces: volatility, coupling, lifecycle, performance, concurrency, testability, deployment, team ownership, and compatibility.
3. Identify the stable abstractions and volatile implementations.
4. Choose the least powerful pattern or boundary that addresses the forces.
5. Sketch how data and control flow through the design.
6. Check failure, cancellation, retry, and observability paths.
7. Define tests or probes that prove the architecture works.
8. Call out tradeoffs and future migration paths.

## Pattern Selection Rules

Use a pattern when it improves one of these:

- Substitutability: one behavior can be swapped for another safely.
- Boundary protection: external or unstable details stop leaking inward.
- Lifecycle control: construction, initialization, teardown, or ownership is centralized.
- Communication control: senders and receivers are decoupled intentionally.
- Composition: small behaviors can be combined without inheritance tangles.
- State clarity: valid states and transitions become explicit.
- Testability: dependencies and policies become easier to isolate.

Avoid a pattern when it mainly adds names, files, interfaces, or indirection without reducing real risk.

## Creational Patterns

Use creational patterns when object construction has policy, variation, sequencing, or dependency concerns.

### Factory Method

Use when a type delegates creation of a related object to subclasses or configured implementations.

Good fit:

- Construction varies by environment, plugin, provider, or runtime type.
- Callers should depend on an interface, not concrete classes.

Watch for:

- Factories that only wrap `new` without adding policy.
- Hidden dependency graphs that make testing harder.

### Abstract Factory

Use when families of related objects must be created together and remain compatible.

Good fit:

- UI toolkit families, storage/provider families, protocol-specific components.
- Tests need a complete fake family matching production contracts.

Watch for:

- Too many tiny factory interfaces before families are real.

### Builder

Use when construction has many optional parts, validation steps, or order constraints.

Good fit:

- Complex configuration, query construction, documents, immutable objects.
- Need readable setup in tests.

Watch for:

- Builders for simple data objects.
- Invalid intermediate states leaking out.

### Prototype

Use when creating new instances by cloning configured examples is clearer than rebuilding from scratch.

Good fit:

- Expensive setup, templates, runtime-configured objects.

Watch for:

- Shared mutable state accidentally copied by reference.

### Singleton

Treat as a last resort. Prefer dependency injection, module-level composition roots, or explicit lifecycle management.

Use only when:

- There must truly be one process-wide instance.
- Lifecycle, concurrency, and test isolation are handled deliberately.

Watch for:

- Hidden global state, test pollution, ordering bugs, and hard-to-replace dependencies.

## Structural Patterns

Use structural patterns to shape relationships between objects, modules, or APIs.

### Adapter

Use when an external or incompatible API should fit a local interface.

Good fit:

- Third-party services, legacy modules, platform APIs, data format differences.

Watch for:

- Leaking external types beyond the adapter boundary.
- Adapters that become dumping grounds for business rules.

### Facade

Use when a subsystem needs a simpler, stable entry point.

Good fit:

- Complex internal workflows, multiple low-level services, migration boundaries.

Watch for:

- Facades that hide too much and become god services.

### Decorator

Use when behavior should be layered around an object without changing its core type.

Good fit:

- Logging, caching, retry, authorization, metrics, validation, compression.

Watch for:

- Order-dependent decorator stacks with unclear semantics.
- Decorators that mutate core behavior unexpectedly.

### Composite

Use when individual objects and groups should be treated uniformly.

Good fit:

- Trees, UI elements, rule groups, file/folder structures, expression nodes.

Watch for:

- Forcing uniform operations where leaves and containers have genuinely different contracts.

### Proxy

Use when access to another object needs control.

Good fit:

- Lazy loading, remote calls, caching, authorization, resource protection.

Watch for:

- Hiding network, latency, permission, or failure semantics behind a local-looking call.

### Bridge

Use when abstraction and implementation should vary independently.

Good fit:

- Multiple dimensions of variation, such as shape/rendering or domain operation/provider.

Watch for:

- Premature splitting before two axes of variation are proven.

### Flyweight

Use when many small objects can share immutable intrinsic state.

Good fit:

- Memory-sensitive rendering, parsing, symbols, glyphs, tiles.

Watch for:

- Shared mutable state and complexity that outweighs memory savings.

## Behavioral Patterns

Use behavioral patterns to clarify responsibility, control flow, state transitions, and communication.

### Strategy

Use when an algorithm or policy varies behind a stable interface.

Good fit:

- Pricing rules, ranking, validation, serialization, retry policy, auth policy.

Watch for:

- Strategy objects that are just one-line wrappers around functions unless the language or repo favors that shape.

### Template Method

Use when an algorithm skeleton is stable and subclasses fill specific steps.

Good fit:

- Framework hooks, import/export pipelines, common workflows with limited variation.

Watch for:

- Inheritance traps, hidden call order, and fragile base classes.

Prefer composition or Strategy when variation is likely to grow.

### Observer

Use when producers should notify unknown consumers.

Good fit:

- UI events, domain events, cache invalidation, plugin hooks.

Watch for:

- Ordering assumptions, reentrancy, memory leaks, delivery guarantees, and silent failure.

### Command

Use when actions need to be represented as objects or records.

Good fit:

- Queues, undo/redo, audit logs, retries, authorization, scheduling.

Watch for:

- Commands that capture too much mutable context.
- Missing idempotency for retries.

### State

Use when behavior changes by lifecycle state and transitions matter.

Good fit:

- Orders, sessions, jobs, workflows, connection lifecycles.

Watch for:

- State classes when a simple enum and transition table would be clearer.

### Chain Of Responsibility

Use when a request may be handled by one of several handlers in sequence.

Good fit:

- Middleware, validation pipelines, auth checks, fallback resolution.

Watch for:

- Debuggability, ordering bugs, and swallowed failures.

### Mediator

Use when many objects coordinate through tangled references.

Good fit:

- UI coordination, workflow orchestration, modules with many-to-many interaction.

Watch for:

- Mediators becoming centralized god objects.

### Iterator

Use when traversal should be separated from collection internals.

Good fit:

- Custom collections, paginated data, streaming sources, lazy traversal.

Watch for:

- Hidden IO or expensive work inside innocent-looking iteration.

### Visitor

Use when many operations must be performed over a stable object structure.

Good fit:

- ASTs, expression trees, document models.

Watch for:

- Painful evolution when new element types are frequent.

### Memento

Use when state snapshots are needed without exposing internals.

Good fit:

- Undo, checkpoints, speculative edits.

Watch for:

- Large memory cost, stale snapshots, and sensitive data capture.

### Interpreter

Use when a small language or grammar needs representation and evaluation.

Good fit:

- Rules, filters, expressions, simple DSLs.

Watch for:

- Hand-rolling parsers when a proven parser library is better.

## Boundary Patterns

Classic patterns often appear at architecture boundaries. Use these boundary shapes deliberately:

- Ports and adapters: keep domain code independent from infrastructure.
- Facade: expose a stable API over a complex subsystem.
- Anti-corruption layer: translate external models into local domain concepts.
- Composition root: centralize wiring and lifecycle at application startup.
- Domain events: decouple state changes from follow-up reactions.
- Repository or gateway: hide persistence or service access behind domain-oriented methods.

Do not create boundary layers that simply pass data through without policy, translation, or isolation value.

## Architecture Review Checklist

Review architecture with these questions:

- What changes often, and is it isolated?
- What must stay consistent, and who owns that invariant?
- Where do external APIs, schemas, and protocols stop leaking?
- Is data flow understandable without reading every implementation?
- Are lifecycle, cancellation, retry, and shutdown explicit?
- Are failures observable and recoverable where appropriate?
- Does the design support focused tests without excessive mocking?
- Are there unnecessary abstractions, factories, managers, or base classes?
- Would a new maintainer know where to add the next related feature?

## Anti-Patterns To Push Back On

- Pattern-first design: choosing a pattern before naming the forces.
- Manager/service sprawl: vague classes that own unrelated behavior.
- Leaky abstraction: callers must understand hidden implementation details.
- Accidental singleton: global state disguised as convenience.
- Boolean architecture: flags controlling many unrelated behavior paths.
- Framework capture: domain rules shaped around framework plumbing.
- Over-mocking: tests coupled to internal call choreography instead of behavior.
- Premature generality: extension points built before variation exists.

## Output Style

When giving architecture guidance:

- Name the recommended shape or pattern.
- Explain why it fits the forces.
- Include at least one rejected alternative when useful.
- Describe tradeoffs and migration path.
- Keep diagrams textual unless the user asks for a formal diagram.
- For implementation work, make changes in the codebase rather than only describing the design.
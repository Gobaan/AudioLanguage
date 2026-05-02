---
name: backend-concurrency-design
description: "Guide backend design, implementation, refactoring, and review for async execution, concurrency, atomicity, idempotency, retries, transactions, queues, workers, distributed systems, database consistency, race conditions, cancellation, timeouts, backpressure, and reliability. Use when Codex works on APIs, services, jobs, background workers, message consumers, schedulers, database updates, locking, optimistic concurrency, or failure-prone backend workflows."
---

# Backend Concurrency Design

## Purpose

Use this skill to design and review backend code that remains correct under concurrent requests, duplicate delivery, retries, partial failure, cancellation, and load.

Backend correctness is not just whether the happy path works. Always ask what happens when the same operation runs twice, two actors race, a dependency times out, a transaction partially succeeds, or a worker crashes between steps.

## Core Rule

Make ownership, atomicity, and failure behavior explicit.

Before coding, identify:

- The source of truth for each piece of state.
- The operation that must be atomic.
- The boundary where retries may happen.
- Whether the operation is safe to run twice.
- What happens if two requests or workers act on the same entity.
- What happens on timeout, cancellation, crash, and restart.
- How failures are observed, recovered, or retried.

If these are unclear, fix the design before adding more async code.

## Backend State Categories

Classify state before designing concurrency controls.

- Request-local state: safe within one request or task.
- Process-local state: cache, singleton, in-memory queue, rate limiter; unsafe across processes unless explicitly coordinated.
- Database state: usually the source of truth; use constraints and transactions to protect invariants.
- Message state: events, commands, jobs; assume at-least-once delivery unless proven otherwise.
- External service state: remote and failure-prone; design for timeout, retry, and reconciliation.

Do not use process-local state as the only authority for cross-request or cross-worker decisions.

## Async Basics

Async code needs lifecycle discipline.

- Await tasks that must complete before returning.
- Track background tasks that outlive the request.
- Propagate cancellation when the caller no longer needs the work.
- Shield critical cleanup only when intentionally required.
- Put timeouts around network, database, lock, and queue operations.
- Avoid fire-and-forget unless there is a supervisor, retry path, or durable queue.
- Do not block an event loop with CPU work or synchronous IO.

Async is concurrency. Treat shared mutable state in async code with the same suspicion as threaded code.

## Concurrency Model

Name the concurrency model before implementation.

Common models:

- Single request transaction: one request owns the workflow until commit.
- Optimistic concurrency: detect conflicts with versions, timestamps, unique constraints, or compare-and-swap.
- Pessimistic locking: lock rows, resources, or distributed keys to serialize access.
- Queue serialization: route work for the same entity through one queue/partition/actor.
- Actor ownership: one actor owns mutable state and processes messages sequentially.
- Immutable/event log: append facts and derive state from them.

Choose the least complex model that protects the invariant.

## Atomicity

Define the smallest operation that must be all-or-nothing.

Use database transactions when:

- Multiple writes must preserve one invariant.
- A read-check-write sequence can race.
- Related rows must change together.
- A state transition must happen exactly once.

Use constraints when:

- Uniqueness, foreign keys, non-null values, and valid ranges can be enforced by the database.
- The database can reject invalid concurrent writes more reliably than application code.

Use compare-and-swap or version checks when:

- Updates should succeed only if the record has not changed.
- Users or workers may edit the same entity concurrently.

Avoid check-then-act without a transaction, lock, constraint, or version condition.

## Transactions

Keep transactions short, clear, and local to the invariant.

- Open the transaction as late as possible and commit as soon as the invariant is protected.
- Avoid network calls while holding a transaction open.
- Understand isolation level assumptions.
- Handle serialization failures and deadlocks as retryable when appropriate.
- Keep transaction boundaries visible in code.
- Do not hide transactions in helpers if callers need to reason about atomicity.

If a workflow spans the database and an external service, a single database transaction is not enough. Use idempotency, outbox, saga, reconciliation, or compensating action.

## Idempotency

Design retryable operations to be safe when repeated.

Use idempotency keys when:

- Clients may retry creates, payments, imports, sends, or state transitions.
- A timeout leaves the caller unsure whether the operation succeeded.

An idempotent operation should:

- Have a stable operation key.
- Store the result or final state for that key.
- Return the same meaningful response on duplicate attempts.
- Protect the key with a unique constraint or equivalent atomic guard.
- Avoid repeating irreversible side effects.

Idempotency is not just "ignore duplicates." It should preserve the intended result.

## Retries

Retries are only safe when the operation is idempotent or guarded.

For retries:

- Use bounded attempts.
- Use exponential backoff with jitter for remote dependencies.
- Classify errors as retryable or permanent.
- Respect cancellation and deadlines.
- Avoid retry storms and coordinated retries.
- Log enough context to diagnose repeated failures.

Never retry blindly around a non-idempotent side effect.

## Message Queues And Workers

Assume queues deliver at least once unless the project proves stronger guarantees.

Workers should handle:

- Duplicate messages.
- Out-of-order messages.
- Poison messages.
- Partial progress before crash.
- Visibility timeout expiry.
- Dead-letter or parking queues.
- Backpressure when downstream systems are slow.
- Graceful shutdown without losing in-flight work.

Acknowledge messages only after durable success, or after recording enough state to resume safely.

## Outbox Pattern

Use an outbox when a database change and message/event publish must stay consistent.

Good fit:

- Persist domain change and publish event.
- Create job after committing related data.
- Avoid losing events after a DB commit but before publish.

Shape:

1. Write domain data and outbox record in the same transaction.
2. A separate dispatcher reads unpublished outbox records.
3. Dispatcher publishes with retry.
4. Mark outbox record delivered or track attempts.
5. Consumers remain idempotent because publishes may duplicate.

Do not publish irreversible external messages from inside a transaction and assume it solves consistency.

## Sagas And Compensation

Use sagas when a workflow spans multiple services or resources without one atomic transaction.

- Store each step's durable state.
- Make each step idempotent.
- Define compensation for steps that can be undone.
- Define reconciliation for steps that cannot be undone.
- Expose workflow status for debugging and support.

Do not pretend distributed workflows are atomic. Make progress and recovery explicit.

## Locks

Use locks to protect a specific invariant, not as a general feeling of safety.

For local locks:

- Protect only process-local state.
- Keep critical sections small.
- Do not await or call unknown code while holding a lock unless the primitive and language make that safe and intentional.
- Define lock ordering when multiple locks exist.

For distributed locks:

- Prefer database constraints, transactions, or queue partitioning first.
- Use leases with expiration and fencing tokens when stale owners are dangerous.
- Design for lock loss, process pause, and retry.

A lock without a clear protected invariant is usually a design smell.

## Atomic Versus Basic Operations

Distinguish basic operations from atomic operations.

Basic operation:

- One line or one helper call that may still be unsafe under concurrency.
- Example: read a value, check a flag, append to a list, query for existing row, then insert later.

Atomic operation:

- The system guarantees no interleaving can violate the invariant.
- Example: database unique insert, transaction-protected state transition, compare-and-swap update, single queue partition owner, locked critical section.

When reviewing code, look for multi-step logic that needs to behave as one step.

## Race Conditions To Hunt

Check for:

- Lost update: two writers overwrite each other.
- Double create: two requests both see missing data and insert.
- Double spend: balance or quota checked before concurrent use.
- Double send: email, payment, notification, or webhook sent twice.
- Stale read: decision based on old state.
- Check-then-act: validation and write are not atomic.
- Time-of-check/time-of-use: permissions or resources change after check.
- Reordered events: older event overwrites newer state.
- Restart gap: crash after side effect but before recording success.

If one of these would hurt users or data, add a real guard.

## Cancellation And Timeouts

Every backend boundary should have a timeout or cancellation story.

- Propagate request cancellation to work that is no longer needed.
- Do not cancel critical cleanup halfway through unless safe.
- Use deadlines to bound total workflow time.
- Prefer explicit timeout errors over hanging tasks.
- Make long-running jobs resumable or checkpointed.
- On shutdown, stop accepting new work, finish or checkpoint in-flight work, and release resources.

Timeouts create uncertainty. Pair them with idempotency and reconciliation.

## Backpressure

When downstream systems slow down, the backend must degrade intentionally.

Options:

- Limit concurrency.
- Bound queues.
- Reject or shed load with clear errors.
- Apply rate limits.
- Use circuit breakers for failing dependencies.
- Pause consumers or reduce batch size.
- Prioritize critical work.

Unbounded queues and unlimited task creation turn latency into memory failure.

## Caching

Treat caches as derived state with consistency rules.

- Define TTL, invalidation, and stale behavior.
- Avoid using cache presence as authority for correctness.
- Protect cache stampedes with request coalescing or locks when needed.
- Include tenant/user/permission dimensions in cache keys.
- Do not cache secrets or authorization-sensitive data without clear boundaries.

The database or event log should usually remain the source of truth.

## External Side Effects

External calls are unreliable and often irreversible.

For payments, emails, webhooks, file writes, and third-party API mutations:

- Use idempotency keys when the provider supports them.
- Store intent before the call when recovery matters.
- Store result after the call when duplicates matter.
- Reconcile uncertain outcomes.
- Avoid holding DB transactions open during slow external calls.
- Make duplicate sends harmless or detectable.

If you cannot know whether the side effect happened after a timeout, design an inquiry or reconciliation path.

## Observability

Concurrency and retry bugs need evidence.

Log or trace:

- Correlation/request/job IDs.
- Idempotency keys.
- Entity IDs and state transitions.
- Retry attempt and retry reason.
- Lock wait time and timeout.
- Queue message ID, delivery count, and ack/nack decision.
- Transaction conflict, deadlock, or serialization failure.

Do not log secrets, tokens, raw credentials, or sensitive payloads.

## Testing Strategy

Test the failure mode, not just the function.

Use:

- Unit tests for pure state transition rules.
- Transaction/integration tests for constraints and conflict behavior.
- Duplicate-delivery tests for consumers and idempotency.
- Concurrent request tests for race-prone workflows.
- Fake clocks for timeout, lease, and retry behavior.
- Stress or repeated tests when races are likely.
- Contract tests around external service adapters.

A test that runs the same operation twice is often the cheapest reliability test.

## Review Checklist

When reviewing backend async or concurrent code, ask:

- What is the source of truth?
- What invariant must never be violated?
- Is the invariant protected atomically?
- What happens if two callers run this at once?
- What happens if this message is delivered twice?
- What happens if this times out after the side effect succeeds?
- Are retries bounded, classified, and safe?
- Are cancellation and shutdown handled?
- Is process-local state being mistaken for global truth?
- Are database constraints doing enough work?
- Is failure observable with IDs and state transitions?
- Do tests cover duplicate, concurrent, and partial-failure cases?

## Common Pushbacks

Push back on:

- Check-then-insert without a unique constraint or transaction.
- Fire-and-forget background work without supervision or durable state.
- Retrying non-idempotent operations.
- Queue consumers that assume exactly-once delivery.
- Locks used without a named invariant.
- Long transactions around network calls.
- In-memory coordination in multi-process deployments.
- Catch-and-log errors that mark work as successful.
- Missing timeout around remote dependencies.
- Unbounded task creation or queues.

## Output Style

When giving backend concurrency guidance:

- Name the invariant and source of truth first.
- State the recommended concurrency model.
- Explain the atomic guard: transaction, constraint, lock, version check, queue partition, or idempotency key.
- Describe retry, timeout, cancellation, and crash behavior.
- Mention observability and tests for the risky paths.
- For implementation tasks, make the code change rather than only giving advice.
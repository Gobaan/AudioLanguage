---
name: react-code-design
description: "Guide React code design, implementation, refactoring, and review. Use when Codex works on React, Next.js, Remix, Vite, JSX/TSX, hooks, components, state management, effects, forms, routing, data fetching, accessibility, rendering performance, server/client boundaries, or frontend architecture decisions."
---

# React Code Design

## Purpose

Use this skill to design and implement React code that is maintainable, accessible, predictable, and pleasant to evolve. Apply it when creating components, refactoring UI, reviewing React changes, debugging render/state behavior, or deciding where logic should live.

Favor the existing app's framework, routing, styling, state, and testing conventions. Do not introduce a new React library or architectural pattern unless the local codebase already uses it or the benefit is clear.

## Core Rule

Design React code around ownership of state, data flow, and user intent.

Before coding, identify:

- What user interaction or view state is being modeled.
- Which component owns each piece of state.
- Which data comes from the server, URL, form, local UI state, or derived computation.
- Which effects synchronize with external systems.
- Which behavior must be reusable across components.
- Which accessibility and keyboard interactions users will expect.

If ownership is unclear, fix the ownership model before adding more hooks.

## Component Boundaries

Create components around coherent UI responsibilities, not arbitrary visual fragments.

Good component boundaries usually have:

- A clear purpose visible from the component name.
- Props that describe domain concepts or UI intent.
- Minimal knowledge of parent layout and sibling behavior.
- Local state only for state the component truly owns.
- Stable accessibility semantics.

Avoid components that are:

- Named after layout trivia, such as generic wrappers that hide real behavior.
- Controlled partly by props and partly by hidden internal state without a clear contract.
- So configurable that they become mini-frameworks.
- Split so finely that reading the workflow requires jumping through many files.

## Props And Composition

Prefer explicit props and composition over hidden coupling.

- Use children or render slots when the caller should provide content.
- Use named props when the component owns structure and only needs values or callbacks.
- Keep boolean props sparse; multiple booleans often mean variants or state should be modeled explicitly.
- Avoid passing entire large objects when the child needs only a few fields, unless the object is the domain concept being displayed.
- Keep callback names event-shaped: `onSave`, `onSelectItem`, `onOpenChange`.
- Keep command props action-shaped: `saveDraft`, `deleteItem`, `loadMore`.

Use compound components only when they reduce real coordination complexity and match local conventions.

## State Ownership

Put state at the lowest common owner that needs to read or change it.

Use local component state for:

- Temporary UI state, such as open/closed, selected tab, active row, draft input.
- State that resets naturally when the component unmounts.

Use URL state for:

- Shareable filters, tabs, pagination, search, selected IDs, and navigation-relevant state.

Use server/cache state for:

- Data fetched from APIs, mutations, loading/error states, and invalidation.

Use global state only for:

- Cross-cutting app state that many distant areas need and cannot be represented by URL or server cache.

Do not mirror props into state unless editing a draft, managing animation/intermediate state, or intentionally taking a snapshot.

## Derived State

Derive values during render when possible.

- Compute filtered, sorted, grouped, or formatted data from existing state instead of storing another copy.
- Use `useMemo` for expensive computations or referential stability required by child components, not as a default habit.
- Avoid state that can become stale relative to its source.
- Keep derivations pure and deterministic.

If derived state needs to be stored, document the reason through naming and tests rather than comments alone.

## Effects

Use effects to synchronize React with external systems. Do not use effects as a default place for business logic.

Appropriate effects:

- Subscriptions and cleanup.
- Timers, media queries, observers, focus management, imperative widgets.
- Network calls only when the framework or project does not provide a better data-fetching mechanism.
- Synchronizing with browser APIs such as localStorage, document title, or history.

Avoid effects that:

- Copy props into state unnecessarily.
- Derive render data that could be computed directly.
- Trigger chains of updates that are hard to reason about.
- Hide user-event logic that belongs in an event handler.

Every effect should have a clear external system, complete cleanup when needed, and a dependency list that matches the values it reads.

## Hooks

Custom hooks should package reusable stateful behavior, not just hide code.

A good custom hook:

- Has a focused name beginning with `use`.
- Owns one coherent concern.
- Returns a small, stable API.
- Keeps side effects explicit.
- Is testable through a component or hook test when risky.

Avoid hooks that return large bags of unrelated data and actions. Split by ownership or lifecycle, not by file size alone.

## Data Fetching And Mutations

Follow the app's existing data layer first: framework loaders/actions, React Query, SWR, Apollo, server components, route loaders, or local services.

For fetched data:

- Keep loading, empty, error, and success states explicit.
- Avoid duplicate caches unless there is a clear invalidation story.
- Normalize or adapt API data at a boundary when the raw shape is awkward for UI.
- Make mutation success, failure, optimistic updates, rollback, and invalidation intentional.
- Avoid firing requests from render or from effects with unstable dependencies.

Prefer domain-named data functions over components knowing endpoint details.

## Server And Client Boundaries

For frameworks with server/client boundaries, keep responsibilities clear.

Server-side code is good for:

- Secure data access, secrets, authorization, heavy computation, initial fetches, SEO-critical content.

Client-side code is good for:

- Interactivity, local UI state, browser APIs, optimistic interactions, focus, gestures, live updates.

Do not pass non-serializable values across server/client boundaries. Do not move code client-side merely to make an import work; fix the boundary or split the component.

## Forms

Design forms around user workflow and validation ownership.

- Use controlled inputs when React state must drive validation, conditional UI, formatting, or submission.
- Use uncontrolled or form-library patterns when the app already uses them and the form is large.
- Keep field-level, form-level, and server validation distinct.
- Preserve user input on recoverable errors.
- Handle disabled, pending, success, and error states accessibly.
- Use labels, descriptions, and error messages connected to fields.

Do not bury validation rules in display components if the rules are domain behavior.

## Rendering Performance

Optimize render performance only where the UI or measurements justify it.

First check:

- Unnecessary state lifted too high.
- Context values changing too often.
- Expensive derivations repeated every render.
- Large lists without virtualization.
- Unstable keys causing remounts.
- Child components receiving new object/function props unnecessarily.

Use `memo`, `useMemo`, and `useCallback` to solve identified churn, not as decoration. Prefer better state placement and smaller render surfaces before memoization.

## Context

Use context for values that are truly ambient within a subtree.

Good context values:

- Theme, locale, auth session, router-ish services, feature flags, dependency providers, coordinated compound component state.

Risky context values:

- Frequently changing large objects.
- Server data better handled by a cache.
- Feature-specific state needed by only a few nearby components.

Split read-heavy and write-heavy context when it reduces rerenders and complexity.

## Lists And Identity

Keys are identity, not a warning suppressor.

- Use stable IDs from data whenever possible.
- Avoid array indexes when items can reorder, insert, delete, or preserve internal state.
- Keep item state keyed to item identity.
- Be careful with optimistic items and temporary IDs.

Bad keys create subtle UI state bugs.

## Accessibility

Treat accessibility as part of component correctness.

- Use semantic HTML before ARIA.
- Ensure interactive elements are keyboard reachable and have visible focus.
- Connect labels, descriptions, and errors to form fields.
- Preserve expected keyboard patterns for menus, dialogs, tabs, comboboxes, and grids.
- Manage focus for dialogs, route transitions when needed, and destructive flows.
- Do not use `div` or `span` as buttons when a native button works.
- Respect reduced motion and color contrast.

For complex widgets, prefer proven accessible primitives already used by the app.

## Styling

Follow the project's styling system.

- Keep styling colocated according to local convention.
- Use design tokens or existing utility classes where available.
- Do not encode business state only through color.
- Keep responsive constraints explicit: min/max widths, grid behavior, overflow, and wrapping.
- Avoid layout shifts caused by hover states, loading labels, or dynamic content.

Component APIs should expose intent, not arbitrary styling escape hatches, unless the design system requires them.

## Error And Empty States

Represent UI states deliberately:

- Loading: show progress without layout thrash.
- Empty: give the next useful action when appropriate.
- Error: explain what failed and what the user can do.
- Permission denied: distinguish from empty data.
- Offline or stale: show data freshness when relevant.

Do not collapse all non-success states into `null`.

## Testing

Test behavior at the level users and maintainers care about.

Prefer:

- Component tests for rendering, interaction, accessibility-relevant behavior, and state transitions.
- Integration tests for routed flows, data fetching, mutations, and cache invalidation.
- Unit tests for pure formatting, validation, reducers, and domain logic.
- Visual or screenshot tests when layout regressions are likely and the project supports them.

Avoid tests coupled to hook call order, internal state names, or implementation-only component structure.

## Refactoring React Code

When refactoring:

1. Identify state ownership and data sources.
2. Separate pure render, stateful behavior, and boundary adapters.
3. Remove mirrored or duplicated state.
4. Extract components only around meaningful UI responsibilities.
5. Extract hooks only around reusable stateful behavior.
6. Preserve accessibility and keyboard behavior.
7. Verify with focused tests or manual interaction.

Do not split components just because a file is long. Split when responsibilities are mixed or reuse is real.

## Review Checklist

When reviewing React code, check:

- Is state owned by the right component or layer?
- Is derived state computed instead of duplicated?
- Are effects necessary and correctly scoped to external synchronization?
- Are props clear, minimal, and intention-revealing?
- Are server/cache/URL/local states separated?
- Are loading, empty, error, and permission states handled?
- Is accessibility preserved for keyboard and screen reader users?
- Are keys stable and identity-based?
- Is performance addressed by state placement before memoization?
- Do tests cover the important user behavior or regression risk?

## Common Pushbacks

Push back on:

- `useEffect` used to compute ordinary render data.
- State duplicated across URL, cache, parent, and child without a sync plan.
- Global state for feature-local concerns.
- Components with many boolean props controlling unrelated variants.
- Context used as a dumping ground.
- Memoization added everywhere without a measured or explained problem.
- Accessibility regressions hidden behind custom UI.
- New libraries introduced for a problem the project already has a pattern for.

## Output Style

When giving React guidance:

- Name the ownership model first.
- Explain which state belongs where.
- Describe component boundaries and data flow.
- Mention effects only when they synchronize with an external system.
- Include accessibility and test implications when relevant.
- For code tasks, implement the change rather than stopping at advice.
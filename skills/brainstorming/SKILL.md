---
name: brainstorming
description: Large-scale product brainstorming for generating, organizing, and evaluating new ideas, feature areas, product directions, experiments, and roadmap bets. Use when Codex needs to expand a vague product thesis into many possible directions, create feature portfolios, discover opportunity spaces, synthesize ideas from research or experience, or prepare raw ideas for later product feature engineering.
---

# Brainstorming

## Core Posture

Expand before narrowing. Treat the first pass as exploration of possibility space, not a decision about what to build. Generate enough surface area that surprising ideas can appear, then cluster, compare, and select.

Keep ideas grounded in real use. Avoid lists of generic features. Tie each idea to a user, situation, motivation, behavior change, or repeated moment in the product.

Prefer systems of ideas over isolated ideas:

- Opportunity areas before individual features.
- Feature families before tickets.
- User journeys before screens.
- Loops and unlocks before one-off interactions.
- Experiments before large commitments.

## Workflow

1. Identify the product thesis, target user, current constraint, and ambition level.
2. Generate multiple opportunity spaces: acquisition, activation, habit, learning, expression, trust, community, monetization, retention, expansion, and maintenance.
3. For each promising space, generate feature families rather than single features.
4. Create variants at different scales: tiny experiment, MVP feature, polished version, long-term platform bet.
5. Cluster ideas by user value, technical leverage, learning value, and strategic risk.
6. Name the strongest patterns that emerge.
7. Select a small set of directions for deeper feature engineering or prototyping.
8. Preserve good rejected ideas in a parking lot with the reason they are not first.

## Idea Sources

Use several lenses so the brainstorm does not collapse into one familiar pattern:

### User Journey

Walk through first visit, first success, first failure, second session, habit formation, plateau, advanced use, and reactivation. Ask what feature could make each moment sharper.

### Capability Growth

Ask what the user can do now, what they almost can do, what they avoid, and what would make them feel newly capable.

### Friction Removal

Find moments where users hesitate, repeat manual work, lose context, feel embarrassed, wait too long, fail silently, or cannot tell whether they are improving.

### Motivation

Look for visible progress, meaningful unlocks, social proof, personal relevance, emotional stakes, novelty, and immediate usefulness.

### Feedback Loops

Ask what the product learns from user behavior and how that learning changes the next experience.

### Content and Context

Ask whether the product needs more content, better sequencing, richer situations, more variation, stronger personalization, or a clearer bridge from practice to real use.

### Platform Leverage

Look for reusable systems: templates, generators, scenario libraries, recommendation engines, assessment signals, creator tools, or shared assets.

### Boundary Pushing

Generate a few intentionally weird or ambitious ideas. Then translate the useful part into a feasible near-term experiment.

## Divergence Prompts

Use these prompts to create breadth:

- What would this product do if it had no UI?
- What would it do if it had no content library?
- What would it do if every session had to produce a real-world outcome?
- What would make a user come back tomorrow without a reminder?
- What would make progress visible after five minutes?
- What would make the product feel alive rather than static?
- What would an expert user still use after one year?
- What would remove the most boring 30% of the experience?
- What would create a new habit loop?
- What would turn passive consumption into active production?
- What would the product learn that competitors do not know?
- What would be possible if generation cost were near zero?
- What would be possible if human review were scarce and expensive?
- What would be culturally or emotionally wrong if done carelessly?
- What should never be automated?

## Clustering

After generating ideas, organize them into a useful map:

- **Now**: small experiments or obvious improvements.
- **Next**: features that need design and implementation but fit the current product.
- **Later**: platform bets, infrastructure, or ambitious experiences.
- **Wild**: strange ideas with a valuable underlying insight.
- **Avoid**: ideas likely to create fake progress, shallow engagement, trust problems, or maintenance burden.

Also cluster by product function:

- Acquisition: why someone tries it.
- Activation: how they reach the first meaningful success.
- Habit: why they return.
- Depth: how the experience gets richer over time.
- Feedback: how the system adapts.
- Trust: why the user believes the product is accurate and worth using.
- Maintenance: what the product becomes after the beginner phase.

## Evaluation

Score promising ideas qualitatively, not with fake precision:

- **User pull**: Would someone naturally want this?
- **Capability gain**: Does it make the user genuinely better at something?
- **Frequency**: Does it matter often enough?
- **Differentiation**: Does it create a product shape competitors do not have?
- **Learning signal**: Would building it teach us something important?
- **Feasibility**: Can we test it cheaply?
- **Compounding value**: Does it create assets, data, habits, or systems that get better over time?
- **Risk**: Could it mislead, annoy, overwhelm, or erode trust?

## Output Shape

For a broad brainstorm, produce:

1. Product thesis restated in plain language
2. Opportunity map
3. Feature families
4. Wild ideas worth translating
5. Top directions to explore next
6. First experiments
7. Risks and anti-ideas
8. Handoff notes for deeper feature engineering

For a faster session, output a ranked idea list with one-line rationale, expected user value, and smallest test.

## Handoff to Feature Engineering

Use this skill to generate and organize possibilities. When one direction is chosen, switch to `feature-engineering` to shape the exact mechanics, first session, progression, feedback loop, MVP scope, and failure checks.

# AI Interactions Log

> **Stretch features only.** Only fill in the sections that apply to stretch features you attempted. If you did not attempt a stretch feature, leave its section blank or delete it. This file is not required for the core project.

---

## Agentic Workflow (SF8)

> Document your experience using an AI agent (e.g., Cursor Agent, Claude, Copilot) to make multi-step changes autonomously.

**What task did you give the agent?**

<!-- Describe the goal you asked the agent to accomplish -->

**Prompts used:**

<!-- Paste the key prompts you gave the agent -->

**What did the agent generate or change?**

<!-- List the files edited, code generated, or commands run -->

**What did you verify or fix manually?**

<!-- Describe anything the agent got wrong or that required human review -->

---

## Design Pattern (SF10)

> Document how AI helped you choose or implement a design pattern.

**Which design pattern did you use?**

The **Strategy pattern**. Each ranking mode (balanced, genre-first, mood-first, energy-focused) is a separate strategy object. The rest of the program asks the current strategy to score a song and never needs to know which mode is active. Switching modes means passing in a different object, not changing any code.

**How did AI help you brainstorm or implement it?**

I gave Claude Code (in VS Code) `recommender.py` and asked it to brainstorm a design that would let a user switch between ranking modes in `main.py` while keeping the code modular. It laid out four options and their trade-offs:

| Option | How it works | Trade-off |
|---|---|---|
| 1. `if`/`elif` on a mode name | One `score_song` with a branch per mode | Simplest, but every new mode means editing the scoring function, and the branches get long |
| 2. One scoring function per mode | `score_genre_first()`, `score_mood_first()`, … | The five scoring rules get copied four times. A fix like the capitalization bug would have to be made in four places |
| 3. Abstract base class + one subclass per mode | Textbook Strategy, with each subclass overriding `score()` | Clean, but heavy here: the subclasses would be identical except for their numbers |
| 4. **One strategy class, with the weights as data** | A `ScoringStrategy` holds its weights and a `score()` method; each mode is one instance | Chosen: one copy of the rules, and a new mode is just a new set of numbers |

We chose option 4 for these reasons:
- **The modes only differ in their weights.** They all use the same five rules.
- **The edge-case fixes apply to every mode automatically.** These are the earlier fixes for capital letters, `"False"` as text and out-of-range energy.
- **Adding a mode is one step:** create a new `ScoringStrategy` and add it to `STRATEGIES`.
- **The design can still grow.** If a future mode needs a *different rule* (for example, penalizing repeated artists), it can subclass `ScoringStrategy` and override `score()`. That's option 3, used only where it's needed.

The AI also suggested:
- **Giving every mode the same maximum score (5.0),** so the score bars and the side-by-side comparison stay fair. A test checks this.
- **Building the `--mode` choices from `STRATEGIES`,** so a new mode shows up in the command line automatically.
- **Making strategies `frozen`,** so a mode's weights can't be changed by accident while the program runs.

**What I checked myself:**
- I ran `python -m src.main --compare` to confirm that each mode actually ranks songs differently. For example, *Gym Hero* scores 3.92 in genre-first but 1.85 in mood-first.
- I confirmed that an invalid mode like `--mode bogus` gives a clear error listing the valid modes.
- I ran `pytest`: all 4 tests pass, including 2 new ones for the strategies.
- The default mode, `balanced`, gives exactly the same results as before the refactor.

**How does the pattern appear in your final code?**

- **[`ScoringStrategy`](src/recommender.py#L87)** (`src/recommender.py`): the strategy class. It holds the five weights, a `max_score` property and the `score()` method that applies the rules and returns `(score, reasons)`.
- **[`BALANCED`, `GENRE_FIRST`, `MOOD_FIRST`, `ENERGY_FOCUSED`](src/recommender.py#L143)**: the four concrete strategies, each a `ScoringStrategy` with its own weights.
- **[`STRATEGIES` and `get_strategy()`](src/recommender.py#L164)**: a lookup table from mode name to strategy, with a helper that raises a clear error for unknown names.
- **[`score_song()`](src/recommender.py#L175), [`recommend_songs()`](src/recommender.py#L182) and `Recommender(songs, strategy)`**: these take a strategy (default `BALANCED`) and hand the scoring to it. They don't contain any weights themselves.
- **[`parse_args()`](src/main.py#L43) in `src/main.py`**: reads `--mode` and `--compare` from the command line and picks the strategy with `get_strategy(args.mode)`.

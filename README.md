# 🎵 Music Recommender Simulation

## Project Summary

In this project you will build and explain a small music recommender system.

Your goal is to:

- Represent songs and a user "taste profile" as data
- Design a scoring rule that turns that data into recommendations
- Evaluate what your system gets right and wrong
- Reflect on how this mirrors real world AI recommenders

Replace this paragraph with your own summary of what your version does.

---

## How The System Works

Real-world platforms like Spotify and YouTube combine two main approaches. **Collaborative filtering** recommends what similar users enjoyed ("people who liked this also liked..."). **Content-based filtering** recommends songs whose own attributes, such as genre, mood, energy and tempo, resemble what a listener already likes. These platforms also learn from behavior at huge scale: plays, skips, replays, likes and playlist adds. Our version is a simple content-based recommender. It has no other users or listening history, so it compares each song directly to one user's taste profile and gives it a score. It gives the most weight to how *close* the song's **energy** is to the user's target (closer earns more points, and higher isn't automatically better), then adds equal bonuses for matching **genre** and **mood**. Songs are ranked by total score, and the top matches are returned along with the reasons they scored well.

### Song features

Each row of `data/songs.csv` becomes a `Song` with:

| Feature | Type | Used in scoring? |
|---|---|---|
| `genre` | category (e.g. pop, lofi, rock) | Yes, exact match |
| `mood` | category (e.g. happy, chill, intense) | Yes, exact match |
| `energy` | 0.0–1.0 | Yes, closeness to target |
| `valence` | 0.0–1.0 (how positive/bright it sounds) | Yes, closeness to target |
| `acousticness` | 0.0–1.0 | Yes, based on `likes_acoustic` |
| `tempo_bpm`, `danceability` | number | Not yet (kept for future experiments) |

### User profile

The `UserProfile` stores one listener's taste:

- `favorite_genre`: the genre they want most
- `favorite_mood`: the mood they're in
- `target_energy`: how intense they want the music (0.0 = calm, 1.0 = max)
- `target_valence`: how bright or positive they want it to sound
- `likes_acoustic`: `True` for acoustic/organic sounds, `False` for produced/electronic

### Algorithm recipe

**Step 1: Score every song.** Each song starts at 0 and earns points:

| Rule | Points | Why this weight |
|---|---|---|
| Genre matches `favorite_genre` | **+1.0** | A real taste signal, but no longer strong enough to override everything else (was +2.0, see [Experiments](#experiments-you-tried)) |
| Mood matches `favorite_mood` | **+1.0** | Equal to genre, so a right-mood song from a nearby genre can compete |
| Energy closeness | **+2.0 × (1 − \|song.energy − target_energy\|)** | The biggest weight: rewards being *near* the target, not just high (was 1.0×) |
| Valence closeness | **+0.5 × (1 − \|song.valence − target_valence\|)** | Fine-tunes the vibe |
| Acoustic preference | **+0.5 × acousticness** if `likes_acoustic`, else **+0.5 × (1 − acousticness)** | Small nudge toward the preferred sound |

The maximum possible score is **5.0**. The categories (genre and mood) are worth up to 2.0 and the numeric features up to 3.0, so a song that matches the user's energy and vibe can beat a same-genre song that doesn't.

**Step 2: Record reasons.** For each rule that adds points, save a short reason (e.g. `"genre match: pop (+1.0)"`) so every recommendation can explain itself.

**Step 3: Rank and pick.** Sort all songs by score, highest first, and return the top `k` (default 5) with their scores and reasons.

```
user profile ──┐
               ├──> score_song() for every song ──> sort by score ──> top k + reasons
songs.csv ─────┘
```

**Worked example.** For the default profile in `src/main.py` (pop, happy, energy 0.80, valence 0.80, not acoustic):

| Rank | Song | Genre / Mood | Score |
|---|---|---|---|
| 1 | Sunrise City | pop / happy | 4.85 |
| 2 | Rooftop Lights | indie pop / happy | 3.74 |
| 3 | Gym Hero | pop / intense | 3.70 |
| 4 | Concrete Crown | hip-hop / confident | 2.81 |
| 5 | Neon Pulse | edm / euphoric | 2.69 |

### Biases to watch for

- **Genre dominance / filter bubble (reduced, not gone).** With the original weights (genre +2.0, energy 1.0×), a same-genre song with the wrong mood beat a different-genre song with the right mood: *Gym Hero* (pop, **intense**) outranked *Rooftop Lights* (indie pop, **happy**). After the weight shift, Rooftop Lights is #2 (3.74) and Gym Hero #3 (3.70). The *High-energy lofi fan* still gets two calm lofi songs first (energy 0.35–0.42), because genre + mood (2.0) can still outweigh a large energy miss, but #3–#5 are now high-energy songs. The trade-off: genre loyalty is weaker, so a user who truly only wants one genre may see more songs outside it.
- **Exact string matching.** `"indie pop"` does not count as `"pop"`, and `"chill"` does not count as `"relaxed"`. Related labels get zero credit, which penalizes subgenres and synonyms. (Capitalization and extra spaces are handled: `"Pop "` now matches `"pop"`.)
- **Uneven catalog.** Of 18 songs, lofi has 3 and pop has 2, but most genres (metal, classical, country, reggae, folk, etc.) have only **one** song. A metal fan gets one real match and four filler picks, so users with less common tastes get worse recommendations. In the *Contradictory metal* edge case, the only metal song (*Iron Tempest*, energy 0.97) is far from the requested energy 0.1, so it now falls to **#8**: the user gets no metal at all in their top 5. In *Missing keys* (pop only), the #3 pick scores **0.00** because there are only two pop songs.
- **Mood labels are subjective.** Someone decided each song's mood. One label per song can't capture that a track might be both "moody" and "focused", and the labels reflect whoever tagged the data.
- **Energy/valence assumptions.** Closeness scoring assumes everyone wants songs *near* one target value. It can't represent a listener who likes both very calm and very intense music.
- **Artist repetition isn't handled.** Nothing stops the top 5 from being dominated by one artist (e.g. Neon Echo or LoRoom), and there's no way to deliberately surface lesser-known artists.
- **No feedback loop.** The system never learns from skips or likes, so a bad recommendation will keep showing up.

### Edge case testing

`src/main.py` runs six tricky profiles (`EDGE_CASE_PROFILES`) after the main recommendations to check whether the scoring logic can be fooled. The first four exposed bugs that are now fixed in `score_song`; the last two show design trade-offs that remain.

| Profile | What it tests | Before fix | After fix / result |
|---|---|---|---|
| Capitalized labels (`"Pop"`, `"Happy"`) | Case-sensitive matching | Sunrise City scored 2.85 (matches missed) | 4.85, labels are lowercased and trimmed |
| String boolean (`likes_acoustic: "False"`) | `bool("False")` is `True` in Python | Treated as an acoustic fan (4.53) | 4.85, strings like `"false"` are read as False |
| Energy out of range (`target_energy: 1.5`) | Targets outside 0.0–1.0 | Calm songs earned **negative** points | Target clamped to 1.00 |
| Missing keys (`{"favorite_genre": "pop"}`) | Incomplete profiles | Display crashed with `KeyError` | Runs; missing rules are skipped |
| High-energy lofi fan (lofi, chill, energy 0.95) | Genre vs. energy conflict | — | Lofi songs still #1–#2 (energy ≤ 0.42); high-energy songs fill #3–#5 |
| Contradictory metal (metal, peaceful, energy 0.1) | Conflicting preferences | — | Classical wins clearly (3.76); the only metal song drops to #8 |

---

## Getting Started

### Setup

1. Create a virtual environment (optional but recommended):

   ```bash
   python -m venv .venv
   source .venv/bin/activate      # Mac or Linux
   .venv\Scripts\activate         # Windows

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Run the app:

```bash
python -m src.main
```

### Running Tests

Run the starter tests with:

```bash
pytest
```

You can add more tests in `tests/test_recommender.py`.

---

## Sample Recommendation Output

Output of `python -m src.main` using the default taste profile in `src/main.py` (pop, happy, energy 0.80, valence 0.80, not acoustic), with the current weights (genre +1.0, mood +1.0, energy 2.0×, valence 0.5×, acoustic 0.5×):

```text
Loading songs from data/songs.csv...
Loaded songs: 18

============================================================
 Top 5 recommendations
 Profile: pop / happy / energy 0.80
============================================================

 #1  Sunrise City  (Neon Echo)
     pop / happy
     Score: 4.85 / 5.00  ███████████████████░
     Why:
       • genre match: pop (+1.0)
       • mood match: happy (+1.0)
       • energy 0.82 vs target 0.80 (+1.96)
       • valence 0.84 vs target 0.80 (+0.48)
       • produced sound, acousticness 0.18 (+0.41)

------------------------------------------------------------

 #2  Rooftop Lights  (Indigo Parade)
     indie pop / happy
     Score: 3.74 / 5.00  ███████████████░░░░░
     Why:
       • mood match: happy (+1.0)
       • energy 0.76 vs target 0.80 (+1.92)
       • valence 0.81 vs target 0.80 (+0.49)
       • produced sound, acousticness 0.35 (+0.33)

------------------------------------------------------------

 #3  Gym Hero  (Max Pulse)
     pop / intense
     Score: 3.70 / 5.00  ███████████████░░░░░
     Why:
       • genre match: pop (+1.0)
       • energy 0.93 vs target 0.80 (+1.74)
       • valence 0.77 vs target 0.80 (+0.48)
       • produced sound, acousticness 0.05 (+0.47)

------------------------------------------------------------

 #4  Concrete Crown  (Block Theory)
     hip-hop / confident
     Score: 2.81 / 5.00  ███████████░░░░░░░░░
     Why:
       • energy 0.78 vs target 0.80 (+1.96)
       • valence 0.62 vs target 0.80 (+0.41)
       • produced sound, acousticness 0.12 (+0.44)

------------------------------------------------------------

 #5  Neon Pulse  (Hyperdrive)
     edm / euphoric
     Score: 2.69 / 5.00  ███████████░░░░░░░░░
     Why:
       • energy 0.95 vs target 0.80 (+1.70)
       • valence 0.79 vs target 0.80 (+0.49)
       • produced sound, acousticness 0.02 (+0.49)

------------------------------------------------------------
```

### Edge case profiles

The same run then prints the top 5 for each profile in `EDGE_CASE_PROFILES` (see [Edge case testing](#edge-case-testing)).

#### Capitalized labels

Identical to the lowercase default profile, so case and spacing no longer affect matching.

```text
============================================================
 Top 5 recommendations: Capitalized labels
 Profile: Pop / Happy / energy 0.80
============================================================

 #1  Sunrise City  (Neon Echo)
     pop / happy
     Score: 4.85 / 5.00  ███████████████████░
     Why:
       • genre match: pop (+1.0)
       • mood match: happy (+1.0)
       • energy 0.82 vs target 0.80 (+1.96)
       • valence 0.84 vs target 0.80 (+0.48)
       • produced sound, acousticness 0.18 (+0.41)

------------------------------------------------------------

 #2  Rooftop Lights  (Indigo Parade)
     indie pop / happy
     Score: 3.74 / 5.00  ███████████████░░░░░
     Why:
       • mood match: happy (+1.0)
       • energy 0.76 vs target 0.80 (+1.92)
       • valence 0.81 vs target 0.80 (+0.49)
       • produced sound, acousticness 0.35 (+0.33)

------------------------------------------------------------

 #3  Gym Hero  (Max Pulse)
     pop / intense
     Score: 3.70 / 5.00  ███████████████░░░░░
     Why:
       • genre match: pop (+1.0)
       • energy 0.93 vs target 0.80 (+1.74)
       • valence 0.77 vs target 0.80 (+0.48)
       • produced sound, acousticness 0.05 (+0.47)

------------------------------------------------------------

 #4  Concrete Crown  (Block Theory)
     hip-hop / confident
     Score: 2.81 / 5.00  ███████████░░░░░░░░░
     Why:
       • energy 0.78 vs target 0.80 (+1.96)
       • valence 0.62 vs target 0.80 (+0.41)
       • produced sound, acousticness 0.12 (+0.44)

------------------------------------------------------------

 #5  Neon Pulse  (Hyperdrive)
     edm / euphoric
     Score: 2.69 / 5.00  ███████████░░░░░░░░░
     Why:
       • energy 0.95 vs target 0.80 (+1.70)
       • valence 0.79 vs target 0.80 (+0.49)
       • produced sound, acousticness 0.02 (+0.49)

------------------------------------------------------------
```

#### String boolean

Identical to the default profile: `"False"` is correctly read as not acoustic.

```text
============================================================
 Top 5 recommendations: String boolean
 Profile: pop / happy / energy 0.80
============================================================

 #1  Sunrise City  (Neon Echo)
     pop / happy
     Score: 4.85 / 5.00  ███████████████████░
     Why:
       • genre match: pop (+1.0)
       • mood match: happy (+1.0)
       • energy 0.82 vs target 0.80 (+1.96)
       • valence 0.84 vs target 0.80 (+0.48)
       • produced sound, acousticness 0.18 (+0.41)

------------------------------------------------------------

 #2  Rooftop Lights  (Indigo Parade)
     indie pop / happy
     Score: 3.74 / 5.00  ███████████████░░░░░
     Why:
       • mood match: happy (+1.0)
       • energy 0.76 vs target 0.80 (+1.92)
       • valence 0.81 vs target 0.80 (+0.49)
       • produced sound, acousticness 0.35 (+0.33)

------------------------------------------------------------

 #3  Gym Hero  (Max Pulse)
     pop / intense
     Score: 3.70 / 5.00  ███████████████░░░░░
     Why:
       • genre match: pop (+1.0)
       • energy 0.93 vs target 0.80 (+1.74)
       • valence 0.77 vs target 0.80 (+0.48)
       • produced sound, acousticness 0.05 (+0.47)

------------------------------------------------------------

 #4  Concrete Crown  (Block Theory)
     hip-hop / confident
     Score: 2.81 / 5.00  ███████████░░░░░░░░░
     Why:
       • energy 0.78 vs target 0.80 (+1.96)
       • valence 0.62 vs target 0.80 (+0.41)
       • produced sound, acousticness 0.12 (+0.44)

------------------------------------------------------------

 #5  Neon Pulse  (Hyperdrive)
     edm / euphoric
     Score: 2.69 / 5.00  ███████████░░░░░░░░░
     Why:
       • energy 0.95 vs target 0.80 (+1.70)
       • valence 0.79 vs target 0.80 (+0.49)
       • produced sound, acousticness 0.02 (+0.49)

------------------------------------------------------------
```

#### Energy out of range

The target is clamped to 1.00, so the reasons say `vs target 1.00` and no song gets negative points. With energy now weighted 2.0×, the highest-energy songs rise: *Gym Hero* moves back to #2 and *Iron Tempest* (energy 0.97) enters at #5.

```text
============================================================
 Top 5 recommendations: Energy out of range
 Profile: pop / happy / energy 1.50
============================================================

 #1  Sunrise City  (Neon Echo)
     pop / happy
     Score: 4.53 / 5.00  ██████████████████░░
     Why:
       • genre match: pop (+1.0)
       • mood match: happy (+1.0)
       • energy 0.82 vs target 1.00 (+1.64)
       • valence 0.84 vs target 0.80 (+0.48)
       • produced sound, acousticness 0.18 (+0.41)

------------------------------------------------------------

 #2  Gym Hero  (Max Pulse)
     pop / intense
     Score: 3.82 / 5.00  ███████████████░░░░░
     Why:
       • genre match: pop (+1.0)
       • energy 0.93 vs target 1.00 (+1.86)
       • valence 0.77 vs target 0.80 (+0.48)
       • produced sound, acousticness 0.05 (+0.47)

------------------------------------------------------------

 #3  Rooftop Lights  (Indigo Parade)
     indie pop / happy
     Score: 3.34 / 5.00  █████████████░░░░░░░
     Why:
       • mood match: happy (+1.0)
       • energy 0.76 vs target 1.00 (+1.52)
       • valence 0.81 vs target 0.80 (+0.49)
       • produced sound, acousticness 0.35 (+0.33)

------------------------------------------------------------

 #4  Neon Pulse  (Hyperdrive)
     edm / euphoric
     Score: 2.88 / 5.00  ████████████░░░░░░░░
     Why:
       • energy 0.95 vs target 1.00 (+1.90)
       • valence 0.79 vs target 0.80 (+0.49)
       • produced sound, acousticness 0.02 (+0.49)

------------------------------------------------------------

 #5  Iron Tempest  (Ashen Forge)
     metal / angry
     Score: 2.65 / 5.00  ███████████░░░░░░░░░
     Why:
       • energy 0.97 vs target 1.00 (+1.94)
       • valence 0.25 vs target 0.80 (+0.22)
       • produced sound, acousticness 0.03 (+0.48)

------------------------------------------------------------
```

#### Missing keys

Only genre is set, and only two pop songs exist, so #3–#5 score 0.00 and simply follow CSV order. These are filler picks, not real recommendations.

```text
============================================================
 Top 5 recommendations: Missing keys
 Profile: pop / any / energy any
============================================================

 #1  Sunrise City  (Neon Echo)
     pop / happy
     Score: 1.00 / 5.00  ████░░░░░░░░░░░░░░░░
     Why:
       • genre match: pop (+1.0)

------------------------------------------------------------

 #2  Gym Hero  (Max Pulse)
     pop / intense
     Score: 1.00 / 5.00  ████░░░░░░░░░░░░░░░░
     Why:
       • genre match: pop (+1.0)

------------------------------------------------------------

 #3  Midnight Coding  (LoRoom)
     lofi / chill
     Score: 0.00 / 5.00  ░░░░░░░░░░░░░░░░░░░░
     Why:
       • no preferences matched

------------------------------------------------------------

 #4  Storm Runner  (Voltline)
     rock / intense
     Score: 0.00 / 5.00  ░░░░░░░░░░░░░░░░░░░░
     Why:
       • no preferences matched

------------------------------------------------------------

 #5  Library Rain  (Paper Lanterns)
     lofi / chill
     Score: 0.00 / 5.00  ░░░░░░░░░░░░░░░░░░░░
     Why:
       • no preferences matched

------------------------------------------------------------
```

#### High-energy lofi fan

Two lofi songs still come first, but the rest of the list now matches the energy request: *Storm Runner* (0.91), *Neon Pulse* (0.95) and *Iron Tempest* (0.97) fill #3–#5, pushing *Focus Flow* (lofi, 0.40) out.

```text
============================================================
 Top 5 recommendations: High-energy lofi fan
 Profile: lofi / chill / energy 0.95
============================================================

 #1  Midnight Coding  (LoRoom)
     lofi / chill
     Score: 3.56 / 5.00  ██████████████░░░░░░
     Why:
       • genre match: lofi (+1.0)
       • mood match: chill (+1.0)
       • energy 0.42 vs target 0.95 (+0.94)
       • valence 0.56 vs target 0.50 (+0.47)
       • produced sound, acousticness 0.71 (+0.15)

------------------------------------------------------------

 #2  Library Rain  (Paper Lanterns)
     lofi / chill
     Score: 3.32 / 5.00  █████████████░░░░░░░
     Why:
       • genre match: lofi (+1.0)
       • mood match: chill (+1.0)
       • energy 0.35 vs target 0.95 (+0.80)
       • valence 0.60 vs target 0.50 (+0.45)
       • produced sound, acousticness 0.86 (+0.07)

------------------------------------------------------------

 #3  Storm Runner  (Voltline)
     rock / intense
     Score: 2.86 / 5.00  ███████████░░░░░░░░░
     Why:
       • energy 0.91 vs target 0.95 (+1.92)
       • valence 0.48 vs target 0.50 (+0.49)
       • produced sound, acousticness 0.10 (+0.45)

------------------------------------------------------------

 #4  Neon Pulse  (Hyperdrive)
     edm / euphoric
     Score: 2.84 / 5.00  ███████████░░░░░░░░░
     Why:
       • energy 0.95 vs target 0.95 (+2.00)
       • valence 0.79 vs target 0.50 (+0.35)
       • produced sound, acousticness 0.02 (+0.49)

------------------------------------------------------------

 #5  Iron Tempest  (Ashen Forge)
     metal / angry
     Score: 2.82 / 5.00  ███████████░░░░░░░░░
     Why:
       • energy 0.97 vs target 0.95 (+1.96)
       • valence 0.25 vs target 0.50 (+0.38)
       • produced sound, acousticness 0.03 (+0.48)

------------------------------------------------------------
```

#### Contradictory metal

Mood, energy and acoustic preference all point to calm music, so classical wins clearly. The only metal song (energy 0.97) is no longer in the top 5.

```text
============================================================
 Top 5 recommendations: Contradictory metal
 Profile: metal / peaceful / energy 0.10
============================================================

 #1  Moonlit Sonata Redux  (Elena Vasquez)
     classical / peaceful
     Score: 3.76 / 5.00  ███████████████░░░░░
     Why:
       • mood match: peaceful (+1.0)
       • energy 0.18 vs target 0.10 (+1.84)
       • valence 0.42 vs target 0.30 (+0.44)
       • acoustic sound, acousticness 0.97 (+0.48)

------------------------------------------------------------

 #2  Autumn Letters  (Hazel & Pine)
     folk / melancholic
     Score: 2.54 / 5.00  ██████████░░░░░░░░░░
     Why:
       • energy 0.30 vs target 0.10 (+1.60)
       • valence 0.28 vs target 0.30 (+0.49)
       • acoustic sound, acousticness 0.90 (+0.45)

------------------------------------------------------------

 #3  Spacewalk Thoughts  (Orbit Bloom)
     ambient / chill
     Score: 2.42 / 5.00  ██████████░░░░░░░░░░
     Why:
       • energy 0.28 vs target 0.10 (+1.64)
       • valence 0.65 vs target 0.30 (+0.32)
       • acoustic sound, acousticness 0.92 (+0.46)

------------------------------------------------------------

 #4  Library Rain  (Paper Lanterns)
     lofi / chill
     Score: 2.28 / 5.00  █████████░░░░░░░░░░░
     Why:
       • energy 0.35 vs target 0.10 (+1.50)
       • valence 0.60 vs target 0.30 (+0.35)
       • acoustic sound, acousticness 0.86 (+0.43)

------------------------------------------------------------

 #5  Coffee Shop Stories  (Slow Stereo)
     jazz / relaxed
     Score: 2.20 / 5.00  █████████░░░░░░░░░░░
     Why:
       • energy 0.37 vs target 0.10 (+1.46)
       • valence 0.71 vs target 0.30 (+0.30)
       • acoustic sound, acousticness 0.89 (+0.45)

------------------------------------------------------------
```

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or demo video link here -->

---

## Experiments You Tried

### Experiment 1: Weight shift (kept)

**Change:** genre **+2.0 → +1.0** and energy **1.0× → 2.0×**. Mood, valence and acoustic stayed the same, so the maximum score is still 5.0.

**Why:** the edge cases showed genre overriding everything else. A pop fan got the wrong-mood *Gym Hero* above the right-mood *Rooftop Lights*, and a lofi fan asking for energy 0.95 got only calm lofi songs.

| Profile | Before (genre 2.0, energy 1.0) | After (genre 1.0, energy 2.0) |
|---|---|---|
| Default (pop/happy, 0.8) | Sunrise City 4.87, **Gym Hero 3.83**, Rooftop Lights 2.78, Neon Pulse 1.84, Concrete Crown 1.83 | Sunrise City 4.85, **Rooftop Lights 3.74**, Gym Hero 3.70, Concrete Crown 2.81, Neon Pulse 2.69 |
| High-energy lofi fan (0.95) | Midnight Coding 4.08, Library Rain 3.92, Focus Flow 3.02, Storm Runner 1.90, Neon Pulse 1.84 | Midnight Coding 3.56, Library Rain 3.32, **Storm Runner 2.86, Neon Pulse 2.84, Iron Tempest 2.82** |
| Contradictory metal (0.1) | Moonlit Sonata 2.84, **Iron Tempest 2.62**, Autumn Letters 1.74, Spacewalk 1.60, Library Rain 1.53 | Moonlit Sonata 3.76, Autumn Letters 2.54, Spacewalk 2.42, Library Rain 2.28, Coffee Shop 2.20 |

**Result:** the system became more sensitive to *how a song sounds* and less loyal to labels. Right-mood songs from nearby genres can now compete, and energy requests are respected. The cost is that genre matters less: the metal fan gets no metal song in their top 5 (Iron Tempest falls to #8).

### Experiment 2: Removing mood (rejected)

**Change:** mood **+1.0 → 0**, everything else at the original weights.

| Profile | Result |
|---|---|
| Default (pop/happy) | Sunrise City 3.87 and Gym Hero 3.83 nearly tie; Rooftop Lights (the right mood) falls to **#5** (1.78) |
| Contradictory metal (peaceful, 0.1) | *Iron Tempest* (angry, energy 0.97) becomes **#1** (2.62) |

**Result:** worse in every case tested. Without mood, genre dominates even more and the system can't tell an intense song from a happy one, so mood was kept.

---

## Limitations and Risks

Summarize some limitations of your recommender.

Examples:

- It only works on a tiny catalog
- It does not understand lyrics or language
- It might over favor one genre or mood

You will go deeper on this in your model card.

---

## Reflection

Read and complete `model_card.md`:

[**Model Card**](model_card.md)

I learned that music has different ways to pull people in to listen to some more. These big entertainment apps know how to keep their customers listening
-I used claude to help with this project alot to understand the implementation and some of the changes needed to make this project work.
-The simple reconnmendations made this project better. Some of the previous music genres werent correct
-Next I would try to add some different genres of music to see if the simulator could still pick up on little details.
- about how recommenders turn data into predictions
- about where bias or unfairness could show up in systems like this




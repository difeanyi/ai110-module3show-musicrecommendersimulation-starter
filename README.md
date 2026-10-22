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

Real-world platforms like Spotify and YouTube combine two main approaches. **Collaborative filtering** recommends what similar users enjoyed ("people who liked this also liked..."). **Content-based filtering** recommends songs whose own attributes, such as genre, mood, energy and tempo, resemble what a listener already likes. These platforms also learn from behavior at huge scale: plays, skips, replays, likes and playlist adds. Our version is a simple content-based recommender. It has no other users or listening history, so it compares each song directly to one user's taste profile and gives it a score. It prioritizes **genre** first (an exact match earns the most points), then **mood**, then how *close* the song's **energy** is to the user's target. Closer earns more points, and higher isn't automatically better. Songs are ranked by total score, and the top matches are returned along with the reasons they scored well.

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
| Genre matches `favorite_genre` | **+2.0** | Strongest taste signal; most people have genres they never want |
| Mood matches `favorite_mood` | **+1.0** | Refines the pick within a genre; acts as a tiebreaker |
| Energy closeness | **+1.0 × (1 − \|song.energy − target_energy\|)** | Rewards being *near* the target, not just high |
| Valence closeness | **+0.5 × (1 − \|song.valence − target_valence\|)** | Fine-tunes the vibe |
| Acoustic preference | **+0.5 × acousticness** if `likes_acoustic`, else **+0.5 × (1 − acousticness)** | Small nudge toward the preferred sound |

The maximum possible score is **5.0**. The categories (genre and mood) are worth up to 3.0 and the numeric features up to 2.0, so a match on both genre and mood almost always wins.

**Step 2: Record reasons.** For each rule that adds points, save a short reason (e.g. `"genre match: pop (+2.0)"`) so every recommendation can explain itself.

**Step 3: Rank and pick.** Sort all songs by score, highest first, and return the top `k` (default 5) with their scores and reasons.

```
user profile ──┐
               ├──> score_song() for every song ──> sort by score ──> top k + reasons
songs.csv ─────┘
```

**Worked example.** For the default profile in `src/main.py` (pop, happy, energy 0.80, valence 0.80, not acoustic):

| Rank | Song | Genre / Mood | Score |
|---|---|---|---|
| 1 | Sunrise City | pop / happy | 4.87 |
| 2 | Gym Hero | pop / intense | 3.83 |
| 3 | Rooftop Lights | indie pop / happy | 2.78 |
| 4 | Neon Pulse | edm / euphoric | 1.84 |
| 5 | Concrete Crown | hip-hop / confident | 1.83 |

### Biases to watch for

- **Genre dominance / filter bubble.** Genre is worth twice as much as mood, so a same-genre song with the wrong mood beats a different-genre song with the right mood. In the example above, *Gym Hero* (pop, **intense**) outranks *Rooftop Lights* (indie pop, **happy**), even though Rooftop Lights is much closer to what the user asked for. Users rarely get pushed outside their favorite genre.
- **Exact string matching.** `"indie pop"` does not count as `"pop"`, and `"chill"` does not count as `"relaxed"`. Related labels get zero credit, which penalizes subgenres and synonyms.
- **Uneven catalog.** Of 18 songs, lofi has 3 and pop has 2, but most genres (metal, classical, country, reggae, folk, etc.) have only **one** song. A metal fan gets one real match and four filler picks, so users with less common tastes get worse recommendations.
- **Mood labels are subjective.** Someone decided each song's mood. One label per song can't capture that a track might be both "moody" and "focused", and the labels reflect whoever tagged the data.
- **Energy/valence assumptions.** Closeness scoring assumes everyone wants songs *near* one target value. It can't represent a listener who likes both very calm and very intense music.
- **Artist repetition isn't handled.** Nothing stops the top 5 from being dominated by one artist (e.g. Neon Echo or LoRoom), and there's no way to deliberately surface lesser-known artists.
- **No feedback loop.** The system never learns from skips or likes, so a bad recommendation will keep showing up.

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

Output of `python -m src.main` using the default taste profile in `src/main.py` (pop, happy, energy 0.80, valence 0.80, not acoustic):

```text
Loading songs from data/songs.csv...
Loaded songs: 18

============================================================
 Top 5 recommendations
 Profile: pop / happy / energy 0.80
============================================================

 #1  Sunrise City  (Neon Echo)
     pop / happy
     Score: 4.87 / 5.00  ███████████████████░
     Why:
       • genre match: pop (+2.0)
       • mood match: happy (+1.0)
       • energy 0.82 vs target 0.80 (+0.98)
       • valence 0.84 vs target 0.80 (+0.48)
       • produced sound, acousticness 0.18 (+0.41)

------------------------------------------------------------

 #2  Gym Hero  (Max Pulse)
     pop / intense
     Score: 3.83 / 5.00  ███████████████░░░░░
     Why:
       • genre match: pop (+2.0)
       • energy 0.93 vs target 0.80 (+0.87)
       • valence 0.77 vs target 0.80 (+0.48)
       • produced sound, acousticness 0.05 (+0.47)

------------------------------------------------------------

 #3  Rooftop Lights  (Indigo Parade)
     indie pop / happy
     Score: 2.78 / 5.00  ███████████░░░░░░░░░
     Why:
       • mood match: happy (+1.0)
       • energy 0.76 vs target 0.80 (+0.96)
       • valence 0.81 vs target 0.80 (+0.49)
       • produced sound, acousticness 0.35 (+0.33)

------------------------------------------------------------

 #4  Neon Pulse  (Hyperdrive)
     edm / euphoric
     Score: 1.84 / 5.00  ███████░░░░░░░░░░░░░
     Why:
       • energy 0.95 vs target 0.80 (+0.85)
       • valence 0.79 vs target 0.80 (+0.49)
       • produced sound, acousticness 0.02 (+0.49)

------------------------------------------------------------

 #5  Concrete Crown  (Block Theory)
     hip-hop / confident
     Score: 1.83 / 5.00  ███████░░░░░░░░░░░░░
     Why:
       • energy 0.78 vs target 0.80 (+0.98)
       • valence 0.62 vs target 0.80 (+0.41)
       • produced sound, acousticness 0.12 (+0.44)

------------------------------------------------------------
```

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or demo video link here -->

---

## Experiments You Tried

Use this section to document the experiments you ran. For example:

- What happened when you changed the weight on genre from 2.0 to 0.5
- What happened when you added tempo or valence to the score
- How did your system behave for different types of users

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

Write 1 to 2 paragraphs here about what you learned:

- about how recommenders turn data into predictions
- about where bias or unfairness could show up in systems like this




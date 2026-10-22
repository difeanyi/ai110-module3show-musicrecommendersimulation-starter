import csv
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, asdict

@dataclass
class Song:
    """
    Represents a song and its attributes.
    Required by tests/test_recommender.py
    """
    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float

@dataclass
class UserProfile:
    """
    Represents a user's taste preferences.
    Required by tests/test_recommender.py
    """
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool
    target_valence: Optional[float] = None

class Recommender:
    """
    OOP implementation of the recommendation logic.
    Required by tests/test_recommender.py
    """
    def __init__(self, songs: List[Song], strategy: Optional["ScoringStrategy"] = None):
        self.songs = songs
        self.strategy = strategy or BALANCED

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        """Returns the top k songs for the user, ranked by score from highest to lowest."""
        prefs = asdict(user)
        ranked = sorted(self.songs, key=lambda song: self.strategy.score(prefs, asdict(song))[0], reverse=True)
        return ranked[:k]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        """Returns the song's score and the reasons it earned points, as one readable string."""
        score, reasons = self.strategy.score(asdict(user), asdict(song))
        return f"Score {score:.2f}: " + "; ".join(reasons)

def load_songs(csv_path: str) -> List[Dict]:
    """
    Loads songs from a CSV file.
    Required by src/main.py
    """
    print(f"Loading songs from {csv_path}...")
    float_fields = ["energy", "tempo_bpm", "valence", "danceability", "acousticness"]

    songs = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            # csv reads everything as text, so convert numeric columns for scoring
            row["id"] = int(row["id"])
            for field in float_fields:
                row[field] = float(row[field])
            songs.append(row)
    return songs

def _normalize_label(value) -> str:
    """Lowercases and trims a genre/mood label so "Pop " matches "pop"."""
    return str(value).strip().lower() if value is not None else ""

def _clamp_unit(value: Optional[float]) -> Optional[float]:
    """Keeps a numeric target inside 0.0-1.0 so closeness points never go negative."""
    return None if value is None else max(0.0, min(1.0, float(value)))

def _to_bool(value) -> Optional[bool]:
    """Reads True/False from a real bool or a string like "false", since bool("False") is True."""
    if value is None or isinstance(value, bool):
        return value
    return str(value).strip().lower() in ("true", "yes", "1")

@dataclass(frozen=True)
class ScoringStrategy:
    """
    One ranking mode: a named set of weights plus the rules that turn them into a score.
    Swapping the strategy changes how songs are ranked without touching the rest of the code.
    """
    name: str
    description: str
    genre_points: float
    mood_points: float
    energy_weight: float
    valence_weight: float
    acoustic_weight: float

    @property
    def max_score(self) -> float:
        """Highest score a song can earn under this strategy."""
        return (self.genre_points + self.mood_points + self.energy_weight
                + self.valence_weight + self.acoustic_weight)

    def score(self, user_prefs: Dict, song: Dict) -> Tuple[float, List[str]]:
        """Scores one song against the user's preferences and returns (score, list of reasons)."""
        score = 0.0
        reasons = []

        # Categories: fixed points for an exact match
        if _normalize_label(song["genre"]) == _normalize_label(user_prefs.get("favorite_genre")):
            score += self.genre_points
            reasons.append(f"genre match: {song['genre']} (+{self.genre_points:.1f})")
        if _normalize_label(song["mood"]) == _normalize_label(user_prefs.get("favorite_mood")):
            score += self.mood_points
            reasons.append(f"mood match: {song['mood']} (+{self.mood_points:.1f})")

        # Numbers: reward closeness to the target, not size
        target_energy = _clamp_unit(user_prefs.get("target_energy"))
        if target_energy is not None:
            points = self.energy_weight * (1 - abs(song["energy"] - target_energy))
            score += points
            reasons.append(f"energy {song['energy']:.2f} vs target {target_energy:.2f} (+{points:.2f})")

        target_valence = _clamp_unit(user_prefs.get("target_valence"))
        if target_valence is not None:
            points = self.valence_weight * (1 - abs(song["valence"] - target_valence))
            score += points
            reasons.append(f"valence {song['valence']:.2f} vs target {target_valence:.2f} (+{points:.2f})")

        likes_acoustic = _to_bool(user_prefs.get("likes_acoustic"))
        if likes_acoustic is not None:
            fit = song["acousticness"] if likes_acoustic else 1 - song["acousticness"]
            points = self.acoustic_weight * fit
            score += points
            sound = "acoustic" if likes_acoustic else "produced"
            reasons.append(f"{sound} sound, acousticness {song['acousticness']:.2f} (+{points:.2f})")

        return score, reasons

# Available ranking modes; every strategy has a max score of 5.0 so scores stay comparable
BALANCED = ScoringStrategy(
    name="balanced",
    description="Energy matters most, with equal bonuses for genre and mood",
    genre_points=1.0, mood_points=1.0, energy_weight=2.0, valence_weight=0.5, acoustic_weight=0.5,
)
GENRE_FIRST = ScoringStrategy(
    name="genre-first",
    description="Stick to the favorite genre; everything else is a tiebreaker",
    genre_points=3.0, mood_points=1.0, energy_weight=0.5, valence_weight=0.25, acoustic_weight=0.25,
)
MOOD_FIRST = ScoringStrategy(
    name="mood-first",
    description="Match the mood, even if the genre is different",
    genre_points=0.5, mood_points=3.0, energy_weight=1.0, valence_weight=0.25, acoustic_weight=0.25,
)
ENERGY_FOCUSED = ScoringStrategy(
    name="energy-focused",
    description="Match the intensity level; labels barely matter",
    genre_points=0.5, mood_points=0.5, energy_weight=3.5, valence_weight=0.25, acoustic_weight=0.25,
)

STRATEGIES: Dict[str, ScoringStrategy] = {
    strategy.name: strategy for strategy in (BALANCED, GENRE_FIRST, MOOD_FIRST, ENERGY_FOCUSED)
}

def get_strategy(name: str) -> ScoringStrategy:
    """Looks up a strategy by name, e.g. "mood-first"; raises ValueError listing valid names."""
    key = _normalize_label(name)
    if key not in STRATEGIES:
        raise ValueError(f"Unknown strategy {name!r}. Choose from: {', '.join(STRATEGIES)}")
    return STRATEGIES[key]

def score_song(user_prefs: Dict, song: Dict, strategy: ScoringStrategy = BALANCED) -> Tuple[float, List[str]]:
    """
    Scores a single song against user preferences using the given strategy.
    Required by recommend_songs() and src/main.py
    """
    return strategy.score(user_prefs, song)

def recommend_songs(
    user_prefs: Dict, songs: List[Dict], k: int = 5, strategy: ScoringStrategy = BALANCED
) -> List[Tuple[Dict, float, str]]:
    """
    Functional implementation of the recommendation logic.
    Required by src/main.py
    """
    scored = []
    for song in songs:
        score, reasons = score_song(user_prefs, song, strategy)
        scored.append((song, score, "; ".join(reasons)))

    scored.sort(key=lambda item: item[1], reverse=True)
    return scored[:k]

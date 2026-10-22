"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

You will implement the functions in recommender.py:
- load_songs
- score_song
- recommend_songs
"""

from pathlib import Path

try:
    from src.recommender import load_songs, recommend_songs  # python -m src.main
except ModuleNotFoundError:
    from recommender import load_songs, recommend_songs  # python src/main.py / Run button

# Resolve the CSV relative to this file so it loads from any working directory
SONGS_CSV = Path(__file__).resolve().parent.parent / "data" / "songs.csv"

# Display settings for the terminal output
MAX_SCORE = 5.0  # highest possible score from the Algorithm Recipe
LINE_WIDTH = 60
BAR_WIDTH = 20

# Tricky profiles for checking that the scoring logic can't be fooled
EDGE_CASE_PROFILES = {
    "Capitalized labels": {"favorite_genre": "Pop", "favorite_mood": "Happy",
                           "target_energy": 0.8, "target_valence": 0.8, "likes_acoustic": False},
    "String boolean": {"favorite_genre": "pop", "favorite_mood": "happy",
                       "target_energy": 0.8, "target_valence": 0.8, "likes_acoustic": "False"},
    "Energy out of range": {"favorite_genre": "pop", "favorite_mood": "happy",
                            "target_energy": 1.5, "target_valence": 0.8, "likes_acoustic": False},
    "Missing keys": {"favorite_genre": "pop"},
    "High-energy lofi fan": {"favorite_genre": "lofi", "favorite_mood": "chill",
                             "target_energy": 0.95, "target_valence": 0.5, "likes_acoustic": False},
    "Contradictory metal": {"favorite_genre": "metal", "favorite_mood": "peaceful",
                            "target_energy": 0.1, "target_valence": 0.3, "likes_acoustic": True},
}


def main() -> None:
    songs = load_songs(str(SONGS_CSV))
    print(f"Loaded songs: {len(songs)}")

    # Taste profile: categories are matched exactly, numbers (0.0-1.0) score by closeness
    user_prefs = {
        "favorite_genre": "pop",
        "favorite_mood": "happy",
        "target_energy": 0.80,   # upbeat, but not max intensity
        "target_valence": 0.80,  # bright, positive sound
        "likes_acoustic": False,  # leans toward produced/electronic tracks
    }

    recommendations = recommend_songs(user_prefs, songs, k=5)
    print_recommendations(user_prefs, recommendations)

    print("\n\nEDGE CASE PROFILES")
    for name, profile in EDGE_CASE_PROFILES.items():
        print_recommendations(profile, recommend_songs(profile, songs, k=5), title=name)


def print_recommendations(user_prefs: dict, recommendations: list, title: str = "") -> None:
    """Prints each recommendation with its rank, score bar, and scoring reasons."""
    energy = user_prefs.get("target_energy")
    print()
    print("=" * LINE_WIDTH)
    print(f" Top {len(recommendations)} recommendations" + (f": {title}" if title else ""))
    print(
        f" Profile: {user_prefs.get('favorite_genre', 'any')} / {user_prefs.get('favorite_mood', 'any')}"
        f" / energy {f'{energy:.2f}' if energy is not None else 'any'}"
    )
    print("=" * LINE_WIDTH)

    for rank, (song, score, explanation) in enumerate(recommendations, start=1):
        filled = round(score / MAX_SCORE * BAR_WIDTH)
        bar = "█" * filled + "░" * (BAR_WIDTH - filled)

        print()
        print(f" #{rank}  {song['title']}  ({song['artist']})")
        print(f"     {song['genre']} / {song['mood']}")
        print(f"     Score: {score:.2f} / {MAX_SCORE:.2f}  {bar}")
        print("     Why:")
        for reason in explanation.split("; ") if explanation else ["no preferences matched"]:
            print(f"       • {reason}")
        print()
        print("-" * LINE_WIDTH)


if __name__ == "__main__":
    main()

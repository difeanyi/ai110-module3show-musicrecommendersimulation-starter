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


def print_recommendations(user_prefs: dict, recommendations: list) -> None:
    """Prints each recommendation with its rank, score bar, and scoring reasons."""
    print()
    print("=" * LINE_WIDTH)
    print(f" Top {len(recommendations)} recommendations")
    print(
        f" Profile: {user_prefs['favorite_genre']} / {user_prefs['favorite_mood']}"
        f" / energy {user_prefs['target_energy']:.2f}"
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
        for reason in explanation.split("; "):
            print(f"       • {reason}")
        print()
        print("-" * LINE_WIDTH)


if __name__ == "__main__":
    main()

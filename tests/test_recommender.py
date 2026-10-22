from src.recommender import Song, UserProfile, Recommender

def make_small_recommender() -> Recommender:
    songs = [
        Song(
            id=1,
            title="Test Pop Track",
            artist="Test Artist",
            genre="pop",
            mood="happy",
            energy=0.8,
            tempo_bpm=120,
            valence=0.9,
            danceability=0.8,
            acousticness=0.2,
        ),
        Song(
            id=2,
            title="Chill Lofi Loop",
            artist="Test Artist",
            genre="lofi",
            mood="chill",
            energy=0.4,
            tempo_bpm=80,
            valence=0.6,
            danceability=0.5,
            acousticness=0.9,
        ),
    ]
    return Recommender(songs)


def test_recommend_returns_songs_sorted_by_score():
    user = UserProfile(
        favorite_genre="pop",
        favorite_mood="happy",
        target_energy=0.8,
        likes_acoustic=False,
    )
    rec = make_small_recommender()
    results = rec.recommend(user, k=2)

    assert len(results) == 2
    # Starter expectation: the pop, happy, high energy song should score higher
    assert results[0].genre == "pop"
    assert results[0].mood == "happy"


def test_explain_recommendation_returns_non_empty_string():
    user = UserProfile(
        favorite_genre="pop",
        favorite_mood="happy",
        target_energy=0.8,
        likes_acoustic=False,
    )
    rec = make_small_recommender()
    song = rec.songs[0]

    explanation = rec.explain_recommendation(user, song)
    assert isinstance(explanation, str)
    assert explanation.strip() != ""


def test_strategies_change_the_ranking():
    from src.recommender import GENRE_FIRST, MOOD_FIRST

    songs = [
        Song(id=1, title="Pop But Intense", artist="A", genre="pop", mood="intense",
             energy=0.8, tempo_bpm=120, valence=0.8, danceability=0.8, acousticness=0.2),
        Song(id=2, title="Happy Not Pop", artist="B", genre="indie", mood="happy",
             energy=0.8, tempo_bpm=120, valence=0.8, danceability=0.8, acousticness=0.2),
    ]
    user = UserProfile(favorite_genre="pop", favorite_mood="happy", target_energy=0.8, likes_acoustic=False)

    assert Recommender(songs, GENRE_FIRST).recommend(user, k=1)[0].title == "Pop But Intense"
    assert Recommender(songs, MOOD_FIRST).recommend(user, k=1)[0].title == "Happy Not Pop"


def test_every_strategy_has_same_max_score():
    from src.recommender import STRATEGIES

    assert {round(s.max_score, 6) for s in STRATEGIES.values()} == {5.0}

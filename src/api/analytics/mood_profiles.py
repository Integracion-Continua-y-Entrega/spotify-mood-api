MOOD_TARGETS: dict[str, dict[str, float]] = {
    "happy":       {"energy": 0.8, "valence": 0.85, "danceability": 0.75, "acousticness": 0.2,  "instrumentalness": 0.1},
    "relaxed":     {"energy": 0.3, "valence": 0.60, "danceability": 0.40, "acousticness": 0.7,  "instrumentalness": 0.4},
    "melancholic": {"energy": 0.3, "valence": 0.20, "danceability": 0.35, "acousticness": 0.6,  "instrumentalness": 0.3},
    "energetic":   {"energy": 0.9, "valence": 0.65, "danceability": 0.80, "acousticness": 0.1,  "instrumentalness": 0.1},
}
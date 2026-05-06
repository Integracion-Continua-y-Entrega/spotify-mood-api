from math import sqrt
import pandas as pd
from models.mood import Mood
from analytics.mood_profiles import MOOD_TARGETS

MOOD_WEIGHT = 0.4
USER_WEIGHT = 1 - MOOD_WEIGHT

FEATURES = ["energy", "danceability", "valence", "acousticness", "instrumentalness"]

def _blend_targets(acoustic_profile: dict, mood: Mood) -> dict[str, float]:
    """
    Mezcla el perfil del usuario con los targets del mood.
    Resultado: un único target por feature que combina ambas fuentes.
    """
    mood_targets = MOOD_TARGETS[mood.value]
    return {
        feature: USER_WEIGHT * acoustic_profile[feature]["target"] + MOOD_WEIGHT * mood_targets[feature]
        for feature in FEATURES
    }

def get_tracks_recommendations(tracks: list[dict], acoustic_profile: dict, mood: Mood):
    df = pd.DataFrame(tracks)

    blended = _blend_targets(acoustic_profile, mood)

    df['distance'] = df.apply(lambda row: sqrt(sum(
        (blended[f] - row['acoustic_features'][f]) ** 2
        for f in FEATURES
    )), axis=1)

    similar_tracks = df.sort_values(by='distance', ascending=True).head(10)
    similar_tracks['spotify_id'] = similar_tracks['external_ids'].str['spotify_id']

    return similar_tracks[['id', 'distance']].reset_index(drop=True)

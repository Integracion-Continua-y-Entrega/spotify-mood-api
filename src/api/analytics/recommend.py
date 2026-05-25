from math import sqrt
import pandas as pd
from models.mood import Mood
from analytics.mood_profiles import MOOD_TARGETS
import numpy as np

MOOD_WEIGHT = 0.4
USER_WEIGHT = 1 - MOOD_WEIGHT

FEATURES = ["energy", 
"danceability", "valence", "acousticness", "instrumentalness"]

TOP_K = 50

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
    
    # 1. Crear un df de numppy vacío
    matrix = np.empty((len(tracks), len(FEATURES)), dtype=np.float32)
    ids = []

    for i, track in enumerate(tracks):
        af = track["acoustic_features"]

        matrix[i] = (
            af["energy"],
            af["danceability"],
            af["valence"],
            af["acousticness"],
            af["instrumentalness"],
        )

        ids.append(str(track["_id"]))

    # 2. Combinar o balancear el peso del perfil acústico del usuario con el del MOOD  
    blended = _blend_targets(acoustic_profile, mood)

    # Objeto unidimensional a utilizar en el broadcasting
    features_arr = np.array([blended[f] for f in FEATURES], dtype=np.float32)

    # BROADCASTING
    distances = np.sum((matrix - features_arr) ** 2, axis=1)

    k = min(TOP_K, len(distances))

    top_idx = np.argpartition(distances, k - 1)[:k]

    sorted_idx = top_idx[np.argsort(distances[top_idx])]

    return [ {
            "id": ids[i],
            "distance": float(distances[i]) 
        }
        for i in sorted_idx
    ]
from math import sqrt
from venv import logger
import pandas as pd
from models.mood import Mood
from analytics.mood_profiles import MOOD_TARGETS
import numpy as np

MOOD_WEIGHT = 0.4
USER_WEIGHT = 1 - MOOD_WEIGHT # Los pesos deben sumar a 1

FEATURES = ["energy", 
            "danceability", 
            "valence", 
            "tempo",
            "acousticness", 
            "instrumentalness",
            ]
SAMPLING_TEMPERATURE = 0.5

TOP_K = 25 # Total de canciones a devolver por recomendación

CANDIDATE_POOL = 200 # Tamaño de pool para samplear

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
    """
    Obtiene recomendaciones de canciones a través del cálculo de las distancias al cuadrado  
    con una ponderación entre el perfil acústico del usuario y un MOOD
    Args:
        tracks: Catálogo completo de canciones con sus features acústicos.
        acoustic_profile: Perfil acústico del usuario persistido en BD.
        mood: Estado de ánimo del usuario
    Returns:
        Dict {"tracks": Lista de dicts {"id": str, "distance": float} ordenada de menor a mayor distancia.
        "query_params": Targets acústicos ponderados para obtener la recomendación.
    """
    t_min = acoustic_profile["tempo_range"]["min"]
    t_max = acoustic_profile["tempo_range"]["max"]

    t_range = t_max - t_min if (t_max - t_min) > 0 else 1

    # Se añade dinámicamente el target de tempo desnormalizado al perfil acústico del usuario
    acoustic_profile_copy = acoustic_profile.copy()
    acoustic_profile_copy["tempo"] = {
        "target": 0.5
    }

    matrix = np.empty((len(tracks), len(FEATURES)), dtype=np.float32)
    ids = []

    for i, track in enumerate(tracks):
        af = track["acoustic_features"]

        normalized_tempo = (af["tempo"] - t_min) / t_range

        # Añadir clamping en caso para valores negativos y superiores a 1
        normalized_tempo = max(0.0, min(1.0, normalized_tempo))

        matrix[i] = (
            af["energy"],
            af["danceability"],
            af["valence"],
            normalized_tempo,
            af["acousticness"],
            af["instrumentalness"],
        )

        ids.append(str(track["_id"]))

    blended = _blend_targets(acoustic_profile_copy, mood)

    # float32 para consistencia con la matrix y reducir uso de memoria
    features_arr = np.array([blended[f] for f in FEATURES], dtype=np.float32)

    # Distancia al cuadrado; el ranking es equivalente a euclidiana y evita la raíz cuadrada
    distances = np.sum((matrix - features_arr) ** 2, axis=1)

    # Implementar sampling
    pool_size = min(CANDIDATE_POOL, len(distances))

    candidate_idx = np.argpartition(
        distances, 
        pool_size - 1
    )[:pool_size]

    candidate_distances = distances[candidate_idx]

    scores = 1 / (candidate_distances + 1e-4)

    weights = scores ** (1 / SAMPLING_TEMPERATURE)

    if np.isinf(weights).any():
        # Reemplaza los infinitos por el valor máximo representable en float32
        weights = np.where(np.isinf(weights), np.finfo(np.float32).max, weights)

    probabilities = weights / weights.sum()
    logger.info(probabilities)
    logger.info(matrix[candidate_idx])

    selected_idx = np.random.choice(
        candidate_idx,
        size=min(TOP_K, len(candidate_idx)),
        replace=False,
        p=probabilities
    )

    sorted_idx = selected_idx[np.argsort(distances[selected_idx])]

    selected_acoustic_features = matrix[selected_idx]

    min_norm_tempo = np.min(selected_acoustic_features[:, 3])
    max_norm_tempo = np.max(selected_acoustic_features[:, 3])

    return {
        "tracks": [ {
            "id": ids[i],
            "distance": float(distances[i]) 
        }
        for i in sorted_idx],
        "query_params": {
            "energy": {
                "min": np.min(selected_acoustic_features[:, 0]),
                "max": np.max(selected_acoustic_features[:, 0]),
            },
            "danceability": {
                "min": np.min(selected_acoustic_features[:, 1]),
                "max": np.max(selected_acoustic_features[:, 1]),
            },
            "valence": {
                "min": np.min(selected_acoustic_features[:, 2]),
                "max": np.max(selected_acoustic_features[:, 2]),
            },
            "tempo": {
                "min": float(t_range * min_norm_tempo + t_min),
                "max": float(t_range * max_norm_tempo + t_min),
            },
        }
    }

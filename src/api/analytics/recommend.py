from logging import Logger
import logging

from analytics.user_feedback import UserFeedback
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
SAMPLING_TEMPERATURE = 4

TOP_K = 25 # Total de canciones a devolver por recomendación

CANDIDATE_POOL = 200 # Tamaño de pool para samplear

ELITE_RATIO = 0.2

RECENT_PENALTY = 3

FEEDBACK_PENALIZATION = {
    UserFeedback.LIKE.value: 0.75,
    UserFeedback.SKIP.value: 1.15,
    UserFeedback.DISLIKE.value: 2.0,

}

elite_size = max(
    3,
    int(TOP_K * ELITE_RATIO)
)

logger = logging.getLogger(__name__)

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

def get_tracks_recommendations(
        tracks: list[dict], 
        acoustic_profile: dict, 
        mood: Mood,
        recent_track_ids: list[str],
        feedback_map: dict,
    ):
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

    # Penalizaciones
    for i, track_id in enumerate(ids):
        
        # Repetición
        if track_id in recent_track_ids:
            distances[i] *= RECENT_PENALTY
        
        # feedback
        if track_id in feedback_map.keys():
            feedback = feedback_map[track_id]
            if feedback == UserFeedback.LIKE.value:
                distances[i] *= FEEDBACK_PENALIZATION[UserFeedback.LIKE.value]
            elif feedback == UserFeedback.SKIP.value:
                distances[i] *= FEEDBACK_PENALIZATION[UserFeedback.SKIP.value]
            elif feedback == UserFeedback.DISLIKE.value:
                distances[i] *= FEEDBACK_PENALIZATION[UserFeedback.DISLIKE.value]


    # Implementar sampling
    pool_size = min(CANDIDATE_POOL, len(distances))

    candidate_idx = np.argpartition(
        distances, 
        pool_size - 1
    )[:pool_size]

    candidate_sorted = candidate_idx[
        np.argsort(distances[candidate_idx])
    ]

    # Elite fijo
    elite_idx = candidate_sorted[:elite_size]

    # Candidatos restantes
    remaining_candidates = candidate_sorted[elite_size:]

    remaining_distances = distances[remaining_candidates]

    # Softmax invertido
    scores = np.exp(
        -remaining_distances / SAMPLING_TEMPERATURE
    )

    probabilities = scores / scores.sum()

    sample_size = min(
        TOP_K - elite_size,
        len(remaining_candidates)
    )

    sampled_idx = np.random.choice(
        remaining_candidates,
        size=sample_size,
        replace=False,
        p=probabilities
    )

    selected = []

    remaining = list(sampled_idx)

    while len(selected) < TOP_K - elite_size:

        best_idx = None
        best_score = -np.inf

        for idx in remaining:

            relevance = -distances[idx]

            diversity_penalty = 0

            similarities = []
            if selected:

                for s in selected:
                    sim = np.dot(matrix[idx], matrix[s]) / (
                        np.linalg.norm(matrix[idx]) * np.linalg.norm(matrix[s])
                    )

                    similarities.append(sim)

                diversity_penalty = (
                    0.3 * max(similarities)
                )

            score = (
                relevance
                - diversity_penalty
            )

            if score > best_score:
                best_score = score
                best_idx = idx

        selected.append(best_idx)
        remaining.remove(best_idx)

    final_idx = np.concatenate([
        elite_idx,
        np.array(selected, dtype=np.intp)
    ])

    # Orden final
    sorted_idx = final_idx[
        np.argsort(distances[final_idx])
    ]

    selected_acoustic_features = matrix[sorted_idx]

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

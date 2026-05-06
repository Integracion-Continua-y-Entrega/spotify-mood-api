import pandas as pd
from models.user import AcousticParam, AcousticParamRange, AcousticProfile, Preferences


def calculate_user_preferences(tracks: list[dict]) -> Preferences:
    if not tracks:
        raise ValueError("No tracks provided to calculate preferences")

    # Extraer acoustic_features (ya es dict gracias a model_dump)
    features = [t["acoustic_features"] for t in tracks if t.get("acoustic_features")]
    df = pd.DataFrame(features)

    # Géneros: aplanar lista de listas y tomar los top 5
    all_genres = [genre for t in tracks for genre in (t.get("genre") or [])]
    top_genres = (
        pd.Series(all_genres).value_counts().head(5).index.tolist()
        if all_genres else None
    )

    # Idioma más frecuente
    languages = [t["language"] for t in tracks if t.get("language")]
    top_language = (
        pd.Series(languages).value_counts().idxmax()
        if languages else None
    )

    def make_param(col: str) -> AcousticParam:
        return AcousticParam(
            target=round(df[col].mean(), 4),
            min=round(df[col].min(), 4),
            max=round(df[col].max(), 4),
        )

    return Preferences(
        favorite_genres=top_genres,
        language=top_language,
        acoustic_profile=AcousticProfile(
            energy=make_param("energy"),
            danceability=make_param("danceability"),
            valence=make_param("valence"),
            acousticness=make_param("acousticness"),
            instrumentalness=make_param("instrumentalness"),
            tempo_range=AcousticParamRange(
                min=round(df["tempo"].min(), 4),
                max=round(df["tempo"].max(), 4),
            ),
        ),
    )
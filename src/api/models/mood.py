from enum import Enum


class Mood(str, Enum):
    happy = "happy"
    relaxed = "relaxed"
    melancholic = "melancholic"
    energetic = "energetic"
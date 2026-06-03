from enum import Enum

class UserFeedback(str, Enum):
    LIKE = "like"
    DISLIKE = "dislike"
    SKIP = "skip"

from datetime import datetime
from enum import Enum
from zoneinfo import ZoneInfo

class TimeOfDay(str, Enum):
    MORNING   = "morning"    # 05:00 – 11:59
    AFTERNOON = "afternoon"  # 12:00 – 17:59
    EVENING   = "evening"    # 18:00 – 21:59
    NIGHT     = "night"      # 22:00 – 04:59

def get_time_of_day(dt: datetime | None = None) -> TimeOfDay:
    """Clasifica la hora local del servidor en uno de los 4 períodos del día."""
    hour = (dt or datetime.now(ZoneInfo("America/Mexico_City"))).hour

    if 5 <= hour < 12:
        return TimeOfDay.MORNING
    elif 12 <= hour < 18:
        return TimeOfDay.AFTERNOON
    elif 18 <= hour < 22:
        return TimeOfDay.EVENING
    else:
        return TimeOfDay.NIGHT
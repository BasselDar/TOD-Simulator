from typing import Dict, List, Tuple, NamedTuple
from enum import Enum

class TransitType(Enum):
    METRO = "🚇 Metro"
    BUS = "🚌 Bus"
    TRAM = "🚊 Tram"
    TRAIN = "🚂 Train"
    FERRY = "⛴️ Ferry"
    MINIBUS = "🚐 Minibus"
    FUTURE = "🏗️ Planned"

class TransitStation(NamedTuple):
    lat: float
    lon: float
    name: str
    type: TransitType
    line: str
    status: str = "Operational"  # Operational, Under Construction, Planned
    frequency: int = 0  # Service frequency in minutes (0 if unknown)

def get_cairo_transit_data() -> List[TransitStation]:
    return [
        # Metro Stations
        TransitStation(30.0444, 31.2357, "Sadat", TransitType.METRO, "Line 1", "Operational", 3),
        TransitStation(30.0561, 31.2394, "Ramses", TransitType.METRO, "Line 1", "Operational", 3),
        # Add more metro stations...

        # Bus Terminals
        TransitStation(30.0512, 31.2412, "Tahrir Bus Terminal", TransitType.BUS, "Multiple", "Operational", 10),
        TransitStation(30.0623, 31.2458, "Ramses Bus Station", TransitType.BUS, "Multiple", "Operational", 15),
        # Add more bus stations...

        # Minibus Stops
        TransitStation(30.0478, 31.2332, "Downtown Minibus Stop", TransitType.MINIBUS, "Multiple", "Operational", 5),
        # Add more minibus stops...
    ]

def get_alexandria_transit_data() -> List[TransitStation]:
    return [
        # Tram Stations
        TransitStation(31.1990, 29.9055, "Misr Station", TransitType.TRAM, "Raml Line", "Operational", 8),
        TransitStation(31.1967, 29.8937, "Sidi Gaber", TransitType.TRAIN, "Main Line", "Operational", 30),
        # Add more stations...
    ]

# Add more cities...

TRANSIT_DATA: Dict[str, List[TransitStation]] = {
    "Cairo": get_cairo_transit_data(),
    "Alexandria": get_alexandria_transit_data(),
    # Add other cities...
} 
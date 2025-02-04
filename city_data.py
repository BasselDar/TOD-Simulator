from src.transit_data import TransitType, TransitStation
from src.spatial_analysis import SpatialAnalyzer

# Expanded city boundaries to ensure full coverage
CITY_PRESETS = {
    "Cairo": {
        'north': 30.3500,  # Extended north to cover New Cairo and Shorouk
        'south': 29.8500,  # Extended south to cover Helwan and 15th of May
        'east': 31.7000,   # Extended east to cover New Cairo and future developments
        'west': 31.0500    # Extended west to cover 6th of October City
    },
    "Alexandria": {
        'north': 31.4000,  # Extended to cover northern coast
        'south': 31.0500,  # Extended south
        'east': 30.1500,   # Extended east
        'west': 29.7500    # Extended west to cover Borg El Arab
    },
    "Giza": {
        'north': 30.1500,  # Extended north
        'south': 29.9000,  # Extended south to cover all pyramids
        'east': 31.3000,   # Extended east
        'west': 31.0000    # Extended west
    },
    "Luxor": {
        'north': 25.8000,  # Extended to cover all temples
        'south': 25.6000,  # Extended south
        'east': 32.7500,   # Extended east
        'west': 32.5500    # Extended west to cover Valley of Kings
    },
    "Aswan": {
        'north': 24.2000,  # Extended north
        'south': 24.0000,  # Extended south
        'east': 33.0000,   # Extended east
        'west': 32.8000    # Extended west
    },
    "Port Said": {
        'north': 31.3500,  # Extended north to cover port
        'south': 31.1500,  # Extended south
        'east': 32.4500,   # Extended east
        'west': 32.2000    # Extended west
    },
    "Hurghada": {
        'north': 27.4000,  # Extended north
        'south': 27.1000,  # Extended south
        'east': 33.9000,   # Extended east to cover resorts
        'west': 33.7000    # Extended west
    },
    "New Administrative Capital": {
        'north': 30.1000,  # Extended north
        'south': 29.9500,  # Extended south
        'east': 31.9000,   # Extended east
        'west': 31.6500    # Extended west
    },
    "Damietta": {
        'north': 31.5000,  # Extended north to cover port
        'south': 31.3500,  # Extended south
        'east': 31.9000,   # Extended east
        'west': 31.7500    # Extended west
    },
    "Mansoura": {
        'north': 31.1000,  # Extended north
        'south': 30.9500,  # Extended south
        'east': 31.4500,   # Extended east
        'west': 31.3000    # Extended west
    },
    "Tanta": {
        'north': 30.8500,  # Extended north
        'south': 30.7000,  # Extended south
        'east': 31.1000,   # Extended east
        'west': 30.9000    # Extended west
    },
    "Suez": {
        'north': 30.0500,  # Extended north
        'south': 29.9000,  # Extended south
        'east': 32.6500,   # Extended east
        'west': 32.4500    # Extended west
    },
    "Ismailia": {
        'north': 30.6500,  # Extended north
        'south': 30.5000,  # Extended south
        'east': 32.3500,   # Extended east
        'west': 32.2000    # Extended west
    },
    "Custom": None
}

# City information with emojis and details
CITY_INFO = {
    "Cairo": "🏛️ Capital | 👥 20M | 🚇 3 Metro Lines",
    "Alexandria": "🌊 Mediterranean Port | 👥 5.2M | 🚊 Tram",
    "Giza": "🔺 Pyramids | 👥 3.8M | 🚇 Metro Connection",
    "Luxor": "🏺 Ancient Thebes | 👥 506K | ⛴️ Nile Transport",
    "Aswan": "💧 High Dam | 👥 290K | ⛴️ River Hub",
    "Port Said": "🚢 Suez Canal | 👥 749K | 🚢 Maritime Hub",
    "Hurghada": "🏖️ Red Sea Resort | 👥 248K | ✈️ Airport",
    "New Administrative Capital": "🏗️ New Capital | 🚄 HSR | 🌱 Smart City",
    "Damietta": "🚢 Port City | 👥 330K | 🏭 Industry Hub",
    "Mansoura": "🎓 University City | 👥 480K | 🏥 Medical",
    "Tanta": "🌆 Delta City | 👥 421K | 🚂 Rail Junction",
    "Suez": "🚢 Canal City | 👥 728K | 🏭 Industry",
    "Ismailia": "🌳 Garden City | 👥 366K | ⚓ Canal Admin"
}

def get_transit_nodes(selected_city):
    """Get transit stations for each city"""
    # Get city bounds
    city_bounds = CITY_PRESETS.get(selected_city)
    if not city_bounds:
        return [
            TransitStation(30.0444, 31.2357, "Custom Station 1", TransitType.BUS, "Custom Line", "Planned", 0),
            TransitStation(30.0561, 31.2394, "Custom Station 2", TransitType.BUS, "Custom Line", "Planned", 0),
        ]
    
    # Initialize spatial analyzer with city bounds
    analyzer = SpatialAnalyzer(city_bounds)
    
    try:
        # Try to load OSM data first
        osm_stations = analyzer.load_osm_transit_data()
        if osm_stations:
            return osm_stations
    except Exception as e:
        print(f"Error loading OSM data: {e}")
        print("Falling back to predefined stations")
    
    # Fall back to predefined stations if OSM data fails or is empty
    transit_data = {
        "Cairo": [
            # Metro Line 1 (Blue) - Helwan to New El-Marg
            TransitStation(29.8491, 31.3347, "Helwan", TransitType.METRO, "Line 1", "Operational", 3),
            TransitStation(29.8711, 31.3250, "Ain Helwan", TransitType.METRO, "Line 1", "Operational", 3),
            TransitStation(29.9071, 31.2972, "Maadi", TransitType.METRO, "Line 1", "Operational", 3),
            TransitStation(30.0444, 31.2357, "Sadat", TransitType.METRO, "Line 1", "Operational", 3),
            TransitStation(30.0561, 31.2394, "Ramses", TransitType.METRO, "Line 1", "Operational", 3),
            TransitStation(30.0722, 31.2824, "Heliopolis", TransitType.METRO, "Line 1", "Operational", 3),
            TransitStation(30.0832, 31.2928, "Ain Shams", TransitType.METRO, "Line 1", "Operational", 3),
            TransitStation(30.1312, 31.3248, "El-Marg", TransitType.METRO, "Line 1", "Operational", 3),
            TransitStation(30.1392, 31.3385, "New El-Marg", TransitType.METRO, "Line 1", "Operational", 3),
            
            # Metro Line 2 (Red) - Shubra to Monib
            TransitStation(30.1134, 31.2454, "Shubra El-Kheima", TransitType.METRO, "Line 2", "Operational", 3),
            TransitStation(30.0819, 31.2453, "Shubra", TransitType.METRO, "Line 2", "Operational", 3),
            TransitStation(30.0728, 31.2841, "Road El-Farag", TransitType.METRO, "Line 2", "Operational", 3),
            TransitStation(30.0561, 31.2394, "Ramses", TransitType.METRO, "Line 2", "Operational", 3),
            TransitStation(30.0444, 31.2357, "Sadat", TransitType.METRO, "Line 2", "Operational", 3),
            TransitStation(30.0419, 31.2453, "Dokki", TransitType.METRO, "Line 2", "Operational", 3),
            TransitStation(30.0147, 31.2045, "Cairo University", TransitType.METRO, "Line 2", "Operational", 3),
            TransitStation(29.9809, 31.2008, "Monib", TransitType.METRO, "Line 2", "Operational", 3),
            
            # Metro Line 3 (Green) - Airport to Kit Kat
            TransitStation(30.1119, 31.3997, "Airport", TransitType.METRO, "Line 3", "Operational", 4),
            TransitStation(30.0812, 31.2901, "Haroun", TransitType.METRO, "Line 3", "Operational", 4),
            TransitStation(30.0733, 31.2789, "Heliopolis Square", TransitType.METRO, "Line 3", "Operational", 4),
            TransitStation(30.0515, 31.2495, "Attaba", TransitType.METRO, "Line 3", "Operational", 4),
            TransitStation(30.0444, 31.2357, "Nasser", TransitType.METRO, "Line 3", "Operational", 4),
            TransitStation(30.0419, 31.2123, "Kit Kat", TransitType.METRO, "Line 3", "Operational", 4),
            
            # Major Bus Terminals
            TransitStation(30.0512, 31.2412, "Tahrir Bus Terminal", TransitType.BUS, "Multiple Lines", "Operational", 10),
            TransitStation(30.0623, 31.2458, "Ramses Bus Station", TransitType.BUS, "Multiple Lines", "Operational", 15),
            TransitStation(30.0478, 31.2332, "Downtown Terminal", TransitType.BUS, "City Lines", "Operational", 8),
            TransitStation(30.0712, 31.2812, "Heliopolis Bus Terminal", TransitType.BUS, "Multiple Lines", "Operational", 12),
            TransitStation(30.1119, 31.3997, "Airport Bus Station", TransitType.BUS, "Airport Lines", "Operational", 20),
            TransitStation(30.0147, 31.2045, "Cairo University Terminal", TransitType.BUS, "University Lines", "Operational", 10),
            TransitStation(29.9691, 31.2591, "Maadi Bus Terminal", TransitType.BUS, "Southern Lines", "Operational", 15),
            
            # Train Stations
            TransitStation(30.0561, 31.2467, "Ramses Railway", TransitType.TRAIN, "National Rail", "Operational", 30),
            TransitStation(30.1119, 31.3997, "Airport Link", TransitType.TRAIN, "Airport Express", "Under Construction", 15),
            TransitStation(30.1123, 31.3101, "Ain Shams Railway", TransitType.TRAIN, "Regional Rail", "Operational", 45),
            TransitStation(30.0733, 31.2789, "Heliopolis Railway", TransitType.TRAIN, "Regional Rail", "Operational", 40),
            
            # Future Metro Stations (Line 4)
            TransitStation(30.0289, 31.2111, "6th of October", TransitType.METRO, "Line 4", "Planned", 5),
            TransitStation(30.0444, 31.2357, "Downtown", TransitType.METRO, "Line 4", "Planned", 5),
            TransitStation(30.0733, 31.2789, "Nasr City", TransitType.METRO, "Line 4", "Planned", 5),
            
            # Monorail Stations
            TransitStation(30.0175, 31.7488, "New Capital Station", TransitType.TRAIN, "Monorail", "Under Construction", 8),
            TransitStation(30.0234, 31.5456, "Future City", TransitType.TRAIN, "Monorail", "Under Construction", 8),
            TransitStation(30.0112, 31.4502, "Sports City", TransitType.TRAIN, "Monorail", "Under Construction", 8),
        ],
        "Alexandria": [
            # Main Railway Stations
            TransitStation(31.1990, 29.9055, "Alexandria Main Station", TransitType.TRAIN, "Main Line", "Operational", 30),
            TransitStation(31.1967, 29.8937, "Sidi Gaber", TransitType.TRAIN, "Main Line", "Operational", 30),
            TransitStation(31.2067, 29.9137, "Misr Station", TransitType.TRAIN, "Regional", "Operational", 45),
            
            # Tram System
            TransitStation(31.1984, 29.9191, "Raml Station", TransitType.TRAM, "Raml Line", "Operational", 8),
            TransitStation(31.2001, 29.9089, "Mansheya", TransitType.TRAM, "Raml Line", "Operational", 8),
            TransitStation(31.2142, 29.9425, "San Stefano", TransitType.TRAM, "Raml Line", "Operational", 8),
            TransitStation(31.2234, 29.9542, "Sporting", TransitType.TRAM, "Raml Line", "Operational", 8),
            TransitStation(31.2134, 29.9442, "Cleopatra", TransitType.TRAM, "Raml Line", "Operational", 8),
            TransitStation(31.2034, 29.9342, "Saba Pasha", TransitType.TRAM, "Raml Line", "Operational", 8),
            
            # Bus Terminals
            TransitStation(31.1984, 29.9091, "Downtown Terminal", TransitType.BUS, "City Lines", "Operational", 10),
            TransitStation(31.2084, 29.9291, "East Terminal", TransitType.BUS, "Regional", "Operational", 15),
            
            # Ferry Terminals
            TransitStation(31.2023, 29.8854, "Port Terminal", TransitType.FERRY, "Port Line", "Operational", 60),
            TransitStation(31.1989, 29.8789, "Abu Qir Ferry", TransitType.FERRY, "Abu Qir Line", "Operational", 45),
            TransitStation(31.2123, 29.8954, "Western Harbor", TransitType.FERRY, "Harbor Line", "Operational", 30),
        ],
        "Luxor": [
            TransitStation(25.6995, 32.6421, "Luxor Railway Station", TransitType.TRAIN, "Upper Egypt Line", "Operational", 120),
            TransitStation(25.7051, 32.6381, "Luxor Ferry Terminal", TransitType.FERRY, "Nile Line", "Operational", 30),
            TransitStation(25.6912, 32.6367, "Karnak Temple Stop", TransitType.BUS, "Tourist Line", "Operational", 20),
            TransitStation(25.7151, 32.6481, "East Bank Terminal", TransitType.BUS, "City Lines", "Operational", 15),
            TransitStation(25.7251, 32.6281, "West Bank Ferry", TransitType.FERRY, "West Bank Line", "Operational", 20),
            TransitStation(25.7351, 32.6381, "Airport Express", TransitType.BUS, "Airport Line", "Operational", 30),
        ],
        "Aswan": [
            TransitStation(24.0891, 32.8985, "Aswan Railway Station", TransitType.TRAIN, "Upper Egypt Line", "Operational", 120),
            TransitStation(24.0876, 32.8894, "Aswan Ferry Port", TransitType.FERRY, "Nile Line", "Operational", 30),
            TransitStation(24.0902, 32.8877, "City Center Terminal", TransitType.BUS, "City Line", "Operational", 15),
            TransitStation(24.0991, 32.8877, "High Dam Station", TransitType.BUS, "Dam Line", "Operational", 20),
            TransitStation(24.0851, 32.8987, "Philae Temple Terminal", TransitType.FERRY, "Temple Line", "Operational", 45),
            TransitStation(24.0791, 32.8887, "Airport Terminal", TransitType.BUS, "Airport Line", "Operational", 30),
        ],
        "Port Said": [
            TransitStation(31.2571, 32.2887, "Port Said Station", TransitType.TRAIN, "Delta Line", "Operational", 60),
            TransitStation(31.2654, 32.3024, "Maritime Terminal", TransitType.FERRY, "Port Line", "Operational", 120),
            TransitStation(31.2589, 32.2935, "City Center Hub", TransitType.BUS, "City Line", "Operational", 15),
            TransitStation(31.2671, 32.3124, "Port Terminal", TransitType.BUS, "Port Line", "Operational", 20),
            TransitStation(31.2754, 32.2924, "East District", TransitType.BUS, "District Line", "Operational", 15),
            TransitStation(31.2554, 32.3124, "Free Zone Terminal", TransitType.BUS, "Zone Line", "Operational", 30),
        ],
        "New Administrative Capital": [
            TransitStation(30.0175, 31.7488, "High-Speed Rail Terminal", TransitType.TRAIN, "Express Line", "Under Construction", 30),
            TransitStation(30.0234, 31.7456, "Central Business District", TransitType.METRO, "NAC Line", "Planned", 5),
            TransitStation(30.0112, 31.7502, "Government District", TransitType.BUS, "Gov Line", "Operational", 10),
            TransitStation(30.0198, 31.7399, "Monorail Station", TransitType.TRAIN, "Monorail", "Under Construction", 8),
            TransitStation(30.0298, 31.7499, "Residential District", TransitType.BUS, "District Line", "Operational", 15),
            TransitStation(30.0398, 31.7599, "Sports City", TransitType.BUS, "Sports Line", "Under Construction", 20),
            TransitStation(30.0498, 31.7699, "Knowledge City", TransitType.BUS, "Education Line", "Planned", 15),
        ],
        "Damietta": [
            TransitStation(31.4178, 31.8146, "Damietta Railway", TransitType.TRAIN, "Delta Line", "Operational", 60),
            TransitStation(31.4256, 31.8092, "Port Terminal", TransitType.BUS, "Port Line", "Operational", 20),
            TransitStation(31.4167, 31.8081, "City Center", TransitType.BUS, "City Line", "Operational", 15),
            TransitStation(31.4289, 31.8154, "New Damietta", TransitType.BUS, "Coastal Line", "Operational", 30),
            TransitStation(31.4201, 31.8167, "Maritime Port", TransitType.FERRY, "Port Line", "Operational", 60),
            TransitStation(31.4301, 31.8267, "Furniture City", TransitType.BUS, "Industrial Line", "Operational", 25),
        ],
        "Mansoura": [
            TransitStation(31.0375, 31.3846, "Mansoura Station", TransitType.TRAIN, "Delta Line", "Operational", 45),
            TransitStation(31.0412, 31.3812, "University Terminal", TransitType.BUS, "Campus Line", "Operational", 10),
            TransitStation(31.0389, 31.3789, "City Center", TransitType.BUS, "City Line", "Operational", 15),
            TransitStation(31.0401, 31.3867, "Medical Complex", TransitType.BUS, "Hospital Line", "Operational", 12),
            TransitStation(31.0356, 31.3834, "River Port", TransitType.FERRY, "Nile Line", "Operational", 45),
            TransitStation(31.0456, 31.3934, "New Mansoura", TransitType.BUS, "Coastal Line", "Under Construction", 20),
        ],
        "Tanta": [
            TransitStation(30.7867, 31.0012, "Tanta Railway", TransitType.TRAIN, "Delta Line", "Operational", 30),
            TransitStation(30.7889, 30.9987, "Central Station", TransitType.BUS, "City Line", "Operational", 15),
            TransitStation(30.7845, 31.0034, "University Stop", TransitType.BUS, "Campus Line", "Operational", 12),
            TransitStation(30.7901, 30.9967, "Market Terminal", TransitType.BUS, "Market Line", "Operational", 20),
            TransitStation(30.7945, 31.0134, "Medical Center", TransitType.BUS, "Hospital Line", "Operational", 15),
            TransitStation(30.7967, 30.9912, "Industrial Zone", TransitType.BUS, "Industry Line", "Operational", 25),
        ],
        "Suez": [
            TransitStation(29.9867, 32.5487, "Suez Station", TransitType.TRAIN, "Canal Line", "Operational", 60),
            TransitStation(29.9789, 32.5412, "Port Terminal", TransitType.BUS, "Port Line", "Operational", 20),
            TransitStation(29.9845, 32.5389, "City Center", TransitType.BUS, "City Line", "Operational", 15),
            TransitStation(29.9912, 32.5467, "Industrial Zone", TransitType.BUS, "Industry Line", "Operational", 30),
            TransitStation(29.9834, 32.5512, "Maritime Port", TransitType.FERRY, "Canal Line", "Operational", 45),
            TransitStation(29.9934, 32.5612, "Economic Zone", TransitType.BUS, "SEZONE Line", "Operational", 25),
        ],
        "Ismailia": [
            TransitStation(30.5923, 32.2789, "Ismailia Station", TransitType.TRAIN, "Canal Line", "Operational", 45),
            TransitStation(30.5889, 32.2812, "City Center", TransitType.BUS, "City Line", "Operational", 15),
            TransitStation(30.5912, 32.2867, "University Terminal", TransitType.BUS, "Campus Line", "Operational", 12),
            TransitStation(30.5945, 32.2834, "Canal Authority", TransitType.BUS, "Canal Line", "Operational", 20),
            TransitStation(30.5878, 32.2889, "Lake Terminal", TransitType.FERRY, "Lake Line", "Operational", 60),
            TransitStation(30.5978, 32.2989, "Technology Valley", TransitType.BUS, "Tech Line", "Under Construction", 25),
        ],
        "Hurghada": [
            TransitStation(27.2579, 33.8116, "Hurghada Bus Station", TransitType.BUS, "City Line", "Operational", 20),
            TransitStation(27.1841, 33.7995, "Airport Terminal", TransitType.BUS, "Airport Line", "Operational", 30),
            TransitStation(27.2317, 33.8115, "Marina Terminal", TransitType.FERRY, "Marina Line", "Operational", 60),
            TransitStation(27.2417, 33.8215, "Sakkala Terminal", TransitType.BUS, "Tourist Line", "Operational", 15),
            TransitStation(27.2517, 33.8315, "El Dahar Station", TransitType.BUS, "Market Line", "Operational", 20),
            TransitStation(27.2617, 33.8415, "New Hurghada", TransitType.BUS, "Coastal Line", "Under Construction", 25),
        ],
        "Custom": [
            TransitStation(30.0444, 31.2357, "Custom Station 1", TransitType.BUS, "Custom Line", "Planned", 0),
            TransitStation(30.0561, 31.2394, "Custom Station 2", TransitType.BUS, "Custom Line", "Planned", 0),
        ]
    }
    
    return transit_data.get(selected_city, []) 
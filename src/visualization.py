import folium
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Tuple, Optional
import numpy as np
from src.transit_data import TransitType, TransitStation

class TODVisualizer:
    def __init__(self, center, bounds):
        self.city_center = center
        self.city_bounds = bounds
        self.transit_stations = []
        self.buffer_distances = {}
        self.buffer_opacities = {}
        
        # Load stations from egypt_osm file
        self.load_stations_from_file()
        
    def load_stations_from_file(self):
        """Load transit stations from egypt_osm file."""
        try:
            import geopandas as gpd
            from shapely.geometry import Point
            
            # Load all relevant transport data
            transport_points = gpd.read_file('src/egypt_osm/gis_osm_transport_free_1.shp')
            transport_areas = gpd.read_file('src/egypt_osm/gis_osm_transport_a_free_1.shp')
            railways = gpd.read_file('src/egypt_osm/gis_osm_railways_free_1.shp')
            traffic = gpd.read_file('src/egypt_osm/gis_osm_traffic_free_1.shp')
            
            print("\nAvailable data:")
            print(f"Transport points: {len(transport_points)}")
            print(f"Transport areas: {len(transport_areas)}")
            print(f"Railways: {len(railways)}")
            print(f"Traffic points: {len(traffic)}")
            
            # Filter to city bounds
            bounds = (
                self.city_bounds['west'],
                self.city_bounds['south'],
                self.city_bounds['east'],
                self.city_bounds['north']
            )
            
            def filter_by_bounds(gdf):
                return gdf.cx[bounds[0]:bounds[2], bounds[1]:bounds[3]]
            
            transport_points = filter_by_bounds(transport_points)
            transport_areas = filter_by_bounds(transport_areas)
            railways = filter_by_bounds(railways)
            traffic = filter_by_bounds(traffic)
            
            print("\nAfter filtering to city bounds:")
            print(f"Transport points: {len(transport_points)}")
            print(f"Transport areas: {len(transport_areas)}")
            print(f"Railways: {len(railways)}")
            print(f"Traffic points: {len(traffic)}")
            
            # Process transport points
            for _, row in transport_points.iterrows():
                station_type = self._determine_station_type(row)
                if station_type:
                    self.transit_stations.append(
                        TransitStation(
                            lat=row.geometry.y,
                            lon=row.geometry.x,
                            name=row.get('name', 'Unknown Station'),
                            type=station_type,
                            line=row.get('fclass', 'Unknown Line'),
                            status="Operational",
                            frequency=self._estimate_frequency(station_type)
                        )
                    )
            
            # Process transport areas (stations, terminals)
            for _, row in transport_areas.iterrows():
                station_type = self._determine_station_type(row)
                if station_type:
                    centroid = row.geometry.centroid
                    self.transit_stations.append(
                        TransitStation(
                            lat=centroid.y,
                            lon=centroid.x,
                            name=row.get('name', 'Unknown Station'),
                            type=station_type,
                            line=row.get('fclass', 'Unknown Line'),
                            status="Operational",
                            frequency=self._estimate_frequency(station_type)
                        )
                    )
            
            # Process railways (stations)
            for _, row in railways.iterrows():
                if row.get('fclass') in ['station', 'halt', 'stop']:
                    station_type = self._determine_station_type(row)
                    if station_type:
                        centroid = row.geometry.centroid
                        station = TransitStation(
                            lat=centroid.y,
                            lon=centroid.x,
                            name=row.get('name', 'Unknown Station'),
                            type=station_type,
                            line=row.get('fclass', 'Unknown Line'),
                            status="Operational",
                            frequency=self._estimate_frequency(station_type)
                        )
                        if not any(self._is_same_station(station, existing) for existing in self.transit_stations):
                            self.transit_stations.append(station)
            
            # Process traffic points (bus stops, etc)
            for _, row in traffic.iterrows():
                if row.get('fclass') in ['bus_stop', 'bus_station']:
                    station = TransitStation(
                        lat=row.geometry.y,
                        lon=row.geometry.x,
                        name=row.get('name', 'Unknown Station'),
                        type=TransitType.BUS,
                        line=row.get('fclass', 'Unknown Line'),
                        status="Operational",
                        frequency=15  # Default bus frequency
                    )
                    if not any(self._is_same_station(station, existing) for existing in self.transit_stations):
                        self.transit_stations.append(station)
            
            print(f"\nSuccessfully loaded {len(self.transit_stations)} stations from OSM data")
            
            # Print breakdown by type
            type_counts = {}
            for station in self.transit_stations:
                type_counts[station.type] = type_counts.get(station.type, 0) + 1
            print("\nStation types breakdown:")
            for t, count in type_counts.items():
                print(f"{t.value}: {count}")
            
        except Exception as e:
            print(f"Error loading stations from egypt_osm: {e}")
            print("Using default stations instead")
            self._load_default_stations()
    
    def _is_same_station(self, station1: TransitStation, station2: TransitStation, distance_threshold: float = 50) -> bool:
        """Check if two stations are the same (within 50m of each other)"""
        distance = self.calculate_distance(station1.lat, station1.lon, station2.lat, station2.lon)
        return distance <= distance_threshold
    
    def _determine_station_type(self, station_data) -> Optional[TransitType]:
        """Determine station type from OSM data with improved detection."""
        fclass = str(station_data.get('fclass', '')).lower()
        name = str(station_data.get('name', '')).lower()
        
        # Metro/Subway detection
        if any(term in name for term in ['metro', 'subway', 'underground', 'محطة', 'مترو']):
            return TransitType.METRO
        
        # Check for Arabic station names
        if 'محطة' in name:
            if any(term in name for term in ['قطار', 'سكة حديد']):
                return TransitType.TRAIN
            elif any(term in name for term in ['ترام']):
                return TransitType.TRAM
            elif any(term in name for term in ['اتوبيس', 'حافلة']):
                return TransitType.BUS
        
        # Map OSM classifications to transit types
        type_mapping = {
            'station': TransitType.TRAIN,
            'rail_station': TransitType.TRAIN,
            'railway_station': TransitType.TRAIN,
            'halt': TransitType.TRAIN,
            'tram_stop': TransitType.TRAM,
            'bus_stop': TransitType.BUS,
            'bus_station': TransitType.BUS,
            'ferry_terminal': TransitType.FERRY,
            'minibus': TransitType.MINIBUS
        }
        
        # Check both fclass and name for type indicators
        if fclass in type_mapping:
            return type_mapping[fclass]
        
        # Additional checks based on name
        if 'train' in name or 'railway' in name or 'rail' in name:
            return TransitType.TRAIN
        elif 'tram' in name:
            return TransitType.TRAM
        elif 'bus' in name:
            return TransitType.BUS
        elif 'ferry' in name or 'boat' in name:
            return TransitType.FERRY
        
        return None
    
    def _load_default_stations(self):
        """Load a set of default stations if file loading fails."""
        # Add some example stations for testing
        default_stations = [
            TransitStation("Central Station", self.city_center[0], self.city_center[1], 
                         TransitType.METRO, 5),
            # Add more default stations as needed
        ]
        self.transit_stations.extend(default_stations)
        print(f"Loaded {len(default_stations)} default stations")

    def get_transit_style(self, transit_type: TransitType) -> Dict:
        """Get styling for different transit types"""
        styles = {
            TransitType.METRO: {
                'color': '#E31E24',  # Bright red for metro
                'radius': 8,
                'icon': '🚇',
                'label': 'Metro Line'
            },
            TransitType.BUS: {
                'color': '#1E88E5',  # Bright blue for bus
                'radius': 6,
                'icon': '🚌',
                'label': 'Bus Route'
            },
            TransitType.TRAM: {
                'color': '#9B59B6',  # Bright purple for tram
                'radius': 7,
                'icon': '🚊',
                'label': 'Tram Line'
            },
            TransitType.TRAIN: {
                'color': '#FFA000',  # Dark orange for train
                'radius': 8,
                'icon': '🚂',
                'label': 'Train Line'
            },
            TransitType.FERRY: {
                'color': '#00ACC1',  # Cyan for ferry
                'radius': 7,
                'icon': '⛴️',
                'label': 'Ferry Route'
            },
            TransitType.MINIBUS: {
                'color': '#7B1FA2',  # Dark purple for minibus
                'radius': 5,
                'icon': '🚐',
                'label': 'Minibus Route'
            },
            TransitType.FUTURE: {
                'color': '#757575',  # Grey for future
                'radius': 6,
                'icon': '🏗️',
                'label': 'Planned Station'
            }
        }
        return styles.get(transit_type, styles[TransitType.BUS])

    def get_tod_score(self, distance_to_transit: float, walkability: float) -> float:
        """Calculate TOD score based on distance to transit and walkability"""
        if distance_to_transit > 800:  # More than 800m from transit
            return 0.2 * walkability / 100
        elif distance_to_transit > 500:  # 500-800m from transit
            return 0.5 * walkability / 100
        else:  # Within 500m of transit
            return walkability / 100

    def _add_tod_analysis_layer(self, m: folium.Map, land_use: Dict[str, np.ndarray], walkability_scores: np.ndarray, show_filters: Dict[str, bool]):
        """Add TOD score visualization with accurate urban mix calculation."""
        tod_layer = folium.FeatureGroup(name='TOD Analysis')
        
        # Add padding to ensure full coverage (20% extra on each side)
        lat_padding = (self.city_bounds['north'] - self.city_bounds['south']) * 0.2
        lon_padding = (self.city_bounds['east'] - self.city_bounds['west']) * 0.2
        
        analysis_bounds = {
            'north': self.city_bounds['north'] + lat_padding,
            'south': self.city_bounds['south'] - lat_padding,
            'east': self.city_bounds['east'] + lon_padding,
            'west': self.city_bounds['west'] - lon_padding
        }
        
        lat_step = (analysis_bounds['north'] - analysis_bounds['south']) / walkability_scores.shape[0]
        lon_step = (analysis_bounds['east'] - analysis_bounds['west']) / walkability_scores.shape[1]
        
        # Pre-calculate cell centers and corners for better accuracy
        def get_cell_bounds(lat, lon):
            """Get all corners and center of the cell for better station detection"""
            corners = [
                (lat, lon),  # SW
                (lat + lat_step, lon),  # NW
                (lat + lat_step, lon + lon_step),  # NE
                (lat, lon + lon_step),  # SE
                (lat + lat_step/2, lon + lon_step/2)  # Center
            ]
            return corners
        
        # Only use stations that are currently visible based on filters
        visible_stations = [station for station in self.transit_stations 
                          if show_filters.get(station.type.value.split(' ')[-1], True)]
        
        for i in range(walkability_scores.shape[0]):
            for j in range(walkability_scores.shape[1]):
                lat = analysis_bounds['south'] + i * lat_step
                lon = analysis_bounds['west'] + j * lon_step
                
                # Get all points to check for this cell
                check_points = get_cell_bounds(lat, lon)
                
                # Find nearest stations considering all cell points
                nearest_stations = set()  # Use set to avoid duplicates
                for check_lat, check_lon in check_points:
                    for station in visible_stations:  # Use filtered stations here
                        dist = self.calculate_distance(check_lat, check_lon, station.lat, station.lon)
                        if dist <= 1000:  # Consider stations within 1km from any point of the cell
                            nearest_stations.add((dist, station))
                
                # Convert set back to list and sort by distance
                nearest_stations = sorted(list(nearest_stations), key=lambda x: x[0])
                
                tod_score = 0
                if nearest_stations:
                    # Calculate score for each station type
                    type_scores = {}
                    for dist, station in nearest_stations:
                        # More generous distance-based score with smoother falloff
                        if dist <= 400:  # Primary catchment
                            distance_score = 100
                        elif dist <= 800:  # Secondary catchment
                            distance_score = 100 - ((dist - 400) / 4)  # Smooth falloff
                        else:  # Tertiary catchment
                            distance_score = 80 - ((dist - 800) / 5)  # Gentler falloff
                        
                        # Station type weights with better granularity
                        type_multiplier = {
                            TransitType.METRO: 1.0,
                            TransitType.TRAIN: 1.0,
                            TransitType.TRAM: 0.95,
                            TransitType.BUS: 0.9,
                            TransitType.MINIBUS: 0.85,
                            TransitType.FERRY: 0.9
                        }.get(station.type, 0.9)
                        
                        station_score = distance_score * type_multiplier
                        
                        # Keep best score for each type
                        current_type_score = type_scores.get(station.type, 0)
                        type_scores[station.type] = max(current_type_score, station_score)
                    
                    # Base score is the highest individual station score
                    tod_score = max(type_scores.values())
                    
                    # Enhanced bonus system for multiple types
                    unique_types = len(type_scores)
                    if unique_types > 1:
                        # Progressive bonus: 20% for 2 types, +15% for each additional type
                        bonus_multiplier = 1.0 + (0.2 + (unique_types - 2) * 0.15)
                        tod_score *= min(1.8, bonus_multiplier)  # Cap at 80% bonus
                    
                    # Special bonus for transit mix
                    has_rapid_transit = any(t in type_scores for t in [TransitType.METRO, TransitType.TRAIN])
                    has_local_transit = any(t in type_scores for t in [TransitType.BUS, TransitType.TRAM])
                    if has_rapid_transit and has_local_transit:
                        tod_score *= 1.25  # 25% bonus for good transit mix
                    
                    tod_score = min(100, tod_score)
                
                # Enhanced color scheme with much lower opacity
                if tod_score >= 75:
                    color = '#2ECC71'  # Green
                    category = "High TOD Potential"
                    opacity = 0.35  # Significantly reduced from 0.6
                elif tod_score >= 45:
                    color = '#F1C40F'  # Yellow
                    category = "Medium TOD Potential"
                    opacity = 0.25  # Significantly reduced from 0.4
                else:
                    color = '#E74C3C'  # Red
                    category = "Low TOD Potential"
                    opacity = 0.15  # Significantly reduced from 0.3
                
                # Enhanced popup with detailed mix information
                if nearest_stations:
                    closest_station = nearest_stations[0]
                    closest_distance = closest_station[0]
                    closest_name = closest_station[1].name
                    
                    # Calculate urban mix details with better categorization
                    rapid_transit = [s.type.name for _, s in nearest_stations 
                                   if s.type in [TransitType.METRO, TransitType.TRAIN]]
                    local_transit = [s.type.name for _, s in nearest_stations 
                                   if s.type in [TransitType.BUS, TransitType.TRAM]]
                    other_transit = [s.type.name for _, s in nearest_stations 
                                   if s.type not in [TransitType.METRO, TransitType.TRAIN, TransitType.BUS, TransitType.TRAM]]
                    
                    mix_details = []
                    if rapid_transit:
                        mix_details.append(f"🚊 Rapid Transit: {', '.join(rapid_transit)}")
                    if local_transit:
                        mix_details.append(f"🚌 Local Transit: {', '.join(local_transit)}")
                    if other_transit:
                        mix_details.append(f"🚐 Other Transit: {', '.join(other_transit)}")
                    
                    popup_html = f"""
                    <div style='font-family: Arial; font-size: 12px; padding: 10px;'>
                        <b>TOD Score:</b> {tod_score:.1f}/100
                        <br>
                        <b>Nearby Stations:</b> {len(nearest_stations)}
                        <br>
                        <b>Transit Mix:</b>
                        <br>
                        {'<br>'.join(mix_details) if mix_details else 'No transit mix'}
                        <br>
                        <b>Closest Station:</b> {closest_name} ({closest_distance:.0f}m)
                    </div>
                    """
                else:
                    popup_html = f"""
                    <div style='font-family: Arial; font-size: 12px; padding: 10px;'>
                        <b>TOD Score:</b> {tod_score:.1f}/100
                        <br>
                        <b>Nearby Stations:</b> 0
                        <br>
                        <b>Transit Mix:</b> None
                        <br>
                        <b>Closest Station:</b> None
                    </div>
                    """
                
                folium.Rectangle(
                    bounds=[(lat, lon), (lat + lat_step, lon + lon_step)],
                    color=color,
                    weight=1,
                    fill=True,
                    fill_opacity=opacity,
                    popup=folium.Popup(popup_html, max_width=250),
                    tooltip=f"{category} ({tod_score:.1f})"
                ).add_to(tod_layer)
        
        tod_layer.add_to(m)

    def calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points in meters"""
        from math import sin, cos, sqrt, atan2, radians
        
        R = 6371000  # Earth's radius in meters
        
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        
        return R * c
    
    def create_interactive_map(
        self,
        land_use: Dict[str, np.ndarray],
        transit_stations: List[TransitStation],
        walkability_scores: np.ndarray,
        show_filters: Dict[str, bool],
        buffer_distances: Dict[str, int],
        buffer_opacities: Dict[str, float]
    ) -> folium.Map:
        """Create interactive map with filters"""
        self.transit_stations = transit_stations
        self.buffer_distances = buffer_distances
        self.buffer_opacities = buffer_opacities
        
        # Create base map
        m = folium.Map(
            location=self.city_center,
            zoom_start=6 if self.city_center[0] == 26.8206 else 13,
            control_scale=True,
            prefer_canvas=True  # Better performance for many markers
        )
        
        # Add stations directly to map
        for station in transit_stations:
            # Strip emoji from type value to match filter keys
            station_type = station.type.value.split(' ')[-1]
            if show_filters.get(station_type, True):
                style = self.get_transit_style(station.type)
                
                # Add station marker
                folium.CircleMarker(
                    location=(station.lat, station.lon),
                    radius=style['radius'],
                    color=style['color'],
                    fill=True,
                    fill_color=style['color'],
                    fill_opacity=0.9,
                    popup=self._create_station_popup(station, style),
                    tooltip=f"{style['icon']} {station.name}"
                ).add_to(m)
                
                # Add walking radius if enabled
                if show_filters.get('show_walkability_radius', True):
                    folium.Circle(
                        location=(station.lat, station.lon),
                        radius=buffer_distances['primary'],
                        color=style['color'],
                        weight=1,
                        fill=True,
                        fill_color=style['color'],
                        fill_opacity=buffer_opacities['primary']
                    ).add_to(m)
        
        # Add TOD analysis if enabled
        if show_filters.get('show_tod_analysis', True):
            self._add_tod_analysis_layer(m, land_use, walkability_scores, show_filters)
        
        return m
    
    def create_dashboard_figures(self, land_use: Dict[str, np.ndarray], walkability_scores: np.ndarray) -> Dict[str, go.Figure]:
        """Create modern dashboard visualization figures"""
        figures = {}
        
        # Calculate land use percentages
        total_cells = land_use['residential'].size
        land_use_dist = {
            '🏘️ Residential': np.sum(land_use['residential']) / total_cells * 100,
            '🌳 Green Space': np.sum(land_use['green']) / total_cells * 100
        }
        
        # Create modern donut chart
        figures['land_use_dist'] = go.Figure(data=[go.Pie(
            labels=list(land_use_dist.keys()),
            values=list(land_use_dist.values()),
            hole=0.7,
            marker=dict(
                colors=['#FF8C77', '#2ECC71']
            ),
            textinfo='label+percent',
            textfont=dict(size=14),
            hovertemplate="<b>%{label}</b><br>" +
                          "Area: %{value:.1f}%<br>" +
                          "<extra></extra>"
        )])
        
        figures['land_use_dist'].update_layout(
            title={
                'text': 'Land Use Distribution',
                'y': 0.95,
                'x': 0.5,
                'xanchor': 'center',
                'yanchor': 'top',
                'font': dict(size=20)
            },
            showlegend=False,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(t=80, b=20, l=20, r=20),
            annotations=[{
                'text': 'Urban<br>Mix',
                'x': 0.5,
                'y': 0.5,
                'font_size': 16,
                'showarrow': False
            }]
        )
        
        return figures

    def _get_point_at_distance(self, lat: float, lon: float, distance: float, bearing: float) -> Tuple[float, float]:
        """Calculate a point at a given distance and bearing from start point"""
        from math import sin, cos, asin, radians, atan2, degrees, pi
        
        R = 6371000  # Earth's radius in meters
        
        lat1 = radians(lat)
        lon1 = radians(lon)
        bearing = radians(bearing)
        
        # Calculate new point
        lat2 = asin(
            sin(lat1) * cos(distance/R) +
            cos(lat1) * sin(distance/R) * cos(bearing)
        )
        
        lon2 = lon1 + atan2(
            sin(bearing) * sin(distance/R) * cos(lat1),
            cos(distance/R) - sin(lat1) * sin(lat2)
        )
        
        return (degrees(lat2), degrees(lon2)) 

    def _create_station_popup(self, station: TransitStation, style: Dict) -> folium.Popup:
        """Create a modern popup for a transit station"""
        popup_html = f"""
        <div style='font-family: Arial, sans-serif; padding: 12px; background: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>
            <h4 style="margin: 0 0 10px 0; color: {style['color']}; display: flex; align-items: center;">
                {style['icon']} <span style="margin-left: 8px;">{station.name}</span>
            </h4>
            <div style="display: grid; grid-template-columns: auto 1fr; gap: 5px;">
                <div style="color: #666;">Type:</div>
                <div style="font-weight: 500;">{station.type.value}</div>
                <div style="color: #666;">Service:</div>
                <div style="font-weight: 500;">{style['label']}</div>
                {f'<div style="color: #666;">Frequency:</div><div style="font-weight: 500;">Every {station.frequency} min</div>' if station.frequency else ''}
            </div>
        </div>
        """
        return folium.Popup(popup_html, max_width=300)

    def _estimate_frequency(self, station_type: TransitType) -> float:
        """Estimate service frequency in minutes based on station type."""
        base_frequencies = {
            TransitType.METRO: 5,    # Every 5 minutes
            TransitType.TRAIN: 20,   # Every 20 minutes
            TransitType.TRAM: 10,    # Every 10 minutes
            TransitType.BUS: 15,     # Every 15 minutes
            TransitType.MINIBUS: 8,  # Every 8 minutes
            TransitType.FERRY: 30    # Every 30 minutes
        }
        return base_frequencies.get(station_type, 15)  # Default to 15 minutes

    def create_city_info_html(self) -> str:
        """Create detailed HTML for city information display"""
        # Count stations by type
        station_counts = {}
        for station in self.transit_stations:
            station_counts[station.type] = station_counts.get(station.type, 0) + 1
        
        # Calculate coverage statistics
        total_area = (self.city_bounds['north'] - self.city_bounds['south']) * \
                    (self.city_bounds['east'] - self.city_bounds['west']) * 111 * 111  # Approx km²
        
        # Create HTML with modern styling
        html = """
        <div style="font-family: Arial, sans-serif; padding: 15px; background: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <h3 style="margin: 0 0 15px 0; color: #2c3e50; border-bottom: 2px solid #eee; padding-bottom: 10px;">
                Transit Network Overview
            </h3>
            <div style="margin-bottom: 15px;">
                <h4 style="margin: 0 0 10px 0; color: #34495e;">Transit Types</h4>
                <div style="display: grid; grid-template-columns: auto 1fr; gap: 8px; align-items: center;">
        """
        
        # Add station counts with icons and colors in a more organized layout
        styles = {t: self.get_transit_style(t) for t in TransitType}
        for transit_type, count in station_counts.items():
            style = styles[transit_type]
            html += f"""
                    <div style="display: flex; align-items: center; background: rgba({self._hex_to_rgb(style['color'])}, 0.1); 
                              padding: 5px 10px; border-radius: 4px; border-left: 3px solid {style['color']};">
                        <span style="margin-right: 8px; font-size: 16px;">{style['icon']}</span>
                        <span style="color: {style['color']}; font-weight: 600;">{style['label']}</span>
                    </div>
                    <div style="font-weight: 500;">{count} stations</div>
            """
        
        # Add coverage statistics with improved styling
        html += f"""
                </div>
            </div>
            <div style="margin-bottom: 15px;">
                <h4 style="margin: 0 0 10px 0; color: #34495e;">Coverage Statistics</h4>
                <div style="display: grid; grid-template-columns: auto 1fr; gap: 8px; background: #f8f9fa; padding: 10px; border-radius: 4px;">
                    <div style="display: flex; align-items: center;"><span style="margin-right: 5px;">🎯</span> Total Stations:</div>
                    <div style="font-weight: 500;">{len(self.transit_stations)}</div>
                    <div style="display: flex; align-items: center;"><span style="margin-right: 5px;">📏</span> Service Area:</div>
                    <div style="font-weight: 500;">{total_area:.1f} km²</div>
                </div>
            </div>
            <div>
                <h4 style="margin: 0 0 10px 0; color: #34495e;">Service Frequency</h4>
                <div style="display: grid; grid-template-columns: auto 1fr; gap: 8px; background: #f8f9fa; padding: 10px; border-radius: 4px;">
                    <div style="display: flex; align-items: center;"><span style="margin-right: 5px;">🚇</span> Metro:</div>
                    <div style="font-weight: 500;">Every 5 min (peak)</div>
                    <div style="display: flex; align-items: center;"><span style="margin-right: 5px;">🚊</span> Tram:</div>
                    <div style="font-weight: 500;">Every 10 min</div>
                    <div style="display: flex; align-items: center;"><span style="margin-right: 5px;">🚌</span> Bus:</div>
                    <div style="font-weight: 500;">Every 10-15 min</div>
                </div>
            </div>
        </div>
        """
        return html

    def _hex_to_rgb(self, hex_color: str) -> str:
        """Convert hex color to RGB values for CSS."""
        hex_color = hex_color.lstrip('#')
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return f"{r}, {g}, {b}"
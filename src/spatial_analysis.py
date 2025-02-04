import geopandas as gpd
import osmnx as ox
import networkx as nx
from typing import Dict, Tuple, List
import numpy as np
from src.transit_data import TransitType, TransitStation

class SpatialAnalyzer:
    def __init__(self, city_bounds: Dict[str, float]):
        """
        Initialize spatial analyzer with city boundaries.
        
        Args:
            city_bounds: Dictionary with 'north', 'south', 'east', 'west' coordinates
        """
        self.city_bounds = city_bounds
        self.G = None  # Street network
        self.transit_nodes = None
        self.buildings = None
        
    def load_street_network(self):
        """Load street network from OSM"""
        self.G = ox.graph_from_bbox(
            self.city_bounds['north'],
            self.city_bounds['south'],
            self.city_bounds['east'],
            self.city_bounds['west'],
            network_type='walk'
        )
        return self.G
    
    def load_osm_transit_data(self) -> List[TransitStation]:
        """Load transit data from local OSM files"""
        # Load transport points and areas
        transport_points = gpd.read_file('src/egypt_osm/gis_osm_transport_free_1.shp')
        transport_areas = gpd.read_file('src/egypt_osm/gis_osm_transport_a_free_1.shp')
        railways = gpd.read_file('src/egypt_osm/gis_osm_railways_free_1.shp')
        traffic = gpd.read_file('src/egypt_osm/gis_osm_traffic_free_1.shp')
        
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
        
        transit_stations = []
        
        # Process transport points
        for _, row in transport_points.iterrows():
            station_type = self._get_transit_type(row)
            if station_type:
                transit_stations.append(
                    TransitStation(
                        lat=row.geometry.y,
                        lon=row.geometry.x,
                        name=row.get('name', 'Unknown Station'),
                        type=station_type,
                        line=row.get('fclass', 'Unknown Line'),
                        status="Operational",
                        frequency=self._estimate_frequency(row)
                    )
                )
        
        # Process transport areas (stations, terminals)
        for _, row in transport_areas.iterrows():
            station_type = self._get_transit_type(row)
            if station_type:
                centroid = row.geometry.centroid
                transit_stations.append(
                    TransitStation(
                        lat=centroid.y,
                        lon=centroid.x,
                        name=row.get('name', 'Unknown Station'),
                        type=station_type,
                        line=row.get('fclass', 'Unknown Line'),
                        status="Operational",
                        frequency=self._estimate_frequency(row)
                    )
                )
        
        return transit_stations
    
    def _get_transit_type(self, feature) -> TransitType:
        """Determine transit type from OSM feature"""
        fclass = feature.get('fclass', '').lower()
        
        if 'subway' in fclass or 'metro' in fclass:
            return TransitType.METRO
        elif 'bus' in fclass:
            return TransitType.BUS
        elif 'tram' in fclass:
            return TransitType.TRAM
        elif 'train' in fclass or 'railway' in fclass:
            return TransitType.TRAIN
        elif 'ferry' in fclass:
            return TransitType.FERRY
        elif 'minibus' in fclass:
            return TransitType.MINIBUS
        return None
    
    def _estimate_frequency(self, feature) -> int:
        """Estimate service frequency based on feature type"""
        fclass = feature.get('fclass', '').lower()
        
        # Default frequencies based on transit type
        if 'subway' in fclass or 'metro' in fclass:
            return 3  # Every 3 minutes
        elif 'bus' in fclass:
            return 15  # Every 15 minutes
        elif 'tram' in fclass:
            return 8  # Every 8 minutes
        elif 'train' in fclass:
            return 30  # Every 30 minutes
        elif 'ferry' in fclass:
            return 60  # Every 60 minutes
        elif 'minibus' in fclass:
            return 5  # Every 5 minutes
        return 0  # Unknown frequency
    
    def calculate_walkability_score(self, point: Tuple[float, float]) -> float:
        """
        Calculate walkability score based on network distance to amenities.
        
        Args:
            point: (latitude, longitude) tuple
        
        Returns:
            float: Walkability score (0-100)
        """
        if self.G is None:
            self.load_street_network()
            
        # Find nearest node in network
        nearest_node = ox.nearest_nodes(self.G, point[1], point[0])
        
        # Calculate distances to amenities
        amenities = ox.geometries_from_point(
            point,
            tags={'amenity': True},
            dist=500
        )
        
        if len(amenities) == 0:
            return 0
            
        # Score based on number and proximity of amenities
        distances = []
        for _, amenity in amenities.iterrows():
            target_node = ox.nearest_nodes(
                self.G,
                amenity.geometry.y,
                amenity.geometry.x
            )
            try:
                distance = nx.shortest_path_length(
                    self.G,
                    nearest_node,
                    target_node,
                    weight='length'
                )
                distances.append(distance)
            except nx.NetworkXNoPath:
                continue
                
        if not distances:
            return 0
            
        # Calculate score (100 = perfect walkability)
        avg_distance = np.mean(distances)
        num_amenities = len(distances)
        
        score = 100 * (num_amenities / 10) * np.exp(-avg_distance / 500)
        return min(100, score) 
    
    def _calculate_transit_accessibility(self, point: Tuple[float, float]) -> float:
        """Calculate TOD score based on distance to nearest stations."""
        if not self.spatial_index or not self.transit_nodes:
            return 0
        
        # Find all stations within 1km
        nearby_stations = []
        for station in self.transit_nodes:
            dist = self.calculate_distance(point[0], point[1], station.lat, station.lon)
            if dist <= 1000:  # Only consider stations within 1km
                nearby_stations.append((dist, station))
        
        if not nearby_stations:
            return 0
            
        # Base score calculation
        tod_score = 0
        
        # Calculate score for each station type
        type_scores = {}
        for dist, station in nearby_stations:
            # More generous distance-based score
            if dist <= 500:  # Increased from 400m
                distance_score = 100
            elif dist <= 800:
                distance_score = 85  # Higher base score for secondary zone
            else:
                distance_score = 70  # Higher minimum score if within 1km
            
            # Simplified type weights - all stations matter
            type_multiplier = {
                TransitType.METRO: 1.0,
                TransitType.TRAIN: 1.0,
                TransitType.TRAM: 0.9,
                TransitType.BUS: 0.9,
                TransitType.MINIBUS: 0.8,
                TransitType.FERRY: 0.9
            }.get(station.type, 0.9)
            
            station_score = distance_score * type_multiplier
            
            # Keep best score for each type
            current_type_score = type_scores.get(station.type, 0)
            type_scores[station.type] = max(current_type_score, station_score)
        
        # Base score is the highest individual station score
        tod_score = max(type_scores.values())
        
        # Significant bonus for multiple station types
        unique_types = len(type_scores)
        if unique_types > 1:
            # 30% bonus for 2 types, 50% for 3+
            bonus_multiplier = 1.5 if unique_types >= 3 else 1.3
            tod_score *= bonus_multiplier
        
        # Additional bonus for having both metro/train and bus/tram
        has_rapid_transit = any(t in type_scores for t in [TransitType.METRO, TransitType.TRAIN])
        has_local_transit = any(t in type_scores for t in [TransitType.BUS, TransitType.TRAM])
        if has_rapid_transit and has_local_transit:
            tod_score *= 1.2  # 20% bonus for good transit mix
        
        print(f"TOD Score: {min(100, tod_score):.1f} (based on {len(nearby_stations)} stations, {unique_types} types)")
        return min(100, tod_score)

    def calculate_transit_coverage(self, transit_nodes, buffer_distance):
        """Calculate the percentage of city area covered by transit stations."""
        try:
            from shapely.geometry import Point, box
            from shapely.ops import unary_union
            
            # Create city boundary box
            city_box = box(
                self.city_bounds['west'],
                self.city_bounds['south'],
                self.city_bounds['east'],
                self.city_bounds['north']
            )
            city_area = city_box.area
            
            # Convert buffer distance from meters to degrees (approximate)
            # 1 degree ≈ 111,000 meters at the equator
            buffer_degrees = buffer_distance / 111000
            
            # Create union of all station buffers
            covered_areas = []
            for station in transit_nodes:
                station_point = Point(station.lon, station.lat)
                station_buffer = station_point.buffer(buffer_degrees)
                covered_areas.append(station_buffer)
            
            if not covered_areas:
                return 0.0
            
            total_coverage = unary_union(covered_areas)
            
            # Calculate intersection with city boundary
            covered_city_area = total_coverage.intersection(city_box)
            
            # Calculate percentage
            coverage_percentage = (covered_city_area.area / city_area) * 100
            
            # Cap at 100% and ensure non-negative
            return min(max(coverage_percentage, 0), 100)
            
        except Exception as e:
            print(f"Error calculating transit coverage: {e}")
            return 0.0
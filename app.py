import streamlit as st
import numpy as np
from src.spatial_analysis import SpatialAnalyzer
from src.optimization import TODOptimizer
from src.visualization import TODVisualizer
from src.transit_data import TransitType
from city_data import CITY_PRESETS, CITY_INFO, get_transit_nodes
import plotly.graph_objects as go
from shapely.geometry import Point, box
from shapely.ops import unary_union

def render_sidebar():
    """Render sidebar controls"""
    st.sidebar.header("Simulation Parameters")
    
    # City Selection
    selected_city = st.sidebar.selectbox(
        "Select City",
        options=list(CITY_PRESETS.keys())
    )
    
    if selected_city == "Custom":
        city_bounds = {
            'north': st.sidebar.number_input("North Boundary", value=30.1728),
            'south': st.sidebar.number_input("South Boundary", value=29.9511),
            'east': st.sidebar.number_input("East Boundary", value=31.3062),
            'west': st.sidebar.number_input("West Boundary", value=31.2357)
        }
    else:
        city_bounds = CITY_PRESETS[selected_city]
        if selected_city != "Custom":
            st.sidebar.markdown("---")
            st.sidebar.markdown(f"### 🌆 {selected_city}")
            st.sidebar.markdown(CITY_INFO.get(selected_city, ""))
    
    st.sidebar.markdown("---")
    
    # Development Parameters
    with st.sidebar.expander("Development Parameters", expanded=True):
        min_green_space = st.slider(
            "Minimum Green Space (%)",
            0, 100, 20,
            help="Minimum percentage of area that must be green space"
        ) / 100
        
        max_transit_distance = st.slider(
            "Maximum Transit Distance (m)",
            100, 1000, 500,
            help="Maximum walking distance to transit stations"
        )
        
        density_factor = st.slider(
            "Development Density",
            0.0, 2.0, 1.0,
            help="Relative density of development (1.0 = normal)"
        )
    
    # Advanced Settings
    with st.sidebar.expander("Advanced Settings"):
        grid_resolution = st.select_slider(
            "Grid Resolution",
            options=['Low (20x20)', 'Medium (50x50)', 'High (100x100)', 'Very High (200x200)'],
            value='High (100x100)',
            help="Size of the analysis grid (higher = more detailed but slower)"
        )
        
        # Convert resolution string to tuple
        resolution_map = {
            'Low (20x20)': {
                'size': (20, 20),
                'info': 'Quick overview, 1 cell ≈ 2-3 km²'
            },
            'Medium (50x50)': {
                'size': (50, 50),
                'info': 'Balanced performance, 1 cell ≈ 800m²'
            },
            'High (100x100)': {
                'size': (100, 100),
                'info': 'Detailed analysis, 1 cell ≈ 200m²'
            },
            'Very High (200x200)': {
                'size': (200, 200),
                'info': 'Maximum detail, 1 cell ≈ 50m², may be slower'
            }
        }
        grid_size = resolution_map[grid_resolution]['size']
        
        optimization_weights = {
            'residential': st.slider("Residential Weight", 0.0, 2.0, 1.5),
            'commercial': st.slider("Commercial Weight", 0.0, 2.0, 1.0),
            'green': st.slider("Green Space Weight", 0.0, 2.0, 0.5)
        }
    
    return (
        selected_city,
        city_bounds,
        min_green_space,
        max_transit_distance,
        density_factor,
        grid_size,
        optimization_weights
    )

def render_metrics(land_use, walkability_scores):
    """Render key metrics with modern styling"""
    st.markdown("""
    <style>
        .metric-row {
            display: flex;
            justify-content: space-between;
            margin-bottom: 20px;
        }
        .metric-card {
            background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            flex: 1;
            margin: 0 10px;
            transition: transform 0.2s;
        }
        .metric-card:hover {
            transform: translateY(-5px);
        }
        .metric-title {
            font-size: 1.1em;
            font-weight: 600;
            color: #1e1e1e;
            margin-bottom: 10px;
        }
        .metric-value {
            font-size: 2em;
            font-weight: 700;
            color: #2c3e50;
        }
        .metric-subtitle {
            font-size: 0.9em;
            color: #666;
            margin-top: 5px;
        }
    </style>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        avg_walk = np.mean(walkability_scores)
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">🚶‍♂️ Walkability Score</div>
                <div class="metric-value">{avg_walk:.1f}</div>
                <div class="metric-subtitle">
                    {'Excellent' if avg_walk >= 80 else
                     'Good' if avg_walk >= 60 else
                     'Fair' if avg_walk >= 40 else
                     'Poor'}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    with col2:
        green_space_pct = np.sum(land_use['green']) / land_use['green'].size * 100
        target_green = 20
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">🌳 Green Space</div>
                <div class="metric-value">{green_space_pct:.1f}%</div>
                <div class="metric-subtitle">
                    {'Above Target' if green_space_pct > target_green else
                     'At Target' if green_space_pct == target_green else
                     'Below Target'} ({target_green}% target)
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

def render_sidebar_controls(selected_city):
    """Render all sidebar controls and information in sidebar"""
    st.sidebar.markdown("---")
    
    # Combined Transit Types and Filters
    st.sidebar.markdown("#### 🚉 Transit Types")
    
    filters = {}
    
    # Metro
    col1, col2 = st.sidebar.columns([1, 4])
    with col1:
        filters['Metro'] = st.checkbox(
            'Metro',
            value=True,
            key='filter_METRO',
            label_visibility='collapsed'
        )
    with col2:
        st.markdown('🚇 Metro - <span style="color: #E31E24;">●</span> High-capacity', unsafe_allow_html=True)
    
    # Bus
    col1, col2 = st.sidebar.columns([1, 4])
    with col1:
        filters['Bus'] = st.checkbox(
            'Bus',
            value=True,
            key='filter_BUS',
            label_visibility='collapsed'
        )
    with col2:
        st.markdown('🚌 Bus - <span style="color: #1E88E5;">●</span> Local service', unsafe_allow_html=True)
    
    # Tram
    col1, col2 = st.sidebar.columns([1, 4])
    with col1:
        filters['Tram'] = st.checkbox(
            'Tram',
            value=True,
            key='filter_TRAM',
            label_visibility='collapsed'
        )
    with col2:
        st.markdown('🚊 Tram - <span style="color: #9B59B6;">●</span> Street-level', unsafe_allow_html=True)
    
    # Train
    col1, col2 = st.sidebar.columns([1, 4])
    with col1:
        filters['Train'] = st.checkbox(
            'Train',
            value=True,
            key='filter_TRAIN',
            label_visibility='collapsed'
        )
    with col2:
        st.markdown('🚂 Train - <span style="color: #FFA000;">●</span> Regional', unsafe_allow_html=True)
    
    st.sidebar.markdown("---")
    
    # TOD Analysis Settings
    with st.sidebar.expander("🎯 TOD Analysis Settings", expanded=True):
        st.markdown("""
        <span style="color: #2ECC71;">■</span> High TOD (75-100)
        - Excellent transit access
        - Multiple transit types
        - Optimal walking distance
        
        <span style="color: #F1C40F;">■</span> Medium TOD (45-74)
        - Good transit access
        - Limited transit mix
        - Acceptable walking distance
        
        <span style="color: #E74C3C;">■</span> Low TOD (0-44)
        - Limited transit access
        - Single transit type
        - Extended walking distance
        """, unsafe_allow_html=True)
        
        filters['show_tod_analysis'] = st.checkbox(
            "Show TOD Analysis",
            value=True,
            help="Show transit-oriented development potential"
        )
    
    # Walking Distance Settings
    with st.sidebar.expander("🚶 Walking Distance", expanded=True):
        walking_distance = st.number_input(
            "Maximum Distance (m)",
            min_value=200,
            max_value=1000,
            value=500,
            step=50,
            help="Maximum comfortable walking distance"
        )
        
        buffer_distances = {
            'primary': walking_distance,
            'secondary': walking_distance
        }
        
        buffer_opacities = {
            'primary': st.slider(
                "Coverage Opacity",
                0.0, 1.0, 0.3,
                help="Adjust the visibility"
            ),
            'secondary': 0
        }
        
        filters['show_walkability_radius'] = st.checkbox(
            "Show Coverage Circles",
            value=True,
            help="Show walking distance radius"
        )
    
    # Analysis Resolution
    with st.sidebar.expander("🔍 Resolution", expanded=False):
        selected_resolution = st.select_slider(
            "Grid Detail",
            options=['Low (20x20)', 'Medium (50x50)', 'High (100x100)', 'Very High (200x200)'],
            value='High (100x100)'
        )
        
        resolution_map = {
            'Low (20x20)': {'size': (20, 20)},
            'Medium (50x50)': {'size': (50, 50)},
            'High (100x100)': {'size': (100, 100)},
            'Very High (200x200)': {'size': (200, 200)}
        }
        grid_size = resolution_map[selected_resolution]['size']
    
    # Advanced Filters
    with st.sidebar.expander("⚙️ Advanced Filters", expanded=False):
        filters['show_only_operational'] = st.checkbox(
            "Only Operational Stations",
            value=False
        )
        
        filters['min_frequency'] = st.slider(
            "Max Wait Time (min)",
            0, 60, 15,
            help="Service frequency filter"
        )
        
        min_green_space = st.slider(
            "Green Space (%)",
            0, 100, 20,
            help="Target percentage"
        ) / 100
    
    return filters, min_green_space, walking_distance, grid_size, buffer_distances, buffer_opacities

def main():
    st.set_page_config(
        page_title="TOD Simulator",
        page_icon="🏙️",
        layout="wide"
    )
    
    # Title and Description
    col1, col2 = st.columns([2,1])
    with col1:
        st.title("🏙️ Transit-Oriented Development Simulator")
    with col2:
        st.write("")  # Spacing
        st.write("")  # Spacing
        if st.button("ℹ️ About", help="Learn more about TOD simulation"):
            st.info("""
                This simulator helps urban planners optimize Transit-Oriented Development (TOD).
                Adjust parameters in the sidebar and see how they affect development patterns.
                """)
    
    # City information dictionary
    CITY_INFO = {
        "Cairo": """
        🏛️ **Capital City**
        - Population: 9.5 million
        - Area: 3,085 km²
        - Transit Types: Metro, Bus, Tram
        - Key Features:
          - 3 Metro lines
          - Extensive bus network
          - Historical tram system
        """,
        
        "Alexandria": """
        🌊 **Coastal Metropolis**
        - Population: 5.2 million
        - Area: 2,679 km²
        - Transit Types: Tram, Bus
        - Key Features:
          - Historic tram network
          - Waterfront development
          - Bus rapid transit system
        """,
        
        "Port Said": """
        🚢 **Port City**
        - Population: 749,371
        - Area: 1,351 km²
        - Transit Types: Bus, Train
        - Key Features:
          - Major seaport
          - Railway connection
          - Waterfront transit
        """,
        
        "Suez": """
        ⚓ **Canal City**
        - Population: 728,180
        - Area: 326.4 km²
        - Transit Types: Bus, Train
        - Key Features:
          - Strategic location
          - Industrial transit
          - Port connectivity
        """
    }

    # Get city selection first
    selected_city = st.sidebar.selectbox(
        "Select City",
        options=list(CITY_PRESETS.keys())
    )
    
    # Get city bounds based on selection
    if selected_city == "Custom":
        city_bounds = {
            'north': st.sidebar.number_input("North Boundary", value=30.1728),
            'south': st.sidebar.number_input("South Boundary", value=29.9511),
            'east': st.sidebar.number_input("East Boundary", value=31.3062),
            'west': st.sidebar.number_input("West Boundary", value=31.2357)
        }
    else:
        city_bounds = CITY_PRESETS[selected_city]
        if selected_city != "Custom":
            st.sidebar.markdown("---")
            st.sidebar.markdown(f"### 🌆 {selected_city}")
            st.sidebar.markdown(CITY_INFO.get(selected_city, ""))
    
    # Get all other parameters from the new sidebar controls
    filters, min_green_space, max_transit_distance, grid_size, buffer_distances, buffer_opacities = render_sidebar_controls(selected_city)
    
    # Fix the city_center calculation
    city_center = (
        (city_bounds['north'] + city_bounds['south']) / 2,
        (city_bounds['east'] + city_bounds['west']) / 2
    )
    
    # Initialize analyzer and get transit nodes
    analyzer = SpatialAnalyzer(city_bounds)
    transit_nodes = get_transit_nodes(selected_city)
    
    # Calculate coverage using the transit nodes
    try:
        coverage = analyzer.calculate_transit_coverage(transit_nodes, buffer_distances['primary'])
    except Exception as e:
        print(f"Error in coverage calculation: {e}")
        coverage = 0.0
    
    visualizer = TODVisualizer(city_center, city_bounds)
    
    # Main tabs
    tab1, tab2, tab3 = st.tabs([
        "📊 Development Plan",
        "🚶 Walkability Analysis",
        "📈 Sustainability Metrics"
    ])
    
    # Generate sample walkability scores
    walkability_scores = np.random.rand(*grid_size) * 100
    
    # Optimize land use
    optimizer = TODOptimizer(
        grid_size,
        transit_nodes,
        min_green_space,
        buffer_distances['secondary']
    )
    
    with st.spinner("Running simulation..."):
        land_use = optimizer.optimize_land_use(walkability_scores)
    
    with tab1:
        st.header("Development Plan Overview")
        
        # Create three columns for metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("### 🚶 Walkability Score")
            walkability_value = np.mean(walkability_scores)
            st.markdown(f"# {walkability_value:.1f}")
            if walkability_value >= 75:
                st.success("Excellent")
            elif walkability_value >= 50:
                st.info("Fair")
            else:
                st.warning("Needs Improvement")
        
        with col2:
            st.markdown("### 🌳 Green Space")
            green_percentage = land_use['green'].mean() * 100
            st.markdown(f"# {green_percentage:.1f}%")
            if green_percentage >= min_green_space * 100:
                st.success(f"Above Target ({min_green_space*100}% target)")
            else:
                st.warning(f"Below Target ({min_green_space*100}% target)")
        
        with col3:
            st.markdown("### 🚉 Transit Coverage")
            st.markdown(f"# {coverage:.1f}%")
            if coverage >= 70:
                st.success("High Coverage")
            elif coverage >= 40:
                st.info("Moderate Coverage")
            else:
                st.warning("Low Coverage")
        
        # Filter transit stations based on selections
        filtered_stations = [
            station for station in transit_nodes
            if filters.get(station.type.value, True)
            and (not filters['show_only_operational'] or station.status == "Operational")
            and (filters['min_frequency'] == 0 or station.frequency <= filters['min_frequency'])
        ]
        
        # Show the interactive map
        st.markdown("### 🗺️ Interactive Map")
        m = visualizer.create_interactive_map(
            land_use,
            filtered_stations,
            walkability_scores,
            filters,
            buffer_distances,
            buffer_opacities
        )
        st.components.v1.html(m._repr_html_(), height=500)
        
        # Create two columns for charts
        chart_col1, chart_col2 = st.columns(2)
        
        with chart_col1:
            st.markdown("### Land Use Distribution")
            # Create donut chart for land use
            try:
                land_use_values = [
                    float(land_use['green'].mean() * 100),
                    float(land_use['residential'].mean() * 100),
                    float(land_use['commercial'].mean() * 100)
                ]
            except (KeyError, AttributeError):
                land_use_values = [33.3, 33.3, 33.4]
            
            fig1 = go.Figure(data=[go.Pie(
                labels=['Green Space', 'Residential', 'Commercial'],
                values=land_use_values,
                hole=.4,
                marker_colors=['#2ECC71', '#E74C3C', '#3498DB']
            )])
            fig1.update_layout(
                showlegend=True,
                margin=dict(t=0, b=0, l=0, r=0),
                height=300,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig1, use_container_width=True)
        
        with chart_col2:
            st.markdown("### Station Summary")
            
            # Calculate station statistics
            total_stations = len(transit_nodes)
            operational = len([s for s in transit_nodes if s.status == "Operational"])
            high_freq = len([s for s in transit_nodes if s.frequency <= 10])  # High frequency = 10 min or less
            
            # Create summary metrics
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Stations", total_stations)
                st.metric("High Frequency", f"{high_freq} stations")
            
            with col2:
                st.metric("Operational", operational)
                st.metric("Coverage", f"{coverage:.1f}%")
            
            # Add station type breakdown
            st.markdown("#### Station Types")
            for transit_type in ['Metro', 'Bus', 'Tram', 'Train']:
                count = len([s for s in transit_nodes if s.type.value == transit_type])
                if count > 0:
                    st.markdown(f"""
                    {'🚇' if transit_type == 'Metro' else '🚌' if transit_type == 'Bus' else '🚊' if transit_type == 'Tram' else '🚂'} **{transit_type}:** {count} stations
                    """)
            
            # Add frequency information
            st.markdown("#### Service Frequency")
            freq_data = [s.frequency for s in transit_nodes if s.frequency > 0]
            if freq_data:
                avg_freq = np.mean(freq_data)
                min_freq = np.min(freq_data)
                st.markdown(f"""
                ⏱️ Average wait: **{avg_freq:.0f}** minutes
                🚄 Best frequency: **{min_freq:.0f}** minutes
                """)
    
    with tab2:
        st.subheader("Walkability Analysis")
        
        # Filter transit stations based on selections
        filtered_stations = [
            station for station in transit_nodes
            if filters.get(station.type.value, True)  # Check if station type is enabled
            and (not filters['show_only_operational'] or station.status == "Operational")
            and (filters['min_frequency'] == 0 or station.frequency <= filters['min_frequency'])
        ]
        
        # Create columns for analysis metrics
        wcol1, wcol2 = st.columns(2)
        
        with wcol1:
            st.metric("Transit Stations", len(filtered_stations))
            st.metric("Average Walking Distance", f"{buffer_distances['primary']}m")
        
        with wcol2:
            st.metric("Coverage Area", f"{coverage:.1f}%")
            st.metric("Service Frequency", f"{filters['min_frequency']} min")
        
        # Add walkability statistics
        st.markdown("#### 📊 Coverage Statistics")
        walk_stats = {
            "High Access Areas": f"{np.sum(walkability_scores > 80) / walkability_scores.size * 100:.1f}%",
            "Medium Access Areas": f"{np.sum((walkability_scores > 40) & (walkability_scores <= 80)) / walkability_scores.size * 100:.1f}%",
            "Low Access Areas": f"{np.sum(walkability_scores <= 40) / walkability_scores.size * 100:.1f}%"
        }
        
        for metric, value in walk_stats.items():
            st.metric(metric, value)
        
        # Add detailed analysis section
        st.markdown("### Detailed Analysis")
        
        analysis_cols = st.columns(3)
        
        with analysis_cols[0]:
            st.markdown("#### 🎯 Areas Needing Improvement")
            low_walk_pct = np.sum(walkability_scores < 40) / walkability_scores.size * 100
            st.metric("Low Walkability Areas", f"{low_walk_pct:.1f}%")
            st.markdown("""
            Areas with walkability scores below 40 need:
            - Better transit connections
            - Improved pedestrian infrastructure
            - More local amenities
            """)
        
        with analysis_cols[1]:
            st.markdown("#### 🚶‍♂️ Pedestrian Access")
            avg_distance = np.mean([station.frequency for station in filtered_stations if station.frequency > 0])
            st.metric("Average Service Frequency", f"{avg_distance:.1f} min")
            st.markdown("""
            Factors affecting pedestrian access:
            - Distance to transit
            - Service frequency
            - Walking infrastructure
            """)
        
        with analysis_cols[2]:
            st.markdown("#### 💡 Recommendations")
            st.markdown("""
            Based on analysis:
            1. Add transit stations in low-coverage areas
            2. Increase service frequency where needed
            3. Improve pedestrian infrastructure
            4. Add more amenities near stations
            """)
    
    with tab3:
        st.subheader("Sustainability Impact Analysis")
        
        # Calculate base metrics
        total_stations = len(filtered_stations)
        operational_stations = len([s for s in filtered_stations if s.status == "Operational"])
        coverage_ratio = coverage / 100  # Convert to decimal
        green_area = land_use['green'].mean() * 100
        
        # Create three columns for main metrics
        metric_col1, metric_col2, metric_col3 = st.columns(3)
        
        with metric_col1:
            st.metric("Transit Network Coverage", f"{coverage:.1f}%",
                     delta=f"{coverage_ratio*100-50:.1f}% from baseline")
        with metric_col2:
            st.metric("Green Space Ratio", f"{green_area:.1f}%",
                     delta=f"{green_area-20:.1f}% from target")
        with metric_col3:
            st.metric("Operational Efficiency", 
                     f"{(operational_stations/total_stations*100):.1f}%",
                     delta=f"{operational_stations} active stations")
        
        # Environmental Impact Section
        st.markdown("### 🌱 Environmental Impact Assessment")
        env_col1, env_col2 = st.columns(2)
        
        with env_col1:
            # Calculate environmental metrics
            daily_ridership = operational_stations * 5000  # Estimate 5000 riders per station
            car_trips_reduced = daily_ridership * 0.6  # Assume 60% would have used cars
            co2_reduction = car_trips_reduced * 2.5 / 1000  # 2.5 kg CO2 per car trip
            
            # Create emissions reduction chart
            emissions_data = {
                'Category': ['Car Emissions Saved', 'Public Transit Emissions', 'Net Reduction'],
                'Tons CO2/Year': [co2_reduction * 365, co2_reduction * 0.2 * 365, co2_reduction * 0.8 * 365]
            }
            
            fig_emissions = go.Figure(data=[
                go.Bar(name='CO2 Impact',
                      x=emissions_data['Category'],
                      y=emissions_data['Tons CO2/Year'],
                      marker_color=['#2ECC71', '#E74C3C', '#3498DB'])
            ])
            fig_emissions.update_layout(
                title="Annual CO2 Impact (Tons)",
                height=300,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig_emissions, use_container_width=True)
            
            # Environmental metrics
            st.markdown(f"""
            #### Key Environmental Metrics
            - **CO₂ Reduction:** {co2_reduction * 365:.0f} tons/year
            - **Car Trips Reduced:** {car_trips_reduced * 365:,.0f}/year
            - **Green Space Added:** {green_area:.1f}% of area
            - **Air Quality Improvement:** {coverage_ratio * 25:.1f}%
            """)
        
        with env_col2:
            # Create green space distribution chart
            green_space_data = {
                'Category': ['Parks', 'Urban Forest', 'Green Corridors', 'Other Green'],
                'Percentage': [green_area * 0.4, green_area * 0.3, green_area * 0.2, green_area * 0.1]
            }
            
            fig_green = go.Figure(data=[go.Pie(
                labels=green_space_data['Category'],
                values=green_space_data['Percentage'],
                marker_colors=['#2ECC71', '#27AE60', '#229954', '#1E8449']
            )])
            fig_green.update_layout(
                title="Green Space Distribution",
                height=300,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig_green, use_container_width=True)
        
        # Social Impact Section
        st.markdown("### 👥 Social Impact Analysis")
        social_col1, social_col2 = st.columns(2)
        
        with social_col1:
            # Calculate social metrics
            population_served = coverage_ratio * 1000000  # Estimate based on coverage
            accessibility_score = np.mean(walkability_scores)
            avg_wait_time = np.mean([s.frequency for s in filtered_stations if s.frequency > 0])
            
            # Create accessibility chart
            accessibility_data = {
                'Distance': ['< 5 min', '5-10 min', '10-15 min', '> 15 min'],
                'Population': [
                    population_served * 0.4,
                    population_served * 0.3,
                    population_served * 0.2,
                    population_served * 0.1
                ]
            }
            
            fig_access = go.Figure(data=[
                go.Bar(name='Population Access',
                      x=accessibility_data['Distance'],
                      y=accessibility_data['Population'],
                      marker_color=['#2ECC71', '#3498DB', '#F1C40F', '#E74C3C'])
            ])
            fig_access.update_layout(
                title="Transit Accessibility Distribution",
                height=300,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig_access, use_container_width=True)
        
        with social_col2:
            # Create service quality metrics
            quality_metrics = {
                'Metric': ['Frequency', 'Coverage', 'Accessibility', 'Integration'],
                'Score': [
                    min(100, 100 - avg_wait_time),
                    coverage,
                    accessibility_score,
                    (coverage + accessibility_score) / 2
                ]
            }
            
            fig_quality = go.Figure(data=[
                go.Scatterpolar(
                    r=quality_metrics['Score'],
                    theta=quality_metrics['Metric'],
                    fill='toself',
                    marker_color='#3498DB'
                )
            ])
            fig_quality.update_layout(
                title="Service Quality Assessment",
                height=300,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                polar=dict(
                    radialaxis=dict(range=[0, 100])
                )
            )
            st.plotly_chart(fig_quality, use_container_width=True)
        
        # Recommendations Section
        st.markdown("### 🎯 Sustainability Recommendations")
        rec_col1, rec_col2 = st.columns(2)
        
        with rec_col1:
            st.markdown("""
            #### Environmental Actions
            1. Increase green space by 15%
            2. Implement solar panels at stations
            3. Add electric bus routes
            4. Develop green corridors
            5. Reduce carbon footprint
            6. Improve waste management
            """)
        
        with rec_col2:
            st.markdown("""
            #### Social Initiatives
            1. Improve station accessibility
            2. Increase service frequency
            3. Add real-time information
            4. Enhance safety features
            5. Expand coverage to underserved areas
            6. Improve pedestrian infrastructure
            """)

if __name__ == "__main__":
    main() 
"""
Data Loader - Utility for loading airport and route data from CSV files.

This module provides functionality to load airports, routes, and flight
schedules from various file formats (CSV, JSON).
"""

import csv
import json
import os
from typing import List, Dict, Optional, Tuple
from datetime import datetime

from ..models.airport import Airport
from ..models.flight import Flight
from ..models.graph import RouteGraph


class DataLoader:
    """
    Utility class for loading data from files.
    
    Supports loading airports from CSV, routes from CSV,
    and flight schedules from JSON.
    """
    
    def __init__(self, data_dir: str = None):
        """
        Initialize the data loader.
        
        Args:
            data_dir: Directory containing data files
        """
        if data_dir is None:
            # Default to 'data' directory relative to project root
            self._data_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                'data'
            )
        else:
            self._data_dir = data_dir
    
    @property
    def data_dir(self) -> str:
        """Get the data directory path."""
        return self._data_dir
    
    def load_airports(self, filename: str = "airports.csv") -> List[Airport]:
        """
        Load airports from a CSV file.
        
        Expected CSV format: ID,Name,Latitude,Longitude[,WeatherFactor]
        
        Args:
            filename: Name of the CSV file
            
        Returns:
            List of Airport objects
        """
        filepath = os.path.join(self._data_dir, filename)
        airports = []
        
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Airport file not found: {filepath}")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                try:
                    weather_factor = float(row.get('WeatherFactor', row.get('weather_factor', 1.0)))
                except (ValueError, TypeError):
                    weather_factor = 1.0
                
                airport = Airport(
                    id=row.get('ID', row.get('id', '')).strip().upper(),
                    name=row.get('Name', row.get('name', '')).strip(),
                    latitude=float(row.get('Latitude', row.get('latitude', row.get('Lat', row.get('lat', 0))))),
                    longitude=float(row.get('Longitude', row.get('longitude', row.get('Long', row.get('long', 0))))),
                    weather_factor=weather_factor
                )
                airports.append(airport)
        
        return airports
    
    def load_routes(self, filename: str = "routes.csv") -> List[Tuple[str, str, float]]:
        """
        Load routes from a CSV file.
        
        Expected CSV format: SourceID,DestID,Distance
        
        Args:
            filename: Name of the CSV file
            
        Returns:
            List of (source_id, dest_id, distance) tuples
        """
        filepath = os.path.join(self._data_dir, filename)
        routes = []
        
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Routes file not found: {filepath}")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                source = row.get('SourceID', row.get('source_id', row.get('Source', row.get('source', '')))).strip().upper()
                dest = row.get('DestID', row.get('dest_id', row.get('Dest', row.get('dest', row.get('Destination', row.get('destination', '')))))).strip().upper()
                
                try:
                    distance = float(row.get('Distance', row.get('distance', 0)))
                except (ValueError, TypeError):
                    distance = 0.0
                
                if source and dest:
                    routes.append((source, dest, distance))
        
        return routes
    
    def load_route_graph(self, airports_file: str = "airports.csv",
                         routes_file: str = "routes.csv",
                         bidirectional: bool = True,
                         calculate_distance: bool = True) -> RouteGraph:
        """
        Load a complete route graph from CSV files.
        
        Args:
            airports_file: Airports CSV filename
            routes_file: Routes CSV filename
            bidirectional: Whether routes are bidirectional
            calculate_distance: Recalculate distance from coordinates if True
            
        Returns:
            RouteGraph with airports and routes loaded
        """
        graph = RouteGraph()
        
        # Load airports
        airports = self.load_airports(airports_file)
        for airport in airports:
            graph.add_airport(airport)
        
        # Load routes
        routes = self.load_routes(routes_file)
        for source_id, dest_id, distance in routes:
            if graph.has_node(source_id) and graph.has_node(dest_id):
                if bidirectional:
                    graph.add_bidirectional_route(
                        source_id, dest_id,
                        distance=None if calculate_distance else distance
                    )
                else:
                    graph.add_route(
                        source_id, dest_id,
                        distance=None if calculate_distance else distance
                    )
        
        return graph
    
    def load_flights(self, filename: str = "simulated_schedules.json") -> List[Flight]:
        """
        Load flights from a JSON file.
        
        Expected JSON format:
        {
            "flights": [
                {
                    "flight_id": "FL001",
                    "origin": "JFK",
                    "destination": "LHR",
                    "arrival_start": "2024-01-15T14:30:00",
                    "occupancy_time": 15,
                    "priority": 5
                },
                ...
            ]
        }
        
        Args:
            filename: Name of the JSON file
            
        Returns:
            List of Flight objects
        """
        filepath = os.path.join(self._data_dir, filename)
        
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Flights file not found: {filepath}")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        flights = []
        flight_data = data.get('flights', data if isinstance(data, list) else [])
        
        for entry in flight_data:
            arrival_str = entry.get('arrival_start', entry.get('arrival_time', ''))
            
            # Parse datetime
            if isinstance(arrival_str, str):
                try:
                    arrival_start = datetime.fromisoformat(arrival_str)
                except ValueError:
                    # Try alternative formats
                    for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%H:%M']:
                        try:
                            arrival_start = datetime.strptime(arrival_str, fmt)
                            if fmt == '%H:%M':
                                # Add today's date
                                today = datetime.now()
                                arrival_start = arrival_start.replace(
                                    year=today.year,
                                    month=today.month,
                                    day=today.day
                                )
                            break
                        except ValueError:
                            continue
                    else:
                        continue  # Skip if can't parse
            else:
                continue
            
            flight = Flight(
                flight_id=entry.get('flight_id', f"FL{len(flights):04d}"),
                origin=entry.get('origin', 'UNK'),
                destination=entry.get('destination', 'UNK'),
                arrival_start=arrival_start,
                occupancy_time=int(entry.get('occupancy_time', 15)),
                priority=int(entry.get('priority', 5))
            )
            flights.append(flight)
        
        return flights
    
    def save_schedule(self, flights: List[Flight], filename: str = "schedule_output.json") -> str:
        """
        Save flight schedule to a JSON file.
        
        Args:
            flights: List of scheduled Flight objects
            filename: Output filename
            
        Returns:
            Path to the saved file
        """
        filepath = os.path.join(self._data_dir, filename)
        
        data = {
            "generated_at": datetime.now().isoformat(),
            "total_flights": len(flights),
            "flights": []
        }
        
        for flight in sorted(flights, key=lambda f: f.arrival_start):
            data["flights"].append({
                "flight_id": flight.flight_id,
                "origin": flight.origin,
                "destination": flight.destination,
                "arrival_start": flight.arrival_start.isoformat(),
                "arrival_end": flight.arrival_end.isoformat(),
                "occupancy_time": flight.occupancy_time,
                "runway_id": flight.runway_id,
                "priority": flight.priority
            })
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        return filepath
    
    def create_sample_data(self) -> None:
        """
        Create sample data files for testing.
        
        Creates airports.csv, routes.csv, and simulated_schedules.json
        with example data.
        """
        os.makedirs(self._data_dir, exist_ok=True)
        
        # Sample airports
        airports_data = [
            ['ID', 'Name', 'Latitude', 'Longitude', 'WeatherFactor'],
            ['JFK', 'John F. Kennedy International', '40.6413', '-73.7781', '1.0'],
            ['LHR', 'London Heathrow', '51.4700', '-0.4543', '1.1'],
            ['CDG', 'Paris Charles de Gaulle', '49.0097', '2.5479', '1.0'],
            ['FRA', 'Frankfurt Airport', '50.0379', '8.5622', '1.0'],
            ['DXB', 'Dubai International', '25.2532', '55.3657', '0.9'],
            ['SIN', 'Singapore Changi', '1.3644', '103.9915', '1.0'],
            ['HND', 'Tokyo Haneda', '35.5494', '139.7798', '1.0'],
            ['LAX', 'Los Angeles International', '33.9416', '-118.4085', '0.95'],
            ['ORD', "Chicago O'Hare", '41.9742', '-87.9073', '1.1'],
            ['SFO', 'San Francisco International', '37.6213', '-122.3790', '1.0'],
        ]
        
        with open(os.path.join(self._data_dir, 'airports.csv'), 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(airports_data)
        
        # Sample routes (connections between airports)
        routes_data = [
            ['SourceID', 'DestID', 'Distance'],
            # US domestic
            ['JFK', 'LAX', '3983'],
            ['JFK', 'ORD', '1180'],
            ['JFK', 'SFO', '4139'],
            ['LAX', 'SFO', '543'],
            ['LAX', 'ORD', '2800'],
            ['ORD', 'SFO', '2960'],
            # Transatlantic
            ['JFK', 'LHR', '5555'],
            ['JFK', 'CDG', '5834'],
            ['JFK', 'FRA', '6197'],
            ['LAX', 'LHR', '8756'],
            # European
            ['LHR', 'CDG', '344'],
            ['LHR', 'FRA', '654'],
            ['CDG', 'FRA', '450'],
            # Middle East / Asia connections
            ['LHR', 'DXB', '5493'],
            ['FRA', 'DXB', '4838'],
            ['DXB', 'SIN', '5839'],
            ['SIN', 'HND', '5311'],
            ['LAX', 'HND', '8816'],
            ['LAX', 'SIN', '14114'],
        ]
        
        with open(os.path.join(self._data_dir, 'routes.csv'), 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(routes_data)
        
        # Sample flight schedule
        base_time = datetime.now().replace(hour=14, minute=0, second=0, microsecond=0)
        flights_data = {
            "description": "Sample flight schedule for runway scheduling demo",
            "flights": [
                {"flight_id": "FL001", "origin": "JFK", "destination": "LHR", 
                 "arrival_start": base_time.isoformat(), "occupancy_time": 15, "priority": 3},
                {"flight_id": "FL002", "origin": "CDG", "destination": "LHR",
                 "arrival_start": (base_time.replace(minute=10)).isoformat(), "occupancy_time": 12, "priority": 5},
                {"flight_id": "FL003", "origin": "FRA", "destination": "LHR",
                 "arrival_start": (base_time.replace(minute=5)).isoformat(), "occupancy_time": 18, "priority": 2},
                {"flight_id": "FL004", "origin": "DXB", "destination": "LHR",
                 "arrival_start": (base_time.replace(minute=30)).isoformat(), "occupancy_time": 15, "priority": 4},
                {"flight_id": "FL005", "origin": "SIN", "destination": "LHR",
                 "arrival_start": (base_time.replace(minute=25)).isoformat(), "occupancy_time": 20, "priority": 5},
            ]
        }
        
        with open(os.path.join(self._data_dir, 'simulated_schedules.json'), 'w') as f:
            json.dump(flights_data, f, indent=2)
        
        print(f"Sample data created in: {self._data_dir}")

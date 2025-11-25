"""
Unit tests for the routing module.

Tests Dijkstra's algorithm implementation and route planning functionality.
"""

import unittest
import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models.airport import Airport
from src.models.graph import RouteGraph
from src.algorithms.routing import RoutePlanner, RouteResult


class TestAirport(unittest.TestCase):
    """Test cases for the Airport model."""
    
    def test_airport_creation(self):
        """Test basic airport creation."""
        airport = Airport(
            id="JFK",
            name="John F. Kennedy International",
            latitude=40.6413,
            longitude=-73.7781
        )
        
        self.assertEqual(airport.id, "JFK")
        self.assertEqual(airport.name, "John F. Kennedy International")
        self.assertAlmostEqual(airport.latitude, 40.6413, places=4)
        self.assertAlmostEqual(airport.longitude, -73.7781, places=4)
        self.assertEqual(airport.weather_factor, 1.0)
    
    def test_airport_with_weather_factor(self):
        """Test airport creation with weather factor."""
        airport = Airport(
            id="LHR",
            name="London Heathrow",
            latitude=51.47,
            longitude=-0.4543,
            weather_factor=1.2
        )
        
        self.assertEqual(airport.weather_factor, 1.2)
    
    def test_invalid_latitude(self):
        """Test that invalid latitude raises ValueError."""
        with self.assertRaises(ValueError):
            Airport(id="TST", name="Test", latitude=100.0, longitude=0.0)
    
    def test_invalid_longitude(self):
        """Test that invalid longitude raises ValueError."""
        with self.assertRaises(ValueError):
            Airport(id="TST", name="Test", latitude=0.0, longitude=200.0)
    
    def test_distance_calculation(self):
        """Test Haversine distance calculation."""
        jfk = Airport(id="JFK", name="JFK", latitude=40.6413, longitude=-73.7781)
        lhr = Airport(id="LHR", name="LHR", latitude=51.47, longitude=-0.4543)
        
        distance = jfk.distance_to(lhr)
        
        # JFK to LHR is approximately 5555 km
        self.assertGreater(distance, 5500)
        self.assertLess(distance, 5700)
    
    def test_distance_to_self(self):
        """Test that distance to self is zero."""
        airport = Airport(id="JFK", name="JFK", latitude=40.6413, longitude=-73.7781)
        
        self.assertEqual(airport.distance_to(airport), 0.0)
    
    def test_weighted_distance(self):
        """Test weighted distance with weather factors."""
        apt1 = Airport(id="A", name="A", latitude=0.0, longitude=0.0, weather_factor=1.0)
        apt2 = Airport(id="B", name="B", latitude=1.0, longitude=1.0, weather_factor=1.5)
        
        base_distance = apt1.distance_to(apt2)
        weighted_distance = apt1.get_weighted_distance(apt2, include_weather=True)
        
        # Average weather factor is (1.0 + 1.5) / 2 = 1.25
        expected = base_distance * 1.25
        self.assertAlmostEqual(weighted_distance, expected, places=2)
    
    def test_airport_equality(self):
        """Test airport equality based on ID."""
        apt1 = Airport(id="JFK", name="JFK", latitude=40.6413, longitude=-73.7781)
        apt2 = Airport(id="JFK", name="Different Name", latitude=40.6413, longitude=-73.7781)
        apt3 = Airport(id="LHR", name="LHR", latitude=51.47, longitude=-0.4543)
        
        self.assertEqual(apt1, apt2)
        self.assertNotEqual(apt1, apt3)
    
    def test_airport_hash(self):
        """Test that airports can be used in sets."""
        apt1 = Airport(id="JFK", name="JFK", latitude=40.6413, longitude=-73.7781)
        apt2 = Airport(id="JFK", name="JFK", latitude=40.6413, longitude=-73.7781)
        
        airport_set = {apt1, apt2}
        self.assertEqual(len(airport_set), 1)


class TestRouteGraph(unittest.TestCase):
    """Test cases for the RouteGraph model."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.graph = RouteGraph()
        
        self.jfk = Airport(id="JFK", name="JFK", latitude=40.6413, longitude=-73.7781)
        self.lhr = Airport(id="LHR", name="LHR", latitude=51.47, longitude=-0.4543)
        self.cdg = Airport(id="CDG", name="CDG", latitude=49.0097, longitude=2.5479)
        
        self.graph.add_airport(self.jfk)
        self.graph.add_airport(self.lhr)
        self.graph.add_airport(self.cdg)
    
    def test_add_airport(self):
        """Test adding airports to graph."""
        self.assertTrue(self.graph.has_node("JFK"))
        self.assertTrue(self.graph.has_node("LHR"))
        self.assertTrue(self.graph.has_node("CDG"))
        self.assertEqual(len(self.graph), 3)
    
    def test_add_route(self):
        """Test adding routes between airports."""
        self.graph.add_route("JFK", "LHR", distance=5555)
        
        self.assertTrue(self.graph.has_edge("JFK", "LHR"))
        self.assertFalse(self.graph.has_edge("LHR", "JFK"))  # Directed graph
    
    def test_add_bidirectional_route(self):
        """Test adding bidirectional routes."""
        self.graph.add_bidirectional_route("JFK", "LHR", distance=5555)
        
        self.assertTrue(self.graph.has_edge("JFK", "LHR"))
        self.assertTrue(self.graph.has_edge("LHR", "JFK"))
    
    def test_get_neighbors(self):
        """Test getting neighbors of a node."""
        self.graph.add_route("JFK", "LHR", distance=5555)
        self.graph.add_route("JFK", "CDG", distance=5834)
        
        neighbors = self.graph.get_neighbors("JFK")
        neighbor_ids = [n[0] for n in neighbors]
        
        self.assertIn("LHR", neighbor_ids)
        self.assertIn("CDG", neighbor_ids)
        self.assertEqual(len(neighbors), 2)
    
    def test_get_route_distance(self):
        """Test getting route distance."""
        self.graph.add_route("JFK", "LHR", distance=5555)
        
        distance = self.graph.get_route_distance("JFK", "LHR")
        self.assertEqual(distance, 5555)
    
    def test_nonexistent_route(self):
        """Test getting nonexistent route distance."""
        distance = self.graph.get_route_distance("JFK", "LHR")
        self.assertIsNone(distance)


class TestRoutePlanner(unittest.TestCase):
    """Test cases for the RoutePlanner class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.graph = RouteGraph()
        
        # Create a simple test network
        self.airports = {
            'A': Airport(id='A', name='Airport A', latitude=0.0, longitude=0.0),
            'B': Airport(id='B', name='Airport B', latitude=1.0, longitude=0.0),
            'C': Airport(id='C', name='Airport C', latitude=0.0, longitude=1.0),
            'D': Airport(id='D', name='Airport D', latitude=1.0, longitude=1.0),
        }
        
        for airport in self.airports.values():
            self.graph.add_airport(airport)
        
        # Create routes with explicit distances
        # A -> B: 100, A -> C: 150, B -> D: 100, C -> D: 50
        self.graph.add_route('A', 'B', distance=100)
        self.graph.add_route('A', 'C', distance=150)
        self.graph.add_route('B', 'D', distance=100)
        self.graph.add_route('C', 'D', distance=50)
        
        self.planner = RoutePlanner(self.graph, cruising_speed=100)  # 100 km/h for easy calculation
    
    def test_dijkstra_shortest_path(self):
        """Test Dijkstra's algorithm finds shortest path."""
        # Shortest path A -> D should be A -> B -> D (200) not A -> C -> D (200)
        # Actually both are 200, but we test that it finds a valid path
        result = self.planner.find_shortest_path('A', 'D')
        
        self.assertIsNotNone(result)
        self.assertEqual(result.source.id, 'A')
        self.assertEqual(result.destination.id, 'D')
        self.assertEqual(result.total_distance, 200)  # A-B-D or A-C-D
    
    def test_direct_route(self):
        """Test finding a direct route."""
        result = self.planner.find_shortest_path('A', 'B')
        
        self.assertIsNotNone(result)
        self.assertEqual(len(result.path), 2)
        self.assertEqual(result.total_distance, 100)
    
    def test_no_route_exists(self):
        """Test when no route exists."""
        # Add isolated airport
        self.graph.add_airport(Airport(id='Z', name='Isolated', latitude=10.0, longitude=10.0))
        
        result = self.planner.find_shortest_path('A', 'Z')
        self.assertIsNone(result)
    
    def test_same_source_destination(self):
        """Test route to same airport."""
        result = self.planner.find_shortest_path('A', 'A')
        
        self.assertIsNotNone(result)
        self.assertEqual(result.total_distance, 0)
    
    def test_eta_calculation(self):
        """Test ETA calculation."""
        departure = datetime(2025, 1, 1, 12, 0, 0)
        result = self.planner.find_shortest_path('A', 'B', departure_time=departure)
        
        # Distance is 100 km, speed is 100 km/h, so flight time is 1 hour
        expected_eta = departure + timedelta(hours=1)
        
        self.assertEqual(result.eta, expected_eta)
    
    def test_nonexistent_source(self):
        """Test with nonexistent source airport."""
        with self.assertRaises(ValueError):
            self.planner.dijkstra('XXX', 'A')
    
    def test_nonexistent_destination(self):
        """Test with nonexistent destination airport."""
        with self.assertRaises(ValueError):
            self.planner.dijkstra('A', 'XXX')
    
    def test_find_all_paths(self):
        """Test finding all paths between airports."""
        # Add another route to create multiple paths
        self.graph.add_route('A', 'D', distance=300)  # Direct but longer
        
        paths = self.planner.find_all_paths('A', 'D', max_stops=2)
        
        self.assertGreater(len(paths), 0)
        
        # All paths should start with A and end with D
        for path in paths:
            self.assertEqual(path[0].id, 'A')
            self.assertEqual(path[-1].id, 'D')
    
    def test_cruising_speed_setter(self):
        """Test setting cruising speed."""
        self.planner.set_cruising_speed(500)
        
        departure = datetime(2025, 1, 1, 12, 0, 0)
        result = self.planner.find_shortest_path('A', 'B', departure_time=departure)
        
        # Distance 100km at 500 km/h = 0.2 hours = 12 minutes
        expected_eta = departure + timedelta(hours=0.2)
        
        self.assertEqual(result.eta, expected_eta)
    
    def test_invalid_cruising_speed(self):
        """Test that invalid cruising speed raises error."""
        with self.assertRaises(ValueError):
            self.planner.set_cruising_speed(-100)


class TestRouteResult(unittest.TestCase):
    """Test cases for RouteResult dataclass."""
    
    def test_route_result_string(self):
        """Test RouteResult string representation."""
        jfk = Airport(id="JFK", name="JFK", latitude=40.6413, longitude=-73.7781)
        lhr = Airport(id="LHR", name="LHR", latitude=51.47, longitude=-0.4543)
        
        result = RouteResult(
            source=jfk,
            destination=lhr,
            path=[jfk, lhr],
            total_distance=5555.0,
            eta=datetime(2025, 1, 1, 20, 0, 0),
            flight_time=timedelta(hours=8),
            segments=[(jfk, lhr, 5555.0)]
        )
        
        result_str = str(result)
        
        self.assertIn("JFK", result_str)
        self.assertIn("LHR", result_str)
        self.assertIn("5555", result_str)


if __name__ == '__main__':
    unittest.main()

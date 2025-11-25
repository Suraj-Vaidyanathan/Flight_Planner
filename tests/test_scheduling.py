"""
Unit tests for the scheduling module.

Tests graph coloring algorithms and runway scheduling functionality.
"""

import unittest
import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models.flight import Flight
from src.models.graph import ConflictGraph
from src.algorithms.scheduling import RunwayScheduler, ScheduleResult


class TestFlight(unittest.TestCase):
    """Test cases for the Flight model."""
    
    def test_flight_creation(self):
        """Test basic flight creation."""
        arrival = datetime(2025, 1, 1, 14, 0, 0)
        
        flight = Flight(
            flight_id="FL001",
            origin="JFK",
            destination="LHR",
            arrival_start=arrival,
            occupancy_time=15
        )
        
        self.assertEqual(flight.flight_id, "FL001")
        self.assertEqual(flight.origin, "JFK")
        self.assertEqual(flight.destination, "LHR")
        self.assertEqual(flight.arrival_start, arrival)
        self.assertEqual(flight.occupancy_time, 15)
        self.assertEqual(flight.arrival_end, arrival + timedelta(minutes=15))
        self.assertIsNone(flight.runway_id)
    
    def test_arrival_end_calculation(self):
        """Test that arrival_end is calculated correctly."""
        arrival = datetime(2025, 1, 1, 14, 0, 0)
        
        flight = Flight(
            flight_id="FL001",
            origin="JFK",
            destination="LHR",
            arrival_start=arrival,
            occupancy_time=20
        )
        
        expected_end = arrival + timedelta(minutes=20)
        self.assertEqual(flight.arrival_end, expected_end)
    
    def test_invalid_occupancy_time(self):
        """Test that invalid occupancy time raises error."""
        with self.assertRaises(ValueError):
            Flight(
                flight_id="FL001",
                origin="JFK",
                destination="LHR",
                arrival_start=datetime.now(),
                occupancy_time=0
            )
    
    def test_overlapping_flights(self):
        """Test overlap detection between flights."""
        base_time = datetime(2025, 1, 1, 14, 0, 0)
        
        flight1 = Flight(
            flight_id="FL001",
            origin="JFK",
            destination="LHR",
            arrival_start=base_time,
            occupancy_time=15
        )
        
        # Overlapping flight (starts 10 minutes after flight1)
        flight2 = Flight(
            flight_id="FL002",
            origin="CDG",
            destination="LHR",
            arrival_start=base_time + timedelta(minutes=10),
            occupancy_time=15
        )
        
        self.assertTrue(flight1.overlaps_with(flight2))
        self.assertTrue(flight2.overlaps_with(flight1))  # Symmetric
    
    def test_non_overlapping_flights(self):
        """Test non-overlapping flights."""
        base_time = datetime(2025, 1, 1, 14, 0, 0)
        
        flight1 = Flight(
            flight_id="FL001",
            origin="JFK",
            destination="LHR",
            arrival_start=base_time,
            occupancy_time=15
        )
        
        # Non-overlapping flight (starts after flight1 ends)
        flight2 = Flight(
            flight_id="FL002",
            origin="CDG",
            destination="LHR",
            arrival_start=base_time + timedelta(minutes=20),
            occupancy_time=15
        )
        
        self.assertFalse(flight1.overlaps_with(flight2))
    
    def test_adjacent_flights_no_overlap(self):
        """Test that adjacent flights (touching but not overlapping) don't conflict."""
        base_time = datetime(2025, 1, 1, 14, 0, 0)
        
        flight1 = Flight(
            flight_id="FL001",
            origin="JFK",
            destination="LHR",
            arrival_start=base_time,
            occupancy_time=15
        )
        
        # Starts exactly when flight1 ends
        flight2 = Flight(
            flight_id="FL002",
            origin="CDG",
            destination="LHR",
            arrival_start=base_time + timedelta(minutes=15),
            occupancy_time=15
        )
        
        self.assertFalse(flight1.overlaps_with(flight2))
    
    def test_overlap_duration(self):
        """Test overlap duration calculation."""
        base_time = datetime(2025, 1, 1, 14, 0, 0)
        
        flight1 = Flight(
            flight_id="FL001",
            origin="JFK",
            destination="LHR",
            arrival_start=base_time,
            occupancy_time=20
        )
        
        flight2 = Flight(
            flight_id="FL002",
            origin="CDG",
            destination="LHR",
            arrival_start=base_time + timedelta(minutes=10),
            occupancy_time=20
        )
        
        overlap = flight1.get_overlap_duration(flight2)
        self.assertEqual(overlap, 10)  # 10 minutes overlap
    
    def test_flight_equality(self):
        """Test flight equality based on ID."""
        arrival = datetime(2025, 1, 1, 14, 0, 0)
        
        flight1 = Flight(flight_id="FL001", origin="JFK", destination="LHR", arrival_start=arrival)
        flight2 = Flight(flight_id="FL001", origin="CDG", destination="LHR", arrival_start=arrival)
        flight3 = Flight(flight_id="FL002", origin="JFK", destination="LHR", arrival_start=arrival)
        
        self.assertEqual(flight1, flight2)
        self.assertNotEqual(flight1, flight3)
    
    def test_flight_sorting(self):
        """Test that flights can be sorted by arrival time."""
        base_time = datetime(2025, 1, 1, 14, 0, 0)
        
        flight1 = Flight(flight_id="FL001", origin="JFK", destination="LHR", 
                        arrival_start=base_time + timedelta(minutes=30))
        flight2 = Flight(flight_id="FL002", origin="CDG", destination="LHR",
                        arrival_start=base_time)
        flight3 = Flight(flight_id="FL003", origin="FRA", destination="LHR",
                        arrival_start=base_time + timedelta(minutes=15))
        
        sorted_flights = sorted([flight1, flight2, flight3])
        
        self.assertEqual(sorted_flights[0].flight_id, "FL002")
        self.assertEqual(sorted_flights[1].flight_id, "FL003")
        self.assertEqual(sorted_flights[2].flight_id, "FL001")
    
    def test_generate_random_flight(self):
        """Test random flight generation."""
        base_time = datetime(2025, 1, 1, 14, 0, 0)
        
        flight = Flight.generate_random(
            destination="LHR",
            base_time=base_time,
            flight_number=42
        )
        
        self.assertEqual(flight.flight_id, "FL0042")
        self.assertEqual(flight.destination, "LHR")
        self.assertIsNotNone(flight.origin)
        self.assertIsNotNone(flight.arrival_start)


class TestConflictGraph(unittest.TestCase):
    """Test cases for the ConflictGraph model."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.base_time = datetime(2025, 1, 1, 14, 0, 0)
        
        self.flights = [
            Flight(flight_id="FL001", origin="JFK", destination="LHR",
                  arrival_start=self.base_time, occupancy_time=15),
            Flight(flight_id="FL002", origin="CDG", destination="LHR",
                  arrival_start=self.base_time + timedelta(minutes=10), occupancy_time=15),
            Flight(flight_id="FL003", origin="FRA", destination="LHR",
                  arrival_start=self.base_time + timedelta(minutes=30), occupancy_time=15),
        ]
    
    def test_build_conflict_graph(self):
        """Test building conflict graph from flights."""
        graph = ConflictGraph()
        graph.build_from_flights(self.flights)
        
        self.assertEqual(len(graph), 3)
        
        # FL001 and FL002 overlap
        self.assertTrue(graph.has_edge("FL001", "FL002"))
        
        # FL003 doesn't overlap with others
        self.assertFalse(graph.has_edge("FL001", "FL003"))
        self.assertFalse(graph.has_edge("FL002", "FL003"))
    
    def test_get_conflict_count(self):
        """Test getting conflict count for a flight."""
        graph = ConflictGraph()
        graph.build_from_flights(self.flights)
        
        # FL001 conflicts with FL002 only
        self.assertEqual(graph.get_conflict_count("FL001"), 1)
        
        # FL003 has no conflicts
        self.assertEqual(graph.get_conflict_count("FL003"), 0)
    
    def test_get_conflicting_flights(self):
        """Test getting list of conflicting flights."""
        graph = ConflictGraph()
        graph.build_from_flights(self.flights)
        
        conflicts = graph.get_conflicting_flights("FL001")
        conflict_ids = [f.flight_id for f in conflicts]
        
        self.assertIn("FL002", conflict_ids)
        self.assertNotIn("FL003", conflict_ids)
    
    def test_adjacency_matrix(self):
        """Test adjacency matrix generation."""
        graph = ConflictGraph()
        graph.build_from_flights(self.flights)
        
        matrix = graph.get_adjacency_matrix()
        
        self.assertEqual(len(matrix), 3)
        self.assertEqual(len(matrix[0]), 3)
    
    def test_max_degree(self):
        """Test finding maximum degree node."""
        # Create more complex conflict pattern
        flights = [
            Flight(flight_id="FL001", origin="A", destination="X",
                  arrival_start=self.base_time, occupancy_time=30),
            Flight(flight_id="FL002", origin="B", destination="X",
                  arrival_start=self.base_time + timedelta(minutes=10), occupancy_time=30),
            Flight(flight_id="FL003", origin="C", destination="X",
                  arrival_start=self.base_time + timedelta(minutes=20), occupancy_time=30),
        ]
        
        graph = ConflictGraph()
        graph.build_from_flights(flights)
        
        max_node, max_degree = graph.get_max_degree()
        
        # FL002 is in the middle and overlaps with both FL001 and FL003
        # But FL001 also overlaps with FL002 and FL003 (30 min window covers all)
        # All three flights overlap with each other, so all have degree 2
        self.assertEqual(max_degree, 2)


class TestRunwayScheduler(unittest.TestCase):
    """Test cases for the RunwayScheduler class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.base_time = datetime(2025, 1, 1, 14, 0, 0)
    
    def test_no_conflicts(self):
        """Test scheduling flights with no conflicts."""
        flights = [
            Flight(flight_id="FL001", origin="JFK", destination="LHR",
                  arrival_start=self.base_time, occupancy_time=10),
            Flight(flight_id="FL002", origin="CDG", destination="LHR",
                  arrival_start=self.base_time + timedelta(minutes=15), occupancy_time=10),
            Flight(flight_id="FL003", origin="FRA", destination="LHR",
                  arrival_start=self.base_time + timedelta(minutes=30), occupancy_time=10),
        ]
        
        scheduler = RunwayScheduler(algorithm='dsatur')
        result = scheduler.schedule(flights)
        
        # All flights can use the same runway
        self.assertEqual(result.num_runways, 1)
    
    def test_all_conflicts(self):
        """Test scheduling flights that all conflict."""
        # All flights at the same time
        flights = [
            Flight(flight_id="FL001", origin="JFK", destination="LHR",
                  arrival_start=self.base_time, occupancy_time=15),
            Flight(flight_id="FL002", origin="CDG", destination="LHR",
                  arrival_start=self.base_time, occupancy_time=15),
            Flight(flight_id="FL003", origin="FRA", destination="LHR",
                  arrival_start=self.base_time, occupancy_time=15),
        ]
        
        scheduler = RunwayScheduler(algorithm='dsatur')
        result = scheduler.schedule(flights)
        
        # Each flight needs its own runway
        self.assertEqual(result.num_runways, 3)
    
    def test_partial_conflicts(self):
        """Test scheduling flights with partial conflicts."""
        flights = [
            Flight(flight_id="FL001", origin="JFK", destination="LHR",
                  arrival_start=self.base_time, occupancy_time=20),
            Flight(flight_id="FL002", origin="CDG", destination="LHR",
                  arrival_start=self.base_time + timedelta(minutes=10), occupancy_time=20),
            Flight(flight_id="FL003", origin="FRA", destination="LHR",
                  arrival_start=self.base_time + timedelta(minutes=25), occupancy_time=20),
        ]
        
        scheduler = RunwayScheduler(algorithm='dsatur')
        result = scheduler.schedule(flights)
        
        # FL001 and FL002 conflict, FL002 and FL003 conflict
        # FL001 and FL003 don't conflict, so they can share a runway
        self.assertEqual(result.num_runways, 2)
    
    def test_dsatur_algorithm(self):
        """Test DSatur algorithm produces valid schedule."""
        flights = [
            Flight(flight_id="FL001", origin="JFK", destination="LHR",
                  arrival_start=self.base_time, occupancy_time=15),
            Flight(flight_id="FL002", origin="CDG", destination="LHR",
                  arrival_start=self.base_time + timedelta(minutes=5), occupancy_time=15),
            Flight(flight_id="FL003", origin="FRA", destination="LHR",
                  arrival_start=self.base_time + timedelta(minutes=20), occupancy_time=15),
        ]
        
        scheduler = RunwayScheduler(algorithm='dsatur')
        result = scheduler.schedule(flights)
        
        is_valid, conflicts = scheduler.validate_schedule(result.flights)
        self.assertTrue(is_valid)
        self.assertEqual(len(conflicts), 0)
    
    def test_welsh_powell_algorithm(self):
        """Test Welsh-Powell algorithm produces valid schedule."""
        flights = [
            Flight(flight_id="FL001", origin="JFK", destination="LHR",
                  arrival_start=self.base_time, occupancy_time=15),
            Flight(flight_id="FL002", origin="CDG", destination="LHR",
                  arrival_start=self.base_time + timedelta(minutes=5), occupancy_time=15),
            Flight(flight_id="FL003", origin="FRA", destination="LHR",
                  arrival_start=self.base_time + timedelta(minutes=20), occupancy_time=15),
        ]
        
        scheduler = RunwayScheduler(algorithm='welsh_powell')
        result = scheduler.schedule(flights)
        
        is_valid, conflicts = scheduler.validate_schedule(result.flights)
        self.assertTrue(is_valid)
    
    def test_greedy_algorithm(self):
        """Test Greedy algorithm produces valid schedule."""
        flights = [
            Flight(flight_id="FL001", origin="JFK", destination="LHR",
                  arrival_start=self.base_time, occupancy_time=15),
            Flight(flight_id="FL002", origin="CDG", destination="LHR",
                  arrival_start=self.base_time + timedelta(minutes=5), occupancy_time=15),
        ]
        
        scheduler = RunwayScheduler(algorithm='greedy')
        result = scheduler.schedule(flights)
        
        is_valid, conflicts = scheduler.validate_schedule(result.flights)
        self.assertTrue(is_valid)
    
    def test_invalid_algorithm(self):
        """Test that invalid algorithm raises error."""
        with self.assertRaises(ValueError):
            RunwayScheduler(algorithm='invalid')
    
    def test_empty_flight_list(self):
        """Test scheduling empty flight list."""
        scheduler = RunwayScheduler()
        result = scheduler.schedule([])
        
        self.assertEqual(result.num_runways, 0)
        self.assertEqual(len(result.flights), 0)
    
    def test_single_flight(self):
        """Test scheduling single flight."""
        flights = [
            Flight(flight_id="FL001", origin="JFK", destination="LHR",
                  arrival_start=self.base_time, occupancy_time=15)
        ]
        
        scheduler = RunwayScheduler()
        result = scheduler.schedule(flights)
        
        self.assertEqual(result.num_runways, 1)
        self.assertEqual(result.flights[0].runway_id, 1)
    
    def test_runway_assignments(self):
        """Test that runway assignments are correctly populated."""
        flights = [
            Flight(flight_id="FL001", origin="JFK", destination="LHR",
                  arrival_start=self.base_time, occupancy_time=15),
            Flight(flight_id="FL002", origin="CDG", destination="LHR",
                  arrival_start=self.base_time, occupancy_time=15),
        ]
        
        scheduler = RunwayScheduler()
        result = scheduler.schedule(flights)
        
        # Check runway_assignments dict
        self.assertIn(1, result.runway_assignments)
        self.assertIn(2, result.runway_assignments)
        
        total_assigned = sum(len(flights) for flights in result.runway_assignments.values())
        self.assertEqual(total_assigned, 2)
    
    def test_validate_valid_schedule(self):
        """Test validation of a valid schedule."""
        flights = [
            Flight(flight_id="FL001", origin="JFK", destination="LHR",
                  arrival_start=self.base_time, occupancy_time=15),
            Flight(flight_id="FL002", origin="CDG", destination="LHR",
                  arrival_start=self.base_time + timedelta(minutes=20), occupancy_time=15),
        ]
        
        # Assign same runway (no conflict since they don't overlap)
        flights[0].runway_id = 1
        flights[1].runway_id = 1
        
        scheduler = RunwayScheduler()
        is_valid, conflicts = scheduler.validate_schedule(flights)
        
        self.assertTrue(is_valid)
        self.assertEqual(len(conflicts), 0)
    
    def test_validate_invalid_schedule(self):
        """Test validation detects conflicts."""
        flights = [
            Flight(flight_id="FL001", origin="JFK", destination="LHR",
                  arrival_start=self.base_time, occupancy_time=15),
            Flight(flight_id="FL002", origin="CDG", destination="LHR",
                  arrival_start=self.base_time + timedelta(minutes=5), occupancy_time=15),
        ]
        
        # Force same runway (creates conflict)
        flights[0].runway_id = 1
        flights[1].runway_id = 1
        
        scheduler = RunwayScheduler()
        is_valid, conflicts = scheduler.validate_schedule(flights)
        
        self.assertFalse(is_valid)
        self.assertEqual(len(conflicts), 1)
    
    def test_chromatic_number_bounds(self):
        """Test chromatic number bound estimation."""
        # Create a cycle of 3 flights (all pairs conflict)
        flights = [
            Flight(flight_id="FL001", origin="JFK", destination="LHR",
                  arrival_start=self.base_time, occupancy_time=30),
            Flight(flight_id="FL002", origin="CDG", destination="LHR",
                  arrival_start=self.base_time + timedelta(minutes=10), occupancy_time=30),
            Flight(flight_id="FL003", origin="FRA", destination="LHR",
                  arrival_start=self.base_time + timedelta(minutes=20), occupancy_time=30),
        ]
        
        scheduler = RunwayScheduler()
        lower, upper = scheduler.get_chromatic_number_bound(flights)
        
        self.assertGreaterEqual(lower, 1)
        self.assertGreaterEqual(upper, lower)


class TestScheduleResult(unittest.TestCase):
    """Test cases for ScheduleResult dataclass."""
    
    def test_schedule_result_string(self):
        """Test ScheduleResult string representation."""
        base_time = datetime(2025, 1, 1, 14, 0, 0)
        
        flight = Flight(flight_id="FL001", origin="JFK", destination="LHR",
                       arrival_start=base_time, occupancy_time=15)
        flight.runway_id = 1
        
        result = ScheduleResult(
            flights=[flight],
            num_runways=1,
            runway_assignments={1: [flight]},
            conflicts_resolved=0
        )
        
        result_str = str(result)
        
        self.assertIn("FL001", result_str)
        self.assertIn("RUNWAY 1", result_str)
    
    def test_schedule_table(self):
        """Test schedule table generation."""
        base_time = datetime(2025, 1, 1, 14, 0, 0)
        
        flight = Flight(flight_id="FL001", origin="JFK", destination="LHR",
                       arrival_start=base_time, occupancy_time=15)
        flight.runway_id = 1
        
        result = ScheduleResult(
            flights=[flight],
            num_runways=1,
            runway_assignments={1: [flight]}
        )
        
        table = result.get_schedule_table()
        
        self.assertIn("FL001", table)
        self.assertIn("JFK", table)
        self.assertIn("LHR", table)


if __name__ == '__main__':
    unittest.main()

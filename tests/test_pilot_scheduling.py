"""
Test cases for Pilot Scheduling Algorithm.

This module tests the ethical pilot scheduler to ensure it respects
FAA regulations and assigns pilots fairly.
"""

import unittest
from datetime import datetime, timedelta
import sys
import os

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models.pilot import Pilot, PilotAssignment
from src.models.flight import Flight
from src.algorithms.pilot_scheduling import PilotScheduler, PilotScheduleResult


class TestPilotModel(unittest.TestCase):
    """Test cases for the Pilot model."""
    
    def test_pilot_creation(self):
        """Test creating a pilot."""
        pilot = Pilot(
            pilot_id="P001",
            name="Capt. Smith",
            certification="ATP",
            max_daily_hours=8.0,
            min_rest_hours=10.0,
            home_base="JFK"
        )
        
        self.assertEqual(pilot.pilot_id, "P001")
        self.assertEqual(pilot.name, "Capt. Smith")
        self.assertEqual(pilot.total_hours_today, 0.0)
        self.assertIsNone(pilot.last_flight_end)
    
    def test_pilot_can_fly_initial(self):
        """Test that a fresh pilot can fly."""
        pilot = Pilot(
            pilot_id="P001",
            name="Capt. Smith",
            max_daily_hours=8.0,
            min_rest_hours=10.0
        )
        
        flight_start = datetime.now()
        self.assertTrue(pilot.can_fly(flight_start, 2.0))
    
    def test_pilot_cannot_exceed_daily_hours(self):
        """Test that pilot cannot exceed daily hour limit."""
        pilot = Pilot(
            pilot_id="P001",
            name="Capt. Smith",
            max_daily_hours=8.0,
            min_rest_hours=10.0
        )
        
        # Assign 7 hours worth of flights
        pilot.total_hours_today = 7.0
        
        flight_start = datetime.now()
        
        # Can fly 1 hour flight (total 8)
        self.assertTrue(pilot.can_fly(flight_start, 1.0))
        
        # Cannot fly 2 hour flight (would total 9)
        self.assertFalse(pilot.can_fly(flight_start, 2.0))
    
    def test_pilot_requires_rest(self):
        """Test that pilot requires rest between flights."""
        pilot = Pilot(
            pilot_id="P001",
            name="Capt. Smith",
            max_daily_hours=8.0,
            min_rest_hours=10.0
        )
        
        # Last flight ended 5 hours ago
        flight_end = datetime.now() - timedelta(hours=5)
        pilot.last_flight_end = flight_end
        pilot.total_hours_today = 2.0
        
        # Next flight starts now (only 5 hours rest)
        flight_start = datetime.now()
        
        # Should not be able to fly (needs 10 hours rest)
        self.assertFalse(pilot.can_fly(flight_start, 2.0))
        
        # Flight starting 11 hours after last one should be OK
        flight_start_later = flight_end + timedelta(hours=11)
        self.assertTrue(pilot.can_fly(flight_start_later, 2.0))
    
    def test_pilot_assignment(self):
        """Test assigning a flight to a pilot."""
        pilot = Pilot(
            pilot_id="P001",
            name="Capt. Smith",
            max_daily_hours=8.0,
            min_rest_hours=10.0
        )
        
        flight_start = datetime.now()
        flight_end = flight_start + timedelta(hours=2)
        
        pilot.assign_flight("FL001", flight_start, flight_end, 2.0)
        
        self.assertEqual(len(pilot.assigned_flights), 1)
        self.assertEqual(pilot.total_hours_today, 2.0)
        self.assertEqual(pilot.last_flight_end, flight_end)


class TestPilotScheduler(unittest.TestCase):
    """Test cases for the PilotScheduler algorithm."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.scheduler = PilotScheduler(min_rest_hours=10.0, max_daily_hours=8.0)
        self.base_time = datetime.now().replace(hour=10, minute=0, second=0, microsecond=0)
    
    def test_scheduler_creation(self):
        """Test creating a scheduler."""
        self.assertEqual(self.scheduler.min_rest_hours, 10.0)
        self.assertEqual(self.scheduler.max_daily_hours, 8.0)
    
    def test_create_pilots(self):
        """Test creating a fleet of pilots."""
        pilots = self.scheduler.create_pilots(5, base_airport="JFK")
        
        self.assertEqual(len(pilots), 5)
        
        for pilot in pilots:
            self.assertEqual(pilot.max_daily_hours, 8.0)
            self.assertEqual(pilot.min_rest_hours, 10.0)
            self.assertEqual(pilot.home_base, "JFK")
    
    def test_schedule_simple(self):
        """Test scheduling a simple set of flights."""
        # Create 2 pilots
        self.scheduler.create_pilots(2, base_airport="JFK")
        
        # Create 3 flights with no conflicts
        flights = [
            Flight(
                flight_id="FL001",
                origin="JFK",
                destination="LHR",
                arrival_start=self.base_time,
                occupancy_time=15
            ),
            Flight(
                flight_id="FL002",
                origin="CDG",
                destination="LHR",
                arrival_start=self.base_time + timedelta(hours=12),
                occupancy_time=15
            ),
            Flight(
                flight_id="FL003",
                origin="FRA",
                destination="LHR",
                arrival_start=self.base_time + timedelta(hours=1),
                occupancy_time=15
            )
        ]
        
        result = self.scheduler.schedule(flights, strategy='least_busy')
        
        # All flights should be assigned
        self.assertEqual(len(result.assignments), 3)
        self.assertEqual(len(result.unassigned_flights), 0)
        self.assertEqual(result.compliance_rate, 100.0)
    
    def test_schedule_with_rest_constraint(self):
        """Test that scheduler respects rest requirements."""
        # Create 1 pilot
        self.scheduler.create_pilots(1, base_airport="JFK")
        
        # Create 2 flights 5 hours apart (less than 10 hour rest requirement)
        flights = [
            Flight(
                flight_id="FL001",
                origin="JFK",
                destination="LHR",
                arrival_start=self.base_time,
                occupancy_time=15
            ),
            Flight(
                flight_id="FL002",
                origin="CDG",
                destination="LHR",
                arrival_start=self.base_time + timedelta(hours=5),
                occupancy_time=15
            )
        ]
        
        result = self.scheduler.schedule(flights, strategy='least_busy')
        
        # Only 1 flight should be assigned (first one)
        self.assertEqual(len(result.assignments), 1)
        self.assertEqual(len(result.unassigned_flights), 1)
        self.assertLess(result.compliance_rate, 100.0)
    
    def test_schedule_with_daily_hour_limit(self):
        """Test that scheduler respects daily hour limits."""
        # Create 1 pilot with 8 hour limit
        self.scheduler.create_pilots(1, base_airport="JFK")
        
        # Create many short flights that exceed 8 hours total
        flights = []
        for i in range(20):  # 20 flights * 0.75 hours = 15 hours
            flights.append(Flight(
                flight_id=f"FL{i:03d}",
                origin="JFK",
                destination="LHR",
                arrival_start=self.base_time + timedelta(hours=i * 12),  # 12 hours apart
                occupancy_time=15  # 15 minutes + 30 buffer = 45 min = 0.75 hours
            ))
        
        result = self.scheduler.schedule(flights, strategy='least_busy')
        
        # Should only assign enough flights to stay under 8 hour limit
        self.assertLessEqual(len(result.assignments), 10)  # Approximately 8/0.75
        self.assertGreater(len(result.unassigned_flights), 0)
    
    def test_least_busy_strategy(self):
        """Test least busy strategy distributes work fairly."""
        # Create 3 pilots
        self.scheduler.create_pilots(3, base_airport="JFK")
        
        # Create 6 flights spaced far apart
        flights = []
        for i in range(6):
            flights.append(Flight(
                flight_id=f"FL{i:03d}",
                origin="JFK",
                destination="LHR",
                arrival_start=self.base_time + timedelta(hours=i * 12),
                occupancy_time=15
            ))
        
        result = self.scheduler.schedule(flights, strategy='least_busy')
        
        # All flights should be assigned
        self.assertEqual(len(result.assignments), 6)
        
        # Each pilot should have 2 flights (fair distribution)
        pilot_counts = {}
        for assignment in result.assignments:
            pilot_counts[assignment.pilot_id] = pilot_counts.get(assignment.pilot_id, 0) + 1
        
        # Should have 3 pilots with assignments
        self.assertEqual(len(pilot_counts), 3)
    
    def test_validation(self):
        """Test schedule validation."""
        # Create valid assignments
        pilot_id = "P001"
        assignments = [
            PilotAssignment(
                pilot_id=pilot_id,
                flight_id="FL001",
                assignment_time=datetime.now(),
                flight_start=self.base_time,
                flight_end=self.base_time + timedelta(hours=2)
            ),
            PilotAssignment(
                pilot_id=pilot_id,
                flight_id="FL002",
                assignment_time=datetime.now(),
                flight_start=self.base_time + timedelta(hours=13),  # 11 hours rest
                flight_end=self.base_time + timedelta(hours=15)
            )
        ]
        
        is_valid, violations = self.scheduler.validate_schedule(assignments)
        
        # Should be valid (11 hours rest > 10 hour requirement)
        self.assertTrue(is_valid)
        self.assertEqual(len(violations), 0)
    
    def test_validation_insufficient_rest(self):
        """Test validation catches insufficient rest."""
        pilot_id = "P001"
        assignments = [
            PilotAssignment(
                pilot_id=pilot_id,
                flight_id="FL001",
                assignment_time=datetime.now(),
                flight_start=self.base_time,
                flight_end=self.base_time + timedelta(hours=2)
            ),
            PilotAssignment(
                pilot_id=pilot_id,
                flight_id="FL002",
                assignment_time=datetime.now(),
                flight_start=self.base_time + timedelta(hours=5),  # Only 3 hours rest
                flight_end=self.base_time + timedelta(hours=7)
            )
        ]
        
        is_valid, violations = self.scheduler.validate_schedule(assignments)
        
        # Should be invalid (3 hours rest < 10 hour requirement)
        self.assertFalse(is_valid)
        self.assertGreater(len(violations), 0)
    
    def test_validation_exceeds_daily_hours(self):
        """Test validation catches exceeded daily hours."""
        pilot_id = "P001"
        assignments = [
            PilotAssignment(
                pilot_id=pilot_id,
                flight_id="FL001",
                assignment_time=datetime.now(),
                flight_start=self.base_time,
                flight_end=self.base_time + timedelta(hours=5)
            ),
            PilotAssignment(
                pilot_id=pilot_id,
                flight_id="FL002",
                assignment_time=datetime.now(),
                flight_start=self.base_time + timedelta(hours=16),
                flight_end=self.base_time + timedelta(hours=20)
            )
        ]
        
        is_valid, violations = self.scheduler.validate_schedule(assignments)
        
        # Should be invalid (9 hours > 8 hour limit)
        self.assertFalse(is_valid)
        self.assertGreater(len(violations), 0)


if __name__ == '__main__':
    unittest.main()

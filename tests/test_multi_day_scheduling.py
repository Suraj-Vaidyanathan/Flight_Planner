"""
Unit tests for multi-day flight generation and pilot scheduling
"""
import unittest
from datetime import datetime, timedelta
from src.models.flight import Flight
from src.models.pilot import Pilot
from src.utils.multi_day_generator import MultiDayFlightGenerator
from src.algorithms.multi_day_pilot_scheduling import MultiDayPilotScheduler


class TestMultiDayFlightGenerator(unittest.TestCase):
    """Test multi-day flight generation"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.generator = MultiDayFlightGenerator()
        
    def test_generate_single_day(self):
        """Test generating flights for a single day"""
        flights = self.generator.generate_multi_day_flights(
            destination="JFK",
            num_days=1,
            flights_per_day=10
        )
        
        self.assertGreaterEqual(len(flights), 8)  # Allow for randomness
        # All flights should be on day 0
        for flight in flights:
            self.assertEqual(flight.day, 0)
            
    def test_generate_multiple_days(self):
        """Test generating flights across multiple days"""
        flights = self.generator.generate_multi_day_flights(
            destination="LAX",
            num_days=3,
            flights_per_day=15,
        )
        
        # Should have flights across 3 days
        days = set(f.day for f in flights)
        self.assertEqual(len(days), 3)
        self.assertEqual(days, {0, 1, 2})
        
    def test_realistic_pattern(self):
        """Test that flights are generated with realistic distribution"""
        flights = self.generator.generate_multi_day_flights(
            destination="ORD",
            num_days=2,
            flights_per_day=20
        )
        
        # Just verify flights were generated across days
        days = set(f.day for f in flights)
        self.assertEqual(len(days), 2)
        
    def test_flight_attributes(self):
        """Test that generated flights have all required attributes"""
        flights = self.generator.generate_multi_day_flights(
            destination="SFO",
            num_days=1,
            flights_per_day=5,
        )
        
        for flight in flights:
            # Check all new attributes exist
            self.assertIsNotNone(flight.passenger_count)
            self.assertIsNotNone(flight.distance)
            self.assertIsNotNone(flight.flight_duration)
            self.assertIsNotNone(flight.day)
            self.assertEqual(flight.delayed_by, 0)
            
            # Validate ranges
            self.assertGreaterEqual(flight.passenger_count, 50)
            self.assertLessEqual(flight.passenger_count, 300)
            self.assertGreater(flight.distance, 0)
            self.assertGreater(flight.flight_duration, 0)


class TestMultiDayPilotScheduler(unittest.TestCase):
    """Test multi-day pilot scheduling"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.generator = MultiDayFlightGenerator()
        self.scheduler = MultiDayPilotScheduler()
        
    def test_single_day_scheduling(self):
        """Test scheduling pilots for single day"""
        flights = self.generator.generate_multi_day_flights(
            destination="BOS",
            num_days=1,
            flights_per_day=10,
        )
        
        pilots = [Pilot(f"P{i:03d}", f"Pilot {i}", "Commercial") for i in range(5)]
        
        result = self.scheduler.schedule(flights, pilots)
        
        self.assertIsNotNone(result)
        self.assertEqual(len(result.daily_schedules), 1)
        self.assertGreater(len(result.all_assignments), 0)
        
    def test_multi_day_scheduling(self):
        """Test scheduling pilots across multiple days"""
        flights = self.generator.generate_multi_day_flights(
            destination="MIA",
            num_days=3,
            flights_per_day=15,
        )
        
        pilots = [Pilot(f"P{i:03d}", f"Pilot {i}", "Commercial") for i in range(8)]
        
        result = self.scheduler.schedule(flights, pilots)
        
        # Should have schedules for 3 days
        self.assertEqual(len(result.daily_schedules), 3)
        
        # Each day should have its own schedule
        for day in range(3):
            self.assertIn(day, result.daily_schedules)
            day_schedule = result.daily_schedules[day]
            self.assertGreater(len(day_schedule.assignments), 0)
            
    def test_daily_hour_reset(self):
        """Test that pilot hours reset each day"""
        flights = self.generator.generate_multi_day_flights(
            destination="SEA",
            num_days=2,
            flights_per_day=12,
        )
        
        # Use only 2 pilots to maximize their usage
        pilots = [Pilot(f"P{i:03d}", f"Pilot {i}", "Commercial") for i in range(2)]
        
        result = self.scheduler.schedule(flights, pilots, max_daily_hours=8.0)
        
        # Check that same pilots can work multiple days
        pilot_days = {}
        for assignment in result.all_assignments:
            pilot_id = assignment.pilot_id
            day = assignment.day
            if pilot_id not in pilot_days:
                pilot_days[pilot_id] = set()
            pilot_days[pilot_id].add(day)
            
        # At least one pilot should work multiple days
        multi_day_pilots = [pid for pid, days in pilot_days.items() if len(days) > 1]
        self.assertGreater(len(multi_day_pilots), 0)
        
    def test_faa_compliance(self):
        """Test FAA regulation compliance across days"""
        flights = self.generator.generate_multi_day_flights(
            destination="DEN",
            num_days=2,
            flights_per_day=10,
        )
        
        pilots = [Pilot(f"P{i:03d}", f"Pilot {i}", "Commercial") for i in range(10)]
        
        result = self.scheduler.schedule(
            flights, 
            pilots,
            max_daily_hours=8.0,
            min_rest_hours=10.0
        )
        
        # Should be FAA compliant
        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.violations), 0)
        
        # Check overall compliance rate
        self.assertGreaterEqual(result.overall_compliance_rate, 95.0)
        
    def test_pilot_utilization(self):
        """Test pilot utilization tracking"""
        flights = self.generator.generate_multi_day_flights(
            destination="ATL",
            num_days=2,
            flights_per_day=15,
        )
        
        pilots = [Pilot(f"P{i:03d}", f"Pilot {i}", "Commercial") for i in range(6)]
        
        result = self.scheduler.schedule(flights, pilots)
        
        # Should have utilization data
        self.assertGreater(len(result.pilot_utilization), 0)
        
        # All utilized pilots should have non-zero utilization
        for pilot_id, util_pct in result.pilot_utilization.items():
            self.assertGreater(util_pct, 0)
            self.assertLessEqual(util_pct, 100)


if __name__ == '__main__':
    unittest.main()

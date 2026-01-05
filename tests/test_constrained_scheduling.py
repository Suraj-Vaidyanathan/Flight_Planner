"""
Unit tests for constrained runway scheduling
"""
import unittest
from datetime import datetime, timedelta
from src.models.flight import Flight
from src.utils.multi_day_generator import MultiDayFlightGenerator
from src.algorithms.constrained_scheduling import ConstrainedRunwayScheduler


class TestConstrainedRunwayScheduler(unittest.TestCase):
    """Test constrained runway scheduling with various algorithms"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.generator = MultiDayFlightGenerator()
        self.scheduler = ConstrainedRunwayScheduler()
        
    def test_priority_based_algorithm(self):
        """Test priority-based scheduling algorithm"""
        flights = self.generator.generate_multi_day_flights(
            destination="JFK",
            num_days=1,
            flights_per_day=20,
        )
        
        result = self.scheduler.schedule(
            flights=flights,
            max_runways=2,
            algorithm="priority_based"
        )
        
        self.assertIsNotNone(result)
        self.assertEqual(result.algorithm, "priority_based")
        self.assertLessEqual(len(result.runway_assignments), 2)
        
        # Check some flights were delayed
        if len(flights) > 10:  # With 2 runways and many flights, delays expected
            self.assertGreater(len(result.delayed_flights), 0)
            
    def test_passenger_first_algorithm(self):
        """Test passenger count priority algorithm"""
        flights = self.generator.generate_multi_day_flights(
            destination="LAX",
            num_days=1,
            flights_per_day=15,
        )
        
        result = self.scheduler.schedule(
            flights=flights,
            max_runways=3,
            algorithm="passenger_first"
        )
        
        self.assertEqual(result.algorithm, "passenger_first")
        
        # Check that higher passenger flights tend to be scheduled earlier
        # (not delayed or less delayed)
        if result.delayed_flights:
            avg_passengers_delayed = sum(f.passenger_count for f in result.delayed_flights) / len(result.delayed_flights)
            avg_passengers_all = sum(f.passenger_count for f in flights) / len(flights)
            # Delayed flights should have fewer passengers on average
            self.assertLessEqual(avg_passengers_delayed, avg_passengers_all * 1.2)
            
    def test_distance_first_algorithm(self):
        """Test distance priority algorithm"""
        flights = self.generator.generate_multi_day_flights(
            destination="ORD",
            num_days=1,
            flights_per_day=15,
        )
        
        result = self.scheduler.schedule(
            flights=flights,
            max_runways=3,
            algorithm="distance_first"
        )
        
        self.assertEqual(result.algorithm, "distance_first")
        self.assertGreater(result.total_flights, 0)
        
    def test_hybrid_algorithm(self):
        """Test hybrid weighted algorithm"""
        flights = self.generator.generate_multi_day_flights(
            destination="SFO",
            num_days=1,
            flights_per_day=15,
        )
        
        result = self.scheduler.schedule(
            flights=flights,
            max_runways=3,
            algorithm="hybrid"
        )
        
        self.assertEqual(result.algorithm, "hybrid")
        self.assertIsNotNone(result.on_time_percentage)
        
    def test_runway_capacity_constraint(self):
        """Test that runway capacity is respected"""
        flights = self.generator.generate_multi_day_flights(
            destination="BOS",
            num_days=1,
            flights_per_day=10,
        )
        
        max_runways = 2
        result = self.scheduler.schedule(
            flights=flights,
            max_runways=max_runways,
            algorithm="priority_based"
        )
        
        # Check that we don't use more runways than allowed
        self.assertLessEqual(len(result.runway_assignments), max_runways)
        
        # Check that at any given time, no more than max_runways are in use
        for runway_id, runway_flights in result.runway_assignments.items():
            # Verify flights on same runway don't overlap
            sorted_flights = sorted(runway_flights, key=lambda f: f.departure_time)
            for i in range(len(sorted_flights) - 1):
                current_end = sorted_flights[i].departure_time + timedelta(hours=sorted_flights[i].flight_duration)
                next_start = sorted_flights[i + 1].departure_time + timedelta(minutes=sorted_flights[i + 1].delayed_by)
                # Next flight should start after current ends
                self.assertGreaterEqual(next_start, current_end)
                
    def test_delay_tracking(self):
        """Test that delays are properly tracked"""
        flights = self.generator.generate_multi_day_flights(
            destination="MIA",
            num_days=1,
            flights_per_day=25,
        )
        
        result = self.scheduler.schedule(
            flights=flights,
            max_runways=2,
            algorithm="priority_based"
        )
        
        # Check delayed flights have delay values
        for flight in result.delayed_flights:
            self.assertGreater(flight.delayed_by, 0)
            
        # Total delay should match sum of individual delays
        total = sum(f.delayed_by for f in result.delayed_flights)
        self.assertEqual(total, result.total_delay_minutes)
        
        # On-time percentage should be reasonable
        self.assertGreaterEqual(result.on_time_percentage, 0)
        self.assertLessEqual(result.on_time_percentage, 100)
        
    def test_compare_algorithms(self):
        """Test algorithm comparison functionality"""
        flights = self.generator.generate_multi_day_flights(
            destination="SEA",
            num_days=1,
            flights_per_day=20,
        )
        
        comparison = self.scheduler.compare_algorithms(
            flights=flights,
            max_runways=3
        )
        
        # Should have results for all 4 algorithms
        self.assertEqual(len(comparison["comparison"]), 4)
        self.assertIn("priority_based", comparison["comparison"])
        self.assertIn("passenger_first", comparison["comparison"])
        self.assertIn("distance_first", comparison["comparison"])
        self.assertIn("hybrid", comparison["comparison"])
        
        # Each should have stats
        for algo, stats in comparison["comparison"].items():
            self.assertIn("delayed_flights", stats)
            self.assertIn("on_time_percentage", stats)
            self.assertIn("avg_delay_minutes", stats)
            
        # Should identify best algorithm
        self.assertIn("best_algorithm", comparison)
        
    def test_empty_flights(self):
        """Test handling of empty flight list"""
        result = self.scheduler.schedule(
            flights=[],
            max_runways=5,
            algorithm="priority_based"
        )
        
        self.assertEqual(result.total_flights, 0)
        self.assertEqual(len(result.delayed_flights), 0)
        self.assertEqual(result.on_time_percentage, 100.0)
        
    def test_sufficient_runways(self):
        """Test when runways are sufficient (no delays expected)"""
        flights = self.generator.generate_multi_day_flights(
            destination="DEN",
            num_days=1,
            flights_per_day=5,
        )
        
        # Provide more than enough runways
        result = self.scheduler.schedule(
            flights=flights,
            max_runways=10,
            algorithm="priority_based"
        )
        
        # Should have minimal or no delays
        self.assertLess(result.total_delay_minutes, 60)  # Less than 1 hour total
        
    def test_performance_metrics(self):
        """Test that performance metrics are calculated correctly"""
        flights = self.generator.generate_multi_day_flights(
            destination="ATL",
            num_days=1,
            flights_per_day=15,
        )
        
        result = self.scheduler.schedule(
            flights=flights,
            max_runways=3,
            algorithm="hybrid"
        )
        
        # Verify calculations
        on_time_count = result.total_flights - len(result.delayed_flights)
        expected_percentage = (on_time_count / result.total_flights * 100) if result.total_flights > 0 else 100
        self.assertAlmostEqual(result.on_time_percentage, expected_percentage, places=1)
        
        # Average delay calculation
        if result.delayed_flights:
            expected_avg = result.total_delay_minutes / len(result.delayed_flights)
            self.assertAlmostEqual(result.avg_delay_minutes, expected_avg, places=1)


if __name__ == '__main__':
    unittest.main()

"""
Integration tests for multi-day scheduling and constrained runway features
"""
import unittest
from src.utils.multi_day_generator import MultiDayFlightGenerator
from src.algorithms.multi_day_pilot_scheduling import MultiDayPilotScheduler
from src.algorithms.constrained_scheduling import ConstrainedRunwayScheduler
from src.models.pilot import Pilot


class TestMultiDayIntegration(unittest.TestCase):
    """Integration tests for multi-day features"""
    
    def test_full_multi_day_workflow(self):
        """Test complete multi-day workflow"""
        # Generate flights
        generator = MultiDayFlightGenerator()
        flights = generator.generate_multi_day_flights(
            destination="JFK",
            num_days=2,
            flights_per_day=10
        )
        
        # Verify flights generated
        self.assertGreater(len(flights), 0)
        
        # Check attributes exist
        for flight in flights:
            self.assertIsNotNone(flight.passenger_count)
            self.assertIsNotNone(flight.distance)
            self.assertIsNotNone(flight.day)
            
    def test_constrained_scheduling_workflow(self):
        """Test constrained runway scheduling"""
        # Generate flights
        generator = MultiDayFlightGenerator()
        flights = generator.generate_multi_day_flights(
            destination="LAX",
            num_days=1,
            flights_per_day=15
        )
        
        # Schedule with constraints
        scheduler = ConstrainedRunwayScheduler(max_runways=3, algorithm="priority_based")
        result = scheduler.schedule(flights=flights)
        
        # Verify result
        self.assertIsNotNone(result)
        self.assertEqual(result.algorithm, "priority_based")
        self.assertGreaterEqual(result.on_time_percentage, 0)
        self.assertLessEqual(result.on_time_percentage, 100)
        
    def test_algorithm_comparison(self):
        """Test algorithm comparison feature"""
        # Generate flights
        generator = MultiDayFlightGenerator()
        flights = generator.generate_multi_day_flights(
            destination="ORD",
            num_days=1,
            flights_per_day=12
        )
        
        # Compare algorithms - use one scheduler instance and call compare
        scheduler = ConstrainedRunwayScheduler(max_runways=2, algorithm="priority_based")
        comparison = scheduler.compare_algorithms(flights)
        
        # Verify comparison
        self.assertIn("comparison", comparison)
        self.assertIn("best_algorithm", comparison)
        self.assertEqual(len(comparison["comparison"]), 4)


if __name__ == '__main__':
    unittest.main()

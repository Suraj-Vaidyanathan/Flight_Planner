"""
Multi-Day Flight Generator - Creates flights spanning multiple days.

This module generates realistic flight schedules across multiple days
to enable pilot reassignment and multi-day scheduling demonstrations.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import random

from ..models.flight import Flight


class MultiDayFlightGenerator:
    """Generates flights spanning multiple days with realistic patterns."""
    
    # Common airport codes
    AIRPORTS = [
        'JFK', 'LAX', 'ORD', 'DFW', 'ATL', 'SFO', 'MIA', 'BOS', 'SEA', 'DEN',
        'LAS', 'PHX', 'IAH', 'MCO', 'EWR', 'MSP', 'DTW', 'PHL', 'LGA', 'BWI'
    ]
    
    # Passenger count ranges by route type
    PASSENGER_RANGES = {
        'short': (50, 150),      # Short-haul flights
        'medium': (120, 250),    # Medium-haul flights
        'long': (200, 400)       # Long-haul flights
    }
    
    # Distance ranges (km) by route type
    DISTANCE_RANGES = {
        'short': (200, 1000),
        'medium': (1000, 3000),
        'long': (3000, 8000)
    }
    
    def __init__(self, seed: int = None):
        """
        Initialize the generator.
        
        Args:
            seed: Random seed for reproducibility
        """
        if seed is not None:
            random.seed(seed)
    
    def generate_multi_day_flights(
        self,
        destination: str,
        num_days: int = 3,
        flights_per_day: int = 15,
        start_date: datetime = None,
        time_spread_hours: int = 16
    ) -> List[Flight]:
        """
        Generate flights spanning multiple days.
        
        Args:
            destination: Destination airport code
            num_days: Number of days to generate flights for
            flights_per_day: Average number of flights per day
            start_date: Start date (defaults to today)
            time_spread_hours: Hours in the day to spread flights (e.g., 6 AM to 10 PM = 16 hours)
            
        Returns:
            List of Flight objects spanning multiple days
        """
        if start_date is None:
            start_date = datetime.now().replace(hour=6, minute=0, second=0, microsecond=0)
        
        all_flights = []
        flight_counter = 1
        
        for day in range(num_days):
            day_start = start_date + timedelta(days=day)
            
            # Vary flights per day slightly for realism
            day_flights = flights_per_day + random.randint(-3, 3)
            day_flights = max(5, day_flights)  # At least 5 flights per day
            
            # Generate flights for this day
            for i in range(day_flights):
                # Spread flights throughout the day
                hour_offset = (i / day_flights) * time_spread_hours
                minutes_offset = random.randint(-30, 30)
                
                arrival_time = day_start + timedelta(hours=hour_offset, minutes=minutes_offset)
                
                # Generate flight
                flight = self._generate_flight(
                    flight_number=flight_counter,
                    destination=destination,
                    arrival_time=arrival_time,
                    day=day
                )
                
                all_flights.append(flight)
                flight_counter += 1
        
        # Sort by arrival time
        all_flights.sort(key=lambda f: f.arrival_start)
        
        return all_flights
    
    def _generate_flight(
        self,
        flight_number: int,
        destination: str,
        arrival_time: datetime,
        day: int
    ) -> Flight:
        """
        Generate a single flight with realistic attributes.
        
        Args:
            flight_number: Sequential flight number
            destination: Destination airport
            arrival_time: Scheduled arrival time
            day: Day number (0-indexed)
            
        Returns:
            Flight object with all attributes
        """
        # Select origin airport (not the destination)
        origin = random.choice([a for a in self.AIRPORTS if a != destination])
        
        # Determine route type based on random selection
        route_type = random.choices(
            ['short', 'medium', 'long'],
            weights=[50, 35, 15]  # Most flights are short/medium haul
        )[0]
        
        # Generate passenger count
        pass_range = self.PASSENGER_RANGES[route_type]
        passenger_count = random.randint(pass_range[0], pass_range[1])
        
        # Generate distance
        dist_range = self.DISTANCE_RANGES[route_type]
        distance = random.randint(dist_range[0], dist_range[1])
        
        # Generate flight duration (hours)
        # Approximate: distance / average speed (800 km/h) + buffer
        flight_duration = (distance / 800.0) + random.uniform(0.5, 1.5)
        
        # Cap flight duration at 7.5 hours to ensure schedulability
        # (leaves 0.5h buffer below FAA 8-hour daily limit)
        flight_duration = min(flight_duration, 7.5)
        
        # Determine priority
        # Higher priority for long-distance, high-passenger flights
        if route_type == 'long' or passenger_count > 300:
            priority = random.randint(1, 3)  # High priority
        elif route_type == 'medium' or passenger_count > 150:
            priority = random.randint(3, 6)  # Medium priority
        else:
            priority = random.randint(5, 10)  # Lower priority
        
        # Runway occupancy time (10-25 minutes)
        occupancy_time = random.randint(10, 25)
        
        # Create flight ID
        flight_id = f"FL{flight_number:04d}"
        
        # Create Flight object
        flight = Flight(
            flight_id=flight_id,
            origin=origin,
            destination=destination,
            arrival_start=arrival_time,
            occupancy_time=occupancy_time,
            priority=priority
        )
        
        # Store additional attributes (extend Flight class with these)
        flight.passenger_count = passenger_count
        flight.distance = distance
        flight.flight_duration = flight_duration
        flight.day = day
        
        return flight
    
    def generate_with_patterns(
        self,
        destination: str,
        num_days: int = 5,
        pattern: str = 'realistic',
        flights_per_day: int = 15
    ) -> List[Flight]:
        """
        Generate flights with specific patterns for testing different algorithms.
        
        Args:
            destination: Destination airport
            num_days: Number of days
            pattern: Pattern type ('realistic', 'peak_hours', 'uniform', 'random')
            flights_per_day: Number of flights per day
            
        Returns:
            List of flights with the specified pattern
        """
        if pattern == 'realistic':
            # Realistic pattern: more flights during peak hours (morning, evening)
            return self._generate_realistic_pattern(destination, num_days, flights_per_day)
        
        elif pattern == 'peak_hours':
            # Heavy concentration during peak hours
            return self._generate_peak_hours_pattern(destination, num_days, flights_per_day)
        
        elif pattern == 'uniform':
            # Evenly distributed throughout the day
            return self._generate_uniform_pattern(destination, num_days, flights_per_day)
        
        elif pattern == 'random':
            # Completely random distribution
            return self._generate_random_pattern(destination, num_days, flights_per_day)
        
        else:
            raise ValueError(f"Unknown pattern: {pattern}")
    
    def _generate_realistic_pattern(self, destination: str, num_days: int, flights_per_day: int = 15) -> List[Flight]:
        """Generate flights with realistic morning/evening peaks."""
        all_flights = []
        flight_counter = 1
        start_date = datetime.now().replace(hour=6, minute=0, second=0, microsecond=0)
        
        # Peak hours: 6-9 AM and 5-8 PM
        peak_morning = [(6, 9), 0.4]   # 40% of flights
        peak_evening = [(17, 20), 0.35]  # 35% of flights
        off_peak = [(9, 17), 0.15]       # 15% of flights
        late = [(20, 23), 0.10]          # 10% of flights
        
        periods = [peak_morning, peak_evening, off_peak, late]
        
        for day in range(num_days):
            day_start = start_date + timedelta(days=day)
            total_flights = flights_per_day + random.randint(-2, 2)
            
            for period_range, proportion in periods:
                num_flights = int(total_flights * proportion)
                start_hour, end_hour = period_range
                
                for _ in range(num_flights):
                    hour = random.randint(start_hour, end_hour - 1)
                    minute = random.randint(0, 59)
                    arrival_time = day_start.replace(hour=hour, minute=minute)
                    
                    flight = self._generate_flight(flight_counter, destination, arrival_time, day)
                    all_flights.append(flight)
                    flight_counter += 1
        
        all_flights.sort(key=lambda f: f.arrival_start)
        return all_flights
    
    def _generate_peak_hours_pattern(self, destination: str, num_days: int, flights_per_day: int = 15) -> List[Flight]:
        """Generate flights concentrated in peak hours."""
        all_flights = []
        flight_counter = 1
        start_date = datetime.now().replace(hour=6, minute=0, second=0, microsecond=0)
        
        for day in range(num_days):
            day_start = start_date + timedelta(days=day)
            
            # 80% of flights in peak hours (7-9 AM, 6-8 PM)
            peak_flights = flights_per_day + random.randint(-2, 2)
            
            for _ in range(peak_flights):
                # Choose morning or evening peak
                if random.random() < 0.5:
                    hour = random.randint(7, 8)
                else:
                    hour = random.randint(18, 19)
                
                minute = random.randint(0, 59)
                arrival_time = day_start.replace(hour=hour, minute=minute)
                
                flight = self._generate_flight(flight_counter, destination, arrival_time, day)
                all_flights.append(flight)
                flight_counter += 1
        
        all_flights.sort(key=lambda f: f.arrival_start)
        return all_flights
    
    def _generate_uniform_pattern(self, destination: str, num_days: int, flights_per_day: int = 15) -> List[Flight]:
        """Generate uniformly distributed flights."""
        all_flights = []
        flight_counter = 1
        start_date = datetime.now().replace(hour=6, minute=0, second=0, microsecond=0)
        
        for day in range(num_days):
            day_start = start_date + timedelta(days=day)
            day_flights = flights_per_day + random.randint(-2, 2)
            
            for i in range(day_flights):
                # Evenly space flights from 6 AM to 11 PM (17 hours)
                hour = 6 + int((i / day_flights) * 17)
                minute = random.randint(0, 59)
                arrival_time = day_start.replace(hour=min(hour, 23), minute=minute)
                
                flight = self._generate_flight(flight_counter, destination, arrival_time, day)
                all_flights.append(flight)
                flight_counter += 1
        
        all_flights.sort(key=lambda f: f.arrival_start)
        return all_flights
    
    def _generate_random_pattern(self, destination: str, num_days: int, flights_per_day: int = 15) -> List[Flight]:
        """Generate completely random flight distribution."""
        all_flights = []
        flight_counter = 1
        start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        for day in range(num_days):
            day_start = start_date + timedelta(days=day)
            day_flights = flights_per_day + random.randint(-3, 3)
            
            for _ in range(flights_per_day):
                hour = random.randint(0, 23)
                minute = random.randint(0, 59)
                arrival_time = day_start.replace(hour=hour, minute=minute)
                
                flight = self._generate_flight(flight_counter, destination, arrival_time, day)
                all_flights.append(flight)
                flight_counter += 1
        
        all_flights.sort(key=lambda f: f.arrival_start)
        return all_flights

"""
Fixed-Constraint Runway Scheduler - Assigns flights with limited runways.

This module implements runway scheduling with a fixed maximum number of runways,
requiring some flights to be delayed. Multiple algorithms prioritize flights
based on different criteria (priority, passenger count, distance).
"""

from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional
from datetime import datetime, timedelta
import heapq

from ..models.flight import Flight


@dataclass
class ConstrainedScheduleResult:
    """
    Result of constrained runway scheduling.
    
    Attributes:
        flights: List of scheduled flights (some may be delayed)
        num_runways: Number of runways used (max allowed)
        runway_assignments: Dict mapping runway_id to list of flights
        delayed_flights: List of flights that were delayed
        total_delay_minutes: Total minutes of delay across all flights
        avg_delay_minutes: Average delay per delayed flight
        on_time_percentage: Percentage of flights not delayed
    """
    flights: List[Flight]
    num_runways: int
    runway_assignments: Dict[int, List[Flight]] = field(default_factory=dict)
    delayed_flights: List[Flight] = field(default_factory=list)
    total_delay_minutes: int = 0
    avg_delay_minutes: float = 0.0
    on_time_percentage: float = 100.0
    
    def __post_init__(self):
        """Calculate metrics."""
        if self.delayed_flights:
            self.avg_delay_minutes = self.total_delay_minutes / len(self.delayed_flights)
        
        if self.flights:
            self.on_time_percentage = ((len(self.flights) - len(self.delayed_flights)) / 
                                      len(self.flights) * 100)
    
    def __str__(self) -> str:
        result = [
            "=" * 80,
            "CONSTRAINED RUNWAY SCHEDULING RESULT",
            "=" * 80,
            f"Maximum Runways Allowed: {self.num_runways}",
            f"Total Flights: {len(self.flights)}",
            f"On-Time Flights: {len(self.flights) - len(self.delayed_flights)}",
            f"Delayed Flights: {len(self.delayed_flights)}",
            f"On-Time Percentage: {self.on_time_percentage:.1f}%",
            f"Total Delay: {self.total_delay_minutes} minutes",
            f"Average Delay: {self.avg_delay_minutes:.1f} minutes per delayed flight",
            "-" * 80,
        ]
        
        for runway_id in sorted(self.runway_assignments.keys()):
            flights = self.runway_assignments[runway_id]
            result.append(f"\nRUNWAY {runway_id}: ({len(flights)} flights)")
            result.append("-" * 50)
            
            sorted_flights = sorted(flights, key=lambda f: f.arrival_start)
            
            for flight in sorted_flights:
                delay_str = f"(DELAYED {flight.delayed_by}min)" if flight.delayed_by > 0 else ""
                result.append(
                    f"  {flight.flight_id}: {flight.origin} -> {flight.destination} | "
                    f"{flight.arrival_start.strftime('%d %H:%M')} - "
                    f"{flight.arrival_end.strftime('%H:%M')} | "
                    f"P:{flight.priority} | Pass:{flight.passenger_count} {delay_str}"
                )
        
        result.append("\n" + "=" * 80)
        return "\n".join(result)


class ConstrainedRunwayScheduler:
    """
    Runway scheduler with fixed maximum runways.
    
    Assigns flights to limited runways, delaying flights when necessary.
    Supports multiple algorithms based on different priority criteria.
    """
    
    # Minimum delay increment (minutes)
    DELAY_INCREMENT = 15
    
    # Maximum allowed delay (minutes)
    MAX_DELAY = 240  # 4 hours
    
    def __init__(self, max_runways: int, algorithm: str = 'priority_based'):
        """
        Initialize the constrained scheduler.
        
        Args:
            max_runways: Maximum number of runways available
            algorithm: Scheduling algorithm ('priority_based', 'passenger_first', 
                      'distance_first', 'hybrid')
        """
        if max_runways < 1:
            raise ValueError("Must have at least 1 runway")
        
        self._max_runways = max_runways
        self._algorithm = algorithm.lower()
        
        valid_algorithms = ['priority_based', 'passenger_first', 'distance_first', 'hybrid']
        if self._algorithm not in valid_algorithms:
            raise ValueError(f"Unknown algorithm: {algorithm}. Use one of {valid_algorithms}")
    
    def _calculate_flight_score(self, flight: Flight) -> float:
        """
        Calculate priority score for a flight based on algorithm.
        
        Lower score = higher priority (processed first).
        
        Args:
            flight: Flight to score
            
        Returns:
            Priority score (lower is better)
        """
        if self._algorithm == 'priority_based':
            # Use flight priority directly
            return float(flight.priority)
        
        elif self._algorithm == 'passenger_first':
            # Prioritize by passenger count (more passengers = higher priority)
            # Normalize to 0-10 range (inverse, so higher passengers = lower score)
            return 10.0 - (min(flight.passenger_count, 500) / 50.0)
        
        elif self._algorithm == 'distance_first':
            # Prioritize by distance (longer flights = higher priority)
            # Normalize to 0-10 range (inverse)
            return 10.0 - (min(flight.distance, 10000) / 1000.0)
        
        elif self._algorithm == 'hybrid':
            # Weighted combination of priority, passengers, and distance
            priority_score = flight.priority * 0.4
            passenger_score = (10.0 - min(flight.passenger_count, 500) / 50.0) * 0.35
            distance_score = (10.0 - min(flight.distance, 10000) / 1000.0) * 0.25
            
            return priority_score + passenger_score + distance_score
        
        return float(flight.priority)
    
    def _find_available_runway(
        self, 
        flight: Flight, 
        runway_schedules: Dict[int, List[Tuple[datetime, datetime]]]
    ) -> Optional[int]:
        """
        Find a runway that can accommodate the flight at its current time.
        
        Args:
            flight: Flight to schedule
            runway_schedules: Dict mapping runway_id to list of (start, end) times
            
        Returns:
            Runway ID if available, None otherwise
        """
        for runway_id in range(1, self._max_runways + 1):
            if runway_id not in runway_schedules:
                runway_schedules[runway_id] = []
            
            # Check if flight conflicts with any scheduled flight on this runway
            conflicts = False
            for scheduled_start, scheduled_end in runway_schedules[runway_id]:
                # Check overlap
                if (flight.arrival_start < scheduled_end and 
                    flight.arrival_end > scheduled_start):
                    conflicts = True
                    break
            
            if not conflicts:
                return runway_id
        
        return None
    
    def _find_earliest_slot(
        self,
        flight: Flight,
        runway_id: int,
        runway_schedules: Dict[int, List[Tuple[datetime, datetime]]]
    ) -> Tuple[datetime, int]:
        """
        Find the earliest available time slot on a runway.
        
        Args:
            flight: Flight to schedule
            runway_id: Target runway
            runway_schedules: Current runway schedules
            
        Returns:
            Tuple of (new_arrival_time, delay_minutes)
        """
        if runway_id not in runway_schedules or not runway_schedules[runway_id]:
            return flight.arrival_start, 0
        
        # Sort scheduled times
        scheduled = sorted(runway_schedules[runway_id], key=lambda x: x[0])
        
        # Try to fit in original time
        current_time = flight.arrival_start
        
        for delay in range(0, self.MAX_DELAY, self.DELAY_INCREMENT):
            new_start = flight.arrival_start + timedelta(minutes=delay)
            new_end = new_start + timedelta(minutes=flight.occupancy_time)
            
            # Check if this slot is available
            conflicts = False
            for scheduled_start, scheduled_end in scheduled:
                if new_start < scheduled_end and new_end > scheduled_start:
                    conflicts = True
                    break
            
            if not conflicts:
                return new_start, delay
        
        # If no slot found within MAX_DELAY, place after last flight
        last_end = max(end for _, end in scheduled)
        new_start = max(last_end, flight.arrival_start)
        delay = int((new_start - flight.arrival_start).total_seconds() / 60)
        
        return new_start, delay
    
    def schedule(self, flights: List[Flight]) -> ConstrainedScheduleResult:
        """
        Schedule flights to limited runways with delays as needed.
        
        Args:
            flights: List of flights to schedule
            
        Returns:
            ConstrainedScheduleResult with assignments and delays
        """
        if not flights:
            return ConstrainedScheduleResult(flights=[], num_runways=self._max_runways)
        
        # Create copies of flights to avoid modifying originals
        flights = [Flight(
            flight_id=f.flight_id,
            origin=f.origin,
            destination=f.destination,
            arrival_start=f.arrival_start,
            occupancy_time=f.occupancy_time,
            priority=f.priority,
            passenger_count=f.passenger_count,
            distance=f.distance,
            flight_duration=f.flight_duration,
            day=f.day,
            delayed_by=0
        ) for f in flights]
        
        # Calculate scores and sort flights by priority
        flight_scores = [(self._calculate_flight_score(f), f) for f in flights]
        flight_scores.sort(key=lambda x: (x[0], x[1].arrival_start))  # Sort by score, then time
        
        sorted_flights = [f for _, f in flight_scores]
        
        # Track runway schedules: runway_id -> list of (start, end) times
        runway_schedules: Dict[int, List[Tuple[datetime, datetime]]] = {}
        
        # Track assignments
        runway_assignments: Dict[int, List[Flight]] = {
            i: [] for i in range(1, self._max_runways + 1)
        }
        
        delayed_flights = []
        total_delay_minutes = 0
        
        # Schedule each flight
        for flight in sorted_flights:
            # Try to find available runway at current time
            runway_id = self._find_available_runway(flight, runway_schedules)
            
            if runway_id is not None:
                # Flight can be scheduled on time
                flight.runway_id = runway_id
                runway_schedules[runway_id].append((flight.arrival_start, flight.arrival_end))
                runway_assignments[runway_id].append(flight)
            
            else:
                # Need to delay the flight - find best runway
                best_runway = None
                best_delay = float('inf')
                best_time = None
                
                for runway_id in range(1, self._max_runways + 1):
                    new_time, delay = self._find_earliest_slot(flight, runway_id, runway_schedules)
                    
                    if delay < best_delay:
                        best_delay = delay
                        best_runway = runway_id
                        best_time = new_time
                
                # Assign to best runway with delay
                flight.arrival_start = best_time
                flight.arrival_end = best_time + timedelta(minutes=flight.occupancy_time)
                flight.runway_id = best_runway
                flight.delayed_by = best_delay
                
                runway_schedules[best_runway].append((flight.arrival_start, flight.arrival_end))
                runway_assignments[best_runway].append(flight)
                
                delayed_flights.append(flight)
                total_delay_minutes += best_delay
        
        return ConstrainedScheduleResult(
            flights=sorted_flights,
            num_runways=self._max_runways,
            runway_assignments=runway_assignments,
            delayed_flights=delayed_flights,
            total_delay_minutes=total_delay_minutes
        )
    
    def get_statistics(self, result: ConstrainedScheduleResult) -> Dict[str, any]:
        """
        Generate detailed statistics for a scheduling result.
        
        Args:
            result: Scheduling result
            
        Returns:
            Dictionary of statistics
        """
        stats = {
            'total_flights': len(result.flights),
            'on_time_flights': len(result.flights) - len(result.delayed_flights),
            'delayed_flights': len(result.delayed_flights),
            'on_time_percentage': result.on_time_percentage,
            'total_delay_minutes': result.total_delay_minutes,
            'avg_delay_minutes': result.avg_delay_minutes,
            'max_delay_minutes': max((f.delayed_by for f in result.delayed_flights), default=0),
            'runways_used': self._max_runways,
            'flights_per_runway': {}
        }
        
        # Calculate flights per runway
        for runway_id, flights in result.runway_assignments.items():
            stats['flights_per_runway'][runway_id] = len(flights)
        
        # Calculate delay distribution
        if result.delayed_flights:
            delays = [f.delayed_by for f in result.delayed_flights]
            stats['delay_distribution'] = {
                'min': min(delays),
                'max': max(delays),
                'avg': sum(delays) / len(delays)
            }
        
        return stats
    
    def compare_algorithms(
        self, 
        flights: List[Flight], 
        max_runways: int
    ) -> Dict[str, ConstrainedScheduleResult]:
        """
        Compare all algorithms on the same set of flights.
        
        Args:
            flights: List of flights to schedule
            max_runways: Maximum runways to use
            
        Returns:
            Dict mapping algorithm name to results
        """
        algorithms = ['priority_based', 'passenger_first', 'distance_first', 'hybrid']
        results = {}
        
        for algo in algorithms:
            scheduler = ConstrainedRunwayScheduler(max_runways, algo)
            results[algo] = scheduler.schedule(flights)
        
        return results

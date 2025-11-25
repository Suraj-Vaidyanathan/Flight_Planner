"""
Flight Model - Represents a scheduled flight for runway scheduling.

This module defines the Flight class which stores flight information
including arrival time windows for conflict detection in runway scheduling.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional
import uuid


@dataclass
class Flight:
    """
    Represents a flight node in the scheduling conflict graph.
    
    Attributes:
        flight_id (str): Unique flight identifier
        origin (str): Origin airport code
        destination (str): Destination airport code
        arrival_start (datetime): Start of arrival time window
        arrival_end (datetime): End of arrival time window (after runway clearance)
        occupancy_time (int): Time needed to land and clear runway (in minutes)
        runway_id (Optional[int]): Assigned runway ID after scheduling
        priority (int): Flight priority (1=highest, lower numbers = higher priority)
    """
    flight_id: str
    origin: str
    destination: str
    arrival_start: datetime
    occupancy_time: int = field(default=15)  # Default 15 minutes
    arrival_end: datetime = field(init=False)
    runway_id: Optional[int] = field(default=None)
    priority: int = field(default=5)  # Default medium priority
    
    def __post_init__(self):
        """Calculate arrival end time and validate data."""
        if self.occupancy_time <= 0:
            raise ValueError(f"Occupancy time must be positive: {self.occupancy_time}")
        
        # Calculate arrival end time based on occupancy time
        self.arrival_end = self.arrival_start + timedelta(minutes=self.occupancy_time)
        
        if self.priority < 1 or self.priority > 10:
            raise ValueError(f"Priority must be between 1-10: {self.priority}")
    
    def overlaps_with(self, other: 'Flight') -> bool:
        """
        Check if this flight's time window overlaps with another flight.
        
        Two flights conflict if their landing windows overlap:
        - Flight A lands during Flight B's window, or
        - Flight B lands during Flight A's window
        
        Args:
            other: Another Flight object
            
        Returns:
            True if the flights have overlapping time windows
        """
        # Two intervals [a1, a2] and [b1, b2] overlap if:
        # a1 < b2 AND b1 < a2
        return (self.arrival_start < other.arrival_end and 
                other.arrival_start < self.arrival_end)
    
    def get_overlap_duration(self, other: 'Flight') -> int:
        """
        Calculate the overlap duration with another flight in minutes.
        
        Args:
            other: Another Flight object
            
        Returns:
            Overlap duration in minutes (0 if no overlap)
        """
        if not self.overlaps_with(other):
            return 0
        
        overlap_start = max(self.arrival_start, other.arrival_start)
        overlap_end = min(self.arrival_end, other.arrival_end)
        
        return int((overlap_end - overlap_start).total_seconds() / 60)
    
    @classmethod
    def generate_random(cls, destination: str, base_time: datetime, 
                       flight_number: int = None, 
                       max_offset_minutes: int = 120,
                       occupancy_range: tuple = (10, 20)) -> 'Flight':
        """
        Generate a random flight for simulation purposes.
        
        Args:
            destination: Destination airport code
            base_time: Base time around which to generate arrival
            flight_number: Optional flight number for ID generation
            max_offset_minutes: Maximum time offset from base_time
            occupancy_range: Tuple of (min, max) occupancy time in minutes
            
        Returns:
            A randomly generated Flight object
        """
        import random
        
        # Generate flight ID
        if flight_number is not None:
            flight_id = f"FL{flight_number:04d}"
        else:
            flight_id = f"FL{random.randint(1000, 9999)}"
        
        # Random origin (simplified)
        origins = ['JFK', 'LAX', 'ORD', 'DFW', 'ATL', 'SFO', 'MIA', 'BOS', 'SEA', 'DEN']
        origin = random.choice(origins)
        
        # Random arrival time offset
        offset = random.randint(-max_offset_minutes, max_offset_minutes)
        arrival_start = base_time + timedelta(minutes=offset)
        
        # Random occupancy time
        occupancy = random.randint(occupancy_range[0], occupancy_range[1])
        
        # Random priority
        priority = random.randint(1, 10)
        
        return cls(
            flight_id=flight_id,
            origin=origin,
            destination=destination,
            arrival_start=arrival_start,
            occupancy_time=occupancy,
            priority=priority
        )
    
    def __hash__(self):
        """Allow Flight to be used in sets and as dictionary keys."""
        return hash(self.flight_id)
    
    def __eq__(self, other):
        """Check equality based on flight ID."""
        if isinstance(other, Flight):
            return self.flight_id == other.flight_id
        return False
    
    def __lt__(self, other):
        """Enable sorting by arrival time."""
        if isinstance(other, Flight):
            return self.arrival_start < other.arrival_start
        return NotImplemented
    
    def __repr__(self):
        return f"Flight({self.flight_id}, {self.origin}->{self.destination})"
    
    def __str__(self):
        runway_str = f"Runway {self.runway_id}" if self.runway_id else "Unassigned"
        return (f"{self.flight_id}: {self.origin} -> {self.destination} | "
                f"Arrival: {self.arrival_start.strftime('%H:%M')} - "
                f"{self.arrival_end.strftime('%H:%M')} | {runway_str}")

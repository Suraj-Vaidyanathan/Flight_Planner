"""
Pilot Model - Represents a pilot for flight assignments.

This module defines the Pilot class which stores pilot information
including duty hours, rest periods, and flight assignments.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional
import uuid


@dataclass
class Pilot:
    """
    Represents a pilot available for flight assignments.
    
    Attributes:
        pilot_id (str): Unique pilot identifier
        name (str): Pilot name
        certification (str): Pilot certification level (e.g., 'ATP', 'Commercial')
        max_daily_hours (float): Maximum daily flying hours allowed
        min_rest_hours (float): Minimum rest hours required between flights
        assigned_flights (List[str]): List of assigned flight IDs
        last_flight_end (Optional[datetime]): End time of last assigned flight
        total_hours_today (float): Total flying hours accumulated today
        home_base (str): Home base airport code
    """
    pilot_id: str
    name: str
    certification: str = field(default='ATP')  # ATP = Airline Transport Pilot
    max_daily_hours: float = field(default=8.0)  # FAA regulation: 8 hours
    min_rest_hours: float = field(default=10.0)  # FAA regulation: 10 hours rest
    assigned_flights: List[str] = field(default_factory=list)
    last_flight_end: Optional[datetime] = field(default=None)
    total_hours_today: float = field(default=0.0)
    home_base: str = field(default='')
    
    def __post_init__(self):
        """Validate pilot data."""
        if self.max_daily_hours <= 0:
            raise ValueError(f"Max daily hours must be positive: {self.max_daily_hours}")
        
        if self.min_rest_hours < 0:
            raise ValueError(f"Min rest hours cannot be negative: {self.min_rest_hours}")
    
    def can_fly(self, flight_start: datetime, flight_duration_hours: float) -> bool:
        """
        Check if pilot can take a flight based on rest and duty limits.
        
        Args:
            flight_start: Start time of the flight
            flight_duration_hours: Duration of the flight in hours
            
        Returns:
            True if pilot can take the flight, False otherwise
        """
        # Check if total hours would exceed daily limit
        if self.total_hours_today + flight_duration_hours > self.max_daily_hours:
            return False
        
        # Check if pilot has had sufficient rest since last flight
        if self.last_flight_end is not None:
            rest_time = (flight_start - self.last_flight_end).total_seconds() / 3600  # hours
            if rest_time < self.min_rest_hours:
                return False
        
        return True
    
    def assign_flight(self, flight_id: str, flight_start: datetime, 
                     flight_end: datetime, flight_duration_hours: float):
        """
        Assign a flight to this pilot.
        
        Args:
            flight_id: ID of the flight to assign
            flight_start: Start time of the flight
            flight_end: End time of the flight
            flight_duration_hours: Duration of the flight in hours
        """
        if not self.can_fly(flight_start, flight_duration_hours):
            raise ValueError(
                f"Cannot assign flight {flight_id} to pilot {self.pilot_id}: "
                f"Would violate duty or rest requirements"
            )
        
        self.assigned_flights.append(flight_id)
        self.last_flight_end = flight_end
        self.total_hours_today += flight_duration_hours
    
    def get_availability_time(self) -> Optional[datetime]:
        """
        Get the earliest time this pilot can take another flight.
        
        Returns:
            Datetime when pilot is available, or None if available now
        """
        if self.last_flight_end is None:
            return None
        
        return self.last_flight_end + timedelta(hours=self.min_rest_hours)
    
    def get_remaining_hours(self) -> float:
        """
        Get remaining flying hours available today.
        
        Returns:
            Hours remaining for duty today
        """
        return max(0.0, self.max_daily_hours - self.total_hours_today)
    
    def reset_daily_hours(self):
        """Reset daily hours counter (for new day)."""
        self.total_hours_today = 0.0
    
    def __str__(self) -> str:
        availability = self.get_availability_time()
        avail_str = "Available now" if availability is None else f"Available at {availability.strftime('%H:%M')}"
        
        return (
            f"Pilot {self.pilot_id} ({self.name}) | {self.certification} | "
            f"Base: {self.home_base} | Flights: {len(self.assigned_flights)} | "
            f"Hours: {self.total_hours_today:.1f}/{self.max_daily_hours:.1f} | {avail_str}"
        )
    
    def __repr__(self) -> str:
        return self.__str__()


@dataclass
class PilotAssignment:
    """
    Represents an assignment of a pilot to a flight.
    
    Attributes:
        pilot_id (str): ID of assigned pilot
        flight_id (str): ID of assigned flight
        assignment_time (datetime): When assignment was made
        flight_start (datetime): Flight start time
        flight_end (datetime): Flight end time
    """
    pilot_id: str
    flight_id: str
    assignment_time: datetime
    flight_start: datetime
    flight_end: datetime
    
    def __str__(self) -> str:
        return (
            f"Assignment: Pilot {self.pilot_id} -> Flight {self.flight_id} | "
            f"{self.flight_start.strftime('%H:%M')} - {self.flight_end.strftime('%H:%M')}"
        )

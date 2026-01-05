"""
Pilot Scheduling Algorithm - Ethical assignment of pilots to flights.

This module implements an ethical pilot scheduler that respects FAA regulations
and ensures sufficient rest periods between flight assignments.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Set
from datetime import datetime, timedelta
import random

from ..models.pilot import Pilot, PilotAssignment
from ..models.flight import Flight


@dataclass
class PilotScheduleResult:
    """
    Represents the result of pilot scheduling.
    
    Attributes:
        assignments: List of pilot-flight assignments
        unassigned_flights: List of flights that couldn't be assigned
        pilot_utilization: Dict mapping pilot_id to utilization percentage
        total_pilots_used: Number of pilots used
        compliance_rate: Percentage of flights successfully assigned
    """
    assignments: List[PilotAssignment]
    unassigned_flights: List[Flight] = field(default_factory=list)
    pilot_utilization: Dict[str, float] = field(default_factory=dict)
    total_pilots_used: int = 0
    compliance_rate: float = 0.0
    
    def __str__(self) -> str:
        result = [
            "=" * 70,
            "PILOT SCHEDULING RESULT",
            "=" * 70,
            f"Total Flights: {len(self.assignments) + len(self.unassigned_flights)}",
            f"Successfully Assigned: {len(self.assignments)}",
            f"Unassigned: {len(self.unassigned_flights)}",
            f"Compliance Rate: {self.compliance_rate:.1f}%",
            f"Pilots Used: {self.total_pilots_used}",
            "-" * 70,
        ]
        
        if self.assignments:
            result.append("\nASSIGNMENTS:")
            result.append("-" * 40)
            
            # Sort by flight start time
            sorted_assignments = sorted(self.assignments, key=lambda a: a.flight_start)
            
            for assignment in sorted_assignments:
                result.append(f"  {assignment}")
        
        if self.pilot_utilization:
            result.append("\nPILOT UTILIZATION:")
            result.append("-" * 40)
            for pilot_id, util in sorted(self.pilot_utilization.items()):
                result.append(f"  Pilot {pilot_id}: {util:.1f}%")
        
        if self.unassigned_flights:
            result.append("\nUNASSIGNED FLIGHTS:")
            result.append("-" * 40)
            for flight in self.unassigned_flights:
                result.append(
                    f"  {flight.flight_id}: {flight.origin} -> {flight.destination} at "
                    f"{flight.arrival_start.strftime('%H:%M')}"
                )
        
        result.append("\n" + "=" * 70)
        return "\n".join(result)
    
    def get_assignment_table(self) -> str:
        """Generate a formatted assignment table."""
        lines = [
            "+----------+----------+--------+-------+-------------+-------------+",
            "| Flight   | Pilot    | Origin | Dest  | Start       | End         |",
            "+----------+----------+--------+-------+-------------+-------------+",
        ]
        
        sorted_assignments = sorted(self.assignments, key=lambda a: a.flight_start)
        
        for assignment in sorted_assignments:
            lines.append(
                f"| {assignment.flight_id:8} | {assignment.pilot_id:8} | "
                f"{assignment.flight_start.strftime('%H:%M'):11} | "
                f"{assignment.flight_end.strftime('%H:%M'):11} |"
            )
        
        lines.append("+----------+----------+--------+-------+-------------+-------------+")
        return "\n".join(lines)


class PilotScheduler:
    """
    Ethical pilot scheduling engine.
    
    Assigns pilots to flights while respecting:
    - FAA duty time regulations (max 8 hours per day)
    - Minimum rest requirements (10 hours between flights)
    - Fair workload distribution
    """
    
    def __init__(self, min_rest_hours: float = 10.0, max_daily_hours: float = 8.0):
        """
        Initialize the pilot scheduler.
        
        Args:
            min_rest_hours: Minimum rest hours required between flights (default: 10)
            max_daily_hours: Maximum daily flying hours (default: 8)
        """
        self.min_rest_hours = min_rest_hours
        self.max_daily_hours = max_daily_hours
        self._pilots: List[Pilot] = []
    
    def add_pilot(self, pilot: Pilot):
        """
        Add a pilot to the scheduler.
        
        Args:
            pilot: Pilot object to add
        """
        self._pilots.append(pilot)
    
    def create_pilots(self, count: int, base_airport: str = '') -> List[Pilot]:
        """
        Create a fleet of pilots.
        
        Args:
            count: Number of pilots to create
            base_airport: Home base airport code
            
        Returns:
            List of created Pilot objects
        """
        names = [
            "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", 
            "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez",
            "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin"
        ]
        
        pilots = []
        for i in range(count):
            name = f"Capt. {names[i % len(names)]}"
            if i >= len(names):
                name += f" {i // len(names) + 1}"
            
            pilot = Pilot(
                pilot_id=f"P{i+1:03d}",
                name=name,
                certification='ATP',
                max_daily_hours=self.max_daily_hours,
                min_rest_hours=self.min_rest_hours,
                home_base=base_airport
            )
            pilots.append(pilot)
            self._pilots.append(pilot)
        
        return pilots
    
    def _calculate_flight_duration(self, flight: Flight) -> float:
        """
        Calculate flight duration in hours.
        
        Args:
            flight: Flight object
            
        Returns:
            Duration in hours
        """
        # For simplicity, assume flight duration is occupancy_time + buffer
        # In reality, this would be the actual flight time
        duration_minutes = flight.occupancy_time + 30  # Add prep time
        return duration_minutes / 60.0
    
    def _find_available_pilot(self, flight: Flight, strategy: str = 'least_busy') -> Optional[Pilot]:
        """
        Find an available pilot for a flight.
        
        Args:
            flight: Flight to assign
            strategy: Selection strategy ('least_busy', 'most_available', 'round_robin')
            
        Returns:
            Available Pilot or None if no pilot is available
        """
        duration = self._calculate_flight_duration(flight)
        available_pilots = []
        
        for pilot in self._pilots:
            if pilot.can_fly(flight.arrival_start, duration):
                available_pilots.append(pilot)
        
        if not available_pilots:
            return None
        
        # Apply selection strategy
        if strategy == 'least_busy':
            # Prefer pilot with fewest hours today (fairness)
            return min(available_pilots, key=lambda p: p.total_hours_today)
        
        elif strategy == 'most_available':
            # Prefer pilot with most remaining hours
            return max(available_pilots, key=lambda p: p.get_remaining_hours())
        
        elif strategy == 'round_robin':
            # Prefer pilot with fewest assignments
            return min(available_pilots, key=lambda p: len(p.assigned_flights))
        
        else:
            return available_pilots[0]
    
    def schedule(self, flights: List[Flight], strategy: str = 'least_busy') -> PilotScheduleResult:
        """
        Schedule pilots to flights using ethical constraints.
        
        Args:
            flights: List of Flight objects to assign pilots to
            strategy: Assignment strategy ('least_busy', 'most_available', 'round_robin')
            
        Returns:
            PilotScheduleResult with pilot assignments
        """
        if not flights:
            return PilotScheduleResult(assignments=[], compliance_rate=100.0)
        
        if not self._pilots:
            # No pilots available
            return PilotScheduleResult(
                assignments=[],
                unassigned_flights=flights,
                compliance_rate=0.0
            )
        
        # Reset all pilots' daily hours
        for pilot in self._pilots:
            pilot.reset_daily_hours()
            pilot.assigned_flights = []
            pilot.last_flight_end = None
        
        assignments: List[PilotAssignment] = []
        unassigned_flights: List[Flight] = []
        
        # Sort flights by start time (greedy scheduling)
        sorted_flights = sorted(flights, key=lambda f: f.arrival_start)
        
        for flight in sorted_flights:
            pilot = self._find_available_pilot(flight, strategy)
            
            if pilot is None:
                unassigned_flights.append(flight)
                continue
            
            # Assign pilot to flight
            duration = self._calculate_flight_duration(flight)
            flight_end = flight.arrival_start + timedelta(hours=duration)
            
            pilot.assign_flight(flight.flight_id, flight.arrival_start, flight_end, duration)
            
            assignment = PilotAssignment(
                pilot_id=pilot.pilot_id,
                flight_id=flight.flight_id,
                assignment_time=datetime.now(),
                flight_start=flight.arrival_start,
                flight_end=flight_end
            )
            assignments.append(assignment)
        
        # Calculate utilization
        pilot_utilization = {}
        pilots_used = set()
        
        for pilot in self._pilots:
            if pilot.assigned_flights:
                pilots_used.add(pilot.pilot_id)
                utilization = (pilot.total_hours_today / pilot.max_daily_hours) * 100
                pilot_utilization[pilot.pilot_id] = utilization
        
        compliance_rate = (len(assignments) / len(flights)) * 100 if flights else 100.0
        
        return PilotScheduleResult(
            assignments=assignments,
            unassigned_flights=unassigned_flights,
            pilot_utilization=pilot_utilization,
            total_pilots_used=len(pilots_used),
            compliance_rate=compliance_rate
        )
    
    def validate_schedule(self, assignments: List[PilotAssignment]) -> Tuple[bool, List[str]]:
        """
        Validate that a pilot schedule respects all constraints.
        
        Args:
            assignments: List of PilotAssignment objects
            
        Returns:
            Tuple of (is_valid, list of violation descriptions)
        """
        violations = []
        
        # Group assignments by pilot
        pilot_assignments: Dict[str, List[PilotAssignment]] = {}
        for assignment in assignments:
            if assignment.pilot_id not in pilot_assignments:
                pilot_assignments[assignment.pilot_id] = []
            pilot_assignments[assignment.pilot_id].append(assignment)
        
        # Check each pilot's schedule
        for pilot_id, pilot_assign in pilot_assignments.items():
            # Sort by flight start time
            sorted_assign = sorted(pilot_assign, key=lambda a: a.flight_start)
            
            # Check total hours
            total_hours = sum(
                (a.flight_end - a.flight_start).total_seconds() / 3600
                for a in sorted_assign
            )
            
            if total_hours > self.max_daily_hours:
                violations.append(
                    f"Pilot {pilot_id} exceeds max daily hours: {total_hours:.1f} > {self.max_daily_hours}"
                )
            
            # Check rest periods
            for i in range(len(sorted_assign) - 1):
                current = sorted_assign[i]
                next_flight = sorted_assign[i + 1]
                
                rest_time = (next_flight.flight_start - current.flight_end).total_seconds() / 3600
                
                if rest_time < self.min_rest_hours:
                    violations.append(
                        f"Pilot {pilot_id}: Insufficient rest between {current.flight_id} and "
                        f"{next_flight.flight_id}: {rest_time:.1f}h < {self.min_rest_hours}h"
                    )
        
        return len(violations) == 0, violations
    
    def get_pilot_schedule(self, pilot_id: str) -> List[PilotAssignment]:
        """
        Get all assignments for a specific pilot.
        
        Args:
            pilot_id: ID of the pilot
            
        Returns:
            List of assignments for that pilot
        """
        pilot = next((p for p in self._pilots if p.pilot_id == pilot_id), None)
        if pilot is None:
            return []
        
        return [
            assignment for assignment in []  # Would need to track assignments
        ]
    
    def get_statistics(self) -> Dict[str, any]:
        """
        Get scheduling statistics.
        
        Returns:
            Dictionary of statistics
        """
        total_pilots = len(self._pilots)
        active_pilots = sum(1 for p in self._pilots if p.assigned_flights)
        
        avg_hours = sum(p.total_hours_today for p in self._pilots) / total_pilots if total_pilots > 0 else 0
        max_hours = max((p.total_hours_today for p in self._pilots), default=0)
        min_hours = min((p.total_hours_today for p in self._pilots if p.assigned_flights), default=0)
        
        return {
            'total_pilots': total_pilots,
            'active_pilots': active_pilots,
            'avg_hours_per_pilot': avg_hours,
            'max_hours': max_hours,
            'min_hours': min_hours,
            'utilization_rate': (active_pilots / total_pilots * 100) if total_pilots > 0 else 0
        }

"""
Multi-Day Pilot Scheduling - Ethical assignment across multiple days.

This module implements enhanced pilot scheduling that handles flights
spanning multiple days, showing pilot reassignments and daily patterns.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from collections import defaultdict

from ..models.pilot import Pilot, PilotAssignment
from ..models.flight import Flight


@dataclass
class DailyPilotSchedule:
    """Schedule for a single day."""
    day: int
    date: datetime
    assignments: List[PilotAssignment] = field(default_factory=list)
    pilots_active: int = 0
    flights_scheduled: int = 0
    compliance_rate: float = 100.0


@dataclass
class MultiDayScheduleResult:
    """
    Result of multi-day pilot scheduling.
    
    Shows daily breakdowns and pilot reassignments across days.
    """
    daily_schedules: Dict[int, DailyPilotSchedule] = field(default_factory=dict)
    all_assignments: List[PilotAssignment] = field(default_factory=list)
    unassigned_flights: List[Flight] = field(default_factory=list)
    pilot_daily_hours: Dict[str, Dict[int, float]] = field(default_factory=dict)  # pilot_id -> {day: hours}
    total_pilots_used: int = 0
    overall_compliance_rate: float = 100.0
    
    def __str__(self) -> str:
        result = [
            "=" * 80,
            "MULTI-DAY PILOT SCHEDULING RESULT",
            "=" * 80,
            f"Total Days: {len(self.daily_schedules)}",
            f"Total Flights: {len(self.all_assignments) + len(self.unassigned_flights)}",
            f"Successfully Assigned: {len(self.all_assignments)}",
            f"Unassigned: {len(self.unassigned_flights)}",
            f"Overall Compliance: {self.overall_compliance_rate:.1f}%",
            f"Pilots Used: {self.total_pilots_used}",
            "=" * 80,
        ]
        
        # Daily breakdown
        for day in sorted(self.daily_schedules.keys()):
            schedule = self.daily_schedules[day]
            result.append(f"\n📅 DAY {day + 1} - {schedule.date.strftime('%Y-%m-%d')}")
            result.append("-" * 60)
            result.append(f"  Flights: {schedule.flights_scheduled}")
            result.append(f"  Active Pilots: {schedule.pilots_active}")
            result.append(f"  Compliance: {schedule.compliance_rate:.1f}%")
            
            if schedule.assignments:
                result.append("\n  Assignments:")
                sorted_assignments = sorted(schedule.assignments, key=lambda a: a.flight_start)
                for assignment in sorted_assignments[:5]:  # Show first 5
                    result.append(f"    • {assignment}")
                if len(schedule.assignments) > 5:
                    result.append(f"    ... and {len(schedule.assignments) - 5} more")
        
        # Pilot workload summary
        result.append("\n" + "=" * 80)
        result.append("PILOT WORKLOAD SUMMARY")
        result.append("-" * 80)
        
        for pilot_id in sorted(self.pilot_daily_hours.keys())[:10]:  # Show first 10 pilots
            hours_by_day = self.pilot_daily_hours[pilot_id]
            total = sum(hours_by_day.values())
            days_worked = len(hours_by_day)
            avg = total / days_worked if days_worked > 0 else 0
            
            result.append(f"  {pilot_id}: {days_worked} days, {total:.1f}h total, {avg:.1f}h avg/day")
        
        result.append("=" * 80)
        return "\n".join(result)


class MultiDayPilotScheduler:
    """
    Enhanced pilot scheduler for multi-day operations.
    
    Handles flights across multiple days with proper daily resets
    and shows pilot reassignments.
    """
    
    def __init__(self, min_rest_hours: float = 10.0, max_daily_hours: float = 8.0):
        """
        Initialize scheduler.
        
        Args:
            min_rest_hours: Minimum rest between flights
            max_daily_hours: Maximum daily flying hours
        """
        self.min_rest_hours = min_rest_hours
        self.max_daily_hours = max_daily_hours
        self._pilots: List[Pilot] = []
    
    def create_pilots(self, count: int, base_airport: str = '') -> List[Pilot]:
        """Create a fleet of pilots."""
        names = [
            "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", 
            "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez",
            "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
            "White", "Harris", "Clark", "Lewis", "Lee", "Walker", "Hall", "Allen",
            "Young", "King", "Wright", "Scott", "Green", "Baker", "Adams", "Nelson"
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
        """Calculate flight duration from flight object."""
        # Use the flight_duration attribute if available
        if hasattr(flight, 'flight_duration') and flight.flight_duration > 0:
            return flight.flight_duration
        
        # Fallback: estimate from occupancy time
        duration_minutes = flight.occupancy_time + 30
        return duration_minutes / 60.0
    
    def _group_flights_by_day(self, flights: List[Flight]) -> Dict[int, List[Flight]]:
        """Group flights by day number."""
        by_day = defaultdict(list)
        
        for flight in flights:
            day = flight.day if hasattr(flight, 'day') else 0
            by_day[day].append(flight)
        
        return dict(by_day)
    
    def _find_available_pilot(
        self, 
        flight: Flight, 
        strategy: str = 'least_busy',
        day: int = 0
    ) -> Optional[Pilot]:
        """Find available pilot for a flight."""
        duration = self._calculate_flight_duration(flight)
        available_pilots = []
        
        for pilot in self._pilots:
            if pilot.can_fly(flight.arrival_start, duration):
                available_pilots.append(pilot)
        
        if not available_pilots:
            # Log why no pilots are available for debugging
            print(f"⚠️  No pilots available for {flight.flight_id} on day {day} at {flight.arrival_start.strftime('%H:%M')} (duration: {duration:.1f}h)")
            print(f"   Total pilots: {len(self._pilots)}")
            for i, pilot in enumerate(self._pilots[:5]):  # Show first 5 pilots
                can_fly_hours = pilot.total_hours_today + duration <= pilot.max_daily_hours
                rest_ok = pilot.last_flight_end is None or (flight.arrival_start - pilot.last_flight_end).total_seconds() / 3600 >= pilot.min_rest_hours
                print(f"   Pilot {pilot.pilot_id}: Hours={pilot.total_hours_today:.1f}/{pilot.max_daily_hours:.1f} {'✓' if can_fly_hours else '✗'}, Rest={'✓' if rest_ok else '✗'}")
            return None
        
        # Apply selection strategy
        if strategy == 'least_busy':
            # Choose pilot with least hours flown today (fair distribution)
            # Break ties by choosing pilot with fewer assigned flights
            # This spreads work across ALL pilots
            return min(available_pilots, key=lambda p: (p.total_hours_today, len(p.assigned_flights)))
        
        elif strategy == 'most_available':
            # Maximize utilization: concentrate work on fewer pilots
            # Choose pilot with MOST hours worked (inverse of remaining)
            # Break ties by choosing pilot with MORE flights (keep using same pilots)
            return max(available_pilots, key=lambda p: (p.total_hours_today, len(p.assigned_flights)))
        
        elif strategy == 'round_robin':
            # Distribute flights equally by number of assignments
            return min(available_pilots, key=lambda p: len(p.assigned_flights))
        
        return available_pilots[0]
    
    def schedule(
        self, 
        flights: List[Flight], 
        strategy: str = 'least_busy'
    ) -> MultiDayScheduleResult:
        """
        Schedule pilots across multiple days.
        
        Args:
            flights: List of flights (may span multiple days)
            strategy: Assignment strategy
            
        Returns:
            MultiDayScheduleResult with daily breakdowns
        """
        if not flights:
            return MultiDayScheduleResult()
        
        if not self._pilots:
            return MultiDayScheduleResult(
                unassigned_flights=flights,
                overall_compliance_rate=0.0
            )
        
        # Group flights by day
        flights_by_day = self._group_flights_by_day(flights)
        
        # Initialize result
        result = MultiDayScheduleResult()
        result.pilot_daily_hours = defaultdict(lambda: defaultdict(float))
        
        all_assignments = []
        all_unassigned = []
        pilots_used = set()
        
        # Schedule each day
        for day in sorted(flights_by_day.keys()):
            day_flights = sorted(flights_by_day[day], key=lambda f: f.arrival_start)
            
            print(f"\n📅 Scheduling Day {day + 1}: {len(day_flights)} flights")
            
            # Reset all pilots for new day
            for pilot in self._pilots:
                pilot.reset_daily_hours()
                # Keep assigned_flights for tracking, but reset last_flight_end
                # to allow flying next day
                pilot.last_flight_end = None
            
            # Create daily schedule
            daily_schedule = DailyPilotSchedule(
                day=day,
                date=day_flights[0].arrival_start.replace(hour=0, minute=0, second=0)
            )
            
            day_assignments = []
            day_unassigned = []
            day_pilots_active = set()
            
            # Schedule flights for this day
            for flight in day_flights:
                pilot = self._find_available_pilot(flight, strategy, day)
                
                if pilot is None:
                    day_unassigned.append(flight)
                    all_unassigned.append(flight)
                    continue
                
                # Assign flight
                duration = self._calculate_flight_duration(flight)
                flight_end = flight.arrival_start + timedelta(hours=duration)
                
                pilot.assign_flight(flight.flight_id, flight.arrival_start, flight_end, duration)
                
                assignment = PilotAssignment(
                    pilot_id=pilot.pilot_id,
                    flight_id=flight.flight_id,
                    assignment_time=datetime.now(),
                    flight_start=flight.arrival_start,
                    flight_end=flight_end,
                    day=day
                )
                
                day_assignments.append(assignment)
                all_assignments.append(assignment)
                day_pilots_active.add(pilot.pilot_id)
                pilots_used.add(pilot.pilot_id)
                
                # Track daily hours
                result.pilot_daily_hours[pilot.pilot_id][day] += duration
            
            # Update daily schedule
            daily_schedule.assignments = day_assignments
            daily_schedule.pilots_active = len(day_pilots_active)
            daily_schedule.flights_scheduled = len(day_flights)
            daily_schedule.compliance_rate = (
                (len(day_assignments) / len(day_flights) * 100) 
                if day_flights else 100.0
            )
            
            print(f"✅ Day {day + 1} complete: {len(day_assignments)}/{len(day_flights)} assigned ({daily_schedule.compliance_rate:.1f}%), {len(day_pilots_active)} pilots used")
            if day_unassigned:
                print(f"   Unassigned: {[f.flight_id for f in day_unassigned]}")
            
            result.daily_schedules[day] = daily_schedule
        
        # Calculate overall statistics
        result.all_assignments = all_assignments
        result.unassigned_flights = all_unassigned
        result.total_pilots_used = len(pilots_used)
        
        total_flights = len(flights)
        result.overall_compliance_rate = (
            (len(all_assignments) / total_flights * 100) 
            if total_flights > 0 else 100.0
        )
        
        return result
    
    def get_pilot_utilization(
        self, 
        result: MultiDayScheduleResult
    ) -> Dict[str, Dict[str, float]]:
        """
        Calculate detailed pilot utilization metrics.
        
        Returns:
            Dict with pilot_id -> {metric: value}
        """
        utilization = {}
        
        for pilot_id, daily_hours in result.pilot_daily_hours.items():
            total_hours = sum(daily_hours.values())
            days_worked = len(daily_hours)
            avg_hours = total_hours / days_worked if days_worked > 0 else 0
            
            # Find pilot object
            pilot = next((p for p in self._pilots if p.pilot_id == pilot_id), None)
            if pilot:
                max_possible = pilot.max_daily_hours * days_worked
                util_pct = (total_hours / max_possible * 100) if max_possible > 0 else 0
                
                utilization[pilot_id] = {
                    'total_hours': total_hours,
                    'days_worked': days_worked,
                    'avg_hours_per_day': avg_hours,
                    'utilization_percentage': util_pct,
                    'max_day_hours': max(daily_hours.values()) if daily_hours else 0,
                    'min_day_hours': min(daily_hours.values()) if daily_hours else 0
                }
        
        return utilization
    
    def validate_schedule(
        self, 
        result: MultiDayScheduleResult
    ) -> Tuple[bool, List[str]]:
        """
        Validate multi-day schedule.
        
        Returns:
            (is_valid, violations)
        """
        violations = []
        
        # Group assignments by pilot and day
        pilot_day_assignments = defaultdict(lambda: defaultdict(list))
        
        for assignment in result.all_assignments:
            # Find the day for this assignment
            for day, schedule in result.daily_schedules.items():
                if assignment in schedule.assignments:
                    pilot_day_assignments[assignment.pilot_id][day].append(assignment)
                    break
        
        # Validate each pilot's daily schedule
        for pilot_id, days in pilot_day_assignments.items():
            for day, assignments in days.items():
                # Sort by time
                sorted_assign = sorted(assignments, key=lambda a: a.flight_start)
                
                # Check daily hours
                total_hours = sum(
                    (a.flight_end - a.flight_start).total_seconds() / 3600
                    for a in sorted_assign
                )
                
                if total_hours > self.max_daily_hours:
                    violations.append(
                        f"Pilot {pilot_id} Day {day}: Exceeds max hours {total_hours:.1f} > {self.max_daily_hours}"
                    )
                
                # Check rest periods
                for i in range(len(sorted_assign) - 1):
                    current = sorted_assign[i]
                    next_flight = sorted_assign[i + 1]
                    
                    rest = (next_flight.flight_start - current.flight_end).total_seconds() / 3600
                    
                    if rest < self.min_rest_hours:
                        violations.append(
                            f"Pilot {pilot_id} Day {day}: Insufficient rest {rest:.1f}h < {self.min_rest_hours}h"
                        )
        
        return len(violations) == 0, violations

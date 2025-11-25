"""
Scheduling Algorithm - Graph Coloring for runway assignment.

This module implements the Runway Scheduler using graph coloring algorithms
(Welsh-Powell and DSatur) to minimize the number of runways needed.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Set
from datetime import datetime

from ..models.flight import Flight
from ..models.graph import ConflictGraph


@dataclass
class ScheduleResult:
    """
    Represents the result of runway scheduling.
    
    Attributes:
        flights: List of scheduled flights with runway assignments
        num_runways: Minimum number of runways needed
        runway_assignments: Dict mapping runway_id to list of flights
        conflicts_resolved: Number of conflicts resolved
    """
    flights: List[Flight]
    num_runways: int
    runway_assignments: Dict[int, List[Flight]] = field(default_factory=dict)
    conflicts_resolved: int = 0
    
    def __str__(self) -> str:
        result = [
            "=" * 70,
            "RUNWAY SCHEDULING RESULT",
            "=" * 70,
            f"Minimum Runways Needed: {self.num_runways}",
            f"Total Flights Scheduled: {len(self.flights)}",
            f"Conflicts Resolved: {self.conflicts_resolved}",
            "-" * 70,
        ]
        
        for runway_id in sorted(self.runway_assignments.keys()):
            flights = self.runway_assignments[runway_id]
            result.append(f"\nRUNWAY {runway_id}:")
            result.append("-" * 40)
            
            # Sort flights by arrival time
            sorted_flights = sorted(flights, key=lambda f: f.arrival_start)
            
            for flight in sorted_flights:
                result.append(
                    f"  {flight.flight_id}: {flight.origin} -> {flight.destination} | "
                    f"{flight.arrival_start.strftime('%H:%M')} - {flight.arrival_end.strftime('%H:%M')}"
                )
        
        result.append("\n" + "=" * 70)
        return "\n".join(result)
    
    def get_schedule_table(self) -> str:
        """Generate a formatted schedule table."""
        lines = [
            "+----------+--------+-------+-------------+-------------+--------+",
            "| Flight   | Origin | Dest  | Arrival     | Clearance   | Runway |",
            "+----------+--------+-------+-------------+-------------+--------+",
        ]
        
        sorted_flights = sorted(self.flights, key=lambda f: f.arrival_start)
        
        for flight in sorted_flights:
            lines.append(
                f"| {flight.flight_id:8} | {flight.origin:6} | {flight.destination:5} | "
                f"{flight.arrival_start.strftime('%H:%M'):11} | "
                f"{flight.arrival_end.strftime('%H:%M'):11} | {flight.runway_id:6} |"
            )
        
        lines.append("+----------+--------+-------+-------------+-------------+--------+")
        return "\n".join(lines)


class RunwayScheduler:
    """
    Runway scheduling engine using graph coloring algorithms.
    
    Assigns runways to flights such that no two conflicting flights
    (with overlapping time windows) share the same runway.
    """
    
    def __init__(self, algorithm: str = "dsatur"):
        """
        Initialize the runway scheduler.
        
        Args:
            algorithm: Coloring algorithm to use ('welsh_powell' or 'dsatur')
        """
        self._algorithm = algorithm.lower()
        if self._algorithm not in ('welsh_powell', 'dsatur', 'greedy'):
            raise ValueError(f"Unknown algorithm: {algorithm}. Use 'welsh_powell', 'dsatur', or 'greedy'")
        
        self._conflict_graph: Optional[ConflictGraph] = None
    
    def build_conflict_graph(self, flights: List[Flight]) -> ConflictGraph:
        """
        Build a conflict graph from flights.
        
        Args:
            flights: List of Flight objects
            
        Returns:
            ConflictGraph with edges between conflicting flights
        """
        graph = ConflictGraph()
        graph.build_from_flights(flights)
        self._conflict_graph = graph
        return graph
    
    def welsh_powell(self, graph: ConflictGraph) -> Dict[str, int]:
        """
        Welsh-Powell graph coloring algorithm.
        
        Orders vertices by decreasing degree and assigns colors greedily.
        
        Args:
            graph: ConflictGraph to color
            
        Returns:
            Dict mapping flight_id to color (runway) number
        """
        # Get all flights sorted by degree (descending)
        flights = graph.get_all_flights()
        sorted_flights = sorted(
            flights,
            key=lambda f: graph.get_degree(f.flight_id),
            reverse=True
        )
        
        colors: Dict[str, int] = {}
        
        for flight in sorted_flights:
            # Find colors used by neighbors
            neighbor_colors: Set[int] = set()
            for neighbor_id, _ in graph.get_neighbors(flight.flight_id):
                if neighbor_id in colors:
                    neighbor_colors.add(colors[neighbor_id])
            
            # Assign smallest available color
            color = 1
            while color in neighbor_colors:
                color += 1
            
            colors[flight.flight_id] = color
        
        return colors
    
    def dsatur(self, graph: ConflictGraph) -> Dict[str, int]:
        """
        DSatur (Degree of Saturation) graph coloring algorithm.
        
        Prioritizes vertices with highest saturation degree (number of
        distinct colors in neighbors). More effective than Welsh-Powell
        for some graph types.
        
        Args:
            graph: ConflictGraph to color
            
        Returns:
            Dict mapping flight_id to color (runway) number
        """
        flights = graph.get_all_flights()
        n = len(flights)
        
        if n == 0:
            return {}
        
        colors: Dict[str, int] = {}
        saturation: Dict[str, Set[int]] = {f.flight_id: set() for f in flights}
        uncolored = set(f.flight_id for f in flights)
        
        while uncolored:
            # Select vertex with max saturation, break ties by degree
            max_sat = -1
            max_degree = -1
            selected = None
            
            for flight_id in uncolored:
                sat = len(saturation[flight_id])
                degree = graph.get_degree(flight_id)
                
                if sat > max_sat or (sat == max_sat and degree > max_degree):
                    max_sat = sat
                    max_degree = degree
                    selected = flight_id
            
            # Find colors used by neighbors
            neighbor_colors: Set[int] = set()
            for neighbor_id, _ in graph.get_neighbors(selected):
                if neighbor_id in colors:
                    neighbor_colors.add(colors[neighbor_id])
            
            # Assign smallest available color
            color = 1
            while color in neighbor_colors:
                color += 1
            
            colors[selected] = color
            uncolored.remove(selected)
            
            # Update saturation of uncolored neighbors
            for neighbor_id, _ in graph.get_neighbors(selected):
                if neighbor_id in uncolored:
                    saturation[neighbor_id].add(color)
        
        return colors
    
    def greedy_coloring(self, graph: ConflictGraph) -> Dict[str, int]:
        """
        Simple greedy graph coloring algorithm.
        
        Processes vertices in arrival time order.
        
        Args:
            graph: ConflictGraph to color
            
        Returns:
            Dict mapping flight_id to color (runway) number
        """
        flights = sorted(graph.get_all_flights(), key=lambda f: f.arrival_start)
        colors: Dict[str, int] = {}
        
        for flight in flights:
            # Find colors used by neighbors
            neighbor_colors: Set[int] = set()
            for neighbor_id, _ in graph.get_neighbors(flight.flight_id):
                if neighbor_id in colors:
                    neighbor_colors.add(colors[neighbor_id])
            
            # Assign smallest available color
            color = 1
            while color in neighbor_colors:
                color += 1
            
            colors[flight.flight_id] = color
        
        return colors
    
    def schedule(self, flights: List[Flight]) -> ScheduleResult:
        """
        Schedule flights to runways using graph coloring.
        
        Args:
            flights: List of Flight objects to schedule
            
        Returns:
            ScheduleResult with runway assignments
        """
        if not flights:
            return ScheduleResult(flights=[], num_runways=0)
        
        # Build conflict graph
        graph = self.build_conflict_graph(flights)
        
        # Count conflicts
        conflicts = len(graph.get_all_edges())
        
        # Apply coloring algorithm
        if self._algorithm == 'welsh_powell':
            colors = self.welsh_powell(graph)
        elif self._algorithm == 'dsatur':
            colors = self.dsatur(graph)
        else:
            colors = self.greedy_coloring(graph)
        
        # Assign runways to flights
        runway_assignments: Dict[int, List[Flight]] = {}
        
        for flight in flights:
            runway_id = colors.get(flight.flight_id, 1)
            flight.runway_id = runway_id
            
            if runway_id not in runway_assignments:
                runway_assignments[runway_id] = []
            runway_assignments[runway_id].append(flight)
        
        num_runways = max(colors.values()) if colors else 0
        
        return ScheduleResult(
            flights=flights,
            num_runways=num_runways,
            runway_assignments=runway_assignments,
            conflicts_resolved=conflicts
        )
    
    def get_chromatic_number_bound(self, flights: List[Flight]) -> Tuple[int, int]:
        """
        Calculate bounds on the chromatic number (minimum runways).
        
        Args:
            flights: List of Flight objects
            
        Returns:
            Tuple of (lower_bound, upper_bound)
        """
        if not flights:
            return 0, 0
        
        graph = self.build_conflict_graph(flights)
        
        # Lower bound: maximum degree + 1 (clique number)
        _, max_degree = graph.get_max_degree()
        lower_bound = 1  # At least 1 runway needed
        
        # Find maximum clique size (simplified - just use max degree)
        # This is an approximation
        lower_bound = max(1, max_degree)
        
        # Upper bound: max_degree + 1 (by greedy coloring theorem)
        upper_bound = max_degree + 1
        
        return lower_bound, upper_bound
    
    def validate_schedule(self, flights: List[Flight]) -> Tuple[bool, List[str]]:
        """
        Validate that a schedule has no conflicts.
        
        Args:
            flights: List of scheduled Flight objects
            
        Returns:
            Tuple of (is_valid, list of conflict descriptions)
        """
        conflicts = []
        n = len(flights)
        
        for i in range(n):
            for j in range(i + 1, n):
                if flights[i].overlaps_with(flights[j]):
                    if flights[i].runway_id == flights[j].runway_id:
                        conflicts.append(
                            f"Conflict: {flights[i].flight_id} and {flights[j].flight_id} "
                            f"both assigned to Runway {flights[i].runway_id}"
                        )
        
        return len(conflicts) == 0, conflicts

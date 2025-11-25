"""
Routing Algorithm - Dijkstra's Algorithm for shortest path.

This module implements the Route Planner component using Dijkstra's
algorithm with a priority queue for efficient shortest path calculation.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import heapq

from ..models.airport import Airport
from ..models.graph import RouteGraph


@dataclass
class RouteResult:
    """
    Represents the result of a route calculation.
    
    Attributes:
        source: Source airport
        destination: Destination airport
        path: List of airports in the route
        total_distance: Total distance in kilometers
        eta: Estimated time of arrival
        flight_time: Total flight time
        segments: List of (from, to, distance) tuples for each segment
    """
    source: Airport
    destination: Airport
    path: List[Airport]
    total_distance: float
    eta: datetime
    flight_time: timedelta
    segments: List[Tuple[Airport, Airport, float]] = field(default_factory=list)
    
    def __str__(self) -> str:
        path_str = " -> ".join(a.id for a in self.path)
        hours, remainder = divmod(self.flight_time.total_seconds(), 3600)
        minutes = remainder // 60
        
        result = [
            "=" * 60,
            "FLIGHT ITINERARY",
            "=" * 60,
            f"Route: {path_str}",
            f"Total Distance: {self.total_distance:.2f} km",
            f"Flight Time: {int(hours)}h {int(minutes)}m",
            f"ETA: {self.eta.strftime('%Y-%m-%d %H:%M')}",
            "-" * 60,
            "ROUTE SEGMENTS:",
        ]
        
        for i, (from_apt, to_apt, dist) in enumerate(self.segments, 1):
            result.append(f"  {i}. {from_apt.id} -> {to_apt.id}: {dist:.2f} km")
        
        result.append("=" * 60)
        return "\n".join(result)


class RoutePlanner:
    """
    Route planning engine using Dijkstra's algorithm.
    
    Finds the shortest path between airports considering distance
    and optional weather factors.
    """
    
    # Average cruising speed in km/h (typical commercial aircraft)
    DEFAULT_CRUISING_SPEED = 850.0
    
    def __init__(self, graph: RouteGraph, cruising_speed: float = None):
        """
        Initialize the route planner.
        
        Args:
            graph: RouteGraph containing airports and routes
            cruising_speed: Aircraft cruising speed in km/h
        """
        self._graph = graph
        self._cruising_speed = cruising_speed or self.DEFAULT_CRUISING_SPEED
    
    @property
    def graph(self) -> RouteGraph:
        """Get the route graph."""
        return self._graph
    
    def set_cruising_speed(self, speed: float) -> None:
        """
        Set the aircraft cruising speed.
        
        Args:
            speed: Speed in km/h
        """
        if speed <= 0:
            raise ValueError("Cruising speed must be positive")
        self._cruising_speed = speed
    
    def dijkstra(self, source_id: str, destination_id: str) -> Tuple[Dict[str, float], Dict[str, Optional[str]]]:
        """
        Implement Dijkstra's algorithm to find shortest paths.
        
        Args:
            source_id: Source airport ID
            destination_id: Destination airport ID
            
        Returns:
            Tuple of (distances dict, predecessors dict)
        """
        if not self._graph.has_node(source_id):
            raise ValueError(f"Source airport '{source_id}' not found")
        if not self._graph.has_node(destination_id):
            raise ValueError(f"Destination airport '{destination_id}' not found")
        
        # Initialize distances with infinity
        distances: Dict[str, float] = {node_id: float('inf') for node_id in self._graph.nodes}
        distances[source_id] = 0
        
        # Track predecessors for path reconstruction
        predecessors: Dict[str, Optional[str]] = {node_id: None for node_id in self._graph.nodes}
        
        # Priority queue: (distance, node_id)
        pq = [(0, source_id)]
        visited = set()
        
        while pq:
            current_dist, current_id = heapq.heappop(pq)
            
            # Skip if already processed
            if current_id in visited:
                continue
            
            visited.add(current_id)
            
            # Early termination if destination reached
            if current_id == destination_id:
                break
            
            # Explore neighbors
            for neighbor_id, weight in self._graph.get_neighbors(current_id):
                if neighbor_id in visited:
                    continue
                
                new_dist = current_dist + weight
                
                if new_dist < distances[neighbor_id]:
                    distances[neighbor_id] = new_dist
                    predecessors[neighbor_id] = current_id
                    heapq.heappush(pq, (new_dist, neighbor_id))
        
        return distances, predecessors
    
    def find_shortest_path(self, source_id: str, destination_id: str,
                           departure_time: datetime = None) -> Optional[RouteResult]:
        """
        Find the shortest path between two airports.
        
        Args:
            source_id: Source airport ID
            destination_id: Destination airport ID
            departure_time: Departure time (defaults to now)
            
        Returns:
            RouteResult object or None if no path exists
        """
        if departure_time is None:
            departure_time = datetime.now()
        
        # Run Dijkstra's algorithm
        distances, predecessors = self.dijkstra(source_id, destination_id)
        
        # Check if destination is reachable
        if distances[destination_id] == float('inf'):
            return None
        
        # Reconstruct path
        path = []
        current = destination_id
        
        while current is not None:
            airport = self._graph.get_node(current)
            if airport:
                path.append(airport)
            current = predecessors[current]
        
        path.reverse()
        
        # Calculate segments
        segments = []
        for i in range(len(path) - 1):
            from_apt = path[i]
            to_apt = path[i + 1]
            dist = self._graph.get_route_distance(from_apt.id, to_apt.id)
            if dist is not None:
                segments.append((from_apt, to_apt, dist))
        
        # Calculate flight time and ETA
        total_distance = distances[destination_id]
        flight_hours = total_distance / self._cruising_speed
        flight_time = timedelta(hours=flight_hours)
        eta = departure_time + flight_time
        
        return RouteResult(
            source=path[0],
            destination=path[-1],
            path=path,
            total_distance=total_distance,
            eta=eta,
            flight_time=flight_time,
            segments=segments
        )
    
    def find_all_paths(self, source_id: str, destination_id: str,
                       max_stops: int = 5) -> List[List[Airport]]:
        """
        Find all possible paths between two airports (up to max_stops).
        
        Uses DFS to explore all paths. Useful for finding alternatives.
        
        Args:
            source_id: Source airport ID
            destination_id: Destination airport ID
            max_stops: Maximum number of intermediate stops
            
        Returns:
            List of paths, where each path is a list of Airport objects
        """
        if not self._graph.has_node(source_id) or not self._graph.has_node(destination_id):
            return []
        
        all_paths = []
        
        def dfs(current: str, path: List[str], visited: set):
            if len(path) > max_stops + 2:  # source + max_stops + destination
                return
            
            if current == destination_id:
                # Convert path to Airport objects
                airport_path = [self._graph.get_node(node_id) for node_id in path]
                all_paths.append(airport_path)
                return
            
            for neighbor_id, _ in self._graph.get_neighbors(current):
                if neighbor_id not in visited:
                    visited.add(neighbor_id)
                    path.append(neighbor_id)
                    dfs(neighbor_id, path, visited)
                    path.pop()
                    visited.remove(neighbor_id)
        
        visited = {source_id}
        dfs(source_id, [source_id], visited)
        
        return all_paths
    
    def get_reachable_airports(self, source_id: str, max_distance: float = None) -> List[Tuple[Airport, float]]:
        """
        Get all airports reachable from a source airport.
        
        Args:
            source_id: Source airport ID
            max_distance: Maximum distance filter (optional)
            
        Returns:
            List of (Airport, distance) tuples sorted by distance
        """
        distances, _ = self.dijkstra(source_id, source_id)  # Run to all nodes
        
        # Run full Dijkstra (we need to visit all nodes)
        distances = {node_id: float('inf') for node_id in self._graph.nodes}
        distances[source_id] = 0
        pq = [(0, source_id)]
        visited = set()
        
        while pq:
            current_dist, current_id = heapq.heappop(pq)
            
            if current_id in visited:
                continue
            visited.add(current_id)
            
            for neighbor_id, weight in self._graph.get_neighbors(current_id):
                if neighbor_id not in visited:
                    new_dist = current_dist + weight
                    if new_dist < distances[neighbor_id]:
                        distances[neighbor_id] = new_dist
                        heapq.heappush(pq, (new_dist, neighbor_id))
        
        results = []
        for node_id, dist in distances.items():
            if node_id != source_id and dist != float('inf'):
                if max_distance is None or dist <= max_distance:
                    airport = self._graph.get_node(node_id)
                    if airport:
                        results.append((airport, dist))
        
        return sorted(results, key=lambda x: x[1])

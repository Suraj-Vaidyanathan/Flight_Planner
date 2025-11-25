"""
Graph Models - Generic graph structures for routing and scheduling.

This module defines graph data structures using adjacency lists for
efficient traversal and manipulation of airport routing and flight
conflict graphs.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple, Optional, Any, Generic, TypeVar
from collections import defaultdict
import heapq

from .airport import Airport
from .flight import Flight


T = TypeVar('T')


class Graph(Generic[T]):
    """
    Generic graph implementation using an adjacency list.
    
    This base class provides fundamental graph operations that can be
    used for both routing (weighted, directed) and scheduling (unweighted, undirected).
    """
    
    def __init__(self, directed: bool = True):
        """
        Initialize an empty graph.
        
        Args:
            directed: If True, edges are directed; otherwise undirected
        """
        self._adjacency_list: Dict[str, List[Tuple[str, float]]] = defaultdict(list)
        self._nodes: Dict[str, T] = {}
        self._directed = directed
    
    @property
    def nodes(self) -> Dict[str, T]:
        """Get all nodes in the graph."""
        return self._nodes
    
    @property
    def is_directed(self) -> bool:
        """Check if graph is directed."""
        return self._directed
    
    def add_node(self, node_id: str, node: T) -> None:
        """
        Add a node to the graph.
        
        Args:
            node_id: Unique identifier for the node
            node: The node object to add
        """
        self._nodes[node_id] = node
        if node_id not in self._adjacency_list:
            self._adjacency_list[node_id] = []
    
    def add_edge(self, source: str, destination: str, weight: float = 1.0) -> None:
        """
        Add an edge between two nodes.
        
        Args:
            source: Source node ID
            destination: Destination node ID  
            weight: Edge weight (default 1.0)
        """
        if source not in self._nodes:
            raise ValueError(f"Source node '{source}' not found in graph")
        if destination not in self._nodes:
            raise ValueError(f"Destination node '{destination}' not found in graph")
        
        self._adjacency_list[source].append((destination, weight))
        
        # For undirected graphs, add edge in both directions
        if not self._directed:
            self._adjacency_list[destination].append((source, weight))
    
    def get_neighbors(self, node_id: str) -> List[Tuple[str, float]]:
        """
        Get all neighbors of a node with edge weights.
        
        Args:
            node_id: The node ID to get neighbors for
            
        Returns:
            List of (neighbor_id, weight) tuples
        """
        return self._adjacency_list.get(node_id, [])
    
    def get_node(self, node_id: str) -> Optional[T]:
        """
        Get a node by its ID.
        
        Args:
            node_id: The node ID to retrieve
            
        Returns:
            The node object or None if not found
        """
        return self._nodes.get(node_id)
    
    def has_node(self, node_id: str) -> bool:
        """Check if a node exists in the graph."""
        return node_id in self._nodes
    
    def has_edge(self, source: str, destination: str) -> bool:
        """Check if an edge exists between two nodes."""
        return any(dest == destination for dest, _ in self._adjacency_list.get(source, []))
    
    def get_all_edges(self) -> List[Tuple[str, str, float]]:
        """
        Get all edges in the graph.
        
        Returns:
            List of (source, destination, weight) tuples
        """
        edges = []
        seen = set()
        
        for source, neighbors in self._adjacency_list.items():
            for dest, weight in neighbors:
                edge_key = (source, dest) if self._directed else tuple(sorted([source, dest]))
                if edge_key not in seen:
                    edges.append((source, dest, weight))
                    seen.add(edge_key)
        
        return edges
    
    def get_degree(self, node_id: str) -> int:
        """
        Get the degree (number of connections) of a node.
        
        Args:
            node_id: The node ID
            
        Returns:
            Number of edges connected to this node
        """
        return len(self._adjacency_list.get(node_id, []))
    
    def __len__(self) -> int:
        """Return the number of nodes in the graph."""
        return len(self._nodes)
    
    def __contains__(self, node_id: str) -> bool:
        """Check if a node exists in the graph."""
        return node_id in self._nodes


class RouteGraph(Graph[Airport]):
    """
    Specialized graph for airport routing using Dijkstra's algorithm.
    
    Edges represent routes between airports with weights based on distance
    and optional weather factors.
    """
    
    def __init__(self):
        """Initialize a directed route graph."""
        super().__init__(directed=True)
        self._edge_weights: Dict[Tuple[str, str], float] = {}
    
    def add_airport(self, airport: Airport) -> None:
        """
        Add an airport node to the graph.
        
        Args:
            airport: Airport object to add
        """
        self.add_node(airport.id, airport)
    
    def add_route(self, source_id: str, dest_id: str, 
                  distance: Optional[float] = None,
                  include_weather: bool = True) -> None:
        """
        Add a route between two airports.
        
        Args:
            source_id: Source airport ID
            dest_id: Destination airport ID
            distance: Explicit distance (if None, calculated from coordinates)
            include_weather: Whether to include weather factors in weight
        """
        source = self.get_node(source_id)
        dest = self.get_node(dest_id)
        
        if source is None or dest is None:
            raise ValueError(f"Both airports must exist: {source_id}, {dest_id}")
        
        if distance is None:
            distance = source.get_weighted_distance(dest, include_weather)
        elif include_weather:
            avg_weather = (source.weather_factor + dest.weather_factor) / 2
            distance *= avg_weather
        
        self._edge_weights[(source_id, dest_id)] = distance
        self.add_edge(source_id, dest_id, distance)
    
    def add_bidirectional_route(self, source_id: str, dest_id: str,
                                distance: Optional[float] = None,
                                include_weather: bool = True) -> None:
        """
        Add a bidirectional route between two airports.
        
        Args:
            source_id: First airport ID
            dest_id: Second airport ID
            distance: Explicit distance (if None, calculated from coordinates)
            include_weather: Whether to include weather factors in weight
        """
        self.add_route(source_id, dest_id, distance, include_weather)
        self.add_route(dest_id, source_id, distance, include_weather)
    
    def get_route_distance(self, source_id: str, dest_id: str) -> Optional[float]:
        """
        Get the distance of a specific route.
        
        Args:
            source_id: Source airport ID
            dest_id: Destination airport ID
            
        Returns:
            Route distance or None if route doesn't exist
        """
        return self._edge_weights.get((source_id, dest_id))
    
    def get_all_airports(self) -> List[Airport]:
        """Get all airports in the graph."""
        return list(self._nodes.values())


class ConflictGraph(Graph[Flight]):
    """
    Specialized undirected graph for flight scheduling conflicts.
    
    Nodes are flights, and edges represent scheduling conflicts
    (overlapping time windows).
    """
    
    def __init__(self):
        """Initialize an undirected conflict graph."""
        super().__init__(directed=False)
        self._adjacency_matrix: Optional[List[List[bool]]] = None
        self._flight_index: Dict[str, int] = {}
    
    def add_flight(self, flight: Flight) -> None:
        """
        Add a flight node to the conflict graph.
        
        Args:
            flight: Flight object to add
        """
        self._flight_index[flight.flight_id] = len(self._flight_index)
        self.add_node(flight.flight_id, flight)
    
    def build_from_flights(self, flights: List[Flight]) -> None:
        """
        Build the conflict graph from a list of flights.
        
        Automatically detects conflicts based on overlapping time windows
        and creates edges between conflicting flights.
        
        Args:
            flights: List of Flight objects
        """
        # Add all flights as nodes
        for flight in flights:
            self.add_flight(flight)
        
        # Detect conflicts and add edges
        n = len(flights)
        for i in range(n):
            for j in range(i + 1, n):
                if flights[i].overlaps_with(flights[j]):
                    self.add_edge(flights[i].flight_id, flights[j].flight_id)
    
    def get_conflict_count(self, flight_id: str) -> int:
        """
        Get the number of conflicts for a specific flight.
        
        Args:
            flight_id: The flight ID
            
        Returns:
            Number of conflicting flights
        """
        return self.get_degree(flight_id)
    
    def get_conflicting_flights(self, flight_id: str) -> List[Flight]:
        """
        Get all flights that conflict with a given flight.
        
        Args:
            flight_id: The flight ID
            
        Returns:
            List of conflicting Flight objects
        """
        conflicts = []
        for neighbor_id, _ in self.get_neighbors(flight_id):
            flight = self.get_node(neighbor_id)
            if flight:
                conflicts.append(flight)
        return conflicts
    
    def get_adjacency_matrix(self) -> List[List[bool]]:
        """
        Generate and return the adjacency matrix representation.
        
        Returns:
            2D boolean matrix where True indicates a conflict
        """
        n = len(self._nodes)
        matrix = [[False] * n for _ in range(n)]
        
        for source_id, neighbors in self._adjacency_list.items():
            i = self._flight_index.get(source_id, -1)
            if i >= 0:
                for dest_id, _ in neighbors:
                    j = self._flight_index.get(dest_id, -1)
                    if j >= 0:
                        matrix[i][j] = True
                        matrix[j][i] = True
        
        return matrix
    
    def get_all_flights(self) -> List[Flight]:
        """Get all flights in the graph."""
        return list(self._nodes.values())
    
    def get_max_degree(self) -> Tuple[Optional[str], int]:
        """
        Find the node with maximum degree (most conflicts).
        
        Returns:
            Tuple of (flight_id, degree) or (None, 0) if graph is empty
        """
        if not self._nodes:
            return None, 0
        
        max_node = None
        max_degree = -1
        
        for node_id in self._nodes:
            degree = self.get_degree(node_id)
            if degree > max_degree:
                max_degree = degree
                max_node = node_id
        
        return max_node, max_degree

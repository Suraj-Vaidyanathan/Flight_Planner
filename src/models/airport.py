"""
Airport Model - Represents a node in the routing graph.

This module defines the Airport class which stores airport information
including its unique identifier, name, and geographical coordinates.
"""

from dataclasses import dataclass, field
from typing import Optional
import math


@dataclass
class Airport:
    """
    Represents an airport node in the routing graph.
    
    Attributes:
        id (str): Unique airport identifier (e.g., 'JFK', 'LHR')
        name (str): Full name of the airport
        latitude (float): Geographical latitude coordinate
        longitude (float): Geographical longitude coordinate
        weather_factor (float): Weather multiplier affecting flight costs (1.0 = clear)
    """
    id: str
    name: str
    latitude: float
    longitude: float
    weather_factor: float = field(default=1.0)
    
    def __post_init__(self):
        """Validate airport data after initialization."""
        if not self.id:
            raise ValueError("Airport ID cannot be empty")
        if not -90 <= self.latitude <= 90:
            raise ValueError(f"Invalid latitude: {self.latitude}")
        if not -180 <= self.longitude <= 180:
            raise ValueError(f"Invalid longitude: {self.longitude}")
        if self.weather_factor < 0:
            raise ValueError(f"Weather factor cannot be negative: {self.weather_factor}")
    
    def distance_to(self, other: 'Airport') -> float:
        """
        Calculate the great-circle distance to another airport using the Haversine formula.
        
        Args:
            other: Another Airport object
            
        Returns:
            Distance in kilometers
        """
        # Earth's radius in kilometers
        R = 6371.0
        
        # Convert to radians
        lat1 = math.radians(self.latitude)
        lat2 = math.radians(other.latitude)
        delta_lat = math.radians(other.latitude - self.latitude)
        delta_lon = math.radians(other.longitude - self.longitude)
        
        # Haversine formula
        a = math.sin(delta_lat / 2) ** 2 + \
            math.cos(lat1) * math.cos(lat2) * math.sin(delta_lon / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    def get_weighted_distance(self, other: 'Airport', include_weather: bool = True) -> float:
        """
        Calculate weighted distance considering weather factors.
        
        Args:
            other: Another Airport object
            include_weather: Whether to include weather factors in calculation
            
        Returns:
            Weighted distance in kilometers
        """
        base_distance = self.distance_to(other)
        
        if include_weather:
            # Average the weather factors of both airports
            avg_weather = (self.weather_factor + other.weather_factor) / 2
            return base_distance * avg_weather
        
        return base_distance
    
    def __hash__(self):
        """Allow Airport to be used in sets and as dictionary keys."""
        return hash(self.id)
    
    def __eq__(self, other):
        """Check equality based on airport ID."""
        if isinstance(other, Airport):
            return self.id == other.id
        return False
    
    def __repr__(self):
        return f"Airport({self.id}, {self.name})"
    
    def __str__(self):
        return f"{self.id} - {self.name} ({self.latitude:.4f}, {self.longitude:.4f})"

"""
Time Utilities - Helper functions for time-related operations.

This module provides utilities for handling time intervals,
overlap detection, and time formatting for the scheduling system.
"""

from datetime import datetime, timedelta
from typing import List, Tuple, Optional
import random


class TimeUtils:
    """
    Utility class for time-related operations.
    
    Provides methods for time interval manipulation, overlap detection,
    and time formatting.
    """
    
    @staticmethod
    def intervals_overlap(start1: datetime, end1: datetime,
                         start2: datetime, end2: datetime) -> bool:
        """
        Check if two time intervals overlap.
        
        Args:
            start1, end1: First interval boundaries
            start2, end2: Second interval boundaries
            
        Returns:
            True if intervals overlap
        """
        return start1 < end2 and start2 < end1
    
    @staticmethod
    def get_overlap_duration(start1: datetime, end1: datetime,
                            start2: datetime, end2: datetime) -> timedelta:
        """
        Calculate the overlap duration between two intervals.
        
        Args:
            start1, end1: First interval boundaries
            start2, end2: Second interval boundaries
            
        Returns:
            Duration of overlap (zero if no overlap)
        """
        if not TimeUtils.intervals_overlap(start1, end1, start2, end2):
            return timedelta(0)
        
        overlap_start = max(start1, start2)
        overlap_end = min(end1, end2)
        
        return overlap_end - overlap_start
    
    @staticmethod
    def merge_intervals(intervals: List[Tuple[datetime, datetime]]) -> List[Tuple[datetime, datetime]]:
        """
        Merge overlapping time intervals.
        
        Args:
            intervals: List of (start, end) datetime tuples
            
        Returns:
            List of merged non-overlapping intervals
        """
        if not intervals:
            return []
        
        # Sort by start time
        sorted_intervals = sorted(intervals, key=lambda x: x[0])
        merged = [sorted_intervals[0]]
        
        for start, end in sorted_intervals[1:]:
            last_start, last_end = merged[-1]
            
            if start <= last_end:
                # Overlapping - extend the last interval
                merged[-1] = (last_start, max(last_end, end))
            else:
                # Non-overlapping - add new interval
                merged.append((start, end))
        
        return merged
    
    @staticmethod
    def find_gaps(intervals: List[Tuple[datetime, datetime]],
                  window_start: datetime, window_end: datetime,
                  min_gap: timedelta = None) -> List[Tuple[datetime, datetime]]:
        """
        Find gaps between intervals within a time window.
        
        Args:
            intervals: List of (start, end) datetime tuples
            window_start, window_end: Time window to search within
            min_gap: Minimum gap duration to report (optional)
            
        Returns:
            List of gap intervals
        """
        if not intervals:
            return [(window_start, window_end)]
        
        # Merge overlapping intervals first
        merged = TimeUtils.merge_intervals(intervals)
        gaps = []
        
        # Gap before first interval
        if merged[0][0] > window_start:
            gaps.append((window_start, merged[0][0]))
        
        # Gaps between intervals
        for i in range(len(merged) - 1):
            gap_start = merged[i][1]
            gap_end = merged[i + 1][0]
            if gap_start < gap_end:
                gaps.append((gap_start, gap_end))
        
        # Gap after last interval
        if merged[-1][1] < window_end:
            gaps.append((merged[-1][1], window_end))
        
        # Filter by minimum gap if specified
        if min_gap:
            gaps = [(s, e) for s, e in gaps if e - s >= min_gap]
        
        return gaps
    
    @staticmethod
    def format_duration(duration: timedelta) -> str:
        """
        Format a duration in a human-readable format.
        
        Args:
            duration: Time duration
            
        Returns:
            Formatted string (e.g., "2h 30m")
        """
        total_seconds = int(duration.total_seconds())
        
        if total_seconds < 0:
            return "Invalid duration"
        
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        parts = []
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0 or (hours == 0 and seconds == 0):
            parts.append(f"{minutes}m")
        if seconds > 0 and hours == 0:
            parts.append(f"{seconds}s")
        
        return " ".join(parts) if parts else "0m"
    
    @staticmethod
    def format_time_range(start: datetime, end: datetime,
                         include_date: bool = False) -> str:
        """
        Format a time range for display.
        
        Args:
            start, end: Time range boundaries
            include_date: Whether to include the date
            
        Returns:
            Formatted string (e.g., "14:30 - 15:45")
        """
        if include_date:
            fmt = "%Y-%m-%d %H:%M"
        else:
            fmt = "%H:%M"
        
        return f"{start.strftime(fmt)} - {end.strftime(fmt)}"
    
    @staticmethod
    def generate_random_times(base_time: datetime, count: int,
                             window_minutes: int = 120,
                             min_duration: int = 10,
                             max_duration: int = 20) -> List[Tuple[datetime, datetime]]:
        """
        Generate random time intervals for simulation.
        
        Args:
            base_time: Center point for time generation
            count: Number of intervals to generate
            window_minutes: Time window size (±minutes from base)
            min_duration, max_duration: Duration range in minutes
            
        Returns:
            List of (start, end) datetime tuples
        """
        intervals = []
        
        for _ in range(count):
            offset = random.randint(-window_minutes, window_minutes)
            start = base_time + timedelta(minutes=offset)
            duration = random.randint(min_duration, max_duration)
            end = start + timedelta(minutes=duration)
            intervals.append((start, end))
        
        return sorted(intervals, key=lambda x: x[0])
    
    @staticmethod
    def round_to_nearest(dt: datetime, minutes: int = 5) -> datetime:
        """
        Round a datetime to the nearest interval.
        
        Args:
            dt: Datetime to round
            minutes: Interval in minutes
            
        Returns:
            Rounded datetime
        """
        total_minutes = dt.hour * 60 + dt.minute
        rounded_minutes = round(total_minutes / minutes) * minutes
        
        new_hour = rounded_minutes // 60
        new_minute = rounded_minutes % 60
        
        return dt.replace(hour=new_hour % 24, minute=new_minute, second=0, microsecond=0)
    
    @staticmethod
    def get_time_slot(dt: datetime, slot_minutes: int = 30) -> int:
        """
        Get the time slot index for a given datetime.
        
        Useful for grouping flights by time slots.
        
        Args:
            dt: Datetime
            slot_minutes: Slot duration in minutes
            
        Returns:
            Slot index (0-based from midnight)
        """
        total_minutes = dt.hour * 60 + dt.minute
        return total_minutes // slot_minutes
    
    @staticmethod
    def calculate_eta(departure: datetime, distance_km: float,
                     speed_kmh: float = 850.0,
                     taxi_minutes: int = 15) -> datetime:
        """
        Calculate estimated time of arrival.
        
        Args:
            departure: Departure datetime
            distance_km: Distance in kilometers
            speed_kmh: Average speed in km/h
            taxi_minutes: Time for taxi and landing
            
        Returns:
            Estimated arrival datetime
        """
        flight_hours = distance_km / speed_kmh
        flight_duration = timedelta(hours=flight_hours)
        taxi_time = timedelta(minutes=taxi_minutes)
        
        return departure + flight_duration + taxi_time

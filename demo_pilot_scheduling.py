#!/usr/bin/env python3
"""
Demo script for Ethical Pilot Scheduling feature.

This script demonstrates the pilot scheduling algorithm with
a realistic scenario.
"""

import sys
import os
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.models.pilot import Pilot
from src.models.flight import Flight
from src.algorithms.pilot_scheduling import PilotScheduler


def print_banner():
    """Print demo banner."""
    print("\n" + "=" * 70)
    print("         ETHICAL PILOT SCHEDULING - DEMONSTRATION")
    print("=" * 70)


def demo_basic_scheduling():
    """Demonstrate basic pilot scheduling."""
    print("\n" + "-" * 70)
    print("SCENARIO 1: Basic Scheduling with 3 Pilots and 5 Flights")
    print("-" * 70)
    
    # Create scheduler
    scheduler = PilotScheduler(min_rest_hours=10.0, max_daily_hours=8.0)
    
    # Create pilots
    print("\n👥 Creating 3 pilots...")
    pilots = scheduler.create_pilots(3, base_airport='LHR')
    
    for pilot in pilots:
        print(f"   • {pilot.name} ({pilot.pilot_id})")
    
    # Create flights
    print("\n✈️  Creating 5 flights arriving at LHR...")
    base_time = datetime.now().replace(hour=10, minute=0, second=0, microsecond=0)
    
    flights = [
        Flight("FL001", "JFK", "LHR", base_time, 15),
        Flight("FL002", "CDG", "LHR", base_time + timedelta(hours=1), 15),
        Flight("FL003", "FRA", "LHR", base_time + timedelta(hours=2), 15),
        Flight("FL004", "DXB", "LHR", base_time + timedelta(hours=12), 15),
        Flight("FL005", "SIN", "LHR", base_time + timedelta(hours=13), 15),
    ]
    
    for flight in flights:
        print(f"   • {flight.flight_id}: {flight.origin} → {flight.destination} "
              f"at {flight.arrival_start.strftime('%H:%M')}")
    
    # Schedule
    print("\n🔄 Running Least Busy scheduling strategy...")
    result = scheduler.schedule(flights, strategy='least_busy')
    
    # Results
    print("\n" + "=" * 70)
    print("RESULTS:")
    print("=" * 70)
    print(f"✅ Successfully assigned: {len(result.assignments)}/{len(flights)} flights")
    print(f"📊 Compliance rate: {result.compliance_rate:.1f}%")
    print(f"👥 Pilots used: {result.total_pilots_used}/{len(pilots)}")
    
    # Show assignments
    print("\n📋 ASSIGNMENTS:")
    for assignment in sorted(result.assignments, key=lambda a: a.flight_start):
        duration = (assignment.flight_end - assignment.flight_start).total_seconds() / 3600
        print(f"   {assignment.pilot_id} → {assignment.flight_id}: "
              f"{assignment.flight_start.strftime('%H:%M')} - "
              f"{assignment.flight_end.strftime('%H:%M')} ({duration:.1f}h)")
    
    # Validate
    is_valid, violations = scheduler.validate_schedule(result.assignments)
    print(f"\n{'✅' if is_valid else '❌'} Validation: {'PASSED' if is_valid else 'FAILED'}")
    
    print("\n" + "=" * 70)


def demo_rest_constraint():
    """Demonstrate rest constraint enforcement."""
    print("\n" + "-" * 70)
    print("SCENARIO 2: Testing Rest Requirement Enforcement")
    print("-" * 70)
    
    scheduler = PilotScheduler(min_rest_hours=10.0, max_daily_hours=8.0)
    
    print("\n👥 Creating 1 pilot...")
    pilots = scheduler.create_pilots(1, base_airport='LHR')
    print(f"   • {pilots[0].name} ({pilots[0].pilot_id})")
    
    # Create flights too close together
    print("\n✈️  Creating 3 flights with insufficient rest gaps...")
    base_time = datetime.now().replace(hour=10, minute=0, second=0, microsecond=0)
    
    flights = [
        Flight("FL001", "JFK", "LHR", base_time, 15),
        Flight("FL002", "CDG", "LHR", base_time + timedelta(hours=3), 15),  # Only 3h rest!
        Flight("FL003", "FRA", "LHR", base_time + timedelta(hours=6), 15),  # Only 3h rest!
    ]
    
    for i, flight in enumerate(flights):
        rest_msg = ""
        if i > 0:
            gap = (flight.arrival_start - flights[i-1].arrival_start).total_seconds() / 3600
            rest_msg = f" (gap: {gap:.0f}h)"
        print(f"   • {flight.flight_id}: {flight.arrival_start.strftime('%H:%M')}{rest_msg}")
    
    print("\n⚠️  Note: Only 3 hours between flights, but 10 hours rest required!")
    
    result = scheduler.schedule(flights, strategy='least_busy')
    
    print("\n" + "=" * 70)
    print("RESULTS:")
    print("=" * 70)
    print(f"✅ Assigned: {len(result.assignments)} flights")
    print(f"❌ Unassigned: {len(result.unassigned_flights)} flights (due to rest requirements)")
    
    if result.unassigned_flights:
        print("\n🚫 Unassigned flights:")
        for flight in result.unassigned_flights:
            print(f"   • {flight.flight_id} (insufficient rest from previous flight)")
    
    print("\n💡 This demonstrates ethical scheduling - pilot safety comes first!")
    print("=" * 70)


def demo_daily_hour_limit():
    """Demonstrate daily hour limit enforcement."""
    print("\n" + "-" * 70)
    print("SCENARIO 3: Testing Daily Hour Limit (8 hours max)")
    print("-" * 70)
    
    scheduler = PilotScheduler(min_rest_hours=10.0, max_daily_hours=8.0)
    
    print("\n👥 Creating 1 pilot...")
    pilots = scheduler.create_pilots(1, base_airport='LHR')
    print(f"   • {pilots[0].name} ({pilots[0].pilot_id})")
    
    # Create many flights spaced far apart (respect rest)
    print("\n✈️  Creating 15 short flights (0.75h each) spaced 12 hours apart...")
    base_time = datetime.now().replace(hour=10, minute=0, second=0, microsecond=0)
    
    flights = []
    for i in range(15):
        flights.append(Flight(
            f"FL{i+1:03d}",
            "JFK",
            "LHR",
            base_time + timedelta(hours=i * 12),
            15
        ))
    
    print(f"   • {len(flights)} flights x 0.75h = {len(flights) * 0.75:.1f}h total")
    print(f"   • Max allowed: 8.0h per day")
    
    result = scheduler.schedule(flights, strategy='least_busy')
    
    print("\n" + "=" * 70)
    print("RESULTS:")
    print("=" * 70)
    print(f"✅ Assigned: {len(result.assignments)} flights")
    print(f"❌ Unassigned: {len(result.unassigned_flights)} flights (exceeds daily limit)")
    
    # Check pilot hours
    if pilots[0].assigned_flights:
        print(f"\n👨‍✈️ Pilot {pilots[0].pilot_id}:")
        print(f"   Total hours: {pilots[0].total_hours_today:.2f}h / 8.00h max")
        print(f"   Flights assigned: {len(pilots[0].assigned_flights)}")
        print(f"   Remaining capacity: {pilots[0].get_remaining_hours():.2f}h")
    
    print("\n💡 Scheduler respects duty hour limits - preventing pilot fatigue!")
    print("=" * 70)


def demo_strategy_comparison():
    """Compare different scheduling strategies."""
    print("\n" + "-" * 70)
    print("SCENARIO 4: Comparing Scheduling Strategies")
    print("-" * 70)
    
    # Create flights
    base_time = datetime.now().replace(hour=10, minute=0, second=0, microsecond=0)
    flights = []
    for i in range(9):
        flights.append(Flight(
            f"FL{i+1:03d}",
            "JFK",
            "LHR",
            base_time + timedelta(hours=i * 12),
            15
        ))
    
    strategies = ['least_busy', 'most_available', 'round_robin']
    
    for strategy in strategies:
        scheduler = PilotScheduler(min_rest_hours=10.0, max_daily_hours=8.0)
        scheduler.create_pilots(3, base_airport='LHR')
        
        result = scheduler.schedule(flights.copy(), strategy=strategy)
        
        print(f"\n📊 Strategy: {strategy.replace('_', ' ').title()}")
        print(f"   Assigned: {len(result.assignments)}/{len(flights)}")
        print(f"   Pilots used: {result.total_pilots_used}/3")
        
        # Count assignments per pilot
        pilot_counts = {}
        for assignment in result.assignments:
            pilot_counts[assignment.pilot_id] = pilot_counts.get(assignment.pilot_id, 0) + 1
        
        print(f"   Distribution: {dict(sorted(pilot_counts.items()))}")
    
    print("\n" + "=" * 70)


def main():
    """Run all demonstrations."""
    print_banner()
    
    try:
        demo_basic_scheduling()
        
        input("\nPress Enter to continue to next scenario...")
        demo_rest_constraint()
        
        input("\nPress Enter to continue to next scenario...")
        demo_daily_hour_limit()
        
        input("\nPress Enter to continue to next scenario...")
        demo_strategy_comparison()
        
        print("\n" + "=" * 70)
        print("✅ All demonstrations completed successfully!")
        print("=" * 70)
        print("\n💡 Key Takeaways:")
        print("   • Scheduler enforces FAA regulations (10h rest, 8h max)")
        print("   • Pilot safety is prioritized over operational efficiency")
        print("   • Multiple strategies available for different scenarios")
        print("   • All schedules are validated before use")
        print("\n🎯 Try running the main application (python main.py) and select")
        print("   Option 8 for interactive pilot scheduling!")
        print()
        
    except KeyboardInterrupt:
        print("\n\n👋 Demo interrupted by user.\n")
    except Exception as e:
        print(f"\n❌ Error during demo: {e}")
        raise


if __name__ == "__main__":
    main()

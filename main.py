#!/usr/bin/env python3
"""
FlightOptima: Route Planner & Runway Scheduler

A backend simulation tool that calculates the most efficient flight path 
between airports and optimizes runway usage using graph coloring algorithms.

Usage:
    python main.py

Author: FlightOptima Team
Version: 1.0.0
"""

import os
import sys
from datetime import datetime, timedelta
from typing import Optional, List
import random

# Add src to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.models.airport import Airport
from src.models.flight import Flight
from src.models.graph import RouteGraph, ConflictGraph
from src.algorithms.routing import RoutePlanner, RouteResult
from src.algorithms.scheduling import RunwayScheduler, ScheduleResult
from src.utils.data_loader import DataLoader
from src.utils.time_utils import TimeUtils


class FlightOptimaApp:
    """
    Main application class for FlightOptima.
    
    Provides an interactive CLI for route planning and runway scheduling.
    """
    
    BANNER = """
╔═══════════════════════════════════════════════════════════════════════════════╗
║                                                                               ║
║     ███████╗██╗     ██╗ ██████╗ ██╗  ██╗████████╗ ██████╗ ██████╗ ████████╗   ║
║     ██╔════╝██║     ██║██╔════╝ ██║  ██║╚══██╔══╝██╔═══██╗██╔══██╗╚══██╔══╝   ║
║     █████╗  ██║     ██║██║  ███╗███████║   ██║   ██║   ██║██████╔╝   ██║      ║
║     ██╔══╝  ██║     ██║██║   ██║██╔══██║   ██║   ██║   ██║██╔═══╝    ██║      ║
║     ██║     ███████╗██║╚██████╔╝██║  ██║   ██║   ╚██████╔╝██║        ██║      ║
║     ╚═╝     ╚══════╝╚═╝ ╚═════╝ ╚═╝  ╚═╝   ╚═╝    ╚═════╝ ╚═╝        ╚═╝      ║
║                                                                               ║
║                 Route Planner & Runway Scheduler v1.0                         ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
"""
    
    def __init__(self):
        """Initialize the application."""
        self.data_loader = DataLoader()
        self.route_graph: Optional[RouteGraph] = None
        self.route_planner: Optional[RoutePlanner] = None
        self.scheduler = RunwayScheduler(algorithm='dsatur')
        self.flights: List[Flight] = []
        self.last_route_result: Optional[RouteResult] = None
        
    def clear_screen(self):
        """Clear the terminal screen."""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def print_banner(self):
        """Print the application banner."""
        print(self.BANNER)
    
    def print_menu(self):
        """Print the main menu."""
        print("\n" + "=" * 60)
        print("                      MAIN MENU")
        print("=" * 60)
        print("\n  [1] 📂 Load Airport & Route Data")
        print("  [2] 🗺️  Find Shortest Route Between Airports")
        print("  [3] ✈️  View All Available Airports")
        print("  [4] 🔍 Find All Possible Routes")
        print("  [5] 📅 Load Flight Schedule for Scheduling")
        print("  [6] 🎲 Generate Random Flights for Simulation")
        print("  [7] 🛬 Run Runway Scheduler")
        print("  [8] 📊 Full Demo (Route + Scheduling)")
        print("  [9] ℹ️  Help & About")
        print("  [0] 🚪 Exit")
        print("\n" + "=" * 60)
    
    def get_input(self, prompt: str, default: str = None) -> str:
        """Get user input with optional default value."""
        if default:
            user_input = input(f"{prompt} [{default}]: ").strip()
            return user_input if user_input else default
        return input(f"{prompt}: ").strip()
    
    def wait_for_enter(self):
        """Wait for user to press Enter."""
        input("\n⏎ Press Enter to continue...")
    
    def load_data(self):
        """Load airport and route data from CSV files."""
        print("\n" + "-" * 60)
        print("               LOADING DATA")
        print("-" * 60)
        
        try:
            # Check if data files exist
            airports_path = os.path.join(self.data_loader.data_dir, 'airports.csv')
            routes_path = os.path.join(self.data_loader.data_dir, 'routes.csv')
            
            if not os.path.exists(airports_path) or not os.path.exists(routes_path):
                print("\n⚠️  Data files not found. Creating sample data...")
                self.data_loader.create_sample_data()
            
            print("\n📂 Loading airports from airports.csv...")
            self.route_graph = self.data_loader.load_route_graph(
                bidirectional=True,
                calculate_distance=False  # Use distances from CSV
            )
            
            airports = self.route_graph.get_all_airports()
            edges = self.route_graph.get_all_edges()
            
            print(f"✅ Loaded {len(airports)} airports")
            print(f"✅ Loaded {len(edges)} routes")
            
            self.route_planner = RoutePlanner(self.route_graph)
            
            print("\n🎉 Data loaded successfully!")
            
        except Exception as e:
            print(f"\n❌ Error loading data: {e}")
        
        self.wait_for_enter()
    
    def view_airports(self):
        """Display all available airports."""
        if not self.route_graph:
            print("\n⚠️  Please load data first (Option 1)")
            self.wait_for_enter()
            return
        
        print("\n" + "-" * 60)
        print("               AVAILABLE AIRPORTS")
        print("-" * 60)
        
        airports = sorted(self.route_graph.get_all_airports(), key=lambda a: a.id)
        
        print(f"\n{'ID':<6} {'Name':<35} {'Lat':>8} {'Long':>9} {'Weather':>8}")
        print("-" * 70)
        
        for airport in airports:
            print(f"{airport.id:<6} {airport.name[:35]:<35} {airport.latitude:>8.4f} "
                  f"{airport.longitude:>9.4f} {airport.weather_factor:>8.2f}")
        
        print(f"\nTotal: {len(airports)} airports")
        self.wait_for_enter()
    
    def find_route(self):
        """Find the shortest route between two airports."""
        if not self.route_planner:
            print("\n⚠️  Please load data first (Option 1)")
            self.wait_for_enter()
            return
        
        print("\n" + "-" * 60)
        print("           FIND SHORTEST ROUTE")
        print("-" * 60)
        
        # Get source airport
        source = self.get_input("\n🛫 Enter source airport code (e.g., JFK)").upper()
        if not self.route_graph.has_node(source):
            print(f"\n❌ Airport '{source}' not found!")
            self.wait_for_enter()
            return
        
        # Get destination airport
        dest = self.get_input("🛬 Enter destination airport code (e.g., LHR)").upper()
        if not self.route_graph.has_node(dest):
            print(f"\n❌ Airport '{dest}' not found!")
            self.wait_for_enter()
            return
        
        if source == dest:
            print("\n❌ Source and destination cannot be the same!")
            self.wait_for_enter()
            return
        
        # Get departure time
        dep_input = self.get_input("🕐 Enter departure time (HH:MM) or press Enter for now", 
                                   datetime.now().strftime("%H:%M"))
        try:
            dep_time = datetime.strptime(dep_input, "%H:%M")
            dep_time = datetime.now().replace(
                hour=dep_time.hour, minute=dep_time.minute, second=0, microsecond=0
            )
        except ValueError:
            dep_time = datetime.now()
        
        # Get cruising speed
        speed_input = self.get_input("✈️  Enter cruising speed (km/h)", "850")
        try:
            speed = float(speed_input)
            self.route_planner.set_cruising_speed(speed)
        except ValueError:
            pass
        
        print("\n🔍 Calculating optimal route...")
        
        result = self.route_planner.find_shortest_path(source, dest, dep_time)
        
        if result:
            self.last_route_result = result
            print("\n" + str(result))
        else:
            print(f"\n❌ No route found from {source} to {dest}")
        
        self.wait_for_enter()
    
    def find_all_routes(self):
        """Find all possible routes between two airports."""
        if not self.route_planner:
            print("\n⚠️  Please load data first (Option 1)")
            self.wait_for_enter()
            return
        
        print("\n" + "-" * 60)
        print("         FIND ALL POSSIBLE ROUTES")
        print("-" * 60)
        
        source = self.get_input("\n🛫 Enter source airport code").upper()
        if not self.route_graph.has_node(source):
            print(f"\n❌ Airport '{source}' not found!")
            self.wait_for_enter()
            return
        
        dest = self.get_input("🛬 Enter destination airport code").upper()
        if not self.route_graph.has_node(dest):
            print(f"\n❌ Airport '{dest}' not found!")
            self.wait_for_enter()
            return
        
        max_stops = int(self.get_input("📍 Maximum intermediate stops", "3"))
        
        print("\n🔍 Finding all possible routes...")
        
        paths = self.route_planner.find_all_paths(source, dest, max_stops)
        
        if paths:
            print(f"\n✅ Found {len(paths)} possible route(s):\n")
            
            for i, path in enumerate(paths[:10], 1):  # Limit to first 10
                path_str = " -> ".join(a.id for a in path)
                stops = len(path) - 2
                print(f"  {i}. {path_str} ({stops} stop{'s' if stops != 1 else ''})")
            
            if len(paths) > 10:
                print(f"\n  ... and {len(paths) - 10} more routes")
        else:
            print(f"\n❌ No routes found from {source} to {dest}")
        
        self.wait_for_enter()
    
    def load_flights(self):
        """Load flight schedule from JSON file."""
        print("\n" + "-" * 60)
        print("           LOAD FLIGHT SCHEDULE")
        print("-" * 60)
        
        try:
            filename = self.get_input("\n📂 Enter filename", "simulated_schedules.json")
            self.flights = self.data_loader.load_flights(filename)
            
            print(f"\n✅ Loaded {len(self.flights)} flights")
            print("\n" + "-" * 50)
            
            for flight in sorted(self.flights, key=lambda f: f.arrival_start):
                print(f"  {flight.flight_id}: {flight.origin} -> {flight.destination} | "
                      f"Arrival: {flight.arrival_start.strftime('%H:%M')} | "
                      f"Duration: {flight.occupancy_time}min")
            
        except FileNotFoundError as e:
            print(f"\n❌ File not found: {e}")
        except Exception as e:
            print(f"\n❌ Error loading flights: {e}")
        
        self.wait_for_enter()
    
    def generate_random_flights(self):
        """Generate random flights for simulation."""
        print("\n" + "-" * 60)
        print("         GENERATE RANDOM FLIGHTS")
        print("-" * 60)
        
        # Get destination
        dest = self.get_input("\n🛬 Enter destination airport code", "LHR").upper()
        
        # Get number of flights
        try:
            num_flights = int(self.get_input("✈️  Number of flights to generate", "10"))
        except ValueError:
            num_flights = 10
        
        # Get time window
        try:
            window = int(self.get_input("⏱️  Time window (±minutes from now)", "60"))
        except ValueError:
            window = 60
        
        # Generate flights
        base_time = datetime.now().replace(second=0, microsecond=0)
        self.flights = []
        
        origins = ['JFK', 'CDG', 'FRA', 'DXB', 'SIN', 'ORD', 'LAX', 'MAD', 'FCO', 'IST', 'AMS']
        
        for i in range(num_flights):
            flight = Flight.generate_random(
                destination=dest,
                base_time=base_time,
                flight_number=i + 1,
                max_offset_minutes=window,
                occupancy_range=(10, 20)
            )
            # Assign a random origin
            flight.origin = random.choice([o for o in origins if o != dest])
            self.flights.append(flight)
        
        print(f"\n✅ Generated {len(self.flights)} random flights arriving at {dest}\n")
        print("-" * 60)
        
        for flight in sorted(self.flights, key=lambda f: f.arrival_start):
            print(f"  {flight.flight_id}: {flight.origin} -> {flight.destination} | "
                  f"Arrival: {flight.arrival_start.strftime('%H:%M')} - "
                  f"{flight.arrival_end.strftime('%H:%M')} | "
                  f"Priority: {flight.priority}")
        
        self.wait_for_enter()
    
    def run_scheduler(self):
        """Run the runway scheduler on loaded flights."""
        if not self.flights:
            print("\n⚠️  No flights loaded. Please load or generate flights first (Options 5 or 6)")
            self.wait_for_enter()
            return
        
        print("\n" + "-" * 60)
        print("            RUNWAY SCHEDULING")
        print("-" * 60)
        
        # Choose algorithm
        print("\n📊 Select scheduling algorithm:")
        print("  [1] DSatur (Degree of Saturation) - Recommended")
        print("  [2] Welsh-Powell (Degree ordering)")
        print("  [3] Greedy (Time-based ordering)")
        
        choice = self.get_input("\nChoose algorithm", "1")
        
        algorithms = {'1': 'dsatur', '2': 'welsh_powell', '3': 'greedy'}
        algorithm = algorithms.get(choice, 'dsatur')
        
        self.scheduler = RunwayScheduler(algorithm=algorithm)
        
        print(f"\n🔄 Running {algorithm.upper()} algorithm...")
        
        # Schedule flights
        result = self.scheduler.schedule(self.flights.copy())
        
        print("\n" + str(result))
        print("\n" + result.get_schedule_table())
        
        # Validate
        is_valid, conflicts = self.scheduler.validate_schedule(result.flights)
        
        if is_valid:
            print("\n✅ Schedule validation: PASSED - No conflicts detected!")
        else:
            print("\n❌ Schedule validation: FAILED")
            for conflict in conflicts:
                print(f"  - {conflict}")
        
        # Save option
        save = self.get_input("\n💾 Save schedule to file? (y/n)", "n")
        if save.lower() == 'y':
            filepath = self.data_loader.save_schedule(result.flights)
            print(f"✅ Schedule saved to: {filepath}")
        
        self.wait_for_enter()
    
    def run_full_demo(self):
        """Run a complete demo showing routing and scheduling."""
        print("\n" + "=" * 60)
        print("           FULL DEMONSTRATION")
        print("=" * 60)
        
        # Ensure data is loaded
        if not self.route_planner:
            print("\n📂 Loading airport and route data...")
            try:
                self.route_graph = self.data_loader.load_route_graph(
                    bidirectional=True,
                    calculate_distance=False
                )
                self.route_planner = RoutePlanner(self.route_graph)
                print("✅ Data loaded successfully!")
            except Exception as e:
                print(f"❌ Error loading data: {e}")
                self.wait_for_enter()
                return
        
        # Step 1: Find a route
        print("\n" + "-" * 50)
        print("STEP 1: Route Planning")
        print("-" * 50)
        
        source = self.get_input("\n🛫 Enter source airport", "JFK").upper()
        dest = self.get_input("🛬 Enter destination airport", "LHR").upper()
        
        if not self.route_graph.has_node(source) or not self.route_graph.has_node(dest):
            print("❌ Invalid airport code!")
            self.wait_for_enter()
            return
        
        dep_time = datetime.now().replace(second=0, microsecond=0)
        
        print(f"\n🔍 Finding optimal route from {source} to {dest}...")
        
        result = self.route_planner.find_shortest_path(source, dest, dep_time)
        
        if result:
            print("\n" + str(result))
            self.last_route_result = result
        else:
            print(f"❌ No route found!")
            self.wait_for_enter()
            return
        
        # Step 2: Generate flights arriving at destination
        print("\n" + "-" * 50)
        print("STEP 2: Simulating Airport Traffic")
        print("-" * 50)
        
        try:
            num_flights = int(self.get_input(f"\n✈️  Number of flights arriving at {dest}", "8"))
        except ValueError:
            num_flights = 8
        
        # Our flight's ETA
        our_eta = result.eta
        
        # Generate other flights around the same time
        self.flights = [
            Flight(
                flight_id="YOUR_FLIGHT",
                origin=source,
                destination=dest,
                arrival_start=our_eta,
                occupancy_time=15,
                priority=1  # Highest priority
            )
        ]
        
        origins = ['CDG', 'FRA', 'DXB', 'SIN', 'ORD', 'MAD', 'FCO', 'IST', 'AMS', 'BOS']
        
        for i in range(num_flights - 1):
            offset = random.randint(-30, 30)
            arrival = our_eta + timedelta(minutes=offset)
            
            flight = Flight(
                flight_id=f"FL{i+1:03d}",
                origin=random.choice([o for o in origins if o != dest]),
                destination=dest,
                arrival_start=arrival,
                occupancy_time=random.randint(10, 20),
                priority=random.randint(2, 8)
            )
            self.flights.append(flight)
        
        print(f"\n✅ Generated {len(self.flights)} flights (including yours)")
        print("\nIncoming flights at", dest + ":")
        print("-" * 50)
        
        for flight in sorted(self.flights, key=lambda f: f.arrival_start):
            marker = ">>> " if flight.flight_id == "YOUR_FLIGHT" else "    "
            print(f"{marker}{flight.flight_id}: {flight.origin} -> {flight.destination} | "
                  f"{flight.arrival_start.strftime('%H:%M')} - "
                  f"{flight.arrival_end.strftime('%H:%M')}")
        
        # Step 3: Run scheduler
        print("\n" + "-" * 50)
        print("STEP 3: Runway Scheduling")
        print("-" * 50)
        
        print("\n🔄 Running DSatur graph coloring algorithm...")
        
        schedule_result = self.scheduler.schedule(self.flights.copy())
        
        print(f"\n✅ Scheduling complete!")
        print(f"\n🛬 Minimum Runways Needed: {schedule_result.num_runways}")
        print(f"📊 Total Conflicts Resolved: {schedule_result.conflicts_resolved}")
        
        print("\n" + schedule_result.get_schedule_table())
        
        # Find our flight's runway
        our_flight = next((f for f in schedule_result.flights if f.flight_id == "YOUR_FLIGHT"), None)
        if our_flight:
            print(f"\n🎉 YOUR FLIGHT has been assigned to RUNWAY {our_flight.runway_id}")
            print(f"   Landing window: {our_flight.arrival_start.strftime('%H:%M')} - "
                  f"{our_flight.arrival_end.strftime('%H:%M')}")
        
        self.wait_for_enter()
    
    def show_help(self):
        """Display help information."""
        print("\n" + "=" * 60)
        print("                    HELP & ABOUT")
        print("=" * 60)
        
        print("""
FlightOptima v1.0.0 - Route Planner & Runway Scheduler

ABOUT:
------
FlightOptima is a backend simulation tool that:
  • Calculates optimal flight paths using Dijkstra's Algorithm
  • Schedules runway usage using Graph Coloring algorithms
  • Resolves scheduling conflicts automatically

ALGORITHMS:
-----------
1. Routing (Dijkstra's Algorithm):
   - Finds shortest weighted path in the airport graph
   - Considers distance and weather factors
   - Uses priority queue for efficiency (O(E log V))

2. Scheduling (Graph Coloring):
   - DSatur: Prioritizes vertices by saturation degree
   - Welsh-Powell: Orders by vertex degree
   - Greedy: Processes in time order
   - Minimizes number of runways needed

DATA FILES:
-----------
  • airports.csv: Airport definitions (ID, Name, Lat, Long)
  • routes.csv: Route connections (Source, Dest, Distance)
  • simulated_schedules.json: Pre-defined flight schedules

QUICK START:
------------
  1. Load data (Option 1)
  2. Find a route (Option 2)
  3. Generate flights (Option 6)
  4. Run scheduler (Option 7)
  
  OR use Full Demo (Option 8) for guided walkthrough!

TIPS:
-----
  • Airport codes are case-insensitive (JFK = jfk)
  • Weather factor > 1.0 means bad weather (longer travel)
  • Lower priority number = higher priority
""")
        
        self.wait_for_enter()
    
    def run(self):
        """Main application loop."""
        self.clear_screen()
        self.print_banner()
        
        while True:
            self.print_menu()
            
            choice = self.get_input("\n👉 Enter your choice")
            
            if choice == '1':
                self.load_data()
            elif choice == '2':
                self.find_route()
            elif choice == '3':
                self.view_airports()
            elif choice == '4':
                self.find_all_routes()
            elif choice == '5':
                self.load_flights()
            elif choice == '6':
                self.generate_random_flights()
            elif choice == '7':
                self.run_scheduler()
            elif choice == '8':
                self.run_full_demo()
            elif choice == '9':
                self.show_help()
            elif choice == '0':
                print("\n👋 Thank you for using FlightOptima! Safe travels! ✈️\n")
                break
            else:
                print("\n⚠️  Invalid choice. Please try again.")
            
            self.clear_screen()
            self.print_banner()


def main():
    """Entry point for the application."""
    try:
        app = FlightOptimaApp()
        app.run()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!\n")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

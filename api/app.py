"""
FlightOptima API - REST API for Route Planner & Runway Scheduler

This module provides a Flask-based REST API that exposes the core
functionality of FlightOptima for web applications.
"""

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from datetime import datetime, timedelta
import os
import sys
import random

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models.airport import Airport
from src.models.flight import Flight
from src.models.graph import RouteGraph, ConflictGraph
from src.algorithms.routing import RoutePlanner, RouteResult
from src.algorithms.scheduling import RunwayScheduler, ScheduleResult
from src.utils.data_loader import DataLoader


# Initialize Flask app
app = Flask(__name__, static_folder='../frontend/build', static_url_path='')
CORS(app)  # Enable CORS for React development

# Global instances
data_loader = DataLoader()
route_graph = None
route_planner = None


def init_data():
    """Initialize data on startup."""
    global route_graph, route_planner
    try:
        route_graph = data_loader.load_route_graph(bidirectional=True, calculate_distance=False)
        route_planner = RoutePlanner(route_graph)
        return True
    except Exception as e:
        print(f"Error loading data: {e}")
        return False


def airport_to_dict(airport: Airport) -> dict:
    """Convert Airport to JSON-serializable dict."""
    return {
        'id': airport.id,
        'name': airport.name,
        'latitude': airport.latitude,
        'longitude': airport.longitude,
        'weather_factor': airport.weather_factor
    }


def flight_to_dict(flight: Flight) -> dict:
    """Convert Flight to JSON-serializable dict."""
    return {
        'flight_id': flight.flight_id,
        'origin': flight.origin,
        'destination': flight.destination,
        'arrival_start': flight.arrival_start.isoformat(),
        'arrival_end': flight.arrival_end.isoformat(),
        'occupancy_time': flight.occupancy_time,
        'runway_id': flight.runway_id,
        'priority': flight.priority
    }


def route_result_to_dict(result: RouteResult) -> dict:
    """Convert RouteResult to JSON-serializable dict."""
    return {
        'source': airport_to_dict(result.source),
        'destination': airport_to_dict(result.destination),
        'path': [airport_to_dict(a) for a in result.path],
        'total_distance': round(result.total_distance, 2),
        'eta': result.eta.isoformat(),
        'flight_time_minutes': int(result.flight_time.total_seconds() / 60),
        'segments': [
            {
                'from': airport_to_dict(seg[0]),
                'to': airport_to_dict(seg[1]),
                'distance': round(seg[2], 2)
            }
            for seg in result.segments
        ]
    }


def schedule_result_to_dict(result: ScheduleResult) -> dict:
    """Convert ScheduleResult to JSON-serializable dict."""
    runway_assignments = {}
    for runway_id, flights in result.runway_assignments.items():
        runway_assignments[str(runway_id)] = [flight_to_dict(f) for f in sorted(flights, key=lambda x: x.arrival_start)]
    
    return {
        'flights': [flight_to_dict(f) for f in sorted(result.flights, key=lambda x: x.arrival_start)],
        'num_runways': result.num_runways,
        'runway_assignments': runway_assignments,
        'conflicts_resolved': result.conflicts_resolved
    }


# ==================== API Routes ====================

@app.route('/')
def serve_frontend():
    """Serve React frontend."""
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/api/health')
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'version': '1.0.0',
        'data_loaded': route_graph is not None
    })


@app.route('/api/airports')
def get_airports():
    """Get all airports."""
    if not route_graph:
        return jsonify({'error': 'Data not loaded'}), 500
    
    airports = route_graph.get_all_airports()
    return jsonify({
        'airports': [airport_to_dict(a) for a in sorted(airports, key=lambda x: x.id)],
        'count': len(airports)
    })


@app.route('/api/airports/<airport_id>')
def get_airport(airport_id):
    """Get a specific airport."""
    if not route_graph:
        return jsonify({'error': 'Data not loaded'}), 500
    
    airport = route_graph.get_node(airport_id.upper())
    if not airport:
        return jsonify({'error': f'Airport {airport_id} not found'}), 404
    
    return jsonify(airport_to_dict(airport))


@app.route('/api/routes')
def get_routes():
    """Get all routes."""
    if not route_graph:
        return jsonify({'error': 'Data not loaded'}), 500
    
    edges = route_graph.get_all_edges()
    routes = []
    
    for source_id, dest_id, distance in edges:
        source = route_graph.get_node(source_id)
        dest = route_graph.get_node(dest_id)
        if source and dest:
            routes.append({
                'source': airport_to_dict(source),
                'destination': airport_to_dict(dest),
                'distance': round(distance, 2)
            })
    
    return jsonify({
        'routes': routes,
        'count': len(routes)
    })


@app.route('/api/route/find', methods=['POST'])
def find_route():
    """Find shortest route between two airports."""
    if not route_planner:
        return jsonify({'error': 'Data not loaded'}), 500
    
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Request body required'}), 400
    
    source_id = data.get('source', '').upper()
    dest_id = data.get('destination', '').upper()
    
    if not source_id or not dest_id:
        return jsonify({'error': 'Source and destination required'}), 400
    
    # Parse departure time
    departure_str = data.get('departure_time')
    if departure_str:
        try:
            departure_time = datetime.fromisoformat(departure_str)
        except ValueError:
            departure_time = datetime.now()
    else:
        departure_time = datetime.now()
    
    # Set cruising speed if provided
    speed = data.get('cruising_speed', 850)
    route_planner.set_cruising_speed(float(speed))
    
    try:
        result = route_planner.find_shortest_path(source_id, dest_id, departure_time)
        
        if result:
            return jsonify({
                'success': True,
                'route': route_result_to_dict(result)
            })
        else:
            return jsonify({
                'success': False,
                'error': f'No route found from {source_id} to {dest_id}'
            }), 404
    
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/route/all', methods=['POST'])
def find_all_routes():
    """Find all possible routes between two airports."""
    if not route_planner:
        return jsonify({'error': 'Data not loaded'}), 500
    
    data = request.get_json()
    
    source_id = data.get('source', '').upper()
    dest_id = data.get('destination', '').upper()
    max_stops = data.get('max_stops', 3)
    
    if not source_id or not dest_id:
        return jsonify({'error': 'Source and destination required'}), 400
    
    try:
        paths = route_planner.find_all_paths(source_id, dest_id, max_stops)
        
        return jsonify({
            'success': True,
            'paths': [
                {
                    'airports': [airport_to_dict(a) for a in path],
                    'stops': len(path) - 2
                }
                for path in paths[:20]  # Limit to 20 paths
            ],
            'total_found': len(paths)
        })
    
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/flights/generate', methods=['POST'])
def generate_flights():
    """Generate random flights for simulation."""
    data = request.get_json() or {}
    
    destination = data.get('destination', 'LHR').upper()
    num_flights = min(data.get('count', 10), 50)  # Max 50 flights
    window_minutes = data.get('window_minutes', 60)
    
    # Parse base time
    base_time_str = data.get('base_time')
    if base_time_str:
        try:
            base_time = datetime.fromisoformat(base_time_str)
        except ValueError:
            base_time = datetime.now()
    else:
        base_time = datetime.now()
    
    base_time = base_time.replace(second=0, microsecond=0)
    
    # Generate flights
    origins = ['JFK', 'CDG', 'FRA', 'DXB', 'SIN', 'ORD', 'LAX', 'MAD', 'FCO', 'IST', 'AMS', 'BOS', 'SFO']
    flights = []
    
    for i in range(num_flights):
        offset = random.randint(-window_minutes, window_minutes)
        arrival = base_time + timedelta(minutes=offset)
        
        flight = Flight(
            flight_id=f"FL{i+1:03d}",
            origin=random.choice([o for o in origins if o != destination]),
            destination=destination,
            arrival_start=arrival,
            occupancy_time=random.randint(10, 20),
            priority=random.randint(1, 10)
        )
        flights.append(flight)
    
    return jsonify({
        'success': True,
        'flights': [flight_to_dict(f) for f in sorted(flights, key=lambda x: x.arrival_start)],
        'count': len(flights),
        'destination': destination
    })


@app.route('/api/schedule', methods=['POST'])
def schedule_flights():
    """Schedule flights to runways using graph coloring."""
    data = request.get_json()
    
    if not data or 'flights' not in data:
        return jsonify({'error': 'Flights data required'}), 400
    
    algorithm = data.get('algorithm', 'dsatur').lower()
    
    if algorithm not in ('dsatur', 'welsh_powell', 'greedy'):
        return jsonify({'error': 'Invalid algorithm. Use: dsatur, welsh_powell, or greedy'}), 400
    
    # Parse flights from request
    flights = []
    for f_data in data['flights']:
        try:
            arrival_start = datetime.fromisoformat(f_data['arrival_start'])
            flight = Flight(
                flight_id=f_data['flight_id'],
                origin=f_data.get('origin', 'UNK'),
                destination=f_data.get('destination', 'UNK'),
                arrival_start=arrival_start,
                occupancy_time=f_data.get('occupancy_time', 15),
                priority=f_data.get('priority', 5)
            )
            flights.append(flight)
        except (KeyError, ValueError) as e:
            return jsonify({'error': f'Invalid flight data: {e}'}), 400
    
    if not flights:
        return jsonify({'error': 'No valid flights provided'}), 400
    
    # Build conflict graph for visualization
    conflict_graph = ConflictGraph()
    conflict_graph.build_from_flights(flights)
    
    conflicts = []
    for source_id, neighbors in conflict_graph._adjacency_list.items():
        for dest_id, _ in neighbors:
            if source_id < dest_id:  # Avoid duplicates
                conflicts.append({'flight1': source_id, 'flight2': dest_id})
    
    # Run scheduler
    scheduler = RunwayScheduler(algorithm=algorithm)
    result = scheduler.schedule(flights)
    
    # Validate schedule
    is_valid, validation_errors = scheduler.validate_schedule(result.flights)
    
    response = schedule_result_to_dict(result)
    response['algorithm'] = algorithm
    response['is_valid'] = is_valid
    response['validation_errors'] = validation_errors
    response['conflicts'] = conflicts
    
    return jsonify(response)


@app.route('/api/schedule/demo', methods=['POST'])
def schedule_demo():
    """Run a complete demo: generate flights and schedule them."""
    data = request.get_json() or {}
    
    destination = data.get('destination', 'LHR').upper()
    num_flights = min(data.get('count', 10), 50)
    algorithm = data.get('algorithm', 'dsatur').lower()
    
    # Generate flights around current time
    base_time = datetime.now().replace(second=0, microsecond=0)
    origins = ['JFK', 'CDG', 'FRA', 'DXB', 'SIN', 'ORD', 'LAX', 'MAD', 'FCO', 'IST']
    
    flights = []
    for i in range(num_flights):
        offset = random.randint(-45, 45)
        arrival = base_time + timedelta(minutes=offset)
        
        flight = Flight(
            flight_id=f"FL{i+1:03d}",
            origin=random.choice([o for o in origins if o != destination]),
            destination=destination,
            arrival_start=arrival,
            occupancy_time=random.randint(10, 18),
            priority=random.randint(1, 10)
        )
        flights.append(flight)
    
    # Build conflict graph
    conflict_graph = ConflictGraph()
    conflict_graph.build_from_flights(flights)
    
    conflicts = []
    for source_id, neighbors in conflict_graph._adjacency_list.items():
        for dest_id, _ in neighbors:
            if source_id < dest_id:
                conflicts.append({'flight1': source_id, 'flight2': dest_id})
    
    # Schedule
    scheduler = RunwayScheduler(algorithm=algorithm)
    result = scheduler.schedule(flights)
    
    is_valid, _ = scheduler.validate_schedule(result.flights)
    
    response = schedule_result_to_dict(result)
    response['algorithm'] = algorithm
    response['is_valid'] = is_valid
    response['conflicts'] = conflicts
    response['destination'] = destination
    
    return jsonify(response)


@app.route('/api/route/with-scheduling', methods=['POST'])
def route_with_scheduling():
    """Find route and simulate scheduling at destination."""
    if not route_planner:
        return jsonify({'error': 'Data not loaded'}), 500
    
    data = request.get_json()
    
    source_id = data.get('source', '').upper()
    dest_id = data.get('destination', '').upper()
    num_flights = min(data.get('num_other_flights', 8), 30)
    
    if not source_id or not dest_id:
        return jsonify({'error': 'Source and destination required'}), 400
    
    departure_time = datetime.now().replace(second=0, microsecond=0)
    
    # Find route
    try:
        route_result = route_planner.find_shortest_path(source_id, dest_id, departure_time)
        
        if not route_result:
            return jsonify({'error': f'No route found from {source_id} to {dest_id}'}), 404
        
        # Generate flights arriving around our ETA
        our_eta = route_result.eta
        origins = ['JFK', 'CDG', 'FRA', 'DXB', 'SIN', 'ORD', 'LAX', 'MAD', 'FCO', 'IST', 'AMS']
        
        flights = [
            Flight(
                flight_id="YOUR_FLIGHT",
                origin=source_id,
                destination=dest_id,
                arrival_start=our_eta,
                occupancy_time=15,
                priority=1
            )
        ]
        
        for i in range(num_flights):
            offset = random.randint(-30, 30)
            arrival = our_eta + timedelta(minutes=offset)
            
            flight = Flight(
                flight_id=f"FL{i+1:03d}",
                origin=random.choice([o for o in origins if o != dest_id and o != source_id]),
                destination=dest_id,
                arrival_start=arrival,
                occupancy_time=random.randint(10, 18),
                priority=random.randint(2, 8)
            )
            flights.append(flight)
        
        # Build conflict graph
        conflict_graph = ConflictGraph()
        conflict_graph.build_from_flights(flights)
        
        conflicts = []
        for src, neighbors in conflict_graph._adjacency_list.items():
            for dst, _ in neighbors:
                if src < dst:
                    conflicts.append({'flight1': src, 'flight2': dst})
        
        # Schedule
        scheduler = RunwayScheduler(algorithm='dsatur')
        schedule_result = scheduler.schedule(flights)
        
        # Validate schedule
        is_valid, _ = scheduler.validate_schedule(schedule_result.flights)
        
        schedule_response = schedule_result_to_dict(schedule_result)
        schedule_response['is_valid'] = is_valid
        schedule_response['conflicts'] = conflicts
        
        return jsonify({
            'route': route_result_to_dict(route_result),
            'schedule': schedule_response,
            'your_flight': flight_to_dict(next(f for f in schedule_result.flights if f.flight_id == "YOUR_FLIGHT"))
        })
    
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


# Error handlers
@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors."""
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Endpoint not found'}), 404
    return send_from_directory(app.static_folder, 'index.html')


@app.errorhandler(500)
def server_error(e):
    """Handle 500 errors."""
    return jsonify({'error': 'Internal server error'}), 500


def create_app():
    """Factory function to create the Flask app."""
    init_data()
    return app


if __name__ == '__main__':
    print("🚀 Starting FlightOptima API Server...")
    init_data()
    print("✅ Data loaded successfully")
    print("📡 API running at http://localhost:5001")
    print("📖 API Docs: http://localhost:5001/api/health")
    app.run(debug=True, host='0.0.0.0', port=5001)

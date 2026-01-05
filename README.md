# FlightOptima: Route Planner, Runway Scheduler & Multi-Day Pilot Scheduler

A comprehensive flight planning and scheduling simulation tool featuring route optimization with Dijkstra's algorithm, runway scheduling using graph coloring, FAA-compliant multi-day pilot scheduling, and constrained runway operations with intelligent delay management.

## 🚀 Features

### Component A: Route Planner
- **Shortest Path Calculation**: Uses Dijkstra's Algorithm with Priority Queue for optimal O(E log V) performance
- **Distance Calculation**: Haversine formula for accurate great-circle distances
- **Weather Factors**: Optional weather-based route weighting
- **Multi-path Discovery**: Find all possible routes between airports
- **ETA Calculation**: Accurate arrival time estimation based on cruising speed

### Component B: Runway Scheduler
- **Conflict Detection**: Automatic identification of overlapping landing windows
- **Graph Coloring Algorithms**:
  - **DSatur** (Degree of Saturation) - Recommended for most cases
  - **Welsh-Powell** - Degree-based ordering
  - **Greedy** - Time-based ordering
- **Minimum Runway Optimization**: Minimizes the number of runways needed
- **Schedule Validation**: Ensures no conflicts in final assignments

### Component C: Multi-Day Pilot Scheduler 🆕
- **Multi-Day Operations**: Schedule pilots across 1-7 days with automatic daily hour resets
- **FAA Compliance**: Enforces 8-hour daily limit and 10-hour minimum rest requirements
- **Realistic Flight Patterns**: Generate flights with peak hours, uniform, or random distributions
- **Fair Distribution**: Multiple strategies (Least Busy, Most Available, Round Robin)
- **Pilot Reassignments**: Track which pilots work which days
- **Automatic Validation**: Comprehensive checks for all duty and rest requirements
- **Utilization Tracking**: Monitor pilot workload and capacity across multiple days
- **Safety First**: Prioritizes pilot well-being over operational efficiency

### Component D: Constrained Runway Scheduler 🆕
- **Limited Runway Capacity**: Simulate real-world runway constraints
- **Intelligent Delay Management**: Automatically delay flights when runways are full
- **Multiple Scheduling Algorithms**:
  - **Priority-Based**: Flight priority determines scheduling order
  - **Passenger-First**: Prioritize high-capacity flights
  - **Distance-First**: Long-haul flights get runway priority
  - **Hybrid**: Weighted combination (40% priority, 35% passengers, 25% distance)
- **Algorithm Comparison**: Compare all four algorithms to find the best for your scenario
- **Performance Metrics**: Track on-time percentage, average delays, and total delay time
- **Detailed Flight Data**: Passenger counts, distances, durations, and delay tracking

### 🌐 Web Application
- **Interactive Map**: Visualize flight routes on a world map with Leaflet
- **Four Navigation Tabs**:
  - **Route Planning**: Find optimal paths between airports
  - **Runway Scheduling**: Schedule flights with graph coloring
  - **Multi-Day Pilot Scheduling**: Assign pilots across multiple days
  - **Constrained Runways**: Simulate limited runway capacity
- **Real-time Scheduling**: Schedule flights with visual feedback
- **Responsive Design**: Works on desktop and mobile
- **Day-by-Day Breakdown**: View assignments grouped by day in multi-day mode
- **Algorithm Visualization**: Compare scheduling strategies side-by-side

## 📁 Project Structure

```
Flight_Planner/
│
├── data/                          # Data files
│   ├── airports.csv               # Airport definitions
│   ├── routes.csv                 # Route connections
│   └── simulated_schedules.json   # Sample flight schedules
│
├── src/
│   ├── __init__.py
│   ├── models/                    # Data Models
│   │   ├── airport.py             # Airport class (Node)
│   │   ├── flight.py              # Flight class with multi-day support
│   │   ├── pilot.py               # Pilot class
│   │   └── graph.py               # Graph implementations
│   │
│   ├── algorithms/                # Core Algorithms
│   │   ├── routing.py             # Dijkstra's implementation
│   │   ├── scheduling.py          # Graph Coloring implementation
│   │   ├── pilot_scheduling.py    # Single-day pilot scheduler
│   │   ├── multi_day_pilot_scheduling.py  # Multi-day scheduler 🆕
│   │   └── constrained_scheduling.py      # Constrained runway scheduler 🆕
│   │
│   └── utils/                     # Utilities
│       ├── data_loader.py         # CSV/JSON data loading
│       ├── time_utils.py          # Time interval operations
│       └── multi_day_generator.py # Multi-day flight generator 🆕
│
├── api/                           # REST API
│   ├── __init__.py
│   └── app.py                     # Flask API server (enhanced with new endpoints)
│
├── frontend/                      # React Frontend
│   ├── public/
│   │   └── index.html
│   ├── src/
│   │   ├── components/
│   │   │   ├── RunwayScheduleChart.js
│   │   │   ├── PilotScheduleViewer.js    # Enhanced for multi-day 🆕
│   │   │   └── ConstrainedRunwayViewer.js # New component 🆕
│   │   ├── App.js                 # Enhanced with 4 tabs
│   │   ├── api.js                 # Updated API client
│   │   ├── index.js
│   │   └── index.css              # Enhanced styles
│   └── package.json
│
├── tests/                         # Unit Tests
│   ├── test_routing.py
│   ├── test_scheduling.py
│   ├── test_pilot_scheduling.py
│   ├── test_multi_day_scheduling.py      # New tests 🆕
│   └── test_constrained_scheduling.py     # New tests 🆕
│
├── main.py                        # CLI Application
├── requirements.txt               # Dependencies
└── README.md                      # This file
```

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/Flight_Planner.git
   cd Flight_Planner
   ```

2. **Create a virtual environment** (recommended)
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install frontend dependencies** (for web application)
   ```bash
   cd frontend
   npm install
   cd ..
   ```

## 🚀 Quick Start

### Option 1: Command Line Interface (CLI)
```bash
python main.py
```

### Option 2: Web Application

**Terminal 1 - Start the API server:**
```bash
python -m api.app
```
The API will be available at `http://localhost:5000`

**Terminal 2 - Start the React frontend:**
```bash
cd frontend
npm start
```
The web app will open at `http://localhost:3000`

### Run Tests
```bash
python -m pytest tests/ -v
```

## 📖 Usage

### CLI Menu Options

1. **Load Airport & Route Data**: Load airports and routes from CSV files
2. **Find Shortest Route**: Calculate optimal path between two airports
3. **View All Airports**: List all available airports
4. **Find All Possible Routes**: Discover alternative routes
5. **Load Flight Schedule**: Load predefined flight schedules
6. **Generate Random Flights**: Create simulated traffic
7. **Run Runway Scheduler**: Schedule flights to minimize runways
8. **Run Ethical Pilot Scheduler**: Assign pilots with FAA compliance (NEW!)
9. **Full Demo**: Complete walkthrough of routing + scheduling + pilots
10. **Help & About**: View documentation and tips

### Example Workflow

```python
from src.utils.data_loader import DataLoader
from src.algorithms.routing import RoutePlanner
from src.algorithms.scheduling import RunwayScheduler
from src.algorithms.pilot_scheduling import PilotScheduler
from datetime import datetime

# Load data
loader = DataLoader()
graph = loader.load_route_graph()

# Find shortest route
planner = RoutePlanner(graph)
result = planner.find_shortest_path("JFK", "LHR", datetime.now())
print(result)

# Schedule flights to runways
flights = loader.load_flights()
scheduler = RunwayScheduler(algorithm='dsatur')
schedule = scheduler.schedule(flights)
print(schedule)

# Assign pilots ethically
pilot_scheduler = PilotScheduler(min_rest_hours=10.0, max_daily_hours=8.0)
pilot_scheduler.create_pilots(5, base_airport='LHR')
pilot_result = pilot_scheduler.schedule(flights, strategy='least_busy')
print(pilot_result)

# Validate compliance
is_valid, violations = pilot_scheduler.validate_schedule(pilot_result.assignments)
if is_valid:
    print("✅ All FAA regulations satisfied!")
```

### Pilot Scheduling Demo

Run the standalone pilot scheduling demo:

```bash
python demo_pilot_scheduling.py
```

This demonstrates:
- ✅ Basic pilot scheduling
- ✅ Rest requirement enforcement (10 hours)
- ✅ Daily hour limit enforcement (8 hours)
- ✅ Strategy comparison (Least Busy vs Round Robin)

For detailed documentation, see [PILOT_SCHEDULING.md](PILOT_SCHEDULING.md)
```

## 📊 Data Formats

### airports.csv
```csv
ID,Name,Latitude,Longitude,WeatherFactor
JFK,John F. Kennedy International,40.6413,-73.7781,1.0
LHR,London Heathrow,51.4700,-0.4543,1.1
```

### routes.csv
```csv
SourceID,DestID,Distance
JFK,LHR,5555
JFK,CDG,5834
```

### simulated_schedules.json
```json
{
  "flights": [
    {
      "flight_id": "FL001",
      "origin": "JFK",
      "destination": "LHR",
      "arrival_start": "2025-01-15T14:00:00",
      "occupancy_time": 15,
      "priority": 3
    }
  ]
}
```

## 🧮 Algorithms

### Dijkstra's Algorithm (Routing)
- **Time Complexity**: O(E log V) with priority queue
- **Space Complexity**: O(V)
- Uses min-heap for efficient next-node selection
- Supports early termination upon reaching destination

### Graph Coloring (Scheduling)

#### DSatur Algorithm
- Prioritizes vertices by saturation degree (distinct colors in neighbors)
- Excellent for sparse conflict graphs
- Generally produces optimal or near-optimal results

#### Welsh-Powell Algorithm
- Orders vertices by decreasing degree
- Simple and effective for regular graphs
- Guaranteed to use at most Δ+1 colors (Δ = max degree)

#### Greedy Algorithm
- Processes flights in arrival time order
- Fast execution
- May not always produce minimal coloring

## 🧪 Testing

The project includes comprehensive unit tests:

- **test_routing.py**: Tests for Dijkstra's algorithm, path finding, ETA calculation
- **test_scheduling.py**: Tests for graph coloring, conflict detection, validation

Run tests with coverage:
```bash
pip install pytest-cov
python -m pytest tests/ --cov=src --cov-report=html
```

## 🌐 API Reference

The REST API provides the following endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/airports` | GET | List all airports |
| `/api/routes` | GET | List all routes |
| `/api/route/find` | POST | Find shortest route between airports |
| `/api/schedule` | POST | Schedule flights to runways |
| `/api/schedule/demo` | GET | Get demo schedule data |
| `/api/route/with-scheduling` | POST | Find route and schedule at destination |
| `/api/pilots/schedule` | POST | Schedule pilots to flights (single day) |
| `/api/flights/generate-multi-day` | POST | Generate multi-day flights 🆕 |
| `/api/pilots/schedule-multi-day` | POST | Schedule pilots across multiple days 🆕 |
| `/api/runways/schedule-constrained` | POST | Schedule with runway constraints 🆕 |
| `/api/runways/compare-algorithms` | POST | Compare scheduling algorithms 🆕 |

### Example: Generate Multi-Day Flights
```bash
curl -X POST http://localhost:5000/api/flights/generate-multi-day \
  -H "Content-Type: application/json" \
  -d '{
    "destination": "JFK",
    "num_days": 3,
    "flights_per_day": 15,
    "pattern": "realistic"
  }'
```

### Example: Schedule Multi-Day Pilots
```bash
curl -X POST http://localhost:5000/api/pilots/schedule-multi-day \
  -H "Content-Type: application/json" \
  -d '{
    "flights": [...],
    "num_pilots": 10,
    "max_daily_hours": 8.0,
    "min_rest_hours": 10.0,
    "strategy": "least_busy"
  }'
```

### Example: Schedule with Runway Constraints
```bash
curl -X POST http://localhost:5000/api/runways/schedule-constrained \
  -H "Content-Type: application/json" \
  -d '{
    "flights": [...],
    "max_runways": 3,
    "algorithm": "hybrid"
  }'
```

### Example: Compare Scheduling Algorithms
```bash
curl -X POST http://localhost:5000/api/runways/compare-algorithms \
  -H "Content-Type: application/json" \
  -d '{
    "flights": [...],
    "max_runways": 3
  }'
```

## 🎯 Usage Examples

### Multi-Day Pilot Scheduling
```python
from src.utils.multi_day_generator import MultiDayFlightGenerator
from src.algorithms.multi_day_pilot_scheduling import MultiDayPilotScheduler
from src.models.pilot import Pilot

# Generate flights across 3 days
generator = MultiDayFlightGenerator()
flights = generator.generate_multi_day_flights(
    destination_airport="JFK",
    num_days=3,
    flights_per_day=15,
    pattern="realistic"
)

# Create pilots
pilots = [Pilot(f"P{i:03d}", f"Pilot {i}", "Commercial") for i in range(8)]

# Schedule pilots across all days
scheduler = MultiDayPilotScheduler()
result = scheduler.schedule(
    flights=flights,
    pilots=pilots,
    max_daily_hours=8.0,
    min_rest_hours=10.0,
    strategy="least_busy"
)

print(f"Total pilots used: {result.total_pilots_used}")
print(f"Days scheduled: {len(result.daily_schedules)}")
print(f"Total assignments: {len(result.all_assignments)}")
print(f"Compliance rate: {result.overall_compliance_rate}%")
print(f"FAA compliant: {result.is_valid}")
```

### Constrained Runway Scheduling
```python
from src.algorithms.constrained_scheduling import ConstrainedRunwayScheduler

scheduler = ConstrainedRunwayScheduler()

# Schedule with limited runways
result = scheduler.schedule(
    flights=flights,
    max_runways=3,
    algorithm="hybrid"
)

print(f"Algorithm: {result.algorithm}")
print(f"Total flights: {result.total_flights}")
print(f"Delayed flights: {len(result.delayed_flights)}")
print(f"On-time percentage: {result.on_time_percentage}%")
print(f"Average delay: {result.avg_delay_minutes} minutes")

# Compare all algorithms
comparison = scheduler.compare_algorithms(flights, max_runways=3)
print(f"Best algorithm: {comparison['best_algorithm']}")
```

## 📈 Performance

| Operation | Time Complexity | Space Complexity |
|-----------|-----------------|------------------|
| Dijkstra's Shortest Path | O(E log V) | O(V) |
| Graph Coloring (DSatur) | O(V² log V) | O(V²) |
| Conflict Graph Construction | O(n²) | O(n²) |

Where:
- V = number of airports/flights
- E = number of routes
- n = number of flights

## 🔧 Configuration

### Cruising Speed
Default: 850 km/h (typical commercial aircraft)
```python
planner.set_cruising_speed(900)  # km/h
```

### Weather Factors
- 1.0 = Clear weather (no penalty)
- \>1.0 = Bad weather (longer travel time)
- <1.0 = Favorable conditions

## 📝 License

MIT License - feel free to use and modify as needed.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Write tests for new functionality
4. Submit a pull request

## 📧 Contact

For questions or suggestions, please open an issue on GitHub 

# FlightOptima: Route Planner & Runway Scheduler

A comprehensive backend simulation tool that calculates the most efficient flight path between airports using weighted graphs and optimizes runway usage at destination airports using graph coloring algorithms.

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

### 🌐 Web Application (NEW!)
- **Interactive Map**: Visualize flight routes on a world map with Leaflet
- **Route Visualization**: See departure, destination, and waypoints
- **Runway Timeline**: Gantt-style chart showing runway assignments
- **Real-time Scheduling**: Schedule flights with visual feedback
- **Responsive Design**: Works on desktop and mobile

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
│   │   ├── flight.py              # Flight class (Scheduling Node)
│   │   └── graph.py               # Graph implementations
│   │
│   ├── algorithms/                # Core Algorithms
│   │   ├── routing.py             # Dijkstra's implementation
│   │   └── scheduling.py          # Graph Coloring implementation
│   │
│   └── utils/                     # Utilities
│       ├── data_loader.py         # CSV/JSON data loading
│       └── time_utils.py          # Time interval operations
│
├── api/                           # REST API (NEW!)
│   ├── __init__.py
│   └── app.py                     # Flask API server
│
├── frontend/                      # React Frontend (NEW!)
│   ├── public/
│   │   └── index.html
│   ├── src/
│   │   ├── components/
│   │   │   └── RunwayScheduleChart.js
│   │   ├── App.js
│   │   ├── api.js
│   │   ├── index.js
│   │   └── index.css
│   └── package.json
│
├── tests/                         # Unit Tests
│   ├── test_routing.py
│   └── test_scheduling.py
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
8. **Full Demo**: Complete walkthrough of routing + scheduling

### Example Workflow

```python
from src.utils.data_loader import DataLoader
from src.algorithms.routing import RoutePlanner
from src.algorithms.scheduling import RunwayScheduler
from datetime import datetime

# Load data
loader = DataLoader()
graph = loader.load_route_graph()

# Find shortest route
planner = RoutePlanner(graph)
result = planner.find_shortest_path("JFK", "LHR", datetime.now())
print(result)

# Schedule flights
flights = loader.load_flights()
scheduler = RunwayScheduler(algorithm='dsatur')
schedule = scheduler.schedule(flights)
print(schedule)
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

### Example: Find Shortest Route
```bash
curl -X POST http://localhost:5000/api/route/find \
  -H "Content-Type: application/json" \
  -d '{"origin": "JFK", "destination": "LHR"}'
```

### Example: Schedule Flights
```bash
curl -X POST http://localhost:5000/api/schedule \
  -H "Content-Type: application/json" \
  -d '{"flights": [...], "algorithm": "dsatur"}'
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

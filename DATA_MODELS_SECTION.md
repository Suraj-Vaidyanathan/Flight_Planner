# DATA MODELS SECTION
## For Methodology Chapter

---

### Data Models

The Flight Planner system employs a comprehensive set of data models to represent domain entities and algorithmic structures. The core entity models—Airport, Flight, and Pilot—encapsulate domain-specific attributes and implement validation logic in initialization to enforce data integrity constraints. These models serve as the foundation upon which algorithms operate, ensuring that invalid states cannot be represented.

**Core Domain Entity Attributes:**

| Entity | Key Attributes | Purpose |
|--------|---|---------|
| **Airport** | id, name, latitude, longitude, weather_factor | Network nodes in routing graph; geographic coordinates used for distance calculations |
| **Flight** | flight_id, origin, destination, arrival_start, occupancy_time, runway_id, priority | Scheduling entities; temporal windows for conflict detection |
| **Pilot** | pilot_id, certification, max_daily_hours, min_rest_hours, current_duty_hours | Resource allocation; FAA compliance constraints |

The Airport model computes distances to other airports via the Haversine formula, providing edge weights for the routing graph. The Flight model automatically calculates arrival end time from occupancy duration and implements overlap detection with other flights through interval intersection logic. The Pilot model tracks cumulative duty hours and validates assignments against regulatory constraints.

**Graph Structure Models:**

| Graph Type | Vertices | Edges | Directionality | Primary Use |
|-----------|----------|-------|----------------|-------------|
| **RouteGraph** | Airports | Distance-weighted routes | Directed | Dijkstra pathfinding |
| **ConflictGraph** | Flights | Temporal overlaps | Undirected | Graph coloring |
| **Generic Graph** | Generic type T | Weighted edges | Configurable | Extensible base structure |

Graph models implement adjacency list representation for memory efficiency. The RouteGraph maintains weighted, directed edges representing flight routes with distance metrics. The ConflictGraph maintains undirected edges representing temporal conflicts between flights, enabling efficient neighbor enumeration for coloring algorithms. All graph structures enforce node existence validation prior to edge insertion, preventing orphaned edges and maintaining structural integrity required for algorithm correctness.

---

**Word Count:** 271 words

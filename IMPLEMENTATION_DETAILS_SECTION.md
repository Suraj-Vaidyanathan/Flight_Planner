# IMPLEMENTATION DETAILS SECTION
## For Methodology Chapter

---

### Implementation Details

The Flight Planner system implements a RESTful API architecture with three primary endpoints facilitating algorithmic execution and data retrieval. The route optimization endpoint accepts source and destination airport parameters, invokes the Dijkstra pathfinding algorithm, and returns optimal paths with distance and time metrics. The runway scheduling endpoint receives flight lists and scheduling algorithm preferences, executes graph coloring algorithms, and returns conflict-free runway assignments. The pilot assignment endpoint distributes flights across available pilots using fairness-aware strategies while validating FAA regulatory compliance.

**Frontend-Backend Communication Architecture:**

```
┌─────────────────────────────────────────────────────────────┐
│                    REACT FRONTEND LAYER                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │   App.js     │  │   api.js     │  │ RunwaySchedule   │  │
│  │  (State Mgmt)│  │(HTTP Client) │  │  Chart.js        │  │
│  └──────┬───────┘  └──────┬───────┘  └────────┬─────────┘  │
└─────────┼──────────────────┼────────────────────┼────────────┘
          │                  │                    │
          └──────────────────┼────────────────────┘
                      HTTP/JSON Requests
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│              FLASK REST API LAYER (app.py)                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ GET /route   │  │POST /schedule│  │POST /assign-     │  │
│  │              │  │              │  │pilots            │  │
│  └──────┬───────┘  └──────┬───────┘  └────────┬─────────┘  │
└─────────┼──────────────────┼────────────────────┼────────────┘
          │                  │                    │
          └──────────────────┼────────────────────┘
                    Method Invocations
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
         ▼                   ▼                   ▼
    ┌─────────────┐  ┌─────────────┐  ┌──────────────────┐
    │RoutePlanner │  │RunwayScheduler│ │PilotScheduler  │
    │(routing.py) │  │(scheduling.py)│ │(pilot_sched.py)│
    └─────────────┘  └─────────────┘  └──────────────────┘
         │                   │                   │
         └───────────────────┼───────────────────┘
              Data Model & Graph Operations
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
         ▼                   ▼                   ▼
    ┌─────────────┐  ┌─────────────┐  ┌──────────────────┐
    │RouteGraph   │  │ConflictGraph│  │PilotModels,     │
    │(Airports)   │  │(Flights)    │  │Validation Logic │
    └─────────────┘  └─────────────┘  └──────────────────┘
         │                   │                   │
         └───────────────────┼───────────────────┘
                      JSON Response
                             │
         ┌───────────────────┴───────────────────┐
         │                                       │
         ▼                                       ▼
    ┌──────────────────────────────────────────────┐
    │  Frontend renders results via React          │
    │  components and visualization charts         │
    └──────────────────────────────────────────────┘
```

The frontend layer implements three primary React components: App.js manages application state and user interactions, api.js abstracts HTTP communication through an Axios wrapper, and RunwayScheduleChart.js visualizes scheduling results using Chart.js. Data flows unidirectionally from user input through API requests, algorithm execution, and response handling back to component rendering. The backend validates all incoming requests, enforces data constraints, executes appropriate algorithms, and returns structured JSON responses containing results and metadata required for visualization.

---

**Word Count:** 268 words

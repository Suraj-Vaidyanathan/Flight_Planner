# SYSTEM ARCHITECTURE SECTION
## For Methodology Chapter

---

### System Architecture

The Flight Planner system implements a three-tier client-server architecture with distinct separation of concerns across presentation, application, and data processing layers. The frontend layer, developed in React.js, provides the user interface and handles request orchestration through an Axios HTTP client. This layer communicates exclusively with the backend via RESTful endpoints, insulating algorithmic logic from presentation concerns.

The application layer consists of a Flask REST API server that acts as the primary controller, receiving HTTP requests from the frontend and delegating computation to specialized algorithmic modules. The core algorithms are organized into three independent engines: the routing engine implements Dijkstra's shortest path algorithm for route optimization, the scheduling engine employs graph coloring algorithms for runway conflict resolution, and the pilot scheduler enforces fairness metrics alongside regulatory compliance validation. 

The data model layer provides abstract representations of domain entities—airports, flights, and pilots—along with generic graph structures utilized by both routing and scheduling algorithms. Data models enforce domain constraints through validation in initialization, ensuring algorithmic correctness. The utility layer manages data loading from persistent storage (CSV files for airport and route definitions, JSON for simulated schedules) and provides temporal calculations required across algorithms. Request flow initiates from the frontend, traverses the REST API for validation and routing, executes within appropriate algorithm modules, and returns results as JSON responses for visualization.

---

**Word Count:** 237 words

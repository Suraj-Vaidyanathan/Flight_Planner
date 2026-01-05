# TOOLS AND TECHNIQUES SECTION
## For Methodology Chapter

---

### Tools and Techniques

The Flight Planner system leverages a carefully selected technology stack optimized for algorithmic implementation, scalability, and maintainability. The selection of each tool reflects deliberate engineering trade-offs between performance, development velocity, and ecosystem maturity. Backend development utilizes Python for its superior algorithm implementation support, extensive built-in data structure libraries (heapq for priority queues, collections for graph adjacency lists), and rapid prototyping capabilities. Flask was selected as the REST API framework for its minimal overhead, straightforward routing mechanisms, and excellent CORS support without substantial configuration complexity.

**Complete Technology Stack Architecture:**

```
┌────────────────────────────────────────────────────────────────────┐
│                    FRONTEND TECHNOLOGIES                           │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │  React.js    │  │ JavaScript   │  │   Axios HTTP Client  │   │
│  │ (Framework)  │  │  (ES6+)      │  │  (Promise-based)     │   │
│  └──────────────┘  └──────────────┘  └──────────────────────┘   │
│                                                                    │
│  ┌──────────────┐  ┌──────────────┐                              │
│  │  Chart.js    │  │    CSS3      │                              │
│  │(Visualization)│  │  (Styling)   │                              │
│  └──────────────┘  └──────────────┘                              │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────┐
│                    BACKEND TECHNOLOGIES                            │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │  Python 3.x  │  │    Flask     │  │   heapq (Priority    │   │
│  │ (Language)   │  │ (Framework)  │  │   Queue)             │   │
│  └──────────────┘  └──────────────┘  └──────────────────────┘   │
│                                                                    │
│  ┌──────────────┐  ┌──────────────┐                              │
│  │   pytest     │  │  Pandas/     │                              │
│  │  (Testing)   │  │  NumPy       │                              │
│  │              │  │ (Data Proc.) │                              │
│  └──────────────┘  └──────────────┘                              │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────┐
│              DATA FORMATS & VERSION CONTROL                        │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │  CSV Files   │  │  JSON Files  │  │   Git/GitHub         │   │
│  │(Static Data) │  │(Schedules)   │  │ (Version Control)    │   │
│  └──────────────┘  └──────────────┘  └──────────────────────┘   │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

**Technology Justification:**

The frontend framework React.js enables component-based architecture with efficient virtual DOM rendering, minimizing manual DOM manipulation and supporting reactive state updates. JavaScript ES6+ provides modern asynchronous capabilities (Promises/async-await) essential for HTTP communication. Axios abstracts HTTP client complexity with automatic JSON serialization and promise-based request handling superior to lower-level fetch API alternatives. Chart.js facilitates runway schedule visualization without introducing heavy dependencies. Python's heapq library provides binary min-heap priority queue implementation essential for Dijkstra's algorithm efficiency, while pytest enables fixture-based unit testing with parametrized test cases reducing code duplication. Git/GitHub supports collaborative development with branch strategies (pilot_feature branch implementation) enabling parallel feature development.

---

**Word Count:** 292 words

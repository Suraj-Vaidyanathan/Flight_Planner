# ALGORITHM DESIGN SECTION
## For Methodology Chapter

---

### Algorithm Design

The Flight Planner system integrates three specialized algorithms to address distinct optimization problems inherent to aviation logistics. The routing algorithm employs Dijkstra's shortest path algorithm with binary min-heap priority queue to compute minimum-distance paths between airports in a weighted, directed graph. Each airport represents a vertex, and direct routes between airports represent weighted edges, with edge weights corresponding to geographical distances computed via the Haversine formula. The algorithm terminates upon reaching the destination, providing optimal route paths along with total distance and estimated flight time calculations.

**Routing Algorithm Characteristics:**

| Aspect | Details |
|--------|---------|
| **Algorithm** | Dijkstra's Shortest Path with Min-Heap |
| **Time Complexity** | O((V + E) log V) |
| **Space Complexity** | O(V + E) |
| **Optimality** | Guaranteed optimal solution |
| **Graph Type** | Weighted, directed |
| **Key Advantage** | Early termination upon destination reach |

The runway scheduling algorithm formulates the assignment problem as a graph coloring challenge, wherein flights represent vertices and temporal overlaps represent edges. Three coloring strategies are implemented with distinct performance-quality trade-offs:

| Algorithm | Time Complexity | Solution Quality | Best Use Case |
|-----------|-----------------|------------------|---------------|
| **Welsh-Powell** | O(V² + E) | Good | Moderate-sized networks |
| **DSatur** | O(V² + E) | Excellent | Optimal runway minimization |
| **Greedy** | O(V² + E) | Fair | Speed-critical applications |

The objective is to assign each flight to a runway such that no temporally conflicting flights share a single runway resource, thereby minimizing the total number of required runways. Conflicts are detected when flight arrival time windows overlap, represented as undirected edges in the conflict graph.

The pilot assignment algorithm implements fairness-aware bipartite matching constrained by regulatory compliance. Three assignment strategies distribute flight assignments across available pilots:

| Strategy | Optimization Focus | Fairness Metric |
|----------|-------------------|-----------------|
| **Least-Busy** | Minimize maximum duty hours | Even distribution |
| **Most-Available** | Maximize capacity utilization | Total hours assigned |
| **Round-Robin** | Equitable rotation | Equal assignment attempts |

All strategies enforce Federal Aviation Administration duty hour restrictions, minimum rest period requirements, and occupancy time constraints. Assignments are validated through compliance checks prior to confirmation, ensuring adherence to regulatory frameworks governing pilot work schedules.

---

**Word Count:** 267 words

# Ethical Pilot Scheduling

## Overview

The Ethical Pilot Scheduling feature ensures that pilots are assigned to flights in compliance with FAA regulations and ethical labor practices. The scheduler prioritizes pilot safety and well-being by enforcing mandatory rest periods and duty hour limits.

## Features

### 1. **FAA Compliance**
- **Maximum Daily Hours**: 8 hours per day (configurable)
- **Minimum Rest Period**: 10 hours between flights (configurable)
- **Automatic Validation**: All schedules are validated against regulations

### 2. **Fair Distribution Strategies**

The scheduler supports three assignment strategies:

#### Least Busy (Recommended)
- Assigns flights to pilots with the fewest hours worked
- Ensures fair workload distribution
- Prevents overwork of individual pilots

#### Most Available
- Assigns flights to pilots with the most remaining hours
- Maximizes pilot capacity utilization
- Good for high-volume scheduling

#### Round Robin
- Assigns flights evenly based on assignment count
- Simple and predictable distribution
- Suitable for uniform flight durations

### 3. **Ethical Constraints**

The scheduler enforces:
- **No consecutive flights**: Pilots must have rest between assignments
- **Daily hour limits**: Cannot exceed maximum duty hours
- **Fatigue prevention**: Minimum rest periods strictly enforced
- **Transparency**: All violations are reported clearly

## Usage

### Command Line Interface

```bash
python main.py
# Select Option 8: Run Ethical Pilot Scheduler
```

### Programmatic Usage

```python
from src.algorithms.pilot_scheduling import PilotScheduler
from src.models.pilot import Pilot
from src.models.flight import Flight
from datetime import datetime, timedelta

# Create scheduler with custom parameters
scheduler = PilotScheduler(
    min_rest_hours=10.0,  # FAA requirement
    max_daily_hours=8.0    # FAA requirement
)

# Create pilots
pilots = scheduler.create_pilots(5, base_airport='JFK')

# Create flights
flights = [
    Flight(
        flight_id="FL001",
        origin="JFK",
        destination="LHR",
        arrival_start=datetime.now(),
        occupancy_time=15
    ),
    # ... more flights
]

# Schedule pilots to flights
result = scheduler.schedule(flights, strategy='least_busy')

# Check results
print(f"Assigned: {len(result.assignments)}")
print(f"Compliance Rate: {result.compliance_rate:.1f}%")

# Validate schedule
is_valid, violations = scheduler.validate_schedule(result.assignments)
if is_valid:
    print("✅ All FAA regulations satisfied!")
else:
    print("❌ Violations detected:")
    for violation in violations:
        print(f"  • {violation}")
```

## Models

### Pilot

Represents a pilot available for flight assignments.

```python
@dataclass
class Pilot:
    pilot_id: str
    name: str
    certification: str = 'ATP'  # Airline Transport Pilot
    max_daily_hours: float = 8.0
    min_rest_hours: float = 10.0
    assigned_flights: List[str] = field(default_factory=list)
    last_flight_end: Optional[datetime] = None
    total_hours_today: float = 0.0
    home_base: str = ''
```

Key methods:
- `can_fly(flight_start, duration)`: Check if pilot can take a flight
- `assign_flight(...)`: Assign a flight to the pilot
- `get_availability_time()`: Get when pilot is next available
- `get_remaining_hours()`: Get remaining duty hours

### PilotAssignment

Represents an assignment of a pilot to a flight.

```python
@dataclass
class PilotAssignment:
    pilot_id: str
    flight_id: str
    assignment_time: datetime
    flight_start: datetime
    flight_end: datetime
```

### PilotScheduleResult

Contains the complete scheduling result.

```python
@dataclass
class PilotScheduleResult:
    assignments: List[PilotAssignment]
    unassigned_flights: List[Flight]
    pilot_utilization: Dict[str, float]
    total_pilots_used: int
    compliance_rate: float
```

## Algorithm

The pilot scheduler uses a **greedy time-based assignment** algorithm:

1. **Sort flights** by start time (earliest first)
2. **For each flight**:
   - Find available pilots who meet constraints
   - Select pilot based on strategy (least busy, most available, etc.)
   - Assign pilot to flight and update their status
3. **Validate** the complete schedule against all regulations

### Time Complexity
- **O(n × m)** where:
  - n = number of flights
  - m = number of pilots

### Space Complexity
- **O(n + m)** for storing flights and pilots

## FAA Regulations

The scheduler implements the following FAA regulations:

### 14 CFR Part 117 (Flight and Duty Limitations)

- **§117.11 Flight time limitation**: Maximum 8 hours in 24 consecutive hours
- **§117.25 Rest period**: Minimum 10 hours before duty
- **§117.27 Consecutive nighttime operations**: Additional rest requirements (simplified in this implementation)

### Configurable Parameters

While FAA regulations are the default, you can customize:

```python
scheduler = PilotScheduler(
    min_rest_hours=12.0,  # More strict than FAA
    max_daily_hours=6.0    # Reduced duty hours
)
```

## Examples

### Example 1: Basic Scheduling

```python
scheduler = PilotScheduler()
pilots = scheduler.create_pilots(3)

flights = [
    Flight("FL001", "JFK", "LHR", datetime.now(), 15),
    Flight("FL002", "CDG", "LHR", datetime.now() + timedelta(hours=1), 15),
    Flight("FL003", "FRA", "LHR", datetime.now() + timedelta(hours=2), 15),
]

result = scheduler.schedule(flights, strategy='least_busy')
print(result)
```

### Example 2: Handling High Volume

```python
# Create more pilots for high volume
scheduler = PilotScheduler()
scheduler.create_pilots(10)  # 10 pilots

# Generate many flights
flights = []
for i in range(50):
    flights.append(Flight(
        f"FL{i:03d}",
        "JFK",
        "LHR",
        datetime.now() + timedelta(hours=i * 0.5),
        15
    ))

result = scheduler.schedule(flights, strategy='most_available')

print(f"Successfully assigned: {len(result.assignments)}/50 flights")
print(f"Pilots used: {result.total_pilots_used}/10")
```

### Example 3: Validating an Existing Schedule

```python
# Load assignments from somewhere
assignments = [...]

is_valid, violations = scheduler.validate_schedule(assignments)

if not is_valid:
    print("Schedule violations found:")
    for violation in violations:
        print(f"  ❌ {violation}")
```

## Statistics and Monitoring

The scheduler provides detailed statistics:

```python
result = scheduler.schedule(flights)

# Get statistics
stats = scheduler.get_statistics()

print(f"Total Pilots: {stats['total_pilots']}")
print(f"Active Pilots: {stats['active_pilots']}")
print(f"Average Hours: {stats['avg_hours_per_pilot']:.1f}h")
print(f"Utilization: {stats['utilization_rate']:.1f}%")

# Check pilot utilization
for pilot_id, util in result.pilot_utilization.items():
    print(f"Pilot {pilot_id}: {util:.1f}% utilized")
```

## Best Practices

### 1. Right-Size Your Pilot Fleet

```python
num_flights = len(flights)
avg_flight_duration = 0.75  # hours
total_hours_needed = num_flights * avg_flight_duration

# Add buffer for rest requirements
recommended_pilots = int((total_hours_needed / 8.0) * 1.5) + 1
```

### 2. Monitor Compliance Rate

```python
result = scheduler.schedule(flights)

if result.compliance_rate < 90.0:
    print("⚠️  Low compliance rate - consider adding more pilots")
    recommended = scheduler._pilots + len(result.unassigned_flights) // 2
    print(f"Recommended: {recommended} pilots")
```

### 3. Use Appropriate Strategy

- **High-volume, time-critical**: `most_available`
- **Fair distribution**: `least_busy` (recommended)
- **Simple, predictable**: `round_robin`

### 4. Validate Before Deployment

```python
# Always validate after scheduling
is_valid, violations = scheduler.validate_schedule(result.assignments)

if not is_valid:
    raise Exception("Schedule violates FAA regulations")
```

## Testing

Run the test suite:

```bash
# Run all pilot scheduling tests
python -m pytest tests/test_pilot_scheduling.py -v

# Run specific test
python -m pytest tests/test_pilot_scheduling.py::TestPilotScheduler::test_schedule_simple -v
```

## Limitations

1. **Single-day scheduling**: Currently assumes all flights occur within a single day
2. **Simplified flight duration**: Uses occupancy_time + buffer as proxy
3. **No timezone handling**: All times are assumed to be in the same timezone
4. **Basic certification**: Doesn't distinguish between aircraft types
5. **No crew pairing**: Assigns individual pilots, not crew pairs

## Future Enhancements

- [ ] Multi-day scheduling with rolling windows
- [ ] Timezone-aware scheduling for international flights
- [ ] Aircraft type certification matching
- [ ] Crew pairing (captain + first officer)
- [ ] Monthly/yearly duty hour limits
- [ ] Preference-based scheduling
- [ ] Optimization for fuel efficiency
- [ ] Integration with crew management systems

## References

- [FAA Part 117 - Flight and Duty Limitations](https://www.faa.gov/regulations_policies/rulemaking/recently_published/media/2120-AJ58_FinalRule.pdf)
- [ICAO Fatigue Management](https://www.icao.int/safety/fatiguemanagement/)
- [Airline Pilot Central - Duty Regulations](https://www.airlinepilotcentral.com/)

## License

This implementation is for educational and simulation purposes. Always consult with aviation legal experts before deploying in production environments.

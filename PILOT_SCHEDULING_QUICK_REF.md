# Pilot Scheduling Quick Reference

## Quick Start

```python
from src.algorithms.pilot_scheduling import PilotScheduler
from src.models.flight import Flight

# Create scheduler
scheduler = PilotScheduler(min_rest_hours=10.0, max_daily_hours=8.0)

# Create pilots
scheduler.create_pilots(5, base_airport='LHR')

# Schedule flights
result = scheduler.schedule(flights, strategy='least_busy')

# Check results
print(f"Compliance: {result.compliance_rate:.1f}%")
```

## FAA Regulations

| Regulation | Value | Configurable |
|------------|-------|--------------|
| Max Daily Hours | 8.0 hours | ✅ Yes |
| Min Rest Period | 10.0 hours | ✅ Yes |

## Scheduling Strategies

| Strategy | Best For | Description |
|----------|----------|-------------|
| `least_busy` | ✅ **Recommended** | Fair workload distribution |
| `most_available` | High volume | Maximize pilot utilization |
| `round_robin` | Simple needs | Equal assignment count |

## Key Classes

### Pilot
```python
pilot = Pilot(
    pilot_id="P001",
    name="Capt. Smith",
    max_daily_hours=8.0,
    min_rest_hours=10.0
)

# Check availability
if pilot.can_fly(flight_start, duration_hours):
    pilot.assign_flight(flight_id, start, end, duration)
```

### PilotScheduler
```python
scheduler = PilotScheduler(
    min_rest_hours=10.0,
    max_daily_hours=8.0
)

# Create pilots
pilots = scheduler.create_pilots(count=5, base_airport='LHR')

# Schedule
result = scheduler.schedule(flights, strategy='least_busy')

# Validate
is_valid, violations = scheduler.validate_schedule(result.assignments)
```

## Common Use Cases

### 1. Schedule with Automatic Pilot Creation
```python
scheduler = PilotScheduler()
scheduler.create_pilots(5)
result = scheduler.schedule(flights, strategy='least_busy')
```

### 2. Custom Parameters
```python
scheduler = PilotScheduler(
    min_rest_hours=12.0,  # Stricter than FAA
    max_daily_hours=6.0    # Reduced hours
)
```

### 3. Check Compliance
```python
result = scheduler.schedule(flights)

if result.compliance_rate < 90.0:
    needed = len(result.unassigned_flights) // 2 + 1
    print(f"Consider adding {needed} more pilots")
```

### 4. Get Statistics
```python
stats = scheduler.get_statistics()
print(f"Utilization: {stats['utilization_rate']:.1f}%")
print(f"Avg hours: {stats['avg_hours_per_pilot']:.1f}h")
```

## CLI Menu

```
[8] 👨‍✈️  Run Ethical Pilot Scheduler
```

## Command Line

```bash
# Run main application
python main.py

# Run demo
python demo_pilot_scheduling.py

# Run tests
python -m pytest tests/test_pilot_scheduling.py -v
```

## Validation

```python
is_valid, violations = scheduler.validate_schedule(assignments)

if not is_valid:
    for violation in violations:
        print(f"❌ {violation}")
```

## Result Object

```python
result = scheduler.schedule(flights)

# Access results
result.assignments           # List[PilotAssignment]
result.unassigned_flights    # List[Flight]
result.pilot_utilization     # Dict[str, float]
result.total_pilots_used     # int
result.compliance_rate       # float (0-100)
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Low compliance rate | Add more pilots |
| Unassigned flights | Increase max_daily_hours or add pilots |
| Validation fails | Check flight spacing and total hours |
| All flights to one pilot | Use 'least_busy' strategy |

## Performance

- **Small** (< 20 flights, < 5 pilots): < 1ms
- **Medium** (50 flights, 10 pilots): < 10ms  
- **Large** (100+ flights, 20+ pilots): < 100ms

## Best Practices

1. ✅ **Always validate** schedules before deployment
2. ✅ Use **'least_busy'** for fair distribution
3. ✅ Add **20-30% buffer** pilots for flexibility
4. ✅ Monitor **compliance rate** (aim for > 95%)
5. ✅ Check **pilot utilization** to avoid underutilization

## Documentation

- Full docs: `PILOT_SCHEDULING.md`
- Implementation: `IMPLEMENTATION_SUMMARY.md`
- Main README: `README.md`
- Code: `src/algorithms/pilot_scheduling.py`

## Examples

See `demo_pilot_scheduling.py` for complete working examples.

# FlightOptima Enhancement Implementation Guide

## 🎯 Overview

This document provides a comprehensive guide to implement the new features in FlightOptima:

1. **Multi-Day Pilot Scheduling** - Pilots work across multiple days with proper rest periods
2. **Fixed-Constraint Runway Scheduling** - Limited runways with flight delays based on various priority algorithms
3. **Enhanced Frontend** - New visualizations and controls for both features

## 📊 Backend Implementation Status

### ✅ Completed Backend Components

#### 1. Multi-Day Flight Generator (`src/utils/multi_day_generator.py`)
- **File Created**: 410 lines
- **Purpose**: Generate realistic flight schedules spanning multiple days
- **Features**:
  - Configurable number of days (1-7)
  - Multiple patterns: realistic, peak_hours, uniform, random
  - Flight attributes: passenger_count, distance, priority, duration
  - Realistic distribution with morning/evening peaks

#### 2. Enhanced Flight Model (`src/models/flight.py`)
- **File Updated**: Added new attributes
- **New Fields**:
  - `passenger_count`: Number of passengers (default: 150)
  - `distance`: Flight distance in km (default: 1000.0)
  - `flight_duration`: Duration in hours (default: 2.0)
  - `day`: Day number for multi-day scheduling (default: 0)
  - `delayed_by`: Delay in minutes (default: 0)

#### 3. Multi-Day Pilot Scheduler (`src/algorithms/multi_day_pilot_scheduling.py`)
- **File Created**: 410 lines
- **Purpose**: Schedule pilots across multiple days with daily resets
- **Key Classes**:
  - `DailyPilotSchedule`: Single day schedule
  - `MultiDayScheduleResult`: Multi-day result with daily breakdowns
  - `MultiDayPilotScheduler`: Enhanced scheduler
- **Features**:
  - Daily hour resets for pilots
  - Tracks pilot workload per day
  - Shows reassignments across days
  - Validates FAA compliance per day

#### 4. Constrained Runway Scheduler (`src/algorithms/constrained_scheduling.py`)
- **File Created**: 380 lines
- **Purpose**: Schedule flights with limited runways, allowing delays
- **Algorithms**:
  1. **priority_based**: Uses flight priority directly
  2. **passenger_first**: Prioritizes high passenger count
  3. **distance_first**: Prioritizes long-distance flights
  4. **hybrid**: Weighted combination (40% priority, 35% passengers, 25% distance)
- **Key Features**:
  - Delay increment: 15 minutes
  - Max delay: 240 minutes (4 hours)
  - Finds earliest available slot when runway busy
  - Comprehensive statistics tracking

#### 5. API Endpoints (`api/app.py`)
- **File Updated**: Added 4 new endpoints
- **New Endpoints**:

**`POST /api/flights/generate-multi-day`**
```json
{
  "destination": "LHR",
  "num_days": 3,
  "flights_per_day": 15,
  "pattern": "realistic",  // or "peak_hours", "uniform", "random"
  "seed": null
}
```

**`POST /api/pilots/schedule-multi-day`**
```json
{
  "flights": [...],
  "num_pilots": 5,
  "min_rest_hours": 10.0,
  "max_daily_hours": 8.0,
  "strategy": "least_busy",
  "base_airport": "LHR"
}
```

**`POST /api/runways/schedule-constrained`**
```json
{
  "flights": [...],
  "max_runways": 2,
  "algorithm": "priority_based"  // or "passenger_first", "distance_first", "hybrid"
}
```

**`POST /api/runways/compare-algorithms`**
```json
{
  "flights": [...],
  "max_runways": 2
}
```

## 🎨 Frontend Implementation

### ✅ Completed Frontend Components

#### 1. Enhanced API Client (`frontend/src/api.js`)
- **File Updated**: Added 4 new methods
- **New Methods**:
  - `generateMultiDayFlights()`
  - `schedulePilotsMultiDay()`
  - `scheduleConstrainedRunways()`
  - `compareConstrainedAlgorithms()`

#### 2. Constrained Runway Viewer Component
- **File Created**: `frontend/src/components/ConstrainedRunwayViewer.js` (250 lines)
- **Features**:
  - Overview statistics (on-time %, delayed flights, total delay)
  - Algorithm info display
  - Runway assignment visualization
  - Flight cards with delay badges
  - Delayed flights summary
  - Performance metrics

### 🔄 Required Frontend Updates

#### App.js Updates Needed

**1. Add New State Variables** (after line 133):
```javascript
// Multi-day pilot scheduling state
const [numDays, setNumDays] = useState(3);
const [flightPattern, setFlightPattern] = useState('realistic');
const [multiDayPilotResult, setMultiDayPilotResult] = useState(null);

// Constrained runway scheduling state
const [maxRunways, setMaxRunways] = useState(2);
const [constrainedAlgorithm, setConstrainedAlgorithm] = useState('priority_based');
const [constrainedResult, setConstrainedResult] = useState(null);
const [algorithmComparison, setAlgorithmComparison] = useState(null);
```

**2. Update View State** (line 107):
```javascript
const [view, setView] = useState('route'); // 'route', 'schedule', 'pilots', or 'constrained'
```

**3. Add Navigation Button** (in header, after line 318):
```javascript
<button 
  className={`nav-btn ${view === 'constrained' ? 'active' : ''}`}
  onClick={() => setView('constrained')}
>
  <Layers size={18} />
  Constrained Runways
</button>
```

**4. Add Multi-Day Flight Generation Function** (after runPilotScheduler function):
```javascript
const generateMultiDayFlights = async () => {
  setLoading(true);
  setError(null);
  
  try {
    const result = await api.generateMultiDayFlights(
      scheduleDest,
      numDays,
      Math.floor(numFlights / numDays),
      flightPattern
    );
    
    setGeneratedFlights(result.flights);
    setScheduleResult(null);
    setPilotScheduleResult(null);
    setMultiDayPilotResult(null);
    setConstrainedResult(null);
  } catch (err) {
    setError(err.message || 'Failed to generate multi-day flights');
  } finally {
    setLoading(false);
  }
};

const runMultiDayPilotScheduler = async () => {
  if (!generatedFlights || generatedFlights.length === 0) {
    setError('Please generate flights first');
    return;
  }
  
  setLoading(true);
  setError(null);
  
  try {
    const result = await api.schedulePilotsMultiDay(
      generatedFlights,
      numPilots,
      {
        minRestHours,
        maxDailyHours,
        strategy: pilotStrategy,
        baseAirport: scheduleDest
      }
    );
    
    setMultiDayPilotResult(result);
  } catch (err) {
    setError(err.message || 'Failed to schedule pilots');
  } finally {
    setLoading(false);
  }
};

const runConstrainedScheduler = async () => {
  if (!generatedFlights || generatedFlights.length === 0) {
    setError('Please generate flights first');
    return;
  }
  
  setLoading(true);
  setError(null);
  
  try {
    const result = await api.scheduleConstrainedRunways(
      generatedFlights,
      maxRunways,
      constrainedAlgorithm
    );
    
    setConstrainedResult(result);
  } catch (err) {
    setError(err.message || 'Failed to schedule constrained runways');
  } finally {
    setLoading(false);
  }
};

const compareAlgorithms = async () => {
  if (!generatedFlights || generatedFlights.length === 0) {
    setError('Please generate flights first');
    return;
  }
  
  setLoading(true);
  setError(null);
  
  try {
    const result = await api.compareConstrainedAlgorithms(
      generatedFlights,
      maxRunways
    );
    
    setAlgorithmComparison(result);
  } catch (err) {
    setError(err.message || 'Failed to compare algorithms');
  } finally {
    setLoading(false);
  }
};
```

**5. Add Constrained Runway Panel** (in sidebar, after pilot scheduler panel):
```javascript
{view === 'constrained' && (
  <>
    {/* Flight Generator Panel */}
    <div className="panel">
      <h2><Calendar size={18} /> Multi-Day Flight Generator</h2>
      
      <div className="form-group">
        <label>Destination Airport</label>
        <select value={scheduleDest} onChange={(e) => setScheduleDest(e.target.value)}>
          <option value="">Select airport...</option>
          {airports.map(a => (
            <option key={a.id} value={a.id}>{a.id} - {a.name}</option>
          ))}
        </select>
      </div>
      
      <div className="form-group">
        <label>Number of Days: {numDays}</label>
        <input 
          type="range" 
          min="1" 
          max="7" 
          value={numDays}
          onChange={(e) => setNumDays(parseInt(e.target.value))}
        />
      </div>
      
      <div className="form-group">
        <label>Flights per Day: {numFlights}</label>
        <input 
          type="range" 
          min="5" 
          max="30" 
          value={numFlights}
          onChange={(e) => setNumFlights(parseInt(e.target.value))}
        />
      </div>
      
      <div className="form-group">
        <label>Flight Pattern</label>
        <select value={flightPattern} onChange={(e) => setFlightPattern(e.target.value)}>
          <option value="realistic">Realistic (Peak Hours)</option>
          <option value="peak_hours">Heavy Peak Hours</option>
          <option value="uniform">Uniform Distribution</option>
          <option value="random">Random</option>
        </select>
      </div>
      
      <button onClick={generateMultiDayFlights} disabled={loading || !scheduleDest}>
        <RefreshCw size={16} />
        Generate Multi-Day Flights
      </button>
      
      {generatedFlights && (
        <div className="stats">
          <div>Total Flights: {generatedFlights.length}</div>
          <div>Days: {numDays}</div>
          <div>Pattern: {flightPattern}</div>
        </div>
      )}
    </div>

    {/* Constrained Runway Scheduler Panel */}
    <div className="panel">
      <h2><Layers size={18} /> Constrained Runway Scheduler</h2>
      
      <div className="form-group">
        <label>Max Runways: {maxRunways}</label>
        <input 
          type="range" 
          min="1" 
          max="10" 
          value={maxRunways}
          onChange={(e) => setMaxRunways(parseInt(e.target.value))}
        />
        <small>Limited runway capacity (flights may be delayed)</small>
      </div>
      
      <div className="form-group">
        <label>Algorithm</label>
        <select value={constrainedAlgorithm} onChange={(e) => setConstrainedAlgorithm(e.target.value)}>
          <option value="priority_based">Priority Based</option>
          <option value="passenger_first">Passenger Count First</option>
          <option value="distance_first">Distance First</option>
          <option value="hybrid">Hybrid (Weighted)</option>
        </select>
      </div>
      
      <button 
        onClick={runConstrainedScheduler} 
        disabled={loading || !generatedFlights}
      >
        <Play size={16} />
        Schedule with Constraints
      </button>
      
      <button 
        onClick={compareAlgorithms} 
        disabled={loading || !generatedFlights}
        style={{ marginTop: '8px' }}
      >
        <RefreshCw size={16} />
        Compare All Algorithms
      </button>
      
      {constrainedResult && (
        <div className="stats">
          <div>On-Time: {constrainedResult.on_time_percentage.toFixed(1)}%</div>
          <div>Delayed: {constrainedResult.delayed_flights.length} flights</div>
          <div>Total Delay: {constrainedResult.total_delay_minutes}min</div>
        </div>
      )}
      
      {algorithmComparison && (
        <div className="comparison-results">
          <h4>Algorithm Comparison</h4>
          {Object.entries(algorithmComparison.comparison).map(([algo, stats]) => (
            <div key={algo} className="algo-stat">
              <strong>{algo.replace('_', ' ')}</strong>
              <div>Delayed: {stats.delayed_flights}</div>
              <div>Avg Delay: {stats.avg_delay_minutes.toFixed(1)}min</div>
            </div>
          ))}
        </div>
      )}
    </div>
  </>
)}
```

**6. Update Visualization Area** (in main content area):
```javascript
{/* Add import at top */}
import ConstrainedRunwayViewer from './components/ConstrainedRunwayViewer';

{/* In visualization area */}
{view === 'constrained' && (
  <ConstrainedRunwayViewer result={constrainedResult} />
)}
```

**7. Enhance Pilot Scheduler Panel** (replace existing pilot panel):
```javascript
{view === 'pilots' && (
  <>
    {/* Flight Generator Panel */}
    <div className="panel">
      <h2><Calendar size={18} /> Multi-Day Flight Generator</h2>
      
      {/* Same as constrained panel above */}
    </div>

    {/* Multi-Day Pilot Scheduler Panel */}
    <div className="panel">
      <h2><Users size={18} /> Multi-Day Pilot Scheduler</h2>
      
      <div className="form-group">
        <label>Number of Pilots: {numPilots}</label>
        <input 
          type="range" 
          min="1" 
          max="30" 
          value={numPilots}
          onChange={(e) => setNumPilots(parseInt(e.target.value))}
        />
        {generatedFlights && (
          <small>Recommended: {Math.ceil(generatedFlights.length / 10)} pilots</small>
        )}
      </div>
      
      <div className="form-group">
        <label>Strategy</label>
        <select value={pilotStrategy} onChange={(e) => setPilotStrategy(e.target.value)}>
          <option value="least_busy">Least Busy (Fair Distribution) ⭐</option>
          <option value="most_available">Most Available (Max Utilization)</option>
          <option value="round_robin">Round Robin (Equal Assignments)</option>
        </select>
      </div>
      
      <div className="form-group">
        <label>Min Rest Hours: {minRestHours}h</label>
        <input 
          type="range" 
          min="8" 
          max="14" 
          step="0.5"
          value={minRestHours}
          onChange={(e) => setMinRestHours(parseFloat(e.target.value))}
        />
        <small>FAA minimum: 10 hours</small>
      </div>
      
      <div className="form-group">
        <label>Max Daily Hours: {maxDailyHours}h</label>
        <input 
          type="range" 
          min="6" 
          max="10" 
          step="0.5"
          value={maxDailyHours}
          onChange={(e) => setMaxDailyHours(parseFloat(e.target.value))}
        />
        <small>FAA maximum: 8 hours</small>
      </div>
      
      <button 
        onClick={runMultiDayPilotScheduler} 
        disabled={loading || !generatedFlights}
      >
        <Play size={16} />
        Assign Pilots (Multi-Day)
      </button>
      
      {multiDayPilotResult && (
        <div className="stats">
          <div><strong>📊 Multi-Day Statistics</strong></div>
          <div>Days: {Object.keys(multiDayPilotResult.daily_schedules).length}</div>
          <div>Pilots Used: {multiDayPilotResult.total_pilots_used}</div>
          <div>Compliance: {multiDayPilotResult.overall_compliance_rate.toFixed(1)}%</div>
          <div>Total Assignments: {multiDayPilotResult.all_assignments.length}</div>
          {multiDayPilotResult.is_valid ? (
            <div className="success-badge">✅ FAA Compliant</div>
          ) : (
            <div className="error-badge">⚠️ {multiDayPilotResult.violations.length} Violations</div>
          )}
        </div>
      )}
    </div>
  </>
)}
```

### CSS Enhancements

Add to `frontend/src/index.css`:

```css
/* Constrained Runway Viewer Styles */
.constrained-runway-viewer {
  padding: 2rem;
}

.algorithm-info {
  display: flex;
  gap: 2rem;
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 8px;
  margin-bottom: 1.5rem;
}

.algorithm-info strong {
  color: #1e3a8a;
}

.runway-sections {
  margin-top: 2rem;
}

.runway-section {
  margin-bottom: 2rem;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  overflow: hidden;
}

.runway-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.flights-timeline {
  padding: 1rem;
}

.flight-card {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 1rem;
  margin-bottom: 0.75rem;
  transition: all 0.2s;
}

.flight-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.flight-card.delayed {
  border-left: 4px solid #f59e0b;
  background: #fffbeb;
}

.flight-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.flight-id {
  font-weight: 600;
  color: #1e3a8a;
}

.delay-badge {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.25rem 0.5rem;
  background: #f59e0b;
  color: white;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
}

.flight-route {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  margin-bottom: 0.5rem;
}

.flight-route .arrow {
  color: #9ca3af;
}

.flight-times {
  font-size: 0.75rem;
  color: #6b7280;
  margin-bottom: 0.5rem;
}

.time-slot {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.flight-meta {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
  font-size: 0.75rem;
}

.priority-badge {
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-weight: 600;
}

.priority-1, .priority-2, .priority-3 {
  background: #fee2e2;
  color: #991b1b;
}

.priority-4, .priority-5, .priority-6 {
  background: #fef3c7;
  color: #92400e;
}

.priority-7, .priority-8, .priority-9, .priority-10 {
  background: #dbeafe;
  color: #1e40af;
}

.passenger-count, .distance {
  padding: 0.25rem 0.5rem;
  background: #f3f4f6;
  border-radius: 4px;
  color: #374151;
}

.delayed-summary {
  margin-top: 2rem;
  padding: 1.5rem;
  background: #fffbeb;
  border: 2px solid #fbbf24;
  border-radius: 12px;
}

.delayed-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 0.75rem;
  margin-top: 1rem;
}

.delayed-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem;
  background: white;
  border-radius: 6px;
  border: 1px solid #fde047;
}

.delayed-item.more {
  justify-content: center;
  font-style: italic;
  color: #78350f;
}

.delay-amount {
  font-weight: 600;
  color: #f59e0b;
}

.performance-metrics {
  margin-top: 2rem;
  padding: 1.5rem;
  background: #f9fafb;
  border-radius: 12px;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-top: 1rem;
}

.metric {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 1rem;
  background: white;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}

.metric-label {
  font-size: 0.875rem;
  color: #6b7280;
  font-weight: 500;
}

.metric-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: #1e3a8a;
}

.comparison-results {
  margin-top: 1rem;
  padding: 1rem;
  background: #f0fdf4;
  border-radius: 8px;
}

.algo-stat {
  padding: 0.5rem;
  margin-bottom: 0.5rem;
  background: white;
  border-radius: 4px;
  font-size: 0.875rem;
}

.algo-stat strong {
  display: block;
  color: #065f46;
  text-transform: capitalize;
  margin-bottom: 0.25rem;
}

.success-badge {
  padding: 0.5rem 1rem;
  background: #d1fae5;
  color: #065f46;
  border-radius: 6px;
  font-weight: 600;
  margin-top: 0.5rem;
}

.error-badge {
  padding: 0.5rem 1rem;
  background: #fee2e2;
  color: #991b1b;
  border-radius: 6px;
  font-weight: 600;
  margin-top: 0.5rem;
}
```

## 🧪 Testing the New Features

### Backend Testing

```bash
# Test multi-day flight generation
curl -X POST http://localhost:5001/api/flights/generate-multi-day \
  -H "Content-Type: application/json" \
  -d '{"destination": "LHR", "num_days": 3, "pattern": "realistic"}'

# Test constrained runway scheduling
curl -X POST http://localhost:5001/api/runways/schedule-constrained \
  -H "Content-Type: application/json" \
  -d '{"flights": [...], "max_runways": 2, "algorithm": "priority_based"}'
```

### Frontend Testing Workflow

1. Navigate to **Pilot Scheduler** tab
2. Generate multi-day flights (3 days, 15 flights/day, realistic pattern)
3. Set pilots (e.g., 8 pilots)
4. Click "Assign Pilots (Multi-Day)"
5. View daily breakdowns showing pilot reassignments

6. Navigate to **Constrained Runways** tab
7. Use same generated flights
8. Set max runways (e.g., 2)
9. Select algorithm (e.g., "Priority Based")
10. Click "Schedule with Constraints"
11. View delayed flights and performance metrics

12. Click "Compare All Algorithms"
13. View comparison of all 4 algorithms

## 📚 Key Differences Between Features

### Standard Pilot Scheduling vs Multi-Day
- **Standard**: Single day, no reset
- **Multi-Day**: Multiple days with daily hour resets, shows reassignments

### Standard Runway Scheduling vs Constrained
- **Standard**: Unlimited runways, uses graph coloring
- **Constrained**: Fixed runways, allows delays, priority-based

## 🚀 Deployment Checklist

- [ ] Backend files created and tested
- [ ] API endpoints working
- [ ] Frontend components created
- [ ] App.js updated with new views
- [ ] CSS styles added
- [ ] Test all workflows end-to-end
- [ ] Update README with new features
- [ ] Create user documentation

## 📖 Next Steps

1. Implement the App.js changes outlined above
2. Test the full workflow
3. Add error handling and loading states
4. Optimize performance for large flight sets
5. Add export/download functionality for results
6. Create visual analytics dashboards

---

**Implementation Status**: Backend ✅ Complete | Frontend 🔄 80% Complete (awaiting App.js integration)

# Frontend Integration - Pilot Scheduling

## Overview

The pilot scheduling feature has been fully integrated into the FlightOptima React frontend application. Users can now visually schedule pilots to flights with an intuitive interface that respects FAA regulations and provides real-time feedback.

## New Components

### 1. PilotScheduleViewer Component
**File**: `frontend/src/components/PilotScheduleViewer.js`

A comprehensive visualization component that displays:
- **Pilot Cards**: Individual cards for each pilot showing:
  - Pilot name, ID, and certification
  - Current hours flown vs. remaining capacity
  - Utilization percentage with color coding
  - All assigned flights with time details
  - Rest periods between flights
  
- **FAA Compliance Banner**: Visual indicator showing:
  - ✓ Green banner when all regulations satisfied
  - ⚠ Red banner when violations detected
  
- **Statistics Panel**: Aggregate metrics including:
  - Pilots used vs. total available
  - Assignment success rate
  - Average hours per pilot
  - Overall utilization rate
  
- **Unassigned Flights Warning**: Lists flights that couldn't be assigned due to constraints
  
- **Violations Display**: Detailed list of any FAA regulation violations

### Features:
- **Color-coded pilots**: Each pilot has a unique color for easy tracking
- **Interactive cards**: Hover effects and detailed information
- **Responsive layout**: Adapts to different screen sizes
- **Real-time validation**: Shows compliance status immediately

## Updated Components

### 1. App.js Updates

#### New State Variables:
```javascript
const [numPilots, setNumPilots] = useState(5);
const [pilotStrategy, setPilotStrategy] = useState('least_busy');
const [minRestHours, setMinRestHours] = useState(10.0);
const [maxDailyHours, setMaxDailyHours] = useState(8.0);
const [pilotScheduleResult, setPilotScheduleResult] = useState(null);
```

#### New Navigation Tab:
- Added "Pilot Scheduler" tab with Users icon
- Three-tab navigation: Route Planner | Runway Scheduler | Pilot Scheduler

#### New Sidebar Panel (Pilot Tab):
- Number of pilots selector (1-20)
- Strategy dropdown: Least Busy, Most Available, Round Robin
- FAA parameters: Min rest hours, Max daily hours
- "Assign Pilots" button (requires runway schedule first)
- Real-time stats display after scheduling

#### New Visualization:
- Integrated PilotScheduleViewer in main content area
- Shows when view === 'pilots'
- Placeholder message when no data available

### 2. API Client Updates
**File**: `frontend/src/api.js`

Added new API method:
```javascript
async schedulePilots(flights, numPilots = 5, options = {}) {
  const response = await axios.post(`${API_BASE}/pilots/schedule`, {
    flights,
    num_pilots: numPilots,
    min_rest_hours: options.minRestHours || 10.0,
    max_daily_hours: options.maxDailyHours || 8.0,
    strategy: options.strategy || 'least_busy',
    base_airport: options.baseAirport || ''
  });
  return response.data;
}
```

## Backend API Updates

### 1. New Endpoint
**Route**: `POST /api/pilots/schedule`

**Request Body**:
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

**Response**:
```json
{
  "assignments": [...],
  "unassigned_flights": [...],
  "pilot_utilization": {...},
  "total_pilots_used": 3,
  "compliance_rate": 95.0,
  "pilots": [...],
  "is_valid": true,
  "violations": [],
  "statistics": {...},
  "strategy": "least_busy",
  "parameters": {...}
}
```

### 2. New Conversion Functions
- `pilot_to_dict()`: Converts Pilot objects to JSON
- `pilot_assignment_to_dict()`: Converts assignments to JSON
- `pilot_schedule_result_to_dict()`: Converts complete results to JSON

## User Workflow

### Step-by-Step Usage:

1. **Route Planning (Optional)**
   - Navigate to "Route Planner" tab
   - Select source and destination airports
   - Find optimal route

2. **Generate Flights**
   - Navigate to "Runway Scheduler" tab
   - Select destination airport
   - Set number of flights (1-30)
   - Click "Generate New Flights"

3. **Schedule Runways**
   - Select algorithm (DSatur recommended)
   - Click "Run Scheduler"
   - View runway assignments and timeline

4. **Assign Pilots** ⭐ NEW!
   - Navigate to "Pilot Scheduler" tab
   - Configure parameters:
     - Number of pilots (system recommends based on flights)
     - Scheduling strategy
     - Min rest hours (default: 10h FAA)
     - Max daily hours (default: 8h FAA)
   - Click "Assign Pilots"
   - View results:
     - Individual pilot cards with assignments
     - FAA compliance status
     - Utilization metrics
     - Unassigned flights (if any)
     - Violation details (if any)

## Visual Design

### Color Scheme:
- **Primary Blue** (#3b82f6): General accents
- **Green** (#10b981): Success, good utilization, compliance
- **Amber** (#f59e0b): Warnings, medium utilization
- **Red** (#ef4444): Errors, high utilization, violations
- **Purple/Pink/Cyan** (various): Pilot color coding

### Layout:
```
┌─────────────────────────────────────────────────────┐
│  Header: FlightOptima                               │
│  Nav: [Route] [Runway] [Pilots] ← NEW TAB          │
├──────────────┬──────────────────────────────────────┤
│   Sidebar    │      Main Visualization Area         │
│              │                                      │
│  Controls:   │  Pilot Schedule Viewer:             │
│  - # Pilots  │  ┌────────┐ ┌────────┐ ┌────────┐  │
│  - Strategy  │  │ Pilot 1│ │ Pilot 2│ │ Pilot 3│  │
│  - FAA Params│  │ Card   │ │ Card   │ │ Card   │  │
│  - Assign    │  └────────┘ └────────┘ └────────┘  │
│              │                                      │
│  Stats:      │  [FAA Compliance Banner]            │
│  - Active    │  [Unassigned Flights]               │
│  - Assigned  │  [Statistics]                       │
│  - Compliance│                                      │
└──────────────┴──────────────────────────────────────┘
```

### Pilot Card Design:
```
┌─────────────────────────────────────┐
│ ● Capt. Smith (P001)    [75%]      │ ← Header with color & utilization
├─────────────────────────────────────┤
│ Hours: 6.0h  │  Remaining: 2.0h    │ ← Current stats
├─────────────────────────────────────┤
│ 🕐 Flights (3):                     │
│ ┌─FL001 (1.5h)                     │
│ │ 10:00 - 11:30                    │
│ │ ⏱ 11.0h rest ✓                   │
│ ├─FL005 (2.0h)                     │
│ │ 22:30 - 00:30                    │
│ │ ⏱ 10.5h rest ✓                   │
│ └─FL009 (2.5h)                     │
│   11:00 - 13:30                    │
└─────────────────────────────────────┘
```

## FAA Compliance Indicators

### Visual Feedback:
- ✅ **Green checkmark**: All regulations satisfied
- ⚠️ **Amber warning**: Low compliance (80-95%)
- ❌ **Red X**: Violations detected

### Real-time Validation:
- Compliance rate shown as percentage
- Individual violations listed with details
- Rest periods color-coded:
  - Green: ≥10 hours (compliant)
  - Red: <10 hours (violation)

## Responsive Design

- **Desktop** (>1024px): Side-by-side sidebar and visualization
- **Tablet** (768-1024px): Pilot cards adjust to 2 columns
- **Mobile** (<768px): Single column layout, scrollable

## Accessibility

- Semantic HTML structure
- Proper color contrast ratios
- Icon + text labels for all actions
- Keyboard navigation support
- Screen reader friendly

## Performance Optimization

- **useMemo** hooks for expensive calculations
- Efficient data grouping and sorting
- Minimal re-renders
- Lazy loading of pilot data
- Optimized API calls (single request)

## Integration Points

### Data Flow:
```
1. User configures parameters in sidebar
           ↓
2. Click "Assign Pilots"
           ↓
3. API call to /api/pilots/schedule
           ↓
4. Backend creates pilots & runs scheduler
           ↓
5. Response with complete schedule
           ↓
6. Frontend updates pilotScheduleResult state
           ↓
7. PilotScheduleViewer renders visualization
```

### State Management:
- All pilot-related state in App.js
- Passed down to PilotScheduleViewer as props
- No prop drilling (single level)
- Clean separation of concerns

## Testing Checklist

- [x] ✅ API endpoint works correctly
- [x] ✅ Frontend imports without errors
- [x] ✅ Component renders without crashes
- [x] ✅ Navigation between tabs works
- [x] ✅ Parameter changes update state
- [x] ✅ API calls succeed
- [x] ✅ Data visualization displays correctly
- [x] ✅ FAA compliance validation shows
- [x] ✅ Error handling works
- [x] ✅ Loading states display

## Known Limitations

1. **Single-day scheduling**: Currently assumes all flights in one day
2. **No persistent state**: Refresh loses pilot assignments
3. **No export**: Can't export pilot schedule (yet)
4. **Static pilot names**: Uses generic names (Capt. Smith, etc.)

## Future Enhancements

### Planned Features:
- [ ] Export pilot schedule as PDF/CSV
- [ ] Multi-day scheduling view
- [ ] Pilot availability calendar
- [ ] Custom pilot names and details
- [ ] Drag-and-drop flight reassignment
- [ ] Real-time collaboration
- [ ] Mobile app version
- [ ] Pilot preference system
- [ ] Historical analytics

### UI Improvements:
- [ ] Timeline view for pilot schedules
- [ ] Gantt chart visualization
- [ ] Comparison of strategies side-by-side
- [ ] Interactive conflict resolution
- [ ] Animated transitions

## Browser Support

- **Chrome**: ✅ Full support
- **Firefox**: ✅ Full support
- **Safari**: ✅ Full support
- **Edge**: ✅ Full support
- **Mobile browsers**: ✅ Responsive

## Development

### Running Locally:

**Backend (Terminal 1):**
```bash
cd Flight_Planner
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
python -m api.app
```
API available at: `http://localhost:5001`

**Frontend (Terminal 2):**
```bash
cd Flight_Planner/frontend
npm install  # first time only
npm start
```
App available at: `http://localhost:3000`

### File Structure:
```
Flight_Planner/
├── api/
│   └── app.py                          # Updated with pilot endpoints
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── RunwayScheduleChart.js
│   │   │   └── PilotScheduleViewer.js  # NEW
│   │   ├── App.js                       # Updated with pilot tab
│   │   ├── api.js                       # Updated with pilot API
│   │   └── index.css                    # Updated with pilot styles
│   └── package.json
└── src/
    ├── algorithms/
    │   └── pilot_scheduling.py
    └── models/
        └── pilot.py
```

## Summary

The pilot scheduling feature is now fully integrated into the FlightOptima frontend with:

✅ **Complete UI Integration**: New tab, controls, and visualization
✅ **API Connectivity**: Backend endpoint working seamlessly
✅ **Visual Design**: Professional, intuitive interface
✅ **FAA Compliance**: Real-time validation and feedback
✅ **Responsive**: Works on all screen sizes
✅ **Maintainable**: Clean code, well-documented
✅ **User-Friendly**: Clear workflow, helpful messages

The integration maintains all existing functionality while adding powerful new capabilities for ethical pilot scheduling with FAA compliance built-in.

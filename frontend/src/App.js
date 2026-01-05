import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap } from 'react-leaflet';
import L from 'leaflet';
import { 
  Plane, MapPin, Route, Calendar, 
  Play, RefreshCw, ChevronRight, AlertCircle,
  Layers, Timer, Users
} from 'lucide-react';
import api from './api';
import RunwayScheduleChart from './components/RunwayScheduleChart';
import PilotScheduleViewer from './components/PilotScheduleViewer';
import ConstrainedRunwayViewer from './components/ConstrainedRunwayViewer';

// Fix Leaflet marker icons
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
});

// Custom airport icon
const createAirportIcon = (isHighlighted = false, isSource = false, isDest = false) => {
  let color = '#3b82f6';
  if (isSource) color = '#10b981';
  if (isDest) color = '#ef4444';
  if (isHighlighted) color = '#f59e0b';
  
  return L.divIcon({
    className: 'custom-marker',
    html: `<div style="
      width: ${isHighlighted ? '20px' : '14px'};
      height: ${isHighlighted ? '20px' : '14px'};
      background: ${color};
      border: 2px solid white;
      border-radius: 50%;
      box-shadow: 0 2px 8px rgba(0,0,0,0.3);
    "></div>`,
    iconSize: [isHighlighted ? 20 : 14, isHighlighted ? 20 : 14],
    iconAnchor: [isHighlighted ? 10 : 7, isHighlighted ? 10 : 7],
  });
};

// Map bounds adjuster component
function MapBounds({ bounds }) {
  const map = useMap();
  
  useEffect(() => {
    if (bounds && bounds.length > 0) {
      try {
        map.fitBounds(bounds, { padding: [50, 50] });
      } catch (e) {
        console.warn('Could not fit bounds:', e);
      }
    }
  }, [bounds, map]);
  
  return null;
}

// Split a path into segments that don't cross the antimeridian
// This ensures each segment stays within -180 to 180 longitude
function splitPathAtAntimeridian(coordinates) {
  if (!coordinates || coordinates.length < 2) return [coordinates || []];
  
  const segments = [];
  let currentSegment = [[coordinates[0][0], coordinates[0][1]]];
  
  for (let i = 1; i < coordinates.length; i++) {
    const [lat1, lng1] = currentSegment[currentSegment.length - 1];
    const [lat2, lng2] = coordinates[i];
    
    // Check if this segment crosses the antimeridian (large longitude jump)
    const lngDiff = lng2 - lng1;
    
    if (Math.abs(lngDiff) > 180) {
      // Crossing the antimeridian - need to split
      // Calculate the crossing point
      const crossingLat = lat1 + (lat2 - lat1) * Math.abs((lng1 > 0 ? 180 - lng1 : -180 - lng1) / (lngDiff > 0 ? lngDiff - 360 : lngDiff + 360));
      
      // End current segment at the antimeridian
      if (lng1 > 0) {
        // Going from east to west (positive to negative)
        currentSegment.push([crossingLat, 180]);
        segments.push(currentSegment);
        currentSegment = [[ crossingLat, -180], [lat2, lng2]];
      } else {
        // Going from west to east (negative to positive)
        currentSegment.push([crossingLat, -180]);
        segments.push(currentSegment);
        currentSegment = [[crossingLat, 180], [lat2, lng2]];
      }
    } else {
      // Normal segment, just add the point
      currentSegment.push([lat2, lng2]);
    }
  }
  
  // Don't forget the last segment
  if (currentSegment.length > 0) {
    segments.push(currentSegment);
  }
  
  return segments.filter(seg => seg.length >= 2);
}

function App() {
  const [view, setView] = useState('route'); // 'route', 'schedule', 'pilots', or 'constrained'
  const [airports, setAirports] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // Route planner state
  const [source, setSource] = useState('JFK');
  const [destination, setDestination] = useState('LHR');
  const [cruisingSpeed, setCruisingSpeed] = useState(850);
  const [routeResult, setRouteResult] = useState(null);
  
  // Scheduler state
  const [numFlights, setNumFlights] = useState(12);
  const [algorithm, setAlgorithm] = useState('dsatur');
  const [scheduleResult, setScheduleResult] = useState(null);
  const [scheduleDest, setScheduleDest] = useState('LHR');
  const [generatedFlights, setGeneratedFlights] = useState(null); // Store generated flights
  
  // Pilot scheduler state
  const [numPilots, setNumPilots] = useState(5);
  const [pilotStrategy, setPilotStrategy] = useState('least_busy');
  const [minRestHours, setMinRestHours] = useState(10.0);
  const [maxDailyHours, setMaxDailyHours] = useState(8.0);
  const [pilotScheduleResult, setPilotScheduleResult] = useState(null);
  
  // Multi-day pilot scheduling state
  const [numDays, setNumDays] = useState(3);
  const [flightPattern, setFlightPattern] = useState('realistic');
  const [multiDayPilotResult, setMultiDayPilotResult] = useState(null);
  
  // Constrained runway scheduling state
  const [maxRunways, setMaxRunways] = useState(2);
  const [constrainedAlgorithm, setConstrainedAlgorithm] = useState('priority_based');
  const [constrainedResult, setConstrainedResult] = useState(null);
  const [algorithmComparison, setAlgorithmComparison] = useState(null);
  
  // Load airports on mount
  useEffect(() => {
    loadAirports();
  }, []);
  
  const loadAirports = async () => {
    try {
      const data = await api.getAirports();
      setAirports(data.airports);
    } catch (err) {
      setError('Failed to load airports');
      console.error(err);
    }
  };
  
  // Routes can be loaded on demand if needed
  // const loadRoutes = async () => { ... };
  
  const findRoute = async () => {
    if (!source || !destination) {
      setError('Please select source and destination');
      return;
    }
    
    setLoading(true);
    setError(null);
    
    try {
      const result = await api.findRoute(source, destination, cruisingSpeed);
      if (result.success) {
        setRouteResult(result.route);
      } else {
        setError(result.error || 'No route found');
      }
    } catch (err) {
      setError(err.message || 'Failed to find route');
    } finally {
      setLoading(false);
    }
  };
  
  const runScheduler = async () => {
    // If no flights generated yet, generate them first
    if (!generatedFlights || generatedFlights.length === 0) {
      await generateFlights();
      return;
    }
    
    // Schedule the existing flights with the selected algorithm
    setLoading(true);
    setError(null);
    
    try {
      const result = await api.scheduleFlights(generatedFlights, algorithm);
      setScheduleResult(result);
    } catch (err) {
      setError(err.message || 'Failed to run scheduler');
    } finally {
      setLoading(false);
    }
  };
  
  const generateFlightsForRunway = async () => {
    // Use the same multi-day flight generator
    await generateMultiDayFlights();
  };
  
  const runPilotScheduler = async () => {
    if (!scheduleResult || !scheduleResult.flights || scheduleResult.flights.length === 0) {
      setError('Please run runway scheduler first');
      return;
    }
    
    setLoading(true);
    setError(null);
    
    try {
      const result = await api.schedulePilots(
        scheduleResult.flights,
        numPilots,
        {
          minRestHours,
          maxDailyHours,
          strategy: pilotStrategy,
          baseAirport: scheduleDest
        }
      );
      setPilotScheduleResult(result);
    } catch (err) {
      setError(err.message || 'Failed to run pilot scheduler');
    } finally {
      setLoading(false);
    }
  };

  const generateMultiDayFlights = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await api.generateMultiDayFlights(
        scheduleDest,
        numDays,
        numFlights, // numFlights is already "flights per day"
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
  
  const runFullDemo = async () => {
    if (!source || !destination) {
      setError('Please select source and destination');
      return;
    }
    
    setLoading(true);
    setError(null);
    
    try {
      const result = await api.routeWithScheduling(source, destination, numFlights);
      setRouteResult(result.route);
      setScheduleResult(result.schedule);
      setScheduleDest(destination);
      setView('schedule');
    } catch (err) {
      setError(err.message || 'Failed to run demo');
    } finally {
      setLoading(false);
    }
  };
  
  // Get path segments for route visualization (handles antimeridian crossing)
  const getPathSegments = () => {
    if (!routeResult || !routeResult.path || routeResult.path.length === 0) return [];
    
    const rawCoords = routeResult.path.map(airport => [airport.latitude, airport.longitude]);
    return splitPathAtAntimeridian(rawCoords);
  };
  
  // Get map bounds from route or all airports
  const getMapBounds = () => {
    if (routeResult && routeResult.path && routeResult.path.length > 0) {
      return routeResult.path.map(a => [a.latitude, a.longitude]);
    }
    if (airports.length > 0) {
      return airports.map(a => [a.latitude, a.longitude]);
    }
    return [[40, -74], [51, 0]]; // Default: JFK to London area
  };
  
  const formatDuration = (minutes) => {
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return `${hours}h ${mins}m`;
  };
  
  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <h1>
          <Plane size={28} />
          Flight<span>Optima</span>
        </h1>
        <nav className="nav">
          <button 
            className={`nav-btn ${view === 'route' ? 'active' : ''}`}
            onClick={() => setView('route')}
          >
            <Route size={18} />
            Route Planner
          </button>
          <button 
            className={`nav-btn ${view === 'schedule' ? 'active' : ''}`}
            onClick={() => setView('schedule')}
          >
            <Calendar size={18} />
            Runway Scheduler
          </button>
          <button 
            className={`nav-btn ${view === 'pilots' ? 'active' : ''}`}
            onClick={() => setView('pilots')}
          >
            <Users size={18} />
            Pilot Scheduler
          </button>
          <button 
            className={`nav-btn ${view === 'constrained' ? 'active' : ''}`}
            onClick={() => setView('constrained')}
          >
            <Layers size={18} />
            Constrained Runways
          </button>
        </nav>
      </header>
      
      {/* Main Content */}
      <main className="main-content">
        {/* Sidebar */}
        <aside className="sidebar">
          {view === 'route' ? (
            <>
              {/* Route Planner Panel */}
              <div className="panel">
                <h2><MapPin size={18} /> Route Planner</h2>
                
                <div className="form-group">
                  <label>Source Airport</label>
                  <select value={source} onChange={(e) => setSource(e.target.value)}>
                    <option value="">Select airport...</option>
                    {airports.map(a => (
                      <option key={a.id} value={a.id}>{a.id} - {a.name}</option>
                    ))}
                  </select>
                </div>
                
                <div className="form-group">
                  <label>Destination Airport</label>
                  <select value={destination} onChange={(e) => setDestination(e.target.value)}>
                    <option value="">Select airport...</option>
                    {airports.map(a => (
                      <option key={a.id} value={a.id}>{a.id} - {a.name}</option>
                    ))}
                  </select>
                </div>
                
                <div className="form-group">
                  <label>Cruising Speed (km/h)</label>
                  <input 
                    type="number" 
                    value={cruisingSpeed}
                    onChange={(e) => setCruisingSpeed(Number(e.target.value))}
                    min="400"
                    max="1200"
                  />
                </div>
                
                <button 
                  className="btn btn-primary" 
                  onClick={findRoute}
                  disabled={loading}
                >
                  {loading ? <RefreshCw size={18} className="spin" /> : <Route size={18} />}
                  Find Shortest Route
                </button>
              </div>
              
              {/* Full Demo Panel */}
              <div className="panel">
                <h2><Play size={18} /> Full Demo</h2>
                <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem', marginBottom: '1rem' }}>
                  Find route and simulate runway scheduling at destination
                </p>
                
                <div className="form-group">
                  <label>Other Flights at Destination</label>
                  <input 
                    type="number" 
                    value={numFlights}
                    onChange={(e) => setNumFlights(Number(e.target.value))}
                    min="1"
                    max="30"
                  />
                </div>
                
                <button 
                  className="btn btn-secondary" 
                  onClick={runFullDemo}
                  disabled={loading}
                >
                  {loading ? <RefreshCw size={18} className="spin" /> : <Play size={18} />}
                  Run Full Demo
                </button>
              </div>
              
              {/* Route Result */}
              {routeResult && (
                <div className="panel">
                  <h2><ChevronRight size={18} /> Route Result</h2>
                  
                  <div className="stats-grid">
                    <div className="stat-card">
                      <div className="value">{Math.round(routeResult.total_distance)}</div>
                      <div className="label">km</div>
                    </div>
                    <div className="stat-card">
                      <div className="value">{formatDuration(routeResult.flight_time_minutes)}</div>
                      <div className="label">Flight Time</div>
                    </div>
                  </div>
                  
                  <div style={{ marginTop: '1rem' }}>
                    <strong>Route:</strong>
                    <div style={{ color: 'var(--text-muted)', marginTop: '0.5rem' }}>
                      {routeResult.path.map((a, i) => (
                        <span key={a.id}>
                          {a.id}
                          {i < routeResult.path.length - 1 && ' → '}
                        </span>
                      ))}
                    </div>
                  </div>
                  
                  {routeResult.segments.length > 1 && (
                    <div style={{ marginTop: '1rem' }}>
                      <strong>Segments:</strong>
                      {routeResult.segments.map((seg, i) => (
                        <div key={i} style={{ 
                          display: 'flex', 
                          justifyContent: 'space-between',
                          padding: '0.5rem 0',
                          borderBottom: '1px solid var(--surface)',
                          color: 'var(--text-muted)',
                          fontSize: '0.875rem'
                        }}>
                          <span>{seg.from.id} → {seg.to.id}</span>
                          <span>{Math.round(seg.distance)} km</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </>
          ) : view === 'schedule' ? (
            <>
              {/* Multi-Day Flight Generator Panel */}
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
                  <label>Flights per Day: ~{numFlights}</label>
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
                
                <button 
                  className="btn btn-primary"
                  onClick={generateMultiDayFlights} 
                  disabled={loading || !scheduleDest}
                >
                  {loading ? <RefreshCw size={18} className="spin" /> : <RefreshCw size={18} />}
                  Generate Multi-Day Flights
                </button>
                
                {generatedFlights && (
                  <div className="stats-grid" style={{ marginTop: '1rem' }}>
                    <div className="stat-card">
                      <div className="value">{generatedFlights.length}</div>
                      <div className="label">Total Flights</div>
                    </div>
                    <div className="stat-card">
                      <div className="value">{numDays}</div>
                      <div className="label">Days</div>
                    </div>
                  </div>
                )}
              </div>
              
              {/* Runway Scheduler Panel */}
              <div className="panel">
                <h2><Layers size={18} /> Runway Scheduler</h2>
                
                <div className="form-group">
                  <label>Algorithm</label>
                  <select value={algorithm} onChange={(e) => setAlgorithm(e.target.value)}>
                    <option value="dsatur">DSatur (Recommended)</option>
                    <option value="welsh_powell">Welsh-Powell</option>
                    <option value="greedy">Greedy</option>
                  </select>
                </div>
                
                <button 
                  className="btn btn-primary" 
                  onClick={runScheduler}
                  disabled={loading || !generatedFlights}
                >
                  {loading ? <RefreshCw size={18} className="spin" /> : <Timer size={18} />}
                  {generatedFlights ? 'Schedule Runways' : 'Generate Flights First'}
                </button>
                
                {generatedFlights && (
                  <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.5rem' }}>
                    💡 Change algorithm and re-run to compare results
                  </p>
                )}
              </div>
              
              {/* Schedule Stats */}
              {scheduleResult && (
                <div className="panel">
                  <h2><AlertCircle size={18} /> Schedule Stats</h2>
                  
                  <div style={{ 
                    marginBottom: '1rem', 
                    padding: '0.5rem 0.75rem', 
                    background: 'var(--surface)', 
                    borderRadius: '6px',
                    fontSize: '0.85rem'
                  }}>
                    <strong>Algorithm:</strong> {scheduleResult.algorithm || algorithm}
                  </div>
                  
                  <div className="stats-grid">
                    <div className="stat-card">
                      <div className="value">{scheduleResult.num_runways}</div>
                      <div className="label">Runways</div>
                    </div>
                    <div className="stat-card">
                      <div className="value">{scheduleResult.flights.length}</div>
                      <div className="label">Flights</div>
                    </div>
                    <div className="stat-card">
                      <div className="value">{scheduleResult.conflicts_resolved}</div>
                      <div className="label">Conflicts</div>
                    </div>
                  </div>
                  
                  <div style={{ marginTop: '1rem' }}>
                    <span style={{ 
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '0.5rem',
                      padding: '0.5rem 1rem',
                      background: scheduleResult.is_valid ? 'rgba(16, 185, 129, 0.2)' : 'rgba(239, 68, 68, 0.2)',
                      color: scheduleResult.is_valid ? 'var(--secondary)' : 'var(--danger)',
                      borderRadius: '8px',
                      fontSize: '0.875rem',
                      fontWeight: '500'
                    }}>
                      {scheduleResult.is_valid ? '✓ Valid Schedule' : '✗ Invalid Schedule'}
                    </span>
                  </div>
                </div>
              )}
            </>
          ) : view === 'pilots' ? (
            <>
              {/* Multi-Day Flight Generator Panel */}
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
                  <label>Flights per Day: ~{numFlights}</label>
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
                
                <button 
                  className="btn btn-primary"
                  onClick={generateMultiDayFlights} 
                  disabled={loading || !scheduleDest}
                >
                  {loading ? <RefreshCw size={18} className="spin" /> : <RefreshCw size={18} />}
                  Generate Multi-Day Flights
                </button>
                
                {generatedFlights && (
                  <div className="stats-grid" style={{ marginTop: '1rem' }}>
                    <div className="stat-card">
                      <div className="value">{generatedFlights.length}</div>
                      <div className="label">Total Flights</div>
                    </div>
                    <div className="stat-card">
                      <div className="value">{numDays}</div>
                      <div className="label">Days</div>
                    </div>
                  </div>
                )}
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
                    onChange={(e) => setNumPilots(Number(e.target.value))}
                  />
                  {generatedFlights && (
                    <small style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>
                      Recommended: {Math.ceil(generatedFlights.length / 10)} pilots
                    </small>
                  )}
                </div>
                
                <div className="form-group">
                  <label>Scheduling Strategy</label>
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
                  <small style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>
                    FAA minimum: 10 hours
                  </small>
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
                  <small style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>
                    FAA maximum: 8 hours
                  </small>
                </div>
                
                <button 
                  className="btn btn-primary" 
                  onClick={runMultiDayPilotScheduler} 
                  disabled={loading || !generatedFlights}
                >
                  {loading ? <RefreshCw size={18} className="spin" /> : <Play size={18} />}
                  {generatedFlights ? 'Assign Pilots (Multi-Day)' : 'Generate Flights First'}
                </button>
                
                {!generatedFlights && (
                  <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.5rem' }}>
                    💡 Generate multi-day flights first
                  </p>
                )}
              </div>
              
              {/* Multi-Day Pilot Stats */}
              {multiDayPilotResult && (
                <div className="panel">
                  <h2><AlertCircle size={18} /> Multi-Day Stats</h2>
                  
                  <div className="stats-grid">
                    <div className="stat-card">
                      <div className="value">{Object.keys(multiDayPilotResult.daily_schedules).length}</div>
                      <div className="label">Days</div>
                    </div>
                    <div className="stat-card">
                      <div className="value" style={{ color: '#10b981' }}>
                        {multiDayPilotResult.total_pilots_used}
                      </div>
                      <div className="label">Pilots Used</div>
                    </div>
                    <div className="stat-card">
                      <div className="value">{multiDayPilotResult.all_assignments.length}</div>
                      <div className="label">Assignments</div>
                    </div>
                    <div className="stat-card">
                      <div className="value" style={{ color: '#10b981' }}>
                        {multiDayPilotResult.overall_compliance_rate.toFixed(1)}%
                      </div>
                      <div className="label">Compliance</div>
                    </div>
                  </div>
                  
                  <div style={{ marginTop: '1rem' }}>
                    <span style={{ 
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '0.5rem',
                      padding: '0.5rem 1rem',
                      background: multiDayPilotResult.is_valid ? 'rgba(16, 185, 129, 0.2)' : 'rgba(239, 68, 68, 0.2)',
                      color: multiDayPilotResult.is_valid ? 'var(--secondary)' : 'var(--danger)',
                      borderRadius: '8px',
                      fontSize: '0.875rem',
                      fontWeight: '500'
                    }}>
                      {multiDayPilotResult.is_valid ? '✅ FAA Compliant' : `⚠️ ${multiDayPilotResult.violations.length} Violations`}
                    </span>
                  </div>
                </div>
              )}
            </>
          ) : view === 'constrained' ? (
            <>
              {/* Multi-Day Flight Generator Panel */}
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
                  <label>Flights per Day: ~{numFlights}</label>
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
                
                <button 
                  className="btn btn-primary"
                  onClick={generateMultiDayFlights} 
                  disabled={loading || !scheduleDest}
                >
                  {loading ? <RefreshCw size={18} className="spin" /> : <RefreshCw size={18} />}
                  Generate Multi-Day Flights
                </button>
                
                {generatedFlights && (
                  <div className="stats-grid" style={{ marginTop: '1rem' }}>
                    <div className="stat-card">
                      <div className="value">{generatedFlights.length}</div>
                      <div className="label">Total Flights</div>
                    </div>
                    <div className="stat-card">
                      <div className="value">{numDays}</div>
                      <div className="label">Days</div>
                    </div>
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
                  <small style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>
                    Limited runway capacity (flights may be delayed)
                  </small>
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
                  className="btn btn-primary"
                  onClick={runConstrainedScheduler} 
                  disabled={loading || !generatedFlights}
                >
                  {loading ? <RefreshCw size={18} className="spin" /> : <Play size={18} />}
                  Schedule with Constraints
                </button>
                
                <button 
                  className="btn"
                  onClick={compareAlgorithms} 
                  disabled={loading || !generatedFlights}
                  style={{ marginTop: '8px' }}
                >
                  <RefreshCw size={16} />
                  Compare All Algorithms
                </button>
              </div>
              
              {/* Constrained Stats */}
              {constrainedResult && (
                <div className="panel">
                  <h2><AlertCircle size={18} /> Constraint Stats</h2>
                  
                  <div className="stats-grid">
                    <div className="stat-card">
                      <div className="value" style={{ color: '#10b981' }}>
                        {constrainedResult.on_time_percentage.toFixed(1)}%
                      </div>
                      <div className="label">On-Time</div>
                    </div>
                    <div className="stat-card">
                      <div className="value" style={{ color: '#f59e0b' }}>
                        {constrainedResult.delayed_flights.length}
                      </div>
                      <div className="label">Delayed</div>
                    </div>
                    <div className="stat-card">
                      <div className="value">{constrainedResult.total_delay_minutes}</div>
                      <div className="label">Total Delay (min)</div>
                    </div>
                  </div>
                </div>
              )}
              
              {/* Algorithm Comparison */}
              {algorithmComparison && (
                <div className="panel">
                  <h2>🔄 Algorithm Comparison</h2>
                  {Object.entries(algorithmComparison.comparison).map(([algo, stats]) => (
                    <div key={algo} style={{
                      padding: '0.75rem',
                      marginBottom: '0.5rem',
                      background: 'var(--surface)',
                      borderRadius: '6px',
                      fontSize: '0.85rem'
                    }}>
                      <strong style={{ display: 'block', marginBottom: '0.25rem', textTransform: 'capitalize' }}>
                        {algo.replace('_', ' ')}
                      </strong>
                      <div>Delayed: {stats.delayed_flights} flights</div>
                      <div>Avg Delay: {stats.avg_delay_minutes.toFixed(1)}min</div>
                      <div>On-Time: {stats.on_time_percentage.toFixed(1)}%</div>
                    </div>
                  ))}
                </div>
              )}
            </>
          ) : null}
          
          {/* Error display */}
          {error && (
            <div className="error">
              <AlertCircle size={18} style={{ marginRight: '0.5rem' }} />
              {error}
            </div>
          )}
        </aside>
        
        {/* Main visualization area */}
        {view === 'route' ? (
          <div className="map-container">
            <MapContainer
              center={[20, 0]}
              zoom={2}
              style={{ height: '100%', width: '100%' }}
            >
              <TileLayer
                attribution='&copy; <a href="https://carto.com/">CARTO</a>'
                url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
              />
              
              <MapBounds bounds={getMapBounds()} />
              
              {/* All airports */}
              {airports.map(airport => {
                const isSource = routeResult && airport.id === routeResult.source.id;
                const isDest = routeResult && airport.id === routeResult.destination.id;
                const isInPath = routeResult && routeResult.path.some(a => a.id === airport.id);
                
                return (
                  <Marker
                    key={airport.id}
                    position={[airport.latitude, airport.longitude]}
                    icon={createAirportIcon(isInPath, isSource, isDest)}
                  >
                    <Popup>
                      <div style={{ color: '#1e293b' }}>
                        <strong>{airport.id}</strong><br />
                        {airport.name}<br />
                        <small>
                          {airport.latitude.toFixed(4)}, {airport.longitude.toFixed(4)}
                        </small>
                      </div>
                    </Popup>
                  </Marker>
                );
              })}
              
              {/* Route path - rendered as multiple segments to handle antimeridian */}
              {routeResult && getPathSegments().map((segment, idx) => (
                <Polyline
                  key={`route-segment-${idx}`}
                  positions={segment}
                  color="#3b82f6"
                  weight={3}
                  opacity={0.8}
                  dashArray="10, 10"
                />
              ))}
            </MapContainer>
            
            {/* Route info overlay */}
            {routeResult && (
              <div className="route-info">
                <h3>✈️ Flight Route</h3>
                <div className="stat">
                  <span className="stat-label">From</span>
                  <span className="stat-value">{routeResult.source.id}</span>
                </div>
                <div className="stat">
                  <span className="stat-label">To</span>
                  <span className="stat-value">{routeResult.destination.id}</span>
                </div>
                <div className="stat">
                  <span className="stat-label">Distance</span>
                  <span className="stat-value">{Math.round(routeResult.total_distance)} km</span>
                </div>
                <div className="stat">
                  <span className="stat-label">Flight Time</span>
                  <span className="stat-value">{formatDuration(routeResult.flight_time_minutes)}</span>
                </div>
                <div className="stat">
                  <span className="stat-label">Stops</span>
                  <span className="stat-value">{routeResult.path.length - 2}</span>
                </div>
              </div>
            )}
          </div>
        ) : view === 'schedule' ? (
          <div className="schedule-container">
            {scheduleResult ? (
              <RunwayScheduleChart scheduleResult={scheduleResult} />
            ) : (
              <div className="loading">
                <p>Generate flights to see runway scheduling visualization</p>
              </div>
            )}
          </div>
        ) : view === 'pilots' ? (
          <div className="schedule-container">
            {multiDayPilotResult ? (
              <PilotScheduleViewer pilotScheduleResult={multiDayPilotResult} isMultiDay={true} />
            ) : (
              <div className="loading">
                <p>Generate multi-day flights and run pilot scheduler to see assignments</p>
              </div>
            )}
          </div>
        ) : view === 'constrained' ? (
          <div className="schedule-container">
            {constrainedResult ? (
              <ConstrainedRunwayViewer result={constrainedResult} />
            ) : (
              <div className="loading">
                <p>Generate flights and run constrained scheduler to see results</p>
              </div>
            )}
          </div>
        ) : (
          <div className="schedule-container">
            {pilotScheduleResult ? (
              <PilotScheduleViewer pilotScheduleResult={pilotScheduleResult} />
            ) : (
              <div className="loading">
                <p>Run runway scheduler first, then assign pilots to flights</p>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}

export default App;

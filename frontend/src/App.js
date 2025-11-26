import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap } from 'react-leaflet';
import L from 'leaflet';
import { 
  Plane, MapPin, Route, Calendar, 
  Play, RefreshCw, ChevronRight, AlertCircle,
  Layers, Timer
} from 'lucide-react';
import api from './api';
import RunwayScheduleChart from './components/RunwayScheduleChart';

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
  const [view, setView] = useState('route'); // 'route' or 'schedule'
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
  
  const generateFlights = async () => {
    setLoading(true);
    setError(null);
    setScheduleResult(null); // Clear previous results
    
    try {
      const result = await api.generateFlights(scheduleDest, numFlights);
      setGeneratedFlights(result.flights);
      
      // Automatically schedule after generating
      const scheduleResultData = await api.scheduleFlights(result.flights, algorithm);
      setScheduleResult(scheduleResultData);
    } catch (err) {
      setError(err.message || 'Failed to generate flights');
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
          ) : (
            <>
              {/* Scheduler Panel */}
              <div className="panel">
                <h2><Layers size={18} /> Runway Scheduler</h2>
                
                <div className="form-group">
                  <label>Destination Airport</label>
                  <select value={scheduleDest} onChange={(e) => { setScheduleDest(e.target.value); setGeneratedFlights(null); setScheduleResult(null); }}>
                    {airports.map(a => (
                      <option key={a.id} value={a.id}>{a.id} - {a.name}</option>
                    ))}
                  </select>
                </div>
                
                <div className="form-group">
                  <label>Number of Flights</label>
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
                  onClick={generateFlights}
                  disabled={loading}
                  style={{ marginBottom: '0.5rem' }}
                >
                  {loading ? <RefreshCw size={18} className="spin" /> : <RefreshCw size={18} />}
                  Generate New Flights
                </button>
                
                {generatedFlights && (
                  <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', margin: '0.5rem 0' }}>
                    ✓ {generatedFlights.length} flights generated for {scheduleDest}
                  </p>
                )}
                
                <div className="form-group" style={{ marginTop: '1rem' }}>
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
                  {generatedFlights ? 'Run Scheduler' : 'Generate Flights First'}
                </button>
                
                {generatedFlights && (
                  <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.5rem' }}>
                    💡 Change algorithm and click "Run Scheduler" to compare results with same flights
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
          )}
          
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
        ) : (
          <div className="schedule-container">
            {scheduleResult ? (
              <RunwayScheduleChart scheduleResult={scheduleResult} />
            ) : (
              <div className="loading">
                <p>Generate flights to see runway scheduling visualization</p>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}

export default App;

import React, { useMemo } from 'react';

// Runway colors - distinct colors for each runway
const RUNWAY_COLORS = [
  '#3b82f6', // Blue
  '#10b981', // Green
  '#f59e0b', // Amber
  '#ef4444', // Red
  '#8b5cf6', // Purple
  '#ec4899', // Pink
  '#06b6d4', // Cyan
  '#84cc16', // Lime
  '#f97316', // Orange
  '#6366f1', // Indigo
];

function RunwayScheduleChart({ scheduleResult }) {
  // Calculate time bounds for the timeline
  const { flightsByRunway, timeLabels } = useMemo(() => {
    if (!scheduleResult || !scheduleResult.flights.length) {
      return { timeRange: { min: 0, max: 60 }, flightsByRunway: {}, timeLabels: [] };
    }
    
    const flights = scheduleResult.flights;
    
    // Find min and max times
    const times = flights.flatMap(f => [
      new Date(f.arrival_start).getTime(),
      new Date(f.arrival_end).getTime()
    ]);
    
    const minTime = Math.min(...times);
    const maxTime = Math.max(...times);
    
    // Add padding (5 minutes on each side)
    const paddedMin = minTime - 5 * 60 * 1000;
    const paddedMax = maxTime + 5 * 60 * 1000;
    const totalDuration = paddedMax - paddedMin;
    
    // Group flights by runway
    const byRunway = {};
    flights.forEach(flight => {
      const runway = flight.runway_id;
      if (!byRunway[runway]) {
        byRunway[runway] = [];
      }
      byRunway[runway].push({
        ...flight,
        startOffset: ((new Date(flight.arrival_start).getTime() - paddedMin) / totalDuration) * 100,
        width: ((new Date(flight.arrival_end).getTime() - new Date(flight.arrival_start).getTime()) / totalDuration) * 100
      });
    });
    
    // Generate time labels (every 10 minutes)
    const labels = [];
    const interval = 10 * 60 * 1000; // 10 minutes
    let current = Math.ceil(paddedMin / interval) * interval;
    
    while (current <= paddedMax) {
      const date = new Date(current);
      labels.push({
        time: date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false }),
        offset: ((current - paddedMin) / totalDuration) * 100
      });
      current += interval;
    }
    
    return {
      timeRange: { min: paddedMin, max: paddedMax, duration: totalDuration },
      flightsByRunway: byRunway,
      timeLabels: labels
    };
  }, [scheduleResult]);
  
  if (!scheduleResult) {
    return <div className="loading">No schedule data available</div>;
  }
  
  const runwayIds = Object.keys(flightsByRunway).map(Number).sort((a, b) => a - b);
  
  const formatTime = (isoString) => {
    return new Date(isoString).toLocaleTimeString('en-US', { 
      hour: '2-digit', 
      minute: '2-digit',
      hour12: false 
    });
  };
  
  return (
    <div>
      {/* Header stats */}
      <div className="runway-chart">
        <h3>📊 Schedule Overview</h3>
        <div className="stats-grid">
          <div className="stat-card">
            <div className="value" style={{ color: '#10b981' }}>{scheduleResult.num_runways}</div>
            <div className="label">Runways Needed</div>
          </div>
          <div className="stat-card">
            <div className="value">{scheduleResult.flights.length}</div>
            <div className="label">Total Flights</div>
          </div>
          <div className="stat-card">
            <div className="value" style={{ color: '#f59e0b' }}>{scheduleResult.conflicts_resolved}</div>
            <div className="label">Conflicts Resolved</div>
          </div>
          <div className="stat-card">
            <div className="value" style={{ color: scheduleResult.is_valid ? '#10b981' : '#ef4444' }}>
              {scheduleResult.is_valid ? '✓' : '✗'}
            </div>
            <div className="label">Valid</div>
          </div>
        </div>
      </div>
      
      {/* Timeline visualization */}
      <div className="runway-chart">
        <h3>🛬 Runway Timeline</h3>
        
        {/* Time axis */}
        <div className="timeline">
          <div className="time-axis" style={{ position: 'relative', height: '30px' }}>
            {timeLabels.map((label, i) => (
              <span 
                key={i} 
                className="time-label"
                style={{
                  position: 'absolute',
                  left: `${label.offset}%`,
                  transform: 'translateX(-50%)'
                }}
              >
                {label.time}
              </span>
            ))}
          </div>
          
          {/* Runway rows */}
          {runwayIds.map(runwayId => (
            <div key={runwayId} className="runway-row">
              <div 
                className="runway-label"
                style={{ color: RUNWAY_COLORS[(runwayId - 1) % RUNWAY_COLORS.length] }}
              >
                Runway {runwayId}
              </div>
              <div className="runway-timeline">
                {/* Time grid lines */}
                {timeLabels.map((label, i) => (
                  <div
                    key={i}
                    style={{
                      position: 'absolute',
                      left: `${label.offset}%`,
                      top: 0,
                      bottom: 0,
                      width: '1px',
                      background: 'rgba(255,255,255,0.1)'
                    }}
                  />
                ))}
                
                {/* Flight blocks */}
                {flightsByRunway[runwayId]?.map(flight => (
                  <div
                    key={flight.flight_id}
                    className={`flight-block ${flight.flight_id === 'YOUR_FLIGHT' ? 'your-flight' : ''}`}
                    style={{
                      left: `${flight.startOffset}%`,
                      width: `${Math.max(flight.width, 3)}%`,
                      background: RUNWAY_COLORS[(runwayId - 1) % RUNWAY_COLORS.length],
                    }}
                    title={`${flight.flight_id}: ${flight.origin} → ${flight.destination}\n${formatTime(flight.arrival_start)} - ${formatTime(flight.arrival_end)}`}
                  >
                    {flight.flight_id}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
        
        {/* Legend */}
        <div className="legend">
          {runwayIds.map(runwayId => (
            <div key={runwayId} className="legend-item">
              <div 
                className="legend-color" 
                style={{ background: RUNWAY_COLORS[(runwayId - 1) % RUNWAY_COLORS.length] }}
              />
              <span>Runway {runwayId}</span>
            </div>
          ))}
          <div className="legend-item">
            <div 
              className="legend-color" 
              style={{ 
                background: '#3b82f6', 
                border: '2px solid #fbbf24',
                boxShadow: '0 0 8px rgba(251, 191, 36, 0.5)'
              }}
            />
            <span>Your Flight</span>
          </div>
        </div>
      </div>
      
      {/* Flight list */}
      <div className="runway-chart">
        <h3>✈️ Flight Schedule</h3>
        <div className="flight-list">
          {scheduleResult.flights
            .sort((a, b) => new Date(a.arrival_start) - new Date(b.arrival_start))
            .map(flight => (
              <div 
                key={flight.flight_id} 
                className="flight-item"
                style={{
                  borderLeft: flight.flight_id === 'YOUR_FLIGHT' 
                    ? '3px solid #fbbf24' 
                    : '3px solid transparent'
                }}
              >
                <div 
                  className="runway-badge"
                  style={{ 
                    background: RUNWAY_COLORS[(flight.runway_id - 1) % RUNWAY_COLORS.length] 
                  }}
                >
                  R{flight.runway_id}
                </div>
                <div className="flight-info">
                  <div className="flight-id">
                    {flight.flight_id}
                    {flight.flight_id === 'YOUR_FLIGHT' && (
                      <span style={{ 
                        marginLeft: '0.5rem', 
                        fontSize: '0.75rem', 
                        color: '#fbbf24',
                        fontWeight: 'normal'
                      }}>
                        ★ Your Flight
                      </span>
                    )}
                  </div>
                  <div className="flight-route">
                    {flight.origin} → {flight.destination}
                  </div>
                </div>
                <div className="flight-time">
                  <div>{formatTime(flight.arrival_start)}</div>
                  <div style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>
                    {flight.occupancy_time}min
                  </div>
                </div>
              </div>
            ))}
        </div>
      </div>
      
      {/* Conflict graph info */}
      {scheduleResult.conflicts && scheduleResult.conflicts.length > 0 && (
        <div className="runway-chart">
          <h3>🔗 Detected Conflicts (Resolved)</h3>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem', marginBottom: '1rem' }}>
            These flight pairs had overlapping time windows and were assigned different runways:
          </p>
          <div style={{ 
            display: 'flex', 
            flexWrap: 'wrap', 
            gap: '0.5rem',
            maxHeight: '150px',
            overflowY: 'auto'
          }}>
            {scheduleResult.conflicts.slice(0, 20).map((conflict, i) => (
              <span 
                key={i}
                style={{
                  padding: '0.25rem 0.75rem',
                  background: 'var(--surface)',
                  borderRadius: '999px',
                  fontSize: '0.75rem',
                  color: 'var(--text-muted)'
                }}
              >
                {conflict.flight1} ↔ {conflict.flight2}
              </span>
            ))}
            {scheduleResult.conflicts.length > 20 && (
              <span style={{ 
                padding: '0.25rem 0.75rem',
                fontSize: '0.75rem',
                color: 'var(--text-muted)'
              }}>
                +{scheduleResult.conflicts.length - 20} more
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default RunwayScheduleChart;

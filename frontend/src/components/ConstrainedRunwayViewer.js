import React, { useMemo } from 'react';
import { AlertTriangle, Clock, Users, TrendingUp, TrendingDown, Calendar } from 'lucide-react';

const ConstrainedRunwayViewer = ({ result }) => {
  // No result, show empty state
  if (!result) {
    return (
      <div className="empty-state">
        <Calendar size={48} />
        <p>Run the constrained runway scheduler to see results</p>
      </div>
    );
  }

  // Calculate statistics
  const stats = useMemo(() => {
    const { flights, delayed_flights, on_time_percentage, total_delay_minutes, avg_delay_minutes } = result;
    
    return {
      totalFlights: flights.length,
      delayedFlights: delayed_flights.length,
      onTimeFlights: flights.length - delayed_flights.length,
      onTimePercentage: on_time_percentage,
      totalDelayMinutes: total_delay_minutes,
      avgDelayMinutes: avg_delay_minutes || 0,
      maxDelayMinutes: delayed_flights.length > 0 
        ? Math.max(...delayed_flights.map(f => f.delayed_by)) 
        : 0
    };
  }, [result]);

  // Group flights by day for multi-day display
  const flightsByDay = useMemo(() => {
    const grouped = {};
    result.flights.forEach(flight => {
      const day = flight.day || 0;
      if (!grouped[day]) grouped[day] = [];
      grouped[day].push(flight);
    });
    return grouped;
  }, [result.flights]);

  // Get flights for each runway
  const runwayAssignments = result.runway_assignments || {};

  return (
    <div className="constrained-runway-viewer">
      {/* Header Statistics */}
      <div className="overview-stats">
        <div className="stat-card">
          <div className="stat-header">
            <Calendar size={20} />
            <span>Total Flights</span>
          </div>
          <div className="stat-value">{stats.totalFlights}</div>
        </div>

        <div className="stat-card">
          <div className="stat-header">
            <TrendingUp size={20} className="text-success" />
            <span>On-Time</span>
          </div>
          <div className="stat-value text-success">{stats.onTimeFlights}</div>
          <div className="stat-sub">{stats.onTimePercentage.toFixed(1)}%</div>
        </div>

        <div className="stat-card">
          <div className="stat-header">
            <TrendingDown size={20} className="text-warning" />
            <span>Delayed</span>
          </div>
          <div className="stat-value text-warning">{stats.delayedFlights}</div>
          <div className="stat-sub">{(100 - stats.onTimePercentage).toFixed(1)}%</div>
        </div>

        <div className="stat-card">
          <div className="stat-header">
            <Clock size={20} />
            <span>Total Delay</span>
          </div>
          <div className="stat-value">{stats.totalDelayMinutes}min</div>
          <div className="stat-sub">Avg: {stats.avgDelayMinutes.toFixed(1)}min</div>
        </div>
      </div>

      {/* Algorithm Info */}
      <div className="algorithm-info">
        <div>
          <strong>Algorithm:</strong> {result.algorithm.replace('_', ' ').toUpperCase()}
        </div>
        <div>
          <strong>Max Runways:</strong> {result.num_runways}
        </div>
        <div>
          <strong>Max Delay:</strong> {stats.maxDelayMinutes}min
        </div>
      </div>

      {/* Runway Assignments */}
      <div className="runway-sections">
        <h3><Users size={20} /> Runway Assignments ({Object.values(runwayAssignments).filter(flights => flights.length > 0).length} Runways Used)</h3>
        <div style={{ maxHeight: '600px', overflowY: 'auto', paddingRight: '0.5rem' }}>
        {Object.entries(runwayAssignments)
          .filter(([runwayId, flights]) => flights.length > 0)
          .sort(([a], [b]) => Number(a) - Number(b))
          .map(([runwayId, flights]) => (
          <div key={runwayId} className="runway-section">
            <div className="runway-header">
              <h4>Runway {runwayId}</h4>
              <span className="flight-count">{flights.length} flights</span>
            </div>

            <div className="flights-timeline">
              {flights.map((flight, idx) => {
                const isDelayed = flight.delayed_by > 0;
                const arrivalTime = new Date(flight.arrival_start);
                const endTime = new Date(flight.arrival_end);
                
                return (
                  <div 
                    key={flight.flight_id} 
                    className={`flight-card ${isDelayed ? 'delayed' : ''}`}
                  >
                    <div className="flight-header">
                      <span className="flight-id">{flight.flight_id}</span>
                      {isDelayed && (
                        <span className="delay-badge">
                          <AlertTriangle size={14} />
                          +{flight.delayed_by}min
                        </span>
                      )}
                    </div>

                    <div className="flight-details">
                      <div className="flight-route">
                        <span>{flight.origin}</span>
                        <span className="arrow">→</span>
                        <span>{flight.destination}</span>
                      </div>

                      <div className="flight-times">
                        <div className="time-slot">
                          <Clock size={12} />
                          {arrivalTime.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                          {' '}
                          {arrivalTime.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}
                          {' - '}
                          {endTime.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}
                        </div>
                      </div>

                      <div className="flight-meta">
                        <span className="priority-badge priority-{flight.priority}">
                          P{flight.priority}
                        </span>
                        <span className="passenger-count">
                          {flight.passenger_count} pax
                        </span>
                        <span className="distance">
                          {flight.distance.toFixed(0)} km
                        </span>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        ))}
        </div>
      </div>

      {/* Delayed Flights Summary */}
      {stats.delayedFlights > 0 && (
        <div className="delayed-summary">
          <h3><AlertTriangle size={20} /> Delayed Flights ({stats.delayedFlights})</h3>
          <div className="delayed-grid" style={{ maxHeight: '400px', overflowY: 'auto', paddingRight: '0.5rem' }}>
            {result.delayed_flights.slice(0, 10).map((flight) => (
              <div key={flight.flight_id} className="delayed-item">
                <span className="flight-id">{flight.flight_id}</span>
                <span className="delay-amount">+{flight.delayed_by}min</span>
                <span className="reason">Runway capacity</span>
              </div>
            ))}
            {result.delayed_flights.length > 10 && (
              <div className="delayed-item more">
                ... and {result.delayed_flights.length - 10} more
              </div>
            )}
          </div>
        </div>
      )}

      {/* Performance Metrics */}
      <div className="performance-metrics" style={{
        marginTop: '2rem',
        padding: '1.5rem',
        background: 'linear-gradient(135deg, rgba(59, 130, 246, 0.1), rgba(139, 92, 246, 0.1))',
        borderRadius: '12px',
        border: '1px solid rgba(59, 130, 246, 0.3)'
      }}>
        <h3 style={{ marginBottom: '1.5rem', fontSize: '1.25rem' }}>📊 Performance Metrics</h3>
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '1.5rem'
        }}>
          <div style={{
            padding: '1.25rem',
            background: 'rgba(0, 0, 0, 0.3)',
            borderRadius: '8px',
            textAlign: 'center',
            border: '1px solid rgba(255, 255, 255, 0.1)'
          }}>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>On-Time Rate</div>
            <div style={{ fontSize: '2rem', fontWeight: 'bold', color: stats.onTimePercentage >= 75 ? '#10b981' : '#f59e0b' }}>
              {stats.onTimePercentage.toFixed(1)}%
            </div>
          </div>
          <div style={{
            padding: '1.25rem',
            background: 'rgba(0, 0, 0, 0.3)',
            borderRadius: '8px',
            textAlign: 'center',
            border: '1px solid rgba(255, 255, 255, 0.1)'
          }}>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>Average Delay</div>
            <div style={{ fontSize: '2rem', fontWeight: 'bold' }}>
              {stats.avgDelayMinutes.toFixed(1)}<span style={{ fontSize: '1rem', color: 'var(--text-muted)' }}>min</span>
            </div>
          </div>
          <div style={{
            padding: '1.25rem',
            background: 'rgba(0, 0, 0, 0.3)',
            borderRadius: '8px',
            textAlign: 'center',
            border: '1px solid rgba(255, 255, 255, 0.1)'
          }}>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>Max Delay</div>
            <div style={{ fontSize: '2rem', fontWeight: 'bold', color: stats.maxDelayMinutes > 60 ? '#ef4444' : '#f59e0b' }}>
              {stats.maxDelayMinutes}<span style={{ fontSize: '1rem', color: 'var(--text-muted)' }}>min</span>
            </div>
          </div>
          <div style={{
            padding: '1.25rem',
            background: 'rgba(0, 0, 0, 0.3)',
            borderRadius: '8px',
            textAlign: 'center',
            border: '1px solid rgba(255, 255, 255, 0.1)'
          }}>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>Runways Used</div>
            <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#3b82f6' }}>
              {result.num_runways}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ConstrainedRunwayViewer;

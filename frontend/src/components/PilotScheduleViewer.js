import React, { useMemo } from 'react';
import { Users, Clock, AlertTriangle, CheckCircle, Award } from 'lucide-react';

// Pilot colors for visual distinction
const PILOT_COLORS = [
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
  '#14b8a6', // Teal
  '#f43f5e', // Rose
];

function PilotScheduleViewer({ pilotScheduleResult, isMultiDay = false }) {
  // Group assignments by pilot and optionally by day
  const { assignmentsByPilot, timelineData, assignmentsByDay } = useMemo(() => {
    if (!pilotScheduleResult) {
      return { assignmentsByPilot: {}, timelineData: [], assignmentsByDay: {} };
    }
    
    // Handle multi-day schedules
    if (isMultiDay && pilotScheduleResult.all_assignments) {
      const byPilot = {};
      const byDay = {};
      
      console.log('🔍 Processing all_assignments:', pilotScheduleResult.all_assignments.length, 'assignments');
      console.log('🔍 First few assignments:', pilotScheduleResult.all_assignments.slice(0, 3));
      
      pilotScheduleResult.all_assignments.forEach(assignment => {
        const pilotId = assignment.pilot_id;
        const day = assignment.day || 0;
        
        if (assignment.day === undefined) {
          console.warn('⚠️ Assignment missing day property:', assignment);
        }
        
        // By pilot
        if (!byPilot[pilotId]) {
          byPilot[pilotId] = [];
        }
        byPilot[pilotId].push(assignment);
        
        // By day
        if (!byDay[day]) {
          byDay[day] = [];
        }
        byDay[day].push(assignment);
      });
      
      // Sort assignments
      Object.keys(byPilot).forEach(pilotId => {
        byPilot[pilotId].sort((a, b) => {
          if (a.day !== b.day) return a.day - b.day;
          return new Date(a.flight_start) - new Date(b.flight_start);
        });
      });
      
      console.log('🔍 Grouped assignments by day:', byDay);
      console.log('🔍 Days found:', Object.keys(byDay));
      
      // Create timeline data
      const timeline = Object.keys(byPilot).map(pilotId => ({
        pilotId,
        pilot: { pilot_id: pilotId },
        assignments: byPilot[pilotId]
      }));
      
      return {
        assignmentsByPilot: byPilot,
        timelineData: timeline,
        assignmentsByDay: byDay
      };
    }
    
    // Single-day schedule
    if (!pilotScheduleResult.assignments) {
      return { assignmentsByPilot: {}, timelineData: [], assignmentsByDay: {} };
    }
    
    const byPilot = {};
    pilotScheduleResult.assignments.forEach(assignment => {
      const pilotId = assignment.pilot_id;
      if (!byPilot[pilotId]) {
        byPilot[pilotId] = [];
      }
      byPilot[pilotId].push(assignment);
    });
    
    // Sort assignments within each pilot by time
    Object.keys(byPilot).forEach(pilotId => {
      byPilot[pilotId].sort((a, b) => 
        new Date(a.flight_start) - new Date(b.flight_start)
      );
    });
    
    // Create timeline data
    const timeline = Object.keys(byPilot).map(pilotId => {
      const pilot = pilotScheduleResult.pilots.find(p => p.pilot_id === pilotId);
      return {
        pilotId,
        pilot,
        assignments: byPilot[pilotId]
      };
    });
    
    return {
      assignmentsByPilot: byPilot,
      timelineData: timeline,
      assignmentsByDay: {}
    };
  }, [pilotScheduleResult, isMultiDay]);
  
  if (!pilotScheduleResult) {
    return <div className="loading">No pilot schedule data available</div>;
  }
  
  const formatTime = (isoString) => {
    return new Date(isoString).toLocaleTimeString('en-US', { 
      hour: '2-digit', 
      minute: '2-digit',
      hour12: false 
    });
  };
  
  const formatHours = (hours) => {
    if (hours === undefined || hours === null || isNaN(hours)) return 'N/A';
    return `${hours.toFixed(1)}h`;
  };
  
  const getPilotColor = (index) => {
    return PILOT_COLORS[index % PILOT_COLORS.length];
  };
  
  const getUtilizationColor = (utilization) => {
    if (utilization >= 90) return '#ef4444'; // Red - high
    if (utilization >= 70) return '#f59e0b'; // Amber - medium
    if (utilization >= 40) return '#10b981'; // Green - good
    return '#6b7280'; // Gray - low
  };
  
  return (
    <div>
      {/* Header Stats */}
      <div className="runway-chart">
        <h3>👨‍✈️ {isMultiDay ? 'Multi-Day ' : ''}Pilot Schedule Overview</h3>
        <div className="stats-grid">
          <div className="stat-card">
            <div className="value" style={{ color: '#10b981' }}>
              {isMultiDay ? pilotScheduleResult.total_pilots_used : 
                `${pilotScheduleResult.total_pilots_used}/${pilotScheduleResult.pilots.length}`}
            </div>
            <div className="label">Pilots Used</div>
          </div>
          <div className="stat-card">
            <div className="value">
              {isMultiDay ? pilotScheduleResult.all_assignments.length : pilotScheduleResult.assignments.length}
            </div>
            <div className="label">Assigned Flights</div>
          </div>
          {isMultiDay && (
            <div className="stat-card">
              <div className="value">{Object.keys(pilotScheduleResult.daily_schedules).length}</div>
              <div className="label">Days</div>
            </div>
          )}
          {!isMultiDay && (
            <div className="stat-card">
              <div className="value" style={{ color: pilotScheduleResult.unassigned_flights.length > 0 ? '#f59e0b' : '#10b981' }}>
                {pilotScheduleResult.unassigned_flights.length}
              </div>
              <div className="label">Unassigned</div>
            </div>
          )}
          <div className="stat-card">
            <div className="value" style={{ 
              color: (isMultiDay ? pilotScheduleResult.overall_compliance_rate : pilotScheduleResult.compliance_rate) >= 95 ? '#10b981' : 
                     (isMultiDay ? pilotScheduleResult.overall_compliance_rate : pilotScheduleResult.compliance_rate) >= 80 ? '#f59e0b' : '#ef4444' 
            }}>
              {isMultiDay ? pilotScheduleResult.overall_compliance_rate.toFixed(1) : pilotScheduleResult.compliance_rate}%
            </div>
            <div className="label">Compliance</div>
          </div>
        </div>
        
        {/* FAA Compliance Banner */}
        <div style={{ 
          marginTop: '1rem', 
          padding: '0.75rem 1rem',
          background: pilotScheduleResult.is_valid ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
          border: `1px solid ${pilotScheduleResult.is_valid ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`,
          borderRadius: '8px',
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem'
        }}>
          {pilotScheduleResult.is_valid ? (
            <>
              <CheckCircle size={20} color="#10b981" />
              <span style={{ color: '#10b981', fontWeight: '500' }}>
                ✓ All FAA regulations satisfied - Schedule is compliant
              </span>
            </>
          ) : (
            <>
              <AlertTriangle size={20} color="#ef4444" />
              <span style={{ color: '#ef4444', fontWeight: '500' }}>
                ⚠ Schedule has {isMultiDay && pilotScheduleResult.violations ? pilotScheduleResult.violations.length : ''} violations - See details below
              </span>
            </>
          )}
        </div>
      </div>
      
      {/* Multi-Day Breakdown - Show assignments grouped by day */}
      {isMultiDay && assignmentsByDay && Object.keys(assignmentsByDay).length > 0 && (
        <div className="runway-chart">
          <h3>📅 Day-by-Day Breakdown</h3>
          <div style={{
            maxHeight: '600px',
            overflowY: 'auto',
            paddingRight: '0.5rem'
          }}>
            {Object.keys(assignmentsByDay).sort((a, b) => parseInt(a) - parseInt(b)).map(day => {
              const dayAssignments = assignmentsByDay[day];
              const daySchedule = pilotScheduleResult.daily_schedules ? pilotScheduleResult.daily_schedules[day] : null;
              
              return (
                <div 
                  key={day}
                  style={{
                    marginBottom: '1.5rem',
                    padding: '1rem',
                    background: 'var(--surface)',
                    borderRadius: '8px',
                    border: '1px solid rgba(255,255,255,0.1)'
                  }}
                >
                  <div style={{ 
                    display: 'flex', 
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    marginBottom: '1rem',
                    paddingBottom: '0.75rem',
                    borderBottom: '1px solid rgba(255,255,255,0.1)'
                  }}>
                    <h4 style={{ margin: 0 }}>Day {parseInt(day) + 1}</h4>
                    {daySchedule && (
                      <div style={{ display: 'flex', gap: '1rem', fontSize: '0.85rem' }}>
                        <span style={{ color: '#10b981' }}>
                          {daySchedule.total_pilots_used} pilots
                        </span>
                        <span>•</span>
                        <span>{daySchedule.assignments.length} flights</span>
                        <span>•</span>
                        <span style={{ 
                          color: daySchedule.compliance_rate >= 95 ? '#10b981' : '#f59e0b' 
                        }}>
                          {daySchedule.compliance_rate.toFixed(2)}% compliant
                        </span>
                      </div>
                    )}
                  </div>
                  
                  <div style={{ 
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))',
                    gap: '0.75rem'
                  }}>
                    {dayAssignments.map((assignment, idx) => (
                      <div
                        key={`${day}-${assignment.flight_id}`}
                        style={{
                          padding: '0.75rem',
                          background: 'rgba(255,255,255,0.05)',
                          borderRadius: '6px',
                          borderLeft: `3px solid ${getPilotColor(dayAssignments.findIndex(a => a.pilot_id === assignment.pilot_id) % PILOT_COLORS.length)}`
                        }}
                      >
                        <div style={{ 
                          display: 'flex',
                          justifyContent: 'space-between',
                          marginBottom: '0.5rem'
                        }}>
                          <strong style={{ fontSize: '0.9rem' }}>{assignment.flight_id}</strong>
                          <span style={{ 
                            fontSize: '0.75rem',
                            padding: '0.125rem 0.5rem',
                            background: 'rgba(59, 130, 246, 0.2)',
                            borderRadius: '4px',
                            color: '#3b82f6'
                          }}>
                            {assignment.pilot_id}
                          </span>
                        </div>
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                          {formatTime(assignment.flight_start)} - {formatTime(assignment.flight_end)}
                        </div>
                        {assignment.duration_hours !== undefined && (
                          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
                            Duration: {formatHours(assignment.duration_hours)}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
      
      {/* Pilot Cards */}
      <div className="runway-chart">
        <h3><Users size={20} /> Pilot Assignments</h3>
        <div style={{ 
          display: 'grid', 
          gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', 
          gap: '1rem',
          marginTop: '1rem'
        }}>
          {timelineData.map((data, index) => {
            const { pilot, assignments } = data;
            // Safely get utilization, ensuring it's a valid number
            const rawUtilization = pilotScheduleResult.pilot_utilization ? 
              pilotScheduleResult.pilot_utilization[pilot.pilot_id] : undefined;
            const utilization = typeof rawUtilization === 'number' && !isNaN(rawUtilization) ? 
              rawUtilization : 0;
            
            return (
              <div 
                key={pilot.pilot_id} 
                style={{
                  background: 'var(--surface)',
                  border: `2px solid ${getPilotColor(index)}`,
                  borderRadius: '8px',
                  padding: '1rem',
                  transition: 'transform 0.2s',
                  cursor: 'pointer'
                }}
                className="pilot-card"
              >
                {/* Pilot Header */}
                <div style={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  justifyContent: 'space-between',
                  marginBottom: '0.75rem',
                  paddingBottom: '0.75rem',
                  borderBottom: '1px solid rgba(255,255,255,0.1)'
                }}>
                  <div>
                    <div style={{ 
                      display: 'flex', 
                      alignItems: 'center', 
                      gap: '0.5rem',
                      marginBottom: '0.25rem'
                    }}>
                      <div style={{
                        width: '10px',
                        height: '10px',
                        borderRadius: '50%',
                        background: getPilotColor(index)
                      }} />
                      <strong style={{ fontSize: '1rem' }}>{pilot.name || pilot.pilot_id}</strong>
                    </div>
                    <div style={{ 
                      fontSize: '0.75rem', 
                      color: 'var(--text-muted)',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.5rem'
                    }}>
                      <span>{pilot.pilot_id}</span>
                      {pilot.certification && (
                        <>
                          <span>•</span>
                          <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                            <Award size={12} />
                            {pilot.certification}
                          </span>
                        </>
                      )}
                    </div>
                  </div>
                  
                  {/* Utilization Badge */}
                  <div style={{
                    padding: '0.25rem 0.75rem',
                    background: `${getUtilizationColor(utilization)}20`,
                    color: getUtilizationColor(utilization),
                    borderRadius: '12px',
                    fontSize: '0.75rem',
                    fontWeight: '600'
                  }}>
                    {utilization.toFixed(0)}%
                  </div>
                </div>
                
                {/* Hours Stats - Only show for single-day mode */}
                {!isMultiDay && pilot.total_hours_today !== undefined && (
                  <div style={{ 
                    display: 'grid',
                    gridTemplateColumns: '1fr 1fr',
                    gap: '0.5rem',
                    marginBottom: '0.75rem'
                  }}>
                    <div style={{ 
                      padding: '0.5rem',
                      background: 'rgba(59, 130, 246, 0.1)',
                      borderRadius: '6px',
                      textAlign: 'center'
                    }}>
                      <div style={{ fontSize: '1.25rem', fontWeight: '600', color: '#3b82f6' }}>
                        {formatHours(pilot.total_hours_today)}
                      </div>
                      <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                        Flown
                      </div>
                    </div>
                    <div style={{ 
                      padding: '0.5rem',
                      background: 'rgba(16, 185, 129, 0.1)',
                      borderRadius: '6px',
                      textAlign: 'center'
                    }}>
                      <div style={{ fontSize: '1.25rem', fontWeight: '600', color: '#10b981' }}>
                        {formatHours(pilot.remaining_hours)}
                      </div>
                      <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                        Remaining
                      </div>
                    </div>
                  </div>
                )}
                
                {/* Assignments */}
                <div style={{ fontSize: '0.85rem' }}>
                  <div style={{ 
                    fontWeight: '500', 
                    marginBottom: '0.5rem',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.25rem',
                    color: 'var(--text-muted)'
                  }}>
                    <Clock size={14} />
                    Flights ({assignments.length})
                  </div>
                  <div style={{ maxHeight: '150px', overflowY: 'auto' }}>
                    {assignments.map((assignment, idx) => {
                      // Calculate rest before next flight
                      let restTime = null;
                      if (idx < assignments.length - 1) {
                        const nextStart = new Date(assignments[idx + 1].flight_start);
                        const currentEnd = new Date(assignment.flight_end);
                        restTime = (nextStart - currentEnd) / (1000 * 60 * 60); // hours
                      }
                      
                      return (
                        <div 
                          key={assignment.flight_id}
                          style={{
                            padding: '0.5rem',
                            marginBottom: '0.5rem',
                            background: 'rgba(255,255,255,0.05)',
                            borderRadius: '4px',
                            borderLeft: `3px solid ${getPilotColor(index)}`
                          }}
                        >
                          <div style={{ 
                            display: 'flex', 
                            justifyContent: 'space-between',
                            marginBottom: '0.25rem'
                          }}>
                            <strong>{assignment.flight_id}</strong>
                            {assignment.duration_hours !== undefined && (
                              <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>
                                {formatHours(assignment.duration_hours)}
                              </span>
                            )}
                          </div>
                          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                            {formatTime(assignment.flight_start)} - {formatTime(assignment.flight_end)}
                          </div>
                          {restTime !== null && (
                            <div style={{ 
                              marginTop: '0.25rem',
                              fontSize: '0.7rem',
                              color: restTime < 10 ? '#ef4444' : '#10b981',
                              fontWeight: '500'
                            }}>
                              ⏱ {formatHours(restTime)} rest
                              {restTime < 10 && ' ⚠️'}
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
      
      {/* Unassigned Flights - Only for single-day mode */}
      {!isMultiDay && pilotScheduleResult.unassigned_flights && pilotScheduleResult.unassigned_flights.length > 0 && (
        <div className="runway-chart">
          <h3 style={{ color: '#f59e0b' }}>
            <AlertTriangle size={20} /> Unassigned Flights
          </h3>
          <div style={{ 
            background: 'rgba(251, 191, 36, 0.1)',
            border: '1px solid rgba(251, 191, 36, 0.3)',
            borderRadius: '8px',
            padding: '1rem'
          }}>
            <p style={{ marginBottom: '0.75rem', color: '#f59e0b' }}>
              The following flights could not be assigned due to duty hour or rest requirements:
            </p>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
              {pilotScheduleResult.unassigned_flights.map(flight => (
                <div 
                  key={flight.flight_id}
                  style={{
                    padding: '0.5rem 0.75rem',
                    background: 'rgba(251, 191, 36, 0.2)',
                    borderRadius: '6px',
                    fontSize: '0.85rem',
                    border: '1px solid rgba(251, 191, 36, 0.4)'
                  }}
                >
                  <strong>{flight.flight_id}</strong>
                  <span style={{ margin: '0 0.5rem', color: 'var(--text-muted)' }}>•</span>
                  <span style={{ fontSize: '0.75rem' }}>
                    {flight.origin} → {flight.destination}
                  </span>
                </div>
              ))}
            </div>
            <p style={{ marginTop: '0.75rem', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
              💡 Consider adding more pilots or adjusting flight schedules
            </p>
          </div>
        </div>
      )}
      
      {/* Violations */}
      {pilotScheduleResult.violations && pilotScheduleResult.violations.length > 0 && (
        <div className="runway-chart">
          <h3 style={{ color: '#ef4444' }}>
            <AlertTriangle size={20} /> Regulation Violations
          </h3>
          <div style={{ 
            background: 'rgba(239, 68, 68, 0.1)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            borderRadius: '8px',
            padding: '1rem'
          }}>
            {pilotScheduleResult.violations.map((violation, idx) => (
              <div 
                key={idx}
                style={{
                  padding: '0.75rem',
                  marginBottom: idx < pilotScheduleResult.violations.length - 1 ? '0.5rem' : 0,
                  background: 'rgba(239, 68, 68, 0.1)',
                  borderLeft: '3px solid #ef4444',
                  borderRadius: '4px',
                  fontSize: '0.85rem'
                }}
              >
                ❌ {violation}
              </div>
            ))}
          </div>
        </div>
      )}
      
      {/* Statistics */}
      {pilotScheduleResult.statistics && (
        <div className="runway-chart">
          <h3>📊 Statistics</h3>
          <div style={{ 
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: '1rem'
          }}>
            <div style={{ padding: '1rem', background: 'var(--surface)', borderRadius: '8px' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.25rem' }}>
                Total Pilots
              </div>
              <div style={{ fontSize: '1.5rem', fontWeight: '600' }}>
                {pilotScheduleResult.statistics.total_pilots}
              </div>
            </div>
            <div style={{ padding: '1rem', background: 'var(--surface)', borderRadius: '8px' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.25rem' }}>
                Active Pilots
              </div>
              <div style={{ fontSize: '1.5rem', fontWeight: '600', color: '#10b981' }}>
                {pilotScheduleResult.statistics.active_pilots}
              </div>
            </div>
            <div style={{ padding: '1rem', background: 'var(--surface)', borderRadius: '8px' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.25rem' }}>
                Avg Hours / Pilot
              </div>
              <div style={{ fontSize: '1.5rem', fontWeight: '600', color: '#3b82f6' }}>
                {formatHours(pilotScheduleResult.statistics.avg_hours_per_pilot)}
              </div>
            </div>
            <div style={{ padding: '1rem', background: 'var(--surface)', borderRadius: '8px' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.25rem' }}>
                Utilization Rate
              </div>
              <div style={{ fontSize: '1.5rem', fontWeight: '600', color: '#f59e0b' }}>
                {pilotScheduleResult.statistics.utilization_rate.toFixed(1)}%
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default PilotScheduleViewer;

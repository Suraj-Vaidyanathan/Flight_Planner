// Enhanced Multi-Day Pilot Scheduler Panel Component
// This replaces the existing pilot scheduler panel in App.js

/* Replace the pilot scheduler section (line ~684-820) with this code */

{view === 'pilots' ? (
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
    {/* Multi-Day Flight Generator Panel (same as pilots) */}
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
      
      {!generatedFlights && (
        <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.5rem' }}>
          💡 Generate multi-day flights first
        </p>
      )}
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
) : (
  /* Original single-day pilot scheduler panel code remains here */
)}

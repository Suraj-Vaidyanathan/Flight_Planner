import axios from 'axios';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:5001/api';

const api = {
  // Health check
  async healthCheck() {
    const response = await axios.get(`${API_BASE}/health`);
    return response.data;
  },
  
  // Get all airports
  async getAirports() {
    const response = await axios.get(`${API_BASE}/airports`);
    return response.data;
  },
  
  // Get single airport
  async getAirport(id) {
    const response = await axios.get(`${API_BASE}/airports/${id}`);
    return response.data;
  },
  
  // Get all routes
  async getRoutes() {
    const response = await axios.get(`${API_BASE}/routes`);
    return response.data;
  },
  
  // Find shortest route
  async findRoute(source, destination, cruisingSpeed = 850) {
    const response = await axios.post(`${API_BASE}/route/find`, {
      source,
      destination,
      cruising_speed: cruisingSpeed
    });
    return response.data;
  },
  
  // Find all possible routes
  async findAllRoutes(source, destination, maxStops = 3) {
    const response = await axios.post(`${API_BASE}/route/all`, {
      source,
      destination,
      max_stops: maxStops
    });
    return response.data;
  },
  
  // Generate random flights
  async generateFlights(destination, count = 10, windowMinutes = 60) {
    const response = await axios.post(`${API_BASE}/flights/generate`, {
      destination,
      count,
      window_minutes: windowMinutes
    });
    return response.data;
  },
  
  // Schedule flights
  async scheduleFlights(flights, algorithm = 'dsatur') {
    const response = await axios.post(`${API_BASE}/schedule`, {
      flights,
      algorithm
    });
    return response.data;
  },
  
  // Run schedule demo
  async scheduleDemo(destination, count = 10, algorithm = 'dsatur') {
    const response = await axios.post(`${API_BASE}/schedule/demo`, {
      destination,
      count,
      algorithm
    });
    return response.data;
  },
  
  // Full demo: route + scheduling
  async routeWithScheduling(source, destination, numOtherFlights = 8) {
    const response = await axios.post(`${API_BASE}/route/with-scheduling`, {
      source,
      destination,
      num_other_flights: numOtherFlights
    });
    return response.data;
  },
  
  // Schedule pilots to flights
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
  },

  // Generate multi-day flights
  async generateMultiDayFlights(destination, numDays = 3, flightsPerDay = 15, pattern = 'realistic', seed = null) {
    const response = await axios.post(`${API_BASE}/flights/generate-multi-day`, {
      destination,
      num_days: numDays,
      flights_per_day: flightsPerDay,
      pattern,
      seed
    });
    return response.data;
  },

  // Schedule pilots across multiple days
  async schedulePilotsMultiDay(flights, numPilots = 5, options = {}) {
    const response = await axios.post(`${API_BASE}/pilots/schedule-multi-day`, {
      flights,
      num_pilots: numPilots,
      min_rest_hours: options.minRestHours || 10.0,
      max_daily_hours: options.maxDailyHours || 8.0,
      strategy: options.strategy || 'least_busy',
      base_airport: options.baseAirport || ''
    });
    return response.data;
  },

  // Schedule with constrained runways
  async scheduleConstrainedRunways(flights, maxRunways = 2, algorithm = 'priority_based') {
    const response = await axios.post(`${API_BASE}/runways/schedule-constrained`, {
      flights,
      max_runways: maxRunways,
      algorithm
    });
    return response.data;
  },

  // Compare constrained scheduling algorithms
  async compareConstrainedAlgorithms(flights, maxRunways = 2) {
    const response = await axios.post(`${API_BASE}/runways/compare-algorithms`, {
      flights,
      max_runways: maxRunways
    });
    return response.data;
  }
};

export default api;

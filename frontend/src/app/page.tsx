'use strict';

'use client';

import React, { useState, useEffect, useRef } from 'react';
import { 
  Search, 
  MapPin, 
  Utensils, 
  Star, 
  Sparkles, 
  Plus, 
  Minus, 
  X, 
  Database, 
  Award, 
  ArrowRight,
  Wifi,
  WifiOff,
  Flame,
  Info
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

// API Server Address
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Curated Unsplash images sorted by cuisine categories for beautiful cards
const cuisineImages: Record<string, string[]> = {
  italian: [
    'https://images.unsplash.com/photo-1546549032-9571cd6b27df?auto=format&fit=crop&w=600&q=80',
    'https://images.unsplash.com/photo-1513104890138-7c749659a591?auto=format&fit=crop&w=600&q=80',
    'https://images.unsplash.com/photo-1579751626657-72bc17010498?auto=format&fit=crop&w=600&q=80'
  ],
  biryani: [
    'https://images.unsplash.com/photo-1585938338392-50a59970d8ee?auto=format&fit=crop&w=600&q=80',
    'https://images.unsplash.com/photo-1633945274405-b6c8069047b0?auto=format&fit=crop&w=600&q=80'
  ],
  mughlai: [
    'https://images.unsplash.com/photo-1565557623262-b51c2513a641?auto=format&fit=crop&w=600&q=80',
    'https://images.unsplash.com/photo-1601050690597-df056fb4ce78?auto=format&fit=crop&w=600&q=80'
  ],
  fastfood: [
    'https://images.unsplash.com/photo-1568901346375-23c9450c58cd?auto=format&fit=crop&w=600&q=80',
    'https://images.unsplash.com/photo-1571091718767-18b5b1457add?auto=format&fit=crop&w=600&q=80',
    'https://images.unsplash.com/photo-1550547660-d9450f859349?auto=format&fit=crop&w=600&q=80'
  ],
  southindian: [
    'https://images.unsplash.com/photo-1668236543090-82eba5ee5976?auto=format&fit=crop&w=600&q=80',
    'https://images.unsplash.com/photo-1541014741259-df5290db5785?auto=format&fit=crop&w=600&q=80'
  ],
  northindian: [
    'https://images.unsplash.com/photo-1631452180519-c014fe946bc7?auto=format&fit=crop&w=600&q=80',
    'https://images.unsplash.com/photo-1588166524941-3bf61a9c41db?auto=format&fit=crop&w=600&q=80'
  ],
  chinese: [
    'https://images.unsplash.com/photo-1563245372-f21724e3856d?auto=format&fit=crop&w=600&q=80',
    'https://images.unsplash.com/photo-1585032226651-759b368d7246?auto=format&fit=crop&w=600&q=80',
    'https://images.unsplash.com/photo-1525755662778-989d0524087e?auto=format&fit=crop&w=600&q=80'
  ],
  cafe: [
    'https://images.unsplash.com/photo-1509042239860-f550ce710b93?auto=format&fit=crop&w=600&q=80',
    'https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=600&q=80',
    'https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?auto=format&fit=crop&w=600&q=80'
  ],
  desserts: [
    'https://images.unsplash.com/photo-1578985545062-69928b1d9587?auto=format&fit=crop&w=600&q=80',
    'https://images.unsplash.com/photo-1551024601-bec78aea704b?auto=format&fit=crop&w=600&q=80',
    'https://images.unsplash.com/photo-1501443762994-82bd5dace89a?auto=format&fit=crop&w=600&q=80'
  ],
  bar: [
    'https://images.unsplash.com/photo-1514362545857-3bc16c4c7d1b?auto=format&fit=crop&w=600&q=80',
    'https://images.unsplash.com/photo-1470337458703-46ad1756a187?auto=format&fit=crop&w=600&q=80',
    'https://images.unsplash.com/photo-1532634922-8fe0b757fb13?auto=format&fit=crop&w=600&q=80'
  ],
  japanese: [
    'https://images.unsplash.com/photo-1579871494447-9811cf80d66c?auto=format&fit=crop&w=600&q=80',
    'https://images.unsplash.com/photo-1569718212165-3a8278d5f624?auto=format&fit=crop&w=600&q=80'
  ],
  mexican: [
    'https://images.unsplash.com/photo-1565299585323-38d6b0865b47?auto=format&fit=crop&w=600&q=80',
    'https://images.unsplash.com/photo-1626379616459-b2ce1d9decbc?auto=format&fit=crop&w=600&q=80'
  ],
  salad: [
    'https://images.unsplash.com/photo-1512621776951-a57141f2eefd?auto=format&fit=crop&w=600&q=80'
  ],
  steak: [
    'https://images.unsplash.com/photo-1544025162-d76694265947?auto=format&fit=crop&w=600&q=80',
    'https://images.unsplash.com/photo-1546964124-0cce460f38ef?auto=format&fit=crop&w=600&q=80'
  ],
  seafood: [
    'https://images.unsplash.com/photo-1534080564583-6be75777b70a?auto=format&fit=crop&w=600&q=80'
  ],
  default: [
    'https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=600&q=80',
    'https://images.unsplash.com/photo-1555396273-367ea4eb4db5?auto=format&fit=crop&w=600&q=80',
    'https://images.unsplash.com/photo-1552566626-52f8b828add9?auto=format&fit=crop&w=600&q=80'
  ]
};

function getRestaurantImage(name: string, cuisines: string[], id: string): string {
  const searchStr = (name + ' ' + cuisines.join(' ')).toLowerCase();
  const hash = id ? id.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0) : 0;
  
  const categories = [
    { keys: ['pizza', 'italian', 'pasta', 'lasagna'], list: cuisineImages.italian },
    { keys: ['biryani', 'pulav'], list: cuisineImages.biryani },
    { keys: ['kebab', 'kabab', 'tandoori', 'tikka', 'mughlai'], list: cuisineImages.mughlai },
    { keys: ['burger', 'fast food', 'fries'], list: cuisineImages.fastfood },
    { keys: ['dosa', 'idli', 'south indian', 'uttapam', 'sambar'], list: cuisineImages.southindian },
    { keys: ['north indian', 'curry', 'roti', 'thali', 'paneer'], list: cuisineImages.northindian },
    { keys: ['chinese', 'momo', 'noodle', 'asian', 'dim sum', 'wonton'], list: cuisineImages.chinese },
    { keys: ['ice cream', 'gelato', 'dessert', 'sweet', 'cake', 'pastry', 'bakery', 'waffle', 'donut'], list: cuisineImages.desserts },
    { keys: ['cafe', 'coffee', 'tea', 'chai', 'latte', 'espresso'], list: cuisineImages.cafe },
    { keys: ['bar', 'pub', 'brewery', 'cocktail', 'beer', 'lounge', 'wine'], list: cuisineImages.bar },
    { keys: ['sushi', 'japanese', 'ramen', 'tempura'], list: cuisineImages.japanese },
    { keys: ['taco', 'mexican', 'burrito', 'nacho', 'quesadilla'], list: cuisineImages.mexican },
    { keys: ['salad', 'healthy', 'bowl', 'green'], list: cuisineImages.salad },
    { keys: ['steak', 'bbq', 'ribs', 'grill', 'meat'], list: cuisineImages.steak },
    { keys: ['seafood', 'fish', 'crab', 'prawn', 'lobster'], list: cuisineImages.seafood }
  ];

  for (const cat of categories) {
    if (cat.keys.some(key => searchStr.includes(key))) {
      return cat.list[hash % cat.list.length];
    }
  }
  
  const list = cuisineImages['default'];
  return list[hash % list.length];
}

// Popular chips to display
const popularCuisineChips = ["North Indian", "Chinese", "Italian", "Cafe", "South Indian", "Desserts", "Biryani"];
const popularExtrasTags = ["Outdoor Seating", "Family Friendly", "Romantic", "Rooftop", "Live Music", "Valet Parking"];

interface Restaurant {
  id: string;
  name: string;
  location: string;
  cuisines: string[];
  rating: number | null;
  cost_for_two: number | null;
  budget_band: string | null;
  metadata?: Record<string, any>;
}

interface Recommendation {
  rank: number;
  restaurant: Restaurant;
  explanation: string;
  match_highlights: string[];
}

export default function Home() {
  // Option lists from backend
  const [cities, setCities] = useState<string[]>([]);
  const [cuisines, setCuisines] = useState<string[]>([]);
  const [totalRecords, setTotalRecords] = useState<number>(0);
  const [optionsLoading, setOptionsLoading] = useState<boolean>(true);

  // Form selections
  const [locationInput, setLocationInput] = useState<string>('');
  const [showLocationDropdown, setShowLocationDropdown] = useState<boolean>(false);
  
  const [budgetBand, setBudgetBand] = useState<string | null>(null);
  
  const [cuisineInput, setCuisineInput] = useState<string>('');
  const [selectedCuisine, setSelectedCuisine] = useState<string>('');
  const [showCuisineDropdown, setShowCuisineDropdown] = useState<boolean>(false);
  
  const [minRating, setMinRating] = useState<number>(3.5);
  
  const [selectedExtrasTags, setSelectedExtrasTags] = useState<Set<string>>(new Set());
  const [customRequests, setCustomRequests] = useState<string>('');
  
  const [topK, setTopK] = useState<number>(5);
  const [useMock, setUseMock] = useState<boolean>(false);

  // App running states
  const [isSearching, setIsSearching] = useState<boolean>(false);
  const [apiError, setApiError] = useState<string>('');
  const [searchExecuted, setSearchExecuted] = useState<boolean>(false);
  const [latency, setLatency] = useState<number>(0);
  const [candidateCount, setCandidateCount] = useState<number>(0);

  // Results
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [aiSummary, setAiSummary] = useState<string>('');
  const [selectedRecId, setSelectedRecId] = useState<string | null>(null);

  // Refs for closing dropdowns when clicking outside
  const locationRef = useRef<HTMLDivElement>(null);
  const cuisineRef = useRef<HTMLDivElement>(null);

  // Fetch locations & cuisines on mount
  useEffect(() => {
    fetchOptions();

    // Event listener for click outside dropdowns
    function handleClickOutside(event: MouseEvent) {
      if (locationRef.current && !locationRef.current.contains(event.target as Node)) {
        setShowLocationDropdown(false);
      }
      if (cuisineRef.current && !cuisineRef.current.contains(event.target as Node)) {
        setShowCuisineDropdown(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, []);

  const fetchOptions = async () => {
    try {
      setOptionsLoading(true);
      const res = await fetch(`${API_BASE}/api/options`);
      if (!res.ok) throw new Error("Failed to fetch filter options");
      const data = await res.json();
      setCities(data.cities || []);
      setCuisines(data.cuisines || []);
      setTotalRecords(data.total_records || 0);
    } catch (err: any) {
      console.error(err);
      setApiError("Could not connect to FastAPI server. Please make sure it is running at port 8000.");
    } finally {
      setOptionsLoading(false);
    }
  };

  // Autocomplete filter lists
  const filteredCities = locationInput.trim() === ''
    ? cities
    : cities.filter(c => c.toLowerCase().includes(locationInput.toLowerCase()));

  const filteredCuisines = cuisineInput.trim() === ''
    ? cuisines
    : cuisines.filter(c => c.toLowerCase().includes(cuisineInput.toLowerCase()));

  // Stars change trigger
  const handleStarClick = (rating: number) => {
    setMinRating(rating);
  };

  // Cuisine chip click trigger
  const handleCuisineChipClick = (cuisineName: string) => {
    if (selectedCuisine === cuisineName) {
      setSelectedCuisine('');
    } else {
      setSelectedCuisine(cuisineName);
      setCuisineInput('');
    }
  };

  // Extra tag click trigger
  const handleExtraTagClick = (tag: string) => {
    const updated = new Set(selectedExtrasTags);
    if (updated.has(tag)) {
      updated.delete(tag);
    } else {
      updated.add(tag);
    }
    setSelectedExtrasTags(updated);
  };

  // Stepper triggers
  const handleKAdjust = (amount: number) => {
    const val = topK + amount;
    if (val >= 1 && val <= 10) {
      setTopK(val);
    }
  };

  // Trigger search
  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!locationInput) {
      setApiError("Location is required to get recommendations.");
      return;
    }

    setIsSearching(true);
    setApiError('');
    setSearchExecuted(false);
    setSelectedRecId(null);

    const extrasList = Array.from(selectedExtrasTags);
    if (customRequests.trim()) {
      extrasList.push(customRequests.trim());
    }

    const payload = {
      location: locationInput,
      budget: budgetBand,
      cuisine: selectedCuisine || cuisineInput || null,
      min_rating: minRating,
      extras: extrasList.join(', '),
      top_k: topK,
      use_mock: useMock
    };

    const startTime = performance.now();

    try {
      const res = await fetch(`${API_BASE}/api/recommendations`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || "Server failed to process query.");
      }

      const data = await res.json();
      const duration = (performance.now() - startTime) / 1000;
      
      setRecommendations(data.recommendations || []);
      setAiSummary(data.summary || '');
      setCandidateCount(data.candidate_count || 0);
      setLatency(duration);
      setSearchExecuted(true);

      if (data.message) {
        setApiError(data.message);
      }
    } catch (err: any) {
      console.error(err);
      setApiError(err.message || "An unexpected error occurred. Please verify your connection.");
    } finally {
      setIsSearching(false);
    }
  };

  const selectedRec = recommendations.find(r => r.restaurant.id === selectedRecId);

  // Derive confidence rating from highlights & scores
  const getMatchScore = (rec: Recommendation) => {
    const base = rec.restaurant.rating ? rec.restaurant.rating * 18 : 70;
    const highlightBonus = rec.match_highlights.length * 3;
    return Math.min(100, Math.round(base + highlightBonus));
  };

  return (
    <div className="app-container">
      {/* ── LEFT SIDEBAR CONFIG ── */}
      <aside className="sidebar-panel">
        <div>
          {/* Logo Brand */}
          <div className="brand-section">
            <div className="brand-icon">
              <Flame size={20} className="fill-white" />
            </div>
            <div>
              <h1 className="brand-text-title">Gourmet Advisor</h1>
              <span className="brand-text-subtitle">AI Discovery Suite</span>
            </div>
          </div>

          {/* Quick Info & Stats */}
          <div>
            <div className="info-card">
              <span className="info-card-header">Engine Info</span>
              
              <div className="info-row">
                <span className="info-row-label">
                  <Database size={13} /> preloaded data
                </span>
                <span className="info-row-value">
                  {totalRecords.toLocaleString()} recs
                </span>
              </div>
              
              <div className="info-row">
                <span className="info-row-label">
                  {useMock ? <WifiOff size={13} style={{ color: '#ffa502' }} /> : <Wifi size={13} style={{ color: '#00d2ff' }} />}
                  Orchestrator Mode
                </span>
                <span className="info-row-value" style={{ color: useMock ? '#ffa502' : '#00d2ff' }}>
                  {useMock ? 'Offline Mock' : 'Online Gemini'}
                </span>
              </div>
            </div>

            {/* Offline Mock Mode Toggle switch */}
            <div className="info-card">
              <span className="info-card-header">Controls</span>
              <div 
                className={`toggle-switch ${useMock ? 'active' : ''}`}
                onClick={() => setUseMock(!useMock)}
              >
                <div className="toggle-bg">
                  <div className="toggle-circle" />
                </div>
                <div>
                  <span style={{ display: 'block', color: 'white', fontSize: '12px', fontWeight: '500' }}>Use Offline Mock Mode</span>
                  <span style={{ fontSize: '10px', color: '#64748b' }}>Run local fallback recommendations</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Brand footer details */}
        <div style={{
          padding: '16px',
          borderRadius: '16px',
          background: 'linear-gradient(135deg, rgba(0, 210, 255, 0.03) 0%, rgba(157, 78, 221, 0.03) 100%)',
          border: '1px solid rgba(0, 210, 255, 0.08)'
        }}>
          <span style={{ fontSize: '12px', fontWeight: '600', color: '#00d2ff', display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '4px' }}>
            <Sparkles size={12} /> Pro discovery active
          </span>
          <span style={{ fontSize: '10px', color: '#94a3b8', lineHeight: '1.4', display: 'block' }}>
            Filters are applied deterministically to prevent hallucinations. Rationale generated by Gemini 3.5.
          </span>
        </div>
      </aside>

      {/* ── MAIN WORKSPACE ── */}
      <main className="main-workspace">
        
        {/* API Connection Error Alert */}
        {apiError && !isSearching && (
          <div className="alerts-container">
            <div className="alert-box">
              <div style={{ fontSize: '18px' }}>🛑</div>
              <div>
                <h4 className="alert-title">Configuration Exception</h4>
                <p className="alert-message">{apiError}</p>
              </div>
              <button onClick={() => setApiError('')} className="alert-close">
                <X size={16} />
              </button>
            </div>
          </div>
        )}

        <form onSubmit={handleSearch} className="glass-panel">
          <div className="filter-grid">
            
            {/* 1. Location Autocomplete */}
            <div ref={locationRef} className="autocomplete-container">
              <label className="input-label">1. Enter Location</label>
              <div className="relative">
                <span className="input-icon-left">
                  <MapPin size={16} />
                </span>
                <input
                  type="text"
                  placeholder="e.g. Indiranagar, Connaught Place"
                  value={locationInput}
                  onChange={(e) => {
                    setLocationInput(e.target.value);
                    setShowLocationDropdown(true);
                  }}
                  onFocus={() => setShowLocationDropdown(true)}
                  className="form-input pl-11"
                  required
                />
                {locationInput && (
                  <button
                    type="button"
                    onClick={() => {
                      setLocationInput('');
                      setShowLocationDropdown(true);
                    }}
                    className="input-clear-btn"
                  >
                    <X size={14} />
                  </button>
                )}
              </div>

              {showLocationDropdown && filteredCities.length > 0 && (
                <div className="suggestions-dropdown">
                  {filteredCities.map((city) => (
                    <div
                      key={city}
                      onClick={() => {
                        setLocationInput(city);
                        setShowLocationDropdown(false);
                      }}
                      className="suggestion-item"
                    >
                      📍 {city}
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* 2. Budget Selection */}
            <div>
              <label className="input-label">2. Budget Level</label>
              <div className="budget-grid">
                {["low", "medium", "high"].map((b) => (
                  <button
                    key={b}
                    type="button"
                    onClick={() => setBudgetBand(budgetBand === b ? null : b)}
                    className={`budget-btn ${budgetBand === b ? 'active' : ''}`}
                  >
                    {b}
                  </button>
                ))}
              </div>
            </div>

            {/* 3. Ratings Slider */}
            <div>
              <label className="input-label">3. Min Rating Threshold</label>
              <div className="rating-row">
                <div className="star-rating">
                  {[1, 2, 3, 4, 5].map((star) => (
                    <button
                      key={star}
                      type="button"
                      onClick={() => handleStarClick(star)}
                      className={`star-btn ${minRating >= star ? 'active' : ''}`}
                    >
                      <Star size={20} fill={minRating >= star ? "currentColor" : "none"} />
                    </button>
                  ))}
                </div>
                <span className="rating-badge-value">
                  {minRating.toFixed(1)} ★
                </span>
              </div>
            </div>

            {/* 4. Recommendation Count Stepper */}
            <div>
              <label className="input-label">4. Results Count (K)</label>
              <div className="stepper">
                <button
                  type="button"
                  onClick={() => handleKAdjust(-1)}
                  className="stepper-btn"
                  disabled={topK <= 1}
                >
                  <Minus size={14} />
                </button>
                <div className="stepper-value">{topK}</div>
                <button
                  type="button"
                  onClick={() => handleKAdjust(1)}
                  className="stepper-btn"
                  disabled={topK >= 10}
                >
                  <Plus size={14} />
                </button>
              </div>
            </div>

          </div>

          {/* Cuisine Search & Popular Chips */}
          <div className="form-group">
            <label className="input-label">5. Cuisine Specialty</label>
            <div className="cuisine-search-row">
              <div ref={cuisineRef} className="autocomplete-container">
                <div className="relative">
                  <span className="input-icon-left">
                    <Utensils size={16} />
                  </span>
                  <input
                    type="text"
                    placeholder="Search all cuisines..."
                    value={cuisineInput}
                    onChange={(e) => {
                      setCuisineInput(e.target.value);
                      setShowCuisineDropdown(true);
                      setSelectedCuisine('');
                    }}
                    onFocus={() => setShowCuisineDropdown(true)}
                    className="form-input pl-11"
                  />
                  {(cuisineInput || selectedCuisine) && (
                    <button
                      type="button"
                      onClick={() => {
                        setCuisineInput('');
                        setSelectedCuisine('');
                        setShowCuisineDropdown(true);
                      }}
                      className="input-clear-btn"
                    >
                      <X size={14} />
                    </button>
                  )}
                </div>

                {showCuisineDropdown && filteredCuisines.length > 0 && (
                  <div className="suggestions-dropdown">
                    {filteredCuisines.map((cuisine) => (
                      <div
                        key={cuisine}
                        onClick={() => {
                          setSelectedCuisine(cuisine);
                          setCuisineInput('');
                          setShowCuisineDropdown(false);
                        }}
                        className="suggestion-item"
                      >
                        🍲 {cuisine}
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div className="chips-container">
                {popularCuisineChips.map((c) => (
                  <button
                    key={c}
                    type="button"
                    onClick={() => handleCuisineChipClick(c)}
                    className={`cuisine-chip ${selectedCuisine === c ? 'active' : ''}`}
                  >
                    {c}
                  </button>
                ))}
              </div>
            </div>
            
            {selectedCuisine && (
              <div style={{ fontSize: '12px', color: '#94a3b8', display: 'flex', alignItems: 'center', gap: '6px', marginTop: '6px', paddingLeft: '4px' }}>
                <Info size={12} style={{ color: '#00d2ff' }} /> Active Cuisine filter: <strong style={{ color: 'white' }}>{selectedCuisine}</strong>
              </div>
            )}
          </div>

          {/* Special Requests tags and Textarea */}
          <div className="form-group">
            <label className="input-label">6. Special Requests & Ambience</label>
            <div className="chips-container" style={{ marginBottom: '12px' }}>
              {popularExtrasTags.map((tag) => (
                <button
                  key={tag}
                  type="button"
                  onClick={() => handleExtraTagClick(tag)}
                  className={`extra-tag ${selectedExtrasTags.has(tag) ? 'active' : ''}`}
                >
                  {tag}
                </button>
              ))}
            </div>
            <input
              type="text"
              placeholder="Any custom requests? e.g. Rooftop view with candle-light dinner..."
              value={customRequests}
              onChange={(e) => setCustomRequests(e.target.value)}
              className="form-input"
            />
          </div>

          {/* Search Trigger Button */}
          <div className="form-row-divided">
            <button
              type="submit"
              disabled={isSearching}
              className="submit-btn"
            >
              <Sparkles size={16} />
              {isSearching ? 'Analyzing Flavors...' : 'Generate Recommendations'}
            </button>
          </div>
        </form>

        {/* ── LOADER STATE ORB ── */}
        {isSearching && (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '80px 0' }}>
            <div className="ai-orb-container" style={{ marginBottom: '24px' }}>
              <div className="ai-orb loading" />
            </div>
            <h3 className="loader-title">Orchestrator Executing Pipeline</h3>
            <p className="loader-subtitle" style={{ animation: 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite' }}>Filtering Zomato Database & consulting Gemini...</p>
          </div>
        )}

        {/* ── RECOMMENDATIONS GRID ── */}
        {!isSearching && searchExecuted && (
          <div className="results-section">
            
            {/* Header info */}
            <div className="results-header">
              <div>
                <h2 className="results-title">
                  <Sparkles style={{ color: '#00d2ff' }} size={20} />
                  Top Recommended Restaurants
                </h2>
                <span className="results-subtitle">
                  Shortlisted {candidateCount} candidates in <strong style={{ color: '#00d2ff' }}>{latency.toFixed(2)} seconds</strong>
                </span>
              </div>
            </div>

            {/* AI Summary Block */}
            {aiSummary && (
              <div className="summary-panel">
                <span className="summary-header">AI Insights Executive Summary</span>
                <p className="summary-text">{aiSummary}</p>
              </div>
            )}

            {/* Empty list state */}
            {recommendations.length === 0 && (
              <div className="glass-card" style={{ textAlign: 'center', padding: '48px', borderStyle: 'dashed', borderColor: 'rgba(255, 165, 2, 0.2)' }}>
                <span style={{ fontSize: '36px', display: 'block', marginBottom: '16px' }}>🍽️</span>
                <h3 style={{ color: '#ffa502', fontFamily: 'var(--font-outfit)', fontWeight: '600', fontSize: '18px', marginBottom: '8px' }}>No Matching Restaurants</h3>
                <p style={{ color: '#cbd5e1', fontSize: '14px', maxWidth: '512px', margin: '0 auto', lineHeight: '1.6' }}>
                  No records match your exact filters. Try relaxing your rating threshold or broadening your location boundaries.
                </p>
              </div>
            )}

            {/* Cards layout */}
            <div className="cards-list">
              {recommendations.map((rec) => {
                const r = rec.restaurant;
                const score = getMatchScore(rec);
                const isSelected = selectedRecId === r.id;

                return (
                  <div 
                    key={r.id} 
                    className="restaurant-card-wrapper"
                    onClick={() => setSelectedRecId(isSelected ? null : r.id)}
                  >
                    <div className="rank-badge">RANK #{rec.rank}</div>
                    
                    <div className={`restaurant-card ${isSelected ? 'active' : ''}`}>
                      {/* Left: Cuisine themed image */}
                      <div className="card-img-wrapper">
                        {/* eslint-disable-next-line @next/next/no-img-element */}
                        <img 
                          src={getRestaurantImage(r.name, r.cuisines, r.id)} 
                          alt={r.name}
                          className="card-img"
                        />
                        <div className="card-match-badge">
                          <Award size={10} /> {score}% Match
                        </div>
                      </div>

                      {/* Right: Info and highlights */}
                      <div className="card-content">
                        <div>
                          {/* Heading row */}
                          <div className="card-info-header">
                            <div>
                              <h3 className="card-title">{r.name}</h3>
                              <span className="card-location">📍 {r.location}</span>
                            </div>

                            <div className="card-meta-badges">
                              <span className="rating-badge">⭐ {r.rating ? `${r.rating.toFixed(1)} ★` : 'NEW'}</span>
                              <span className="cost-badge">
                                {r.budget_band?.toUpperCase()} • {r.cost_for_two ? `₹${r.cost_for_two} for two` : 'Price N/A'}
                              </span>
                            </div>
                          </div>

                          {/* Cuisines badge row */}
                          <div className="card-cuisines-row">
                            {r.cuisines.map((c, idx) => (
                              <span key={idx} className="cuisine-badge">{c}</span>
                            ))}
                          </div>
                        </div>

                        {/* Rationale snippet */}
                        <div className="explanation-box">
                          <strong style={{ color: '#ff4757', fontWeight: '600', fontFamily: 'var(--font-outfit)', marginRight: '4px' }}>AI Rationale:</strong>
                          {rec.explanation}
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>

          </div>
        )}

      </main>

      {/* ── RIGHT INSIGHTS PANEL SLIDE DRAWER ── */}
      <AnimatePresence>
        {selectedRecId && selectedRec && (
          <motion.div
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'spring', damping: 25, stiffness: 200 }}
            className="drawer-overlay"
          >
            <div>
              {/* Header drawer controls */}
              <div className="drawer-header">
                <span className="drawer-header-title">
                  <Sparkles size={13} /> Gourmet AI Insights
                </span>
                <button 
                  onClick={() => setSelectedRecId(null)}
                  className="drawer-close-btn"
                >
                  <X size={15} />
                </button>
              </div>

              {/* Match Score Circle Graphic */}
              <div className="drawer-score-panel">
                <div className="drawer-circle-container">
                  <svg className="drawer-circle-svg">
                    <circle 
                      cx="56" cy="56" r="48" 
                      stroke="rgba(255, 255, 255, 0.03)"
                      strokeWidth="6"
                      fill="none"
                    />
                    <circle 
                      cx="56" cy="56" r="48" 
                      stroke="#00d2ff"
                      strokeWidth="6"
                      fill="none"
                      strokeDasharray={2 * Math.PI * 48}
                      strokeDashoffset={2 * Math.PI * 48 * (1 - getMatchScore(selectedRec) / 100)}
                      strokeLinecap="round"
                    />
                  </svg>
                  <div className="drawer-score-text">
                    <span className="drawer-score-num">{getMatchScore(selectedRec)}%</span>
                    <span className="drawer-score-label">Confidence</span>
                  </div>
                </div>
                <h4 className="drawer-rest-name">{selectedRec.restaurant.name}</h4>
                <span className="drawer-rest-loc">📍 {selectedRec.restaurant.location}</span>
              </div>

              {/* Highlights & details */}
              <div>
                <div className="drawer-section">
                  <span className="drawer-section-title">Match Highlights</span>
                  <div className="drawer-chips">
                    {selectedRec.match_highlights.map((h, idx) => (
                      <span 
                        key={idx} 
                        className="drawer-chip"
                      >
                        ⚡ {h}
                      </span>
                    ))}
                    {selectedRec.match_highlights.length === 0 && (
                      <span style={{ fontSize: '12px', color: '#64748b', fontStyle: 'italic' }}>No explicit match keywords found</span>
                    )}
                  </div>
                </div>

                <div className="drawer-section">
                  <span className="drawer-section-title">AI Summary Context</span>
                  <p className="drawer-context-box">
                    This restaurant matches your preferences because it's situated in <strong style={{ color: 'white' }}>{selectedRec.restaurant.location}</strong>
                    {selectedRec.restaurant.rating && <> with an exceptional rating of <strong style={{ color: '#ffb800' }}>{selectedRec.restaurant.rating} stars</strong></>}
                    {selectedRec.restaurant.cost_for_two && <>, with an estimated cost of <strong style={{ color: 'white' }}>₹{selectedRec.restaurant.cost_for_two} for two</strong></>}.
                  </p>
                </div>

                <div className="drawer-section">
                  <span className="drawer-section-title">Reasoning Breakdown</span>
                  <p className="drawer-desc-text">
                    {selectedRec.explanation}
                  </p>
                </div>
              </div>
            </div>

            {/* Quick action button */}
            <div className="form-row-divided">
              <a 
                href={`https://www.zomato.com/search?q=${encodeURIComponent(selectedRec.restaurant.name + ' ' + selectedRec.restaurant.location)}`}
                target="_blank" 
                rel="noreferrer"
                className="drawer-footer-btn"
              >
                <span>View on Zomato</span>
                <ArrowRight size={13} />
              </a>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

    </div>
  );
}

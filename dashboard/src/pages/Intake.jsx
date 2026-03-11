import React, { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { Search, Loader, CheckCircle } from 'lucide-react'
import RestaurantCard from '../components/RestaurantCard.jsx'

export default function Intake() {
  const navigate = useNavigate()
  const [url, setUrl] = useState('')
  const [lookupLoading, setLookupLoading] = useState(false)
  const [lookupError, setLookupError] = useState('')
  const [preview, setPreview] = useState(null)
  const [restaurants, setRestaurants] = useState([])
  const [standardizing, setStandardizing] = useState(false)
  const [standardizedOnce, setStandardizedOnce] = useState(false)
  const [toast, setToast] = useState('')

  const loadRestaurants = useCallback(async () => {
    try {
      const res = await fetch('/api/restaurants')
      if (res.ok) setRestaurants(await res.json())
    } catch (e) {}
  }, [])

  useEffect(() => { loadRestaurants() }, [loadRestaurants])

  const handleLookup = async () => {
    if (!url.trim()) return
    setLookupLoading(true)
    setLookupError('')
    setPreview(null)
    try {
      const res = await fetch('/api/lookup/url', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: url.trim() }),
      })
      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || 'Lookup failed')
      }
      setPreview(await res.json())
    } catch (e) {
      setLookupError(e.message)
    } finally {
      setLookupLoading(false)
    }
  }

  const handleSavePreview = async () => {
    if (!preview) return
    const res = await fetch('/api/restaurants', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(preview),
    })
    if (res.ok) {
      setPreview(null)
      setUrl('')
      loadRestaurants()
    } else {
      const err = await res.json()
      setLookupError(err.detail || 'Save failed')
    }
  }

  const handleUpdate = (updated) => {
    setRestaurants((prev) => prev.map((r) => (r.id === updated.id ? updated : r)))
  }

  const handleSubjectToggle = (updated) => {
    setRestaurants((prev) =>
      prev.map((r) => (r.id === updated.id ? updated : { ...r, is_subject: false }))
    )
  }

  const handleDelete = (id) => {
    setRestaurants((prev) => prev.filter((r) => r.id !== id))
  }

  const handleStandardize = async () => {
    setStandardizing(true)
    try {
      const res = await fetch('/api/standardize/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({}),
      })
      const data = await res.json()
      setStandardizedOnce(true)
      setToast(data.message || 'Standardization complete')
      setTimeout(() => setToast(''), 4000)
    } catch (e) {
      setToast('Standardization failed')
      setTimeout(() => setToast(''), 4000)
    } finally {
      setStandardizing(false)
    }
  }

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold text-slate-800 mb-1">Restaurant Intake</h1>
      <p className="text-sm text-slate-500 mb-6">Add up to 10 restaurants. Set one as your subject.</p>

      {/* URL Lookup */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-100 p-5 mb-6">
        <label className="block text-sm font-medium text-slate-700 mb-2">
          Paste a restaurant URL (website, Yelp, or Google Maps)
        </label>
        <div className="flex gap-2">
          <input
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleLookup()}
            placeholder="https://..."
            className="flex-1 border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300"
          />
          <button
            onClick={handleLookup}
            disabled={lookupLoading}
            className="bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-indigo-700 disabled:opacity-50 flex items-center gap-2 transition-colors"
          >
            {lookupLoading ? <Loader className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
            Look Up
          </button>
        </div>
        {lookupError && <p className="text-red-500 text-xs mt-2">{lookupError}</p>}
        <p className="text-xs text-slate-400 mt-2">Add up to 10 restaurants. One will be your subject.</p>

        {/* Preview Card */}
        {preview && (
          <div className="mt-4 p-4 bg-slate-50 rounded-lg border border-slate-200">
            <div className="flex items-start justify-between">
              <div>
                <p className="font-semibold text-slate-800">{preview.name || 'Unknown Restaurant'}</p>
                {preview.neighborhood && <p className="text-xs text-slate-500">{preview.neighborhood}</p>}
                {preview.address && <p className="text-xs text-slate-400">{preview.address}</p>}
                {preview.cuisine_type?.length > 0 && (
                  <p className="text-xs text-slate-400">{preview.cuisine_type.join(', ')}</p>
                )}
              </div>
              <div className="flex gap-2">
                {preview.google_stars && <span className="text-xs text-amber-500">⭐ {preview.google_stars} G</span>}
                {preview.yelp_stars && <span className="text-xs text-red-500">⭐ {preview.yelp_stars} Y</span>}
              </div>
            </div>
            <div className="flex gap-2 mt-3">
              <button
                onClick={handleSavePreview}
                className="bg-indigo-600 text-white px-3 py-1.5 rounded-lg text-xs font-medium hover:bg-indigo-700"
              >
                Add Restaurant
              </button>
              <button onClick={() => setPreview(null)} className="text-slate-400 text-xs hover:text-slate-600">
                Discard
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Restaurant Grid */}
      {restaurants.length === 0 ? (
        <div className="border-2 border-dashed border-slate-200 rounded-xl p-12 text-center">
          <p className="text-slate-400 text-sm">No restaurants yet. Paste a URL above to get started.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-24">
          {restaurants.map((r) => (
            <RestaurantCard
              key={r.id}
              restaurant={r}
              onUpdate={handleUpdate}
              onDelete={handleDelete}
              onSubjectToggle={handleSubjectToggle}
            />
          ))}
        </div>
      )}

      {/* Sticky Action Bar */}
      {restaurants.length >= 2 && (
        <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-slate-200 px-6 py-4 flex items-center justify-between shadow-lg">
          <span className="text-sm text-slate-500 font-medium">{restaurants.length} restaurants added</span>
          <button
            onClick={handleStandardize}
            disabled={standardizing}
            className="bg-slate-800 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-slate-900 disabled:opacity-50 flex items-center gap-2"
          >
            {standardizing ? <Loader className="w-4 h-4 animate-spin" /> : <CheckCircle className="w-4 h-4" />}
            Run Standardization
          </button>
          <button
            onClick={() => navigate('/comparison')}
            disabled={!standardizedOnce}
            className="bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-indigo-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            Go to Comparison →
          </button>
        </div>
      )}

      {/* Toast */}
      {toast && (
        <div className="fixed bottom-20 left-1/2 -translate-x-1/2 bg-slate-900 text-white text-sm px-4 py-2 rounded-full shadow-lg z-50">
          {toast}
        </div>
      )}
    </div>
  )
}

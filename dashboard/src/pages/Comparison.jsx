import React, { useState, useEffect, useCallback } from 'react'
import { Loader, RefreshCw } from 'lucide-react'
import InsightBanner from '../components/InsightBanner.jsx'
import PriceRankingTable from '../components/PriceRankingTable.jsx'

export default function Comparison() {
  const [restaurants, setRestaurants] = useState([])
  const [subject, setSubject] = useState(null)
  const [insight, setInsight] = useState(null)
  const [insightLoading, setInsightLoading] = useState(false)
  const [categories, setCategories] = useState([])
  const [activeCategory, setActiveCategory] = useState(null)
  const [generatingInsight, setGeneratingInsight] = useState(false)

  const loadRestaurants = useCallback(async () => {
    const res = await fetch('/api/restaurants')
    if (!res.ok) return
    const data = await res.json()
    setRestaurants(data)
    const sub = data.find((r) => r.is_subject) || data[0] || null
    setSubject(sub)
    return sub
  }, [])

  const loadCategories = useCallback(async () => {
    const res = await fetch('/api/comparison/categories')
    if (!res.ok) return
    const data = await res.json()
    setCategories(data)
    if (data.length > 0 && !activeCategory) setActiveCategory(data[0].category)
  }, [activeCategory])

  const loadInsight = useCallback(async (subjectId) => {
    if (!subjectId) return
    setInsightLoading(true)
    try {
      const res = await fetch(`/api/insights/latest?subject_restaurant_id=${subjectId}`)
      if (res.ok) setInsight(await res.json())
      else setInsight(null)
    } catch (e) {
      setInsight(null)
    } finally {
      setInsightLoading(false)
    }
  }, [])

  useEffect(() => {
    loadRestaurants().then((sub) => { if (sub) loadInsight(sub.id) })
    loadCategories()
  }, [])

  const handleSubjectChange = async (e) => {
    const id = e.target.value
    await fetch(`/api/restaurants/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ is_subject: true }),
    })
    const sub = restaurants.find((r) => r.id === id)
    setSubject(sub)
    setInsight(null)
    loadInsight(id)
  }

  const handleGenerateInsight = async () => {
    if (!subject) return
    setGeneratingInsight(true)
    try {
      const res = await fetch('/api/insights/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ subject_restaurant_id: subject.id }),
      })
      if (res.ok) setInsight(await res.json())
    } catch (e) {}
    finally { setGeneratingInsight(false) }
  }

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-slate-800">Price Comparison</h1>
        <button
          onClick={handleGenerateInsight}
          disabled={generatingInsight || !subject}
          className="flex items-center gap-2 bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-indigo-700 disabled:opacity-50 transition-colors"
        >
          {generatingInsight ? <Loader className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
          {insight ? 'Regenerate Insight' : 'Generate Insight'}
        </button>
      </div>

      {/* Insight Banner */}
      {insightLoading ? (
        <div className="flex items-center gap-2 text-sm text-slate-400 mb-6">
          <Loader className="w-4 h-4 animate-spin" /> Loading insight...
        </div>
      ) : insight ? (
        <InsightBanner insight={insight} />
      ) : (
        <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 mb-6 text-sm text-slate-400">
          No insight yet. Run standardization first, then click "Generate Insight".
        </div>
      )}

      {/* Subject Selector */}
      <div className="flex items-center gap-3 mb-6">
        <label className="text-sm font-medium text-slate-600 whitespace-nowrap">Comparing against:</label>
        <select
          value={subject?.id || ''}
          onChange={handleSubjectChange}
          className="border border-slate-200 rounded-lg px-3 py-1.5 text-sm text-slate-700 focus:outline-none focus:ring-2 focus:ring-indigo-300"
        >
          {restaurants.map((r) => (
            <option key={r.id} value={r.id}>{r.name}</option>
          ))}
        </select>
      </div>

      {/* Category Tabs */}
      {categories.length > 0 ? (
        <>
          <div className="flex gap-1 overflow-x-auto pb-1 mb-4 border-b border-slate-200">
            {categories.map((cat) => (
              <button
                key={cat.category}
                onClick={() => setActiveCategory(cat.category)}
                className={`px-4 py-2 text-sm font-medium whitespace-nowrap transition-colors rounded-t-lg ${
                  activeCategory === cat.category
                    ? 'text-indigo-600 border-b-2 border-indigo-600 font-semibold'
                    : 'text-slate-500 hover:text-slate-700'
                }`}
              >
                {cat.category}
                <span className="ml-1.5 text-xs bg-slate-100 text-slate-500 rounded-full px-1.5 py-0.5">
                  {cat.restaurant_count}
                </span>
              </button>
            ))}
          </div>

          {activeCategory && (
            <PriceRankingTable
              category={activeCategory}
              subjectRestaurantId={subject?.id}
            />
          )}
        </>
      ) : (
        <div className="text-center py-12 text-slate-400 text-sm">
          No comparison data yet. Add restaurants, upload menus, and run standardization first.
        </div>
      )}
    </div>
  )
}

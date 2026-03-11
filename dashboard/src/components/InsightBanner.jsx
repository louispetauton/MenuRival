import React from 'react'

export default function InsightBanner({ insight }) {
  if (!insight) return null
  const date = new Date(insight.date_generated).toLocaleDateString('en-US', {
    month: 'short', day: 'numeric', year: 'numeric'
  })
  return (
    <div className="bg-indigo-50 border border-indigo-200 rounded-xl p-6 mb-6">
      <h2 className="text-lg font-semibold text-indigo-900 mb-2">{insight.headline}</h2>
      <p className="text-sm text-indigo-800 mb-4">{insight.pricing_position}</p>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <h4 className="text-xs font-semibold text-indigo-700 uppercase tracking-wide mb-2">Opportunities</h4>
          <ul className="space-y-1">
            {(insight.opportunities || []).map((o, i) => (
              <li key={i} className="text-sm text-indigo-800 flex gap-2">
                <span className="text-indigo-400 mt-0.5">•</span>
                <span>{o}</span>
              </li>
            ))}
          </ul>
        </div>
        <div>
          <h4 className="text-xs font-semibold text-indigo-700 uppercase tracking-wide mb-2">Category Gaps</h4>
          <ul className="space-y-1">
            {(insight.gaps || []).map((g, i) => (
              <li key={i} className="text-sm text-indigo-800 flex gap-2">
                <span className="text-indigo-400 mt-0.5">•</span>
                <span>{g}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
      <p className="text-xs text-indigo-400 text-right mt-3">Generated {date}</p>
    </div>
  )
}

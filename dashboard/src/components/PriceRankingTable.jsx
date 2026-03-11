import React, { useEffect, useState } from 'react'
import { Loader } from 'lucide-react'

export default function PriceRankingTable({ category, subjectRestaurantId }) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!category) return
    setLoading(true)
    fetch(`/api/comparison/category/${encodeURIComponent(category)}`)
      .then((r) => r.json())
      .then((d) => { setData(d); setLoading(false) })
      .catch(() => setLoading(false))
  }, [category])

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader className="w-5 h-5 text-indigo-400 animate-spin" />
      </div>
    )
  }

  const items = data?.items || []

  if (items.length < 2) {
    return (
      <div className="text-center py-12 text-slate-400 text-sm">
        Not enough restaurants with {category} items to compare.
      </div>
    )
  }

  return (
    <div className="overflow-x-auto rounded-xl border border-slate-100">
      <table className="w-full text-sm">
        <thead>
          <tr className="bg-slate-50 text-left">
            <th className="px-4 py-3 font-semibold text-slate-500 w-12">Rank</th>
            <th className="px-4 py-3 font-semibold text-slate-500">Restaurant</th>
            <th className="px-4 py-3 font-semibold text-slate-500">Item Name</th>
            <th className="px-4 py-3 font-semibold text-slate-500 text-right">Price</th>
            <th className="px-4 py-3 font-semibold text-slate-500">Position</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-50">
          {items.map((item) => (
            <tr
              key={`${item.restaurant_id}-${item.item_name}`}
              className={item.is_subject ? 'bg-indigo-50' : 'bg-white hover:bg-slate-50'}
            >
              <td className="px-4 py-3 text-center text-base">{item.rank_label}</td>
              <td className={`px-4 py-3 font-medium ${item.is_subject ? 'text-indigo-700' : 'text-slate-800'}`}>
                {item.restaurant_name}
              </td>
              <td className="px-4 py-3 text-slate-600">{item.item_name}</td>
              <td className={`px-4 py-3 text-right font-semibold ${item.is_subject ? 'text-indigo-700' : 'text-slate-800'}`}>
                ${Number(item.price).toFixed(2)}
              </td>
              <td className="px-4 py-3 text-slate-500">{item.percentile_label}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

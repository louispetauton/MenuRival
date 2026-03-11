import React, { useState } from 'react'
import { Trash2, Star, Check, X } from 'lucide-react'
import MenuUploadSlot from './MenuUploadSlot.jsx'

const MENU_TYPES = [
  { key: 'breakfast', label: 'Breakfast' },
  { key: 'brunch', label: 'Brunch' },
  { key: 'lunch', label: 'Lunch' },
  { key: 'dinner', label: 'Dinner' },
  { key: 'drinks', label: 'Drinks' },
  { key: 'happy_hour', label: 'Happy Hour' },
  { key: 'tasting_menu', label: 'Tasting' },
]

function InlineEdit({ value, onSave, className = '' }) {
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState(value || '')
  if (!editing) {
    return (
      <span
        className={`cursor-pointer hover:underline decoration-dotted ${className}`}
        onClick={() => setEditing(true)}
      >
        {value || <span className="text-slate-300 italic">—</span>}
      </span>
    )
  }
  return (
    <span className="flex items-center gap-1">
      <input
        autoFocus
        value={draft}
        onChange={(e) => setDraft(e.target.value)}
        className="border border-indigo-300 rounded px-1 py-0.5 text-sm focus:outline-none focus:ring-1 focus:ring-indigo-400"
        onKeyDown={(e) => {
          if (e.key === 'Enter') { onSave(draft); setEditing(false) }
          if (e.key === 'Escape') setEditing(false)
        }}
      />
      <button onClick={() => { onSave(draft); setEditing(false) }}><Check className="w-3 h-3 text-emerald-500" /></button>
      <button onClick={() => setEditing(false)}><X className="w-3 h-3 text-red-400" /></button>
    </span>
  )
}

export default function RestaurantCard({ restaurant, onUpdate, onDelete, onSubjectToggle }) {
  const [confirmDelete, setConfirmDelete] = useState(false)

  const handleFieldUpdate = async (field, value) => {
    try {
      const res = await fetch(`/api/restaurants/${restaurant.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ [field]: value }),
      })
      if (!res.ok) return
      const updated = await res.json()
      if (onUpdate) onUpdate(updated)
    } catch (e) {
      console.error(e)
    }
  }

  const handleSubject = async () => {
    const res = await fetch(`/api/restaurants/${restaurant.id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ is_subject: true }),
    })
    if (res.ok) {
      const updated = await res.json()
      if (onSubjectToggle) onSubjectToggle(updated)
    }
  }

  const handleDelete = async () => {
    if (!confirmDelete) { setConfirmDelete(true); return }
    await fetch(`/api/restaurants/${restaurant.id}`, { method: 'DELETE' })
    if (onDelete) onDelete(restaurant.id)
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-100 overflow-hidden">
      {/* Header */}
      <div className="p-4 pb-2 flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <h3 className="font-semibold text-slate-800 text-sm truncate">
            <InlineEdit value={restaurant.name} onSave={(v) => handleFieldUpdate('name', v)} />
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            <InlineEdit value={restaurant.neighborhood} onSave={(v) => handleFieldUpdate('neighborhood', v)} />
          </p>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          {restaurant.google_stars && (
            <span className="flex items-center gap-0.5 text-xs text-amber-500 font-medium">
              <Star className="w-3 h-3 fill-amber-400 text-amber-400" /> {restaurant.google_stars} G
            </span>
          )}
          {restaurant.yelp_stars && (
            <span className="flex items-center gap-0.5 text-xs text-red-500 font-medium">
              <Star className="w-3 h-3 fill-red-400 text-red-400" /> {restaurant.yelp_stars} Y
            </span>
          )}
          {confirmDelete ? (
            <div className="flex gap-1">
              <button onClick={handleDelete} className="text-xs text-red-600 font-medium">Confirm</button>
              <button onClick={() => setConfirmDelete(false)} className="text-xs text-slate-400">Cancel</button>
            </div>
          ) : (
            <button onClick={handleDelete} className="text-slate-300 hover:text-red-400 transition-colors">
              <Trash2 className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      {/* Subject Toggle */}
      <div className="px-4 pb-2">
        <button
          onClick={handleSubject}
          className={`w-full text-xs py-1.5 rounded-lg font-medium transition-colors flex items-center justify-center gap-1.5 ${
            restaurant.is_subject
              ? 'bg-indigo-600 text-white'
              : 'bg-slate-100 text-slate-500 hover:bg-indigo-50 hover:text-indigo-600'
          }`}
        >
          {restaurant.is_subject && <Check className="w-3 h-3" />}
          {restaurant.is_subject ? 'Subject Restaurant' : 'Set as Subject Restaurant'}
        </button>
      </div>

      {/* Details */}
      <div className="px-4 pb-2 space-y-0.5">
        <p className="text-xs text-slate-500">
          <span className="font-medium text-slate-400">Addr: </span>
          <InlineEdit value={restaurant.address} onSave={(v) => handleFieldUpdate('address', v)} />
        </p>
        <p className="text-xs text-slate-500">
          <span className="font-medium text-slate-400">Phone: </span>
          <InlineEdit value={restaurant.phone} onSave={(v) => handleFieldUpdate('phone', v)} />
        </p>
        <p className="text-xs text-slate-500">
          <span className="font-medium text-slate-400">Web: </span>
          <InlineEdit value={restaurant.website_url} onSave={(v) => handleFieldUpdate('website_url', v)} />
        </p>
      </div>

      {/* Menu Uploads */}
      <div className="px-4 pb-4">
        <p className="text-xs font-medium text-slate-500 mb-2">Menu Uploads</p>
        <div className="grid grid-cols-2 gap-2">
          {MENU_TYPES.map((mt) => (
            <MenuUploadSlot
              key={mt.key}
              restaurantId={restaurant.id}
              menuType={mt.key}
              label={mt.label}
            />
          ))}
        </div>
      </div>
    </div>
  )
}

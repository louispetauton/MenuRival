import React from 'react'
import { Link, useLocation } from 'react-router-dom'

export default function NavBar() {
  const location = useLocation()
  const linkClass = (path) =>
    `text-sm font-medium transition-colors pb-1 ${
      location.pathname === path
        ? 'text-indigo-600 border-b-2 border-indigo-600'
        : 'text-slate-500 hover:text-slate-800'
    }`
  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-white shadow-sm h-16 flex items-center px-6">
      <span className="text-indigo-600 font-bold text-xl mr-auto">MenuRival</span>
      <div className="flex gap-6">
        <Link to="/" className={linkClass('/')}>Intake</Link>
        <Link to="/comparison" className={linkClass('/comparison')}>Comparison</Link>
      </div>
    </nav>
  )
}

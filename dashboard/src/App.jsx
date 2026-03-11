import React from 'react'
import { Routes, Route } from 'react-router-dom'
import NavBar from './components/NavBar.jsx'
import Intake from './pages/Intake.jsx'
import Comparison from './pages/Comparison.jsx'

export default function App() {
  return (
    <div className="min-h-screen bg-slate-50">
      <NavBar />
      <main className="pt-16">
        <Routes>
          <Route path="/" element={<Intake />} />
          <Route path="/comparison" element={<Comparison />} />
        </Routes>
      </main>
    </div>
  )
}

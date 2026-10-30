import { NavLink, Route, Routes } from 'react-router-dom'
import { GAME_NAME } from './lib/format'
import HowItWorks from './pages/HowItWorks'
import Play from './pages/Play'
import Results from './pages/Results'

export default function App() {
  return (
    <div className="app">
      <nav className="topbar">
        <span className="brand"><span className="brand-mark">₹</span> {GAME_NAME} <small>· RL</small></span>
        <div className="nav-links">
          <NavLink to="/" end>Play</NavLink>
          <NavLink to="/results">Results</NavLink>
          <NavLink to="/how-it-works">How it works</NavLink>
        </div>
      </nav>
      <Routes>
        <Route path="/" element={<Play />} />
        <Route path="/results" element={<Results />} />
        <Route path="/how-it-works" element={<HowItWorks />} />
      </Routes>
    </div>
  )
}

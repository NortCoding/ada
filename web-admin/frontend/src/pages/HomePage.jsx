import React from 'react'
import { Link } from 'react-router-dom'
import { useRoadmap } from '../hooks/useRoadmap'

function Card({ to, title, subtitle }) {
  return (
    <Link to={to} className="glass-panel landing-card" style={{ textDecoration: 'none', color: 'inherit' }}>
      <h3 style={{ margin: 0 }}>{title}</h3>
      <p style={{ margin: '0.4rem 0 0 0', color: 'var(--subtle)', fontSize: '0.9rem' }}>{subtitle}</p>
    </Link>
  )
}

export default function HomePage() {
  const { phase, goals } = useRoadmap()

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
      <div className="glass-card" style={{ padding: '1rem' }}>
        <div style={{ fontSize: '0.85rem', color: 'var(--subtle)' }}>Current ADA phase</div>
        <div style={{ fontSize: '1.4rem', fontWeight: 800 }}>{phase}</div>
        <div style={{ marginTop: 10, fontSize: '0.9rem', color: 'var(--subtle)' }}>Top priorities</div>
        <div style={{ marginTop: 6, display: 'flex', flexWrap: 'wrap', gap: 8 }}>
          {(goals || []).slice(0, 3).map((g, i) => (
            <span key={i} style={{ padding: '6px 10px', background: 'var(--muted)', borderRadius: 999, fontSize: '0.85rem' }}>{g}</span>
          ))}
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 12 }}>
        <Card to="/v2/developer" title="💻 Developer Workspace" subtitle="Chat + files + quick actions (safe)" />
        <Card to="/v2/business" title="📈 Business Workspace" subtitle="Opportunities + plans (practical)" />
        <Card to="/v2/research" title="🔬 Research Workspace" subtitle="Research chat + notes (minimal)" />
        <Card to="/v2/roadmap" title="🧭 Roadmap / Goals" subtitle="Phase, goals, what next" />
        <Card to="/v2/monitor" title="🖥️ System Monitor" subtitle="Real system state" />
      </div>
    </div>
  )
}


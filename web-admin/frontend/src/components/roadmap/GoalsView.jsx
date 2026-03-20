import React from 'react'
import { useRoadmap } from '../../hooks/useRoadmap'

export default function GoalsView() {
  const { loading, error, phase, goals, reload } = useRoadmap()

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', height: '100%' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 12 }}>
        <h2 style={{ margin: 0 }}>🧱 Goals</h2>
        <button className="secondary" onClick={reload} disabled={loading} style={{ padding: '4px 8px', fontSize: '0.8rem' }}>
          {loading ? 'Cargando...' : '↻ Recargar'}
        </button>
      </div>

      {error && (
        <div style={{ padding: '0.75rem', background: 'rgba(239, 68, 68, 0.08)', borderRadius: 8, color: 'var(--danger)' }}>
          {error}
        </div>
      )}

      <div className="glass-card" style={{ padding: '1rem' }}>
        <div style={{ fontSize: '0.85rem', color: 'var(--subtle)' }}>Fase actual</div>
        <div style={{ fontSize: '1.2rem', fontWeight: 700 }}>{phase}</div>
      </div>

      <div className="glass-card" style={{ padding: '1rem', flex: 1, overflow: 'auto' }}>
        <div style={{ fontSize: '0.85rem', color: 'var(--subtle)', marginBottom: 8 }}>Objetivos actuales</div>
        {loading ? (
          <div style={{ color: 'var(--subtle)' }}>Cargando objetivos...</div>
        ) : goals.length ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {goals.map((g, i) => (
              <div key={i} style={{ padding: '0.5rem 0.75rem', background: 'var(--muted)', borderRadius: 10 }}>
                {g}
              </div>
            ))}
          </div>
        ) : (
          <div style={{ color: 'var(--subtle)' }}>No pude parsear objetivos desde el ROADMAP.</div>
        )}
      </div>
    </div>
  )
}


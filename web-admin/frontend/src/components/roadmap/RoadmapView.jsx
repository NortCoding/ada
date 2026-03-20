import React from 'react'
import { useRoadmap } from '../../hooks/useRoadmap'

export default function RoadmapView() {
  const { loading, error, roadmapText, reload } = useRoadmap()

  return (
    <div className="glass-card" style={{ padding: '1rem', overflow: 'auto', height: '100%' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 12 }}>
        <h2 style={{ margin: 0 }}>🧭 Roadmap</h2>
        <button className="secondary" onClick={reload} disabled={loading} style={{ padding: '4px 8px', fontSize: '0.8rem' }}>
          {loading ? 'Cargando...' : '↻ Recargar'}
        </button>
      </div>

      {error && (
        <div style={{ marginTop: 12, padding: '0.75rem', background: 'rgba(239, 68, 68, 0.08)', borderRadius: 8, color: 'var(--danger)' }}>
          {error}
        </div>
      )}

      <pre style={{ marginTop: 12, fontSize: '0.8rem', whiteSpace: 'pre-wrap' }}>
        {roadmapText || (loading ? 'Cargando...' : 'No disponible')}
      </pre>
    </div>
  )
}


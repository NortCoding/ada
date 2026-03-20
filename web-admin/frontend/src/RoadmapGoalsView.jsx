import React, { useEffect, useState, useCallback } from 'react'
import { api } from './api/client'

function extractGoals(roadmapText) {
  if (!roadmapText) return []
  const lines = roadmapText.split('\n')
  const startIdx = lines.findIndex((l) => l.includes('## OBJETIVOS ACTUALES'))
  if (startIdx === -1) return []

  // End at "OBJETIVOS FUTUROS" or "## REGLAS" as a best-effort.
  let endIdx = lines.findIndex((l, i) => i > startIdx && l.includes('OBJETIVOS FUTUROS'))
  if (endIdx === -1) endIdx = lines.findIndex((l, i) => i > startIdx && l.includes('## REGLAS'))
  if (endIdx === -1) endIdx = lines.length

  const goals = []
  for (const l of lines.slice(startIdx, endIdx)) {
    const s = (l || '').trim()
    if (!s) continue
    // Capture "1. Crear..." and "- ..." bullets.
    if (/^\d+\.\s+/.test(s)) goals.push(s)
    if (s.startsWith('- ')) goals.push(s)
  }
  return goals
}

function extractPhase(roadmapText) {
  if (!roadmapText) return 'FASE desconocida'
  const m = roadmapText.match(/FASE\s*([0-9]+)/i)
  if (!m) return 'FASE desconocida'
  return `FASE ${m[1]}`
}

export default function RoadmapGoalsView() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [roadmapText, setRoadmapText] = useState('')

  const load = useCallback(() => {
    setLoading(true)
    setError(null)
    api('/fs/read?path=ada/ROADMAP.md')
      .then((d) => setRoadmapText(d && d.content ? d.content : ''))
      .catch((e) => setError(e.message || 'No disponible'))
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    load()
  }, [load])

  const phase = extractPhase(roadmapText)
  const goals = extractGoals(roadmapText)

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: '1rem', alignItems: 'center' }}>
        <h3 style={{ margin: 0 }}>🧱 Roadmap / Goals</h3>
        <button className="secondary" onClick={load} disabled={loading} style={{ padding: '4px 8px', fontSize: '0.8rem' }}>
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

      <div className="glass-card" style={{ padding: '1rem' }}>
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


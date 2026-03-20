import { useCallback, useEffect, useMemo, useState } from 'react'
import { api } from '../api/client'

function extractPhase(roadmapText) {
  if (!roadmapText) return 'FASE desconocida'
  const m = roadmapText.match(/FASE\s*([0-9]+)/i)
  if (!m) return 'FASE desconocida'
  return `FASE ${m[1]}`
}

function extractGoals(roadmapText) {
  if (!roadmapText) return []
  const lines = roadmapText.split('\n')
  const startIdx = lines.findIndex((l) => l.includes('## OBJETIVOS ACTUALES'))
  if (startIdx === -1) return []
  let endIdx = lines.findIndex((l, i) => i > startIdx && l.includes('OBJETIVOS FUTUROS'))
  if (endIdx === -1) endIdx = lines.findIndex((l, i) => i > startIdx && l.includes('## REGLAS'))
  if (endIdx === -1) endIdx = lines.length

  const goals = []
  for (const l of lines.slice(startIdx, endIdx)) {
    const s = (l || '').trim()
    if (!s) continue
    if (/^\d+\.\s+/.test(s)) goals.push(s)
    if (s.startsWith('- ')) goals.push(s)
  }
  return goals
}

export function useRoadmap() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [roadmapText, setRoadmapText] = useState('')

  const reload = useCallback(() => {
    setLoading(true)
    setError(null)
    api('/fs/read?path=ADA/ada/ROADMAP.md')
      .then((d) => setRoadmapText((d && d.content) || ''))
      .catch((e) => setError(e.message || 'No disponible'))
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    reload()
  }, [reload])

  const phase = useMemo(() => extractPhase(roadmapText), [roadmapText])
  const goals = useMemo(() => extractGoals(roadmapText), [roadmapText])

  return { loading, error, roadmapText, phase, goals, reload }
}


import React, { useEffect, useState } from 'react'
import { api } from '../../api/client'

function parseProgress(text) {
  if (!text) return []
  const lines = text.split('\n')
  const items = []
  for (const l of lines) {
    const m = l.match(/^- \[(.+?)\] (.+)$/)
    if (m) items.push({ ts: m[1], text: m[2] })
  }
  return items
}

export default function RecentActivityLog({ extraItems = [] }) {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [items, setItems] = useState([])

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)
    api('/fs/read?path=ada/memory/progress.md')
      .then((d) => {
        if (cancelled) return
        const text = (d && d.content) || ''
        setItems(parseProgress(text).slice(0, 12))
      })
      .catch((e) => !cancelled && setError(e.message || 'No disponible'))
      .finally(() => !cancelled && setLoading(false))
    return () => {
      cancelled = true
    }
  }, [])

  const merged = [...(extraItems || []), ...(items || [])].slice(0, 12)

  if (loading && !(extraItems && extraItems.length)) return <div style={{ color: 'var(--subtle)' }}>Loading activity…</div>
  if (error) return <div style={{ color: 'var(--subtle)' }}>Activity not available.</div>
  if (!merged.length) return <div style={{ color: 'var(--subtle)' }}>No activity yet.</div>

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      {merged.map((it, idx) => (
        <div key={idx} style={{ padding: '8px 10px', background: 'var(--muted)', borderRadius: 10, fontSize: '0.85rem' }}>
          <div style={{ color: 'var(--subtle)', fontSize: '0.75rem' }}>{it.ts}</div>
          <div>{it.text}</div>
        </div>
      ))}
    </div>
  )
}


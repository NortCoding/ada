import React from 'react'

const colors = {
  pending: { bg: 'rgba(255, 184, 0, 0.12)', fg: 'var(--text)' },
  running: { bg: 'rgba(11, 116, 255, 0.12)', fg: 'var(--text)' },
  completed: { bg: 'rgba(16, 185, 129, 0.14)', fg: 'var(--text)' },
  failed: { bg: 'rgba(239, 68, 68, 0.12)', fg: 'var(--text)' },
}

export default function TaskStatusBadge({ status }) {
  const s = status || 'pending'
  const c = colors[s] || colors.pending
  return (
    <span style={{ padding: '4px 8px', borderRadius: 999, background: c.bg, color: c.fg, fontSize: '0.8rem', fontWeight: 700 }}>
      {s.toUpperCase()}
    </span>
  )
}


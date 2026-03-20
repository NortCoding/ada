import React from 'react'
import TaskStatusBadge from './TaskStatusBadge'

function fmtTime(iso) {
  try {
    const d = new Date(iso)
    return d.toLocaleTimeString()
  } catch (e) {
    return ''
  }
}

export default function TaskList({ tasks }) {
  if (!tasks?.length) {
    return (
      <div style={{ color: 'var(--subtle)', fontSize: '0.9rem' }}>
        No tasks yet. Use quick actions to create your first task.
      </div>
    )
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
      {tasks.slice(0, 8).map((t) => (
        <div key={t.id} className="glass-panel" style={{ padding: '0.9rem', display: 'flex', flexDirection: 'column', gap: 6 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', gap: 10, alignItems: 'center' }}>
            <div style={{ fontWeight: 800 }}>{t.title}</div>
            <TaskStatusBadge status={t.status} />
          </div>
          <div style={{ fontSize: '0.85rem', color: 'var(--subtle)' }}>
            {t.type} · created {fmtTime(t.createdAt)}
          </div>
          {t.error && <div style={{ color: 'var(--danger)', fontSize: '0.85rem' }}>{t.error}</div>}
        </div>
      ))}
    </div>
  )
}


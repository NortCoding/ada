import React, { useEffect, useState } from 'react'
import { api } from '../../api/client'

export default function TopBar() {
  const [agentConnected, setAgentConnected] = useState(false)

  useEffect(() => {
    let cancelled = false
    const ping = () =>
      api('/agent/health')
        .then(() => !cancelled && setAgentConnected(true))
        .catch(() => !cancelled && setAgentConnected(false))
    ping()
    const t = setInterval(ping, 15000)
    return () => {
      cancelled = true
      clearInterval(t)
    }
  }, [])

  return (
    <header style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 14px', borderBottom: '1px solid var(--border)', background: 'var(--panel)' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <div style={{ width: 10, height: 10, borderRadius: '50%', background: agentConnected ? 'var(--success)' : 'var(--muted)' }} />
        <div style={{ fontWeight: 700 }}>System</div>
        <div style={{ fontSize: '0.85rem', color: 'var(--subtle)' }}>{agentConnected ? 'agent-core online' : 'agent-core offline'}</div>
      </div>

      <div style={{ fontSize: '0.85rem', color: 'var(--subtle)' }}>
        UI v2 (incremental)
      </div>
    </header>
  )
}


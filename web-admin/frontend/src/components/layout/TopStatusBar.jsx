import React, { useEffect, useMemo, useState } from 'react'
import { api } from '../../api/client'

function Chip({ label, value }) {
  return (
    <div style={{ display: 'flex', gap: 6, alignItems: 'center', padding: '6px 10px', borderRadius: 999, background: 'var(--muted)', border: '1px solid var(--border)' }}>
      <span style={{ fontSize: '0.75rem', color: 'var(--subtle)', fontWeight: 700 }}>{label}</span>
      <span style={{ fontSize: '0.85rem', fontWeight: 800 }}>{value}</span>
    </div>
  )
}

export default function TopStatusBar({ currentProject = 'ADA', workspaceKey = 'developer', executionMode = false, adaStatus = 'idle' }) {
  const [agentConnected, setAgentConnected] = useState(false)
  const [agentStatus, setAgentStatus] = useState(null)

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

  useEffect(() => {
    let cancelled = false
    api('/agent/status')
      .then((d) => !cancelled && setAgentStatus(d))
      .catch(() => !cancelled && setAgentStatus(null))
    return () => { cancelled = true }
  }, [])

  const activeModel = useMemo(() => {
    const d = agentStatus
    if (!d || typeof d !== 'object') return 'unknown'
    return d.model || d.active_model || d.ollama_model || 'unknown'
  }, [agentStatus])

  const statusDot = agentConnected ? 'var(--success)' : 'var(--danger)'

  return (
    <header style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 14px', borderBottom: '1px solid var(--border)', background: 'var(--panel)' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <div style={{ width: 10, height: 10, borderRadius: '50%', background: statusDot }} />
        <div style={{ fontWeight: 900 }}>ADA</div>
        <div style={{ fontSize: '0.85rem', color: 'var(--subtle)' }}>{agentConnected ? 'online' : 'offline'}</div>
      </div>

      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, justifyContent: 'flex-end' }}>
        <Chip label="project" value={currentProject} />
        <Chip label="workspace" value={workspaceKey} />
        <Chip label="status" value={adaStatus} />
        <Chip label="exec" value={executionMode ? 'ON' : 'OFF'} />
        <Chip label="model" value={activeModel} />
      </div>
    </header>
  )
}


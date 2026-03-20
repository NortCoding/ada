import React from 'react'

export default function SystemMonitorPage({ api, onBack, systemMonitor, setSystemMonitor }) {
  const memoryUsage = systemMonitor?.memory_usage_percent || 0
  const cpuUsage = systemMonitor?.cpu_usage_percent || 0
  const dbStatus = systemMonitor?.services?.db || 'offline'
  const taskStatus = systemMonitor?.services?.task_runner || 'offline'

  return (
    <div className="app-layout" style={{ gridTemplateColumns: 'minmax(0, 1fr)', padding: '2rem', overflow: 'auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <button type="button" className="secondary" onClick={onBack}>← Dashboard</button>
          <h1 style={{ margin: 0, fontSize: '1.8rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>🖥️ System Monitor</h1>
        </div>
        <button
          className="primary"
          onClick={() =>
            api('/system/monitor')
              .then(setSystemMonitor)
              .catch(() => setSystemMonitor({ error: 'No disponible' }))
          }
        >
          ↻ Actualizar Estado
        </button>
      </div>

      {!systemMonitor ? (
        <div className="glass-panel" style={{ padding: '3rem', textAlign: 'center' }}>Cargando datos de telemetría de A.D.A...</div>
      ) : systemMonitor?.error ? (
        <div className="glass-panel" style={{ padding: '1.5rem', color: 'var(--danger)' }}>
          {systemMonitor.error}
        </div>
      ) : (
        <>
          <h3 style={{ marginBottom: '1rem' }}>Recursos de Hardware (Host)</h3>
          <div className="monitor-grid">
            <div className="glass-panel monitor-card animate-fade-in">
              <div className="monitor-label">CPU Usage</div>
              <div className="monitor-value" style={{ color: cpuUsage > 80 ? 'var(--danger)' : 'var(--accent)' }}>{cpuUsage}%</div>
              <div style={{ width: '100%', height: '6px', background: 'var(--border)', borderRadius: '3px', marginTop: '10px', overflow: 'hidden' }}>
                <div style={{ width: `${cpuUsage}%`, height: '100%', background: cpuUsage > 80 ? 'var(--danger)' : 'var(--accent)', transition: 'width 0.5s ease' }} />
              </div>
            </div>

            <div className="glass-panel monitor-card animate-fade-in" style={{ animationDelay: '0.1s' }}>
              <div className="monitor-label">Memory Mapping</div>
              <div className="monitor-value" style={{ color: memoryUsage > 80 ? 'var(--danger)' : 'var(--accent)' }}>{memoryUsage}%</div>
              <div style={{ width: '100%', height: '6px', background: 'var(--border)', borderRadius: '3px', marginTop: '10px', overflow: 'hidden' }}>
                <div style={{ width: `${memoryUsage}%`, height: '100%', background: memoryUsage > 80 ? 'var(--danger)' : 'var(--accent)', transition: 'width 0.5s ease' }} />
              </div>
            </div>

            <div className="glass-panel monitor-card animate-fade-in" style={{ animationDelay: '0.2s' }}>
              <div className="monitor-label">Disk Storage</div>
              <div className="monitor-value" style={{ color: 'var(--text)' }}>
                {systemMonitor?.disk_usage?.percent ? `${systemMonitor.disk_usage.percent}%` : 'N/A'}
              </div>
              {systemMonitor?.disk_usage?.percent && (
                <div style={{ width: '100%', height: '6px', background: 'var(--border)', borderRadius: '3px', marginTop: '10px', overflow: 'hidden' }}>
                  <div style={{ width: `${systemMonitor.disk_usage.percent}%`, height: '100%', background: 'var(--text)', transition: 'width 0.5s ease' }} />
                </div>
              )}
            </div>
          </div>

          <h3 style={{ marginTop: '3rem', marginBottom: '1rem' }}>Salud de Microservicios A.D.A</h3>
          <div className="monitor-grid">
            <div className="glass-panel monitor-card animate-fade-in" style={{ flexDirection: 'row', justifyContent: 'space-between', padding: '1.2rem 2rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <div className={`status-dot ${dbStatus === 'ok' ? 'online' : 'offline'}`} />
                <strong style={{ fontSize: '1.1rem' }}>Vectores & Storage (Postgres)</strong>
              </div>
              <span className={`badge ${dbStatus === 'ok' ? 'badge-success' : 'badge-warn'}`}>{dbStatus === 'ok' ? 'ONLINE' : 'OFFLINE'}</span>
            </div>

            <div className="glass-panel monitor-card animate-fade-in" style={{ flexDirection: 'row', justifyContent: 'space-between', padding: '1.2rem 2rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <div className={`status-dot ${taskStatus === 'ok' ? 'online' : 'offline'}`} />
                <strong style={{ fontSize: '1.1rem' }}>Decision Engine & Sandbox</strong>
              </div>
              <span className={`badge ${taskStatus === 'ok' ? 'badge-success' : 'badge-warn'}`}>{taskStatus === 'ok' ? 'ONLINE' : 'OFFLINE'}</span>
            </div>
          </div>

          <div className="glass-panel animate-fade-in" style={{ marginTop: '3rem', padding: '1.5rem' }}>
            <h4 style={{ marginTop: 0, marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span>📡</span> Raw Telemetry Stream
            </h4>
            <div style={{ background: '#1e1e24', borderRadius: '8px', padding: '1rem', overflowX: 'auto', border: '1px solid rgba(255,255,255,0.05)' }}>
              <pre style={{ margin: 0, fontSize: '0.75rem', color: '#a3b8cc', fontFamily: 'var(--font-mono)' }}>{JSON.stringify(systemMonitor, null, 2)}</pre>
            </div>
          </div>
        </>
      )}
    </div>
  )
}


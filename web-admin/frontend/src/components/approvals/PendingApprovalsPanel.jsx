import React from 'react'

function PreviewBlock({ preview }) {
  if (!preview) return null
  return (
    <pre style={{ marginTop: 10, fontSize: '0.75rem', whiteSpace: 'pre-wrap', background: 'rgba(0,0,0,0.05)', padding: 10, borderRadius: 10 }}>
      {typeof preview === 'string' ? preview : JSON.stringify(preview, null, 2)}
    </pre>
  )
}

function ResultBlock({ result, error }) {
  if (!result && !error) return null
  return (
    <pre style={{ marginTop: 10, fontSize: '0.75rem', whiteSpace: 'pre-wrap', background: 'rgba(0,0,0,0.06)', padding: 10, borderRadius: 10 }}>
      {error ? `ERROR: ${error}` : typeof result === 'string' ? result : JSON.stringify(result, null, 2)}
    </pre>
  )
}

export default function PendingApprovalsPanel({ pending, onApprove, onReject }) {
  if (!pending?.length) {
    return <div style={{ color: 'var(--subtle)', fontSize: '0.9rem' }}>No pending approvals.</div>
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      {pending.slice(0, 5).map((a) => (
        <div key={a.id} className="glass-panel" style={{ padding: '1rem' }}>
          <div style={{ fontWeight: 900 }}>{a.title}</div>
          <div style={{ color: 'var(--subtle)', fontSize: '0.85rem', marginTop: 4 }}>{a.kind}</div>
          <div style={{ color: 'var(--subtle)', fontSize: '0.8rem', marginTop: 4 }}>
            status: <span style={{ fontWeight: 800 }}>{a.status}</span>
          </div>
          <PreviewBlock preview={a.preview} />
          <ResultBlock result={a.result} error={a.error} />
          <div style={{ display: 'flex', gap: 10, marginTop: 10 }}>
            <button disabled={a.status === 'executing'} onClick={() => onApprove(a.id)} style={{ padding: '6px 10px', fontSize: '0.85rem' }}>
              {a.status === 'executing' ? 'Executing…' : 'Approve'}
            </button>
            <button disabled={a.status === 'executing'} className="secondary" onClick={() => onReject(a.id)} style={{ padding: '6px 10px', fontSize: '0.85rem' }}>
              Reject
            </button>
          </div>
        </div>
      ))}
    </div>
  )
}


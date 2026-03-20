import React, { useEffect, useRef, useState } from 'react'
import ChatPane from '../components/ChatPane'
import { api } from '../api/client'

function OpportunityList({ items }) {
  if (!items?.length) return <div style={{ color: 'var(--subtle)' }}>No opportunities loaded yet.</div>
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
      {items.map((o) => (
        <div key={o.id} className="glass-panel" style={{ padding: '1rem' }}>
          <div style={{ fontWeight: 800 }}>{o.title}</div>
          <div style={{ color: 'var(--subtle)', marginTop: 6, fontSize: '0.9rem' }}>{o.why}</div>
          <div style={{ marginTop: 8, fontSize: '0.85rem', color: 'var(--subtle)' }}>
            speed={o.speed} · difficulty={o.difficulty} · revenue={o.revenue_potential} · alignment={o.alignment}
          </div>
        </div>
      ))}
    </div>
  )
}

export default function BusinessWorkspace() {
  const [theme, setTheme] = useState(() => {
    try { return localStorage.getItem('ada_theme') || 'dark' } catch (e) { return 'dark' }
  })
  useEffect(() => {
    try { document.documentElement.setAttribute('data-theme', theme); localStorage.setItem('ada_theme', theme) } catch (e) {}
  }, [theme])

  const [executionMode, setExecutionMode] = useState(false)
  const [chatMessage, setChatMessage] = useState('')
  const [chatHistory, setChatHistory] = useState([{ role: 'ada', text: 'Business workspace listo. ¿Buscamos oportunidades realistas?' }])
  const [loading, setLoading] = useState(false)
  const [agentConnected, setAgentConnected] = useState(false)
  const [businessGoals, setBusinessGoals] = useState('')
  const [opps, setOpps] = useState([])

  const chatEndRef = useRef(null)
  const chatInputRef = useRef(null)

  useEffect(() => {
    api('/agent/health').then(() => setAgentConnected(true)).catch(() => setAgentConnected(false))
    // Load BUSINESS_GOALS.md via FS API (if available)
    api('/fs/read?path=ADA/ada/BUSINESS_GOALS.md')
      .then((d) => setBusinessGoals((d && d.content) || ''))
      .catch(() => setBusinessGoals('BUSINESS_GOALS.md not available'))
  }, [])

  const sendChat = () => {
    const msg = (chatMessage || '').trim()
    if (!msg) return
    setChatMessage('')
    if (chatInputRef.current) chatInputRef.current.textContent = ''
    setChatHistory((h) => [...h, { role: 'user', text: msg }])
    setLoading(true)

    const payload = {
      message: msg,
      use_ollama: true,
      history: chatHistory.map((m) => ({ role: m.role, content: typeof m.text === 'string' ? m.text : '' })),
      agent_type: 'business',
      execution_mode: !!executionMode,
    }

    api('/chat', { method: 'POST', body: JSON.stringify(payload) })
      .then((res) => setChatHistory((h) => [...h, { role: 'ada', text: res.response, brain: res.brain }]))
      .catch((e) => setChatHistory((h) => [...h, { role: 'ada', text: `Error: ${e.message}` }]))
      .finally(() => setLoading(false))
  }

  const loadOpportunities = () => {
    // Keep it simple: seed list (no income simulation) and encourage validation.
    setOpps([
      { id: 'kit_debug_cli', title: 'Debugging starter kit (templates + playbooks)', speed: 9, difficulty: 4, revenue_potential: 7, alignment: 9, why: 'Fast to package; verifiable via CLI evidence.' },
      { id: 'cli_snippets', title: 'CLI automation snippets package', speed: 8, difficulty: 5, revenue_potential: 6, alignment: 8, why: 'Directly leverages analyze/create/fix/run primitives.' },
      { id: 'roadmap_workflow', title: 'Roadmap-to-tasks workflow template', speed: 7, difficulty: 4, revenue_potential: 5, alignment: 7, why: 'Matches roadmap-driven, proposal-only evolution.' },
    ])
  }

  return (
    <div className="app-layout">
      <ChatPane
        executionMode={executionMode}
        onToggleExecutionMode={() => setExecutionMode((v) => !v)}
        theme={theme}
        onToggleTheme={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
        agentConnected={agentConnected}
        loading={loading}
        chatHistory={chatHistory}
        chatMessage={chatMessage}
        setChatMessage={setChatMessage}
        onSendChat={sendChat}
        chatInputRef={chatInputRef}
        chatEndRef={chatEndRef}
      />

      <section className="pane pane-code" aria-label="Opportunities">
        <div className="pane-content" style={{ padding: '1rem', overflow: 'auto', height: '100%' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 12 }}>
            <h3 style={{ margin: 0 }}>📈 Opportunities</h3>
            <button className="secondary" onClick={loadOpportunities}>Load</button>
          </div>
          <div style={{ marginTop: 12 }}>
            <OpportunityList items={opps} />
          </div>
        </div>
      </section>

      <section className="pane pane-preview" aria-label="Business goals">
        <div className="pane-content" style={{ padding: '1rem', overflow: 'auto', height: '100%' }}>
          <h3 style={{ marginTop: 0 }}>🎯 Business goals</h3>
          <pre style={{ fontSize: '0.8rem', whiteSpace: 'pre-wrap' }}>{businessGoals}</pre>
          <div style={{ marginTop: 12, color: 'var(--subtle)', fontSize: '0.85rem' }}>
            Nota: aquí no simulamos ingresos. Proponemos y luego validamos con evidencia.
          </div>
        </div>
      </section>
    </div>
  )
}


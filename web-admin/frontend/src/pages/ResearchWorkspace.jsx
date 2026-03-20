import React, { useEffect, useRef, useState } from 'react'
import ChatPane from '../components/ChatPane'
import { api } from '../api/client'

export default function ResearchWorkspace() {
  const [theme, setTheme] = useState(() => {
    try { return localStorage.getItem('ada_theme') || 'dark' } catch (e) { return 'dark' }
  })
  useEffect(() => {
    try { document.documentElement.setAttribute('data-theme', theme); localStorage.setItem('ada_theme', theme) } catch (e) {}
  }, [theme])

  const [executionMode, setExecutionMode] = useState(false)
  const [chatMessage, setChatMessage] = useState('')
  const [chatHistory, setChatHistory] = useState([{ role: 'ada', text: 'Research workspace listo. ¿Qué investigamos?' }])
  const [loading, setLoading] = useState(false)
  const [agentConnected, setAgentConnected] = useState(false)
  const [notes, setNotes] = useState('')

  const chatEndRef = useRef(null)
  const chatInputRef = useRef(null)

  useEffect(() => {
    api('/agent/health').then(() => setAgentConnected(true)).catch(() => setAgentConnected(false))
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
      agent_type: 'research',
      execution_mode: !!executionMode,
    }

    api('/chat', { method: 'POST', body: JSON.stringify(payload) })
      .then((res) => {
        setChatHistory((h) => [...h, { role: 'ada', text: res.response, brain: res.brain }])
        // Best-effort: append summary to notes (no persistence yet).
        setNotes((n) => (n ? n + '\n\n' : '') + (res.response || '').slice(0, 800))
      })
      .catch((e) => setChatHistory((h) => [...h, { role: 'ada', text: `Error: ${e.message}` }]))
      .finally(() => setLoading(false))
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

      <section className="pane pane-code" aria-label="Research notes">
        <div className="pane-content" style={{ padding: '1rem', overflow: 'auto', height: '100%' }}>
          <h3 style={{ marginTop: 0 }}>🧾 Notes</h3>
          <textarea value={notes} onChange={(e) => setNotes(e.target.value)} rows={20} />
          <div style={{ marginTop: 10, fontSize: '0.85rem', color: 'var(--subtle)' }}>
            Guardado: por ahora solo local (estado UI). Próximo paso: persistir en `ada/memory/`.
          </div>
        </div>
      </section>

      <section className="pane pane-preview" aria-label="Research summary">
        <div className="pane-content" style={{ padding: '1rem', overflow: 'auto', height: '100%' }}>
          <h3 style={{ marginTop: 0 }}>🔬 Summary</h3>
          <div style={{ fontSize: '0.9rem', color: 'var(--subtle)' }}>
            Usa el chat para generar resúmenes verificables. Evita endpoints no soportados.
          </div>
        </div>
      </section>
    </div>
  )
}


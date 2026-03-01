import React, { useState, useEffect, useCallback, useRef } from 'react'

const API = (path, options = {}) =>
  fetch(path.startsWith('http') ? path : `/api${path}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  }).then((r) => (r.ok ? r.json() : Promise.reject(new Error(r.statusText))))

export default function App() {
  const [theme, setTheme] = useState(() => {
    try {
      return localStorage.getItem('ada_theme') || 'dark'
    } catch (e) { return 'dark' }
  })

  useEffect(() => {
    try { document.documentElement.setAttribute('data-theme', theme); localStorage.setItem('ada_theme', theme) } catch (e) {}
  }, [theme])
  const [balance, setBalance] = useState({ income: 0, expense: 0, balance: 0, can_use_paid_tools: false })
  const [events, setEvents] = useState([])
  const [chatMessage, setChatMessage] = useState('')
  const [chatHistory, setChatHistory] = useState([
    { role: 'ada', text: 'Hola, soy A.D.A. Actúo como tu socio: doy mi opinión, propongo planes y explico el porqué de mis decisiones. ¿Sobre qué quieres que hablemos?' }
  ])
  const [pendingProposal, setPendingProposal] = useState(null)
  const [loading, setLoading] = useState(false)
  const [activeTab, setActiveTab] = useState('seguimiento') // seguimiento, panel, plan, logs, brain, finance
  const [needsHelp, setNeedsHelp] = useState({ steps: [], platforms: [] })
  const [plan, setPlan] = useState(null) // plan actual + avances
  const [agentStatus, setAgentStatus] = useState(null) // estado agregado para Panel
  const [planHistory, setPlanHistory] = useState([]) // planes anteriores
  const [brainConsoleEntries, setBrainConsoleEntries] = useState([])
  const [ollamaStatus, setOllamaStatus] = useState({ reachable: false, model_ready: false, error: '', models_available: [] })
  const [selfCheck, setSelfCheck] = useState(null)

  const chatEndRef = useRef(null)
  const chatAbortRef = useRef(null)
  const chatTimeoutRef = useRef(null)

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const loadFinancials = useCallback(() => {
    API('/balance').then(setBalance).catch(console.error)
  }, [])

  const loadEvents = useCallback(() => {
    API('/events?limit=50').then((d) => setEvents(d.events || [])).catch(console.error)
  }, [])

  const loadNeedsHelp = useCallback(() => {
    API('/autonomous/needs_help').then((d) => setNeedsHelp({ steps: d.steps || [], platforms: d.platforms || [] })).catch(() => setNeedsHelp({ steps: [], platforms: [] }))
  }, [])

  const loadPlan = useCallback(() => {
    API('/autonomous/plan').then((d) => {
      const p = d.plan || null
      if (p) p.step_statuses = d.step_statuses || []
      setPlan(p)
    }).catch(() => setPlan(null))
  }, [])

  const loadBrainConsole = useCallback(() => {
    API('/autonomous/brain_console?limit=100').then((d) => setBrainConsoleEntries(d.entries || [])).catch(() => setBrainConsoleEntries([]))
  }, [])

  const loadOllamaStatus = useCallback(() => {
    API('/autonomous/ollama_status').then((d) => setOllamaStatus({
      reachable: !!d.reachable,
      model_ready: !!d.model_ready,
      error: d.error || '',
      models_available: d.models_available || [],
      model_configured: d.model_configured || ''
    })).catch(() => setOllamaStatus({ reachable: false, model_ready: false, error: 'Error al comprobar', models_available: [] }))
  }, [])

  const loadSelfCheck = useCallback(() => {
    API('/autonomous/self_check').then((d) => setSelfCheck({ message: d.message || '', sufficient: d.sufficient })).catch(() => setSelfCheck({ message: 'Error al cargar el autochequeo.', sufficient: false }))
  }, [])

  const loadAgentStatus = useCallback(() => {
    API('/agent/status').then(setAgentStatus).catch(() => setAgentStatus(null))
  }, [])

  const loadPlanHistory = useCallback(() => {
    API('/agent/plan-history').then((d) => setPlanHistory(d.history || [])).catch(() => setPlanHistory([]))
  }, [])

  const loadChatHistory = useCallback(() => {
    API('/chat/history').then((d) => {
      if (d.messages && d.messages.length > 0) {
        setChatHistory(d.messages.map((m) => ({ role: m.role || 'ada', text: m.text || '', brain: m.brain })))
      }
    }).catch(() => { })
  }, [])

  const saveChatHistory = useCallback((history) => {
    if (!history || history.length === 0) return
    API('/chat/history', {
      method: 'POST',
      body: JSON.stringify({
        history: history.map((m) => ({ role: m.role, text: m.text || '', brain: m.brain }))
      })
    }).catch(() => { })
  }, [])

  // Persistir automáticamente cuando cambie el historial (excluyendo el primer mensaje estático)
  useEffect(() => {
    if (chatHistory.length > 1) {
      saveChatHistory(chatHistory)
    }
  }, [chatHistory, saveChatHistory])

  useEffect(() => {
    loadChatHistory()
  }, [loadChatHistory])

  useEffect(() => {
    loadFinancials()
    loadEvents()
    loadNeedsHelp()
    loadPlan()
    const t = setInterval(() => {
      loadFinancials()
      loadEvents()
      loadNeedsHelp()
      loadPlan()
      if (activeTab === 'brain') { loadBrainConsole(); loadOllamaStatus(); }
      if (activeTab === 'panel') { loadAgentStatus(); }
      if (activeTab === 'seguimiento') { loadPlan(); loadAgentStatus(); }
    }, 800)
    return () => clearInterval(t)
  }, [loadFinancials, loadEvents, loadNeedsHelp, loadPlan, activeTab, loadBrainConsole, loadOllamaStatus, loadAgentStatus])

  useEffect(scrollToBottom, [chatHistory])

  const sendChat = () => {
    if (!chatMessage.trim()) return
    const msg = chatMessage.trim()
    setChatMessage('')
    setChatHistory(h => [...h, { role: 'user', text: msg }])
    setLoading(true)

    if (chatTimeoutRef.current) clearTimeout(chatTimeoutRef.current)
    if (chatAbortRef.current) chatAbortRef.current.abort()
    const controller = new AbortController()
    chatAbortRef.current = controller

    const history = chatHistory.slice(-10).map((m) => ({
      role: m.role === 'ada' ? 'assistant' : 'user',
      content: m.text || '',
    }))

    const clearLoading = () => {
      if (chatTimeoutRef.current) {
        clearTimeout(chatTimeoutRef.current)
        chatTimeoutRef.current = null
      }
      chatAbortRef.current = null
      setLoading(false)
    }

    chatTimeoutRef.current = setTimeout(() => {
      chatTimeoutRef.current = null
      if (chatAbortRef.current) {
        chatAbortRef.current.abort()
        chatAbortRef.current = null
      }
      setChatHistory(h => {
        const last = h[h.length - 1]
        const userText = last?.role === 'user' ? (last.text || '') : ''
        if (userText) setTimeout(() => setChatMessage(userText), 0)
        return [...h.slice(0, -1), { role: 'ada', text: 'Tiempo de espera agotado. Edita tu mensaje abajo y vuelve a intentar, o revisa que Ollama y agent-core estén activos.' }]
      })
      setLoading(false)
    }, 200000)

    API('/chat', {
      method: 'POST',
      body: JSON.stringify({ message: msg, use_ollama: true, history }),
      signal: controller.signal,
    })
      .then((res) => {
        clearLoading()
        const newAda = res.response ? { role: 'ada', text: res.response, brain: res.brain } : null
        setChatHistory(h => {
          const next = newAda ? [...h, newAda] : h
          return next
        })
        const prop = res.proposal || (res.full && res.full.proposal)
        if (res.status === 'pending_approval' || res.task_result?.status === 'pending_approval') {
          setPendingProposal(prop)
        }
        loadNeedsHelp()
        loadPlan()
      })
      .catch((e) => {
        clearLoading()
        if (e.name === 'AbortError') {
          setChatHistory(h => {
            const last = h[h.length - 1]
            const userText = last?.role === 'user' ? (last.text || '') : ''
            if (userText) setTimeout(() => setChatMessage(userText), 0)
            return [...h.slice(0, -1), { role: 'ada', text: 'Respuesta detenida. Edita tu mensaje abajo y vuelve a enviar si algo quedó mal.' }]
          })
        } else {
          setChatHistory(h => {
            const next = [...h, { role: 'ada', text: `Error: ${e.message}` }]
            saveChatHistory(next)
            return next
          })
        }
      })
      .finally(() => setLoading(false))
  }

  const stopChat = () => {
    if (chatTimeoutRef.current) {
      clearTimeout(chatTimeoutRef.current)
      chatTimeoutRef.current = null
    }
    if (chatAbortRef.current) {
      chatAbortRef.current.abort()
      chatAbortRef.current = null
    }
    setChatHistory(h => {
      const last = h[h.length - 1]
      const userText = last?.role === 'user' ? (last.text || '') : ''
      if (userText) setTimeout(() => setChatMessage(userText), 0)
      return h.length > 1 && last?.role === 'user' ? [...h.slice(0, -1), { role: 'ada', text: 'Respuesta detenida. Edita tu mensaje abajo y vuelve a enviar si algo quedó mal.' }] : h
    })
    setLoading(false)
  }

  const handleAction = (type, proposal) => {
    setLoading(true)
    const endpoint = type === 'approve' ? '/approve' : '/reject'
    API(endpoint, { method: 'POST', body: JSON.stringify(proposal) })
      .then(() => {
        setPendingProposal(null)
        loadEvents()
      })
      .finally(() => setLoading(false))
  }

  const handleClearPlan = () => {
    if (!window.confirm('¿Estás seguro de que quieres limpiar el plan y todos los avances? Esto reiniciará la estrategia de ADA.')) return
    setLoading(true)
    API('/autonomous/clear_plan', { method: 'POST' })
      .then(() => {
        setPlan(null)
        setNeedsHelp({ steps: [], platforms: [] })
        loadPlan()
        loadEvents()
        setChatHistory(h => [...h, { role: 'ada', text: 'He reiniciado mi plan y avances. ¿En qué quieres que me enfoque ahora para generar ingresos?' }])
      })
      .catch(e => alert('Error al limpiar el plan: ' + e.message))
      .finally(() => setLoading(false))
  }

  return (
    <div className="app-layout">
      {/* LEFT PANE: CHAT & DECISIONS */}
      <section className="pane pane-left">
        <header className="pane-header">
          <h2><span className="badge badge-success">ADA</span> Tu socio</h2>
          <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            <button
              type="button"
              className="secondary"
              onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
              title="Cambiar tema"
            >
              {theme === 'dark' ? 'Modo claro' : 'Modo oscuro'}
            </button>
          </div>
          <div style={{ fontSize: '0.8rem', opacity: 0.6 }}>Opina, propone planes y explica el porqué de sus decisiones</div>
        </header>

        <div className="chat-container">
          <div className="chat-history">
            {chatHistory.map((m, i) => (
              <div key={i} className={`message message-${m.role} animate-fade-in`}>
                <div className="avatar">{m.role === 'ada' ? 'A' : 'T'}</div>
                <div className="message-bubble">
                  {m.brain === 'advanced' && (
                    <div className="brain-indicator advanced">
                      <span className="brain-icon">🧠</span> DeepSeek-R1
                    </div>
                  )}
                  {m.role === 'ada' && m.text.includes('**Necesito tu ayuda:**') ? (() => {
                    const parts = m.text.split('**Necesito tu ayuda:**')
                    const after = parts[1] ? parts[1].trim() : ''
                    return (
                      <>
                        {parts[0].split('\n').map((line, li) => (
                          <div key={li} style={{ marginBottom: line ? '0.2rem' : '0.8rem' }}>{line}</div>
                        ))}
                        {after && (
                          <div className="needs-help-box" style={{ marginTop: '0.75rem', padding: '0.75rem', background: 'rgba(255,180,0,0.15)', borderLeft: '4px solid var(--warn)', borderRadius: 4 }}>
                            <strong>Necesito tu ayuda:</strong>
                            <div style={{ marginTop: 0.25 }}>{after.split('\n').map((l, li) => <div key={li}>{l}</div>)}</div>
                          </div>
                        )}
                      </>
                    )
                  })() : (
                    m.text.split('\n').map((line, li) => (
                      <div key={li} style={{ marginBottom: line ? '0.2rem' : '0.8rem' }}>{line}</div>
                    ))
                  )}
                </div>
              </div>
            ))}
            {loading && (
              <div className="message message-ada animate-fade-in">
                <div className="avatar">A</div>
                <div className="message-bubble" style={{ opacity: 0.9 }}>
                  ADA está pensando y preparando su opinión...
                </div>
              </div>
            )}
            <div ref={chatEndRef} />
          </div>

          <div className="chat-footer">
            {loading && (
              <div className="glass-card animate-fade-in" style={{ marginBottom: '0.75rem', padding: '0.6rem 0.75rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '0.75rem', borderLeft: '4px solid var(--warn)', background: 'rgba(255,180,0,0.15)' }}>
                <span style={{ fontSize: '0.9rem', color: 'var(--warn)', fontWeight: 600 }}>ADA está respondiendo — puedes detener para editar y reenviar</span>
                <button type="button" onClick={stopChat} style={{ padding: '0.45rem 1rem', fontWeight: 600, background: 'var(--warn)', color: '#1a1a1a', border: 'none', borderRadius: 6, cursor: 'pointer', flexShrink: 0 }} title="Detener para poder editar tu mensaje y volver a enviar">
                  Detener
                </button>
              </div>
            )}
            {needsHelp.steps.length > 0 && (
              <div className="glass-card animate-fade-in" style={{ marginBottom: '1rem', borderLeft: '4px solid var(--warn)' }}>
                <div style={{ fontSize: '0.8rem', fontWeight: 'bold', marginBottom: '0.5rem', color: 'var(--warn)' }}>
                  TU SOCIO ADA NECESITA TU AYUDA PARA AVANZAR
                </div>
                <ul style={{ margin: 0, paddingLeft: '1.2rem', fontSize: '0.9rem', marginBottom: '0.5rem', listStyle: 'none' }}>
                  {needsHelp.steps.map((s, i) => (
                    <li key={i} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.35rem' }}>
                      <span>{s.action}</span>
                      <button
                        type="button"
                        className="secondary"
                        style={{ padding: '0.25rem 0.5rem', fontSize: '0.75rem' }}
                        onClick={() => {
                          const stepIndex = s.step_index ?? i
                          const params = new URLSearchParams({ step_index: String(stepIndex), result: 'Completado por el usuario' })
                          fetch(`/api/autonomous/step_done?${params}`, { method: 'POST', headers: { 'Content-Type': 'application/json' } })
                            .then((r) => r.ok ? r.json() : Promise.reject(new Error(r.statusText)))
                            .then(() => { loadNeedsHelp(); loadPlan() })
                            .catch(console.error)
                        }}
                      >
                        Marcar como completado
                      </button>
                    </li>
                  ))}
                </ul>
                {needsHelp.platforms.length > 0 && (
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                    Registros: {needsHelp.platforms.map((p) => (
                      <a key={p.id} href={p.signup_url} target="_blank" rel="noopener noreferrer" style={{ marginRight: '0.5rem' }}>{p.name}</a>
                    ))}
                  </div>
                )}
              </div>
            )}
            {pendingProposal && (
              <div className="glass-card animate-fade-in" style={{ marginBottom: '1rem', borderLeft: '4px solid var(--warn)' }}>
                <div style={{ fontSize: '0.8rem', fontWeight: 'bold', marginBottom: '0.5rem', color: 'var(--warn)' }}>
                  PROPUESTA PENDIENTE
                </div>
                <div style={{ fontSize: '0.9rem', marginBottom: '1rem' }}>{pendingProposal.task_name}</div>
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                  <button onClick={() => handleAction('approve', pendingProposal)}>Aprobar</button>
                  <button className="secondary" onClick={() => handleAction('reject', pendingProposal)}>Ignorar</button>
                </div>
              </div>
            )}
            <div className="chat-input-row">
              <input
                type="text"
                placeholder="Hablar con tu socio: metas, opiniones, por qué ese plan..."
                value={chatMessage}
                onChange={(e) => setChatMessage(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && !loading && sendChat()}
                disabled={loading}
              />
              <button onClick={sendChat} disabled={loading || !chatMessage.trim()}>
                Enviar
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* RIGHT PANE: DEVELOPMENT & SYSTEM OPS */}
      <section className="pane pane-right">
        <header className="pane-header pane-header-tabs">
          <nav className="tab-bar" aria-label="Secciones">
            <button className={`tab-btn ${activeTab === 'seguimiento' ? 'active' : ''}`} onClick={() => { setActiveTab('seguimiento'); loadPlan(); loadAgentStatus(); }}>Seguimiento</button>
            <button className={`tab-btn ${activeTab === 'panel' ? 'active' : ''}`} onClick={() => { setActiveTab('panel'); loadAgentStatus(); loadPlanHistory(); }}>Panel</button>
            <button className={`tab-btn ${activeTab === 'plan' ? 'active' : ''}`} onClick={() => setActiveTab('plan')}>Plan y avances</button>
            <button className={`tab-btn ${activeTab === 'logs' ? 'active' : ''}`} onClick={() => setActiveTab('logs')}>Consola</button>
            <button className={`tab-btn ${activeTab === 'brain' ? 'active' : ''}`} onClick={() => { setActiveTab('brain'); loadBrainConsole(); loadOllamaStatus(); }}>ConsolaCerebro</button>
            <button className={`tab-btn ${activeTab === 'finance' ? 'active' : ''}`} onClick={() => setActiveTab('finance')}>Finanzas</button>
          </nav>
          <div className="pane-header-meta">
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: '0.6rem', opacity: 0.5 }}>BALANCE</div>
              <div style={{ color: balance.balance >= 0 ? 'var(--accent)' : 'var(--err)', fontWeight: 'bold' }}>
                ${balance.balance.toFixed(2)}
              </div>
            </div>
            <div className={`badge ${balance.can_use_paid_tools ? 'badge-success' : 'badge-info'}`}>
              {balance.can_use_paid_tools ? 'PAY-LEVEL' : 'FREE-ONLY'}
            </div>
          </div>
        </header>

        <div className="pane-content">
          {activeTab === 'seguimiento' && (
            <div className="glass-card" style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '1.25rem', overflow: 'auto', padding: '1.25rem' }}>
              <div style={{ marginBottom: '0.5rem' }}>
                <h3 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 700 }}>Seguimiento del avance de ADA</h3>
                <p style={{ margin: '0.35rem 0 0', fontSize: '0.85rem', color: 'var(--text-muted)' }}>Plan y paso a paso — dónde va ADA y qué falta</p>
              </div>
              {plan ? (
                <>
                  {(() => {
                    const steps = plan.steps || []
                    const statuses = plan.step_statuses || []
                    const doneCount = steps.filter((_, i) => (statuses[i] || {}).status === 'done').length
                    const percent = steps.length ? Math.round((doneCount / steps.length) * 100) : 0
                    const currentStep = agentStatus && typeof agentStatus.step_in_execution === 'number' ? agentStatus.step_in_execution : null
                    return (
                      <>
                        <div style={{ background: 'rgba(0,0,0,0.2)', borderRadius: 10, padding: '1rem 1.25rem', border: '1px solid rgba(255,255,255,0.08)' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.6rem', flexWrap: 'wrap', gap: '0.5rem' }}>
                            <span style={{ fontSize: '1rem', fontWeight: 600 }}>Progreso</span>
                            <span style={{ color: 'var(--accent)', fontWeight: 700, fontSize: '1.1rem' }}>{doneCount} de {steps.length} pasos · {percent}%</span>
                          </div>
                          <div style={{ height: 10, background: 'rgba(255,255,255,0.1)', borderRadius: 5, overflow: 'hidden' }}>
                            <div style={{ width: `${percent}%`, height: '100%', background: 'var(--accent)', borderRadius: 5, transition: 'width 0.3s ease' }} />
                          </div>
                        </div>
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.25rem' }}>OBJETIVO</div>
                        <div style={{ fontWeight: 600, marginBottom: '0.5rem' }}>{plan.goal || '—'}</div>
                        {plan.niche && (
                          <>
                            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.25rem' }}>NICHO</div>
                            <div style={{ marginBottom: '1rem' }}>{plan.niche}</div>
                          </>
                        )}
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.5rem', textTransform: 'uppercase', letterSpacing: 0.5 }}>Paso a paso</div>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                          {steps.map((s, i) => {
                            const st = statuses[i] || {}
                            const isDone = st.status === 'done'
                            const isCurrent = currentStep === i
                            const tool = (s.tool || '').toLowerCase()
                            const needsHuman = ['humano', 'human', 'usuario', 'user'].includes(tool)
                            const markDone = () => {
                              const comment = window.prompt('Comentario opcional (ej: Cuenta creada, oferta publicada):')
                              const result = (comment && comment.trim()) ? comment.trim() : 'Completado por el usuario'
                              const params = new URLSearchParams({ step_index: String(i), result })
                              fetch(`/api/autonomous/step_done?${params}`, { method: 'POST', headers: { 'Content-Type': 'application/json' } })
                                .then((r) => r.ok ? r.json() : Promise.reject(new Error(r.statusText)))
                                .then(() => { loadPlan(); loadNeedsHelp(); loadEvents(); loadAgentStatus(); })
                                .catch((e) => { console.error(e); alert('No se pudo marcar. Revisa agent-core.') })
                            }
                            return (
                              <div
                                key={i}
                                style={{
                                  display: 'flex',
                                  alignItems: 'flex-start',
                                  gap: '0.75rem',
                                  padding: '0.9rem 1rem',
                                  background: isCurrent ? 'rgba(255,180,0,0.12)' : isDone ? 'rgba(0,255,136,0.06)' : 'rgba(255,255,255,0.04)',
                                  borderLeft: `4px solid ${isDone ? 'var(--accent)' : isCurrent ? 'var(--warn)' : 'rgba(255,255,255,0.2)'}`,
                                  borderRadius: 8,
                                  transition: 'background 0.2s',
                                }}
                              >
                                <div style={{ flexShrink: 0, width: 28, height: 28, borderRadius: '50%', background: isDone ? 'var(--accent)' : isCurrent ? 'var(--warn)' : 'rgba(255,255,255,0.15)', color: isDone || isCurrent ? '#1a1a1a' : 'var(--text-muted)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 700, fontSize: '0.85rem' }}>
                                  {isDone ? '✓' : i + 1}
                                </div>
                                <div style={{ flex: 1, minWidth: 0 }}>
                                  <div style={{ fontWeight: 600, marginBottom: 0.25 }}>{s.action || s}</div>
                                  {s.tool && <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>({s.tool})</span>}
                                  {isDone && (st.result || st.done_at) && (
                                    <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.35rem' }}>
                                      {st.result && <span>{st.result}</span>}
                                      {st.done_at && <span> — {new Date(st.done_at).toLocaleString()}</span>}
                                    </div>
                                  )}
                                  {!isDone && needsHuman && (
                                    <button type="button" className="secondary" style={{ marginTop: '0.5rem', padding: '0.3rem 0.6rem', fontSize: '0.8rem' }} onClick={markDone}>
                                      Marcar como realizado
                                    </button>
                                  )}
                                </div>
                                <div style={{ flexShrink: 0, fontSize: '0.75rem', fontWeight: 600, color: isDone ? 'var(--accent)' : isCurrent ? 'var(--warn)' : 'var(--text-muted)' }}>
                                  {isDone ? 'Hecho' : isCurrent ? 'En curso' : 'Pendiente'}
                                </div>
                              </div>
                            )
                          })}
                        </div>
                        {plan.next_review && (
                          <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Próxima revisión: {plan.next_review}</div>
                        )}
                      </>
                    )
                  })()}
                </>
              ) : (
                <div style={{ padding: '1.5rem', textAlign: 'center', color: 'var(--text-muted)', background: 'rgba(0,0,0,0.15)', borderRadius: 10 }}>
                  <p style={{ margin: 0 }}>No hay plan cargado.</p>
                  <p style={{ margin: '0.5rem 0 0', fontSize: '0.9rem' }}>Ve a <button type="button" className="secondary" style={{ marginLeft: 4 }} onClick={() => setActiveTab('plan')}>Plan y avances</button> para crear uno o pídeselo a ADA en el chat.</p>
                </div>
              )}
            </div>
          )}

          {activeTab === 'panel' && (
            <div className="glass-card" style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '1.25rem', overflow: 'auto' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 1 }}>Panel del agente — Vista en tiempo real</div>

              {/* SECCIÓN 1: Estado general */}
              <section style={{ borderLeft: '4px solid var(--accent)', paddingLeft: '0.75rem' }}>
                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: 0.35 }}>SECCIÓN 1 — Estado general</div>
                {agentStatus ? (
                  <>
                    <div><strong>Objetivo global:</strong> {agentStatus.goal || '—'}</div>
                    <div><strong>Estado actual:</strong> <span className={`badge ${agentStatus.state === 'needs_human' ? 'badge-warn' : agentStatus.state === 'executing' ? 'badge-info' : 'badge-success'}`}>{agentStatus.state || 'idle'}</span> · Modo: {agentStatus.mode || '—'}</div>
                    <div><strong>Progreso:</strong> <span style={{ color: 'var(--accent)', fontWeight: 600 }}>{agentStatus.progress_percent ?? 0}%</span></div>
                  </>
                ) : (
                  <div style={{ color: 'var(--text-muted)' }}>Cargando estado…</div>
                )}
              </section>

              {/* SECCIÓN 2: Plan detallado */}
              <section style={{ borderLeft: '4px solid var(--accent)', paddingLeft: '0.75rem' }}>
                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: 0.35 }}>SECCIÓN 2 — Plan detallado</div>
                {agentStatus && agentStatus.plan && (agentStatus.plan.steps || []).length > 0 ? (
                  <ol style={{ margin: 0, paddingLeft: '1.2rem' }}>
                    {(agentStatus.plan.steps || []).map((s, i) => {
                      const st = (agentStatus.step_statuses || [])[i] || {}
                      const isDone = st.status === 'done'
                      const isExecuting = agentStatus.step_in_execution === i
                      const tool = (s.tool || '').toLowerCase()
                      const needsHuman = ['humano', 'human', 'usuario', 'user'].includes(tool)
                      const statusLabel = isDone ? 'terminado' : isExecuting ? 'ejecutando' : 'pendiente'
                      const markDone = () => {
                        const comment = window.prompt('Comentario opcional:')
                        const result = (comment && comment.trim()) ? comment.trim() : 'Completado por el usuario'
                        fetch(`/api/agent/complete-step?step_index=${i}&result=${encodeURIComponent(result)}`, { method: 'POST', headers: { 'Content-Type': 'application/json' } })
                          .then((r) => r.ok && (loadAgentStatus(), loadPlan(), loadNeedsHelp(), loadEvents()))
                          .catch(console.error)
                      }
                      const sendCreds = () => {
                        const platform = window.prompt('Plataforma (ej: gumroad, kofi):', 'gumroad')
                        if (!platform) return
                        fetch('/api/agent/credentials', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ platform: platform.trim(), configured: true, note: 'Configurado por usuario' }) })
                          .then((r) => r.ok && markDone())
                          .catch(console.error)
                      }
                      return (
                        <li key={i} style={{ marginBottom: 0.5 }}>
                          <span>{s.action || s}</span> {s.tool && <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>({s.tool})</span>}
                          <div style={{ fontSize: '0.8rem', marginTop: 0.2, display: 'flex', flexWrap: 'wrap', gap: 0.35 }}>
                            <span style={{ color: isDone ? 'var(--accent)' : isExecuting ? 'var(--warn)' : 'var(--text-muted)' }}>{statusLabel}</span>
                            {!isDone && needsHuman && (
                              <>
                                <button type="button" className="secondary" style={{ padding: '0.15rem 0.4rem', fontSize: '0.75rem' }} onClick={markDone}>Marcar como completado</button>
                                <button type="button" className="secondary" style={{ padding: '0.15rem 0.4rem', fontSize: '0.75rem' }} onClick={sendCreds}>Proveer credenciales</button>
                              </>
                            )}
                          </div>
                        </li>
                      )
                    })}
                  </ol>
                ) : (
                  <div style={{ color: 'var(--text-muted)' }}>Sin plan cargado. Crea uno desde Plan y avances o el chat.</div>
                )}
              </section>

              {/* SECCIÓN 3: Logs internos */}
              <section style={{ borderLeft: '4px solid var(--accent)', paddingLeft: '0.75rem' }}>
                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: 0.35 }}>SECCIÓN 3 — Logs internos (qué piensa, decide e intenta ejecutar)</div>
                <div style={{ maxHeight: 220, overflowY: 'auto', fontSize: '0.8rem' }}>
                  {events
                    .filter((ev) => ev.service_name === 'agent-core' && /plan|learning|autonomous|task_executed|proposal_generated|first_offer|step_|needs_help|thinking/.test(ev.event_type || ''))
                    .slice(0, 25)
                    .map((ev) => {
                      const p = ev.payload || {}
                      const msg = p.message || p.result || p.suggestion || ev.event_type.replace(/_/g, ' ')
                      return (
                        <div key={ev.id} style={{ marginBottom: 0.4, padding: '0.25rem 0', borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
                          <span style={{ color: 'var(--text-muted)' }}>[{new Date(ev.created_at).toLocaleTimeString()}]</span> {ev.event_type.replace(/_/g, ' ')} — {typeof msg === 'string' ? msg : JSON.stringify(msg).slice(0, 120)}
                        </div>
                      )
                    })}
                  {events.filter((ev) => ev.service_name === 'agent-core').length === 0 && <div style={{ color: 'var(--text-muted)' }}>Sin eventos aún.</div>}
                </div>
              </section>

              {/* SECCIÓN 4: Intervención humana */}
              <section style={{ borderLeft: '4px solid var(--warn)', paddingLeft: '0.75rem' }}>
                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: 0.35 }}>SECCIÓN 4 — Intervención humana</div>
                {needsHelp.steps.length > 0 ? (
                  <>
                    <p style={{ fontSize: '0.85rem' }}>ADA necesita que completes estos pasos:</p>
                    <ul style={{ margin: 0, paddingLeft: '1.2rem' }}>
                      {needsHelp.steps.map((s, i) => (
                        <li key={i} style={{ marginBottom: 0.4 }}>
                          {s.action}
                          <div style={{ marginTop: 0.25 }}>
                            {needsHelp.platforms && needsHelp.platforms.length > 0 && (
                              <a href={needsHelp.platforms.find((p) => p.id === 'gumroad')?.signup_url || '#'} target="_blank" rel="noopener noreferrer" className="secondary" style={{ marginRight: 0.5, padding: '0.2rem 0.5rem', fontSize: '0.75rem', display: 'inline-block' }}>Ir a completar registro</a>
                            )}
                            <button type="button" className="secondary" style={{ padding: '0.2rem 0.5rem', fontSize: '0.75rem' }} onClick={() => {
                              const stepIndex = s.step_index ?? i
                              const result = window.prompt('Resultado (ej: Cuenta creada):', 'Completado')
                              if (result == null) return
                              fetch(`/api/agent/complete-step?step_index=${stepIndex}&result=${encodeURIComponent(result)}`, { method: 'POST', headers: { 'Content-Type': 'application/json' } })
                                .then((r) => r.ok && (loadAgentStatus(), loadPlan(), loadNeedsHelp(), loadEvents()))
                                .catch(console.error)
                            }}>Marcar como resuelto y continuar</button>
                          </div>
                        </li>
                      ))}
                    </ul>
                  </>
                ) : (
                  <div style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>No hay pasos pendientes que requieran tu intervención.</div>
                )}
              </section>

              {/* Planes anteriores */}
              {planHistory.length > 0 && (
                <section style={{ borderLeft: '4px solid rgba(255,255,255,0.2)', paddingLeft: '0.75rem' }}>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: 0.35 }}>Planes anteriores (histórico)</div>
                  <div style={{ fontSize: '0.8rem' }}>
                    {planHistory.slice(0, 5).map((h, i) => (
                      <div key={i} style={{ marginBottom: 0.35 }}>
                        {h.created_at} — {h.event === 'plan_cleared' ? 'Plan limpiado' : (h.plan && h.plan.goal) || 'Plan creado'}
                      </div>
                    ))}
                  </div>
                </section>
              )}
            </div>
          )}

          {activeTab === 'plan' && (
            <div className="glass-card" style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '1rem', overflow: 'auto' }}>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                <strong style={{ color: 'var(--text)' }}>Para qué sirve:</strong> Aquí ves el plan de ingresos de ADA (objetivo, pasos y avances). Puedes marcar los pasos que tú ya hiciste (ej. cuenta Gumroad creada) con «Marcar como realizado». Para empezar de cero: <strong>Limpiar todo e iniciar de nuevo</strong> (ver docs/INICIO-DESDE-CERO.md).
              </div>
              <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                <button type="button" className="secondary" style={{ fontSize: '0.8rem' }} onClick={loadSelfCheck}>Que ADA revise su funcionamiento y herramientas</button>
                <button type="button" className="secondary" style={{ fontSize: '0.8rem' }} onClick={handleClearPlan}>Solo plan</button>
              <button
                type="button"
                className="danger"
                style={{ fontSize: '0.8rem' }}
                onClick={() => {
                  if (!window.confirm('¿Limpiar TODO (plan, oferta, pasos)? Opcional: también borrar historial de chat. ¿Incluir chat?')) return
                  const clearChat = window.confirm('¿Borrar también el historial del chat? (Cancelar = no borrar chat)')
                  setLoading(true)
                  fetch(`/api/autonomous/reset_all?clear_chat=${clearChat}`, { method: 'POST', headers: { 'Content-Type': 'application/json' } })
                    .then((r) => r.ok ? r.json() : Promise.reject(new Error(r.statusText)))
                    .then((data) => {
                      setPlan(null)
                      setNeedsHelp({ steps: [], platforms: [] })
                      loadPlan(); loadNeedsHelp(); loadEvents(); loadAgentStatus()
                      if (clearChat) {
                        setChatHistory([{ role: 'ada', text: 'Hola, soy A.D.A. He reiniciado todo. ¿Sobre qué quieres que hablemos o qué plan quieres que proponga?' }])
                        saveChatHistory([{ role: 'ada', text: 'Hola, soy A.D.A. He reiniciado todo. ¿Sobre qué quieres que hablemos o qué plan quieres que proponga?' }])
                      }
                      alert(data.message || 'Todo limpiado. Puedes iniciar de nuevo.')
                    })
                    .catch((e) => alert('Error: ' + e.message))
                    .finally(() => setLoading(false))
                }}
              >
                Limpiar todo e iniciar de nuevo
              </button>
              </div>
              {selfCheck && (
                <div style={{ padding: '1rem', background: 'rgba(0,0,0,0.2)', borderRadius: 8, borderLeft: `4px solid ${selfCheck.sufficient ? 'var(--accent)' : 'var(--warn)'}`, whiteSpace: 'pre-wrap', fontSize: '0.9rem' }}>{selfCheck.message}</div>
              )}
              {plan ? (
                <>
                  {(() => {
                    const steps = plan.steps || []
                    const statuses = plan.step_statuses || []
                    const doneCount = steps.filter((_, i) => (statuses[i] || {}).status === 'done').length
                    return steps.length > 0 ? (
                      <div style={{ padding: '0.5rem 0.75rem', background: 'rgba(0,0,0,0.15)', borderRadius: 6, fontSize: '0.9rem' }}>
                        <strong>Resumen:</strong> {doneCount} de {steps.length} pasos completados
                      </div>
                    ) : null
                  })()}
                  <div>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: 0.25 }}>OBJETIVO (propuesta de ADA)</div>
                    <div style={{ fontWeight: 600 }}>{plan.goal || '—'}</div>
                  </div>
                  <div>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: 0.25 }}>NICHO / IDEA (y por qué lo eligió)</div>
                    <div>{plan.niche || '—'}</div>
                  </div>
                  <div>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: 0.5 }}>PASOS DEL PLAN (estado de lo que ADA va realizando)</div>
                    <ol style={{ margin: 0, paddingLeft: '1.2rem' }}>
                      {(plan.steps || []).map((s, i) => {
                        const st = (plan.step_statuses || [])[i] || {}
                        const isDone = st.status === 'done'
                        const tool = (s.tool || '').toLowerCase()
                        const needsHuman = ['humano', 'human', 'usuario', 'user'].includes(tool)
                        const markStepDone = () => {
                          const comment = window.prompt('Comentario opcional (ej: Cuenta Gumroad creada, oferta publicada):')
                          const result = (comment && comment.trim()) ? comment.trim() : 'Completado por el usuario'
                          const platform = /gumroad|ko-fi|kofi|etsy/i.test(result) ? (result.toLowerCase().includes('gumroad') ? 'Gumroad' : result.toLowerCase().includes('ko-fi') || result.toLowerCase().includes('kofi') ? 'Ko-fi' : '') : ''
                          const params = new URLSearchParams({ step_index: String(i), result })
                          if (platform) params.set('platform', platform)
                          fetch(`/api/autonomous/step_done?${params}`, { method: 'POST', headers: { 'Content-Type': 'application/json' } })
                            .then((r) => r.ok ? r.json() : Promise.reject(new Error(r.statusText)))
                            .then(() => { loadPlan(); loadNeedsHelp(); loadEvents() })
                            .catch((e) => { console.error(e); alert('No se pudo marcar el paso. Revisa que agent-core esté en marcha.') })
                        }
                        return (
                          <li key={i} style={{ marginBottom: 0.6 }}>
                            <span>{s.action || s}</span>
                            {s.tool && <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginLeft: 6 }}>({s.tool})</span>}
                            <div style={{ marginTop: 0.25, marginLeft: 0, fontSize: '0.8rem', display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: '0.5rem' }}>
                              {isDone ? (
                                <span style={{ color: 'var(--accent)', display: 'inline-flex', alignItems: 'center', gap: 0.35 }}>
                                  ✓ Hecho
                                  {st.done_at && <span style={{ color: 'var(--text-muted)', fontWeight: 'normal' }}> — {new Date(st.done_at).toLocaleString()}</span>}
                                  {st.result && <span style={{ color: 'var(--text-muted)' }}> — {st.result}</span>}
                                </span>
                              ) : (
                                <>
                                  <span style={{ color: 'var(--text-muted)' }}>○ Pendiente</span>
                                  {needsHuman && (
                                    <button
                                      type="button"
                                      className="secondary"
                                      style={{ padding: '0.2rem 0.5rem', fontSize: '0.75rem' }}
                                      onClick={markStepDone}
                                    >
                                      Marcar como realizado
                                    </button>
                                  )}
                                </>
                              )}
                            </div>
                          </li>
                        )
                      })}
                    </ol>
                  </div>
                  {plan.next_review && (
                    <div style={{ fontSize: '0.85rem' }}>Próxima revisión: {plan.next_review}</div>
                  )}
                  <div style={{ borderTop: '1px solid rgba(255,255,255,0.1)', paddingTop: '0.75rem', marginTop: 0.5 }}>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: 0.5 }}>AVANCES DE ADA (decisiones y eventos recientes)</div>
                    {events
                      .filter((ev) => ev.service_name === 'agent-core' && /plan|learning|autonomous|task_executed|proposal_generated|first_offer|step_executed|step_completed|step_started|needs_help|thinking/.test(ev.event_type || ''))
                      .slice(0, 15)
                      .map((ev) => {
                        const p = ev.payload || {}
                        const isThinking = (ev.event_type || '').includes('thinking')
                        const isNeedsHelp = (ev.event_type || '').includes('needs_help')
                        const isExecuted = (ev.event_type || '').includes('step_executed')
                        return (
                          <div key={ev.id} className={`event-item ${isThinking ? 'event-thinking' : ''}`}>
                            <div className="event-meta">
                              <span className="event-time">[{new Date(ev.created_at).toLocaleTimeString()}]</span>
                              <span className="event-type-badge">{ev.event_type.replace(/_/g, ' ')}</span>
                            </div>
                            <div className="event-content">
                              {p.message || p.result || p.suggestion || (typeof p === 'string' ? p : JSON.stringify(p))}
                            </div>
                            {isThinking && <div className="thinking-pulse"></div>}
                          </div>
                        )
                      })}
                    {events.filter((ev) => ev.service_name === 'agent-core' && /plan|learning|autonomous|task_executed|proposal_generated|first_offer|step_executed|step_completed|step_started|needs_help/.test(ev.event_type || '')).length === 0 && (
                      <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Sin eventos de avance aún.</div>
                    )}
                  </div>
                </>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                  <p style={{ color: 'var(--text-muted)', margin: 0 }}>ADA aún no ha propuesto un plan. Puedes pedirle uno en el chat o generarlo desde aquí.</p>
                  <button
                    type="button"
                    style={{ alignSelf: 'flex-start' }}
                    disabled={loading}
                    onClick={() => {
                      setLoading(true)
                      API('/autonomous/first_plan', { method: 'POST' })
                        .then(() => {
                          loadPlan()
                          loadEvents()
                        })
                        .catch((e) => alert('No se pudo generar el plan: ' + (e.message || 'revisa que agent-core y Ollama estén activos.')))
                        .finally(() => setLoading(false))
                    }}
                  >
                    Que ADA genere el plan ahora
                  </button>
                </div>
              )}
            </div>
          )}

          {activeTab === 'logs' && (
            <div className="glass-card" style={{ flex: 1, display: 'flex', flexDirection: 'column', padding: 0, overflow: 'hidden' }}>
              <div style={{ padding: '0.75rem 1rem', background: 'rgba(0,0,0,0.2)', fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                SISTEMA DE EVENTOS CENTRALIZADO
              </div>
              <div style={{ flex: 1, overflowY: 'auto', padding: '0.5rem' }}>
                {events.map((ev) => (
                  <div key={ev.id} className={`log-entry animate-fade-in ${ev.event_type.startsWith('thinking_') ? 'thinking' : ''}`}>
                    <span className="log-timestamp">[{new Date(ev.created_at).toLocaleTimeString()}]</span>
                    <span className="log-service">{ev.service_name.toUpperCase()}</span>
                    <span className="log-type">{ev.event_type.replace(/_/g, ' ')}</span>
                    <div className="log-payload">
                      {typeof ev.payload === 'object' ? JSON.stringify(ev.payload, null, 2) : ev.payload}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'brain' && (
            <div className="glass-card" style={{ flex: 1, display: 'flex', flexDirection: 'column', padding: 0, overflow: 'hidden' }}>
              <div style={{ padding: '0.75rem 1rem', background: 'rgba(0,0,0,0.2)', fontSize: '0.7rem', color: 'var(--text-muted)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.5rem' }}>
                <span>CONSOLACEREBRO — Errores del cerebro avanzado (DeepSeek) y de Ollama</span>
                <button type="button" className="secondary" style={{ padding: '0.25rem 0.5rem', fontSize: '0.7rem' }} onClick={() => API('/autonomous/brain_console/clear', { method: 'POST' }).then(loadBrainConsole).catch(console.error)}>Limpiar</button>
              </div>
              <div style={{ padding: '0.5rem 1rem', background: ollamaStatus.reachable ? 'rgba(0,255,157,0.08)' : 'rgba(255,100,100,0.1)', borderLeft: `4px solid ${ollamaStatus.reachable ? 'var(--accent)' : 'var(--err)'}`, fontSize: '0.8rem' }}>
                {ollamaStatus.reachable ? (
                  <>Ollama: <strong>alcanzable</strong>{ollamaStatus.model_ready ? ' — modelo listo' : ` — modelo configurado: ${ollamaStatus.model_configured || '?'}. En el host: ollama pull ${ollamaStatus.model_configured || 'llama3.2'}`}</>
                ) : (
                  <>Ollama: <strong>no alcanzable</strong>. {ollamaStatus.error || 'Asegúrate de que Ollama esté en marcha en el host (ollama serve o servicio del sistema).'}</>
                )}
              </div>
              <div style={{ flex: 1, overflowY: 'auto', padding: '0.5rem' }}>
                {brainConsoleEntries.length === 0 ? (
                  <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', padding: '1rem' }}>Sin errores registrados. Los fallos del cerebro avanzado y de Ollama aparecerán aquí.</div>
                ) : (
                  brainConsoleEntries.map((entry, i) => (
                    <div key={i} className="log-entry animate-fade-in" style={{ borderLeft: `3px solid ${entry.brain === 'advanced' ? 'var(--warn)' : 'var(--err)'}`, marginBottom: '0.5rem' }}>
                      <span className="log-timestamp">[{entry.ts ? new Date(entry.ts).toLocaleString() : ''}]</span>
                      <span style={{ fontWeight: 600, marginRight: '0.5rem' }}>{entry.brain === 'advanced' ? 'AVANZADO' : 'OLLAMA'}</span>
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{entry.kind}</span>
                      <div className="log-payload" style={{ marginTop: '0.25rem', wordBreak: 'break-word' }}>{entry.message}</div>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}

          {activeTab === 'finance' && (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              <div className="glass-card">
                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>INGRESOS TOTALES</div>
                <div style={{ fontSize: '1.5rem', color: 'var(--accent)', fontWeight: 'bold' }}>${balance.income.toFixed(2)}</div>
              </div>
              <div className="glass-card">
                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>GASTOS OPERATIVOS</div>
                <div style={{ fontSize: '1.5rem', color: 'var(--err)', fontWeight: 'bold' }}>${balance.expense.toFixed(2)}</div>
              </div>
              <div className="glass-card" style={{ gridColumn: 'span 2', borderLeft: '4px solid var(--secondary)' }}>
                <h3>Estrategia de Reinversión</h3>
                <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
                  {!balance.can_use_paid_tools
                    ? "Actualmente en fase de acumulación. Solo se permiten herramientas Gratuitas/Locales."
                    : "Capital disponible para herramientas de alto ROI. Sugerencia: API de mayor precisión."}
                </p>
              </div>
            </div>
          )}
        </div>
      </section>
    </div>
  )
}

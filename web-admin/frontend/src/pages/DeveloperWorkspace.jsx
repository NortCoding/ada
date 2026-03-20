import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import ChatPane from '../components/ChatPane'
import FileExplorer from '../components/FileExplorer'
import CodeViewer from '../components/CodeViewer'
import { api } from '../api/client'
import TaskList from '../components/tasks/TaskList'
import RecentActivityLog from '../components/activity/RecentActivityLog'
import { useTaskQueue } from '../hooks/useTaskQueue'

export default function DeveloperWorkspace() {
  const [theme, setTheme] = useState(() => {
    try {
      return localStorage.getItem('ada_theme') || 'dark'
    } catch (e) {
      return 'dark'
    }
  })

  useEffect(() => {
    try {
      document.documentElement.setAttribute('data-theme', theme)
      localStorage.setItem('ada_theme', theme)
    } catch (e) {}
  }, [theme])

  const [executionMode, setExecutionMode] = useState(false)
  const [chatMessage, setChatMessage] = useState('')
  const [chatImageBase64, setChatImageBase64] = useState(null)
  const [chatHistory, setChatHistory] = useState([{ role: 'ada', text: 'Developer workspace listo. ¿Qué quieres construir o depurar?' }])
  const [loading, setLoading] = useState(false)
  const [agentConnected, setAgentConnected] = useState(false)

  const chatEndRef = useRef(null)
  const chatInputRef = useRef(null)

  const [fileExplorerExpanded, setFileExplorerExpanded] = useState(() => new Set())
  const [fileExplorerCache, setFileExplorerCache] = useState({})
  const [fileExplorerLoadingPath, setFileExplorerLoadingPath] = useState(null)
  const [selectedFilePath, setSelectedFilePath] = useState(null)
  const [selectedFileContent, setSelectedFileContent] = useState('')
  const [selectedFileLoading, setSelectedFileLoading] = useState(false)

  const { tasks, stats, createTask, startTask, completeTask, failTask } = useTaskQueue()
  const [localActivity, setLocalActivity] = useState([])
  const [pendingPlan, setPendingPlan] = useState(null)
  const [executingPlan, setExecutingPlan] = useState(false)
  const [pendingPlanError, setPendingPlanError] = useState(null)

  const discardPendingPlan = () => {
    setPendingPlan(null)
    setPendingPlanError(null)
    pushActivity('plan descartado por el usuario')
  }

  const pushActivity = useCallback((text) => {
    const ts = new Date().toISOString()
    setLocalActivity((prev) => [{ ts, text }, ...prev].slice(0, 12))
  }, [])

  const fileExplorerToggle = useCallback((path) => {
    setFileExplorerExpanded((prev) => {
      const next = new Set(prev)
      if (next.has(path)) next.delete(path)
      else next.add(path)
      return next
    })
  }, [])

  const fileExplorerFetch = useCallback((path) => {
    if (fileExplorerCache[path] != null) return
    setFileExplorerLoadingPath(path)
    const q = path ? `?path=${encodeURIComponent(path)}` : ''
    api(`/fs/list${q}`)
      .then((data) => setFileExplorerCache((c) => ({ ...c, [data.path === '.' ? '' : data.path]: data.entries || [] })))
      .catch(() => setFileExplorerCache((c) => ({ ...c, [path]: [] })))
      .finally(() => setFileExplorerLoadingPath(null))
  }, [fileExplorerCache])

  useEffect(() => {
    if (!selectedFilePath) { setSelectedFileContent(''); return }
    setSelectedFileLoading(true)
    api(`/fs/read?path=${encodeURIComponent(selectedFilePath)}`)
      .then((d) => setSelectedFileContent(d.content || ''))
      .catch((e) => setSelectedFileContent(`Error al leer archivo: ${e.message}`))
      .finally(() => setSelectedFileLoading(false))
  }, [selectedFilePath])

  useEffect(() => {
    api('/agent/health')
      .then(() => setAgentConnected(true))
      .catch(() => setAgentConnected(false))
  }, [])

  const sendChat = () => {
    const msg = (chatMessage || '').trim()
    if (!msg && !chatImageBase64) return
    const imageToSend = chatImageBase64
    setChatMessage('')
    setChatImageBase64(null)
    if (chatInputRef.current) chatInputRef.current.textContent = ''
    setChatHistory((h) => [...h, { role: 'user', text: msg || '(imagen)', imageBase64: imageToSend }])
    setLoading(true)

    const payload = {
      message: msg || '¿Qué ves?',
      use_ollama: true,
      history: chatHistory.map((m) => ({ role: m.role, content: typeof m.text === 'string' ? m.text : '' })),
      agent_type: 'developer',
      execution_mode: !!executionMode,
    }
    if (imageToSend) payload.image_base64 = imageToSend

    api('/chat', { method: 'POST', body: JSON.stringify(payload) })
      .then((res) => {
        setChatHistory((h) => [...h, { role: 'ada', text: res.response, brain: res.brain }])
        if (res.status === 'pending_plan' && Array.isArray(res.pending_plan)) {
          setPendingPlan(res.pending_plan)
          setPendingPlanError(null)
        } else {
          setPendingPlan(null)
          setPendingPlanError(null)
        }
      })
      .catch((e) => {
        setPendingPlan(null)
        setPendingPlanError(e.message || 'Error')
        setChatHistory((h) => [...h, { role: 'ada', text: `Error: ${e.message}` }])
      })
      .finally(() => setLoading(false))
  }

  const adaStatus = useMemo(() => {
    if (pendingPlan) return 'waiting approval'
    if (stats.running) return 'running'
    return 'idle'
  }, [pendingPlan, stats.running])

  const createQuickTask = (kind) => {
    if (kind === 'analyze') {
      const t = createTask({ type: 'chat_instruction', title: 'Analyze project', input: { message: 'analyze project' } })
      setChatMessage('analyze project')
      if (chatInputRef.current) chatInputRef.current.textContent = 'analyze project'
      completeTask(t.id, 'Prepared chat instruction')
      return
    }
    if (kind === 'fix_error') {
      const msg = 'fix error File testOpt/test.py line 1 NameError: x is not defined'
      const t = createTask({ type: 'chat_instruction', title: 'Fix error (example)', input: { message: msg } })
      setChatMessage(msg)
      if (chatInputRef.current) chatInputRef.current.textContent = msg
      completeTask(t.id, 'Prepared chat instruction')
      return
    }
    if (kind === 'demo_landing') {
      const msg = [
        'Crea una landing page estática para presentar ADA como asistente de desarrollo.',
        'Escribe los archivos bajo dockers/ada-landing-demo/ (index.html y styles.css).',
        'Incluye hero con título, 3 beneficios y un CTA. Estilo sobrio y legible.',
        'Si hace falta, primero LIST_DIR: dockers; luego usa WRITE_FILE con END_FILE por archivo.',
        'Si quieres servir la página localmente con un comando, incluye RUN_COMMAND al final del plan (aprobación aparte).',
      ].join(' ')
      const t = createTask({ type: 'chat_instruction', title: 'Demo: landing ADA', input: { message: msg } })
      setChatMessage(msg)
      if (chatInputRef.current) chatInputRef.current.textContent = msg
      completeTask(t.id, 'Demo prompt listo en el chat')
      return
    }
  }

  const executePendingPlan = () => {
    if (!pendingPlan || executingPlan) return
    setExecutingPlan(true)
    setPendingPlanError(null)

    const t = createTask({ type: 'execute_plan', title: 'Ejecutar plan aprobado', input: { n_actions: pendingPlan.length } })
    startTask(t.id)

    api('/execute_plan', { method: 'POST', body: JSON.stringify({ plan: pendingPlan }) })
      .then((res) => {
        const results = Array.isArray(res?.results) ? res.results : []
        const joined = results.length ? results.join('\n') : '(sin resultados)'
        setChatHistory((h) => [...h, { role: 'ada', text: `Resultado del plan:\n${joined}`, brain: res?.status || 'done' }])
        completeTask(t.id, res?.status || 'done')
        setPendingPlan(null)
        pushActivity(`plan ejecutado · ${res?.status || 'done'}`)
      })
      .catch((e) => {
        setPendingPlanError(e?.message || 'Error al ejecutar plan')
        failTask(t.id, e?.message || 'Error al ejecutar plan')
        pushActivity(`plan ejecutado · error · ${e?.message || 'Error'}`)
      })
      .finally(() => setExecutingPlan(false))
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>

      <div className="app-layout" style={{ flex: 1 }}>
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

      <section className="pane pane-code" aria-label="Código y Archivos">
        <div className="code-layout-split">
          <div className="code-sidebar">
            <header className="pane-header">
              <h3 style={{ margin: 0, fontSize: '0.9rem' }}>📂 Explorador</h3>
              <button className="secondary" style={{ padding: '2px 8px', fontSize: '0.7rem' }} onClick={() => { setFileExplorerCache({}); fileExplorerFetch('') }}>
                RECARGAR
              </button>
            </header>
            <div className="file-explorer-content">
              <FileExplorer
                expanded={fileExplorerExpanded}
                onToggle={fileExplorerToggle}
                cache={fileExplorerCache}
                loadingPath={fileExplorerLoadingPath}
                onSelect={setSelectedFilePath}
                selectedPath={selectedFilePath}
                onFetch={fileExplorerFetch}
              />
            </div>
          </div>
          <div className="code-editor-area">
            <CodeViewer path={selectedFilePath} content={selectedFileContent} loading={selectedFileLoading} />
          </div>
        </div>
      </section>

      <section className="pane pane-preview" aria-label="Developer Actions">
        <div className="pane-content" style={{ padding: '1rem', display: 'flex', flexDirection: 'column', gap: 14, overflow: 'auto' }}>
          <div>
            <h3 style={{ margin: 0 }}>⚡ Quick actions</h3>
            <div style={{ fontSize: '0.85rem', color: 'var(--subtle)', marginTop: 6 }}>
              Atajos para preparar instrucciones en el chat. Si ADA propone un plan delicado, se pedirá aprobación.
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            <button className="secondary" onClick={() => createQuickTask('analyze')}>Analyze project</button>
            <button className="secondary" onClick={() => createQuickTask('fix_error')}>Fix error (example)</button>
            <button className="secondary" onClick={() => createQuickTask('demo_landing')}>Demo: landing ADA (prompt)</button>
          </div>

          <div className="glass-card" style={{ padding: '1rem' }}>
            <h4 style={{ marginTop: 0 }}>⏳ Plan pendiente de aprobación</h4>
            {pendingPlan ? (
              <>
                <div style={{ fontSize: '0.85rem', color: 'var(--subtle)', marginTop: 6 }}>
                  Acciones: {pendingPlan.length}
                </div>
                <pre style={{ marginTop: 10, fontSize: '0.75rem', whiteSpace: 'pre-wrap', background: 'rgba(0,0,0,0.05)', padding: 10, borderRadius: 10 }}>
                  {pendingPlan.map((a, i) => `${i + 1}. ${(a && a.type) || 'unknown'}`).join('\n')}
                </pre>
                {pendingPlanError && <div style={{ color: 'var(--danger)', fontSize: '0.85rem' }}>{pendingPlanError}</div>}
                <div style={{ display: 'flex', gap: 10, marginTop: 10, flexWrap: 'wrap' }}>
                  <button disabled={executingPlan} onClick={executePendingPlan} style={{ padding: '6px 10px', fontSize: '0.85rem' }}>
                    {executingPlan ? 'Ejecutando…' : 'Ejecutar plan'}
                  </button>
                  <button type="button" className="secondary" disabled={executingPlan} onClick={discardPendingPlan} style={{ padding: '6px 10px', fontSize: '0.85rem' }}>
                    Descartar plan
                  </button>
                </div>
              </>
            ) : (
              <div style={{ color: 'var(--subtle)', fontSize: '0.9rem' }}>No hay plan pendiente.</div>
            )}
          </div>

          <div className="glass-card" style={{ padding: '1rem' }}>
            <h4 style={{ marginTop: 0 }}>✅ Tasks</h4>
            <TaskList tasks={tasks} />
          </div>
        </div>
      </section>

      </div>

      <div style={{ borderTop: '1px solid var(--border)', background: 'var(--panel)', padding: '10px 14px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12 }}>
          <div style={{ fontWeight: 800 }}>Recent activity</div>
          <div style={{ fontSize: '0.85rem', color: 'var(--subtle)' }}>
            files read · commands run · tasks completed
          </div>
        </div>
        <div style={{ marginTop: 10 }}>
          <RecentActivityLog extraItems={localActivity} />
        </div>
      </div>
    </div>
  )
}


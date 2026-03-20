import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import ChatPane from '../components/ChatPane'
import FileExplorer from '../components/FileExplorer'
import CodeViewer from '../components/CodeViewer'
import { api } from '../api/client'
import TaskList from '../components/tasks/TaskList'
import PendingApprovalsPanel from '../components/approvals/PendingApprovalsPanel'
import RecentActivityLog from '../components/activity/RecentActivityLog'
import { useTaskQueue } from '../hooks/useTaskQueue'
import { useApprovals } from '../hooks/useApprovals'

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
  const { approvals, pending, requestApproval, approve, reject, markExecuting, markDone, markError } = useApprovals()
  const [localActivity, setLocalActivity] = useState([])

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
      .then((res) => setChatHistory((h) => [...h, { role: 'ada', text: res.response, brain: res.brain }]))
      .catch((e) => setChatHistory((h) => [...h, { role: 'ada', text: `Error: ${e.message}` }]))
      .finally(() => setLoading(false))
  }

  const adaStatus = useMemo(() => {
    if (pending.length) return 'waiting approval'
    if (stats.running) return 'running'
    return 'idle'
  }, [pending.length, stats.running])

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
    if (kind === 'run_command') {
      const cmd = 'ls'
      const t = createTask({ type: 'run_command', title: `Run command: ${cmd}`, input: { command: cmd } })
      requestApproval({
        kind: 'run_command',
        title: `Execute command: ${cmd}`,
        payload: { command: cmd },
        preview: cmd,
      })
      startTask(t.id)
      completeTask(t.id, 'Queued for approval')
      return
    }
    if (kind === 'create_file') {
      const path = 'ADA/test-ui.txt'
      const content = `created from UI at ${new Date().toISOString()}\n`
      const t = createTask({ type: 'create_file', title: `Create file: ${path}`, input: { path } })
      requestApproval({
        kind: 'create_file',
        title: `Create file: ${path}`,
        payload: { path, content },
        preview: { path, contentPreview: content.slice(0, 200) },
      })
      startTask(t.id)
      completeTask(t.id, 'Queued for approval')
      return
    }
    if (kind === 'apply_patch') {
      const path = 'ADA/test-ui.txt'
      const newContent = `patched from UI at ${new Date().toISOString()}\n`
      const t = createTask({ type: 'apply_patch', title: `Apply patch: ${path}`, input: { path } })
      requestApproval({
        kind: 'apply_patch',
        title: `Apply patch: ${path}`,
        payload: { path, new_content: newContent },
        preview: { path, note: 'overwrite with new_content', newContentPreview: newContent.slice(0, 200) },
      })
      startTask(t.id)
      completeTask(t.id, 'Queued for approval')
      return
    }
  }

  const onApprove = (approvalId) => {
    const a = approvals.find((x) => x.id === approvalId)
    if (!a) return
    const actionType =
      a.kind === 'create_file' ? 'create_file' :
      a.kind === 'run_command' ? 'run_command' :
      a.kind === 'apply_patch' ? 'apply_patch' :
      null
    if (!actionType) return

    markExecuting(approvalId)
    const t = createTask({ type: 'approval_execute', title: `Execute approval: ${a.kind}`, input: { approvalId, actionType } })
    startTask(t.id)

    api('/approve/execute', { method: 'POST', body: JSON.stringify({ action_type: actionType, payload: a.payload || {} }) })
      .then((res) => {
        approve(approvalId)
        markDone(approvalId, res)
        completeTask(t.id, res)
        const target = (res && (res.target || (res.verification && res.verification.full_path))) || ''
        const ok = res && res.success === true
        pushActivity(`approved+executed: ${a.kind}${target ? ` · ${target}` : ''} · ${ok ? 'ok' : 'error'}`)
      })
      .catch((e) => {
        markError(approvalId, e.message)
        failTask(t.id, e.message)
        pushActivity(`approved+executed: ${a.kind} · error · ${e.message}`)
      })
  }

  const onReject = (approvalId) => {
    reject(approvalId)
    const t = createTask({ type: 'approval', title: 'Approval rejected', input: { approvalId } })
    completeTask(t.id, 'Rejected')
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
              Estas acciones crean tasks visibles. Ejecutar requiere aprobación.
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            <button className="secondary" onClick={() => createQuickTask('analyze')}>Analyze project</button>
            <button className="secondary" onClick={() => createQuickTask('fix_error')}>Fix error (example)</button>
            <button className="secondary" onClick={() => createQuickTask('run_command')}>Run command (requires approval)</button>
            <button className="secondary" onClick={() => createQuickTask('create_file')}>Create file (requires approval)</button>
            <button className="secondary" onClick={() => createQuickTask('apply_patch')}>Apply patch (requires approval)</button>
          </div>

          <div className="glass-card" style={{ padding: '1rem' }}>
            <h4 style={{ marginTop: 0 }}>⏳ Pending approvals</h4>
            <PendingApprovalsPanel pending={pending} onApprove={onApprove} onReject={onReject} />
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


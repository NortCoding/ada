import React, { useState, useEffect, useCallback, useRef } from 'react'
import SyntaxHighlighter from 'react-syntax-highlighter'
import { dracula } from 'react-syntax-highlighter/dist/esm/styles/hljs'
import { AdaBackground } from './AdaBackground'
import { api as API } from './api/client'
import RoadmapGoalsView from './RoadmapGoalsView'
import ChatPane from './components/ChatPane'
import FileExplorerComponent from './components/FileExplorer'
import CodeViewerComponent from './components/CodeViewer'
import AgentMarketPage from './components/AgentMarketPage'
import SystemMonitorPage from './components/SystemMonitorPage'

function toMessageString (v) {
  if (v == null) return ''
  if (typeof v === 'string') return v === '[object Object]' ? '' : v
  if (typeof v === 'object' && v !== null && typeof v.message === 'string') return v.message
  if (typeof v === 'object' && v !== null && typeof v.detail === 'string') return v.detail
  const s = String(v)
  return s === '[object Object]' ? '' : s
}

function parseMessageWithCodeBlocks(text) {
  if (!text || typeof text !== 'string') return [{ type: 'text', content: '' }]
  const segments = []
  let rest = text
  const re = /```(\w*)\n([\s\S]*?)```/g
  let m
  let lastIndex = 0
  while ((m = re.exec(text)) !== null) {
    if (m.index > lastIndex) segments.push({ type: 'text', content: text.slice(lastIndex, m.index) })
    const lang = (m[1] || '').trim().toLowerCase() || 'text'
    const code = (m[2] || '').trimEnd()
    if (code) segments.push({ type: 'code', content: code, language: lang })
    lastIndex = re.lastIndex
  }
  if (lastIndex < text.length) segments.push({ type: 'text', content: text.slice(lastIndex) })
  if (segments.length === 0) return [{ type: 'text', content: text }]
  return segments
}

function codeBlockLabel(lang) {
  const map = { html: 'HTML', css: 'CSS', js: 'JavaScript', javascript: 'JavaScript', jsx: 'JSX', ts: 'TypeScript', tsx: 'TSX', py: 'Python', json: 'JSON', md: 'Markdown', sh: 'Shell', sql: 'SQL', yaml: 'YAML', yml: 'YAML' }
  return map[lang] || (lang ? lang.toUpperCase() : 'Code')
}

const HIGHLIGHT_LANG = { js: 'javascript', javascript: 'javascript', jsx: 'jsx', ts: 'typescript', tsx: 'tsx', py: 'python', html: 'html', css: 'css', json: 'json', md: 'markdown', sh: 'bash', sql: 'sql', yaml: 'yaml', yml: 'yaml' }

function FileExplorer({ expanded, onToggle, cache, loadingPath, onSelect, selectedPath, onFetch }) {
  const loadRoot = () => { if (!cache['']) onFetch('') }
  React.useEffect(loadRoot, [])

  function renderEntries(relPath) {
    const entries = cache[relPath]
    if (!entries) return null
    return entries.map((e) => {
      const path = relPath ? `${relPath}/${e.name}` : e.name
      const isExpanded = expanded.has(path)
      const isSelected = selectedPath === path
      if (e.is_dir) {
        const hasChildren = isExpanded && cache[path]
        return (
          <div key={path} className="file-tree-folder">
            <button
              type="button"
              className={`file-tree-row ${isSelected ? 'selected' : ''}`}
              onClick={() => { onToggle(path); if (!cache[path]) onFetch(path) }}
              style={{ paddingLeft: (path.split('/').length - 1) * 12 + 8 }}
            >
              <span className="file-tree-chevron">{isExpanded ? '▼' : '▶'}</span>
              <span className="file-tree-icon file-tree-icon-folder">📁</span>
              <span className="file-tree-label">{e.name}</span>
            </button>
            {hasChildren && <div className="file-tree-children">{renderEntries(path)}</div>}
            {isExpanded && loadingPath === path && (
              <div className="file-tree-loading" style={{ paddingLeft: path.split('/').length * 12 + 8 }}>Cargando…</div>
            )}
          </div>
        )
      }
      const ext = (e.name.split('.').pop() || '').toLowerCase()
      const icon = [ 'py', 'js', 'jsx', 'ts', 'tsx', 'json', 'md', 'yml', 'yaml' ].includes(ext) ? '📄' : '📄'
      return (
        <button
          key={path}
          type="button"
          className={`file-tree-row file-tree-file ${isSelected ? 'selected' : ''}`}
          style={{ paddingLeft: (path.split('/').length - 1) * 12 + 8 }}
          onClick={() => onSelect(path)}
        >
          <span className="file-tree-chevron file-tree-chevron-placeholder" />
          <span className="file-tree-icon">{icon}</span>
          <span className="file-tree-label">{e.name}</span>
        </button>
      )
    })
  }
  return <div className="file-tree"><div className="file-tree-root">{renderEntries('')}</div></div>
}

function ChatCodeBlock({ content, language }) {
  const [copied, setCopied] = useState(false)
  const copy = () => { navigator.clipboard.writeText(content).then(() => { setCopied(true); setTimeout(() => setCopied(false), 2000) }) }
  const label = codeBlockLabel(language)
  const highlightLang = HIGHLIGHT_LANG[language] || language || 'text'
  return (
    <div className="chat-code-block">
      <div className="chat-code-block-header">
        <span className="chat-code-block-lang">{label}</span>
        <button type="button" className="chat-code-block-copy" onClick={copy}>{copied ? 'Copied' : 'Copy'}</button>
      </div>
      <div className="chat-code-block-body">
        <SyntaxHighlighter language={highlightLang} style={dracula} customStyle={{ margin: 0, padding: '0.75rem', background: 'transparent', fontSize: '0.85rem' }}>
          {content}
        </SyntaxHighlighter>
      </div>
    </div>
  )
}

function CodeViewer({ path, content, loading }) {
  if (!path) return <div className="code-viewer-empty">Selecciona un archivo para ver su código</div>
  if (loading) return <div className="code-viewer-empty">Cargando {path}...</div>
  const ext = (path.split('.').pop() || '').toLowerCase()
  const highlightLang = HIGHLIGHT_LANG[ext] || ext || 'text'
  return (
    <div className="code-viewer animate-fade-in">
      <div className="code-viewer-header">
        <span>{path}</span>
        <span>{codeBlockLabel(ext)}</span>
      </div>
      <div className="code-viewer-content">
        <SyntaxHighlighter language={highlightLang} style={dracula} customStyle={{ margin: 0, padding: '1rem', background: 'transparent', fontSize: '0.85rem' }} showLineNumbers={true}>
          {content || ''}
        </SyntaxHighlighter>
      </div>
    </div>
  )
}

function ProjectPreview({ path }) {
  // Endpoint `/api/projects/preview/*` is not guaranteed to exist in all deployments.
  // To avoid broken iframes and confusing errors, we disable the preview for now.
  const previewUrl = null
  return (
    <div className="project-preview">
      <div className="project-preview-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '1.2rem' }}>🌐</span>
          <strong style={{ fontSize: '0.9rem' }}>Vista Previa</strong>
        </div>
        <div className="preview-address-bar">
          <span style={{ opacity: 0.5 }}>http://ada.local/</span>
          <span>{path || '...'}</span>
        </div>
        <button
          type="button"
          className="secondary"
          disabled
          style={{ padding: '4px 8px', fontSize: '0.7rem' }}
          title="Preview endpoint no disponible"
        >
          Abrir ↗
        </button>
      </div>
      <div className="preview-empty">
        <div style={{ fontSize: '3rem' }}>🛑</div>
        <p>Preview deshabilitado: endpoint `/api/projects/preview/*` no disponible.</p>
      </div>
    </div>
  )
}

export default function App() {
  const [theme, setTheme] = useState(() => { try { return localStorage.getItem('ada_theme') || 'dark' } catch (e) { return 'dark' } })
  useEffect(() => { try { document.documentElement.setAttribute('data-theme', theme); localStorage.setItem('ada_theme', theme) } catch (e) {} }, [theme])
  const [balance, setBalance] = useState({ income: 0, expense: 0, balance: 0, can_use_paid_tools: false })
  const [events, setEvents] = useState([])
  const [chatMessage, setChatMessage] = useState('')
  const [chatImageBase64, setChatImageBase64] = useState(null)
  const [chatHistory, setChatHistory] = useState([{ role: 'ada', text: 'Hola, soy A.D.A. Tu socio virtual. ¿En qué puedo ayudarte hoy?' }])
  const [loading, setLoading] = useState(false)
  const [executionMode, setExecutionMode] = useState(false)
  const [activeTab, setActiveTab] = useState('preview')
  const [needsHelp, setNeedsHelp] = useState({ steps: [] })
  const [plan, setPlan] = useState(null)
  const [agentStatus, setAgentStatus] = useState(null)
  const [agentConnected, setAgentConnected] = useState(false)
  const [currentWorkspace, setCurrentWorkspace] = useState(null)
  const [agentProposals, setAgentProposals] = useState([])
  const [systemMonitor, setSystemMonitor] = useState(null)
  const [proposeDomain, setProposeDomain] = useState('')
  const [proposeSkills, setProposeSkills] = useState('')
  const [proposePurpose, setProposePurpose] = useState('')
  const [proposeSubmitting, setProposeSubmitting] = useState(false)
  const [proposeError, setProposeError] = useState(null)
  
  const chatEndRef = useRef(null)
  const chatInputRef = useRef(null)
  const [fileExplorerExpanded, setFileExplorerExpanded] = useState(() => new Set())
  const [fileExplorerCache, setFileExplorerCache] = useState({})
  const [fileExplorerLoadingPath, setFileExplorerLoadingPath] = useState(null)
  const [selectedFilePath, setSelectedFilePath] = useState(null)
  const [selectedFileContent, setSelectedFileContent] = useState('')
  const [selectedFileLoading, setSelectedFileLoading] = useState(false)

  useEffect(() => {
    if (!selectedFilePath) { setSelectedFileContent(''); return }
    const ext = (selectedFilePath.split('.').pop() || '').toLowerCase()
    const textExts = ['html', 'css', 'js', 'jsx', 'ts', 'tsx', 'py', 'json', 'md', 'yml', 'yaml', 'txt', 'env', 'Dockerfile', 'yml']
    if (!textExts.includes(ext) && !selectedFilePath.includes('Dockerfile') && !selectedFilePath.includes('docker-compose')) {
      setSelectedFileContent('(Archivo binario o no soportado para previsualización de texto)')
      return
    }
    setSelectedFileLoading(true)
    API(`/fs/read?path=${encodeURIComponent(selectedFilePath)}`)
      .then((data) => setSelectedFileContent(data.content || ''))
      .catch((e) => setSelectedFileContent(`Error al leer archivo: ${e.message}`))
      .finally(() => setSelectedFileLoading(false))
  }, [selectedFilePath])

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
    API(`/fs/list${q}`)
      .then((data) => {
        setFileExplorerCache((c) => ({ ...c, [data.path === '.' ? '' : data.path]: data.entries || [] }))
      })
      .catch(() => setFileExplorerCache((c) => ({ ...c, [path]: [] })))
      .finally(() => setFileExplorerLoadingPath(null))
  }, [fileExplorerCache])

  const loadPlan = useCallback(() => API('/autonomous/plan').then(d => setPlan(d.plan || null)).catch(() => setPlan(null)), [])
  const loadAgentStatus = useCallback(() => API('/agent/status').then(setAgentStatus).catch(() => setAgentStatus(null)), [])

  useEffect(() => {
    loadPlan(); loadAgentStatus();
    API('/agent/health').then(() => setAgentConnected(true)).catch(() => setAgentConnected(false));
    const t = setInterval(() => { 
      loadPlan(); loadAgentStatus(); 
      API('/agent/health').then(() => setAgentConnected(true)).catch(() => setAgentConnected(false));
    }, 10000)
    return () => clearInterval(t)
  }, [loadPlan, loadAgentStatus])

  const sendChat = () => {
    const msg = chatMessage.trim()
    if (!msg && !chatImageBase64) return
    const imageToSend = chatImageBase64
    setChatMessage(''); setChatImageBase64(null)
    if (chatInputRef.current) chatInputRef.current.textContent = ''
    setChatHistory(h => [...h, { role: 'user', text: msg || '(imagen)', imageBase64: imageToSend }])
    setLoading(true)
    const payload = {
      message: msg || '¿Qué ves?',
      use_ollama: true,
      history: chatHistory.map(m => ({ role: m.role, content: toMessageString(m.text) })),
      agent_type: currentWorkspace && ['developer', 'business', 'research', 'general'].includes(currentWorkspace) ? currentWorkspace : undefined,
      execution_mode: !!executionMode
    }
    if (imageToSend) payload.image_base64 = imageToSend
    API('/chat', { method: 'POST', body: JSON.stringify(payload) })
      .then(res => setChatHistory(h => [...h, { role: 'ada', text: res.response, brain: res.brain }]))
      .catch(e => setChatHistory(h => [...h, { role: 'ada', text: `Error: ${e.message}` }]))
      .finally(() => setLoading(false))
  }

  useEffect(() => chatEndRef.current?.scrollIntoView({ behavior: 'smooth' }), [chatHistory])

  // --- PANES DEFINITIONS ---
  const chatPane = (
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
  )

  const codePane = (
    <section className="pane pane-code" aria-label="Código y Archivos">
      <div className="code-layout-split">
        <div className="code-sidebar">
          <header className="pane-header">
            <h3 style={{ margin:0, fontSize: '0.9rem' }}>📂 Explorador</h3>
            <button className="secondary" style={{ padding: '2px 8px', fontSize: '0.7rem' }} onClick={() => { setFileExplorerCache({}); fileExplorerFetch('') }}>RECARGAR</button>
          </header>
          <div className="file-explorer-content">
            <FileExplorerComponent
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
          <CodeViewerComponent path={selectedFilePath} content={selectedFileContent} loading={selectedFileLoading} />
        </div>
      </div>
    </section>
  )

  useEffect(() => {
    if (currentWorkspace === 'agent_market') API('/agent_market/proposals').then(d => setAgentProposals(d.proposals || [])).catch(() => setAgentProposals([]))
  }, [currentWorkspace])
  useEffect(() => {
    if (currentWorkspace === 'system_monitor') API('/system/monitor').then(setSystemMonitor).catch(() => setSystemMonitor({ error: 'No disponible' }))
  }, [currentWorkspace])

  const workspaceLabel = { developer: 'Developer Lab', business: 'Business Lab', research: 'Research Lab', general: 'General', agent_market: 'Agent Market', system_monitor: 'System Monitor' }

  const previewPane = (
    <section className="pane pane-preview" aria-label="Vista Previa y Sistema">
        <nav className="tab-bar">
        <button className={`tab-btn ${activeTab === 'preview' ? 'active' : ''}`} onClick={() => setActiveTab('preview')}>🌐 Vista Previa</button>
        <button className={`tab-btn ${activeTab === 'seguimiento' ? 'active' : ''}`} onClick={() => setActiveTab('seguimiento')}>📊 Avance</button>
        <button className={`tab-btn ${activeTab === 'panel' ? 'active' : ''}`} onClick={() => setActiveTab('panel')}>⚙️ Sistema</button>
        <button className={`tab-btn ${activeTab === 'roadmap' ? 'active' : ''}`} onClick={() => setActiveTab('roadmap')}>🧭 Roadmap</button>
      </nav>
      <div className="pane-content">
        {activeTab === 'preview' && <ProjectPreview path={selectedFilePath} />}
        {activeTab === 'seguimiento' && (
          <div className="glass-card" style={{ padding: '1rem', overflow: 'auto', height: '100%' }}>
            <h3>Seguimiento</h3>
            {plan ? (
              <div className="plan-steps">
                {plan.steps.map((s, i) => (
                  <div key={i} className={`step-item ${(plan.step_statuses?.[i] || {}).status === 'done' ? 'done' : ''}`}>{s.action}</div>
                ))}
              </div>
            ) : <p>No hay plan activo.</p>}
          </div>
        )}
{activeTab === 'panel' && (
          <div className="glass-card" style={{ padding: '1rem', overflow: 'auto', height: '100%' }}>
             <h3>Estado del Sistema</h3>
             {agentStatus ? <pre style={{fontSize:'0.7rem'}}>{JSON.stringify(agentStatus, null, 2)}</pre> : 'Cargando...'}
          </div>
        )}
        {activeTab === 'roadmap' && (
          <div className="glass-card" style={{ padding: '1rem', overflow: 'auto', height: '100%' }}>
            <RoadmapGoalsView />
          </div>
        )}
      </div>
    </section>
  )

  if (currentWorkspace === null) {
    return (
      <>
        <AdaBackground />
        <div className="app-layout" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '100vh', padding: '2rem', gap: '2rem', position: 'relative', zIndex: 1 }}>
          <div style={{ textAlign: 'center', textShadow: '0 2px 10px rgba(0,0,0,0.5)' }}>
            <h1 style={{ fontSize: '3rem', margin: '0 0 1rem 0', fontWeight: 800, letterSpacing: '-0.03em', color: '#fff' }}>A.D.A SYSTEM</h1>
            <p style={{ opacity: 0.9, margin: 0, fontSize: '1.1rem', color: '#e2e8f0', maxWidth: '600px', lineHeight: 1.5 }}>
              Ecosistema de inteligencia artificial. Selecciona un módulo para interactuar con los agentes especializados.
            </p>
          </div>
          <div className="landing-grid">
            <div className="glass-panel landing-card" onClick={() => setCurrentWorkspace('developer')}>
              <div style={{ fontSize: '2.5rem', marginBottom: '1rem' }}>💻</div>
              <h3 style={{ margin: '0 0 0.5rem 0' }}>Developer Lab</h3>
              <p style={{ fontSize: '0.85rem', color: 'var(--subtle)', margin: 0 }}>Desarrollo y código</p>
            </div>
            <div className="glass-panel landing-card" onClick={() => setCurrentWorkspace('business')}>
              <div style={{ fontSize: '2.5rem', marginBottom: '1rem' }}>📈</div>
              <h3 style={{ margin: '0 0 0.5rem 0' }}>Business Lab</h3>
              <p style={{ fontSize: '0.85rem', color: 'var(--subtle)', margin: 0 }}>Estrategia y mercado</p>
            </div>
            <div className="glass-panel landing-card" onClick={() => setCurrentWorkspace('research')}>
              <div style={{ fontSize: '2.5rem', marginBottom: '1rem' }}>🔬</div>
              <h3 style={{ margin: '0 0 0.5rem 0' }}>Research Lab</h3>
              <p style={{ fontSize: '0.85rem', color: 'var(--subtle)', margin: 0 }}>Investigación profunda</p>
            </div>
            <div className="glass-panel landing-card" onClick={() => setCurrentWorkspace('general')}>
              <div style={{ fontSize: '2.5rem', marginBottom: '1rem' }}>🤖</div>
              <h3 style={{ margin: '0 0 0.5rem 0' }}>General AI</h3>
              <p style={{ fontSize: '0.85rem', color: 'var(--subtle)', margin: 0 }}>Asistencia multipropósito</p>
            </div>
            <div className="glass-panel landing-card" onClick={() => setCurrentWorkspace('agent_market')}>
              <div style={{ fontSize: '2.5rem', marginBottom: '1rem' }}>🛒</div>
              <h3 style={{ margin: '0 0 0.5rem 0' }}>Agent Market</h3>
              <p style={{ fontSize: '0.85rem', color: 'var(--subtle)', margin: 0 }}>Directorio de Nodos</p>
            </div>
            <div className="glass-panel landing-card" onClick={() => setCurrentWorkspace('system_monitor')}>
              <div style={{ fontSize: '2.5rem', marginBottom: '1rem' }}>🖥️</div>
              <h3 style={{ margin: '0 0 0.5rem 0' }}>System Monitor</h3>
              <p style={{ fontSize: '0.85rem', color: 'var(--subtle)', margin: 0 }}>Métricas y Salud</p>
            </div>
          </div>
        </div>
      </>
    )
  }

  if (currentWorkspace === 'agent_market') {
    return (
      <AgentMarketPage
        api={API}
        onBack={() => setCurrentWorkspace(null)}
        agentProposals={agentProposals}
        setAgentProposals={setAgentProposals}
        proposeDomain={proposeDomain}
        setProposeDomain={setProposeDomain}
        proposeSkills={proposeSkills}
        setProposeSkills={setProposeSkills}
        proposePurpose={proposePurpose}
        setProposePurpose={setProposePurpose}
        proposeSubmitting={proposeSubmitting}
        setProposeSubmitting={setProposeSubmitting}
        proposeError={proposeError}
        setProposeError={setProposeError}
      />
    )
  }

  if (currentWorkspace === 'system_monitor') {
    return (
      <SystemMonitorPage
        api={API}
        onBack={() => setCurrentWorkspace(null)}
        systemMonitor={systemMonitor}
        setSystemMonitor={setSystemMonitor}
      />
    )
  }

  return (
    <div className="app-layout" style={{ gridTemplateRows: 'auto 1fr' }}>
      <div style={{ gridColumn: '1 / -1', display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.5rem 0.75rem', background: 'var(--panel)', borderBottom: '1px solid var(--border)' }}>
        <button type="button" className="secondary" style={{ padding: '4px 8px', fontSize: '0.8rem' }} onClick={() => setCurrentWorkspace(null)}>← Dashboard</button>
        <span style={{ fontWeight: 600 }}>{workspaceLabel[currentWorkspace] || currentWorkspace}</span>
      </div>
      {chatPane}
      {codePane}
      {previewPane}
    </div>
  )
}

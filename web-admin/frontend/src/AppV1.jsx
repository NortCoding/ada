import React, { useState, useEffect, useCallback, useRef } from 'react'
import { api as API } from './api/client'
import ChatPane from './components/ChatPane'
import FileExplorer from './components/FileExplorer'
import CodeViewer from './components/CodeViewer'
import PendingApprovalsPanel from './components/approvals/PendingApprovalsPanel'

// Layout fijo ADA v1: Izq=Files, Centro=Chat, Der=Approvals+Results
// Mínimo, estable, enfocado desarrollo. Reusa componentes existentes.

export default function AppV1() {
  const [theme, setTheme] = useState('dark')
  const [chatHistory, setChatHistory] = useState([{ role: 'ada', text: 'ADA v1 listo. Chat de desarrollo: analiza código, crea apps desde ideas, ejecuta planes aprobados.' }])
  const [loading, setLoading] = useState(false)
  const [pendingPlan, setPendingPlan] = useState(null)
  const [executionResults, setExecutionResults] = useState([])
  const [fileCache, setFileCache] = useState({})
  const [loadingPath, setLoadingPath] = useState(null)
  const [selectedFile, setSelectedFile] = useState(null)
  const [fileContent, setFileContent] = useState('')
  const [fileLoading, setFileLoading] = useState(false)
  const chatEndRef = useRef(null)

  // File explorer callbacks (reutilizados)
  const toggleExpanded = useCallback((path) => {
    setFileCache(prev => {
      const next = { ...prev }
      if (!next[path]?.length && !loadingPath) fetchDir(path)
      return next
    })
  }, [loadingPath])

  const fetchDir = useCallback((path) => {
    if (fileCache[path] != null || loadingPath === path) return
    setLoadingPath(path)
    API(`/fs/list?path=${encodeURIComponent(path || '')}`)
      .then(data => setFileCache(c => ({ ...c, [data.path || '']: data.entries || [] })))
      .catch(() => setFileCache(c => ({ ...c, [path]: [] })))
      .finally(() => setLoadingPath(null))
  }, [fileCache, loadingPath])

  // Auto-load root
  useEffect(() => { fetchDir('') }, [])

  // File select → read content
  useEffect(() => {
    if (!selectedFile) {
      setFileContent('')
      return
    }
    setFileLoading(true)
    API(`/fs/read?path=${encodeURIComponent(selectedFile)}`)
      .then(data => setFileContent(data.content || ''))
      .catch(e => setFileContent(`Error: ${e.message}`))
      .finally(() => setFileLoading(false))
  }, [selectedFile])

  // Chat send (solo ADA v1 endpoints)
  const sendChat = useCallback((message) => {
    setChatHistory(h => [...h, { role: 'user', text: message }])
    setLoading(true)
    API('/chat', {
      method: 'POST',
      body: JSON.stringify({ message, use_ollama: true })
    })
    .then(res => {
      setChatHistory(h => [...h, { 
        role: 'ada', 
        text: res.response || 'Sin respuesta',
        plan: res.pending_plan 
      }])
      if (res.status === 'pending_plan') {
        setPendingPlan(res.pending_plan)
        setExecutionResults([]) // Clear prev results
      }
    })
    .catch(e => {
      setChatHistory(h => [...h, { role: 'ada', text: `Error: ${e.message}` }])
    })
    .finally(() => setLoading(false))
  }, [])

  // Execute approved plan
  const executePlan = useCallback(() => {
    if (!pendingPlan) return
    setExecutionResults(['Ejecutando plan...'])
    API('/execute_plan', {
      method: 'POST',
      body: JSON.stringify({ plan: pendingPlan })
    })
    .then(res => {
      setExecutionResults(res.results || ['Completado'])
      setPendingPlan(null) // Clear panel
      // Refresh file cache root
      setFileCache({})
      fetchDir('')
    })
    .catch(e => setExecutionResults([`Error ejecución: ${e.message}`]))
  }, [pendingPlan, fetchDir])

  useEffect(() => { chatEndRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [chatHistory])

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
  }, [theme])

  return (
    <div className="app-v1-layout" style={{
      display: 'grid',
      gridTemplateColumns: '280px 1fr 380px',
      gridTemplateRows: '1fr',
      height: '100vh',
      fontFamily: 'system-ui, sans-serif'
    }}>
      {/* Panel izquierdo: File Explorer */}
      <section className="panel-files" style={{ borderRight: '1px solid #333', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
        <div style={{ padding: '12px', fontWeight: 600, borderBottom: '1px solid #333', background: '#1a1a1a' }}>
          📁 Proyectos / Archivos
          <button onClick={() => { setFileCache({}); fetchDir('') }} style={{ float: 'right', fontSize: '11px' }}>↻</button>
        </div>
        <div style={{ flex: 1, overflow: 'auto' }}>
          <FileExplorer
            expanded={new Set()}
            onToggle={toggleExpanded}
            cache={fileCache}
            loadingPath={loadingPath}
            onSelect={setSelectedFile}
            selectedPath={selectedFile}
            onFetch={fetchDir}
          />
        </div>
      </section>

      {/* Panel central: Chat ADA v1 */}
      <section className="panel-chat" style={{ display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        <div style={{ padding: '12px', fontWeight: 600, borderBottom: '1px solid #333', background: '#1a1a1a' }}>
          💬 Chat Desarrollo (ADA v1)
          <span style={{ float: 'right', fontSize: '12px', opacity: 0.7 }}>Ollama local</span>
        </div>
        <div style={{ flex: 1, overflow: 'auto', padding: '16px', background: '#0d1117' }}>
          {chatHistory.map((msg, i) => (
            <div key={i} className={`chat-msg ${msg.role}`}>
              <div style={{ fontWeight: 500, marginBottom: '4px' }}>{msg.role === 'user' ? 'Tú' : 'ADA'}</div>
              <div>{msg.text}</div>
              {msg.plan && (
                <div style={{ fontSize: '11px', color: '#58a6ff', marginTop: '8px' }}>
                  📋 Plan detectado ({msg.plan.length} acciones)
                </div>
              )}
            </div>
          ))}
          {loading && <div style={{ opacity: 0.6 }}>ADA está pensando…</div>}
          <div ref={chatEndRef} />
        </div>
        <ChatPane
          onSendChat={sendChat}
          loading={loading}
          executionMode={false}
          theme={theme}
          onToggleTheme={() => setTheme(t => t === 'dark' ? 'light' : 'dark')}
          agentConnected={true}
          chatMessage={''}
          setChatMessage={() => {}}
          chatInputRef={{}}
          chatEndRef={{}}
        />
      </section>

      {/* Panel derecho: Pending Plan + Results */}
      <section className="panel-right" style={{ borderLeft: '1px solid #333', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
        <div style={{ padding: '12px', fontWeight: 600, borderBottom: '1px solid #333', background: '#1a1a1a' }}>
          ✅ Aprobaciones / Resultados
        </div>
        <div style={{ flex: 1, overflow: 'auto', padding: '16px' }}>
          {pendingPlan ? (
            <>
              <div style={{ background: '#0f4a17', padding: '12px', borderRadius: '6px', marginBottom: '16px' }}>
                <strong>📋 Plan Pendiente ({pendingPlan.length} acciones)</strong>
                <ol style={{ fontSize: '13px', margin: '8px 0 0 0' }}>
                  {pendingPlan.map((action, i) => (
                    <li key={i} style={{ marginBottom: '4px' }}>
                      <code>{action.type}: {action.path || action.command || JSON.stringify(action).slice(0,60)}</code>
                    </li>
                  ))}
                </ol>
                <button
                  onClick={executePlan}
                  style={{
                    width: '100%',
                    padding: '10px',
                    background: '#238636',
                    color: 'white',
                    border: 'none',
                    borderRadius: '6px',
                    fontWeight: 600,
                    cursor: 'pointer',
                    marginTop: '12px'
                  }}
                >
                  🚀 EJECUTAR PLAN
                </button>
              </div>
            </>
          ) : (
            <div style={{ opacity: 0.5, fontStyle: 'italic', textAlign: 'center', paddingTop: '40px' }}>
              Esperando plan a aprobar...
            </div>
          )}
          {executionResults.length > 0 && (
            <div style={{ background: '#161b22', padding: '12px', borderRadius: '6px' }}>
              <strong>📊 Resultados:</strong>
              <pre style={{ fontSize: '12px', marginTop: '8px', maxHeight: '300px', overflow: 'auto' }}>
                {executionResults.join('\n')}
              </pre>
            </div>
          )}
        </div>
      </section>

      {/* Code viewer overlay (sobre files cuando se selecciona) */}
      {selectedFile && (
        <div style={{
          position: 'fixed',
          top: 0, right: 0, bottom: 0, left: 0,
          zIndex: 1000,
          background: 'rgba(0,0,0,0.9)',
          display: 'flex',
          flexDirection: 'column'
        }}>
          <div style={{
            padding: '16px',
            background: '#0d1117',
            borderBottom: '1px solid #333',
            display: 'flex',
            alignItems: 'center',
            gap: '12px'
          }}>
            <button onClick={() => setSelectedFile(null)} style={{ color: '#58a6ff' }}>← Cerrar</button>
            <strong style={{ flex: 1, color: 'white' }}>📄 {selectedFile}</strong>
            <button onClick={() => navigator.clipboard.writeText(fileContent)} style={{ fontSize: '12px' }}>Copy</button>
          </div>
          <CodeViewer path={selectedFile} content={fileContent} loading={fileLoading} />
        </div>
      )}
    </div>
  )
}


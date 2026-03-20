import React, { useState, useEffect, useRef } from 'react'
import { 
  MessageSquare, 
  FolderTree, 
  Play, 
  CheckCircle2, 
  FileCode, 
  Terminal, 
  Send,
  RefreshCw,
  Code
} from 'lucide-react'
import './App.css'

// --- API Helper ---
const API = async (endpoint, options = {}) => {
  const res = await fetch(`/api${endpoint}`, {
    ...options,
    headers: { 'Content-Type': 'application/json', ...options.headers }
  })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export default function App() {
  const [files, setFiles] = useState([])
  const [selectedFile, setSelectedFile] = useState(null)
  const [fileContent, setFileContent] = useState('')
  const [messages, setMessages] = useState([
    { role: 'ada', text: 'Bienvenido a ADA v1. Estoy listo para ayudarte con tu proyecto.' }
  ])
  const [input, setInput] = useState('')
  const [pendingPlan, setPendingPlan] = useState(null)
  const [executionResult, setExecutionResult] = useState(null)
  const [isLoading, setIsLoading] = useState(false)
  
  const chatEndRef = useRef(null)

  // Load root files
  const loadFiles = async (path = '') => {
    try {
      const data = await API(`/fs/list?path=${path}`)
      setFiles(data.entries || [])
    } catch (e) {
      console.error('Error loading files:', e)
    }
  }

  useEffect(() => { loadFiles() }, [])
  useEffect(() => { chatEndRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages])

  const handleSend = async () => {
    if (!input.trim()) return
    const userMsg = input
    setInput('')
    setMessages(prev => [...prev, { role: 'user', text: userMsg }])
    setIsLoading(true)

    try {
      const res = await API('/chat', {
        method: 'POST',
        body: JSON.stringify({ message: userMsg, history: messages.map(m => ({ role: m.role, content: m.text })) })
      })
      
      setMessages(prev => [...prev, { role: 'ada', text: res.response }])
      
      // Check if response contains a pending plan
      if (res.brain?.pending_plan || res.pending_plan) {
        setPendingPlan(res.brain?.pending_plan || res.pending_plan)
      }
    } catch (e) {
      setMessages(prev => [...prev, { role: 'ada', text: `Error: ${e.message}` }])
    } finally {
      setIsLoading(false)
    }
  }

  const handleFileSelect = async (file) => {
    if (file.is_dir) {
      loadFiles(file.path)
      return
    }
    setSelectedFile(file)
    try {
      const data = await API(`/fs/read?path=${file.path}`)
      setFileContent(data.content)
    } catch (e) {
      setFileContent(`Error al leer archivo: ${e.message}`)
    }
  }

  const executePlan = async () => {
    if (!pendingPlan) return
    setIsLoading(true)
    try {
      const res = await API('/execute_plan', {
        method: 'POST',
        body: JSON.stringify({ plan: pendingPlan })
      })
      setExecutionResult(res)
      setPendingPlan(null)
      setMessages(prev => [...prev, { role: 'ada', text: 'Plan ejecutado correctamente. Revisa los resultados en el panel derecho.' }])
      loadFiles() // Refresh file list
    } catch (e) {
      setExecutionResult({ error: e.message })
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="app-container">
      {/* LEFT PANEL: Files */}
      <section className="panel sidebar">
        <div className="panel-header">
          <h2><FolderTree size={16} style={{marginRight:8}} /> Explorador</h2>
          <button className="icon-btn" onClick={() => loadFiles()}><RefreshCw size={14} /></button>
        </div>
        <div className="file-list">
          {files.map((f, i) => (
            <div 
              key={i} 
              className={`file-item ${selectedFile?.path === f.path ? 'active' : ''}`}
              onClick={() => handleFileSelect(f)}
            >
              {f.is_dir ? '📁' : <FileCode size={14} />} {f.name}
            </div>
          ))}
        </div>
      </section>

      {/* CENTER PANEL: Chat & Code */}
      <section className="panel">
        <div className="panel-header">
          <h2><MessageSquare size={16} style={{marginRight:8}} /> Chat de Desarrollo</h2>
          {selectedFile && <span className="current-file">{selectedFile.name}</span>}
        </div>
        
        <div className="chat-container">
          <div className="messages">
            {messages.map((m, i) => (
              <div key={i} className={`message ${m.role} animate-fade-in`}>
                {m.text}
              </div>
            ))}
            {isLoading && <div className="message ada">Escribiendo...</div>}
            <div ref={chatEndRef} />
          </div>

          <div className="chat-input-area">
            <div className="input-wrapper">
              <textarea 
                placeholder="Describe qué quieres construir..."
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && (e.preventDefault(), handleSend())}
              />
              <button className="btn-send" onClick={handleSend} disabled={isLoading}>
                <Send size={18} />
              </button>
            </div>
          </div>
        </div>

        {selectedFile && fileContent && (
          <div className="code-viewer animate-fade-in">
            <div className="code-header">
              <Code size={14} /> {selectedFile.path}
            </div>
            <pre><code>{fileContent}</code></pre>
          </div>
        )}
      </section>

      {/* RIGHT PANEL: Plans & Results */}
      <section className="panel sidebar">
        <div className="panel-header">
          <h2><Terminal size={16} style={{marginRight:8}} /> Plan & Resultados</h2>
        </div>
        
        <div className="right-content">
          {pendingPlan && (
            <div className="pending-plan animate-fade-in">
              <h3><Play size={14} /> Plan Pendiente</h3>
              <div className="plan-steps">
                {pendingPlan.steps?.map((s, i) => (
                  <div key={i} className="plan-step">
                    <CheckCircle2 size={12} color="var(--accent)" /> {s.title || s.action}
                  </div>
                ))}
              </div>
              <button className="btn-execute" onClick={executePlan} disabled={isLoading}>
                EJECUTAR PLAN
              </button>
            </div>
          )}

          {executionResult && (
            <div className="execution-results animate-fade-in">
              <h3><Terminal size={14} /> Resultados</h3>
              <pre className="results-log">
                {JSON.stringify(executionResult, null, 2)}
              </pre>
            </div>
          )}

          {!pendingPlan && !executionResult && (
            <div className="empty-state">
              <p>No hay planes de ejecución activos.</p>
            </div>
          )}
        </div>
      </section>
    </div>
  )
}

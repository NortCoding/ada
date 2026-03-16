import React, { useState, useEffect, useCallback, useRef } from 'react'
import SyntaxHighlighter from 'react-syntax-highlighter'
import { dracula } from 'react-syntax-highlighter/dist/esm/styles/hljs'

const API = (path, options = {}) =>
  fetch(path.startsWith('http') ? path : `/api${path}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  }).then((r) => (r.ok ? r.json() : Promise.reject(new Error(r.statusText))))

function toMessageString (v) {
  if (v == null) return ''
  if (typeof v === 'string') return v === '[object Object]' ? '' : v
  if (typeof v === 'object' && v !== null && typeof v.message === 'string') return v.message
  if (typeof v === 'object' && v !== null && typeof v.detail === 'string') return v.detail
  const s = String(v)
  return s === '[object Object]' ? '' : s
}

/** Parsea texto con bloques ```lang\ncode\n```; devuelve [{ type: 'text'|'code', content, language? }] */
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

/** Etiqueta legible por tipo de archivo / lenguaje */
function codeBlockLabel(lang) {
  const map = { html: 'HTML', css: 'CSS', js: 'JavaScript', javascript: 'JavaScript', jsx: 'JSX', ts: 'TypeScript', tsx: 'TSX', py: 'Python', json: 'JSON', md: 'Markdown', sh: 'Shell', sql: 'SQL', yaml: 'YAML', yml: 'YAML' }
  return map[lang] || (lang ? lang.toUpperCase() : 'Code')
}

const HIGHLIGHT_LANG = { js: 'javascript', javascript: 'javascript', jsx: 'jsx', ts: 'typescript', tsx: 'tsx', py: 'python', html: 'html', css: 'css', json: 'json', md: 'markdown', sh: 'bash', sql: 'sql', yaml: 'yaml', yml: 'yaml' }

/** Explorador de archivos: árbol de directorios del workspace */
function FileExplorer({ expanded, onToggle, cache, loadingPath, onSelect, selectedPath, onFetch }) {
  const loadRoot = () => {
    if (!cache['']) onFetch('')
  }
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
              onClick={() => {
                onToggle(path)
                if (!cache[path]) onFetch(path)
              }}
              style={{ paddingLeft: (path.split('/').length - 1) * 12 + 8 }}
            >
              <span className="file-tree-chevron">{isExpanded ? '▼' : '▶'}</span>
              <span className="file-tree-icon file-tree-icon-folder">📁</span>
              <span className="file-tree-label">{e.name}</span>
            </button>
            {hasChildren && (
              <div className="file-tree-children">
                {renderEntries(path)}
              </div>
            )}
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

  return (
    <div className="file-tree">
      <div className="file-tree-root">{renderEntries('')}</div>
    </div>
  )
}

function ChatCodeBlock({ content, language }) {
  const [copied, setCopied] = useState(false)
  const copy = () => {
    navigator.clipboard.writeText(content).then(() => { setCopied(true); setTimeout(() => setCopied(false), 2000) }).catch(() => {})
  }
  const label = codeBlockLabel(language)
  const highlightLang = HIGHLIGHT_LANG[language] || language || 'text'
  return (
    <div className="chat-code-block">
      <div className="chat-code-block-header">
        <span className="chat-code-block-lang">{label}</span>
        <button type="button" className="chat-code-block-copy" onClick={copy} title="Copiar" aria-label="Copiar">
          {copied ? (
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
          ) : (
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
          )}
        </button>
      </div>
      <div className="chat-code-block-body">
        <SyntaxHighlighter
          language={highlightLang}
          style={dracula}
          customStyle={{ margin: 0, padding: '0.75rem 1rem', background: 'transparent', fontSize: '0.85rem', lineHeight: 1.45 }}
          codeTagProps={{ style: { fontFamily: 'var(--font-mono)' } }}
          showLineNumbers={false}
          PreTag="pre"
        >
          {content}
        </SyntaxHighlighter>
      </div>
    </div>
  )
}

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
  const [chatImageBase64, setChatImageBase64] = useState(null) // Imagen para que ADA la lea (vision)
  const [chatHistory, setChatHistory] = useState([
    { role: 'ada', text: 'Hola, soy A.D.A. Actúo como tu socio: doy mi opinión, propongo planes y explico el porqué de mis decisiones. ¿Sobre qué quieres que hablemos?' }
  ])
  const [pendingProposal, setPendingProposal] = useState(null)
  const [loading, setLoading] = useState(false)
  const [activeTab, setActiveTab] = useState('seguimiento') // seguimiento, panel, plan, logs, brain, finance
  const [needsHelp, setNeedsHelp] = useState({ steps: [], platforms: [] })
  const [plan, setPlan] = useState(null) // plan actual + avances
  const [agentStatus, setAgentStatus] = useState(null) // estado agregado para Panel
  const [agentConnected, setAgentConnected] = useState(false)
  const [planHistory, setPlanHistory] = useState([]) // planes anteriores
  const [brainConsoleEntries, setBrainConsoleEntries] = useState([])
  const [ollamaStatus, setOllamaStatus] = useState({ reachable: false, model_ready: false, error: '', models_available: [] })
  const [selfCheck, setSelfCheck] = useState(null)

  const chatEndRef = useRef(null)
  const chatAbortRef = useRef(null)
  const chatTimeoutRef = useRef(null)
  const chatInputRef = useRef(null)
  const recognitionRef = useRef(null)
  const speakResponseRef = useRef(false)
  const lastSendWasVoiceRef = useRef(false)
  const silenceTimeoutRef = useRef(null)
  const voiceConversationModeRef = useRef(false)

  const [voiceListening, setVoiceListening] = useState(false)
  const [voiceInterimText, setVoiceInterimText] = useState('')
  const [pendingVoiceSend, setPendingVoiceSend] = useState('')
  const [voiceConversationMode, setVoiceConversationMode] = useState(() => {
    try { return localStorage.getItem('ada_voice_conversation') === '1' } catch (e) { return true }
  })
  const [adaToolsOpen, setAdaToolsOpen] = useState(false)
  const [adaToolsResult, setAdaToolsResult] = useState(null)
  const [adaToolsLoading, setAdaToolsLoading] = useState(false)
  const [pendingPlan, setPendingPlan] = useState(null)
  const [speakResponse, setSpeakResponse] = useState(() => {
    try { return localStorage.getItem('ada_speak_response') === '1' } catch (e) { return false }
  })
  useEffect(() => { speakResponseRef.current = speakResponse; try { localStorage.setItem('ada_speak_response', speakResponse ? '1' : '0') } catch (e) {} }, [speakResponse])
  useEffect(() => { voiceConversationModeRef.current = voiceConversationMode; try { localStorage.setItem('ada_voice_conversation', voiceConversationMode ? '1' : '0') } catch (e) {} }, [voiceConversationMode])

  const [fileExplorerExpanded, setFileExplorerExpanded] = useState(() => new Set())
  const [fileExplorerCache, setFileExplorerCache] = useState({})
  const [fileExplorerLoadingPath, setFileExplorerLoadingPath] = useState(null)
  const [selectedFilePath, setSelectedFilePath] = useState(null)
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
    fetch(`/api/fs/list${q}`)
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(r.statusText))))
      .then((data) => {
        setFileExplorerCache((c) => ({ ...c, [data.path === '.' ? '' : data.path]: data.entries || [] }))
      })
      .catch(() => setFileExplorerCache((c) => ({ ...c, [path]: [] })))
      .finally(() => setFileExplorerLoadingPath(null))
  }, [fileExplorerCache])

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

  // Conectar / desconectar ADA (ping a backend) y polling cuando esté conectada
  const connectAgent = useCallback(async (connect) => {
    try {
      const res = await API('/agent/connect', {
        method: 'POST',
        body: JSON.stringify({ connect }),
      })
      setAgentConnected(!!res.connected)
      if (res.connected) loadAgentStatus()
      return { ok: !!res.connected, data: res }
    } catch (e) {
      setAgentConnected(false)
      return { ok: false, error: e.message || String(e) }
    }
  }, [loadAgentStatus])

  useEffect(() => {
    let t = null
    if (agentConnected) {
      // refrescar estado del agente cada 8s
      t = setInterval(() => {
        loadAgentStatus()
      }, 8000)
    }
    return () => { if (t) clearInterval(t) }
  }, [agentConnected, loadAgentStatus])

  const loadPlanHistory = useCallback(() => {
    API('/agent/plan-history').then((d) => setPlanHistory(d.history || [])).catch(() => setPlanHistory([]))
  }, [])

  const loadChatHistory = useCallback(() => {
    API('/chat/history').then((d) => {
      if (d.messages && d.messages.length > 0) {
        setChatHistory(d.messages.map((m) => ({
          role: m.role || 'ada',
          text: toMessageString(m.text || m.content),
          brain: m.brain,
          imageBase64: m.imageBase64 || null,
        })))
      }
    }).catch(() => { })
  }, [])

  const saveChatHistory = useCallback((history) => {
    if (!history || history.length === 0) return
    API('/chat/history', {
      method: 'POST',
      body: JSON.stringify({
        history: history.map((m) => ({ role: m.role, text: toMessageString(m.text), brain: m.brain }))
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

  // Comprobar estado de ADA al montar la app (no conecta automáticamente, solo indica disponibilidad)
  useEffect(() => {
    API('/agent/health').then((h) => {
      try {
        setAgentConnected(!!(h && h['agent-core']))
      } catch (e) { setAgentConnected(false) }
    }).catch(() => setAgentConnected(false))
  }, [])

  useEffect(scrollToBottom, [chatHistory])

  const SILENCE_MS = 1800

  const startVoiceListening = useCallback(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SpeechRecognition) {
      alert('Tu navegador no soporta reconocimiento de voz. Usa Chrome o Edge.')
      return
    }
    if (recognitionRef.current) {
      if (silenceTimeoutRef.current) {
        clearTimeout(silenceTimeoutRef.current)
        silenceTimeoutRef.current = null
      }
      try { recognitionRef.current.stop() } catch (e) {}
      recognitionRef.current = null
      setVoiceListening(false)
      setVoiceInterimText('')
      const text = (chatInputRef.current?.textContent || chatMessage || '').trim()
      if (text && !loading) {
        lastSendWasVoiceRef.current = true
        setChatMessage('')
        setChatImageBase64(null)
        if (chatInputRef.current) chatInputRef.current.textContent = ''
        setPendingVoiceSend(text)
      }
      return
    }
    const rec = new SpeechRecognition()
    rec.continuous = true
    rec.interimResults = true
    rec.lang = 'es-ES'
    rec.onresult = (e) => {
      const last = e.resultIndex
      const r = e.results[last]
      const text = Array.from(r).map((x) => x.transcript).join('').trim()
      if (r.isFinal) {
        setVoiceInterimText('')
        if (text) {
          const el = chatInputRef.current
          if (el) {
            const current = (el.textContent || '').trim()
            const next = current ? current + ' ' + text : text
            el.textContent = next
            setChatMessage(next)
          }
          if (silenceTimeoutRef.current) clearTimeout(silenceTimeoutRef.current)
          silenceTimeoutRef.current = setTimeout(() => {
            silenceTimeoutRef.current = null
            const transcript = (chatInputRef.current && chatInputRef.current.textContent || '').trim()
            if (!transcript || loading) return
            try { if (recognitionRef.current) recognitionRef.current.stop() } catch (err) {}
            lastSendWasVoiceRef.current = true
            setChatMessage('')
            setChatImageBase64(null)
            if (chatInputRef.current) chatInputRef.current.textContent = ''
            setPendingVoiceSend(transcript)
            setVoiceListening(false)
            setVoiceInterimText('')
          }, SILENCE_MS)
        }
      } else {
        setVoiceInterimText(text)
      }
    }
    rec.onend = () => {
      if (silenceTimeoutRef.current) {
        clearTimeout(silenceTimeoutRef.current)
        silenceTimeoutRef.current = null
      }
      if (recognitionRef.current === rec) {
        recognitionRef.current = null
        setVoiceListening(false)
        setVoiceInterimText('')
      }
    }
    rec.onerror = () => {
      if (silenceTimeoutRef.current) {
        clearTimeout(silenceTimeoutRef.current)
        silenceTimeoutRef.current = null
      }
      if (recognitionRef.current === rec) {
        recognitionRef.current = null
        setVoiceListening(false)
        setVoiceInterimText('')
      }
    }
    try {
      rec.start()
      recognitionRef.current = rec
      setVoiceListening(true)
      setVoiceInterimText('')
    } catch (err) {
      setVoiceListening(false)
      setVoiceInterimText('')
    }
  }, [chatMessage, loading])
  useEffect(() => {
    if (!pendingVoiceSend) return
    const msg = pendingVoiceSend
    setPendingVoiceSend('')
    sendChat(msg)
  }, [pendingVoiceSend])

  const speakText = useCallback((text, onEnd) => {
    if (!text || !window.speechSynthesis) return
    window.speechSynthesis.cancel()
    const clean = text.replace(/\*\*[^*]*\*\*/g, '').replace(/\n+/g, '. ').trim()
    if (!clean) return
    const u = new SpeechSynthesisUtterance(clean)
    u.lang = 'es-ES'
    u.rate = 0.95
    if (typeof onEnd === 'function') {
      u.onend = () => { onEnd() }
      u.onerror = () => { onEnd() }
    }
    window.speechSynthesis.speak(u)
  }, [])

  useEffect(() => {
    return () => {
      if (silenceTimeoutRef.current) {
        clearTimeout(silenceTimeoutRef.current)
        silenceTimeoutRef.current = null
      }
      if (recognitionRef.current) {
        try { recognitionRef.current.stop() } catch (e) {}
        recognitionRef.current = null
      }
    }
  }, [])

  const sendChat = (overrideMessage) => {
    const raw = overrideMessage !== undefined && overrideMessage !== null ? overrideMessage : (chatMessage || '')
    const msg = toMessageString(raw).trim()
    if (!msg && !chatImageBase64) return
    const imageToSend = chatImageBase64
    setChatMessage('')
    setChatImageBase64(null)
    if (chatInputRef.current) chatInputRef.current.textContent = ''
    const userText = msg || '(imagen adjunta)'
    setChatHistory(h => [...h, { role: 'user', text: userText, imageBase64: imageToSend || null }])
    setLoading(true)

    if (chatTimeoutRef.current) clearTimeout(chatTimeoutRef.current)
    if (chatAbortRef.current) chatAbortRef.current.abort()
    const controller = new AbortController()
    chatAbortRef.current = controller

    const history = chatHistory.slice(-10).map((m) => ({
      role: m.role === 'ada' ? 'assistant' : 'user',
      content: toMessageString(m.text),
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
        const userText = toMessageString(last?.role === 'user' ? last.text : '')
        if (userText) { setTimeout(() => { setChatMessage(userText); if (chatInputRef.current) chatInputRef.current.textContent = userText }, 0) }
        return [...h.slice(0, -1), { role: 'ada', text: 'Tiempo de espera agotado. Edita tu mensaje abajo y vuelve a intentar, o revisa que Ollama y agent-core estén activos.' }]
      })
      setLoading(false)
    }, 200000)

    const body = { message: msg || '¿Qué ves en esta imagen?', use_ollama: true, history }
    if (imageToSend) body.image_base64 = imageToSend
    API('/chat', {
      method: 'POST',
      body: JSON.stringify(body),
      signal: controller.signal,
    })
      .then((res) => {
        clearLoading()
        const responseText = toMessageString(res.response)
        const newAda = responseText ? { role: 'ada', text: responseText, brain: res.brain } : null
        setChatHistory(h => {
          const next = newAda ? [...h, newAda] : h
          return next
        })
        if (speakResponseRef.current || lastSendWasVoiceRef.current) {
          const wasVoice = lastSendWasVoiceRef.current
          lastSendWasVoiceRef.current = false
          if (responseText) {
            speakText(responseText, () => {
              if (wasVoice && voiceConversationModeRef.current && !loading) startVoiceListening()
            })
          }
        }
        const prop = res.proposal || (res.full && res.full.proposal)
        if (res.status === 'pending_approval' || res.task_result?.status === 'pending_approval') {
          setPendingProposal(prop)
        }
        if (res.status === 'pending_plan' && Array.isArray(res.pending_plan) && res.pending_plan.length > 0) {
          setPendingPlan(res.pending_plan)
        } else {
          setPendingPlan(null)
        }
        loadNeedsHelp()
        loadPlan()
      })
      .catch((e) => {
        clearLoading()
        if (e.name === 'AbortError') {
          setChatHistory(h => {
            const last = h[h.length - 1]
            const userText = toMessageString(last?.role === 'user' ? last.text : '')
            if (userText) { setTimeout(() => { setChatMessage(userText); if (chatInputRef.current) chatInputRef.current.textContent = userText }, 0) }
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
      const userText = toMessageString(last?.role === 'user' ? last.text : '')
      if (userText) { setTimeout(() => { setChatMessage(userText); if (chatInputRef.current) chatInputRef.current.textContent = userText }, 0) }
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

  const handleResetAll = (clearChat = true) => {
    if (!window.confirm('¿Limpiar todo? Se borrarán plan, oferta, aprendizajes y' + (clearChat ? ' el historial del chat. ADA empezará de cero.' : ' (el chat se mantiene).'))) return
    setLoading(true)
    // Vaciar el panel derecho de inmediato para que no siga viendo el plan anterior
    setPlan(null)
    setNeedsHelp({ steps: [], platforms: [] })
    fetch(`/api/autonomous/reset_all?clear_chat=${clearChat}`, { method: 'POST', headers: { 'Content-Type': 'application/json' } })
      .then((r) => r.ok ? r.json() : Promise.reject(new Error(r.statusText)))
      .then((data) => {
        if (clearChat) {
          setChatHistory([{ role: 'ada', text: 'Hola, soy A.D.A. He reiniciado todo. ¿Sobre qué quieres que hablemos o qué plan quieres que proponga?' }])
          saveChatHistory([{ role: 'ada', text: 'Hola, soy A.D.A. He reiniciado todo. ¿Sobre qué quieres que hablemos o qué plan quieres que proponga?' }])
        }
        // Refrescar datos del backend tras un breve retraso para que el reset se haya persistido
        setTimeout(() => {
          loadPlan()
          loadNeedsHelp()
          loadEvents()
          loadAgentStatus()
        }, 500)
        alert(data.message || 'Todo limpiado.')
      })
      .catch((e) => alert('Error: ' + e.message))
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
      {/* COLUMNA IZQUIERDA: EXPLORADOR DE ARCHIVOS */}
      <section className="pane pane-files" aria-label="Explorador de archivos">
        <header className="pane-header pane-header-files">
          <h2 className="file-explorer-title">Archivos</h2>
          <button
            type="button"
            className="secondary"
            style={{ padding: '0.35rem 0.6rem', fontSize: '0.8rem' }}
            onClick={() => {
              setFileExplorerCache({})
              setFileExplorerExpanded(new Set())
              setSelectedFilePath(null)
              fileExplorerFetch('')
            }}
            title="Actualizar raíz"
          >
            Actualizar
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
      </section>
      {/* CENTRO: CHAT & DECISIONS */}
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
            <button
              type="button"
              onClick={async () => {
                const res = await connectAgent(!agentConnected)
                if (res && res.ok) {
                  // toggled state handled inside connectAgent
                } else {
                  alert('No se pudo conectar: ' + (res && res.error ? res.error : 'error'))
                }
              }}
              title="Conectar o desconectar ADA"
              style={{ padding: '0.4rem 0.6rem' }}
            >
              {agentConnected ? 'Desconectar ADA' : 'Conectar ADA'}
            </button>
            <div style={{ width: 10, height: 10, borderRadius: 10, background: agentConnected ? 'var(--success)' : 'var(--muted)', boxShadow: agentConnected ? '0 0 6px rgba(0,200,120,0.2)' : 'none' }} aria-hidden="true" />
          </div>
          <div style={{ fontSize: '0.8rem', opacity: 0.6 }}>Opina, propone planes y explica el porqué de sus decisiones</div>
        </header>

        <div className="chat-container">
          <div className="chat-history">
            {chatHistory.map((m, i) => {
              const msgText = toMessageString(m.text)
              return (
              <div key={i} className={`message message-${m.role} animate-fade-in`}>
                <div className="avatar">{m.role === 'ada' ? 'A' : 'T'}</div>
                <div className="message-bubble">
                  {m.role === 'user' && m.imageBase64 && (
                    <div style={{ marginBottom: '0.5rem' }}>
                      <img
                        src={m.imageBase64.startsWith('data:') ? m.imageBase64 : `data:image/jpeg;base64,${m.imageBase64}`}
                        alt="Imagen enviada"
                        style={{ maxWidth: '100%', maxHeight: 200, borderRadius: 8, display: 'block' }}
                      />
                    </div>
                  )}
                  {m.brain === 'advanced' && (
                    <div className="brain-indicator advanced">
                      <span className="brain-icon">🧠</span> DeepSeek-R1
                    </div>
                  )}
                  {m.role === 'ada' ? (() => {
                    const segments = parseMessageWithCodeBlocks(msgText)
                    return segments.map((seg, si) => {
                      if (seg.type === 'code') {
                        return <ChatCodeBlock key={si} content={seg.content} language={seg.language} />
                      }
                      const text = seg.content
                      if (text.includes('**Necesito tu ayuda:**')) {
                        const parts = text.split('**Necesito tu ayuda:**')
                        const after = parts[1] ? parts[1].trim() : ''
                        return (
                          <React.Fragment key={si}>
                            {parts[0].split('\n').map((line, li) => (
                              <div key={li} style={{ marginBottom: line ? '0.2rem' : '0.8rem' }}>{line}</div>
                            ))}
                            {after && (
                              <div className="needs-help-box" style={{ marginTop: '0.75rem', padding: '0.75rem', background: 'rgba(255,180,0,0.15)', borderLeft: '4px solid var(--warn)', borderRadius: 4 }}>
                                <strong>Necesito tu ayuda:</strong>
                                <div style={{ marginTop: 0.25 }}>{after.split('\n').map((l, li) => <div key={li}>{l}</div>)}</div>
                              </div>
                            )}
                          </React.Fragment>
                        )
                      }
                      return text.split('\n').map((line, li) => (
                        <div key={`${si}-${li}`} style={{ marginBottom: line ? '0.2rem' : '0.8rem' }}>{line}</div>
                      ))
                    })
                  })() : (
                    parseMessageWithCodeBlocks(msgText).map((seg, si) => {
                      if (seg.type === 'code') return <ChatCodeBlock key={si} content={seg.content} language={seg.language} />
                      return seg.content.split('\n').map((line, li) => (
                        <div key={`${si}-${li}`} style={{ marginBottom: line ? '0.2rem' : '0.8rem' }}>{line}</div>
                      ))
                    })
                  )}
                </div>
              </div>
            )})}
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
            {pendingPlan && pendingPlan.length > 0 && (
              <div className="glass-card animate-fade-in" style={{ marginBottom: '1rem', borderLeft: '4px solid var(--accent)' }}>
                <div style={{ fontSize: '0.8rem', fontWeight: 'bold', marginBottom: '0.5rem', color: 'var(--accent)' }}>
                  PLAN PENDIENTE DE EJECUCIÓN
                </div>
                <p style={{ fontSize: '0.85rem', marginBottom: '0.75rem' }}>ADA ha propuesto {pendingPlan.length} acción(es). Revisa el mensaje de arriba y ejecuta cuando quieras.</p>
                <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                  <button
                    type="button"
                    onClick={() => {
                      setLoading(true)
                      API('/execute_plan', { method: 'POST', body: JSON.stringify({ plan: pendingPlan }) })
                        .then((data) => {
                          const results = (data.results || []).join('\n')
                          setChatHistory(h => [...h, { role: 'ada', text: '**Resultado de ejecutar el plan:**\n\n' + (results || '(sin salida)') }])
                          setPendingPlan(null)
                        })
                        .catch((e) => {
                          setChatHistory(h => [...h, { role: 'ada', text: 'Error al ejecutar el plan: ' + e.message }])
                          setPendingPlan(null)
                        })
                        .finally(() => setLoading(false))
                    }}
                  >
                    Ejecutar plan
                  </button>
                  <button type="button" className="secondary" onClick={() => setPendingPlan(null)}>Descartar plan</button>
                </div>
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
            {/* Herramientas ADA v2/v3: objetivos, investigación, auto-mejora, oportunidades, planes, aprendizaje */}
            <div className="ada-tools-section" style={{ marginBottom: '0.75rem' }}>
              <button
                type="button"
                className="secondary"
                style={{ fontSize: '0.8rem', marginBottom: adaToolsOpen ? '0.5rem' : 0 }}
                onClick={() => setAdaToolsOpen((o) => !o)}
                title="Ver herramientas de las APIs v2/v3 (objetivos, investigación, planes, etc.)"
              >
                {adaToolsOpen ? '▼ Ocultar herramientas ADA' : '▶ Herramientas ADA (v2/v3)'}
              </button>
              {adaToolsOpen && (
                <>
                  <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', margin: '0 0 0.5rem 0' }}>
                    Objetivos, investigación, planes y aprendizaje que ADA genera en segundo plano (APIs v2/v3).
                  </p>
                <div className="ada-tools-buttons" style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem', marginBottom: '0.5rem' }}>
                  <button type="button" className="secondary" style={{ fontSize: '0.75rem' }} title="Lista de objetivos que ADA está trabajando en segundo plano"
                    onClick={async () => {
                      setAdaToolsLoading(true); setAdaToolsResult(null)
                      try {
                        const d = await API('/ada/v2/goals')
                        setAdaToolsResult({ title: 'Objetivos (v2)', data: d })
                      } catch (e) { setAdaToolsResult({ title: 'Error', data: e.message }) }
                      finally { setAdaToolsLoading(false) }
                    }}>Objetivos</button>
                  <button type="button" className="secondary" style={{ fontSize: '0.75rem' }} title="Añadir un objetivo para que ADA lo investigue y genere ideas"
                    onClick={async () => {
                      const goal = window.prompt('Objetivo nuevo (ej: aumentar ingresos con un producto digital):')
                      if (!goal?.trim()) return
                      setAdaToolsLoading(true); setAdaToolsResult(null)
                      try {
                        const d = await API('/ada/v2/goals', { method: 'POST', body: JSON.stringify({ goal: goal.trim() }) })
                        setAdaToolsResult({ title: 'Objetivo añadido', data: d })
                      } catch (e) { setAdaToolsResult({ title: 'Error', data: e.message }) }
                      finally { setAdaToolsLoading(false) }
                    }}>Añadir objetivo</button>
                  <button type="button" className="secondary" style={{ fontSize: '0.75rem' }} title="Investigar un tema: ADA analiza y propone estrategias"
                    onClick={async () => {
                      const goal = window.prompt('¿Qué quieres investigar? (ej: cómo monetizar un blog):')
                      if (!goal?.trim()) return
                      setAdaToolsLoading(true); setAdaToolsResult(null)
                      try {
                        const d = await API('/ada/v3/research', { method: 'POST', body: JSON.stringify({ goal: goal.trim(), context: '' }) })
                        setAdaToolsResult({ title: 'Investigación (v3)', data: typeof d.analysis === 'string' ? d.analysis : d })
                      } catch (e) { setAdaToolsResult({ title: 'Error', data: e.message }) }
                      finally { setAdaToolsLoading(false) }
                    }}>Investigar</button>
                  <button type="button" className="secondary" style={{ fontSize: '0.75rem' }} title="Análisis de cuellos de botella y sugerencias de mejora del sistema"
                    onClick={async () => {
                      setAdaToolsLoading(true); setAdaToolsResult(null)
                      try {
                        const d = await API('/ada/v2/self-improvement')
                        setAdaToolsResult({ title: 'Auto-mejora (v2)', data: typeof d.analysis === 'string' ? d.analysis : d })
                      } catch (e) { setAdaToolsResult({ title: 'Error', data: e.message }) }
                      finally { setAdaToolsLoading(false) }
                    }}>Auto-mejora</button>
                  <button type="button" className="secondary" style={{ fontSize: '0.75rem' }} title="Oportunidades mejor puntuadas por ADA"
                    onClick={async () => {
                      setAdaToolsLoading(true); setAdaToolsResult(null)
                      try {
                        const d = await API('/ada/v3/opportunities/top')
                        setAdaToolsResult({ title: 'Oportunidades (v3)', data: d })
                      } catch (e) { setAdaToolsResult({ title: 'Error', data: e.message }) }
                      finally { setAdaToolsLoading(false) }
                    }}>Oportunidades</button>
                  <button type="button" className="secondary" style={{ fontSize: '0.75rem' }} title="Planes de acción generados por el scheduler"
                    onClick={async () => {
                      setAdaToolsLoading(true); setAdaToolsResult(null)
                      try {
                        const d = await API('/ada/v3/plans')
                        setAdaToolsResult({ title: 'Planes (v3)', data: d })
                      } catch (e) { setAdaToolsResult({ title: 'Error', data: e.message }) }
                      finally { setAdaToolsLoading(false) }
                    }}>Planes</button>
                  <button type="button" className="secondary" style={{ fontSize: '0.75rem' }} title="Aprendizajes recientes (experiencias evaluadas)"
                    onClick={async () => {
                      setAdaToolsLoading(true); setAdaToolsResult(null)
                      try {
                        const d = await API('/ada/v3/learning')
                        setAdaToolsResult({ title: 'Aprendizaje (v3)', data: d })
                      } catch (e) { setAdaToolsResult({ title: 'Error', data: e.message }) }
                      finally { setAdaToolsLoading(false) }
                    }}>Aprendizaje</button>
                </div>
                </>
              )}
              {adaToolsLoading && <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.35rem' }}>Cargando…</div>}
              {adaToolsResult && !adaToolsLoading && (
                <div className="ada-tools-result glass-card" style={{ padding: '0.6rem 0.75rem', fontSize: '0.8rem', maxHeight: 220, overflow: 'auto', borderLeft: '4px solid var(--accent)', marginTop: '0.35rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.4rem' }}>
                    <strong>{adaToolsResult.title}</strong>
                    <button type="button" className="secondary" style={{ padding: '0.2rem 0.4rem', fontSize: '0.7rem' }} onClick={() => setAdaToolsResult(null)}>Cerrar</button>
                  </div>
                  <pre style={{ margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-word', fontFamily: 'var(--font-mono)', fontSize: '0.75rem' }}>
                    {typeof adaToolsResult.data === 'string' ? adaToolsResult.data : JSON.stringify(adaToolsResult.data, null, 2)}
                  </pre>
                </div>
              )}
            </div>
            {chatImageBase64 && (
              <div style={{ marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <img src={chatImageBase64.startsWith('data:') ? chatImageBase64 : `data:image/jpeg;base64,${chatImageBase64}`} alt="Adjunta" style={{ maxHeight: 48, borderRadius: 4 }} />
                <button type="button" className="secondary" style={{ fontSize: '0.75rem' }} onClick={() => setChatImageBase64(null)}>Quitar imagen</button>
              </div>
            )}
            {voiceListening && (
              <div className="voice-listening-bar">
                <span className="voice-listening-dot" />
                <span className="voice-listening-text">Te escucho. Habla y al terminar responderé con voz (no hace falta Enviar).</span>
                {voiceInterimText && <span className="voice-interim">"{voiceInterimText}"</span>}
              </div>
            )}
            <div className="chat-image-toolbar">
              <span className="chat-image-toolbar-label">Voz:</span>
              <button
                type="button"
                className={`chat-image-btn chat-voice-btn ${voiceListening ? 'active' : ''}`}
                title={voiceListening ? 'Detener y enviar ya' : 'Conversación por voz con ADA'}
                onClick={startVoiceListening}
                style={voiceListening ? { background: 'rgba(255,80,80,0.25)', borderColor: 'var(--warn)' } : {}}
              >
                {voiceListening ? '⏹ Detener' : '🎤 Hablar con ADA'}
              </button>
              <label style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', cursor: 'pointer', fontSize: '0.8rem', color: 'var(--subtle)' }}>
                <input type="checkbox" checked={voiceConversationMode} onChange={(e) => setVoiceConversationMode(e.target.checked)} />
                Conversación continua
              </label>
              <label style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', cursor: 'pointer', fontSize: '0.8rem', color: 'var(--subtle)' }}>
                <input type="checkbox" checked={speakResponse} onChange={(e) => setSpeakResponse(e.target.checked)} />
                Leer respuesta (texto)
              </label>
              <span className="chat-image-toolbar-label">Imagen:</span>
              <label className="chat-image-btn">
                <input type="file" accept="image/*" style={{ display: 'none' }} onChange={(e) => { const f = e.target.files?.[0]; if (f) { const r = new FileReader(); r.onload = () => setChatImageBase64(r.result); r.readAsDataURL(f) } e.target.value = '' }} />
                📷 Elegir archivo
              </label>
              <button
                type="button"
                className="chat-image-btn"
                title="Pegar imagen desde el portapapeles (Ctrl+V en el cuadro también)"
                onClick={async () => {
                  try {
                    const items = await navigator.clipboard?.read?.()
                    if (!items) return
                    for (const item of items) {
                      const imageType = item.types.find(t => t.startsWith('image/'))
                      if (imageType) {
                        const blob = await item.getType(imageType)
                        const r = new FileReader()
                        r.onload = () => setChatImageBase64(r.result)
                        r.readAsDataURL(blob)
                        return
                      }
                    }
                  } catch (_) {}
                }}
              >
                📋 Pegar imagen
              </button>
            </div>
            <div className="chat-input-row">
              <div
                ref={chatInputRef}
                className="chat-input-editable"
                contentEditable={!loading}
                suppressContentEditableWarning
                role="textbox"
                aria-placeholder="Hablar con tu socio: metas, opiniones, por qué ese plan... (o pega/adjunta una imagen)"
                data-placeholder="Hablar con tu socio: metas, opiniones, por qué ese plan... (o pega/adjunta una imagen)"
                onInput={() => setChatMessage(chatInputRef.current?.textContent?.replace(/\n/g, ' ') ?? '')}
                onPaste={(e) => {
                  const dt = e.clipboardData
                  // Leer texto ya: clipboardData solo está disponible de forma síncrona durante el evento
                  const textPlain = dt ? (dt.getData('text/plain') || '') : ''
                  let file = null
                  if (dt) {
                    if (dt.files?.length && dt.files[0].type.startsWith('image/')) file = dt.files[0]
                    if (!file && dt.items) {
                      for (let i = 0; i < dt.items.length; i++) {
                        if (dt.items[i].type.indexOf('image') !== -1) {
                          file = dt.items[i].getAsFile()
                          break
                        }
                      }
                    }
                  }
                  if (file) {
                    e.preventDefault()
                    const r = new FileReader()
                    r.onload = () => setChatImageBase64(r.result)
                    r.readAsDataURL(file)
                    return
                  }
                  // Pegado de texto: insertar nosotros para controlar formato (ya tenemos textPlain leído en sync)
                  if (textPlain) {
                    e.preventDefault()
                    document.execCommand('insertText', false, textPlain)
                    setChatMessage(chatInputRef.current?.textContent?.replace(/\n/g, ' ') ?? '')
                    return
                  }
                  // Si no había imagen ni texto en el evento, intentar API async solo para imagen (opcional)
                  if (typeof navigator.clipboard?.read === 'function') {
                    e.preventDefault()
                    navigator.clipboard.read().then((items) => {
                      for (const item of items) {
                        const imageType = item.types.find(t => t.startsWith('image/'))
                        if (imageType) {
                          return item.getType(imageType).then((blob) => {
                            const r = new FileReader()
                            r.onload = () => setChatImageBase64(r.result)
                            r.readAsDataURL(blob)
                          })
                        }
                      }
                    }).catch(() => {})
                  }
                }}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault()
                    if (!loading) sendChat()
                  }
                }}
              />
              <button onClick={sendChat} disabled={loading || (!chatMessage.trim() && !chatImageBase64)}>
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
            <button type="button" className="danger" style={{ marginLeft: 'auto', fontSize: '0.75rem', padding: '0.35rem 0.6rem' }} onClick={() => handleResetAll(true)} title="Borrar plan, oferta, aprendizajes y chat. ADA empieza de cero.">Limpiar todo</button>
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
              <button type="button" className="danger" style={{ fontSize: '0.8rem' }} onClick={() => handleResetAll(true)}>Limpiar todo e iniciar de nuevo</button>
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

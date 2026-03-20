import React, { useEffect, useState } from 'react'
import SyntaxHighlighter from 'react-syntax-highlighter'
import { dracula } from 'react-syntax-highlighter/dist/esm/styles/hljs'

const HIGHLIGHT_LANG = { js: 'javascript', javascript: 'javascript', jsx: 'jsx', ts: 'typescript', tsx: 'tsx', py: 'python', html: 'html', css: 'css', json: 'json', md: 'markdown', sh: 'bash', sql: 'sql', yaml: 'yaml', yml: 'yaml' }
const CODE_LABEL = { html: 'HTML', css: 'CSS', js: 'JavaScript', javascript: 'JavaScript', jsx: 'JSX', ts: 'TypeScript', tsx: 'TSX', py: 'Python', json: 'JSON', md: 'Markdown', sh: 'Shell', sql: 'SQL', yaml: 'YAML', yml: 'YAML' }

function toMessageString(v) {
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
  return CODE_LABEL[lang] || (lang ? lang.toUpperCase() : 'Code')
}

function ChatCodeBlock({ content, language }) {
  const [copied, setCopied] = useState(false)
  const copy = () => {
    navigator.clipboard.writeText(content).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    })
  }
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

export default function ChatPane({
  executionMode,
  onToggleExecutionMode,
  theme,
  onToggleTheme,
  agentConnected,
  loading,
  chatHistory,
  chatMessage,
  setChatMessage,
  onSendChat,
  chatInputRef,
  chatEndRef,
}) {
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [chatHistory, chatEndRef])

  return (
    <section className="pane pane-chat" aria-label="Chat con ADA">
      <header className="pane-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div className="avatar" style={{ width: 32, height: 32, fontSize: '1rem', background: 'var(--accent)', color: '#1a1a1a', display: 'flex', alignItems: 'center', justifyContent: 'center', borderRadius: '50%', fontWeight: 'bold' }}>A</div>
          <h2 style={{ margin: 0, fontSize: '1.2rem', fontWeight: 700 }}>ADA <span style={{ fontSize: '0.8rem', opacity: 0.7, fontWeight: 400 }}>asistente de desarrollo</span></h2>
        </div>
        <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
          <button
            type="button"
            className={executionMode ? '' : 'secondary'}
            onClick={() => onToggleExecutionMode()}
            title="Modo ejecución (salida estricta)"
            style={{ padding: '6px 10px', border: executionMode ? '1px solid var(--accent)' : undefined }}
          >
            {executionMode ? '⚡ Ejecución: ON' : '⚡ Ejecución: OFF'}
          </button>
          <button type="button" className="secondary" onClick={onToggleTheme} title="Tema" style={{ padding: '6px' }}>
            {theme === 'dark' ? '☀️' : '🌙'}
          </button>
          <div style={{ width: 10, height: 10, borderRadius: '50%', background: agentConnected ? 'var(--success)' : 'var(--muted)', border: '2px solid rgba(255,255,255,0.1)' }} />
        </div>
      </header>

      <div className="chat-container">
        <div className="chat-history">
          {chatHistory.map((m, i) => (
            <div key={i} className={`message message-${m.role} animate-fade-in`}>
              <div className="avatar">{m.role === 'ada' ? 'A' : 'T'}</div>
              <div className="message-bubble">
                {m.role === 'user' && m.imageBase64 && (
                  <img
                    src={m.imageBase64.startsWith('data:') ? m.imageBase64 : `data:image/jpeg;base64,${m.imageBase64}`}
                    style={{ maxWidth: '100%', borderRadius: 8, marginBottom: 8 }}
                    alt="User upload"
                  />
                )}
                {parseMessageWithCodeBlocks(toMessageString(m.text)).map((seg, si) =>
                  seg.type === 'code' ? (
                    <ChatCodeBlock key={si} content={seg.content} language={seg.language} />
                  ) : (
                    seg.content.split('\n').map((l, li) => (
                      <div key={`${si}-${li}`} style={{ marginBottom: l ? '0.2rem' : '0.8rem' }}>{l}</div>
                    ))
                  )
                )}
              </div>
            </div>
          ))}
          {loading && <div className="message message-ada"><div className="avatar">A</div><div className="message-bubble">ADA está pensando...</div></div>}
          <div ref={chatEndRef} />
        </div>

        <div className="chat-footer">
          <div className="chat-input-row">
            <div
              ref={chatInputRef}
              className="chat-input-editable"
              contentEditable={!loading}
              onInput={() => setChatMessage(chatInputRef.current?.textContent || '')}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault()
                  if (!loading) onSendChat()
                }
              }}
              data-placeholder="Mensaje para ADA..."
            />
            <button onClick={onSendChat} disabled={loading}>Enviar</button>
          </div>
        </div>
      </div>
    </section>
  )
}


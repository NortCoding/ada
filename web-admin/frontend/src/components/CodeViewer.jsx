import React from 'react'
import SyntaxHighlighter from 'react-syntax-highlighter'
import { dracula } from 'react-syntax-highlighter/dist/esm/styles/hljs'

const HIGHLIGHT_LANG = { js: 'javascript', javascript: 'javascript', jsx: 'jsx', ts: 'typescript', tsx: 'tsx', py: 'python', html: 'html', css: 'css', json: 'json', md: 'markdown', sh: 'bash', sql: 'sql', yaml: 'yaml', yml: 'yaml' }
const CODE_LABEL = { html: 'HTML', css: 'CSS', js: 'JavaScript', javascript: 'JavaScript', jsx: 'JSX', ts: 'TypeScript', tsx: 'TSX', py: 'Python', json: 'JSON', md: 'Markdown', sh: 'Shell', sql: 'SQL', yaml: 'YAML', yml: 'YAML' }

function codeBlockLabel(lang) {
  return CODE_LABEL[lang] || (lang ? lang.toUpperCase() : 'Code')
}

export default function CodeViewer({ path, content, loading }) {
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
        <SyntaxHighlighter
          language={highlightLang}
          style={dracula}
          customStyle={{ margin: 0, padding: '1rem', background: 'transparent', fontSize: '0.85rem' }}
          showLineNumbers={true}
        >
          {content || ''}
        </SyntaxHighlighter>
      </div>
    </div>
  )
}


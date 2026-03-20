import React, { useEffect } from 'react'

export default function FileExplorer({ expanded, onToggle, cache, loadingPath, onSelect, selectedPath, onFetch }) {
  const loadRoot = () => {
    if (!cache['']) onFetch('')
  }

  useEffect(() => {
    loadRoot()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

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
      const icon = ['py', 'js', 'jsx', 'ts', 'tsx', 'json', 'md', 'yml', 'yaml'].includes(ext) ? '📄' : '📄'
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


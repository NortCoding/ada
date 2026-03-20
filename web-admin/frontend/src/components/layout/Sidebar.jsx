import React from 'react'
import { NavLink } from 'react-router-dom'

const linkStyle = ({ isActive }) => ({
  display: 'flex',
  gap: 10,
  alignItems: 'center',
  padding: '10px 12px',
  borderRadius: 10,
  textDecoration: 'none',
  color: 'var(--text)',
  background: isActive ? 'var(--accent-weak)' : 'transparent',
  border: isActive ? '1px solid var(--border)' : '1px solid transparent',
  fontWeight: 600,
})

export default function Sidebar() {
  return (
    <aside className="pane" style={{ width: 280, borderRight: '1px solid var(--border)', padding: 14, gap: 10 }}>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 4, padding: '6px 6px 14px 6px' }}>
        <div style={{ fontSize: '1.1rem', fontWeight: 800 }}>ADA v1</div>
        <div style={{ fontSize: '0.85rem', color: 'var(--subtle)' }}>Desarrollo</div>
      </div>

      <nav style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        <NavLink to="/v2/developer" style={linkStyle}>💻 Workspace</NavLink>
      </nav>

      <div style={{ marginTop: 'auto', paddingTop: 14, fontSize: '0.8rem', color: 'var(--subtle)' }}>
        Evita ruido: solo endpoints soportados.
      </div>
    </aside>
  )
}


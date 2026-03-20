import React from 'react'
import { useLocation } from 'react-router-dom'
import Sidebar from './Sidebar'
import TopStatusBar from './TopStatusBar'

export default function AppShell({ children }) {
  const location = useLocation()
  const pathParts = location.pathname.split('/')
  // /v2/developer -> developer
  const workspaceKey = pathParts[2] || 'home'

  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: 'var(--bg)' }}>
      <Sidebar />
      <main style={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0, height: '100vh' }}>
        <TopStatusBar workspaceKey={workspaceKey} />
        <div style={{ flex: 1, minHeight: 0 }}>
          {children}
        </div>
      </main>
    </div>
  )
}


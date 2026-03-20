import React from 'react'
import Sidebar from './Sidebar'
import TopStatusBar from './TopStatusBar'

export default function AppShell({ children }) {
  // ADA v1: solo workspace de desarrollo
  const workspaceKey = 'developer'

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


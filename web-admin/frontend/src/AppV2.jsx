import React from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import AppShell from './components/layout/AppShell'
import DeveloperWorkspace from './pages/DeveloperWorkspace'

export default function AppV2() {
  return (
    <BrowserRouter>
      <AppShell>
        <Routes>
          <Route path="/v2/developer" element={<DeveloperWorkspace />} />
          <Route path="*" element={<Navigate to="/v2/developer" replace />} />
        </Routes>
      </AppShell>
    </BrowserRouter>
  )
}


import React from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import AppShell from './components/layout/AppShell'
import HomePage from './pages/HomePage'
import DeveloperWorkspace from './pages/DeveloperWorkspace'
import BusinessWorkspace from './pages/BusinessWorkspace'
import ResearchWorkspace from './pages/ResearchWorkspace'
import RoadmapPage from './pages/RoadmapPage'
import SystemMonitorPage from './pages/SystemMonitorPage'

export default function AppV2() {
  return (
    <BrowserRouter>
      <AppShell>
        <Routes>
          <Route path="/v2" element={<HomePage />} />
          <Route path="/v2/developer" element={<DeveloperWorkspace />} />
          <Route path="/v2/business" element={<BusinessWorkspace />} />
          <Route path="/v2/research" element={<ResearchWorkspace />} />
          <Route path="/v2/roadmap" element={<RoadmapPage />} />
          <Route path="/v2/monitor" element={<SystemMonitorPage />} />
          <Route path="*" element={<Navigate to="/v2" replace />} />
        </Routes>
      </AppShell>
    </BrowserRouter>
  )
}


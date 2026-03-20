import React, { useEffect, useState } from 'react'
import { api } from '../api/client'
import SystemMonitorPageLegacy from '../components/SystemMonitorPage'

export default function SystemMonitorPage() {
  const [systemMonitor, setSystemMonitor] = useState(null)

  useEffect(() => {
    api('/system/monitor')
      .then(setSystemMonitor)
      .catch(() => setSystemMonitor({ error: 'No disponible' }))
  }, [])

  return (
    <SystemMonitorPageLegacy
      api={api}
      onBack={() => window.history.back()}
      systemMonitor={systemMonitor}
      setSystemMonitor={setSystemMonitor}
    />
  )
}


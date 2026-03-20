import React from 'react'
import GoalsView from '../components/roadmap/GoalsView'
import RoadmapView from '../components/roadmap/RoadmapView'

export default function RoadmapPage() {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, height: '100%', padding: '1rem', boxSizing: 'border-box' }}>
      <GoalsView />
      <RoadmapView />
    </div>
  )
}


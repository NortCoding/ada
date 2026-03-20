import { useCallback, useMemo, useState } from 'react'

function uid() {
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`
}

export function useTaskQueue() {
  const [tasks, setTasks] = useState([])

  const createTask = useCallback((task) => {
    const t = {
      id: uid(),
      type: task.type || 'generic',
      title: task.title || 'Task',
      status: 'pending', // pending|running|completed|failed
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      input: task.input || null,
      output: null,
      error: null,
    }
    setTasks((prev) => [t, ...prev])
    return t
  }, [])

  const updateTask = useCallback((id, patch) => {
    setTasks((prev) =>
      prev.map((t) =>
        t.id === id ? { ...t, ...patch, updatedAt: new Date().toISOString() } : t
      )
    )
  }, [])

  const startTask = useCallback((id) => updateTask(id, { status: 'running' }), [updateTask])
  const completeTask = useCallback((id, output) => updateTask(id, { status: 'completed', output }), [updateTask])
  const failTask = useCallback((id, error) => updateTask(id, { status: 'failed', error: String(error || 'Failed') }), [updateTask])

  const stats = useMemo(() => {
    const counts = { pending: 0, running: 0, completed: 0, failed: 0 }
    for (const t of tasks) counts[t.status] = (counts[t.status] || 0) + 1
    return counts
  }, [tasks])

  return { tasks, stats, createTask, startTask, completeTask, failTask, updateTask }
}


import { useCallback, useMemo, useState } from 'react'

function uid() {
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`
}

export function useApprovals() {
  const [approvals, setApprovals] = useState([])

  const requestApproval = useCallback((a) => {
    const item = {
      id: uid(),
      kind: a.kind, // run_command|apply_patch|create_file
      title: a.title || 'Approval required',
      payload: a.payload || {},
      preview: a.preview || null,
      status: 'pending', // pending|executing|approved|rejected|done|error
      result: null,
      error: null,
      createdAt: new Date().toISOString(),
    }
    setApprovals((prev) => [item, ...prev])
    return item
  }, [])

  const approve = useCallback((id) => {
    setApprovals((prev) => prev.map((a) => (a.id === id ? { ...a, status: 'approved' } : a)))
  }, [])

  const reject = useCallback((id) => {
    setApprovals((prev) => prev.map((a) => (a.id === id ? { ...a, status: 'rejected' } : a)))
  }, [])

  const markExecuting = useCallback((id) => {
    setApprovals((prev) => prev.map((a) => (a.id === id ? { ...a, status: 'executing', error: null } : a)))
  }, [])

  const markDone = useCallback((id, result) => {
    setApprovals((prev) => prev.map((a) => (a.id === id ? { ...a, status: 'done', result: result ?? null, error: null } : a)))
  }, [])

  const markError = useCallback((id, error) => {
    setApprovals((prev) =>
      prev.map((a) => (a.id === id ? { ...a, status: 'error', error: String(error || 'Error') } : a))
    )
  }, [])

  const pending = useMemo(() => approvals.filter((a) => a.status === 'pending' || a.status === 'executing' || a.status === 'error'), [approvals])

  return { approvals, pending, requestApproval, approve, reject, markExecuting, markDone, markError }
}


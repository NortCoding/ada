import { useMemo } from 'react'

export function useWorkspaceAgent(workspaceKey) {
  // Maps v2 workspace routes to agent_type.
  return useMemo(() => {
    if (workspaceKey === 'developer') return 'developer'
    if (workspaceKey === 'business') return 'business'
    if (workspaceKey === 'research') return 'research'
    return 'general'
  }, [workspaceKey])
}


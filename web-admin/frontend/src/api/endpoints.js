// Single source of truth for supported backend endpoints.
// Do NOT add endpoints here unless they exist in web-admin backend proxy.

export const ENDPOINTS = {
  chat: '/chat',
  agentHealth: '/agent/health',
  agentStatus: '/agent/status',
  autonomousPlan: '/autonomous/plan',
  systemMonitor: '/system/monitor',
  agentMarketProposals: '/agent_market/proposals',
  agentMarketPropose: '/agent_market/propose',
  fsList: '/fs/list',
  fsRead: '/fs/read',
  fsWrite: '/fs/write',
  approveExecute: '/approve/execute',
}


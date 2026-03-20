import React from 'react'

export default function AgentMarketPage({
  api,
  onBack,
  agentProposals,
  setAgentProposals,
  proposeDomain,
  setProposeDomain,
  proposeSkills,
  setProposeSkills,
  proposePurpose,
  setProposePurpose,
  proposeSubmitting,
  setProposeSubmitting,
  proposeError,
  setProposeError,
}) {
  const refreshMarket = () => {
    api('/agent_market/proposals')
      .then((d) => setAgentProposals(d.proposals || []))
      .catch(() => setAgentProposals([]))
  }

  const submitPropose = (e) => {
    e.preventDefault()
    const domain = proposeDomain.trim()
    if (!domain) {
      setProposeError('Indica el dominio/nombre del agente')
      return
    }
    const skills = proposeSkills.trim()
      ? proposeSkills.split(/[\s,]+/).map((s) => s.trim()).filter(Boolean)
      : []

    setProposeError(null)
    setProposeSubmitting(true)

    api('/agent_market/propose', {
      method: 'POST',
      body: JSON.stringify({ domain, required_skills: skills, purpose: proposePurpose.trim() }),
    })
      .then(() => {
        setProposeDomain('')
        setProposeSkills('')
        setProposePurpose('')
        refreshMarket()
      })
      .catch((err) => setProposeError(err.message || 'Error al enviar'))
      .finally(() => setProposeSubmitting(false))
  }

  return (
    <div className="app-layout" style={{ gridTemplateColumns: 'minmax(0, 1fr)', padding: '2rem', overflow: 'auto', gap: '2rem' }}>
      <div style={{ gridColumn: '1/-1', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <button type="button" className="secondary" onClick={onBack}>← Dashboard</button>
          <h1 style={{ margin: 0, fontSize: '1.8rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>🛒 Agent Market</h1>
        </div>
        <button className="primary" onClick={refreshMarket}>↻ Refrescar Market</button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '350px 1fr', gap: '2rem', alignItems: 'start' }}>
        <div className="glass-panel" style={{ padding: '1.5rem' }}>
          <h3 style={{ marginTop: 0, borderBottom: '1px solid var(--border)', paddingBottom: '0.75rem', marginBottom: '1.25rem' }}>✨ Proponer Nuevo Agente</h3>
          <p style={{ fontSize: '0.85rem', color: 'var(--subtle)', marginBottom: '1.5rem' }}>
            Define las habilidades y el dominio de un nuevo nodo. La solicitud será evaluada por el core de ADA y los policy engines.
          </p>
          <form onSubmit={submitPropose} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <label style={{ display: 'flex', flexDirection: 'column', gap: 6, fontSize: '0.9rem', fontWeight: 600 }}>
              Dominio o Rol
              <input type="text" value={proposeDomain} onChange={(e) => setProposeDomain(e.target.value)} placeholder="Ej: DevOps, copywriter..." />
            </label>
            <label style={{ display: 'flex', flexDirection: 'column', gap: 6, fontSize: '0.9rem', fontWeight: 600 }}>
              Habilidades (separadas por coma)
              <input type="text" value={proposeSkills} onChange={(e) => setProposeSkills(e.target.value)} placeholder="python, bash, research..." />
            </label>
            <label style={{ display: 'flex', flexDirection: 'column', gap: 6, fontSize: '0.9rem', fontWeight: 600 }}>
              Propósito
              <textarea value={proposePurpose} onChange={(e) => setProposePurpose(e.target.value)} placeholder="Breve descripción del objetivo de este agente..." rows={3} />
            </label>
            {proposeError && <div style={{ color: 'var(--danger)', fontSize: '0.85rem', padding: '0.5rem', background: 'rgba(239, 68, 68, 0.1)', borderRadius: '6px' }}>{proposeError}</div>}
            <button type="submit" disabled={proposeSubmitting} className="primary" style={{ marginTop: '0.5rem', padding: '0.8rem' }}>
              {proposeSubmitting ? 'Generando Propuesta...' : '✦ Enviar Propuesta'}
            </button>
          </form>
        </div>

        <div>
          <h3 style={{ margin: '0 0 1rem 0' }}>Mercado y Base de Nodos Autorizados</h3>
          {agentProposals.length === 0 ? (
            <div className="glass-panel" style={{ padding: '3rem', textAlign: 'center', color: 'var(--subtle)' }}>
              <div style={{ fontSize: '3rem', marginBottom: '1rem', opacity: 0.5 }}>📦</div>
              <p>No hay agentes registrados en el mercado aún.</p>
            </div>
          ) : (
            <div className="market-grid">
              {agentProposals.map((p) => (
                <div key={p.id} className="glass-panel market-card animate-fade-in">
                  <h4>
                    {p.agent_name}
                    <span className={`badge ${p.status === 'activo' || p.status === 'approved' ? 'badge-success' : 'badge-warn'}`}>
                      {p.status}
                    </span>
                  </h4>
                  <p>{p.purpose || 'Sin propósito especificado. Empleado bajo demanda general.'}</p>
                  <div className="skills-tags">
                    {(p.suggested_skills ? (Array.isArray(p.suggested_skills) ? p.suggested_skills : p.suggested_skills.split(',')) : []).map((skill, i) => (
                      <span key={i} className="skill-tag">{skill.trim()}</span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}


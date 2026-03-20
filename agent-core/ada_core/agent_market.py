"""
ADA v3 — Agent Market.
Allows ADA to propose new agents. Proposals require human approval; agents are never auto-created.
"""
from typing import List, Optional

from ada_core import memory_manager


def propose_new_agent(domain: str, required_skills: List[str], purpose: str = "") -> dict:
    """
    Proposes a new agent for a domain with suggested skills.
    Stores in agent_proposals table; status = 'pending'. Human must approve to create.
    Returns the created proposal row as dict or error.
    """
    agent_name = (domain or "unnamed").strip().lower().replace(" ", "_")[:255]
    if not agent_name:
        return {"ok": False, "error": "domain is required"}
    skills_str = ",".join(required_skills[:20]) if required_skills else ""
    conn = memory_manager._get_conn()
    if not conn:
        return {"ok": False, "error": "Database unavailable"}
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO ada_core.agent_proposals (agent_name, purpose, suggested_skills, status)
                VALUES (%s, %s, %s, 'pending')
                RETURNING id, agent_name, purpose, suggested_skills, status, created_at
                """,
                (agent_name, (purpose or "")[:4096], skills_str[:1024]),
            )
            row = cur.fetchone()
            conn.commit()
        if not row:
            return {"ok": False, "error": "Insert failed"}
        return {
            "ok": True,
            "id": row[0],
            "agent_name": row[1],
            "purpose": row[2],
            "suggested_skills": row[3],
            "status": row[4],
            "created_at": str(row[5]) if row[5] else None,
        }
    except Exception as e:
        try:
            conn.rollback()
        except Exception:
            pass
        return {"ok": False, "error": str(e)}
    finally:
        try:
            conn.close()
        except Exception:
            pass


def list_agent_proposals(status: Optional[str] = None) -> List[dict]:
    """Returns list of agent proposals, optionally filtered by status (pending, approved, rejected)."""
    conn = memory_manager._get_conn()
    if not conn:
        return []
    try:
        with conn.cursor() as cur:
            if status:
                cur.execute(
                    """
                    SELECT id, agent_name, purpose, suggested_skills, status, created_at
                    FROM ada_core.agent_proposals WHERE status = %s ORDER BY created_at DESC
                    """,
                    (status,),
                )
            else:
                cur.execute(
                    """
                    SELECT id, agent_name, purpose, suggested_skills, status, created_at
                    FROM ada_core.agent_proposals ORDER BY created_at DESC
                    """
                )
            rows = cur.fetchall()
        return [
            {
                "id": r[0],
                "agent_name": r[1],
                "purpose": r[2],
                "suggested_skills": r[3],
                "status": r[4],
                "created_at": str(r[5]) if r[5] else None,
            }
            for r in rows
        ]
    except Exception:
        return []
    finally:
        try:
            conn.close()
        except Exception:
            pass

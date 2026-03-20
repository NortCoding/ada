"""
ADA v2 — Memory manager.
Stores and retrieves: (1) KV via memory service HTTP, (2) goals/memories/ideas via Postgres.
Never crashes: returns empty lists/dicts or None on failure.
"""
import json
import os
from contextlib import contextmanager
from typing import Any, List, Optional, Tuple

import requests

MEMORY_URL = (os.getenv("MEMORY_URL") or "http://memory-db:3005").strip().rstrip("/")
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))

# Postgres for ada_core schema (goals, memories, ideas)
PG_HOST = os.getenv("PG_HOST", "postgres")
PG_PORT = os.getenv("PG_PORT", "5432")
PG_USER = os.getenv("PG_USER", "ada_user")
PG_PASSWORD = os.getenv("PG_PASSWORD", "supersecret")
PG_DB = os.getenv("PG_DB", "ada_main")


def _get_conn():
    try:
        import psycopg2
        return psycopg2.connect(
            host=PG_HOST,
            port=PG_PORT,
            user=PG_USER,
            password=PG_PASSWORD,
            dbname=PG_DB,
        )
    except Exception:
        return None


class MemoryManager:
    """Unified memory: KV (HTTP) + goals/memories/ideas (Postgres). Safe on failure."""

    # --- KV (memory service) ---
    @staticmethod
    def get_key(key: str) -> Optional[Any]:
        """Get value for key from memory service. Returns None on failure or missing."""
        if not MEMORY_URL:
            return None
        try:
            r = requests.get(f"{MEMORY_URL}/get/{key}", timeout=REQUEST_TIMEOUT)
            if r.status_code != 200:
                return None
            data = r.json() if r.text else {}
            return data.get("value")
        except Exception:
            return None

    @staticmethod
    def set_key(key: str, value: Any) -> bool:
        """Set key in memory service. Returns False on failure."""
        if not MEMORY_URL:
            return False
        try:
            r = requests.post(
                f"{MEMORY_URL}/set",
                json={"key": key, "value": value},
                timeout=REQUEST_TIMEOUT,
            )
            return r.status_code == 200
        except Exception:
            return False

    @staticmethod
    def get_many(keys: List[str]) -> dict:
        """Get multiple keys. Returns dict; missing/failed keys are absent."""
        if not MEMORY_URL or not keys:
            return {}
        try:
            r = requests.get(
                f"{MEMORY_URL}/get_many",
                params={"keys": ",".join(keys)},
                timeout=REQUEST_TIMEOUT,
            )
            if r.status_code != 200:
                return {}
            return r.json() if isinstance(r.json(), dict) else {}
        except Exception:
            return {}

    # --- Goals (Postgres ada_core.goals) ---
    @staticmethod
    def get_active_goals() -> List[dict]:
        """Return list of active goals. Never raises; returns [] on failure or empty table."""
        conn = _get_conn()
        if not conn:
            return []
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, goal, status, created_at FROM ada_core.goals WHERE status = 'active' ORDER BY id"
                )
                rows = cur.fetchall()
            return [
                {"id": r[0], "goal": r[1], "status": r[2], "created_at": str(r[3]) if r[3] else None}
                for r in rows
            ]
        except Exception:
            return []
        finally:
            try:
                conn.close()
            except Exception:
                pass

    @staticmethod
    def add_goal(goal: str, status: str = "active") -> Optional[int]:
        """Insert goal; return id or None on failure."""
        conn = _get_conn()
        if not conn:
            return None
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO ada_core.goals (goal, status) VALUES (%s, %s) RETURNING id",
                    (goal.strip(), status),
                )
                row = cur.fetchone()
                conn.commit()
                return row[0] if row else None
        except Exception:
            try:
                conn.rollback()
            except Exception:
                pass
            return None
        finally:
            try:
                conn.close()
            except Exception:
                pass

    # --- Memories (Postgres ada_core.memories) ---
    @staticmethod
    def add_memory(topic: str, content: str, importance: int = 0) -> bool:
        """Store a memory. Returns False on failure."""
        conn = _get_conn()
        if not conn:
            return False
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO ada_core.memories (topic, content, importance) VALUES (%s, %s, %s)",
                    (topic or "", content.strip(), importance),
                )
                conn.commit()
            return True
        except Exception:
            try:
                conn.rollback()
            except Exception:
                pass
            return False
        finally:
            try:
                conn.close()
            except Exception:
                pass

    @staticmethod
    def get_recent_memories(topic: Optional[str] = None, limit: int = 20) -> List[dict]:
        """Return recent memories, optionally by topic. Never raises."""
        conn = _get_conn()
        if not conn:
            return []
        try:
            with conn.cursor() as cur:
                if topic:
                    cur.execute(
                        "SELECT id, timestamp, topic, content, importance FROM ada_core.memories WHERE topic = %s ORDER BY timestamp DESC LIMIT %s",
                        (topic, limit),
                    )
                else:
                    cur.execute(
                        "SELECT id, timestamp, topic, content, importance FROM ada_core.memories ORDER BY timestamp DESC LIMIT %s",
                        (limit,),
                    )
                rows = cur.fetchall()
            return [
                {
                    "id": r[0],
                    "timestamp": str(r[1]) if r[1] else None,
                    "topic": r[2],
                    "content": r[3],
                    "importance": r[4],
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

    # --- Ideas (Postgres ada_core.ideas) ---
    @staticmethod
    def store_idea(goal_id: Optional[int], idea: str, score: float = 0) -> bool:
        """Store an idea, optionally linked to a goal. Returns False on failure."""
        conn = _get_conn()
        if not conn:
            return False
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO ada_core.ideas (goal_id, idea, score) VALUES (%s, %s, %s)",
                    (goal_id, idea.strip(), score),
                )
                conn.commit()
            return True
        except Exception:
            try:
                conn.rollback()
            except Exception:
                pass
            return False
        finally:
            try:
                conn.close()
            except Exception:
                pass

    @staticmethod
    def get_ideas_for_goal(goal_id: int, limit: int = 50) -> List[dict]:
        """Return ideas for a goal. Never raises."""
        conn = _get_conn()
        if not conn:
            return []
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, goal_id, idea, score, created_at FROM ada_core.ideas WHERE goal_id = %s ORDER BY created_at DESC LIMIT %s",
                    (goal_id, limit),
                )
                rows = cur.fetchall()
            return [
                {
                    "id": r[0],
                    "goal_id": r[1],
                    "idea": r[2],
                    "score": float(r[3]) if r[3] is not None else 0,
                    "created_at": str(r[4]) if r[4] else None,
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

    # --- Experiences (Postgres ada_core.experiences) ---
    @staticmethod
    def add_experience(
        event: str,
        result: Optional[str] = None,
        learning: Optional[str] = None,
        success_score: Optional[float] = None,
        evaluation: Optional[str] = None,
    ) -> bool:
        """Registra una experiencia (evento + resultado + aprendizaje + success_score, evaluation si existen)."""
        conn = _get_conn()
        if not conn:
            return False
        try:
            with conn.cursor() as cur:
                try:
                    cur.execute(
                        """INSERT INTO ada_core.experiences (event, result, learning, success_score, evaluation)
                           VALUES (%s, %s, %s, %s, %s)""",
                        (
                            event.strip(),
                            (result or "").strip() or None,
                            (learning or "").strip() or None,
                            success_score,
                            (evaluation or "").strip() or None,
                        ),
                    )
                except Exception:
                    cur.execute(
                        "INSERT INTO ada_core.experiences (event, result, learning) VALUES (%s, %s, %s)",
                        (event.strip(), (result or "").strip() or None, (learning or "").strip() or None),
                    )
                conn.commit()
            return True
        except Exception:
            try:
                conn.rollback()
            except Exception:
                pass
            return False
        finally:
            try:
                conn.close()
            except Exception:
                pass

    @staticmethod
    def get_recent_experiences(limit: int = 20) -> List[dict]:
        """Últimas experiencias. Incluye success_score y evaluation si existen."""
        conn = _get_conn()
        if not conn:
            return []
        try:
            with conn.cursor() as cur:
                try:
                    cur.execute(
                        """SELECT id, event, result, learning, success_score, evaluation, timestamp
                           FROM ada_core.experiences ORDER BY timestamp DESC LIMIT %s""",
                        (limit,),
                    )
                except Exception:
                    cur.execute(
                        "SELECT id, event, result, learning, NULL, NULL, timestamp FROM ada_core.experiences ORDER BY timestamp DESC LIMIT %s",
                        (limit,),
                    )
                rows = cur.fetchall()
            return [
                {
                    "id": r[0],
                    "event": r[1],
                    "result": r[2],
                    "learning": r[3],
                    "success_score": float(r[4]) if r[4] is not None else None,
                    "evaluation": r[5],
                    "timestamp": str(r[6]) if r[6] else None,
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

    @staticmethod
    def get_plans(limit: int = 20) -> List[dict]:
        """Experiencias que son planes de acción (event LIKE 'action_plan:%')."""
        conn = _get_conn()
        if not conn:
            return []
        try:
            with conn.cursor() as cur:
                try:
                    cur.execute(
                        """SELECT id, event, result, learning, success_score, evaluation, timestamp
                           FROM ada_core.experiences WHERE event LIKE 'action_plan%%' ORDER BY timestamp DESC LIMIT %s""",
                        (limit,),
                    )
                except Exception:
                    cur.execute(
                        "SELECT id, event, result, learning, NULL, NULL, timestamp FROM ada_core.experiences WHERE event LIKE 'action_plan%%' ORDER BY timestamp DESC LIMIT %s",
                        (limit,),
                    )
                rows = cur.fetchall()
            return [
                {
                    "id": r[0],
                    "event": r[1],
                    "result": r[2],
                    "learning": r[3],
                    "success_score": float(r[4]) if len(r) > 4 and r[4] is not None else None,
                    "evaluation": r[5] if len(r) > 5 else None,
                    "timestamp": str(r[6]) if len(r) > 6 and r[6] else None,
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

    @staticmethod
    def update_experience_learning(experience_id: int, learning: str, evaluation: Optional[str] = None, success_score: Optional[float] = None) -> bool:
        """Actualiza learning (y opcionalmente evaluation, success_score) de una experiencia."""
        conn = _get_conn()
        if not conn:
            return False
        try:
            with conn.cursor() as cur:
                try:
                    cur.execute(
                        "UPDATE ada_core.experiences SET learning = %s, evaluation = %s, success_score = %s WHERE id = %s",
                        (learning, evaluation, success_score, experience_id),
                    )
                except Exception:
                    cur.execute("UPDATE ada_core.experiences SET learning = %s WHERE id = %s", (learning, experience_id))
                conn.commit()
            return True
        except Exception:
            try:
                conn.rollback()
            except Exception:
                pass
            return False
        finally:
            try:
                conn.close()
            except Exception:
                pass

    # --- Derived goals (Postgres ada_core.derived_goals) ---
    @staticmethod
    def add_derived_goal(parent_goal_id: Optional[int], goal: str, status: str = "active") -> bool:
        """Crea un goal derivado a partir de un parent goal."""
        conn = _get_conn()
        if not conn:
            return False
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO ada_core.derived_goals (parent_goal_id, goal, status) VALUES (%s, %s, %s)",
                    (parent_goal_id, goal.strip(), status),
                )
                conn.commit()
            return True
        except Exception:
            try:
                conn.rollback()
            except Exception:
                pass
            return False
        finally:
            try:
                conn.close()
            except Exception:
                pass

    @staticmethod
    def get_derived_goals(parent_goal_id: Optional[int] = None, status: str = "active", limit: int = 50) -> List[dict]:
        """Lista goals derivados, opcionalmente por parent."""
        conn = _get_conn()
        if not conn:
            return []
        try:
            with conn.cursor() as cur:
                if parent_goal_id is not None:
                    cur.execute(
                        "SELECT id, parent_goal_id, goal, status, created_at FROM ada_core.derived_goals WHERE parent_goal_id = %s AND status = %s ORDER BY id DESC LIMIT %s",
                        (parent_goal_id, status, limit),
                    )
                else:
                    cur.execute(
                        "SELECT id, parent_goal_id, goal, status, created_at FROM ada_core.derived_goals WHERE status = %s ORDER BY id DESC LIMIT %s",
                        (status, limit),
                    )
                rows = cur.fetchall()
            return [
                {
                    "id": r[0],
                    "parent_goal_id": r[1],
                    "goal": r[2],
                    "status": r[3],
                    "created_at": str(r[4]) if r[4] else None,
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

    # --- Opportunities (Postgres ada_core.opportunities) ---
    @staticmethod
    def store_opportunity(
        idea: str,
        score: float = 0,
        impact: float = 0,
        ease: float = 0,
        speed: float = 0,
        risk: float = 0,
        goal_id: Optional[int] = None,
        status: str = "pending",
    ) -> bool:
        """Guarda una oportunidad evaluada."""
        conn = _get_conn()
        if not conn:
            return False
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO ada_core.opportunities (idea, score, impact, ease, speed, risk, goal_id, status)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                    (idea.strip(), score, impact, ease, speed, risk, goal_id, status),
                )
                conn.commit()
            return True
        except Exception:
            try:
                conn.rollback()
            except Exception:
                pass
            return False
        finally:
            try:
                conn.close()
            except Exception:
                pass

    @staticmethod
    def get_opportunities(goal_id: Optional[int] = None, status: str = "pending", limit: int = 50) -> List[dict]:
        """Lista oportunidades, opcionalmente por goal o status."""
        conn = _get_conn()
        if not conn:
            return []
        try:
            with conn.cursor() as cur:
                if goal_id is not None:
                    cur.execute(
                        """SELECT id, idea, score, impact, ease, speed, risk, status, goal_id, created_at
                           FROM ada_core.opportunities WHERE goal_id = %s AND status = %s ORDER BY score DESC LIMIT %s""",
                        (goal_id, status, limit),
                    )
                else:
                    cur.execute(
                        """SELECT id, idea, score, impact, ease, speed, risk, status, goal_id, created_at
                           FROM ada_core.opportunities WHERE status = %s ORDER BY score DESC LIMIT %s""",
                        (status, limit),
                    )
                rows = cur.fetchall()
            return [
                {
                    "id": r[0], "idea": r[1], "score": float(r[2]) if r[2] is not None else 0,
                    "impact": float(r[3]) if r[3] is not None else 0, "ease": float(r[4]) if r[4] is not None else 0,
                    "speed": float(r[5]) if r[5] is not None else 0, "risk": float(r[6]) if r[6] is not None else 0,
                    "status": r[7], "goal_id": r[8], "created_at": str(r[9]) if r[9] else None,
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

    # --- Action plans (Postgres ada_core.action_plans) — ADA v3 ---
    @staticmethod
    def store_action_plan(opportunity_id: Optional[int], plan: str, status: str = "pending") -> bool:
        """Guarda un plan de acción vinculado a una oportunidad."""
        conn = _get_conn()
        if not conn:
            return False
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO ada_core.action_plans (opportunity_id, plan, status) VALUES (%s, %s, %s)",
                    (opportunity_id, plan.strip(), status),
                )
                conn.commit()
            return True
        except Exception:
            try:
                conn.rollback()
            except Exception:
                pass
            return False
        finally:
            try:
                conn.close()
            except Exception:
                pass

    @staticmethod
    def get_action_plans(status: Optional[str] = None, limit: int = 50) -> List[dict]:
        """Lista planes de acción (tabla action_plans). Si status es None, devuelve todos."""
        conn = _get_conn()
        if not conn:
            return []
        try:
            with conn.cursor() as cur:
                if status:
                    cur.execute(
                        "SELECT id, opportunity_id, plan, status, created_at FROM ada_core.action_plans WHERE status = %s ORDER BY created_at DESC LIMIT %s",
                        (status, limit),
                    )
                else:
                    cur.execute(
                        "SELECT id, opportunity_id, plan, status, created_at FROM ada_core.action_plans ORDER BY created_at DESC LIMIT %s",
                        (limit,),
                    )
                rows = cur.fetchall()
            return [
                {
                    "id": r[0],
                    "opportunity_id": r[1],
                    "plan": r[2],
                    "status": r[3],
                    "created_at": str(r[4]) if r[4] else None,
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

    @staticmethod
    def get_learning(limit: int = 30) -> List[dict]:
        """Experiencias con learning o evaluation no vacíos (lecciones aprendidas)."""
        conn = _get_conn()
        if not conn:
            return []
        try:
            with conn.cursor() as cur:
                try:
                    cur.execute(
                        """SELECT id, event, result, learning, evaluation, success_score, timestamp
                           FROM ada_core.experiences
                           WHERE (learning IS NOT NULL AND TRIM(learning) != '') OR (evaluation IS NOT NULL AND TRIM(evaluation) != '')
                           ORDER BY timestamp DESC LIMIT %s""",
                        (limit,),
                    )
                except Exception:
                    cur.execute(
                        """SELECT id, event, result, learning, NULL, NULL, timestamp
                           FROM ada_core.experiences WHERE learning IS NOT NULL AND TRIM(learning) != '' ORDER BY timestamp DESC LIMIT %s""",
                        (limit,),
                    )
                rows = cur.fetchall()
            return [
                {
                    "id": r[0],
                    "event": r[1],
                    "result": (r[2] or "")[:500],
                    "learning": r[3],
                    "evaluation": r[4] if len(r) > 4 else None,
                    "success_score": float(r[5]) if len(r) > 5 and r[5] is not None else None,
                    "timestamp": str(r[6]) if len(r) > 6 and r[6] else None,
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

    # --- ADA v3: knowledge_base (web research results) ---
    @staticmethod
    def add_knowledge(topic: str, source_url: str = "", summary: str = "") -> bool:
        """Store a knowledge base entry (e.g. from web research). Returns False on failure."""
        conn = _get_conn()
        if not conn:
            return False
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO ada_core.knowledge_base (topic, source_url, summary)
                    VALUES (%s, %s, %s)
                    """,
                    ((topic or "")[:512], (source_url or "")[:2048], (summary or "")[:10000]),
                )
                conn.commit()
            return True
        except Exception:
            try:
                conn.rollback()
            except Exception:
                pass
            return False
        finally:
            try:
                conn.close()
            except Exception:
                pass

    @staticmethod
    def get_knowledge_by_topic(topic: Optional[str] = None, limit: int = 50) -> List[dict]:
        """Return knowledge base entries, optionally filtered by topic. Never raises."""
        conn = _get_conn()
        if not conn:
            return []
        try:
            with conn.cursor() as cur:
                if topic:
                    cur.execute(
                        """
                        SELECT id, topic, source_url, summary, created_at
                        FROM ada_core.knowledge_base WHERE topic ILIKE %s ORDER BY created_at DESC LIMIT %s
                        """,
                        (f"%{topic}%", limit),
                    )
                else:
                    cur.execute(
                        """
                        SELECT id, topic, source_url, summary, created_at
                        FROM ada_core.knowledge_base ORDER BY created_at DESC LIMIT %s
                        """,
                        (limit,),
                    )
                rows = cur.fetchall()
            return [
                {
                    "id": r[0],
                    "topic": r[1],
                    "source_url": r[2],
                    "summary": r[3],
                    "created_at": str(r[4]) if r[4] else None,
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

# A.D.A — Especificación Técnica: Agentes IA Especializados

## 📋 Tabla de Contenidos
1. [Arquitectura de Agentes](#arquitectura-de-agentes)
2. [Agente #1: ALMA (Marketing)](#agente-1-alma-marketing)
3. [Agente #2: CODE (Engineering)](#agente-2-code-engineering)
4. [Agente #3: CARE (Customer Support)](#agente-3-care-customer-support)
5. [Agente #4: DATA (Analytics & BI)](#agente-4-data-analytics--bi)
6. [Agente #5: ENGAGE (Sales)](#agente-5-engage-sales)
7. [Agente #6: QUALITY (QA & Compliance)](#agente-6-quality-qa--compliance)
8. [Agente #7: RESEARCH (Innovation & R&D)](#agente-7-research-innovation--rd)
9. [Sistema de Coordinación Inter-Agentes](#sistema-de-coordinación-inter-agentes)
10. [Testing y Deployment](#testing-y-deployment)

---

## 🏗️ Arquitectura de Agentes

### Principios Fundamentales

Cada agente es un **contenedor Docker independiente** que:

1. **Especialización:** Entrenado en dominio específico (marketing, código, soporte, etc.)
2. **Memoria compartida:** Acceso a PostgreSQL centralizado (ada_memory, ada_finance, ada_logs)
3. **Autonomía progresiva:** Comienza con baja autonomía (propone, humano aprueba); evoluciona a autonomía completa
4. **LLM base:** Ollama local (modelos especializados) + fallback a Gemini API
5. **Orquestación:** A.D.A (decision-engine) asigna tareas a agentes específicos

### Estructura Docker de un Agente

```dockerfile
# agents/alma/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Dependencias comunes
COPY requirements.txt .
RUN pip install -r requirements.txt

# Código del agente
COPY src/ ./src/

# Config específica del agente
ENV AGENT_NAME=ALMA
ENV AGENT_SPECIALTY=marketing
ENV AGENT_MODEL=mistral-7b  # o neural-chat, etc.

# API de agente (puerto único por agente)
EXPOSE 3011  # ALMA: 3011
# CODE: 3012
# CARE: 3013
# etc.

CMD ["python", "src/agent_api.py"]
```

### Docker Compose Actualizado

```yaml
# docker-compose.yml (fragmento - agents)

services:
  # ... servicios existentes (agent-core, decision-engine, etc.) ...

  # ============= AGENTES ESPECIALIZADOS =============

  alma:  # Marketing + Content
    build: ./agents/alma
    container_name: ada_alma
    profiles:
      - extended
    environment:
      PG_HOST: postgres
      PG_PORT: 5432
      PG_USER: ${PG_USER:-ada_user}
      PG_PASSWORD: ${PG_PASSWORD:-supersecret}
      PG_DB: ${PG_DB:-ada_main}
      OLLAMA_URL: ${OLLAMA_URL:-http://host.docker.internal:11434/api/generate}
      OLLAMA_MODEL: mistral-7b
      AGENT_NAME: ALMA
      AGENT_SPECIALTY: marketing
    depends_on:
      postgres:
        condition: service_healthy
    ports:
      - "3011:3011"

  code:  # Engineering
    build: ./agents/code
    container_name: ada_code
    profiles:
      - extended
    environment:
      PG_HOST: postgres
      PG_PORT: 5432
      PG_USER: ${PG_USER:-ada_user}
      PG_PASSWORD: ${PG_PASSWORD:-supersecret}
      PG_DB: ${PG_DB:-ada_main}
      OLLAMA_URL: ${OLLAMA_URL:-http://host.docker.internal:11434/api/generate}
      OLLAMA_MODEL: mistral-7b
      AGENT_NAME: CODE
      AGENT_SPECIALTY: engineering
    depends_on:
      postgres:
        condition: service_healthy
    ports:
      - "3012:3012"

  care:  # Customer Support
    build: ./agents/care
    container_name: ada_care
    profiles:
      - extended
    environment:
      PG_HOST: postgres
      PG_PORT: 5432
      OLLAMA_URL: ${OLLAMA_URL:-http://host.docker.internal:11434/api/generate}
      OLLAMA_MODEL: neural-chat  # mejor para conversación
      AGENT_NAME: CARE
      AGENT_SPECIALTY: support
    depends_on:
      postgres:
        condition: service_healthy
    ports:
      - "3013:3013"

  data:  # Analytics & BI
    build: ./agents/data
    container_name: ada_data
    profiles:
      - extended
    environment:
      PG_HOST: postgres
      PG_PORT: 5432
      OLLAMA_URL: ${OLLAMA_URL:-http://host.docker.internal:11434/api/generate}
      OLLAMA_MODEL: mistral-7b
      AGENT_NAME: DATA
      AGENT_SPECIALTY: analytics
    depends_on:
      postgres:
        condition: service_healthy
    ports:
      - "3014:3014"

  # ... más agentes según timeline ...

volumes:
  pg-data:
  ollama-data:
```

---

## 🎨 Agente #1: ALMA (Marketing)

### Perfil
- **Especialidad:** Marketing, content creation, social media, copywriting
- **Objetivo:** 20-30% aumento en leads y conversiones
- **LLM Base:** Mistral-7B (bueno para creative writing)
- **Modelos Alternativos:** Neural-chat, Nous-Hermes (conversacional)

### Responsabilidades

1. **Content Generation**
   - Twitter/X posts (3-5/día, optimizados para engagement)
   - LinkedIn posts (1-2/semana, B2B focus)
   - Blog drafts (2-3/mes, Medium/Substack)
   - Newsletter contenido (semanal, Substack)
   - Descripciones de productos (Gumroad, SaaS)

2. **Copywriting**
   - Landing pages
   - Email campaigns
   - Ad copy (Upwork, Fiverr)
   - Call-to-action optimization

3. **Analytics & Optimization**
   - Analizar engagement (tweets, posts, newsletters)
   - A/B testing de mensajes
   - Identidad de marca consistency
   - Hashtag research y trending topics

4. **Community Management**
   - Moderar Discord
   - Responder comentarios Twitter/LinkedIn
   - Identificar y cultivar leads
   - Gestionar relaciones con influencers

### API Endpoints

```python
# agents/alma/src/agent_api.py

POST /api/alma/generate-tweets
  Input:  { topic: str, count: int, tone: str }
  Output: { tweets: [{ text, hashtags, scheduled_time }], metrics: {...} }

POST /api/alma/generate-post
  Input:  { platform: str, topic: str, style: str }
  Output: { post: str, hashtags: [], call_to_action: str }

POST /api/alma/content-plan
  Input:  { week_number: int, focus: str }
  Output: { plan: [{ day, content_type, topic, priority }], estimated_engagement: float }

POST /api/alma/optimize-message
  Input:  { original_message: str, platform: str }
  Output: { optimized: str, improvements: [], estimated_ctr: float }

GET /api/alma/analytics
  Input:  { period: str, metrics: [str] }
  Output: { engagement_data, top_posts, trending_topics }

POST /api/alma/email-campaign
  Input:  { segment: str, offer: str, copy_style: str }
  Output: { subject_lines: [], email_body: str, cta: str, estimated_open_rate: float }
```

### Integración con PostgreSQL

```sql
-- Schema extensions para ALMA
CREATE TABLE IF NOT EXISTS ada_alma.content_calendar (
    id SERIAL PRIMARY KEY,
    platform VARCHAR(50),
    content_type VARCHAR(50),
    topic TEXT,
    scheduled_date TIMESTAMP,
    status VARCHAR(20),  -- draft, scheduled, published
    engagement_metrics JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ada_alma.tweet_variants (
    id SERIAL PRIMARY KEY,
    base_topic TEXT,
    variants JSONB,  -- array de opciones
    best_performer VARCHAR(500),
    engagement_score FLOAT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ada_alma.email_campaigns (
    id SERIAL PRIMARY KEY,
    campaign_name VARCHAR(255),
    segment VARCHAR(100),
    subject_line TEXT,
    email_body TEXT,
    cta TEXT,
    sent_at TIMESTAMP,
    open_rate FLOAT,
    click_rate FLOAT
);
```

### Prompts Especializados

```
# System Prompt para ALMA
You are ALMA, A.D.A's Marketing and Content Specialist.
Your role is to:
1. Generate compelling, engaging content for Twitter, LinkedIn, blogs
2. Create copy that converts: landing pages, emails, product descriptions
3. Analyze content performance and optimize messaging
4. Maintain brand voice and identity consistency
5. Identify emerging trends and leverage them for reach

Tone: Professional, approachable, thought-leader in AI/DevOps/IA
Audience: Developers, startup founders, tech enthusiasts, enterprises
Language: Spanish and English (detect from context)

When generating content:
- Use storytelling and personal touches
- Include hooks, questions, and calls-to-action
- Optimize for platform-specific features (hashtags, threading, etc.)
- Avoid hype; focus on real value
- Reference A.D.A's unique positioning: "IA local, arquitectura propia"

Remember: Content is king, but conversion is queen. Always tie back to business goals.
```

### Launch Timeline (Mes 2)

```
Week 1:  Build ALMA Dockerfile + API endpoints
Week 2:  Train on marketing datasets, create prompt templates
Week 3:  Integration testing con decision-engine
Week 4:  Soft launch (ALMA propone, humano aprueba)
         → Monitor engagement lift
Week 5+: Increase autonomy (low-risk posts auto-published)
```

---

## 💻 Agente #2: CODE (Engineering)

### Perfil
- **Especialidad:** Programación, arquitectura, DevOps, code review
- **Objetivo:** 20-30% aumento en velocidad de propuestas técnicas
- **LLM Base:** Mistral-7B o phi-2 (bueno para código)
- **Modelos Alternativos:** Code-Llama, StarCoder

### Responsabilidades

1. **Generación de Código**
   - Propuestas técnicas detalladas (archivos + pseudocódigo)
   - Scripts de automatización (Bash, Python, Go)
   - API designs y documentación
   - Optimización de código existente

2. **Arquitectura y Diseño**
   - Diagrama de sistemas (propuestas de clientes)
   - Análisis de bottlenecks
   - Propuestas de mejora en escalabilidad
   - Technology stack recommendations

3. **DevOps y Infra**
   - Dockerfiles optimizados
   - Docker Compose configurations
   - CI/CD pipeline designs
   - Kubernetes manifests (futuro)

4. **Code Review y QA**
   - Revisar código de clientes
   - Proponer mejoras
   - Detectar vulnerabilidades (básico)
   - Sugerir optimizaciones

### API Endpoints

```python
POST /api/code/generate-proposal
  Input:  { client_problem: str, tech_stack: str, requirements: [str] }
  Output: { proposal: str, architecture: str, code_samples: [str], timeline: str, estimated_cost: float }

POST /api/code/code-review
  Input:  { code: str, language: str, focus: [str] }  # focus: ["performance", "security", "readability"]
  Output: { issues: [{ line, severity, suggestion }], overall_score: float, refactored_version: str }

POST /api/code/optimize
  Input:  { code: str, language: str, goal: str }  # goal: "performance" | "readability" | "maintainability"
  Output: { optimized_code: str, explanation: str, metrics: { before, after } }

POST /api/code/api-design
  Input:  { resource_name: str, operations: [str], requirements: [str] }
  Output: { openapi_spec: str, endpoints: [{}], example_requests: [str] }

GET /api/code/docker-config
  Input:  { app_type: str, dependencies: [str], requirements: [str] }
  Output: { dockerfile: str, docker_compose: str, env_example: str }

POST /api/code/security-audit
  Input:  { code: str, infrastructure: str, threat_level: str }
  Output: { vulnerabilities: [], recommendations: [], risk_score: float }
```

### Integración con PostgreSQL

```sql
CREATE TABLE IF NOT EXISTS ada_code.project_proposals (
    id SERIAL PRIMARY KEY,
    client_id INT,
    problem_description TEXT,
    architecture TEXT,
    code_snippets JSONB,
    estimated_effort FLOAT,  -- horas
    estimated_cost FLOAT,
    technology_stack VARCHAR(500),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ada_code.code_reviews (
    id SERIAL PRIMARY KEY,
    client_id INT,
    code_reviewed TEXT,
    issues JSONB,
    severity_distribution JSONB,  -- { "critical": 2, "high": 5, "medium": 10 }
    overall_score FLOAT,
    reviewed_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ada_code.tech_recommendations (
    id SERIAL PRIMARY KEY,
    use_case VARCHAR(255),
    recommended_stack JSONB,  -- { "backend": "Go", "db": "PostgreSQL", ... }
    reasoning TEXT,
    pros_cons JSONB,
    created_at TIMESTAMP
);
```

### Prompts Especializados

```
You are CODE, A.D.A's Engineering and Architecture Specialist.
Your role is to:
1. Generate detailed technical proposals for clients
2. Review and optimize code across multiple languages
3. Design scalable, maintainable architectures
4. Provide security and performance recommendations
5. Document technical decisions clearly

Languages: Python, JavaScript, Go, Bash, SQL (primary)
Frameworks: Django, FastAPI, Node.js, Docker, Kubernetes (intermediate)

When generating proposals:
- Include architecture diagram (ASCII art)
- Provide code samples (Python/Go preferred)
- Estimate effort in hours (realistic)
- List assumptions and constraints
- Suggest alternatives and trade-offs

Code quality standards:
- Performance: optimize for O(log n) or O(n) where possible
- Security: follow OWASP Top 10
- Readability: clean code principles (Martin)
- Maintainability: DRY, SOLID principles

Always explain WHY, not just WHAT.
```

### Launch Timeline (Mes 3)

```
Week 1-2: Build Dockerfile + API endpoints, integrate code generation models
Week 3:   Create code review templates and rubrics
Week 4:   Integration con decision-engine, testing con propuestas reales
Week 5:   Soft launch (propuestas simple, review by human)
Week 6+:  Autonomy increase (simple propuestas auto-generated)
```

---

## 📞 Agente #3: CARE (Customer Support)

### Perfil
- **Especialidad:** Atención al cliente, soporte técnico, gestión de tickets
- **Objetivo:** Soporte 24/7 asincrónico, reducir tiempo de respuesta a < 2h
- **LLM Base:** Neural-Chat o Nous-Hermes (bueno para conversación)

### Responsabilidades

1. **Soporte Técnico Asincrónico**
   - Responder tickets de soporte
   - Troubleshooting paso a paso
   - Documentación auto-generada (FAQs)
   - Escalado a humano cuando necesario

2. **Gestión de Clientes**
   - Registro de issues y resoluciones
   - Seguimiento de satisfacción (NPS)
   - Sugerencias de mejora basadas en feedback
   - Recomendaciones de up-sell

3. **Documentación**
   - Auto-generar FAQs de issues comunes
   - Crear guías de troubleshooting
   - Actualizar documentación basada en preguntas
   - Crear videos tutoriales (transcripts)

### API Endpoints

```python
POST /api/care/answer-ticket
  Input:  { ticket_id: int, question: str, context: str }
  Output: { answer: str, confidence: float, escalate_to_human: bool, related_docs: [str] }

POST /api/care/generate-faq
  Input:  { topic: str, issue_examples: [str] }
  Output: { faqs: [{ q, a, helpful_count }], doc_version: str }

POST /api/care/nps-survey
  Input:  { client_id: int, recent_interactions: [str] }
  Output: { survey_message: str, follow_up_actions: [str] }

GET /api/care/ticket-status
  Input:  { ticket_id: int }
  Output: { status: str, resolution: str, satisfaction: float }

POST /api/care/escalate
  Input:  { ticket_id: int, reason: str, suggested_resolution: str }
  Output: { escalation_id: str, human_reviewer: str, priority: str }
```

### Integración con PostgreSQL

```sql
CREATE TABLE IF NOT EXISTS ada_care.support_tickets (
    id SERIAL PRIMARY KEY,
    client_id INT,
    question TEXT,
    answer TEXT,
    severity VARCHAR(20),
    status VARCHAR(20),  -- open, in_progress, resolved, escalated
    resolution_time INT,  -- minutos
    satisfaction_rating FLOAT,
    created_at TIMESTAMP,
    resolved_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ada_care.faq_base (
    id SERIAL PRIMARY KEY,
    topic VARCHAR(255),
    question TEXT,
    answer TEXT,
    helpful_count INT DEFAULT 0,
    unhelpful_count INT DEFAULT 0,
    last_updated TIMESTAMP
);
```

---

## 📊 Agente #4: DATA (Analytics & BI)

### Perfil
- **Especialidad:** Análisis de datos, business intelligence, forecasting
- **Objetivo:** Optimizar pricing, identificar oportunidades de ingresos
- **LLM Base:** Mistral-7B con capacidades SQL avanzadas

### Responsabilidades

1. **Análisis de Negocio**
   - Revenue tracking y forecasting
   - Customer lifetime value (CLV) analysis
   - Churn prediction
   - Market segment analysis

2. **Reporting y Dashboards**
   - Reporte mensual de KPIs
   - Custom dashboards por cliente (SaaS)
   - Anomaly detection

3. **Optimización**
   - Pricing recommendations
   - Feature adoption analysis
   - Upsell/cross-sell opportunities
   - Cost optimization

### API Endpoints

```python
POST /api/data/revenue-forecast
  Input:  { period: str, include_factors: [str] }
  Output: { forecast: [{ month, revenue, confidence }], trend: str }

POST /api/data/customer-analysis
  Input:  { segment: str, metrics: [str] }
  Output: { clv: float, churn_risk: float, recommendations: [str] }

POST /api/data/pricing-recommendation
  Input:  { product: str, market_data: {} }
  Output: { recommended_price: float, rationale: str, price_elasticity: float }

GET /api/data/monthly-report
  Input:  { month: str }
  Output: { kpis: {}, trends: {}, recommendations: [str], risk_alerts: [str] }
```

---

## 🎯 Agente #5: ENGAGE (Sales)

### Perfil
- **Especialidad:** Ventas, prospección, negociación, CRM
- **Objetivo:** 30-40% aumento en nuevos leads y cierre de ventas
- **LLM Base:** Mistral-7B con context memory

### Responsabilidades

1. **Prospección Automatizada**
   - Identificar potenciales clientes
   - Generar mensajes personalizados (LinkedIn, email)
   - Seguimiento automático de leads

2. **Negociación**
   - Propuestas de precio personalizadas
   - Términos de contrato (templates)
   - Gestión de objeciones

3. **CRM Management**
   - Actualizar estado de oportunidades
   - Pipeline management
   - Sales forecasting

---

## ✅ Agente #6: QUALITY (QA & Compliance)

### Perfil
- **Especialidad:** Testing, compliance, auditoría, mejora continua
- **Objetivo:** Reducir errores, aumentar confianza en propuestas

### Responsabilidades

1. **Testing Automático**
   - Validar flujos y propuestas
   - Testing de APIs
   - Regression testing

2. **Compliance**
   - Validar cumplimiento de políticas
   - Auditoría de decisiones
   - Documentación de cambios

---

## 🔬 Agente #7: RESEARCH (Innovation & R&D)

### Perfil
- **Especialidad:** Tendencias, innovación, nuevas oportunidades
- **Objetivo:** Identificar 2-3 nuevas líneas de negocio/mes

### Responsabilidades

1. **Market Research**
   - Tendencias IA/tech
   - Nuevas plataformas y integraciones
   - Análisis competitivo

2. **Innovación**
   - Nuevos productos
   - Nuevos servicios
   - Expansión geográfica

---

## 🔄 Sistema de Coordinación Inter-Agentes

### Arquitectura de Decision-Engine Mejorada

```python
# agents/orchestrator/decision_engine_v2.py

class AgentOrchestrator:
    """
    Coordina todos los agentes IA bajo supervisión de A.D.A (CEO)
    """
    
    def __init__(self):
        self.agents = {
            'ada': Agent('agent-core', specialty='general'),
            'alma': Agent('alma', specialty='marketing'),
            'code': Agent('code', specialty='engineering'),
            'care': Agent('care', specialty='support'),
            'data': Agent('data', specialty='analytics'),
            'engage': Agent('engage', specialty='sales'),
            'quality': Agent('quality', specialty='qa'),
            'research': Agent('research', specialty='innovation')
        }
        self.memory_db = PostgreSQL('ada_main')
    
    async def propose_action(self, task: Task) -> List[Proposal]:
        """
        Recibe una tarea y pide propuestas a agentes relevantes
        """
        relevant_agents = self.find_relevant_agents(task.domain)
        proposals = []
        
        for agent in relevant_agents:
            proposal = await agent.propose(task)
            proposals.append(proposal)
        
        # A.D.A (CEO) elige la mejor propuesta
        best_proposal = await self.ada.choose_best(proposals, task)
        
        return best_proposal
    
    async def execute_with_coordination(self, proposal: Proposal):
        """
        Ejecuta propuesta con coordinación entre agentes si necesario
        """
        # Si la propuesta requiere múltiples agentes, coordinar
        required_agents = self.parse_dependencies(proposal)
        
        if len(required_agents) > 1:
            # Parallel execution con dependen cias
            await self.coordinate_agents(proposal, required_agents)
        else:
            # Single agent execution
            await required_agents[0].execute(proposal)
    
    def find_relevant_agents(self, domain: str) -> List[Agent]:
        """
        Retorna agentes especializados en el dominio
        """
        domain_map = {
            'marketing': ['alma', 'engage', 'research'],
            'engineering': ['code', 'quality'],
            'support': ['care'],
            'analytics': ['data'],
            'sales': ['engage', 'data'],
            'innovation': ['research', 'code']
        }
        
        return [self.agents[a] for a in domain_map.get(domain, [])]

class Agent:
    """
    Agente IA especializado
    """
    
    def __init__(self, name: str, specialty: str):
        self.name = name
        self.specialty = specialty
        self.api_url = f"http://{name}:3010+port/api"
        self.autonomy_level = 1  # 1=low (propone), 2=medium, 3=high (ejecuta)
        self.memory = PostgreSQL('ada_main')
    
    async def propose(self, task: Task) -> Proposal:
        """
        Propone solución basada en especialidad
        """
        response = await self.call_api('POST', '/propose', task.to_dict())
        return Proposal.from_response(response, self.name)
    
    async def execute(self, proposal: Proposal):
        """
        Ejecuta propuesta aprobada
        """
        # Logging obligatorio antes de ejecutar
        await self.memory.log_action(
            agent=self.name,
            action=proposal.action,
            status='executing'
        )
        
        # Ejecutar según nivel de autonomía
        if self.autonomy_level == 1:
            # Requiere aprobación humana
            await self.request_approval(proposal)
        elif self.autonomy_level == 2:
            # Ejecuta pero notifica después
            result = await self.call_api('POST', '/execute', proposal.to_dict())
            await self.memory.log_action(
                agent=self.name,
                action=proposal.action,
                status='completed',
                result=result
            )
        elif self.autonomy_level == 3:
            # Ejecuta sin notificación
            await self.call_api('POST', '/execute', proposal.to_dict())
```

### Ejemplo: Flujo Coordinado

```
Usuario → web-admin: "Quiero aumentar ventas"
                      ↓
           decision-engine.propose_action()
                      ↓
        ┌─────────────┼─────────────┐
        ▼             ▼             ▼
      ALMA          ENGAGE        DATA
    (propone        (propone      (propone
     campaign)      sales)        pricing)
        │             │             │
        └─────────────┼─────────────┘
                      ▼
          A.D.A (elige mejor)
                      ↓
        Propuesta + plan de ejecución
                      ↓
        ¿Necesita coordinación?
           SÍ → ALMA (content) + ENGAGE (outreach) en paralelo
           NO → ALMA solo o ENGAGE solo
```

---

## 🧪 Testing y Deployment

### Testing Strategy

```bash
# Sandboxmode (cada agente puede correr en sandbox)
docker compose -f docker-compose.yml \
  -f docker-compose.sandbox.yml \
  --profile extended \
  up -d

# Tests unitarios
pytest agents/alma/tests/
pytest agents/code/tests/
pytest agents/*/tests/

# Integration tests
pytest tests/integration/test_agent_coordination.py

# Performance tests
pytest tests/performance/test_api_latency.py
```

### Deployment Checklist (Por cada agente)

```
□ Código escrito y testeado
□ Docker image construida y testeada
□ Documentación de API completa
□ PostgreSQL migrations ejecutadas
□ Integration testing con decision-engine
□ Soft launch (low autonomy) en producción
□ Monitoreo y alerts configurados
□ Autonomy level gradualmente incrementado
□ Manual review de primeras 10 acciones
□ Performance monitoring (latency, error rate)
```

### Monitoring y Alerts

```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'alma'
    static_configs:
      - targets: ['localhost:3011']
  
  - job_name: 'code'
    static_configs:
      - targets: ['localhost:3012']
  
  - job_name: 'care'
    static_configs:
      - targets: ['localhost:3013']
  
  # ... más agentes ...

# Alertas
- alert: HighErrorRate
  expr: rate(agent_errors_total[5m]) > 0.05
  for: 5m
  annotations:
    summary: "Agente {{ $labels.agent }} tiene tasa de error alta"
```

---

## 📚 Documentación por Agente

Cada agente debe tener:

1. **README.md:** Descripción, especialidad, responsabilidades
2. **API.md:** Endpoints, inputs, outputs
3. **PROMPTS.md:** System prompts y ejemplos
4. **DATABASE.md:** Schema SQL específico del agente
5. **DEPLOYMENT.md:** Guía de lanzamiento
6. **TESTING.md:** Estrategia de testing

---

**Documento versión:** Técnica 1.0  
**Status:** Listo para implementar Mes 2  
**Responsable:** A.D.A (con supervisión humana)


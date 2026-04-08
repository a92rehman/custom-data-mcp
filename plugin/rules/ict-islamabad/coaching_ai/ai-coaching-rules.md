# AI Coaching Query Rules — ICT/Islamabad

## When These Rules Apply

User asks about:
- Digital Coach (AI) observations in ICT
- AI vs human observation bifurcation
- Automated observation questions or scores
- Digital coach request tracking or pipeline status

## How AI Coaching Works in ICT

ICT AI coaching uses the **same observation stack** as human coaching. The bifurcation is at the question level:
- `coaching_observationquestion.source = 'automated'` → AI/Digital Coach questions (107 questions)
- `coaching_observationquestion.source = 'manual'` → Human coach/principal questions (125,676 questions)

This means AI coaching observations are scored using the **same FICO framework** (Sections B/C/D) as human observations. The observation record itself (`coaching_observation`) is shared — the `source` column on questions determines which questions were AI-generated vs human-entered.

## Mandatory Clarifications

### Query Type
Ask: "AI observation count, AI observation scores, or pipeline status (request tracker)?"

### Section
Ask if scores: "Which observation section? B (LP Fidelity), C (Student Learning), D (Student Engagement), or all?"

### Time Period
Ask: "Which time period?"

## Key Tables

### Canonical: Observation Stack (PRODUCTION REPORTING)

| Table | Role | Rows |
|-------|------|------|
| `tbproddb.coaching_observationquestion` | Question metadata — `source` column distinguishes AI vs human | 125,783 |
| `tbproddb.coaching_observation` | Core observation record (shared with human) | (see observation-query-rules.md) |
| `tbproddb.coaching_observationanswer` | Answers to questions (shared with human) | (see observation-query-rules.md) |
| `tbproddb.coaching_questionoption` | Answer options with score_type | (see observation-query-rules.md) |

### Verification Only: Request Tracker (NOT CANONICAL)

| Table | Role | Rows |
|-------|------|------|
| `tbproddb.digital_coach_requesttracker` | Temporary tracker for AI processing pipeline | 44 |

**`digital_coach_requesttracker` is NOT canonical for production reporting.** It is a temporary tracker with mixed statuses. Use for pipeline diagnostics only.

### Verification Only: WhatsApp Messages (NOT CANONICAL)

| Table | Role | Rows |
|-------|------|------|
| `tbproddb.ai_chatbot_whatsappmessage` | WhatsApp onboarding/chat messages | 751,915 |

**`ai_chatbot_whatsappmessage` is NOT canonical.** Discussed as likely unrelated onboarding/chat artifact. Excluded from canonical reporting per CEO reconciliation.

## Critical Variable: source Column

```sql
-- AI observations: filter questions by source
SELECT oq.*
FROM tbproddb.coaching_observationquestion oq
WHERE oq.source = 'automated'
  AND oq.is_active = 'true'

-- Human observations: filter questions by source
SELECT oq.*
FROM tbproddb.coaching_observationquestion oq
WHERE oq.source = 'manual'
  AND oq.is_active = 'true'
```

### Source Distribution
- `manual`: 125,676 questions (human coach/principal)
- `automated`: 107 questions (AI/Digital Coach)

## AI Observation Scoring

AI observations use the **same scoring framework** as human observations (see `observation-query-rules.md`):
- Same score mapping: yes=1.0, partial=0.5, no=0.0, ignore=0.0
- Same sections: B (LP Fidelity), C (Student Learning), D (Student Engagement)
- Same aggregation rules: AVG per section per observation

To get AI-only scores, add `oq.source = 'automated'` to the standard observation query.

## digital_coach_requesttracker (Verification/Diagnostics Only)

### Key Columns
- `task_id` — primary key (STRING)
- `observation_id` — FK to coaching_observation (STRING)
- `status` — pipeline status: `sending` (17), `completed` (16), `failed` (11)
- `message`, `error` — status/error messages
- `progress` — completion progress (FLOAT)
- `current_step` — pipeline step name
- `subject` — subject being coached
- `created`, `updated` — timestamps

### Status Values
| Status | Count | Meaning |
|--------|-------|---------|
| `sending` | 17 | Request in progress |
| `completed` | 16 | Successfully processed |
| `failed` | 11 | Processing failed |

**Use for:** Pipeline health monitoring, error diagnostics, tracking AI coaching rollout.
**NOT for:** Production KPI reporting of session counts or scores.

## Key Difference from RWP

- ICT AI coaching = **same observation stack** with `source='automated'`, scored via FICO B/C/D
- RWP AI coaching = **separate audio-based system** (Rumi coaching_sessions) with transcription + analysis
- Cross-region AI coaching comparison: **session count and completion rate only**

## Aggregation Patterns

| User asks about | How to query |
|-----------------|-------------|
| Total AI observations | `COUNT(DISTINCT co.id)` where observation has at least one `source='automated'` question |
| AI observation scores | Standard FICO query + `WHERE oq.source = 'automated'` |
| AI vs human comparison | Run same query twice, once with `source='automated'`, once with `source='manual'` |
| Pipeline health | `SELECT status, COUNT(*) FROM digital_coach_requesttracker GROUP BY status` |

## Important Notes

- AI and human questions can coexist within the same observation — the `source` column is per-question, not per-observation
- When counting "AI observations", count observations that contain at least one `source='automated'` question
- All standard observation filters still apply (`is_active`, purpose, section IDs) — see `observation-query-rules.md`
- `digital_coach_requesttracker` has only 44 rows — it tracks processing requests, not all AI observations

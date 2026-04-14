# Coaching & Observation Product Analytics — ICT/Islamabad

> Source: `tbproddb.analytics_events` (partitioned on `sent_at`). Always filter `sent_at >= TIMESTAMP('...')`.
> For governed KPI rules (FICO scores, section B/C/D): see `observation-query-rules.md`.
> For AI coaching rules: see `../coaching_ai/ai-coaching-rules.md`.

## When These Rules Apply

User asks about coaching **engagement**, **usage**, **funnels**, observation scheduling, feedback generation, or digital coach activity.

**Always ask:** "What specific time period?" — never assume a duration.

---

## Two Product Features

| Feature | Events | Users | Purpose |
|---------|--------|-------|---------|
| **Human Coaching / Observation** | 18 events | ~240 coaches | Schedule, conduct, and submit observations with feedback |
| **Digital Coach (AI)** | 6 events | ~328 teachers | AI-based classroom recording and feedback |

---

## 1. Human Coaching — Event Catalog

### Scheduling & Planning

| Event | Vol | Users | Key Props | Purpose |
|-------|-----|-------|-----------|---------|
| `visitSchedulerCreateSchedule` | 155 | 78 | — | Creates visit schedule |
| `visitSchedulerSaveSchedule` | 47 | 12 | — | Saves schedule |
| `visitSchedulerScheduleDatesSelected` | 80 | 14 | — | Selects schedule dates |
| `visitSchedulerScheduleDatesEdited` | 40 | 7 | — | Edits schedule dates |
| `visitSchedulerUpdateCoach` | 546 | 10 | — | Updates coach assignment |
| `planObservation` | 6.4K | 236 | `ep_date`, `ep_grade`, `ep_section`, `ep_subject` | Plans an observation |
| `coachScheduleSchoolSelected` | 1.6K | 58 | — | Selects school for scheduling |
| `coachScheduleTeacherPlan` | 854 | 55 | — | Plans teacher observation |
| `coachScheduleVisitReschedule` | 94 | 33 | — | Reschedules a visit |
| `coachScheduleVisitDelete` | 2 | 2 | — | Deletes a visit |

### Observation Execution

| Event | Vol | Users | Purpose |
|-------|-----|-------|---------|
| `coachScheduleObservationOpen` | 14.8K | 214 | Opens observation form |
| `coachScheduleBeginObservation` | 14.7K | 240 | Begins observation |
| `startObservation` | 1.7K | 177 | Starts observation (alternate entry) |
| `coachScheduleObservationSubmitted` | 6.7K | 224 | Submits completed observation |

### Feedback

| Event | Vol | Users | Purpose |
|-------|-----|-------|---------|
| `observationFeedbackAIGenerate` | 6.0K | 221 | Generates AI feedback |
| `observationFeedbackSave` | 5.4K | 220 | Saves feedback |
| `observationFeedbackEdit` | 2.4K | 98 | Edits saved feedback |
| `observationFeedbackManualWrite` | 642 | 84 | Writes manual feedback (vs AI-generated) |

---

## 2. Digital Coach (AI) — Event Catalog

| Event | Vol | Users | Purpose |
|-------|-----|-------|---------|
| `digitalCoachOnboarding` | 62 | 7 | Opens onboarding flow |
| `digitalCoachOnboardingVideo` | 29 | 4 | Watches onboarding video |
| `digitalCoachOnboardingClose` | 33 | 7 | Closes onboarding |
| `digitalCoachRecordingStarted` | 58 | 6 | Starts classroom recording |
| `digitalCoachRecordingSubmitted` | 21 | 6 | Submits recording |
| `digitalCoachFeedbackSeen` | 711 | 328 | Teacher views AI feedback |

> **Note:** Digital coach recording events have very low counts (~6 users). The `digitalCoachFeedbackSeen` event has 328 users — this is teachers viewing feedback from observations scored by the `source='automated'` pipeline (governed in `ai-coaching-rules.md`).

---

## Metric Definitions

### Human Coaching — Adoption

| Metric | Definition |
|--------|-----------|
| Active Coaches | `COUNT(DISTINCT user_id)` where `name LIKE 'coachSchedule%'` in period |
| Observations Opened | `COUNT(*)` of `coachScheduleObservationOpen` |
| Observations Submitted | `COUNT(*)` of `coachScheduleObservationSubmitted` |
| Submission Rate | `Submitted` / `Opened` (6.7K / 14.8K ≈ 45%) |
| AI Feedback Adoption | `observationFeedbackAIGenerate` / `observationFeedbackSave` |
| Manual vs AI Feedback | `ManualWrite` / (`ManualWrite` + `AIGenerate`) |

### Human Coaching — Observation Funnel

| Step | Event | Conversion |
|------|-------|------------|
| 1 | `planObservation` | top of funnel |
| 2 | `coachScheduleObservationOpen` | ÷ planObservation |
| 3 | `coachScheduleBeginObservation` | ÷ Open |
| 4 | `coachScheduleObservationSubmitted` | ÷ Begin (45% submit rate) |
| 5 | `observationFeedbackSave` | ÷ Submitted |

### Digital Coach — Funnel

| Step | Event | Conversion |
|------|-------|------------|
| 1 | `digitalCoachOnboarding` | Entry |
| 2 | `digitalCoachRecordingStarted` | ÷ Onboarding |
| 3 | `digitalCoachRecordingSubmitted` | ÷ Started (21/58 ≈ 36%) |
| 4 | `digitalCoachFeedbackSeen` | Teacher sees result |

### Retention

| Metric | Definition |
|--------|-----------|
| WoW Coach Retention | Coaches with observation events in week N ∩ week N+1 |
| Monthly Active Coaches | `COUNT(DISTINCT user_id)` where `name LIKE 'coachSchedule%'` per month |
| Digital Coach Teachers | `COUNT(DISTINCT user_id)` where `name = 'digitalCoachFeedbackSeen'` per month |

### Reliability

| Metric | Current | Status |
|--------|---------|--------|
| Observation Submit Rate | 6.7K / 14.8K (45%) | **55% drop-off** — monitor |
| Digital Coach Submit Rate | 21 / 58 (36%) | Low volume, early feature |

---

## Properties Reference

| Property | Type | Events | Description |
|----------|------|--------|-------------|
| `$.ep_date` | STRING | `planObservation` | Planned observation date |
| `$.ep_grade` | STRING | `planObservation` | Grade (e.g., "Grade One") |
| `$.ep_section` | STRING | `planObservation` | Section (e.g., "A") |
| `$.ep_subject` | INT | `planObservation` | Subject ID |
| `$.is_offline` | BOOL | All | Offline mode |
| `$.device_type` | STRING | All | mobile / tablet / desktop |
| `$.session_id` | STRING | All | Session ID |

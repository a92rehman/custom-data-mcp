# Taleemabad Data Domain: Comprehensive Research Report

**Date:** 2026-04-04
**Purpose:** Ground the Data Governance MCP Server in real Taleemabad domain knowledge
**Researcher:** Technical Researcher Agent (Claude Opus 4.6)

---

## Table of Contents

1. [Taleemabad Organizational Overview](#1-taleemabad-organizational-overview)
2. [Products and Services](#2-products-and-services)
3. [Theory of Change Model](#3-theory-of-change-model)
4. [Standards Framework (22 Standards)](#4-standards-framework-22-standards)
5. [FICO Observation Framework](#5-fico-observation-framework)
6. [Metric Definitions and Targets](#6-metric-definitions-and-targets)
7. [LP Review Rubric v3](#7-lp-review-rubric-v3)
8. [Certification Systems](#8-certification-systems)
9. [Technical Service Level Targets](#9-technical-service-level-targets)
10. [Data Governance and Security Standards](#10-data-governance-and-security-standards)
11. [Pakistan Education Context](#11-pakistan-education-context)
12. [EdTech Data Patterns](#12-edtech-data-patterns)
13. [Gold Metrics Catalog for the MCP](#13-gold-metrics-catalog-for-the-mcp)
14. [Sources](#14-sources)

---

## 1. Taleemabad Organizational Overview

Taleemabad is a Pakistani EdTech platform founded to revolutionize primary education by providing high-quality, standardized digital learning resources to underserved communities. The platform combines Pakistan's national curriculum (SNC 2020) with animated storytelling, adaptive assessments, and AI-powered teacher support tools.

### Key Facts

| Attribute | Detail |
|-----------|--------|
| **Headquarters** | Pakistan |
| **Focus** | K-12 education, primarily primary grades |
| **Reach** | 10+ million children weekly (via TV, radio, apps, schools) |
| **NIETE Scale** | 341 public schools, 4,044 teachers, ~98,000 students (Islamabad) |
| **User Growth** | 300,000+ direct users (historical); projected 1.3M |
| **Business Model** | B2B (school districts), B2G (government partnerships), B2C (freemium app) |
| **Key Partnerships** | Ministry of Federal Education (MoFEPT), Telenor Pakistan, Aga Khan University (AKU), LUMS School of Education, UNESCO, MIT Solve, EdTech Hub |
| **Reported Impact** | 31% faster literacy/numeracy gains; 70% dropout reduction in partner schools |

### NIETE Programme (National Institute of Excellence in Teacher Education)

Launched in 2024 by MoFEPT in partnership with Taleemabad. This is Pakistan's first university-recognized digital teacher training and licensing program (affiliated with LUMS). Rolled out AI-generated lesson plans following the Gradual Release of Responsibility model across 340+ schools in Islamabad. EdTech Hub evaluation found teachers consistently rated AI plans as better than their own, though platform data revealed low or inconsistent actual usage -- a key data governance challenge.

---

## 2. Products and Services

Taleemabad operates **six core services** evaluated across all 22 standards:

### 2.1 Lesson Plans (via Rumi)

- **Rumi** is Taleemabad's AI-powered Digital Teaching Companion, accessible via WhatsApp
- Generates complete lesson plans in under 2 minutes
- Multilingual: English, Urdu, Arabic, Spanish
- All plans aligned to SNC 2020 standard codes
- Follow I Do / We Do / You Do (Gradual Release) structure
- Benchmark: Rumi-generated LPs score 99.3% on LP Review Rubric v3 (vs. UGLP at 86.1%), effect size d=7.12

### 2.2 Digital Coach

- AI-powered classroom observation and coaching feedback
- Processes classroom audio for coaching analysis
- Scores observations against FICO framework (Sections B, C, D)
- Operates alongside human coaches: AI coaching 1x/week, human coaching 1x/3 weeks
- Inter-rater reliability target: >=75% agreement, kappa ~0.8
- Requires diarization (teacher vs. student voice separation) at >=90% accuracy

### 2.3 Teacher Training

- AKU (Aga Khan University) certified, credit-bearing
- Modular, practical, data-informed
- Includes classroom-applied learning model
- Tracked via module completion, quiz passage, and observable behavioral change

### 2.4 Exam Generator

- AI-generated assessments aligned to SNC 2020
- Latency SLA: 30 seconds
- Tracks: exam administration, results review, reteaching triggers, teacher overrides, student completion

### 2.5 Compliance Manager / User Management

- Student registration (PEFSIS-aligned)
- Photo-verified attendance tracking
- Requisitions, task management, bill tracking
- Live dashboards, automated reminders, exportable reports
- Role-based access: school directors, coordinators, teachers
- Auth latency: <3 seconds

### 2.6 Data & Analytics

- Dashboards with <10s load time; complex queries <30s
- Regional dashboards, comparison groups, reporting periods
- Lower uptime target (99%) vs. other services (99.5%)

---

## 3. Theory of Change Model

Taleemabad's Theory of Change follows a **five-stage pipeline**, each with a measurable metric:

```
Stage 1: LP Adoption (>=65%/week)
    |
    v
Stage 2: Coaching Loop (AI: 1x/week; Human: 1x/3 weeks)
    |
    v
Stage 3: Classroom Practice (FICO Section B >=60%)
    |
    v
Stage 4: Teacher Behavior Change (FICO Section C upward trend)
    |
    v
Stage 5: Student Learning (60% of students score 3/5+)
```

**Critical insight for data governance:** Each stage depends on the preceding stage. The MCP should model these as a causal chain -- if LP adoption drops, downstream metrics will lag. The data pipeline must track temporal dependencies between stages.

---

## 4. Standards Framework (22 Standards)

Taleemabad operates a 22-standard framework across three pillars, with four tiers of criticality.

### 4.1 Pillar Structure

| Pillar | Code | Focus Area |
|--------|------|------------|
| Pedagogical | P | Curriculum alignment, sequencing, gradual release, retrieval practice |
| Technical | T | Uptime, latency, security, offline resilience, model consistency |
| Product/Experience | X | Engagement tracking, UX, feedback loops, onboarding |

### 4.2 Tier Breakdown

| Tier | Count | Label |
|------|-------|-------|
| Tier 1 | 7 | Non-Negotiable |
| Tier 2 | 8 | Essential |
| Tier 3 | 4 | Advanced |
| Tier 4 | 3 | Specialized |

### 4.3 All 22 Standards

#### Tier 1: Non-Negotiable (7)

| ID | Name | KPI/Target |
|----|------|------------|
| P5 | Standards Alignment | 100% LP mapping to SNC 2020 standard codes |
| P2 | Prerequisite Sequencing | Curriculum graph adherence; no orphaned SLOs |
| P3 | Lesson-State Awareness | Real-time teaching timeline tracking |
| P1 | Gradual Release | 3-phase enforcement (I Do / We Do / You Do) |
| T10 | Security & Privacy | PII scrubbing; FERPA/GDPR compliance; encryption at rest |
| T2 | Latency SLAs | LP: 60s; Coach: 10m; Exams: 30s |
| X1 | Engagement Tracking | Behavioral telemetry (LP opened / used / modified / completed) |

#### Tier 2: Essential (8)

| ID | Name | KPI/Target |
|----|------|------------|
| P4 | Active Retrieval Practice | Every lesson includes recall activity from prior learning |
| T1 | Uptime | >=99.5% during school hours (8am-3pm local), per-service, per-building |
| T8 | Multi-Region Routing | Config-driven regional behavior (zero code changes) |
| T6 | Model Consistency | Version-locked models per scoring cycle; monthly drift audits |
| T9 | Offline Resilience | Graceful degradation; local caching; async sync |
| X5 | Mobile-First LMIC Design | <100KB page load; small screens; Urdu-first RTL |
| X3 | Feedback Mechanism | Single-tap feedback on all outputs |
| X8 | Behavioral Observability | Rejection rate, modification rate, time-to-value, override frequency |

#### Tier 3: Advanced (4)

| ID | Name | KPI/Target |
|----|------|------------|
| T5 | Framework Interop | Normalize HOTS/OECD/TEACH/FICO to 0-100% scale |
| X2 | Teacher Agency Loop | Teacher modifications feed back into generation cycle |
| X4 | Progressive Onboarding | Intelligent defaults; progressive feature reveal |
| X10 | Interoperability | MCP-ready; REST APIs + human UI + Model Context Protocol |

#### Tier 4: Specialized (3)

| ID | Name | KPI/Target |
|----|------|------------|
| P6 | Cross-Curricular Awareness | Surface connections between concurrent subjects |
| T3 | Diarization Accuracy | >=90% teacher vs. student voice separation |
| X7 | A/B Testing Rigor | Thompson Sampling; Wilson Score (reject "felt better" intuition) |

---

## 5. FICO Observation Framework

FICO is Taleemabad's custom classroom observation rubric. It spans **29 indicators** across three sections, each scored on a 4-point scale (1=Not Observed/Emerging through 4=Highly Effective).

### 5.1 Section B: Lesson Plan Fidelity (10 Indicators)

**Target: >=60% average across indicators**

| Code | Indicator | Level 4 (Highly Effective) Description |
|------|-----------|---------------------------------------|
| B1 | Instructional Clarity & Learning Objectives | Objective co-constructed with students; revisited; students articulate purpose |
| B2 | Lesson Structure & Sequence | I Do / We Do / You Do with smooth transitions and recap |
| B3 | Activities & Tasks Alignment | All activities purposefully scaffolded toward objective |
| B4 | Activation of Prior Knowledge | Students actively recall and link prior knowledge |
| B5 | Meaningful & Real-World Connections | Students generate own connections; community examples |
| B6 | Differentiation / Ability Grouping | Multiple pathways; struggling supported; advanced stretched |
| B7 | Use of Taleemabad Lesson Plan | Plan followed faithfully AND adapted intelligently |
| B8 | Use of Prescribed Resources | All resources used effectively; complementary additions |
| B9 | Time on Task / Learning | >85% of class time on learning activities; seamless routines |
| B10 | Lesson Closure & Consolidation | Students summarize, connect to next lesson, self-assess |

### 5.2 Section C: High-Leverage Practices (12 Indicators)

**Target: Upward trend over time (time-series analysis)**

| Code | Indicator | Level 4 Description |
|------|-----------|-------------------|
| C1 | Quality Questioning (Bloom's Aligned) | Span all Bloom's levels; students generate questions |
| C2 | Responsive Re-explanation & Adaptive Teaching | Diagnoses misconception; re-explains using student logic |
| C3 | Effective Feedback | Specific, actionable, with next steps; students self-correct |
| C4 | Equitable Participation | All students participate; deliberate strategies; gender-equitable |
| C5 | Student Agency & Voice | Students lead discussions, choose methods, self-assess, peer-teach |
| C6 | Classroom Management & Routines | Clear routines; minimal disruptions; students self-manage |
| C7 | Positive & Supportive Learning Environment | Joyful tone; mistakes celebrated; psychological safety |
| C8 | Modeling, Scaffolding & Problem-Solving | Gradual release with checks at each stage |
| C9 | Collaborative Learning | Structured collaboration (think-pair-share, jigsaw) |
| C10 | Integration of Taleemabad Technology | Seamlessly integrated; students interact actively |
| C11 | Self & Peer Assessment Facilitation | Students use rubrics; suggest improvements; set goals |
| C12 | Classroom Resources & Space for Collaboration | Tables for group work; materials accessible |

### 5.3 Section D: Student Engagement (7 Indicators)

**Target: 60% of students score 3/5+ on dipstick assessments**

| Code | Indicator | Level 4 Description |
|------|-----------|-------------------|
| D1 | Active Participation Rate | >75% actively engaged; students initiating |
| D2 | Cognitive Engagement Level (Bloom's) | Students creating, evaluating, debating |
| D3 | Student-to-Student Interaction | Students build on each other's ideas |
| D4 | Student Confidence & Risk-Taking | Volunteer answers; try difficult problems |
| D5 | On-Task Behavior During Independent Work | Self-regulate; persist through difficulty |
| D6 | Student Use of Learning Materials | Students use materials creatively |
| D7 | Inclusivity of Engagement | Marginalized students included; gender-equitable |

### 5.4 FICO Compliance Logic

| Verdict | Condition |
|---------|-----------|
| **Compliant** | Rubric score >=60% AND FICO Section B >=60% AND overall >=50% |
| **Partially Compliant** | One criterion passes; the other fails |
| **Non-Compliant** | Both rubric and FICO fail |

Only "Compliant" status qualifies for certification.

---

## 6. Metric Definitions and Targets

### 6.1 Primary KPIs (Theory of Change)

| Metric | Definition | Target | Measurement Method | Frequency |
|--------|-----------|--------|-------------------|-----------|
| LP Adoption Rate | Percentage of teachers engaging with AI-generated lesson plans aligned to SNC 2020 | >=65% per week | Weekly engagement tracking (LP opened/used/modified/completed) | Weekly |
| Coaching Loop Frequency | Combined AI and human coaching cadence | AI: 1x/week; Human: 1x/3 weeks | Coaching log audit | Weekly/Triweekly |
| FICO Section B Score | Average fidelity score across 10 LP fidelity indicators | >=60% | Classroom observation (AI + human scored) | Per observation |
| FICO Section C Trend | Directional improvement in high-leverage teaching practices | Upward trend | Time-series analysis of 12 indicators | Longitudinal |
| Student Assessment Performance | Proportion of students meeting proficiency threshold | 60% score 3/5+ | Dipstick assessments | Per assessment cycle |

### 6.2 Quality Assurance KPIs

| Metric | Definition | Target | Method |
|--------|-----------|--------|--------|
| Inter-Rater Reliability (IRR) | Agreement between AI Digital Coach and human coaches on observation scores | >=75% agreement; kappa ~0.8 | Cohen's kappa statistic |
| LP Review Score (Rumi) | Score on 9-dimension, 176-point LP rubric | >=75% pass; Rumi benchmark 99.3% | Rubric scoring |
| Diarization Accuracy | Correct separation of teacher vs. student voice in classroom audio | >=90% | Audio processing QA |
| Model Consistency | Same model + leniency settings across all teachers | Version-locked per cycle | Monthly drift audits |

### 6.3 Technical KPIs

| Metric | Target | Scope |
|--------|--------|-------|
| LP Generation Latency | <=60 seconds | Per request |
| Digital Coach Processing Latency | <=10 minutes | Per observation |
| Teacher Training Page Load | <=15 seconds | Per page |
| Exam Generation Latency | <=30 seconds | Per exam |
| Auth Response Time | <3 seconds | Per auth request |
| Dashboard Load Time | <10 seconds (simple); <30 seconds (complex) | Per query |
| Service Uptime (core) | >=99.5% during school hours (8am-3pm local) | Per-service, per-building |
| Service Uptime (analytics) | >=99% | Aggregate |
| Mobile Page Load Size | <100KB | Per page |

### 6.4 Engagement & Behavioral Metrics

These metrics are **tracked** (no prescribed thresholds) and serve as leading indicators:

**Lesson Plan Engagement Funnel:**
- LP opened -> LP scrolled/reviewed -> LP used in class -> LP modified -> LP completed

**Coach Engagement Funnel:**
- Observation viewed -> Feedback read -> Coaching acted upon -> Score agreement/disagreement -> Manual override frequency

**Training Engagement Funnel:**
- Module opened -> Module completed -> Quiz passed -> Behavioral change observable

**Exam Engagement Funnel:**
- Exam administered -> Results reviewed -> Reteaching triggered -> Teacher override rate -> Student completion rate

**Derived Behavioral Metrics:**
- Rejection rate (feedback thumbs-down frequency)
- Modification rate (how often teachers alter generated content)
- Time-to-value (time from content generation to classroom use)
- Override frequency (how often teachers override AI recommendations)

---

## 7. LP Review Rubric v3

### 9-Dimension Scoring Framework

**Maximum Points: 176 | Passing: >=75% (132 pts) | Excellent: >=90%**

| # | Dimension | Max Points | Description |
|---|-----------|-----------|------------|
| 1 | Structural Completeness | 20 | All required sections present and clearly organized |
| 2 | Curriculum Alignment | 24 | SLOs map explicitly to SNC 2020 standards |
| 3 | Instructional Flow | 36 | I Do / We Do / You Do; transitions; time allocation |
| 4 | Practicality & Teacher Support | 20 | Scripts, cues, instructions for Pakistani classroom context |
| 5 | Accessibility & Differentiation | 16 | Multiple pathways for different ability levels |
| 6 | Deeper Learning & Engagement | 16 | Activities beyond recall (Bloom's Analyze/Evaluate/Create) |
| 7 | Cultural Relevance | 16 | Pakistani context; local examples; community-grounded |
| 8 | Factual Accuracy | 16 | Content correct, current, age-appropriate |
| 9 | Subject-Specific Quality | 12 | Discipline-appropriate pedagogy (phonics, CPA, etc.) |

### Benchmark Performance

| Source | Score | Percentage |
|--------|-------|-----------|
| Rumi (AI-generated) | ~175/176 | 99.3% |
| UGLP (alternative) | ~152/176 | 86.1% |
| Effect Size (Rumi vs UGLP) | d=7.12 | Massive |

---

## 8. Certification Systems

### 8.1 Lesson Plan Certification Checklist (14 Items, 176 pts)

**Categories:**
- Structure & Curriculum (33 pts): SNC 2020 mapping, lesson phases, activities alignment, homework/exit ticket
- Gradual Release & Pedagogy (40 pts): Teacher scripts, student involvement, independent practice, prior knowledge
- Depth & Context (26 pts): Higher-order activities, cultural grounding, differentiation, factual accuracy
- Teacher Usability (20 pts): Standalone usability, resource identification, board content/visual aids

**Certification threshold:** >=75% (132 pts)

### 8.2 Coaching Observation Certification Checklist (19 Items)

**Certification threshold:** >=65% (13/19 indicators observed)

**Section B Fidelity (6 indicators):**
- Learning objective stated & referenced
- I Do / We Do / You Do structure
- Prior knowledge activation
- Taleemabad LP used
- >70% time on-task
- Structured lesson closure

**Section C High-Leverage Practices (7 indicators):**
- Open-ended questioning
- Specific, actionable feedback
- Equitable student call patterns
- Clear classroom routines
- Warm, supportive tone
- Problem-solving modeling
- Taleemabad tech integration

**Section D Student Engagement (6 indicators):**
- >50% visibly engaged
- Cognitive demand (not just copy/recall)
- Student-to-student content discussion
- Risk-taking comfort
- On-task independence
- Ability & gender equity in participation

---

## 9. Technical Service Level Targets

| Service | Latency SLA | Uptime Target | Availability Window | Monitoring Scope |
|---------|-------------|---------------|-------------------|-----------------|
| Lesson Plans | 60 seconds | 99.5% | 8am-3pm local | Per-service, per-building |
| Digital Coach | 10 minutes | 99.5% | 8am-3pm local | Per-service, per-building |
| Teacher Training | 15 seconds | 99.5% | 8am-3pm local | Per-service, per-building |
| Exam Generator | 30 seconds | 99.5% | 8am-3pm local | Per-service, per-building |
| User Management | 3 seconds | 99.5% | 8am-3pm local | Per-service, per-building |
| Data & Analytics | 10s/30s | 99% | Always | Aggregate acceptable |

**Critical design principle:** Aggregate uptime statistics are explicitly rejected as deceptive. All monitoring must be per-service AND per-region/building.

---

## 10. Data Governance and Security Standards

### From Standard T10 (Non-Negotiable)

| Control | Requirement |
|---------|------------|
| PII Scrubbing | Student names anonymized in all generated content |
| Encryption | At-rest encryption for all student response data |
| Compliance | FERPA/GDPR applicable standards |
| Audit Trails | Every data access logged; role-based access control (RBAC) |
| Consent Management | Voice recordings require explicit consent; no unauthorized audio retention |
| Offline Handling | Observations queue locally; resume on reconnect |

### Model Governance (Standard T6)

| Control | Requirement |
|---------|------------|
| Version Locking | Models locked per scoring cycle to prevent score drift |
| Monthly Audits | Systematic drift audits across all teachers |
| No Hidden Variation | Same model + leniency settings for all teachers |
| Transparency | No regional prompt variations; no hidden thumbs on the scale |

### Regional Configuration (Standard T8)

All services use **configuration-driven behavior** (no code deployment per region):

| Service | Regional Config Drivers |
|---------|----------------------|
| Lesson Plans | Curriculum type (SNC/Cambridge), language, format preferences |
| Digital Coach | Observation framework (HOTS/FICO/TEACH/OECD), language, rubric weights |
| Teacher Training | Regional curriculum, language, certification requirements |
| Exam Generator | Exam format, language, curriculum alignment |
| User Management | School hierarchy, regional admin roles, data policies |
| Data & Analytics | Regional dashboards, comparison groups, reporting periods |

### Framework Normalization (Standard T5)

All observation frameworks normalize to a common 0-100% scale:
- HOTS (Higher-Order Thinking Skills)
- OECD
- TEACH (World Bank)
- FICO (Taleemabad custom)

---

## 11. Pakistan Education Context

### 11.1 Single National Curriculum (SNC 2020)

The SNC is Pakistan's education reform initiative to standardize curriculum across all school types (public, private, madaris). This is a **foundational data dependency** for Taleemabad.

| Aspect | Detail |
|--------|--------|
| **Purpose** | Uniform educational standards across all school types |
| **SDG Alignment** | SDG 4 (Quality Education) |
| **Structure** | Standards, Benchmarks, and Student Learning Outcomes (SLOs) per subject |
| **Implementation** | Phase 1: Pre-1 to Grade V (2020); Phase 2: VI-VIII (2022); Phase 3: IX-XII (2023) |
| **Pedagogy Shift** | Away from rote memorization toward inquiry-based, student-centered learning |
| **Key Subjects** | Islamiat, Mathematics, General Knowledge, English, Urdu, Science |
| **Data Impact** | Every LP, SLO, and exam MUST map to explicit SNC 2020 standard codes (Standard P5: 100% mapping) |

### 11.2 Provincial Assessment Bodies

| Province/Region | Assessment Body | Framework |
|-----------------|----------------|-----------|
| Federal (Islamabad) | FBISE | Model Assessment Framework (MAF 2024) |
| Punjab | PECTAA | School-Based Assessment (SBA) |
| Sindh | SEF/SESLOAF | Sindh Education SLO Assessment Framework |
| KPK | Various | Provincial standards |
| Balochistan | Various | Provincial standards |

### 11.3 Data Implications for MCP

- **SLO Codes** are the atomic unit of curriculum alignment -- every metric must trace back to SLO codes
- **PEFSIS alignment** is required for student registration data (Compliance Manager)
- Regional variations mean the MCP must support **config-driven regional behavior** (Standard T8)
- Assessment data must be comparable across provinces via **framework normalization** (Standard T5)
- The SNC provides the canonical taxonomy for all educational content classification

### 11.4 Key Institutional Partners

| Institution | Role |
|-------------|------|
| MoFEPT | Federal ministry; NIETE programme sponsor |
| LUMS School of Education | University accreditation for teacher training |
| Aga Khan University (AKU) | Teacher training certification |
| EdTech Hub | Independent evaluation of AI lesson plans |
| UNESCO | Digital transformation financing toolkit |
| Telenor Pakistan | Infrastructure and connectivity partner |

---

## 12. EdTech Data Patterns

### 12.1 Data Categories Generated by Taleemabad

**Teacher Activity Data:**
- Lesson plan access logs (opened, scrolled, used, modified, completed)
- Training module progress (opened, completed, quiz scores)
- Coaching feedback interactions (viewed, read, acted upon)
- Feedback submissions (thumbs up/down, contextual notes)
- Override and rejection patterns

**Student Outcome Data:**
- Dipstick assessment scores (scored on 1-5 scale)
- Exam completion rates and scores
- Engagement indicators (participation, on-task behavior)
- Learning progression against SLOs
- Adaptive pathway assignments

**Classroom Observation Data:**
- FICO scores (29 indicators across B/C/D sections, each 1-4)
- AI vs. human scorer comparisons (IRR data)
- Audio recordings and diarization results
- Observation timestamps, duration, school/teacher context

**Operational/Technical Data:**
- Service uptime per-building, per-service
- Request latency per endpoint
- Error rates and error types
- Offline queue depth and sync status
- Model version tracking and drift metrics

**Compliance/Administrative Data:**
- Student registration records (PEFSIS-aligned)
- Photo-verified attendance
- Requisitions, financial tracking
- School hierarchy and role assignments

### 12.2 Typical EdTech Reporting Table Structure

Based on industry patterns and Taleemabad's specific needs:

```
fact_lesson_plan_usage
  - teacher_id, school_id, region_id
  - lp_id, snc_slo_code, subject, grade
  - event_type (opened|scrolled|used|modified|completed)
  - timestamp, session_duration
  - device_type, connectivity_status

fact_observation_scores
  - observation_id, teacher_id, school_id
  - observer_type (ai|human), observer_id
  - section (B|C|D), indicator_code (B1-B10, C1-C12, D1-D7)
  - score (1-4), section_average, overall_score
  - compliance_verdict (compliant|partial|non_compliant)
  - timestamp

fact_assessment_results
  - assessment_id, student_id (anonymized), teacher_id, school_id
  - snc_slo_code, subject, grade
  - score, max_score, proficiency_level (1-5)
  - assessment_type (dipstick|exam|quiz)
  - timestamp

fact_coaching_events
  - coaching_id, teacher_id, coach_id
  - coaching_type (ai|human)
  - feedback_items, action_items
  - teacher_response (agree|disagree|context_missing)
  - timestamp

fact_service_health
  - service_name, building_id, region_id
  - uptime_pct, latency_p50, latency_p95, latency_p99
  - error_count, error_types
  - measurement_window (hourly|daily)
  - timestamp

dim_teacher
dim_school
dim_region
dim_snc_slo (curriculum taxonomy)
dim_observation_framework
dim_date
```

---

## 13. Gold Metrics Catalog for the MCP

The following is the complete catalog of metrics that should be registered as **Gold-tier approved metrics** in the Data Governance MCP. Gold metrics have verified definitions, confirmed targets, identified data sources, and assigned stakeholders.

### 13.1 Theory of Change Metrics (5)

| # | Metric Name | Definition | Target | Data Source | Stakeholder | Category |
|---|------------|-----------|--------|------------|-------------|----------|
| 1 | `lp_adoption_rate_weekly` | Percentage of teachers engaging with AI-generated lesson plans per week | >=65% | fact_lesson_plan_usage (event_type IN used, modified, completed) | Pedagogy Team, School Leadership | ToC Stage 1 |
| 2 | `coaching_loop_frequency_ai` | Number of AI coaching observations per teacher per week | 1x/week | fact_coaching_events WHERE coaching_type='ai' | Digital Coach Team | ToC Stage 2 |
| 3 | `coaching_loop_frequency_human` | Number of human coaching observations per teacher per 3-week cycle | 1x/3 weeks | fact_coaching_events WHERE coaching_type='human' | Coaching Operations | ToC Stage 2 |
| 4 | `fico_section_b_average` | Average score across 10 LP fidelity indicators (B1-B10), 4-point scale | >=60% (2.4/4.0) | fact_observation_scores WHERE section='B' | Pedagogy Team | ToC Stage 3 |
| 5 | `student_proficiency_rate` | Percentage of students scoring 3/5 or higher on dipstick assessments | >=60% | fact_assessment_results WHERE score >= 3 | Curriculum Team, School Leadership | ToC Stage 5 |

### 13.2 FICO Observation Metrics (6)

| # | Metric Name | Definition | Target | Data Source | Stakeholder | Category |
|---|------------|-----------|--------|------------|-------------|----------|
| 6 | `fico_section_b_score` | Aggregated Section B fidelity score per teacher per observation | >=60% | fact_observation_scores | Pedagogy Team | Observation |
| 7 | `fico_section_c_trend` | Directional change in Section C average over rolling 3-month window | Upward trend | fact_observation_scores time-series | Pedagogy Team | Observation |
| 8 | `fico_section_d_engagement` | Aggregated Section D student engagement score | Tracked (no threshold) | fact_observation_scores | Student Outcomes Team | Observation |
| 9 | `fico_compliance_verdict` | Overall compliance classification | Compliant | fact_observation_scores + compliance logic | Quality Assurance | Observation |
| 10 | `observation_certification_rate` | Percentage of observations meeting >=65% (13/19) certification threshold | Tracked | Certification checklist results | Quality Assurance | Observation |
| 11 | `fico_indicator_score` | Individual indicator score (B1-B10, C1-C12, D1-D7) per observation | 1-4 scale | fact_observation_scores | Pedagogy Team | Observation |

### 13.3 Quality Assurance Metrics (5)

| # | Metric Name | Definition | Target | Data Source | Stakeholder | Category |
|---|------------|-----------|--------|------------|-------------|----------|
| 12 | `irr_agreement_rate` | Percentage agreement between AI and human observation scores | >=75% | IRR comparison table | AI/ML Team, QA | Quality |
| 13 | `irr_cohens_kappa` | Cohen's kappa coefficient for AI-human inter-rater reliability | kappa ~0.8 | IRR comparison table | AI/ML Team | Quality |
| 14 | `diarization_accuracy` | Percentage of correctly attributed teacher vs. student speech segments | >=90% | Audio processing QA logs | AI/ML Team | Quality |
| 15 | `model_drift_score` | Measured score drift between model versions per scoring cycle | No significant drift | Monthly drift audit results | AI/ML Team | Quality |
| 16 | `lp_rubric_score` | LP Review Rubric v3 score (176 pts, 9 dimensions) | >=75% (132 pts) | LP evaluation results | Content Team | Quality |

### 13.4 LP Quality Metrics (9 -- one per rubric dimension)

| # | Metric Name | Definition | Max Pts | Target | Category |
|---|------------|-----------|---------|--------|----------|
| 17 | `lp_structural_completeness` | All required sections present and organized | 20 | >=75% | LP Quality |
| 18 | `lp_curriculum_alignment` | SLOs map to SNC 2020 standards | 24 | 100% | LP Quality |
| 19 | `lp_instructional_flow` | Gradual release structure with transitions | 36 | >=75% | LP Quality |
| 20 | `lp_practicality` | Teacher scripts and Pakistani context support | 20 | >=75% | LP Quality |
| 21 | `lp_accessibility_differentiation` | Multiple pathways for ability levels | 16 | >=75% | LP Quality |
| 22 | `lp_deeper_learning` | Activities beyond recall (Bloom's higher levels) | 16 | >=75% | LP Quality |
| 23 | `lp_cultural_relevance` | Pakistani context, local examples | 16 | >=75% | LP Quality |
| 24 | `lp_factual_accuracy` | Content correctness and age-appropriateness | 16 | 100% | LP Quality |
| 25 | `lp_subject_specific_quality` | Discipline-appropriate pedagogy | 12 | >=75% | LP Quality |

### 13.5 Technical/Operational Metrics (12)

| # | Metric Name | Definition | Target | Data Source | Stakeholder | Category |
|---|------------|-----------|--------|------------|-------------|----------|
| 26 | `service_uptime_core` | Per-service, per-building uptime during school hours | >=99.5% | fact_service_health | Engineering, Ops | Technical |
| 27 | `service_uptime_analytics` | Data & Analytics service uptime | >=99% | fact_service_health | Engineering | Technical |
| 28 | `lp_generation_latency` | Time to generate a lesson plan | <=60s | Request logs | Engineering | Technical |
| 29 | `coach_processing_latency` | Time to process a coaching observation | <=10m | Request logs | Engineering | Technical |
| 30 | `exam_generation_latency` | Time to generate an exam | <=30s | Request logs | Engineering | Technical |
| 31 | `training_page_load` | Teacher training page load time | <=15s | Request logs | Engineering | Technical |
| 32 | `auth_response_time` | Authentication response time | <3s | Request logs | Engineering | Technical |
| 33 | `dashboard_load_time` | Dashboard and analytics query time | <10s simple; <30s complex | Request logs | Engineering | Technical |
| 34 | `mobile_page_size` | Page payload size for mobile delivery | <100KB | Network analysis | Engineering, UX | Technical |
| 35 | `offline_queue_depth` | Number of pending sync operations during offline mode | Tracked | Sync queue metrics | Engineering | Technical |
| 36 | `snc_alignment_coverage` | Percentage of content mapped to SNC 2020 standard codes | 100% | Content mapping table | Curriculum Team | Technical |
| 37 | `error_rate_per_service` | Error count and types per service per time window | Tracked | Error logs | Engineering | Technical |

### 13.6 Engagement & Behavioral Metrics (8)

| # | Metric Name | Definition | Target | Data Source | Stakeholder | Category |
|---|------------|-----------|--------|------------|-------------|----------|
| 38 | `lp_funnel_completion_rate` | Conversion from LP opened to LP completed | Tracked (upward trend) | fact_lesson_plan_usage | Product, Pedagogy | Engagement |
| 39 | `lp_modification_rate` | Percentage of LPs modified by teachers before use | Tracked | fact_lesson_plan_usage | Product, Pedagogy | Engagement |
| 40 | `feedback_rejection_rate` | Percentage of negative feedback (thumbs-down) across all services | Tracked (downward trend) | Feedback logs | Product | Engagement |
| 41 | `coaching_action_rate` | Percentage of coaching feedback acted upon by teachers | Tracked (upward trend) | fact_coaching_events | Coaching Ops | Engagement |
| 42 | `training_completion_rate` | Percentage of training modules completed per teacher | Tracked | Training progress logs | Teacher Development | Engagement |
| 43 | `exam_reteaching_trigger_rate` | Percentage of exams triggering reteaching actions | Tracked | Exam workflow logs | Curriculum Team | Engagement |
| 44 | `time_to_value` | Elapsed time from content generation to classroom use | Tracked (downward trend) | Timestamp analysis | Product | Engagement |
| 45 | `teacher_override_rate` | Frequency of teachers overriding AI recommendations | Tracked | Override logs | AI/ML Team, Product | Engagement |

### 13.7 Compliance & Administrative Metrics (4)

| # | Metric Name | Definition | Target | Data Source | Stakeholder | Category |
|---|------------|-----------|--------|------------|-------------|----------|
| 46 | `attendance_verification_rate` | Percentage of attendance records with photo verification | Tracked | Compliance Manager | School Ops | Compliance |
| 47 | `pefsis_registration_compliance` | Percentage of students registered per PEFSIS standards | 100% | User Management | Compliance | Compliance |
| 48 | `data_access_audit_coverage` | Percentage of data access events with audit trail | 100% | Audit logs | Security, Compliance | Compliance |
| 49 | `pii_scrubbing_compliance` | Percentage of generated content verified PII-free | 100% | Content scanning logs | Security | Compliance |

### 13.8 Certification Metrics (3)

| # | Metric Name | Definition | Target | Data Source | Stakeholder | Category |
|---|------------|-----------|--------|------------|-------------|----------|
| 50 | `lp_certification_rate` | Percentage of LPs meeting >=75% (132/176 pts) certification threshold | Tracked | LP evaluation results | Content QA | Certification |
| 51 | `coaching_certification_rate` | Percentage of observations meeting >=65% (13/19) certification threshold | Tracked | Observation certification results | Coaching QA | Certification |
| 52 | `teacher_aku_certification_rate` | Percentage of teachers completing AKU-certified training | Tracked | Training completion records | Teacher Development | Certification |

---

### Summary: Gold Metrics by Category

| Category | Count | Key Threshold Metrics |
|----------|-------|-----------------------|
| Theory of Change | 5 | LP Adoption >=65%, FICO-B >=60%, Student Proficiency >=60% |
| FICO Observation | 6 | Section B >=60%, Section C upward trend, Certification >=65% |
| Quality Assurance | 5 | IRR >=75%, kappa ~0.8, Diarization >=90%, LP Rubric >=75% |
| LP Quality (9 dimensions) | 9 | Per-dimension scores against 176-pt rubric |
| Technical/Operational | 12 | Uptime >=99.5%, latency SLAs, SNC coverage 100% |
| Engagement & Behavioral | 8 | All tracked (no hard thresholds; trend-based) |
| Compliance | 4 | PII scrubbing 100%, audit coverage 100% |
| Certification | 3 | LP cert >=75%, Coaching cert >=65% |
| **Total** | **52** | |

---

## 14. Sources

[1] Taleemabad. "Standards Hub - Reference." Taleemabad Standards Hub, 2025. https://taleemabad-standards-hub.vercel.app/reference.html

[2] Taleemabad. "Standards Evaluator." Taleemabad Standards Hub, 2025. https://taleemabad-standards-hub.vercel.app/

[3] UNESCO. "Taleemabad - Financing the Digital Transformation of Education." UNESCO DTC Financing Toolkit. https://www.unesco.org/en/dtc-financing-toolkit/taleemabad

[4] MIT Solve. "Taleemabad." MIT Solve Solutions. https://solve.mit.edu/solutions/20079

[5] Taleemabad. "Solutions - Comprehensive Educational Tools." Taleemabad, 2025. https://taleemabad.com/solutions/

[6] EdTech Hub. "Evaluation of AI-Powered Lesson Plans in Pakistan." EdTech Hub, 2025. https://edtechhub.org/evaluation-of-ai-powered-lesson-plans-in-pakistan/

[7] Pakistan Foundational Learning Hub. "What is NIETE?" PFL Hub, 2024. https://www.pflhub.com/blog/what-is-the-national-institute-of-excellence-in-teacher-education

[8] ProPakistani. "Education Ministry Launches Digital Teacher Training and Support Program." December 2023. https://propakistani.pk/2023/12/19/education-ministry-launches-digital-teacher-training-and-support-program/

[9] Pakistan Ministry of Federal Education and Professional Training. "Single National Curriculum." MoFEPT, 2020. https://mofept.gov.pk/

[10] FBISE. "Assessment Frameworks 2025." Federal Board of Intermediate and Secondary Education. https://www.fbise.edu.pk/curriculum_model_paper.php

[11] UNICEF Innocenti. "Data Governance for EdTech." UNICEF, 2025. https://www.unicef.org/innocenti/reports/data-governance-edtech

[12] 1EdTech. "Learning Data and Analytics." 1EdTech. https://www.1edtech.org/workstream/analytics

[13] Cohen's Kappa. "Interrater Reliability: The Kappa Statistic." PMC/NIH. https://pmc.ncbi.nlm.nih.gov/articles/PMC3900052/

---

## Appendix A: Observation Framework Interoperability Map

The MCP must support normalization across these frameworks to a common 0-100% scale:

| Framework | Origin | Use Case | Normalization Notes |
|-----------|--------|----------|-------------------|
| FICO | Taleemabad (custom) | Primary framework; B/C/D sections | Native 1-4 scale -> 0-100% |
| HOTS | Various | Higher-Order Thinking Skills assessment | Map to Bloom's taxonomy levels |
| TEACH | World Bank | International teacher effectiveness framework | Standardized classroom observation |
| OECD | OECD | International education quality benchmarks | Cross-country comparison |

## Appendix B: Feedback Taxonomy

All services support lightweight feedback with these categories:

| Service | Feedback Options |
|---------|-----------------|
| Lesson Plans | thumbs-up / thumbs-down / "Request change" / "Not possible in my context" |
| Digital Coach | "Agree" / "Disagree" / "Context missing" |
| Teacher Training | "Useful" / "Not useful" / "Already know this" |
| Exam Generator | "Good" / "Too hard" / "Off-topic" + per-question flagging |

## Appendix C: A/B Testing Standards

Standard X7 mandates statistical rigor for all feature testing:
- **Method:** Thompson Sampling (adaptive allocation)
- **Confidence:** Wilson Score intervals
- **Principle:** Reject "felt better" intuition; require statistical evidence
- **Implication for MCP:** All experiment metrics must include confidence intervals and effect sizes

## Appendix D: Mobile/LMIC Constraints for Data Collection

| Constraint | Specification |
|------------|--------------|
| Page load budget | <100KB |
| Target device | 5.5" budget Android phone |
| Connectivity | 3G/4G; intermittent |
| Language | Urdu-first; RTL layout |
| Interaction | Large tap targets; simple workflows |
| Offline support | Core functions cache locally; async sync queue |

These constraints directly impact data collection architecture: telemetry must be lightweight, batched, and resilient to connectivity drops.

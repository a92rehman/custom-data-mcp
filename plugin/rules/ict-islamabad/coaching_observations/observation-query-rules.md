# Coaching Observation Query Rules

## When These Rules Apply

User asks about:
- Classroom observation scores or results
- FICO Section B (Lesson Plan Fidelity), Section C (Student Learning Outcomes), Section D (Student Engagement)
- Coach, principal, or Digital Coach (AI) observation activity
- Feedback given during observations
- Per-question or per-section breakdowns
- Which teachers were observed, by whom, and when

## Mandatory Clarifications

### Section
Ask: "Which observation section? B (LP Fidelity), C (Student Learning), D (Student Engagement), or all?"

### Aggregation Level
Ask: "Per observation, per teacher, per school, or overall?"

### Observer Type
Ask if relevant: "All observers, or specific type? (NIETE-Coach, Principal, Digital Coach)"

### Active Only
Default to active observations only (`co.is_active = 'true'`). Only include missed/cancelled if the user explicitly asks.

## Three Scored Sections

| Section | What it measures | How to identify |
|---------|-----------------|-----------------|
| **B** — LP Fidelity | How well teachers follow lesson plans | `os.id IN (1, 7)` |
| **C** — Student Learning Outcomes | Quality of teaching practices | `oq.id IN (5,6,7,8,10,13,14,15,16,17,18)` |
| **D** — Student Engagement | Student participation and engagement | `oq.section_id = 5 AND oq.id IN (19,20,21,22,23,5300)` |

The `section_type` column emits `'B'`, `'C'`, `'D'`, or `'Other'`.

The `question_block` column extracts block labels from question prompts (e.g., B1, C3, D2) via `REGEXP_EXTRACT`.

## Score Mapping

Raw answers map to numeric scores:

| Answer (`score_type`) | Numeric |
|----------------------|---------|
| `'yes'` | 1.0 |
| `'partial'` | 0.5 |
| `'no'` | 0.0 |
| `'ignore'` | 0.0 |

**`'ignore'` is included in the average** — treat it the same as `'no'`, never exclude it from the denominator.

## Aggregation Rules

### Per-observation section score
Average the numeric scores across all questions in that section for one observation:
```
section_b_score = AVG(numeric_score) WHERE section_type = 'B' GROUP BY Observation_ID
```

### Further aggregation

| User asks about | GROUP BY | Aggregate |
|-----------------|----------|-----------|
| Score per observation | `Observation_ID` | `AVG(numeric_score)` per section |
| Score per teacher | `teacher_profile_id` or `User_id` | `AVG(section_score)` |
| Score per school | `school_emis` | `AVG(section_score)` |
| Score per school with name | Join `school_emis` to `FDE_Schools` for school name |

## Observer Types

Observers are stored polymorphically via two columns on `coaching_observation`:
- `user_profile_content_type_id = 173` → NIETE-Coach (join to `users_coachprofile`)
- `user_profile_content_type_id = 70` → Principal (join to `users_principalprofile`)
- Digital Coach (AI) observations — check with data team for identification method

## AI vs Human Observation Bifurcation

The `source` column on `coaching_observationquestion` distinguishes AI from human observations:
- `source = 'manual'` → Human coach/principal questions (125,676 questions)
- `source = 'automated'` → AI/Digital Coach questions (107 questions)

To filter for human-only observations, add `oq.source = 'manual'` (or `oq.source IS NULL OR oq.source = 'manual'`).
To filter for AI observations, add `oq.source = 'automated'`.

See `coaching_ai/ai-coaching-rules.md` for full AI coaching rules.

## Key Tables

### Raw Tables (canonical for query building)

| Table | Role |
|-------|------|
| `tbproddb.coaching_observation` | Core record — date, boys/girls count, feedback, observer type |
| `tbproddb.coaching_teachervisit` | Links observation to teacher + grade_subject |
| `tbproddb.coaching_observationanswer` | One row per question answered |
| `tbproddb.coaching_observationquestion` | Question metadata — prompt, type, purpose, section, **source** |
| `tbproddb.coaching_questionoption` | Selected answer — label, score_type |
| `tbproddb.coaching_observationquestiongroup` | Question groups — title, order |
| `tbproddb.coaching_observationsection` | Section container (used to classify B/C/D) |
| `tbproddb.coaching_observationtemplate` | Top-level template |
| `tbproddb.users_coachprofile` + `users_user` | Coach identity |
| `tbproddb.users_principalprofile` + `users_user` | Principal identity |
| `tbproddb.user_school_profiles` | Teacher dimension — join via `profile_id = teacher_id` |
| `tbproddb.FDE_Schools` | ICT school reference — join on EMIS for school name |

### Pre-processed FICO Tables (verification / quick lookups)

These are **pre-processed clean tables** maintained by the data team. Use for quick verification or when the raw query is too complex. For governed reporting, prefer the raw tables above — they are the source of truth.

| Table | Role | Rows | Status |
|-------|------|------|--------|
| `tbproddb.Fico_Observations` | Pre-processed observation summaries with observer/teacher/school | 6,697 | Active — use for verification |
| `tbproddb.Fico_Lesson_Fidelity_Data` | Section B scores (B1-B13) per observation | 0 | Empty — not yet populated |
| `tbproddb.cf_indicators_data_fico` | Section C indicator scores (Q5-Q18) per observation | 0 | Empty — not yet populated |
| `tbproddb.mini_assessment_fico_data` | Mini-assessment student correct counts per observation | 0 | Empty — not yet populated |
| `tbproddb.fico_teacher_obs_details` | Teacher observation sequence (observation_number, order_label) | 0 | Empty — not yet populated |

### Fico_Observations Key Columns
- `Observation_ID` — primary key (STRING)
- `Observation_Created`, `Observation_Modified` — dates (DATE)
- `Observation_Date` — display date (STRING)
- `Observer_Role`, `Observer_Name` — observer identity
- `Teacher_Name`, `Teacher_user_id`, `TeacherprofileID` — teacher identity
- `School_Emis`, `School_Name`, `Sector` — school context
- `Grade`, `Subject` — classroom context
- `Observation_Completion_Status` — completion status
- `Feedback_Given` — whether feedback was provided (STRING)
- `Feedback_Text` — actual feedback text (STRING)

**When to use raw vs FICO tables:**
- **Raw tables**: governed queries, score calculations, section breakdowns, custom aggregations
- **Fico_Observations**: quick observation counts, observer/teacher/school lookups, verification of raw query results
- **Other FICO tables**: currently empty (0 rows) — will be useful when populated for Section B/C score verification

## Required Filters

- `oa.is_active = 'true'` — active answers only
- `oq.is_active = 'true'` — active questions only
- `co.is_active = 'true'` — active observations only (excludes missed/cancelled)
- `oq.purpose = 'general' OR oq.prompt LIKE 'B%'` — excludes metadata/admin questions
- Section inclusion filter (B/C/D question IDs listed above) — defines which scored questions to include
- `is_active` filters also apply in JOIN conditions on `qo`, `oqg`, `os`, `ot`

## Important Notes

- Each `Observation_ID` is a unique classroom visit
- One observation has multiple rows (one per question answered)
- Section C question IDs `(5,6,7,8,10,13,14,15,16,17,18)` are the current template — may change if new questions are added
- Section D question IDs `(19,20,21,22,23,5300)` — same caveat
- `user_school_profiles` join: `usp.profile_id = tv.teacher_id`
- For school-level averages: join `school_emis` to `FDE_Schools` for school name

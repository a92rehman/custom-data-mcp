# Human Student Assessment (ASER) Query Rules — Rawalpindi

> **STATUS: DRAFT** — Pending Ahwaz verification of rubric_item_id, status_id, and subject_id mappings. Do not use for production reporting until verified.

## When These Rules Apply

User asks about:
- ASER assessment results in Rawalpindi
- Human-administered student evaluations
- Coach-led student assessments
- Rubric item scores or levels

## Mandatory Clarifications

### Grain
Ask: "Assessment count (per student session) or rubric-level results (per item scored)?"
- 93 assessment sessions vs 264 rubric item scores — different grains

### Subject
Ask: "Which subject, or all?"
- `subject_id` available but mapping TBD

### Aggregation Level
Ask: "Per student, per school, per assessor, or overall?"

## Key Tables

| Table | Role | Rows | Dataset |
|-------|------|------|---------|
| `TaleemHub_DB.aser_assessment_results` | Individual rubric item scores | 264 | TaleemHub_DB |
| `TaleemHub_DB.aser_assessments` | Assessment sessions (one per student per subject) | 93 | TaleemHub_DB |
| `TaleemHub_DB.aser_student_profiles` | Student identity and school | 33 | TaleemHub_DB |
| `TaleemHub_DB.users` | Assessor identity | 1,296 | TaleemHub_DB |

**Note:** These tables are small and unpartitioned. Full scans are acceptable at this scale.

## Join Path

```sql
SELECT ...
FROM TaleemHub_DB.aser_assessment_results aar
JOIN TaleemHub_DB.aser_assessments aa ON aar.assessment_id = aa.id
JOIN TaleemHub_DB.aser_student_profiles asp ON aa.student_profile_id = asp.id
LEFT JOIN TaleemHub_DB.users u ON aa.created_by_user_id = u.id
```

## Count Clarification (93 vs 264)

- **93 assessments** = unique assessment sessions (`aser_assessments`), one per student per subject
- **264 results** = rubric item scores (`aser_assessment_results`), multiple rubric items per assessment
- These are different grains, NOT a data conflict
- For session count KPIs: `COUNT(DISTINCT aa.id)`
- For rubric detail: `COUNT(DISTINCT aar.id)`

## Key Columns

### aser_assessment_results
- `id` — primary key (STRING)
- `assessment_id` — FK to `aser_assessments.id`
- `rubric_item_id` — which ASER rubric item (STRING — **mapping TBD, needs verification**)
- `status_id` — score/outcome for this item (STRING — **mapping TBD, needs verification**)
- `created_at` — timestamp (STRING)

### aser_assessments
- `id` — primary key (STRING)
- `student_profile_id` — FK to `aser_student_profiles.id`
- `subject_id` — which subject (STRING — **mapping TBD, needs verification**)
- `notes` — assessor notes (STRING)
- `created_by_user_id` — FK to `TaleemHub_DB.users.id` (the coach/assessor)
- `created_at`, `updated_at` — timestamps (STRING)

### aser_student_profiles
- `id` — primary key (STRING)
- `student_name`, `student_name_normalized` — student identity
- `school_id` — FK for school-level rollups (STRING)
- `grade_level` — student grade (INTEGER)
- `created_at` — timestamp (STRING)

## Verification Needed (before removing DRAFT)

1. **`rubric_item_id` mapping** — What ASER levels do values represent? (e.g., Nothing, Letter, Word, Sentence, Story)
2. **`status_id` mapping** — What scores/outcomes do values mean? (e.g., passed, failed, partial)
3. **`subject_id` mapping** — What subjects exist? (e.g., Urdu reading, Math, English)
4. **Count reconciliation** — Verify 93 assessments / 264 results with Ahwaz

Run these discovery queries:
```sql
SELECT DISTINCT rubric_item_id, COUNT(*) FROM TaleemHub_DB.aser_assessment_results GROUP BY rubric_item_id
SELECT DISTINCT status_id, COUNT(*) FROM TaleemHub_DB.aser_assessment_results GROUP BY status_id
SELECT DISTINCT subject_id, COUNT(*) FROM TaleemHub_DB.aser_assessments GROUP BY subject_id
```

## Key Difference from ICT

- ICT student results - coaches is **DEPRECATED** per CEO doc
- ICT ASER uses **ODK tables** (`odk.NIETE_-_ICT_-_IMPACT_ICT-ENDLINE-ASER_1-3_Test`) — completely different structure
- Cross-region: **volume comparison only** until RWP rubric mapping is confirmed

## Aggregation Patterns

| User asks about | GROUP BY | Aggregate |
|-----------------|----------|-----------|
| Total assessments | — | `COUNT(DISTINCT aa.id)` |
| Students assessed | — | `COUNT(DISTINCT asp.id)` |
| Results per student | `asp.id`, `asp.student_name` | `COUNT(DISTINCT aar.id)` |
| By school | `asp.school_id` | `COUNT(DISTINCT aa.id)` |
| By grade | `asp.grade_level` | `COUNT(DISTINCT aa.id)` |
| By subject | `aa.subject_id` | `COUNT(DISTINCT aa.id)` |
| By assessor | `aa.created_by_user_id` | `COUNT(DISTINCT aa.id)` |

## Data Conventions

- Timezone: `Asia/Karachi` for all date conversions
- All ID columns are STRING type
- Timestamps are stored as STRING — cast with `PARSE_TIMESTAMP` or `PARSE_DATE` as needed

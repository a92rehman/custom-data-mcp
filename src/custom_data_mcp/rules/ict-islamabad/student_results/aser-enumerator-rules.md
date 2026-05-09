# Student Results — Enumerator ASER Assessment Rules — ICT/Islamabad

## When These Rules Apply

User asks about:
- ASER assessment results from ICT enumerators
- Endline student assessment data
- Student reading/math levels from field assessments
- Enumerator-collected student performance data
- Impact study results

## Mandatory Clarifications

### Grade Range
Ask: "Grades 1-3, grades 4-5, or both?"
- Different ODK forms for each grade range with different column structures
- Grades 1-3: basic letter/word/sentence recognition
- Grades 4-5: sentence fluency, story reading, comprehension

### Subject
Ask: "English, Urdu, Math, or all?"
- Each subject has its own set of columns within the ODK forms

### Assessment Type
Ask if relevant: "Endline only, or include baseline/midline/backchecks?"
- Canonical tables are endline. Other waves available in ODK dataset.

## Key Tables

### Canonical: ICT Endline ASER

| Table | Role | Rows | Dataset |
|-------|------|------|---------|
| `odk.NIETE_-_ICT_-_IMPACT_ICT-ENDLINE-ASER_1-3_Test` | Grades 1-3 ASER endline | 966 | odk |
| `odk.NIETE_-_ICT_-_IMPACT_ICT-ENDLINE-ASER_4-5_Test` | Grades 4-5 ASER endline | 995 | odk |

### Other Waves (verification/comparison only)

| Table | Role | Rows |
|-------|------|------|
| `odk.Baseline_-_NIETE_ASER_Test_1-3_Test` | Baseline grades 1-3 | — |
| `odk.Baseline_-_NIETE_ASER_Test_4-5_test` | Baseline grades 4-5 | — |
| `odk.NIETE_-_ICT_-_IMPACT_ICT-Shortfall-ASER_1-3_Test` | ICT shortfall 1-3 | — |
| `odk.NIETE_-_ICT_-_IMPACT_ICT-shortfall-ASER_4-5_Test` | ICT shortfall 4-5 | — |
| `odk.NIETE_-_ICT_-_IMPACT_BackcheckICT-ENDLINE-ASER_1-3` | ICT endline backcheck 1-3 | — |
| `odk.NIETE_-_ICT_-_IMPACT_BackcheckICT-ENDLINE-ASER_4-5` | ICT endline backcheck 4-5 | — |

### RWP ASER in ODK (for cross-region verification)

| Table | Role |
|-------|------|
| `odk.NIETE_-_ICT_-_IMPACT_RWP-ENDLINE-ASER_1-3_feb` | RWP endline 1-3 |
| `odk.NIETE_-_ICT_-_IMPACT_RWP-ENDLINE-ASER_4-5_Test` | RWP endline 4-5 |

**Note:** These tables are unpartitioned but small (<1,000 rows each). Full scans acceptable.

## Key Columns — Grades 1-3 (`ICT-ENDLINE-ASER_1-3_Test`)

### Metadata
- `__id` — unique submission ID (STRING)
- `start`, `end` — form start/end timestamps (STRING)
- `submission_time` — when submitted (STRING)
- `survey_day` — survey date (STRING)
- `deviceid` — enumerator device ID (STRING)

### Student Info
- `Information_district` — district name
- `Information_enumerator` — enumerator name
- `Information_emis_name` — school EMIS + name
- `Information_student_available` — whether student was present
- `survey_student_name`, `survey_Other_student_name` — student identity
- `survey_other_student_age`, `survey_other_student_gender` — demographics
- `survey_grade_section`, `survey_current_grade_section` — grade
- `survey_new_teacher_name` — teacher name
- `greetings_section_consent` — consent obtained

### English Assessment (Grades 1-3)
- `english_eng_5_capital_letters` — capital letter recognition
- `english_eng_5_small_letters` — small letter recognition
- `english_eng_5_words` — word reading
- `english_eng_word_meaning` — word meaning
- `english_eng_read_4_sentences` — sentence reading

### Urdu Assessment (Grades 1-3)
- Columns follow similar pattern with `urdu_` prefix

### Math Assessment (Grades 1-3)
- Columns follow similar pattern with `math_` prefix

## Key Columns — Grades 4-5 (`ICT-ENDLINE-ASER_4-5_Test`)

Same metadata and student info columns as 1-3, plus:

### English Assessment (Grades 4-5)
- `english_G4_5_eng_read_sentences_G4_5` — sentence reading
- `english_G4_5_eng_sentence_G4_fluency` — fluency rating
- `english_G4_5_eng_sentences_meaning_G4_5` — comprehension
- `english_G4_5_eng_read_story_fluency_G4_5` — story reading fluency
- `english_G4_5_eng_comprehension` — story comprehension

### Urdu and Math follow similar extended patterns

## ASER Level Classification

ASER assessments classify students into levels (standard ASER methodology):
- **Nothing** — cannot identify letters
- **Letter** — recognizes letters but not words
- **Word** — reads words but not sentences
- **Sentence** — reads sentences but not stories/paragraphs
- **Story/Paragraph** — reads connected text fluently

The specific column values encode these levels — exact encoding varies by form. Check distinct values before aggregating.

## Required Filters

- `Information_student_available` — filter to available students
- `greetings_section_consent` — filter to consented assessments
- Join on `Information_emis_name` to `FDE_Schools` for school-level rollups (parse EMIS from string)

## Key Difference from RWP

- ICT ASER: **ODK-based** field enumerator assessments with structured forms
- RWP ASER: **TaleemHub-based** coach-administered assessments with rubric_item_id/status_id
- Cross-region: **volume comparison only** — different tools, different rubric structure
- RWP also has separate AI reading assessments (Rumi) — ICT does not have an active equivalent

## Aggregation Patterns

| User asks about | How to query |
|-----------------|-------------|
| Total students assessed | `COUNT(DISTINCT __id)` from each grade table |
| By school | GROUP BY `Information_emis_name` |
| By enumerator | GROUP BY `Information_enumerator` |
| By grade | Query grade-specific table, or combine with grade label |
| English level distribution | Count distinct values of English assessment columns |
| Cross-wave comparison | Join baseline + endline on student identity columns |

## EGRA/EGMA Assessment

> **STATUS: TBD** — Ahwaz to provide table details. Not yet available.

EGRA (Early Grade Reading Assessment) and EGMA (Early Grade Mathematics Assessment) are additional assessment instruments. Tables and rules will be added when confirmed.

## Important Notes

- ODK forms are flat — each row is one complete student assessment
- Column names are long and descriptive (form field paths)
- All values are STRING type — cast as needed for numeric analysis
- Grade 1-3 and 4-5 forms have **different column structures** — do not UNION without mapping
- The 52 tables in the `odk` dataset cover multiple assessment waves, regions, and instruments
- Always verify which table corresponds to the user's request (ICT vs RWP, endline vs baseline, etc.)

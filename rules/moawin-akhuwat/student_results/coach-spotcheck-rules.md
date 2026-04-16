# Student Results — Coach Spot Checks Query Rules — Moawin / Akhuwat

> **STATUS: COMING SOON** — Table deployment TBD. Schema and structure to be provided by **Mahrah Ashraf** on/before **April 13, 2026**. This rule file is a placeholder and should NOT be used for queries until confirmed.

## When These Rules Apply (Upon Availability)

User asks about:
- Coach-collected student spot check assessments in Moawin or Akhuwat
- Quick student performance assessments during coaching visits
- Student learning outcome spot checks or rapid evaluations
- Coach-administered student result data

## Mandatory Clarifications (When Rules Are Active)

### Assessment Type / Standard
Ask: "Which spot check standard or type?" (once schema is finalized)
- Verify available spot check types with data team

### Coach / Assessor
Ask: "All coaches, or specific coach/observer?"

### Time Period
Ask: "Which time period?"

### Region
Ask: "Moawin or Akhuwat?"

## Current Status

### What We Know
- **Table:** TBD (to be provided by Mahrah Ashraf)
- **Dataset:** Likely `Muawin_Akhuwat_db` (Schoolpilot) or new dedicated BigQuery dataset
- **Purpose:** Coach-collected spot checks during visits or coaching sessions
- **Standard Format:** Follow same structure as other spot check implementations (TBD)
- **Relationship:** May link to coaching_sessions or visits, or be standalone

### What We Need

1. **Table name and dataset** (e.g., `Muawin_Akhuwat_db.coach_spotchecks` or a new dedicated BigQuery dataset)
2. **Schema:** All column names, types, and meanings
3. **Key identifiers:** Student ID, coach/assessor ID, assessment date, spot check type/standard
4. **Score/Result columns:** How are spot check results captured? (numeric, categorical, rubric-based, etc.)
5. **Links to other tables:**
   - FK to coaching_sessions or visits?
   - FK to student records?
   - FK to coach/teacher records?
6. **Regional split:** How is region identified? (organization_id, school_id, etc.)
7. **Filtering rules:**
   - Test/pilot data exclusion?
   - Status/completion filters?
   - Required date ranges?
8. **Aggregation level:** Per student, per coach, per visit, per school?

### Deployment Deadline
- Deployment: April 13, 2026 (per reconciliation notes)
- Rule finalization: Immediately after table structure confirmed
- Expected in next rules update: Post-April 13

## Placeholder Structure

Once the table is available, this rule file will include:

- **Key Tables** section with exact table names and schemas
- **Key Columns** section with descriptions of all relevant fields
- **Join Patterns** for regional/coach/student context
- **Filtering Rules** for test data, dates, completion status
- **Counting Rules** specific to spot check grain (per student, per coach, etc.)
- **Aggregation Patterns** table with standard queries
- **Data Conventions** for timezone, date formats, score scales
- **Key Differences** from AI assessments and school assessments
- **Important Notes** on data quality, join keys, and caveats

## Action Items

1. **Await table deployment** from Mahrah Ashraf (deadline Apr 13)
2. **Gather schema documentation** once table is available
3. **Update this rule file** with complete specifications
4. **Test queries** against production data
5. **Add to index.md** once validated

## Contact

Data team owner for coach spot check table: **Mahrah Ashraf**

Status: COMING SOON
Last updated: April 2026

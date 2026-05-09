# Student Data & Results Product Analytics — ICT/Islamabad

> Source: `tbproddb.analytics_events` (partitioned on `sent_at`). Always filter `sent_at >= TIMESTAMP('...')`.
> For governed KPI rules: see `ai-assessment-rules.md` and `aser-enumerator-rules.md`.

## When These Rules Apply

User asks about student list **engagement**, student data **usage**, results viewing, FLN tracking, report cards, or class management.

**Always ask:** "What specific time period?" — never assume a duration.

---

## Three Product Features

| Feature | Events | Users | Purpose |
|---------|--------|-------|---------|
| **Student List Management** | 10 events | ~3.4K teachers | Manage student rosters per class |
| **Results & Report Cards** | 5 events | ~1.3K teachers | View assessment results and report cards |
| **FLN (Foundational Literacy & Numeracy)** | 3 events | ~918 teachers | Track student FLN categories and audio |

---

## 1. Student List Management — Event Catalog

| Event | Vol | Users | Key Props | Purpose |
|-------|-----|-------|-----------|---------|
| `studentDataLoadTime` | 2.7M | 4.9K | — | Student data loads (performance metric) |
| `studentListAccessed` | 67K | 3.4K | `ep_class_id` | Opens student list |
| `studentListProfileOpened` | 120K | 2.6K | — | Opens student profile |
| `studentListDuplicateAdmission` | 116K | 859 | — | Duplicate admission detected |
| `studentListMarkAsVerified` | 51K | 2.0K | — | Marks student as verified |
| `studentListEditInfo` | 47K | 2.0K | — | Edits student info |
| `studentListAddStudent` | 17K | 1.5K | — | Adds new student |
| `studentListDeleteStudent` | 9.1K | 1.2K | — | Deletes student |
| `studentsManageClassSelected` | 1.3K | 479 | — | Selects class to manage |
| `studentsManageClassTeacher` | 330 | 294 | — | Manages class teacher assignment |
| `studentsManageDeleteOther` | 180 | 22 | — | Deletes non-student record |

## 2. Results & Report Cards — Event Catalog

| Event | Vol | Users | Key Props | Purpose |
|-------|-----|-------|-----------|---------|
| `resultsClassSelected` | 10.6K | 1.3K | — | Selects class to view results |
| `resultsAssessmentSelected` | 7.8K | 1.1K | — | Selects assessment to view |
| `resultsStudentClicked` | 5.7K | 313 | — | Clicks on individual student result |
| `resultsQuestionTypeSelected` | 3.8K | 192 | — | Filters by question type |
| `resultsDashboardClicked` | 2.2K | 421 | — | Opens results dashboard |
| `reportCardPrintClicked` | 1.2K | 336 | — | Prints report card |
| `reportCardStudentClicked` | 62 | 3 | — | Clicks student in report card |
| `manualResultsStudentAdded` | 24 | 5 | — | Manually adds student result |

## 3. FLN (Foundational Literacy & Numeracy) — Event Catalog

| Event | Vol | Users | Purpose |
|-------|-----|-------|---------|
| `flnTabSelected` | 4.4K | 918 | Selects FLN tab |
| `flnAudioPlayed` | 3.6K | 156 | Plays FLN audio content |
| `flnDownloadClicked` | 3.1K | 883 | Downloads FLN content |
| `flnStudentCategoryChanged` | 438 | 25 | Changes student FLN category |
| `flnStudentAdded` | 107 | 11 | Adds student to FLN tracking |

---

## Metric Definitions

### Student List — Adoption & Usage

| Metric | Definition |
|--------|-----------|
| Student List Active Teachers | `COUNT(DISTINCT user_id)` where `name LIKE 'studentList%'` in period |
| Profile View Rate | `studentListProfileOpened` / `studentListAccessed` |
| Student Add Rate | Teachers with `studentListAddStudent` / Teachers with `studentListAccessed` |
| Verification Rate | `studentListMarkAsVerified` / `studentListAccessed` |

### Student List — Data Quality Signals

| Metric | Definition | Status |
|--------|-----------|--------|
| Duplicate Admission Rate | `studentListDuplicateAdmission` / `studentListAccessed` (116K/67K) | **Very high** — investigate |
| Delete Rate | `studentListDeleteStudent` / `studentListAddStudent` (9.1K/17K ≈ 53%) | High churn |

### Results — Funnel

| Step | Event | Conversion |
|------|-------|------------|
| 1 | `resultsDashboardClicked` or `resultsClassSelected` | top |
| 2 | `resultsAssessmentSelected` | ÷ ClassSelected |
| 3 | `resultsStudentClicked` | ÷ AssessmentSelected |

### FLN — Adoption

| Metric | Definition |
|--------|-----------|
| FLN Active Teachers | `COUNT(DISTINCT user_id)` where `name LIKE 'fln%'` in period |
| FLN Audio Engagement | Users with `flnAudioPlayed` / Users with `flnTabSelected` (156/918 ≈ 17%) |
| FLN Download Rate | Users with `flnDownloadClicked` / Users with `flnTabSelected` (883/918 ≈ 96%) |

### Retention

| Metric | Definition |
|--------|-----------|
| Student List MAU | `COUNT(DISTINCT user_id)` where `name LIKE 'studentList%'` per month |
| Results MAU | `COUNT(DISTINCT user_id)` where `name LIKE 'results%'` per month |
| FLN MAU | `COUNT(DISTINCT user_id)` where `name LIKE 'fln%'` per month |

---

## Properties Reference

| Property | Type | Events | Description |
|----------|------|--------|-------------|
| `$.ep_class_id` | INT | `studentListAccessed` | Class identifier |
| `$.is_offline` | BOOL | All | Offline mode |
| `$.device_type` | STRING | All | mobile / tablet / desktop |
| `$.session_id` | STRING | All | Session ID |

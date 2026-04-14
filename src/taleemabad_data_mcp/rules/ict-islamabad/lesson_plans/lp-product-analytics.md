# LP Product Analytics — ICT/Islamabad

> Source: `tbproddb.analytics_events` (partitioned on `sent_at`). Always filter `sent_at >= TIMESTAMP('...')`.
> For governed KPI rules (lp_ratio, status categories): see `lp-query-rules.md`.

## When These Rules Apply

User asks about LP **engagement**, **usage**, **retention**, **funnels**, **drop-off**, **video**, **downloads**, **errors**, or **offline usage**.

**Always ask:** "What specific time period?" — never assume a duration.

---

## Event Catalog (40 events, 7 groups)

### 1. Core LP Lifecycle (governed — see lp-query-rules.md)

| Event | Vol | Users | Purpose |
|-------|-----|-------|---------|
| `lessonLessonStarted` | 3.3M | 5.2K | Opens Core LP |
| `lessonLessonCompleted` | 2.4M | 5.0K | Finishes Core LP |
| `userGenLessonPlanGenerate` | 108K | 3.2K | Generates UGLP |
| `userGenLessonPlanComplete` | 106K | 2.9K | UGLP generation done |

### 2. In-Lesson Engagement

| Event | Vol | Users | Key Props | Purpose |
|-------|-----|-------|-----------|---------|
| `lessonLessonSection` | 15.1M | 4.8K | `ep_lp_section`, `ep_chapter_name`, `ep_is_download` | Section navigation (Introduction / Independent Practice / Conclusion / Homework) |
| `lessonBackClicked` | 149K | 4.1K | `ep_lp_id` | Back navigation (drop-off signal) |

### 3. Video

| Event | Vol | Users | Purpose |
|-------|-----|-------|---------|
| `lessonVideoImpression` | 103K | 3.2K | Video loads in view |
| `lessonVideoStarted` | 35K | 2.5K | Starts watching |
| `lessonVideoInProgress` | 205K | 2.6K | Playback heartbeat |
| `lessonVideoPause` | 48K | 2.1K | Pauses video |
| `lessonVideoCompleted` | 13K | 1.6K | Finishes video |
| `lessonVideoError` | 8K | 573 | Playback error |

### 4. Downloads

| Event | Vol | Users | Purpose |
|-------|-----|-------|---------|
| `lessonDownloadClicked` | 104K | 3.3K | Clicks download (intent) |
| `lessonDownload` | 511K | 3.8K | Download initiated |
| `lessonDownloadComplete` | 165K | 3.8K | Download succeeded |
| `lessonDownloadError` | 435 | 159 | Download failed |
| `lessonRetryDownload` | 10K | 978 | Retries failed download |
| `lessonDownloadDeleted` | 9K | 911 | Deletes downloaded LP |

### 5. Translation

| Event | Vol | Users | Purpose |
|-------|-----|-------|---------|
| `lessonTranslateClicked` | 62K | 2.5K | Clicks translate |
| `lessonTranslateError` | 786K | 473 | Translation error |

### 6. UGLP Funnel (full user journey)

| Event | Vol | Users | Key Props | Purpose |
|-------|-----|-------|-----------|---------|
| `userGenLessonPlanTabSelected` | 74K | 3.1K | — | Selects UGLP tab (top of funnel) |
| `userGenLessonPlanCardClick` | 168K | 3.1K | `ep_grade`, `ep_subject`, `ep_topic` | Clicks existing UGLP card |
| `userGenLessonPlanViewAll` | 52K | 3.0K | — | Views all UGLPs |
| `userGenLessonPlanGenerateNew` | 112K | 3.2K | — | Clicks generate new |
| `userGenLessonPlanGenerate` | 108K | 3.2K | `ep_lesson_plan_id`, `ep_grade`, `ep_subject` | Generation triggered |
| `userGenLessonPlanComplete` | 106K | 2.9K | `ep_lesson_plan_id` | Generation done |
| `userGenLessonPlanEdit` | 3K | 1.4K | — | Edits generated LP |
| `userGenLessonPlanSave` | 1K | 693 | — | Saves edited LP |
| `userGenLessonPlanRevisionSelected` | 31K | 1.2K | `ep_objective` | Selects LP revision |
| `userGenLessonPlanBackClick` | 15K | 2.0K | — | Back from UGLP view |
| `userGenLessonPlanWeeklyLimitReached` | 2K | 404 | — | Hits weekly limit |
| `userGenLessonPlanGenerationBackendError` | 1K | 414 | — | Backend generation error |

### 7. Fluid Lesson (experimental, ~40 users)

| Event | Vol | Users |
|-------|-----|-------|
| `fluidLessonStarted` | 1.9K | 41 |
| `fluidLessonSection` | 7.4K | 39 |
| `fluidLessonCompleted` | 1K | 35 |
| `fluidLessonBackClicked` | 61 | 19 |

### Legacy (ignore)

`lesson_lessonStarted` (28), `lesson_backClicked` (9), `lesson_videoPause` (3), `lesson_videoInProgress` (2), `lesson_videoImpression` (1) — pre-April 2024 underscore variants.

---

## Metric Definitions

### Adoption & Usage

| Metric | Definition |
|--------|-----------|
| LP Active Teachers (DAU/WAU/MAU) | `COUNT(DISTINCT user_id)` where `name IN ('lessonLessonStarted','userGenLessonPlanGenerate')` in period |
| Core LP Usage Rate | Core LP teachers / total active teachers |
| UGLP Adoption Rate | UGLP teachers / total active teachers |
| LP Type Mix | % Core vs % UGLP of total LP starts |

### Engagement Depth

| Metric | Definition |
|--------|-----------|
| Completion Rate (Core) | Distinct LPs completed / started (per `lp-query-rules.md`) |
| Completion Rate (UGLP) | `Complete` / `Generate` events per distinct LP ID |
| Sections per Lesson | `lessonLessonSection` count / `lessonLessonStarted` count, grouped by `ep_lp_id` |
| Video Watch Rate | Users with `VideoStarted` / Users with `LessonStarted` |
| Video Completion Rate | `VideoCompleted` / `VideoStarted` |
| Download Conversion | `DownloadComplete` / `DownloadClicked` |

### UGLP Funnel

| Step | Event | Conversion |
|------|-------|------------|
| 1 | `TabSelected` | top of funnel |
| 2 | `GenerateNew` | ÷ TabSelected |
| 3 | `Generate` | ÷ GenerateNew |
| 4 | `Complete` | ÷ Generate |
| 5 | `Edit` | ÷ Complete |
| 6 | `Save` | ÷ Edit |

### Retention

| Metric | Definition |
|--------|-----------|
| WoW Retention | Users in week N ∩ week N+1 |
| MAU | `COUNT(DISTINCT user_id)` per month |
| Churn | Active in M-1, absent in M |
| Power Users | >N LP starts per week |

### Reliability

| Metric | Current Rate | Status |
|--------|-------------|--------|
| Translation Error | 786K / 62K clicks | **Investigate** |
| Download Error | 435 / 511K (0.09%) | Healthy |
| UGLP Backend Error | 1.1K / 108K (~1%) | Monitor |
| Video Error | 8K / 35K (~23%) | **Investigate** |

### Offline & Downloaded Usage

- Offline: `JSON_VALUE(properties, '$.is_offline') = 'true'`
- Downloaded: `JSON_VALUE(properties, '$.ep_is_download') = 'true'`

---

## Properties Reference

| Property | Type | Events | Description |
|----------|------|--------|-------------|
| `$.ep_lp_id` | INT | All `lesson*` | Lesson plan ID |
| `$.ep_gradesubject_id` | INT | `lessonLessonSection`, `Started`, `Completed` | Grade-subject ID |
| `$.ep_lp_section` | STRING | `lessonLessonSection` | Section name |
| `$.ep_lp_type` | STRING | `lessonLessonSection` | LP type (e.g., ACTIVITY) |
| `$.ep_chapter_name` | STRING | `lessonLessonSection` | Chapter name |
| `$.ep_is_download` | BOOL | `lessonLessonSection` | Used from download |
| `$.is_offline` | BOOL | All | Offline mode |
| `$.ep_lesson_plan_id` | INT | `userGenLessonPlan*` | UGLP ID |
| `$.ep_grade` | STRING | `userGenLessonPlan*` | Grade |
| `$.ep_subject` | STRING | `userGenLessonPlan*` | Subject |
| `$.ep_topic` | STRING | `userGenLessonPlanCardClick` | Topic |
| `$.ep_objective` | BOOL | `RevisionSelected` | Objective flag |
| `$.device_type` | STRING | All | mobile / tablet / desktop |
| `$.is_native_app` | BOOL | All | Native app vs browser |
| `$.app_version` | STRING | All | App version |
| `$.session_id` | STRING | All | Session ID |

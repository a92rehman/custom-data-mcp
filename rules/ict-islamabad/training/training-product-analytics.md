# Training Product Analytics — ICT/Islamabad

> Source: `tbproddb.analytics_events` (partitioned on `sent_at`). Always filter `sent_at >= TIMESTAMP('...')`.
> For governed KPI rules (pass rates, level completion): see `training-query-rules.md`.

## When These Rules Apply

User asks about training **engagement**, **usage**, **retention**, **funnels**, **video watch behavior**, **quiz performance**, **exam generator**, **exam checker**, or **diagnostic tests**.

**Always ask:** "What specific time period?" — never assume a duration.

---

## Three Product Features in Training Domain

The training domain contains **93 events** across 3 distinct features:

| Feature | Events | Purpose |
|---------|--------|---------|
| **Training Courses** | 35 events | Video lessons, quizzes, level exams, diagnostics, certificates |
| **Exam Generator** | 28 events | Teachers create, edit, share, print student exams |
| **Exam Checker** | 16 events | Photograph & auto-grade student papers |

---

## 1. Training Courses — Event Catalog

### Navigation & Course Selection

| Event | Vol | Users | Key Props | Purpose |
|-------|-----|-------|-----------|---------|
| `trainingMenuSelected` | 13K | 2.5K | — | Opens training menu |
| `trainingCourseCategoryClicked` | 310K | 4.2K | — | Selects course category |
| `trainingCourseSelected` | 773K | 5.5K | `ep_course_id` | Selects a specific course |
| `trainingSubjectCourseClicked` | 119K | 3.2K | — | Selects subject-specific course |
| `trainingTrainingSelected` | 2.3M | 5.4K | `ep_course_id` | Selects a training module within course |
| `trainingLevelClicked` | 489K | 4.6K | — | Clicks on a training level |
| `trainingProgressBanner` | 148K | 4.3K | — | Views progress banner |

### Video Engagement

| Event | Vol | Users | Key Props | Purpose |
|-------|-----|-------|-----------|---------|
| `trainingVideoImpression` | 2.3M | 5.6K | `ep_course_id` | Video loads in view |
| `trainingVideoStarted` | 2.3M | 5.6K | `ep_course_id` | Starts watching |
| `trainingVideoInProgress` | 5.3M | 5.5K | `ep_course_id` | Playback heartbeat |
| `trainingVideoPause` | 3.5M | 5.0K | `ep_course_id` | Pauses video |
| `trainingVideoCompleted` | 1.9M | 5.2K | `ep_course_id` | Finishes video |
| `trainingVideoError` | 60K | 3.7K | `ep_course_id` | Playback error |

### Video Downloads

| Event | Vol | Users | Purpose |
|-------|-----|-------|---------|
| `trainingDownloadClicked` | 4.6K | 554 | Clicks download |
| `trainingDownloadStarted` | 4.7K | 532 | Download begins |
| `trainingDownloadComplete` | 8.9K | 686 | Download succeeds |
| `trainingDownloadError` | 1.3K | 194 | Download fails |
| `trainingRetryDownload` | 753 | 90 | Retry after failure |
| `trainingDownloadVideoPlayed` | 359 | 12 | Plays downloaded video |
| `trainingDownloadDeleted` | 86 | 35 | Deletes download |

### Quiz Lifecycle

| Event | Vol | Users | Key Props | Purpose |
|-------|-----|-------|-----------|---------|
| `trainingQuizStarted` | 2.0M | 5.1K | `ep_course_id` | Starts a quiz |
| `trainingQuizComplete` | 2.0M | 5.0K | `ep_course_id` | Finishes a quiz |
| `trainingQuizIncomplete` | 1.3M | 4.8K | `ep_course_id` | Leaves quiz without finishing |
| `trainingQuizPassed` | 485K | 3.9K | `ep_level_name` | Passes quiz |
| `trainingQuizFailed` | 713K | 3.9K | `ep_level_name` | Fails quiz |
| `trainingRetakePopup` | 751K | 4.4K | — | Sees retake prompt |
| `trainingRetakeQuiz` | 2.0K | 368 | — | Clicks retake |

### Level Exams & Progression (governed events — also in training-query-rules.md)

| Event | Vol | Users | Key Props | Purpose |
|-------|-----|-------|-----------|---------|
| `trainingStartExamClicked` | 39K | 3.9K | `ep_level` (INT) | Clicks to start level exam |
| `LevelExamIncomplete` | 274K | 3.8K | — | Leaves level exam incomplete |
| `trainingExamLevelPassed` | 12.5K | 3.7K | `ep_level_name` | **Passes level exam** (governed) |
| `trainingExamLevelFailed` | 4.2K | 1.9K | `ep_level_name` | Fails level exam |
| `levelUnlocked` | 12.5K | 3.7K | — | New level unlocked (mirrors ExamLevelPassed) |
| `trainingCertificateDownload` | 21K | 3.7K | `ep_level` (STRING, e.g., "Teacher Leader") | Downloads level certificate |

### Diagnostics

| Event | Vol | Users | Key Props | Purpose |
|-------|-----|-------|-----------|---------|
| `trainingDiagnosticStarted` | 30K | 3.7K | `ep_level` (INT) | Starts diagnostic test |
| `trainingDiagnosticIncomplete` | 13K | 2.7K | — | Leaves diagnostic incomplete |
| `trainingDiagnosticCompleted` | 10K | 3.6K | — | Completes diagnostic |

---

## 2. Exam Generator — Event Catalog

### Exam Creation Funnel

| Event | Vol | Users | Purpose |
|-------|-----|-------|---------|
| `examGeneratorCreateExam` | 123K | 4.3K | Opens exam creator |
| `examGeneratorAssessmentTypeSelected` | 146K | 4.1K | Selects assessment type |
| `examGeneratorClassSelected` | 137K | 4.1K | Selects class |
| `examGeneratorAssessmentSelected` | 121K | 4.0K | Selects specific assessment |
| `examGeneratorFlnTypeSelected` | 14K | 2.0K | Selects FLN type |
| `examGeneratorChaptersSelected` | 21K | 734 | Selects chapters |
| `examGeneratorGenerateExam` | 69K | 3.6K | Generates exam |
| `examGeneratorLoadQuestions` | 69K | 3.4K | Loads questions |
| `examGeneratorAddToExam` | 354K | 3.8K | Adds question to exam |
| `examGeneratorQualityCheck` | 5.2K | 660 | Runs quality check |
| `examGeneratorDone` | 30K | 2.7K | Finishes exam creation |

### Exam Management

| Event | Vol | Users | Purpose |
|-------|-----|-------|---------|
| `examGeneratorhistroyOpenAssessments` | 116K | 3.5K | Opens exam history |
| `examGeneratorhistoryExamEdit` | 48K | 3.1K | Edits existing exam |
| `examGeneratorEditExam` | 2.3K | 394 | Edits exam (older variant) |
| `examGeneratorEditChapter` | 20K | 2.8K | Edits chapter in exam |
| `examGeneratorSaveExam` | 3.0K | 480 | Saves exam |
| `examGeneratorDeleteExam` | 190 | 73 | Deletes exam |

### Exam Output & Sharing

| Event | Vol | Users | Purpose |
|-------|-----|-------|---------|
| `examGeneratorDownloadAndPrint` | 72K | 3.3K | Downloads and prints |
| `examGeneratorDownloadExam` | 1.1K | 188 | Downloads only |
| `examGeneratorPrintExam` | 122 | 15 | Prints only |
| `examGeneratorShareExam` | 8.1K | 2.0K | Shares exam |
| `examGeneratorShowAnswersAndMarkingScheme` | 40K | 2.5K | Views answers + marking |
| `examGeneratorShowAnswers` | 3.1K | 438 | Views answers only |
| `examGeneratorAddAnswerLines` | 36K | 2.6K | Adds answer lines |
| `examGeneratorAddAnswerSpacing` | 2.8K | 478 | Adjusts answer spacing |

### Exam Configuration (older flow, lower volume)

| Event | Vol | Users | Purpose |
|-------|-----|-------|---------|
| `examGeneratorGradeSelected` | 4.3K | 543 | Selects grade |
| `examGeneratorSubjectSelected` | 4.9K | 541 | Selects subject |
| `examGeneratorExamTypeSelected` | 3.9K | 553 | Selects exam type |
| `examGeneratorQuestionTypeClicked` | 269K | 3.3K | Selects question type |
| `examGeneratorAssessmentStructure` | 30K | 2.8K | Views structure |
| `examGeneratorTypeSelected` | 47 | 12 | Type selection (legacy) |

---

## 3. Exam Checker — Event Catalog

| Event | Vol | Users | Purpose |
|-------|-----|-------|---------|
| `examCheckerClassSelected` | 13K | 829 | Selects class |
| `examCheckerExamSelected` | 11K | 596 | Selects exam to check |
| `examCheckerAssessmentSelected` | 11K | 674 | Selects assessment |
| `examCheckerSelectStudent` | 11K | 321 | Selects student |
| `examCheckerAddStudent` | 2.3K | 240 | Adds student |
| `examCheckerDeleteStudent` | 466 | 87 | Deletes student |
| `examCheckerTakePicture` | 18K | 426 | Photographs answer sheet |
| `examCheckerUploadPicture` | 3.2K | 100 | Uploads photo |
| `examCheckerRetakePicture` | 1.1K | 178 | Retakes photo |
| `examCheckerImageClicked` | 9.3K | 422 | Views captured image |
| `examCheckerConfirmClicked` | 1.9K | 493 | Confirms submission |
| `examCheckerDeleteDialog` | 12K | 119 | Delete confirmation dialog |
| `examCheckerDeleteClicked` | 3.9K | 352 | Confirms delete |
| `examCheckerDeletePictureDialog` | 3.0K | 288 | Picture delete dialog |
| `examCheckerWalkthroughPopup` | 505 | 362 | Sees walkthrough/tutorial |
| `examCheckerStudentResultClicked` | 27 | 21 | Views student result |
| `examCheckerInstructionScreen` | 339 | 186 | Views instructions |

### UG Exam Generator (experimental, ~5 users)

| Event | Vol | Users | Purpose |
|-------|-----|-------|---------|
| `ugEgExamGenerated` | 16 | 5 | Generates UG exam |
| `ugEgExamEditClicked` | 68 | 5 | Edits UG exam |
| `ugEgExamCompleted` | 33 | 4 | Completes UG exam |

### Legacy (ignore)

`training_videoInProgress` (6K), `training_videoStarted` (4.5K), `training_videoPause` (2K), `training_videoImpression` (1.8K), `training_videoCompleted` (573), `training_videoError` (77), `createExamChapterSelect` (18K), `createExamLoadQuestions` (6.7K) — underscore/old variants, pre-2024.

---

## Metric Definitions

### Training Course — Adoption & Usage

| Metric | Definition |
|--------|-----------|
| Training Active Teachers (DAU/WAU/MAU) | `COUNT(DISTINCT user_id)` where `name LIKE 'training%'` in period |
| Course Engagement Rate | Teachers with `trainingTrainingSelected` / total active teachers |
| Video Completion Rate | `trainingVideoCompleted` / `trainingVideoStarted` |
| Quiz Completion Rate | `trainingQuizComplete` / `trainingQuizStarted` |
| Quiz Pass Rate | `trainingQuizPassed` / (`trainingQuizPassed` + `trainingQuizFailed`) |
| Quiz Incomplete Rate | `trainingQuizIncomplete` / `trainingQuizStarted` |

### Training Course — Level Progression Funnel

| Step | Event | Conversion |
|------|-------|------------|
| 1 | `trainingLevelClicked` | top of funnel |
| 2 | `trainingStartExamClicked` | ÷ LevelClicked |
| 3 | `trainingExamLevelPassed` + `trainingExamLevelFailed` | ÷ StartExamClicked |
| 4 | `trainingExamLevelPassed` | Pass rate = Passed / (Passed + Failed) |
| 5 | `trainingCertificateDownload` | ÷ ExamLevelPassed |

### Training Course — Diagnostic Funnel

| Step | Event | Conversion |
|------|-------|------------|
| 1 | `trainingDiagnosticStarted` | top |
| 2 | `trainingDiagnosticCompleted` | ÷ Started (completion rate = 10K / 30K ≈ 35%) |
| 3 | `trainingDiagnosticIncomplete` | drop-off = 13K / 30K ≈ 42% |

### Exam Generator — Funnel

| Step | Event | Conversion |
|------|-------|------------|
| 1 | `examGeneratorCreateExam` | top of funnel |
| 2 | `examGeneratorClassSelected` | ÷ CreateExam |
| 3 | `examGeneratorAssessmentSelected` | ÷ ClassSelected |
| 4 | `examGeneratorGenerateExam` | ÷ AssessmentSelected |
| 5 | `examGeneratorAddToExam` | question selection |
| 6 | `examGeneratorDone` | ÷ GenerateExam |
| 7 | `examGeneratorDownloadAndPrint` | ÷ Done |
| 8 | `examGeneratorShareExam` | share rate |

### Exam Checker — Funnel

| Step | Event | Conversion |
|------|-------|------------|
| 1 | `examCheckerClassSelected` | top |
| 2 | `examCheckerExamSelected` | ÷ ClassSelected |
| 3 | `examCheckerSelectStudent` | ÷ ExamSelected |
| 4 | `examCheckerTakePicture` | ÷ SelectStudent |
| 5 | `examCheckerConfirmClicked` | ÷ TakePicture |

### Retention

| Metric | Definition |
|--------|-----------|
| WoW Training Retention | Users with training events in week N ∩ week N+1 |
| MAU Training | `COUNT(DISTINCT user_id)` where `name LIKE 'training%'` per month |
| Exam Generator MAU | `COUNT(DISTINCT user_id)` where `name LIKE 'examGenerator%'` per month |
| Exam Checker MAU | `COUNT(DISTINCT user_id)` where `name LIKE 'examChecker%'` per month |

### Reliability

| Metric | Current Rate | Status |
|--------|-------------|--------|
| Video Error Rate | 60K / 2.3M (~2.6%) | Monitor |
| Download Error Rate | 1.3K / 4.7K (~27%) | **Investigate** |
| Quiz Fail Rate | 713K / (713K + 485K) (~60%) | High — may be by design |
| Diagnostic Incomplete Rate | 13K / 30K (~42%) | Monitor |
| Level Exam Incomplete | 274K / (274K + 12.5K + 4.2K) (~94%) | **Very high** — investigate |

---

## Properties Reference

| Property | Type | Events | Description |
|----------|------|--------|-------------|
| `$.ep_course_id` | INT | `training*` (navigation, video, quiz) | Course identifier |
| `$.ep_level_name` | STRING | `QuizPassed`, `QuizFailed`, `ExamLevelPassed`, `ExamLevelFailed`, `CertificateDownload` | Level name (e.g., "Teacher Leader") |
| `$.ep_level` | INT or STRING | `StartExamClicked` (INT), `DiagnosticStarted` (INT), `CertificateDownload` (STRING) | Level identifier — **type varies by event** |
| `$.ep_is_download` | BOOL | Video/quiz events | Whether played from download |
| `$.is_offline` | BOOL | All | Offline mode |
| `$.device_type` | STRING | All | mobile / tablet / desktop |
| `$.is_native_app` | BOOL | All | Native app vs browser |
| `$.app_version` | STRING | All | App version |
| `$.session_id` | STRING | All | Session ID |

# Platform & App Product Analytics — ICT/Islamabad

> Source: `tbproddb.analytics_events` (partitioned on `sent_at`). Always filter `sent_at >= TIMESTAMP('...')`.
> These are cross-cutting app-level events not owned by a single feature domain.

## When These Rules Apply

User asks about app-level **engagement**, **signup/onboarding**, **navigation**, **data sync**, **push notifications**, **community**, **errors**, or **platform health**.

**Always ask:** "What specific time period?" — never assume a duration.

---

## Six Product Areas

| Area | Events | Purpose |
|------|--------|---------|
| **Signup & Auth** | 12 events | Registration, login, password reset |
| **Navigation & Dashboard** | 10 events | Menu, class selection, timetable |
| **Data Sync & Offline** | 6 events | Sync success/failure, offline detection |
| **Push Notifications** | 7 events | Permission, delivery, engagement |
| **Community** | 7 events | Posts, comments, likes, notifications |
| **Errors & Reliability** | 5 events | Backend errors, data loading failures, UI errors |

---

## 1. Signup & Auth

| Event | Vol | Users | Purpose |
|-------|-----|-------|---------|
| `signupStarted` | 98K | 8.1K | Begins signup flow |
| `signupPhoneNumberEntered` | 381K | 8.2K | Enters phone number |
| `signupLogin` | 214K | 6.3K | Logs in |
| `signupLoginError` | 14K | 2.6K | Login failure |
| `signupPasswordComplete` | 7.1K | 6.1K | Sets password |
| `signupPasswordError` | 6.9K | 1.8K | Password validation error |
| `signupCompleted` | 3.8K | 3.2K | Finishes signup |
| `signupUserDetails` | 3.8K | 3.2K | Submits user details |
| `accountCreated` | 3.4K | 264 | Account created (server-side) |
| `regionSelected` | 22K | 5.8K | Selects region |
| `resetPasswordForgetPasswordClicked` | 38K | 4.9K | Clicks forgot password |
| `resetPasswordAccountVerificationNextClicked` | 35K | 4.8K | Verification step |
| `resetPasswordOTPVerified` | 26K | 4.6K | OTP verified |
| `resetPasswordChoosePasswordNextClicked` | 30K | 4.6K | Sets new password |
| `resetPasswordResendOTPClicked` | 7.3K | 1.7K | Resends OTP |

## 2. Navigation & Dashboard

| Event | Vol | Users | Purpose |
|-------|-----|-------|---------|
| `menuBarSelected` | 2.1M | 7.4K | Taps menu bar item |
| `dashboardClassSelected` | 1.7M | 5.1K | Selects class on dashboard |
| `dashboardAddClassClicked` | 228K | 6.4K | Clicks add class |
| `dashboardShiftSelected` | 166K | 5.5K | Selects shift |
| `dashboardGradeSelected` | 164K | 5.6K | Selects grade |
| `dashboardSectionSelected` | 162K | 5.5K | Selects section |
| `dashboardSubjectSelected` | 155K | 5.4K | Selects subject |
| `dashboardDaySelected` | 84K | 4.5K | Selects day |
| `profileSelected` | 1.3M | 4.5K | Opens profile |
| `profileEditClicked` | 9.1K | 3.0K | Edits profile |
| `profileScreenLogout` | 31K | 4.5K | Logs out |
| `profileSwitched` | 1.3K | 168 | Switches profile |
| `schoolProfileClicked` | 1.0K | 539 | Views school profile |
| `timetableEditClassClicked` | 83K | 4.5K | Edits class timetable |
| `timetableDeleteClass` | 41K | 3.9K | Deletes class |
| `timetableEditDaysSaved` | 18K | 3.1K | Saves timetable edits |
| `notificationIconClicked` | 42K | 3.9K | Opens notifications |
| `notificationCardClicked` | 11K | 2.7K | Clicks notification card |
| `helpClicked` | 2.2K | 917 | Opens help |
| `chatWidgetClicked` | 94K | 3.8K | Opens chat widget |
| `changeRegionClicked` | 9.8K | 2.6K | Changes region |

## 3. Data Sync & Offline

| Event | Vol | Users | Purpose |
|-------|-----|-------|---------|
| `dataSyncSuccessful` | 3.6M | 6.6K | Sync completed successfully |
| `syncDataSyncDataFailedError` | 650K | 6.5K | Sync failed |
| `recordsFailedToSync` | 8.9K | 2.2K | Individual records failed |
| `pushSyncPartialFailure` | 876 | 330 | Partial sync failure |
| `retryDataRetryDataClicked` | 39K | 3.5K | User retries data load |
| `refreshDataRefreshDataClicked` | 1.4K | 540 | Manual refresh |

## 4. Push Notifications

| Event | Vol | Users | Purpose |
|-------|-----|-------|---------|
| `pushNotificationAllowed` | 19K | 4.0K | Allows push notifications |
| `pushNotificationAllowedAndroid` | 16K | 3.7K | Android-specific allow |
| `pushNotificationDismissed` | 24K | 1.4K | Dismisses notification prompt |
| `pushNotificationDismissedAndroid` | 3.5K | 912 | Android-specific dismiss |
| `pushNotificationClicked` | 6.7K | 1.8K | Clicks push notification |
| `pushNotificationPopupReceived` | 1.6K | 726 | Receives notification popup |
| `parentInvitePrompt` | 4.3K | 1.9K | Sees parent invite prompt |
| `inviteCancelled` | 1.1K | 168 | Cancels invite |

## 5. Community

| Event | Vol | Users | Purpose |
|-------|-----|-------|---------|
| `communitySelectedPostTab` | 38K | 2.8K | Selects community post tab |
| `communityNewPost` | 5.6K | 781 | Creates new post (`has_media`, `has_poll`, `has_content`) |
| `communityNewComment` | 1.4K | 277 | Comments on a post |
| `communityToggleLike` | 14K | 883 | Likes/unlikes a post |
| `communityLoadMorePosts` | 5.4K | 896 | Scrolls for more posts |
| `communityNotificationIconClicked` | 3.2K | 284 | Opens community notifications |
| `communityNotificationClicked` | 1.2K | 102 | Clicks community notification |

## 6. Errors & Reliability

| Event | Vol | Users | Purpose |
|-------|-----|-------|---------|
| `dataLoadingDataLoadingFailed` | 1.1M | 4.5K | Data loading failure |
| `systemBackendError` | 886K | 5.2K | Backend error |
| `noInternetNoInternetPopup` | 860K | 4.0K | No internet detected |
| `UIError` | 16K | 3.0K | UI rendering error |
| `chapterDownload` | 66K | 1.8K | Chapter download initiated |
| `chapterRetryDownload` | 6.3K | 686 | Chapter download retry |

---

## Metric Definitions

### Signup Funnel

| Step | Event | Conversion |
|------|-------|------------|
| 1 | `signupStarted` | top (98K) |
| 2 | `signupPhoneNumberEntered` | ÷ Started |
| 3 | `signupPasswordComplete` | ÷ PhoneEntered |
| 4 | `signupCompleted` | ÷ PasswordComplete (3.8K / 98K ≈ 3.9% overall) |

### App Health

| Metric | Definition | Current | Status |
|--------|-----------|---------|--------|
| Sync Success Rate | `dataSyncSuccessful` / (`Successful` + `FailedError`) | 3.6M / 4.3M ≈ 85% | **15% failure rate** — monitor |
| Data Load Failure Rate | `dataLoadingFailed` / total sessions | 1.1M events, 4.5K users | High volume — investigate |
| Backend Error Rate | `systemBackendError` / total sessions | 886K events, 5.2K users | High volume — investigate |
| No Internet Rate | `noInternetPopup` / total sessions | 860K, 4K users | Infrastructure/connectivity |

### Push Notification Effectiveness

| Metric | Definition |
|--------|-----------|
| Opt-in Rate | `Allowed` / (`Allowed` + `Dismissed`) (19K / 43K ≈ 44%) |
| Click-through Rate | `Clicked` / `PopupReceived` (6.7K / 1.6K) |

### Community Engagement

| Metric | Definition |
|--------|-----------|
| Community MAU | `COUNT(DISTINCT user_id)` where `name LIKE 'community%'` per month |
| Post Rate | `communityNewPost` / `communitySelectedPostTab` (5.6K / 38K ≈ 15%) |
| Like Rate | `communityToggleLike` / `communitySelectedPostTab` (14K / 38K ≈ 37%) |
| Comment Rate | `communityNewComment` / `communitySelectedPostTab` (1.4K / 38K ≈ 4%) |

### Retention (Platform-level)

| Metric | Definition |
|--------|-----------|
| DAU | `COUNT(DISTINCT user_id)` per day from any event |
| WAU | `COUNT(DISTINCT user_id)` per week |
| MAU | `COUNT(DISTINCT user_id)` per month |
| DAU/MAU Ratio | Stickiness metric |
| Session Count per User | `COUNT(DISTINCT session_id)` / `COUNT(DISTINCT user_id)` |

---

## Properties Reference

| Property | Type | Events | Description |
|----------|------|--------|-------------|
| `$.has_media` | BOOL | `communityNewPost` | Post contains media |
| `$.has_poll` | BOOL | `communityNewPost` | Post contains a poll |
| `$.has_content` | BOOL | `communityNewPost` | Post has text content |
| `$.ep_class_id` | INT | Dashboard events | Class identifier |
| `$.is_offline` | BOOL | All | Offline mode |
| `$.device_type` | STRING | All | mobile / tablet / desktop |
| `$.is_native_app` | BOOL | All | Native app vs browser |
| `$.app_version` | STRING | All | App version |
| `$.session_id` | STRING | All | Session ID |

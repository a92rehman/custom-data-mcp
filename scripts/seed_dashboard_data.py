"""Seed dummy data for the observability dashboard."""

import os
import random
import uuid
from datetime import UTC, datetime, timedelta

from google.cloud import bigquery

# Load credentials
env_file = os.path.expanduser("~/.claude/taleemabad-data-mcp.env")
env_vars = {}
with open(env_file) as f:
    for line in f:
        if "=" in line:
            k, v = line.strip().split("=", 1)
            env_vars[k] = v

client = bigquery.Client.from_service_account_json(
    env_vars["GOOGLE_APPLICATION_CREDENTIALS"],
    project="niete-bq-prod",
)

# 1. Add domain column
print("Adding domain column...")
sql = "ALTER TABLE `niete-bq-prod.mcp_audit.activity_log` ADD COLUMN IF NOT EXISTS domain STRING"
client.query(sql).result()
print("Domain column added.")

# 2. Create feedback table
print("Creating feedback table...")
schema = [
    bigquery.SchemaField("feedback_id", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("event_id", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("user_name", "STRING"),
    bigquery.SchemaField("rating", "STRING"),
    bigquery.SchemaField("comment", "STRING"),
    bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
]
table = bigquery.Table("niete-bq-prod.mcp_audit.query_feedback", schema=schema)
table.time_partitioning = bigquery.TimePartitioning(
    type_=bigquery.TimePartitioningType.DAY,
    field="timestamp",
)
client.create_table(table, exists_ok=True)
print("Feedback table ready.")

# 3. Insert dummy activity data
print("Inserting dummy activity data...")

users = ["demo-Sarah", "demo-Ahmed", "demo-Fatima", "demo-Bilal", "demo-Ayesha"]
domains = ["teachers", "lesson_plans", "observations", "training", "other"]

questions = {
    "teachers": [
        "How many active PRIMARY teachers are in ICT?",
        "Show me teacher count by school in Islamabad",
        "Which schools have no active teachers assigned?",
        "How many teachers have multiple profiles?",
        "List teachers who joined this month",
    ],
    "lesson_plans": [
        "What is the LP adoption rate this week for ICT?",
        "Show me On-Schedule vs Off-Schedule teachers",
        "Which subjects have the lowest LP completion?",
        "LP trend for the last 4 weeks in session 2025-26",
        "How many User Generated LPs were completed?",
    ],
    "observations": [
        "What is the average FICO Section B score?",
        "Show observation scores by school",
        "Which coaches did the most observations this month?",
        "Section C trends over the last 3 months",
        "Compare principal vs coach observation scores",
    ],
    "training": [
        "How many teachers passed Level 1 training?",
        "Show pass rates by training level",
        "Which level has the lowest pass rate?",
        "Average attempts to pass Level 2",
        "Teachers who completed all training levels",
    ],
    "other": [
        "List all datasets available",
        "What tables are in tbproddb?",
        "Check freshness of events_partitioned",
        "Show schema for user_school_profiles",
        "How many tables in RUMI_DB?",
    ],
}

tables_by_domain = {
    "teachers": ["users_teacherprofile", "user_school_profiles", "FDE_Schools"],
    "lesson_plans": ["events_partitioned", "lp_info_all_types", "schools_schoolclasstimetable"],
    "observations": ["coaching_observation", "coaching_observationanswer", "coaching_teachervisit"],
    "training": ["teacher_training_level", "teacher_training_assessment"],
    "other": [],
}

rows = []
now = datetime.now(UTC)

for day_offset in range(30, 0, -1):
    day = now - timedelta(days=day_offset)
    num_queries = random.randint(3, 12)
    for _ in range(num_queries):
        domain = random.choice(domains)
        user = random.choice(users)
        question = random.choice(questions[domain])
        has_error = random.random() < 0.08
        is_dry_run = random.random() < 0.15

        ts = day + timedelta(hours=random.randint(8, 18), minutes=random.randint(0, 59))

        tbls = tables_by_domain[domain]
        row = {
            "event_id": str(uuid.uuid4()),
            "timestamp": ts.isoformat(),
            "user_name": user,
            "hostname": "demo-machine",
            "query_text": question,
            "generated_sql": f"SELECT ... FROM {random.choice(tbls) if tbls else 'tbproddb'}",
            "tables_accessed": tbls,
            "domain": domain,
            "result_cached": False,
        }

        if has_error:
            row["error_type"] = random.choice(["BadRequest", "Forbidden", "NotFound"])
            row["error_message"] = "Demo error for dashboard testing"
        elif is_dry_run:
            row["error_type"] = "dry_run"
            row["cost_bytes"] = random.randint(1_000_000, 500_000_000)
            row["cost_usd"] = row["cost_bytes"] / 1_099_511_627_776 * 6.25
        else:
            row["rows_returned"] = random.randint(1, 500)
            row["execution_ms"] = random.randint(200, 8000)
            row["cost_bytes"] = random.randint(1_000_000, 200_000_000)
            row["cost_usd"] = row["cost_bytes"] / 1_099_511_627_776 * 6.25

        rows.append(row)

# Insert in batches
table_id = "niete-bq-prod.mcp_audit.activity_log"
for i in range(0, len(rows), 50):
    batch = rows[i : i + 50]
    errors = client.insert_rows_json(table_id, batch)
    if errors:
        print(f"Batch {i}: errors={errors[:2]}")
    else:
        print(f"Batch {i}-{i + len(batch)}: OK")

print(f"Inserted {len(rows)} dummy activity rows.")

# 4. Insert dummy feedback data
print("Inserting dummy feedback...")
feedback_rows = []
feedback_events = random.sample(rows, min(80, len(rows)))

for r in feedback_events:
    if r.get("error_type") and r["error_type"] != "dry_run":
        continue
    rating = random.choices(["up", "down"], weights=[75, 25])[0]
    comment = None
    if random.random() < 0.3:
        if rating == "up":
            comment = random.choice([
                "Exactly what I needed",
                "Numbers match our internal report",
                "Great, this is correct",
                "Perfect answer",
            ])
        else:
            comment = random.choice([
                "Expected higher numbers",
                "This does not match the Google Sheet",
                "Wrong time period",
                "Missing some schools",
            ])

    fb_ts = datetime.fromisoformat(r["timestamp"]) + timedelta(minutes=random.randint(1, 5))
    feedback_rows.append({
        "feedback_id": str(uuid.uuid4()),
        "event_id": r["event_id"],
        "user_name": r["user_name"],
        "rating": rating,
        "comment": comment,
        "timestamp": fb_ts.isoformat(),
    })

fb_table = "niete-bq-prod.mcp_audit.query_feedback"
for i in range(0, len(feedback_rows), 50):
    batch = feedback_rows[i : i + 50]
    errors = client.insert_rows_json(fb_table, batch)
    if errors:
        print(f"Feedback batch {i}: errors={errors[:2]}")
    else:
        print(f"Feedback batch {i}-{i + len(batch)}: OK")

print(f"Inserted {len(feedback_rows)} dummy feedback rows.")
print("Done! Launch the dashboard now.")

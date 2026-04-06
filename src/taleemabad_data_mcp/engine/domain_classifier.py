"""Classify audit entries by data domain based on tables accessed or SQL text."""

_DOMAIN_KEYWORDS: list[tuple[str, list[str]]] = [
    ("observations", [
        "coaching_observation",
        "coaching_teachervisit",
        "coaching_observationanswer",
        "coaching_observationquestion",
        "coaching_questionoption",
        "coaching_observationquestiongroup",
        "coaching_observationsection",
        "coaching_observationtemplate",
    ]),
    ("training", [
        "teacher_training_level",
        "teacher_training_assessment",
    ]),
    ("lesson_plans", [
        "lp_info_all_types",
        "schoolclasstimetable",
        "schools_schoolclasssubject",
        "schools_schoolclass",
    ]),
    ("teachers", [
        "users_teacherprofile",
        "user_school_profiles",
        "teacher_profiles",
        "users_coachprofile",
        "users_principalprofile",
    ]),
]


def classify_domain(tables_accessed: list[str], sql: str = "") -> str:
    """Classify which data domain a query belongs to.

    Primary: matches table names from BigQuery job metadata.
    Fallback: keyword-matches against the SQL string when tables_accessed is empty.

    Args:
        tables_accessed: List of table IDs from BigQuery referenced_tables.
        sql: Raw SQL string, used as fallback when tables_accessed is empty.

    Returns:
        One of: "observations", "lesson_plans", "training", "teachers", "other".
    """
    search_text = " ".join(tables_accessed).lower()

    if not search_text and sql:
        search_text = sql.lower()

    if not search_text:
        return "other"

    for domain, keywords in _DOMAIN_KEYWORDS:
        if any(kw in search_text for kw in keywords):
            return domain

    return "other"

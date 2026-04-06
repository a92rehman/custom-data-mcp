"""Tests for domain classification."""

from taleemabad_data_mcp.engine.domain_classifier import classify_domain


def test_observations_domain():
    assert classify_domain(["coaching_observation", "coaching_teachervisit"]) == "observations"


def test_observations_single_table():
    assert classify_domain(["coaching_observationanswer"]) == "observations"


def test_lesson_plans_domain():
    assert classify_domain(["events_partitioned", "lp_info_all_types"]) == "lesson_plans"


def test_lesson_plans_timetable():
    assert classify_domain(["schoolclasstimetable", "schools_schoolclass"]) == "lesson_plans"


def test_training_domain():
    assert classify_domain(["teacher_training_level", "user_school_profiles"]) == "training"


def test_training_assessment():
    assert classify_domain(["teacher_training_assessment"]) == "training"


def test_teachers_domain():
    assert classify_domain(["users_teacherprofile", "schools_school"]) == "teachers"


def test_teachers_user_school_profiles_only():
    assert classify_domain(["user_school_profiles"]) == "teachers"


def test_other_domain():
    assert classify_domain(["some_random_table"]) == "other"


def test_empty_tables():
    assert classify_domain([]) == "other"


def test_sql_fallback_observations():
    assert classify_domain([], sql="SELECT * FROM coaching_observation WHERE ...") == "observations"


def test_sql_fallback_lesson_plans():
    assert classify_domain([], sql="SELECT * FROM lp_info_all_types") == "lesson_plans"


def test_sql_fallback_training():
    assert classify_domain([], sql="SELECT * FROM teacher_training_level") == "training"


def test_sql_fallback_teachers():
    assert classify_domain([], sql="SELECT * FROM users_teacherprofile") == "teachers"


def test_sql_fallback_empty():
    assert classify_domain([], sql="") == "other"

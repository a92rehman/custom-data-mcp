"""Tests for the governance_mapper module."""

import pytest
from custom_data_mcp.engine.governance_mapper import (
    extract_tables_from_text,
    get_governance_map,
)


# ---------------------------------------------------------------------------
# extract_tables_from_text
# ---------------------------------------------------------------------------


class TestExtractTablesFromText:
    def test_markdown_table_backtick_format(self):
        """Parses dataset.table from a markdown table cell with backticks."""
        text = "| `tbproddb.coaching_observation` | Core record — date, boys/girls count |"
        result = extract_tables_from_text(text)
        assert ("tbproddb", "coaching_observation") in result

    def test_sql_from_clause(self):
        """Parses dataset.table from a plain SQL FROM clause."""
        text = "FROM tbproddb.coaching_observation co"
        result = extract_tables_from_text(text)
        assert ("tbproddb", "coaching_observation") in result

    def test_sql_join_clause(self):
        """Parses dataset.table from a SQL JOIN clause."""
        text = "JOIN tbproddb.coaching_teachervisit tv ON co.id = tv.observation_id"
        result = extract_tables_from_text(text)
        assert ("tbproddb", "coaching_teachervisit") in result

    def test_taleem_hub_table(self):
        """Parses TaleemHub_DB tables (mixed-case dataset)."""
        text = "FROM TaleemHub_DB.mentoring_visits mv"
        result = extract_tables_from_text(text)
        assert ("TaleemHub_DB", "mentoring_visits") in result

    def test_rumi_db_table(self):
        """Parses RUMI_DB tables."""
        text = "FROM RUMI_DB.lesson_plans lp"
        result = extract_tables_from_text(text)
        assert ("RUMI_DB", "lesson_plans") in result

    def test_odk_table_with_hyphens(self):
        """Parses ODK table names that contain hyphens."""
        text = "| `odk.NIETE_-_ICT_-_IMPACT_ICT-ENDLINE-ASER_1-3_Test` | Grades 1-3 ASER endline |"
        result = extract_tables_from_text(text)
        assert ("odk", "NIETE_-_ICT_-_IMPACT_ICT-ENDLINE-ASER_1-3_Test") in result

    def test_odk_table_no_backticks(self):
        """Parses ODK tables referenced without backticks."""
        text = "FROM odk.NIETE_-_ICT_-_IMPACT_RWP-ENDLINE-ASER_1-3_feb"
        result = extract_tables_from_text(text)
        assert ("odk", "NIETE_-_ICT_-_IMPACT_RWP-ENDLINE-ASER_1-3_feb") in result

    def test_multiple_tables_in_text(self):
        """Extracts multiple distinct table references from the same text."""
        text = """
        FROM tbproddb.coaching_observation co
        JOIN tbproddb.coaching_teachervisit tv ON co.id = tv.observation_id
        JOIN RUMI_DB.lesson_plans lp ON lp.id = tv.lp_id
        """
        result = extract_tables_from_text(text)
        assert ("tbproddb", "coaching_observation") in result
        assert ("tbproddb", "coaching_teachervisit") in result
        assert ("RUMI_DB", "lesson_plans") in result

    def test_returns_empty_for_column_names_only(self):
        """Does NOT match single-word backtick items like column names."""
        text = (
            "Filter: `is_active = 'true'`. The `source` column emits `'B'`, `'C'`, `'D'`. "
            "Use `REGEXP_EXTRACT`. See `coach_profile_id`."
        )
        result = extract_tables_from_text(text)
        assert result == set(), f"Expected empty set, got: {result}"

    def test_returns_empty_for_plain_text(self):
        """Returns empty set when there are no dataset.table references."""
        text = "This is a plain description with no table references."
        result = extract_tables_from_text(text)
        assert result == set()

    def test_deduplicates_same_table_mentioned_multiple_times(self):
        """The same table referenced twice appears only once in the result."""
        text = (
            "FROM tbproddb.coaching_observation co\n"
            "-- also see tbproddb.coaching_observation for details"
        )
        result = extract_tables_from_text(text)
        # It's a set, so duplicates are automatically collapsed
        assert result.count(("tbproddb", "coaching_observation")) == 1 if hasattr(result, "count") else True
        assert len([t for t in result if t == ("tbproddb", "coaching_observation")]) == 1

    def test_unknown_dataset_not_extracted(self):
        """References to datasets not in KNOWN_DATASETS are not returned."""
        text = "FROM unknown_db.some_table t"
        result = extract_tables_from_text(text)
        assert ("unknown_db", "some_table") not in result

    def test_returns_set_of_tuples(self):
        """Return type is set of (dataset, table) tuples."""
        text = "FROM tbproddb.coaching_observation"
        result = extract_tables_from_text(text)
        assert isinstance(result, set)
        for item in result:
            assert isinstance(item, tuple)
            assert len(item) == 2


# ---------------------------------------------------------------------------
# get_governance_map
# ---------------------------------------------------------------------------


class TestGetGovernanceMap:
    def test_returns_dict(self):
        """get_governance_map returns a dict."""
        result = get_governance_map()
        assert isinstance(result, dict)

    def test_coaching_observation_is_governed(self):
        """coaching_observation is a known governed table from observation rules."""
        result = get_governance_map()
        assert ("tbproddb", "coaching_observation") in result

    def test_mentoring_visits_is_governed(self):
        """mentoring_visits is governed under RWP coaching rules."""
        result = get_governance_map()
        assert ("TaleemHub_DB", "mentoring_visits") in result

    def test_lesson_plans_rumi_is_governed(self):
        """RUMI_DB.lesson_plans is governed under RWP LP rules."""
        result = get_governance_map()
        assert ("RUMI_DB", "lesson_plans") in result

    def test_aser_odk_table_is_governed(self):
        """ODK ASER table is governed under ICT student results rules."""
        result = get_governance_map()
        assert ("odk", "NIETE_-_ICT_-_IMPACT_ICT-ENDLINE-ASER_1-3_Test") in result

    def test_each_entry_has_required_keys(self):
        """Each governance entry has at minimum 'domain', 'region', and 'rule_files' keys."""
        result = get_governance_map()
        for key, value in result.items():
            assert "domain" in value, f"Missing 'domain' for {key}"
            assert "region" in value, f"Missing 'region' for {key}"
            assert "rule_files" in value, f"Missing 'rule_files' for {key}"

    def test_rule_files_is_list_of_strings(self):
        """rule_files for each entry is a list of strings (file paths)."""
        result = get_governance_map()
        for key, value in result.items():
            assert isinstance(value["rule_files"], list), f"rule_files not a list for {key}"
            for f in value["rule_files"]:
                assert isinstance(f, str), f"rule_files entry not a string for {key}"

    def test_ict_region_inferred(self):
        """coaching_observation should have region 'ict-islamabad'."""
        result = get_governance_map()
        entry = result.get(("tbproddb", "coaching_observation"))
        assert entry is not None
        assert entry["region"] == "ict-islamabad"

    def test_rawalpindi_region_inferred(self):
        """mentoring_visits should have region 'rawalpindi'."""
        result = get_governance_map()
        entry = result.get(("TaleemHub_DB", "mentoring_visits"))
        assert entry is not None
        assert entry["region"] == "rawalpindi"

    def test_coaching_domain_inferred(self):
        """coaching_observation should map to a coaching-related domain."""
        result = get_governance_map()
        entry = result.get(("tbproddb", "coaching_observation"))
        assert entry is not None
        assert "coaching" in entry["domain"]

    def test_training_domain_inferred(self):
        """teacher_training_level should map to 'training' domain."""
        result = get_governance_map()
        entry = result.get(("tbproddb", "teacher_training_level"))
        assert entry is not None
        assert entry["domain"] == "training"

    def test_lesson_plan_domain_inferred(self):
        """lp_info_all_types should map to 'lesson_plans' domain."""
        result = get_governance_map()
        entry = result.get(("tbproddb", "lp_info_all_types"))
        assert entry is not None
        assert entry["domain"] == "lesson_plans"

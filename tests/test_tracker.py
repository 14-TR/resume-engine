"""Tests for the application tracker module."""

from __future__ import annotations

import pytest

from resume_engine.tracker import (
    VALID_STATUSES,
    add_application,
    delete_application,
    get_application,
    get_stats,
    list_applications,
    update_application,
)


@pytest.fixture
def tmp_db(tmp_path):
    """Return a path to an isolated temp database for each test."""
    return tmp_path / "test_tracker.db"


class TestAddApplication:
    def test_basic_add(self, tmp_db):
        app_id = add_application("Acme", "Engineer", db_path=tmp_db)
        assert isinstance(app_id, int)
        assert app_id >= 1

    def test_add_returns_auto_increment(self, tmp_db):
        id1 = add_application("Co A", "Role A", db_path=tmp_db)
        id2 = add_application("Co B", "Role B", db_path=tmp_db)
        assert id2 > id1

    def test_add_invalid_status(self, tmp_db):
        with pytest.raises(ValueError, match="Invalid status"):
            add_application("Co", "Role", status="banana", db_path=tmp_db)

    def test_add_all_fields(self, tmp_db):
        app_id = add_application(
            "BigCo",
            "Senior Dev",
            applied_date="2026-01-15",
            status="screening",
            url="https://example.com/job",
            notes="Referral from friend",
            db_path=tmp_db,
        )
        row = get_application(app_id, db_path=tmp_db)
        assert row is not None
        assert row["company"] == "BigCo"
        assert row["role"] == "Senior Dev"
        assert row["date"] == "2026-01-15"
        assert row["status"] == "screening"
        assert row["url"] == "https://example.com/job"
        assert row["notes"] == "Referral from friend"


class TestListApplications:
    def test_list_empty(self, tmp_db):
        rows = list_applications(db_path=tmp_db)
        assert rows == []

    def test_list_returns_all(self, tmp_db):
        add_application("A", "Engineer", db_path=tmp_db)
        add_application("B", "Manager", db_path=tmp_db)
        rows = list_applications(db_path=tmp_db)
        assert len(rows) == 2

    def test_list_filter_status(self, tmp_db):
        add_application("A", "Eng", status="applied", db_path=tmp_db)
        add_application("B", "Mgr", status="rejected", db_path=tmp_db)
        rows = list_applications(status="applied", db_path=tmp_db)
        assert len(rows) == 1
        assert rows[0]["company"] == "A"

    def test_list_filter_company(self, tmp_db):
        add_application("Acme Corp", "Dev", db_path=tmp_db)
        add_application("Startup X", "Eng", db_path=tmp_db)
        rows = list_applications(company="acme", db_path=tmp_db)
        assert len(rows) == 1
        assert rows[0]["company"] == "Acme Corp"

    def test_list_limit(self, tmp_db):
        for i in range(5):
            add_application(f"Co{i}", "Role", db_path=tmp_db)
        rows = list_applications(limit=3, db_path=tmp_db)
        assert len(rows) == 3


class TestGetApplication:
    def test_get_existing(self, tmp_db):
        app_id = add_application("TestCo", "Dev", db_path=tmp_db)
        row = get_application(app_id, db_path=tmp_db)
        assert row is not None
        assert row["id"] == app_id
        assert row["company"] == "TestCo"

    def test_get_missing(self, tmp_db):
        row = get_application(9999, db_path=tmp_db)
        assert row is None


class TestUpdateApplication:
    def test_update_status(self, tmp_db):
        app_id = add_application("Co", "Role", db_path=tmp_db)
        ok = update_application(app_id, status="interview", db_path=tmp_db)
        assert ok is True
        row = get_application(app_id, db_path=tmp_db)
        assert row["status"] == "interview"

    def test_update_notes(self, tmp_db):
        app_id = add_application("Co", "Role", db_path=tmp_db)
        update_application(app_id, notes="Had phone screen", db_path=tmp_db)
        row = get_application(app_id, db_path=tmp_db)
        assert row["notes"] == "Had phone screen"

    def test_update_url(self, tmp_db):
        app_id = add_application("Co", "Role", db_path=tmp_db)
        update_application(app_id, url="https://example.com", db_path=tmp_db)
        row = get_application(app_id, db_path=tmp_db)
        assert row["url"] == "https://example.com"

    def test_update_invalid_status(self, tmp_db):
        app_id = add_application("Co", "Role", db_path=tmp_db)
        with pytest.raises(ValueError):
            update_application(app_id, status="banana", db_path=tmp_db)

    def test_update_missing_id(self, tmp_db):
        ok = update_application(9999, status="rejected", db_path=tmp_db)
        assert ok is False


class TestDeleteApplication:
    def test_delete_existing(self, tmp_db):
        app_id = add_application("Co", "Role", db_path=tmp_db)
        ok = delete_application(app_id, db_path=tmp_db)
        assert ok is True
        assert get_application(app_id, db_path=tmp_db) is None

    def test_delete_missing(self, tmp_db):
        ok = delete_application(9999, db_path=tmp_db)
        assert ok is False


class TestGetStats:
    def test_stats_empty(self, tmp_db):
        stats = get_stats(db_path=tmp_db)
        assert stats["total"] == 0
        assert stats["by_status"] == {}

    def test_stats_counts(self, tmp_db):
        add_application("A", "R", status="applied", db_path=tmp_db)
        add_application("B", "R", status="applied", db_path=tmp_db)
        add_application("C", "R", status="rejected", db_path=tmp_db)
        stats = get_stats(db_path=tmp_db)
        assert stats["total"] == 3
        assert stats["by_status"]["applied"] == 2
        assert stats["by_status"]["rejected"] == 1


class TestValidStatuses:
    def test_all_statuses_present(self):
        for s in ["applied", "screening", "interview", "offer", "rejected", "withdrawn"]:
            assert s in VALID_STATUSES

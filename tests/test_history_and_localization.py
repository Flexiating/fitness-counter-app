import json
from datetime import datetime, timedelta

from app.data.history import HistoryRepository, WorkoutSession
from app.ui.main_window import MainWindow
from app.ui.translations import LocalizationManager, tr


def sample_session() -> WorkoutSession:
    start = datetime(2026, 9, 15, 8, 30)
    return WorkoutSession(
        id=None,
        started_at=start.isoformat(),
        ended_at=(start + timedelta(seconds=90)).isoformat(),
        exercise="push_up",
        total_reps=20,
        duration_seconds=90,
        average_fps=29.5,
        average_posture_score=88.0,
        average_tracking_confidence=94.0,
        best_posture_score=97.0,
        target_reached=True,
    )


def test_sqlite_history_crud_filter_and_exports(tmp_path) -> None:
    repository = HistoryRepository(tmp_path / "history.sqlite3")
    session_id = repository.add(sample_session())

    assert repository.get(session_id).total_reps == 20
    assert len(repository.list("2026-09-15", "push_up")) == 1
    assert repository.list(exercise="crunch") == []

    csv_path, json_path = tmp_path / "history.csv", tmp_path / "history.json"
    repository.export_csv(csv_path)
    repository.export_json(json_path)
    assert "average_tracking_confidence" in csv_path.read_text(encoding="utf-8-sig")
    assert json.loads(json_path.read_text(encoding="utf-8"))[0]["target_reached"] is True

    repository.delete(session_id)
    assert repository.list() == []


def test_desktop_language_switch_updates_tabs_immediately() -> None:
    window = MainWindow()
    window.settings_page.language.setCurrentIndex(window.settings_page.language.findData("en"))
    assert window.tabs.tabText(1) == "History"
    window.settings_page.language.setCurrentIndex(window.settings_page.language.findData("vi"))
    assert window.tabs.tabText(1) == "Lịch sử"
    window.close()


def test_completed_desktop_session_is_saved_once(tmp_path) -> None:
    window = MainWindow()
    repository = HistoryRepository(tmp_path / "history.sqlite3")
    window.history_repository = repository
    window.started_at = datetime.now() - timedelta(seconds=30)
    window.metrics.record_repetitions(3, 1.0)
    window.metrics.update_quality(82.0, True)
    window.metrics.update_telemetry(91.0, 29.0)

    window._complete_session()
    window._complete_session()

    sessions = repository.list()
    assert len(sessions) == 1
    assert sessions[0].total_reps == 3
    assert sessions[0].average_tracking_confidence == 91.0
    window.close()


def test_localization_catalogs_have_matching_keys() -> None:
    manager = LocalizationManager("en")
    english = set(manager._catalogs["en"])
    vietnamese = set(manager._catalogs["vi"])
    assert english == vietnamese
    assert tr("exercise.push_up")

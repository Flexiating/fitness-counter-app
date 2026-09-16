from __future__ import annotations

import csv
import json
import sqlite3
from dataclasses import asdict, dataclass
from pathlib import Path

from app.utils.paths import app_data_path


@dataclass(frozen=True)
class WorkoutSession:
    id: int | None
    started_at: str
    ended_at: str
    exercise: str
    total_reps: int
    duration_seconds: float
    average_fps: float
    average_posture_score: float
    average_tracking_confidence: float
    best_posture_score: float
    target_reached: bool

    @property
    def date(self) -> str:
        return self.started_at[:10]


class HistoryRepository:
    COLUMNS = (
        "id", "started_at", "ended_at", "exercise", "total_reps",
        "duration_seconds", "average_fps", "average_posture_score",
        "average_tracking_confidence", "best_posture_score", "target_reached",
    )

    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path) if path is not None else app_data_path("data", "history.sqlite3")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS workout_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    started_at TEXT NOT NULL,
                    ended_at TEXT NOT NULL,
                    exercise TEXT NOT NULL CHECK(exercise IN ('push_up', 'crunch')),
                    total_reps INTEGER NOT NULL CHECK(total_reps >= 0),
                    duration_seconds REAL NOT NULL CHECK(duration_seconds >= 0),
                    average_fps REAL NOT NULL,
                    average_posture_score REAL NOT NULL,
                    average_tracking_confidence REAL NOT NULL,
                    best_posture_score REAL NOT NULL,
                    target_reached INTEGER NOT NULL CHECK(target_reached IN (0, 1))
                )
                """
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_sessions_started ON workout_sessions(started_at DESC)"
            )

    def add(self, session: WorkoutSession) -> int:
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO workout_sessions (
                    started_at, ended_at, exercise, total_reps, duration_seconds,
                    average_fps, average_posture_score, average_tracking_confidence,
                    best_posture_score, target_reached
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session.started_at, session.ended_at, session.exercise,
                    session.total_reps, session.duration_seconds, session.average_fps,
                    session.average_posture_score, session.average_tracking_confidence,
                    session.best_posture_score, int(session.target_reached),
                ),
            )
            return int(cursor.lastrowid)

    def list(self, date_query: str = "", exercise: str | None = None) -> list[WorkoutSession]:
        clauses: list[str] = []
        parameters: list[object] = []
        if date_query.strip():
            clauses.append("substr(started_at, 1, 10) LIKE ?")
            parameters.append(f"%{date_query.strip()}%")
        if exercise:
            clauses.append("exercise = ?")
            parameters.append(exercise)
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        with self._connect() as connection:
            rows = connection.execute(
                f"SELECT {', '.join(self.COLUMNS)} FROM workout_sessions{where} ORDER BY started_at DESC, id DESC",
                parameters,
            ).fetchall()
        return [self._from_row(row) for row in rows]

    def get(self, session_id: int) -> WorkoutSession | None:
        with self._connect() as connection:
            row = connection.execute(
                f"SELECT {', '.join(self.COLUMNS)} FROM workout_sessions WHERE id = ?",
                (session_id,),
            ).fetchone()
        return self._from_row(row) if row else None

    def delete(self, session_id: int) -> None:
        with self._connect() as connection:
            connection.execute("DELETE FROM workout_sessions WHERE id = ?", (session_id,))

    def clear(self) -> None:
        with self._connect() as connection:
            connection.execute("DELETE FROM workout_sessions")

    def export_csv(self, path: str | Path, sessions: list[WorkoutSession] | None = None) -> None:
        records = sessions if sessions is not None else self.list()
        export_columns = ("date",) + self.COLUMNS[1:]
        with Path(path).open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=export_columns)
            writer.writeheader()
            for session in records:
                row = asdict(session)
                row.pop("id", None)
                row["date"] = session.date
                writer.writerow(row)

    def export_json(self, path: str | Path, sessions: list[WorkoutSession] | None = None) -> None:
        records = sessions if sessions is not None else self.list()
        payload = [{"date": item.date, **asdict(item)} for item in records]
        Path(path).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    @staticmethod
    def _from_row(row: sqlite3.Row) -> WorkoutSession:
        values = dict(row)
        values["target_reached"] = bool(values["target_reached"])
        return WorkoutSession(**values)

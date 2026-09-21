"""SQLite-backed persistence for the extraction and review workflow."""

from __future__ import annotations

import sqlite3
import json
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Iterator

from contracts.extraction_contract import (
    EvidenceSpan,
    ExtractionDiagnostic,
    ExtractionResult,
    ExtractionStatus,
    FaultRecord,
)
from contracts.build_contract import BuildAttemptStatus, FaultTreeBuildAttempt
from contracts.release_contract import ReleaseBlock, ReleasedExtractionResult
from contracts.review_contract import (
    FaultRecordReview,
    PendingReviewItem,
    ReviewStatus,
    ReviewableExtractionResult,
)


_SCHEMA = """
CREATE TABLE IF NOT EXISTS extraction_results (
    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
    result_id TEXT NOT NULL UNIQUE,
    status TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS fault_records (
    record_id TEXT PRIMARY KEY,
    result_id TEXT NOT NULL,
    position INTEGER NOT NULL,
    fault_code TEXT,
    component TEXT,
    description TEXT NOT NULL,
    causes_json TEXT NOT NULL,
    parameters_json TEXT NOT NULL,
    confidence REAL,
    FOREIGN KEY (result_id) REFERENCES extraction_results(result_id)
        ON DELETE CASCADE,
    UNIQUE (result_id, position)
);

CREATE TABLE IF NOT EXISTS evidence_spans (
    evidence_id INTEGER PRIMARY KEY AUTOINCREMENT,
    record_id TEXT NOT NULL,
    field TEXT NOT NULL,
    source_id TEXT NOT NULL,
    quote TEXT NOT NULL,
    start INTEGER NOT NULL,
    end INTEGER NOT NULL,
    value_index INTEGER,
    FOREIGN KEY (record_id) REFERENCES fault_records(record_id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS extraction_diagnostics (
    diagnostic_id INTEGER PRIMARY KEY AUTOINCREMENT,
    result_id TEXT NOT NULL,
    position INTEGER NOT NULL,
    code TEXT NOT NULL,
    message TEXT NOT NULL,
    stage TEXT NOT NULL,
    retryable INTEGER NOT NULL,
    FOREIGN KEY (result_id) REFERENCES extraction_results(result_id)
        ON DELETE CASCADE,
    UNIQUE (result_id, position)
);

CREATE TABLE IF NOT EXISTS review_history (
    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
    review_id TEXT NOT NULL UNIQUE,
    record_id TEXT NOT NULL,
    status TEXT NOT NULL,
    reason TEXT,
    reviewer TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (record_id) REFERENCES fault_records(record_id)
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_fault_records_result
    ON fault_records(result_id, position);
CREATE INDEX IF NOT EXISTS idx_review_history_record
    ON review_history(record_id, created_at, sequence);
CREATE INDEX IF NOT EXISTS idx_review_history_status
    ON review_history(status);
"""

_BUILD_SCHEMA = """
CREATE TABLE IF NOT EXISTS release_results (
    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
    release_id TEXT NOT NULL UNIQUE,
    source_result_id TEXT NOT NULL,
    FOREIGN KEY (source_result_id) REFERENCES extraction_results(result_id)
        ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS release_records (
    release_id TEXT NOT NULL,
    record_id TEXT NOT NULL,
    position INTEGER NOT NULL,
    PRIMARY KEY (release_id, record_id),
    UNIQUE (release_id, position),
    FOREIGN KEY (release_id) REFERENCES release_results(release_id)
        ON DELETE CASCADE,
    FOREIGN KEY (record_id) REFERENCES fault_records(record_id)
        ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS release_decisions (
    decision_id INTEGER PRIMARY KEY AUTOINCREMENT,
    release_id TEXT NOT NULL,
    record_id TEXT NOT NULL,
    review_id TEXT NOT NULL,
    status TEXT NOT NULL,
    reason TEXT,
    reviewer TEXT,
    created_at TEXT NOT NULL,
    UNIQUE (release_id, record_id),
    FOREIGN KEY (release_id) REFERENCES release_results(release_id)
        ON DELETE CASCADE,
    FOREIGN KEY (record_id) REFERENCES fault_records(record_id)
        ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS release_blocks (
    block_id INTEGER PRIMARY KEY AUTOINCREMENT,
    release_id TEXT NOT NULL,
    record_id TEXT NOT NULL,
    status TEXT,
    reason TEXT NOT NULL,
    UNIQUE (release_id, record_id),
    FOREIGN KEY (release_id) REFERENCES release_results(release_id)
        ON DELETE CASCADE,
    FOREIGN KEY (record_id) REFERENCES fault_records(record_id)
        ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS build_attempts (
    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
    attempt_id TEXT NOT NULL UNIQUE,
    release_id TEXT NOT NULL,
    source_result_id TEXT NOT NULL,
    top_event TEXT NOT NULL,
    status TEXT NOT NULL,
    reason TEXT,
    retryable INTEGER NOT NULL,
    tree_json TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (release_id) REFERENCES release_results(release_id)
        ON DELETE RESTRICT,
    FOREIGN KEY (source_result_id) REFERENCES extraction_results(result_id)
        ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_build_attempts_release
    ON build_attempts(release_id, sequence);
"""

_DATASET_IMPORT_SCHEMA = """
CREATE TABLE IF NOT EXISTS dataset_imports (
    import_id TEXT PRIMARY KEY,
    dataset_name TEXT NOT NULL,
    dataset_version TEXT NOT NULL,
    source_corpus TEXT NOT NULL,
    record_count INTEGER NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE (dataset_name, dataset_version)
);

CREATE TABLE IF NOT EXISTS dataset_import_records (
    import_id TEXT NOT NULL,
    sample_id TEXT NOT NULL,
    result_id TEXT NOT NULL,
    record_id TEXT NOT NULL,
    source_file TEXT,
    source_url TEXT,
    source_sha256 TEXT,
    source_page_start INTEGER,
    source_page_end INTEGER,
    source_text TEXT NOT NULL,
    PRIMARY KEY (import_id, sample_id),
    UNIQUE (import_id, result_id),
    UNIQUE (import_id, record_id),
    FOREIGN KEY (import_id) REFERENCES dataset_imports(import_id)
        ON DELETE CASCADE,
    FOREIGN KEY (result_id) REFERENCES extraction_results(result_id)
        ON DELETE RESTRICT,
    FOREIGN KEY (record_id) REFERENCES fault_records(record_id)
        ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_dataset_import_records_sample
    ON dataset_import_records(import_id, sample_id);
"""

_SCHEMA_VERSION = 4


class SQLiteExtractionWorkflowRepository:
    """Durable implementation of the extraction workflow repository contract."""

    def __init__(self, database_path: str | Path) -> None:
        if not isinstance(database_path, (str, Path)):
            raise TypeError("database_path must be a string or Path")

        self._database_path = str(database_path)
        if not self._database_path.strip():
            raise ValueError("database_path must not be empty")
        if self._database_path != ":memory:":
            Path(self._database_path).parent.mkdir(parents=True, exist_ok=True)

        with self._connect() as connection:
            self._migrate(connection)

    @property
    def schema_version(self) -> int:
        """Return the SQLite schema version stored in the database."""
        with self._connect() as connection:
            return int(connection.execute("PRAGMA user_version").fetchone()[0])

    def backup_to(
        self,
        destination: str | Path,
        *,
        overwrite: bool = False,
    ) -> Path:
        """Create a consistent SQLite backup without overwriting by default."""
        if self._database_path == ":memory:":
            raise ValueError("in-memory repositories cannot create file backups")
        if not isinstance(destination, (str, Path)):
            raise TypeError("destination must be a string or Path")

        target = Path(destination)
        if not str(target).strip():
            raise ValueError("destination must not be empty")
        target = target.resolve()
        source = Path(self._database_path).resolve()
        if target == source:
            raise ValueError("backup destination must differ from the database path")
        if target.exists() and not overwrite:
            raise FileExistsError(f"backup destination already exists: {target}")
        target.parent.mkdir(parents=True, exist_ok=True)

        with self._connect() as source_connection:
            target_connection = sqlite3.connect(str(target), timeout=5.0)
            try:
                source_connection.backup(target_connection)
                target_connection.commit()
            finally:
                target_connection.close()
        return target

    def save(self, result: ExtractionResult) -> ExtractionResult:
        """Persist one extraction result without overwriting an existing result."""
        self._validate_result(result)
        try:
            with self._connect() as connection:
                self._insert_result(connection, result)
                connection.commit()
        except sqlite3.IntegrityError as exc:
            raise ValueError("result_id has already been stored") from exc
        return result

    def get(self, result_id: str) -> ExtractionResult | None:
        """Load one complete extraction result by result ID."""
        self._validate_result_id(result_id)
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM extraction_results WHERE result_id = ?",
                (result_id.strip(),),
            ).fetchone()
            if row is None:
                return None
            return self._load_result(connection, row)

    def append(self, review: FaultRecordReview) -> FaultRecordReview:
        """Persist one immutable review decision."""
        self._validate_review(review)
        try:
            with self._connect() as connection:
                record = connection.execute(
                    "SELECT 1 FROM fault_records WHERE record_id = ?",
                    (review.record_id,),
                ).fetchone()
                if record is None:
                    raise ValueError(
                        f"no fault record exists for record_id: {review.record_id}"
                    )
                self._insert_review(connection, review)
                connection.commit()
        except sqlite3.IntegrityError as exc:
            raise ValueError("review_id has already been stored") from exc
        return review

    def get_current(self, record_id: str) -> FaultRecordReview | None:
        """Return the latest review decision for one record."""
        self._validate_record_id(record_id)
        with self._connect() as connection:
            return self._load_current_review(connection, record_id.strip())

    def history(self, record_id: str) -> tuple[FaultRecordReview, ...]:
        """Return all review decisions for one record in insertion order."""
        self._validate_record_id(record_id)
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM review_history
                WHERE record_id = ?
                ORDER BY sequence ASC
                """,
                (record_id.strip(),),
            ).fetchall()
            return tuple(self._load_review(row) for row in rows)

    def list_pending(self) -> tuple[FaultRecordReview, ...]:
        """Return current records whose ordinary review state is pending."""
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT record_id, MAX(sequence) AS latest_sequence
                FROM review_history
                GROUP BY record_id
                ORDER BY latest_sequence ASC
                """
            ).fetchall()
            reviews = []
            for row in rows:
                review = self._load_current_review(connection, row["record_id"])
                if review is not None and review.status is ReviewStatus.PENDING:
                    reviews.append(review)
            return tuple(reviews)

    def save_extraction_with_reviews(
        self,
        result: ExtractionResult,
        reviews: tuple[FaultRecordReview, ...],
    ) -> ReviewableExtractionResult:
        """Atomically persist an extraction and one initial review per record."""
        self._validate_result(result)
        reviews = tuple(reviews)
        self._validate_initial_reviews(result, reviews)

        try:
            with self._connect() as connection:
                self._insert_result(connection, result)
                for review in reviews:
                    self._insert_review(connection, review)
                connection.commit()
        except sqlite3.IntegrityError as exc:
            raise ValueError("extraction workflow data already exists") from exc

        return ReviewableExtractionResult(extraction=result, reviews=reviews)

    def list_pending_review_items(self) -> tuple[PendingReviewItem, ...]:
        """Return one item for each record with a current pending review."""
        pending: list[PendingReviewItem] = []
        with self._connect() as connection:
            results = connection.execute(
                "SELECT * FROM extraction_results ORDER BY sequence ASC"
            ).fetchall()
            for result_row in results:
                result = self._load_result(connection, result_row)
                for record in result.records:
                    review = self._load_current_review(connection, record.record_id)
                    if review is None or review.status is not ReviewStatus.PENDING:
                        continue
                    pending.append(
                        PendingReviewItem(
                            result_id=result.result_id,
                            extraction_status=result.status,
                            diagnostics=result.diagnostics,
                            record=record,
                            evidence_spans=tuple(
                                span
                                for span in result.evidence_spans
                                if span.record_id == record.record_id
                            ),
                            review=review,
                        )
                    )
        return tuple(pending)

    def save_release(
        self,
        release: ReleasedExtractionResult,
    ) -> ReleasedExtractionResult:
        """Persist one immutable downstream release projection."""
        if not isinstance(release, ReleasedExtractionResult):
            raise TypeError("release must be a ReleasedExtractionResult")
        try:
            with self._connect() as connection:
                connection.execute(
                    """
                    INSERT INTO release_results(release_id, source_result_id)
                    VALUES (?, ?)
                    """,
                    (release.release_id, release.source_result_id),
                )
                for position, record in enumerate(release.records):
                    connection.execute(
                        """
                        INSERT INTO release_records(release_id, record_id, position)
                        VALUES (?, ?, ?)
                        """,
                        (release.release_id, record.record_id, position),
                    )
                for decision in release.review_decisions:
                    connection.execute(
                        """
                        INSERT INTO release_decisions(
                            release_id, record_id, review_id, status, reason,
                            reviewer, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            release.release_id,
                            decision.record_id,
                            decision.review_id,
                            decision.status.value,
                            decision.reason,
                            decision.reviewer,
                            decision.created_at.isoformat(),
                        ),
                    )
                for block in release.blocked:
                    connection.execute(
                        """
                        INSERT INTO release_blocks(
                            release_id, record_id, status, reason
                        ) VALUES (?, ?, ?, ?)
                        """,
                        (
                            release.release_id,
                            block.record_id,
                            block.status.value if block.status is not None else None,
                            block.reason,
                        ),
                    )
                connection.commit()
        except sqlite3.IntegrityError as exc:
            raise ValueError("release data already exists or is inconsistent") from exc
        return release

    def get_release(self, release_id: str) -> ReleasedExtractionResult | None:
        """Load one persisted release projection."""
        if not isinstance(release_id, str) or not release_id.strip():
            raise ValueError("release_id must be a non-empty string")
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM release_results WHERE release_id = ?",
                (release_id.strip(),),
            ).fetchone()
            if row is None:
                return None

            record_rows = connection.execute(
                """
                SELECT fault_records.*
                FROM release_records
                JOIN fault_records ON fault_records.record_id = release_records.record_id
                WHERE release_records.release_id = ?
                ORDER BY release_records.position ASC
                """,
                (release_id.strip(),),
            ).fetchall()
            records = tuple(self._load_record(connection, item) for item in record_rows)

            decision_rows = connection.execute(
                """
                SELECT review_id, record_id, status, reason, reviewer, created_at
                FROM release_decisions
                WHERE release_id = ?
                ORDER BY decision_id ASC
                """,
                (release_id.strip(),),
            ).fetchall()
            decisions = tuple(self._load_review(item) for item in decision_rows)

            block_rows = connection.execute(
                """
                SELECT record_id, status, reason
                FROM release_blocks
                WHERE release_id = ?
                ORDER BY block_id ASC
                """,
                (release_id.strip(),),
            ).fetchall()
            blocked = tuple(
                ReleaseBlock(
                    record_id=item["record_id"],
                    status=item["status"],
                    reason=item["reason"],
                )
                for item in block_rows
            )

            release = ReleasedExtractionResult(
                source_result_id=row["source_result_id"],
                records=records,
                review_decisions=decisions,
                blocked=blocked,
            )
            object.__setattr__(release, "release_id", row["release_id"])
            return release

    def append_build_attempt(
        self,
        attempt: FaultTreeBuildAttempt,
    ) -> FaultTreeBuildAttempt:
        """Persist one append-only build attempt."""
        if not isinstance(attempt, FaultTreeBuildAttempt):
            raise TypeError("attempt must be a FaultTreeBuildAttempt")
        tree_json = (
            None
            if attempt.tree is None
            else json.dumps(attempt.tree, ensure_ascii=False, sort_keys=True)
        )
        try:
            with self._connect() as connection:
                release = connection.execute(
                    "SELECT 1 FROM release_results WHERE release_id = ?",
                    (attempt.release_id,),
                ).fetchone()
                if release is None:
                    raise ValueError(
                        f"no release exists for release_id: {attempt.release_id}"
                    )
                connection.execute(
                    """
                    INSERT INTO build_attempts(
                        attempt_id, release_id, source_result_id, top_event,
                        status, reason, retryable, tree_json, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        attempt.attempt_id,
                        attempt.release_id,
                        attempt.source_result_id,
                        attempt.top_event,
                        attempt.status.value,
                        attempt.reason,
                        int(attempt.retryable),
                        tree_json,
                        attempt.created_at.isoformat(),
                    ),
                )
                connection.commit()
        except sqlite3.IntegrityError as exc:
            raise ValueError("attempt_id has already been stored") from exc
        return attempt

    def get_build_attempt(self, attempt_id: str) -> FaultTreeBuildAttempt | None:
        if not isinstance(attempt_id, str) or not attempt_id.strip():
            raise ValueError("attempt_id must be a non-empty string")
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM build_attempts WHERE attempt_id = ?",
                (attempt_id.strip(),),
            ).fetchone()
            return None if row is None else self._load_build_attempt(row)

    def list_build_attempts(
        self,
        release_id: str,
    ) -> tuple[FaultTreeBuildAttempt, ...]:
        if not isinstance(release_id, str) or not release_id.strip():
            raise ValueError("release_id must be a non-empty string")
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM build_attempts
                WHERE release_id = ?
                ORDER BY sequence ASC
                """,
                (release_id.strip(),),
            ).fetchall()
            return tuple(self._load_build_attempt(row) for row in rows)

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self._database_path, timeout=5.0)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 5000")
        try:
            yield connection
        finally:
            connection.close()

    @staticmethod
    def _migrate(connection: sqlite3.Connection) -> None:
        current_version = int(
            connection.execute("PRAGMA user_version").fetchone()[0]
        )
        if current_version > _SCHEMA_VERSION:
            raise RuntimeError(
                "database schema is newer than this application: "
                f"{current_version} > {_SCHEMA_VERSION}"
            )

        if current_version < 1:
            connection.executescript(_SCHEMA)
            connection.execute("PRAGMA user_version = 1")
            connection.commit()

        current_version = int(
            connection.execute("PRAGMA user_version").fetchone()[0]
        )
        if current_version < 2:
            connection.executescript(_BUILD_SCHEMA)
            connection.execute("PRAGMA user_version = 2")
            connection.commit()

        current_version = int(
            connection.execute("PRAGMA user_version").fetchone()[0]
        )
        if current_version < 3:
            connection.execute(
                "ALTER TABLE fault_records ADD COLUMN "
                "related_components_json TEXT NOT NULL DEFAULT '[]'"
            )
            connection.execute("PRAGMA user_version = 3")
            connection.commit()

        current_version = int(
            connection.execute("PRAGMA user_version").fetchone()[0]
        )
        if current_version < 4:
            connection.executescript(_DATASET_IMPORT_SCHEMA)
            connection.execute("PRAGMA user_version = 4")
            connection.commit()

    @staticmethod
    def _load_build_attempt(row: sqlite3.Row) -> FaultTreeBuildAttempt:
        tree = None if row["tree_json"] is None else json.loads(row["tree_json"])
        attempt = FaultTreeBuildAttempt(
            release_id=row["release_id"],
            source_result_id=row["source_result_id"],
            top_event=row["top_event"],
            status=BuildAttemptStatus(row["status"]),
            reason=row["reason"],
            retryable=bool(row["retryable"]),
            tree=tree,
            created_at=datetime.fromisoformat(row["created_at"]),
        )
        object.__setattr__(attempt, "attempt_id", row["attempt_id"])
        return attempt

    @staticmethod
    def _insert_result(
        connection: sqlite3.Connection,
        result: ExtractionResult,
    ) -> None:
        connection.execute(
            "INSERT INTO extraction_results(result_id, status) VALUES (?, ?)",
            (result.result_id, result.status.value),
        )
        for position, record in enumerate(result.records):
            connection.execute(
                """
                INSERT INTO fault_records(
                    record_id, result_id, position, fault_code, component,
                    related_components_json,
                    description, causes_json, parameters_json, confidence
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.record_id,
                    result.result_id,
                    position,
                    record.fault_code,
                    record.component,
                    _json_array(record.related_components),
                    record.description,
                    _json_array(record.causes),
                    _json_array(record.parameters),
                    record.confidence,
                ),
            )

        for span in result.evidence_spans:
            connection.execute(
                """
                INSERT INTO evidence_spans(
                    record_id, field, source_id, quote, start, end, value_index
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    span.record_id,
                    span.field.value,
                    span.source_id,
                    span.quote,
                    span.start,
                    span.end,
                    span.value_index,
                ),
            )

        for position, diagnostic in enumerate(result.diagnostics):
            connection.execute(
                """
                INSERT INTO extraction_diagnostics(
                    result_id, position, code, message, stage, retryable
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    result.result_id,
                    position,
                    diagnostic.code,
                    diagnostic.message,
                    diagnostic.stage,
                    int(diagnostic.retryable),
                ),
            )

    @staticmethod
    def _insert_review(
        connection: sqlite3.Connection,
        review: FaultRecordReview,
    ) -> None:
        connection.execute(
            """
            INSERT INTO review_history(
                review_id, record_id, status, reason, reviewer, created_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                review.review_id,
                review.record_id,
                review.status.value,
                review.reason,
                review.reviewer,
                review.created_at.isoformat(),
            ),
        )

    def _load_result(
        self,
        connection: sqlite3.Connection,
        result_row: sqlite3.Row,
    ) -> ExtractionResult:
        result_id = result_row["result_id"]
        record_rows = connection.execute(
            """
            SELECT *
            FROM fault_records
            WHERE result_id = ?
            ORDER BY position ASC
            """,
            (result_id,),
        ).fetchall()
        records = [self._load_record(connection, row) for row in record_rows]

        evidence_rows = connection.execute(
            """
            SELECT *
            FROM evidence_spans
            WHERE record_id IN (
                SELECT record_id FROM fault_records WHERE result_id = ?
            )
            ORDER BY evidence_id ASC
            """,
            (result_id,),
        ).fetchall()
        evidence_spans = tuple(self._load_evidence(row) for row in evidence_rows)

        diagnostic_rows = connection.execute(
            """
            SELECT *
            FROM extraction_diagnostics
            WHERE result_id = ?
            ORDER BY position ASC
            """,
            (result_id,),
        ).fetchall()
        diagnostics = tuple(
            ExtractionDiagnostic(
                code=row["code"],
                message=row["message"],
                stage=row["stage"],
                retryable=bool(row["retryable"]),
            )
            for row in diagnostic_rows
        )

        result = ExtractionResult(
            status=ExtractionStatus(result_row["status"]),
            records=tuple(records),
            evidence_spans=evidence_spans,
            diagnostics=diagnostics,
        )
        object.__setattr__(result, "result_id", result_id)
        return result

    @staticmethod
    def _load_record(
        connection: sqlite3.Connection,
        row: sqlite3.Row,
    ) -> FaultRecord:
        causes = tuple(_json_values(row["causes_json"]))
        parameters = tuple(_json_values(row["parameters_json"]))
        record = FaultRecord(
            description=row["description"],
            fault_code=row["fault_code"],
            component=row["component"],
            related_components=tuple(_json_values(row["related_components_json"])),
            causes=causes,
            parameters=parameters,
            confidence=row["confidence"],
        )
        object.__setattr__(record, "record_id", row["record_id"])
        return record

    @staticmethod
    def _load_evidence(row: sqlite3.Row) -> EvidenceSpan:
        return EvidenceSpan(
            record_id=row["record_id"],
            field=row["field"],
            source_id=row["source_id"],
            quote=row["quote"],
            start=row["start"],
            end=row["end"],
            value_index=row["value_index"],
        )

    def _load_current_review(
        self,
        connection: sqlite3.Connection,
        record_id: str,
    ) -> FaultRecordReview | None:
        row = connection.execute(
            """
            SELECT *
            FROM review_history
            WHERE record_id = ?
            ORDER BY created_at DESC, sequence DESC
            LIMIT 1
            """,
            (record_id,),
        ).fetchone()
        return None if row is None else self._load_review(row)

    @staticmethod
    def _load_review(row: sqlite3.Row) -> FaultRecordReview:
        review = FaultRecordReview(
            record_id=row["record_id"],
            status=ReviewStatus(row["status"]),
            reason=row["reason"],
            reviewer=row["reviewer"],
            created_at=datetime.fromisoformat(row["created_at"]),
        )
        object.__setattr__(review, "review_id", row["review_id"])
        return review

    @staticmethod
    def _validate_result(result: ExtractionResult) -> None:
        if not isinstance(result, ExtractionResult):
            raise TypeError("result must be an ExtractionResult")

    @staticmethod
    def _validate_review(review: FaultRecordReview) -> None:
        if not isinstance(review, FaultRecordReview):
            raise TypeError("review must be a FaultRecordReview")

    @staticmethod
    def _validate_initial_reviews(
        result: ExtractionResult,
        reviews: tuple[FaultRecordReview, ...],
    ) -> None:
        if not all(isinstance(review, FaultRecordReview) for review in reviews):
            raise TypeError("reviews must contain only FaultRecordReview values")
        record_ids = {record.record_id for record in result.records}
        review_record_ids = [review.record_id for review in reviews]
        if len(review_record_ids) != len(set(review_record_ids)):
            raise ValueError("reviews must have unique record_id values")
        if set(review_record_ids) != record_ids:
            raise ValueError(
                "reviews must contain one current state for every extraction record"
            )

    @staticmethod
    def _validate_result_id(result_id: str) -> None:
        if not isinstance(result_id, str) or not result_id.strip():
            raise ValueError("result_id must be a non-empty string")

    @staticmethod
    def _validate_record_id(record_id: str) -> None:
        if not isinstance(record_id, str) or not record_id.strip():
            raise ValueError("record_id must be a non-empty string")


def _json_array(values: tuple[str, ...]) -> str:
    return json.dumps(list(values), ensure_ascii=False)


def _json_values(value: str) -> list[str]:
    values = json.loads(value)
    if not isinstance(values, list) or not all(isinstance(item, str) for item in values):
        raise ValueError("stored repeated field is not a list of strings")
    return values

import webbrowser
from datetime import datetime

from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from core.report import export_csv
from models import Job
from ui import styles
from ui.widgets import TopBar


class ScoreLabel(QLabel):
    def __init__(self, target: int, parent=None):
        super().__init__(parent)
        self._target = target
        self._current = 0
        self.setAlignment(Qt.AlignRight)
        self.setStyleSheet(
            f"font-size:20px; font-weight:500; color:{styles.TEXT_PRIMARY};"
        )
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(16)

    def _tick(self) -> None:
        if self._current >= self._target:
            self.setText(f"{self._target}%")
            self._timer.stop()
            return
        self._current += max(1, (self._target - self._current) // 8)
        self.setText(f"{self._current}%")


class JobCard(QFrame):
    def __init__(self, job: Job, parent=None):
        super().__init__(parent)
        self.job = job
        self.setStyleSheet(
            f"""
            QFrame {{
                background: {styles.RAISED};
                border: 1px solid {styles.BORDER};
                border-radius: 12px;
            }}
            """
        )
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(12)

        left = QVBoxLayout()
        title = QLabel(job.title)
        title.setStyleSheet(
            f"font-size:14px; font-weight:500; color:{styles.TEXT_PRIMARY};"
        )
        meta_parts = [job.company, job.location]
        if job.job_type:
            meta_parts.append(job.job_type)
        meta = QLabel(" · ".join(p for p in meta_parts if p))
        meta.setStyleSheet(f"font-size:12px; color:{styles.TEXT_SECONDARY};")
        left.addWidget(title)
        left.addWidget(meta)

        tags_row = QHBoxLayout()
        tags_row.setSpacing(6)
        for skill in job.matched_skills[:6]:
            tag = QLabel(skill)
            tag.setStyleSheet(
                f"""
                background:{styles.MATCH_BG};
                color:{styles.MATCH_TEXT};
                font-size:11px;
                padding:2px 8px;
                border-radius:20px;
                """
            )
            tags_row.addWidget(tag)
        loc_tag = QLabel(job.location or "Remote")
        loc_tag.setStyleSheet(
            f"""
            background:{styles.LOC_BG};
            color:{styles.LOC_TEXT};
            font-size:11px;
            padding:2px 8px;
            border-radius:20px;
            """
        )
        tags_row.addWidget(loc_tag)
        tags_row.addStretch()
        left.addLayout(tags_row)
        layout.addLayout(left, 1)

        right = QVBoxLayout()
        right.setAlignment(Qt.AlignTop | Qt.AlignRight)
        score_wrap = QVBoxLayout()
        score_wrap.setAlignment(Qt.AlignRight)
        score = ScoreLabel(job.score)
        score_lbl = QLabel("match")
        score_lbl.setAlignment(Qt.AlignRight)
        score_lbl.setStyleSheet(
            f"font-size:10px; color:{styles.TEXT_TERTIARY};"
        )
        score_wrap.addWidget(score)
        score_wrap.addWidget(score_lbl)
        right.addLayout(score_wrap)

        apply_btn = QPushButton("Apply ↗")
        apply_btn.setCursor(Qt.PointingHandCursor)
        apply_btn.setStyleSheet(
            f"""
            QPushButton {{
                font-size:12px;
                padding:6px 14px;
                border: 0.5px solid {styles.BORDER};
                border-radius: 8px;
                background: transparent;
                color: {styles.TEXT_PRIMARY};
            }}
            QPushButton:hover {{ background: {styles.LOG_BG}; }}
            """
        )
        apply_btn.clicked.connect(lambda: webbrowser.open(job.url))
        right.addWidget(apply_btn, 0, Qt.AlignRight)
        layout.addLayout(right)


class ResultsScreen(QWidget):
    back_to_setup = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._jobs: list[Job] = []
        self._threshold = 70
        self._build_ui()

    def _footer_btn_style(self, primary: bool = False) -> str:
        if primary:
            return f"""
            QPushButton {{
                background: {styles.ACCENT};
                color: {styles.ACCENT_TEXT};
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 500;
            }}
            QPushButton:hover {{ background: {styles.ACCENT_HOVER}; }}
            """
        return f"""
        QPushButton {{
            font-size: 13px;
            padding: 10px 16px;
            border: 0.5px solid {styles.BORDER};
            border-radius: 8px;
            background: transparent;
            color: {styles.TEXT_PRIMARY};
        }}
        QPushButton:hover {{ background: {styles.LOG_BG}; }}
        """

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        self.topbar = TopBar(2)
        root.addWidget(self.topbar)

        shell = QWidget()
        shell.setStyleSheet(f"background:{styles.SHELL};")
        body = QVBoxLayout(shell)
        body.setContentsMargins(24, 28, 24, 28)

        header = QHBoxLayout()
        titles = QVBoxLayout()
        self.count_title = QLabel("0 jobs matched")
        self.count_title.setStyleSheet(
            f"font-size:14px; font-weight:500; color:{styles.TEXT_PRIMARY};"
        )
        self.count_sub = QLabel("sorted by match score")
        self.count_sub.setStyleSheet(
            f"font-size:12px; color:{styles.TEXT_SECONDARY};"
        )
        titles.addWidget(self.count_title)
        titles.addWidget(self.count_sub)
        header.addLayout(titles)
        header.addStretch()

        self.export_btn = QPushButton("Export CSV")
        self.export_btn.setCursor(Qt.PointingHandCursor)
        self.export_btn.setStyleSheet(self._footer_btn_style())
        self.export_btn.clicked.connect(self._export_report)
        header.addWidget(self.export_btn)
        body.addLayout(header)
        body.addSpacing(20)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.cards_host = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_host)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.cards_layout.setSpacing(10)
        self.cards_layout.addStretch()
        scroll.setWidget(self.cards_host)
        body.addWidget(scroll, 1)

        footer = QHBoxLayout()
        footer.setSpacing(12)
        self.back_footer_btn = QPushButton("Back to setup")
        self.back_footer_btn.setCursor(Qt.PointingHandCursor)
        self.back_footer_btn.setFixedHeight(40)
        self.back_footer_btn.setStyleSheet(self._footer_btn_style(primary=True))
        self.back_footer_btn.clicked.connect(self.back_to_setup.emit)
        footer.addWidget(self.back_footer_btn, 1)
        body.addLayout(footer)

        root.addWidget(shell, 1)

    def set_results(self, jobs: list[Job], threshold: int) -> None:
        self._jobs = jobs
        self._threshold = threshold
        self.count_title.setText(f"{len(jobs)} jobs matched")
        if jobs:
            self.count_sub.setText("sorted by match score")
        else:
            self.count_sub.setText(f"none above {threshold}% — lower the slider and scan again")
        self.export_btn.setEnabled(bool(jobs))

        while self.cards_layout.count() > 1:
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not jobs:
            empty = QLabel(
                "No jobs met your threshold.\n"
                "Try lowering the match score, another source, or a different /jobs URL."
            )
            empty.setWordWrap(True)
            empty.setStyleSheet(f"color:{styles.TEXT_SECONDARY}; font-size:13px;")
            self.cards_layout.insertWidget(0, empty)
            return

        for job in jobs:
            self.cards_layout.insertWidget(self.cards_layout.count() - 1, JobCard(job))

    def _export_report(self) -> None:
        if not self._jobs:
            return
        default = f"drift_jobs_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export results",
            default,
            "CSV (*.csv)",
        )
        if path:
            saved = export_csv(self._jobs, self._threshold, path)
            QMessageBox.information(
                self,
                "Exported",
                f"Saved {len(self._jobs)} jobs to:\n{saved}",
            )

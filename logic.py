import os
import sys
import json
from PySide6.QtWidgets import QPushButton, QInputDialog, QWidget
from PySide6.QtCore import QTimer, QUrl
from PySide6.QtMultimedia import QSoundEffect

from ui import build_ui


class FocusCat(QWidget):
    padding = 20

    # ---------------- Initialization ----------------

    def __init__(self):
        super().__init__()

        self.state = "startup"
        self.attention_span = None
        self.goal_minutes = 60
        self.remaining = 0
        self.sessions = []

        self.load_or_create_today()
        build_ui(self)
        self.update_ui()

        # timers
        self.tick = QTimer()
        self.tick.timeout.connect(self.on_tick)

        self.beep_timer = QTimer()
        self.beep_timer.timeout.connect(self.play_beep)

        # delay sound init so PyInstaller can extract plugins
        QTimer.singleShot(0, self.init_sound)

    # ---------------- Sound ----------------

    def resource_path(self, relative):
        try:
            return os.path.join(sys._MEIPASS, relative)
        except Exception:
            return os.path.join(os.path.abspath("."), relative)

    def init_sound(self):
        self.beep = QSoundEffect(self)
        self.beep.setSource(QUrl.fromLocalFile(self.resource_path("beep.wav")))
        self.beep.setLoopCount(1)
        self.beep.setVolume(1.0)

    # ---------------- Buttons ----------------

    def create_buttons(self):
        self.btn_start_baseline = QPushButton("Start baseline")
        self.btn_start_baseline.clicked.connect(self.start_baseline)

        self.btn_stop_baseline = QPushButton("Stop baseline")
        self.btn_stop_baseline.clicked.connect(self.stop_baseline)

        self.btn_start_session = QPushButton("Start session")
        self.btn_start_session.clicked.connect(self.start_session)

        self.btn_pause_session = QPushButton("Pause session")
        self.btn_pause_session.clicked.connect(self.pause_session)

        self.btn_resume_session = QPushButton("Resume session")
        self.btn_resume_session.clicked.connect(self.resume_session)

        self.btn_reset_session = QPushButton("Reset session")
        self.btn_reset_session.clicked.connect(self.reset_session)

        self.btn_stop_ringing = QPushButton("Stop ringing")
        self.btn_stop_ringing.clicked.connect(self.stop_ringing)

        self.reset_button = QPushButton("Reset day")
        self.reset_button.clicked.connect(self.reset_day)

        self.manual_span_button = QPushButton("Set span manually")
        self.manual_span_button.clicked.connect(self.set_span_manually)

    # ---------------- JSON ----------------

    def load_or_create_today(self):
        path = "focus-today.json"
        if os.path.exists(path):
            with open(path, "r") as f:
                data = json.load(f)
            self.attention_span = data.get("attention_span_seconds")
            self.goal_minutes = data.get("goal_minutes", 60)
            self.sessions = data.get("sessions", [])
        else:
            self.save_today()

        self.state = "no_span" if self.attention_span is None else "idle"

    def save_today(self):
        data = {
            "attention_span_seconds": self.attention_span,
            "goal_minutes": self.goal_minutes,
            "sessions": self.sessions
        }
        with open("focus-today.json", "w") as f:
            json.dump(data, f, indent=2)

    # ---------------- UI Updates ----------------

    def update_ui(self):
        self.update_stats()
        self.update_cat()
        self.update_encouragement()
        self.update_timer_display()
        self.update_buttons()

    def update_stats(self):
        if self.attention_span is None:
            self.stats.setText(f"Sessions: {len(self.sessions)}")
            self.stats.setStyleSheet("color: white")
            return

        goal_sessions = int(self.goal_minutes // (self.attention_span / 60))
        current = len(self.sessions)
        self.stats.setText(f"Sessions: {current} / {goal_sessions}")

        self.stats.setStyleSheet(
            "color: #68ff77" if current >= goal_sessions else "color: white"
        )

    def update_cat(self):
        faces = {
            "no_span": "/`｡ꞈ｡'\\",
            "baseline": "/`｡ꞈ｡'\\",
            "idle": "/`｡ꞈ｡'\\",
            "running": "/`｡ꞈ｡'\\",
            "paused": "/`｡ꞈ｡'\\",
            "ringing": "/`– ⩊ –'\\",
        }
        self.cat.setText(faces[self.state])

    def update_encouragement(self):
        messages = {
            "no_span": "Let's measure your attention span for today",
            "baseline": "Focus time!",
            "idle": "Ready when you are",
            "running": "Focus time!",
            "paused": "I'll be waiting right here",
            "ringing": "Damn, look at you~",
        }
        self.encouragement.setText(messages[self.state])

    def update_timer_display(self):
        if self.state == "baseline":
            m, s = divmod(self.elapsed, 60)
        elif self.state in ("idle", "paused"):
            m, s = divmod(self.attention_span or 0, 60)
        else:
            m, s = divmod(self.remaining, 60)

        style = "font-size: 32px; font-weight: bold;"
        if self.state == "paused":
            style += " color: grey;"
        if self.state == "ringing":
            style += " color: #68ff77;"

        self.timer_label.setStyleSheet(style)
        self.timer_label.setText(f"{m:02d}:{s:02d}")

    def update_buttons(self):
        mapping = {
            "no_span": [self.btn_start_baseline, self.manual_span_button],
            "baseline": [self.btn_stop_baseline],
            "idle": [self.btn_start_session],
            "running": [self.btn_pause_session],
            "paused": [self.btn_resume_session, self.btn_reset_session],
            "ringing": [self.btn_stop_ringing],
        }
        self.set_action_column(mapping[self.state])

    def set_action_column(self, widgets):
        while self.action_column.count():
            item = self.action_column.takeAt(0)
            if item.widget():
                item.widget().setParent(None)

        self.action_column.addStretch()
        for w in widgets:
            self.action_column.addWidget(w)
        self.action_column.addStretch()

    # ---------------- State Logic ----------------

    def start_baseline(self):
        self.state = "baseline"
        self.elapsed = 0
        self.tick.start(1000)
        self.update_ui()

    def stop_baseline(self):
        self.tick.stop()
        self.attention_span = self.elapsed
        self.sessions.append({"type": "study", "seconds": self.attention_span})
        self.save_today()
        self.state = "idle"
        self.update_ui()

    def start_session(self):
        self.remaining = self.attention_span
        self.state = "running"
        self.tick.start(1000)
        self.update_ui()

    def pause_session(self):
        self.tick.stop()
        self.state = "paused"
        self.update_ui()

    def resume_session(self):
        self.state = "running"
        self.tick.start(1000)
        self.update_ui()

    def reset_session(self):
        self.tick.stop()
        self.state = "idle"
        self.remaining = self.attention_span
        self.update_ui()

    def stop_ringing(self):
        self.state = "idle"
        self.sessions.append({"type": "study", "seconds": self.attention_span})
        self.save_today()
        self.update_ui()
        self.beep_timer.stop()

    def reset_day(self):
        self.attention_span = None
        self.sessions = []
        self.state = "no_span"
        self.cat.setText("/`– ˕ –'\\")
        self.save_today()
        self.update_ui()
        self.manual_span_button.show()

    def set_span_manually(self):
        minutes, ok = QInputDialog.getInt(
            self, "Set attention span", "Minutes:", 25, 1, 300
        )
        if ok:
            self.attention_span = minutes * 60
            self.state = "idle"
            self.save_today()
            self.update_ui()
            self.manual_span_button.hide()

    # ---------------- Goal Editing ----------------

    def on_goal_button(self):
        if not self.is_editing_goal:
            self.goal_row.replaceWidget(self.goal_label, self.goal_edit)
            self.goal_label.hide()
            self.goal_edit.show()
            self.goal_button.setText("✓")
            self.is_editing_goal = True
        else:
            try:
                self.goal_minutes = int(self.goal_edit.text())
            except ValueError:
                pass

            self.goal_row.replaceWidget(self.goal_edit, self.goal_label)
            self.goal_label.setText(f"{self.goal_minutes} mins")
            self.goal_label.show()
            self.goal_edit.hide()

            self.goal_button.setText("⚙")
            self.is_editing_goal = False
            self.save_today()
            self.update_ui()

    # ---------------- Timer Tick ----------------

    def on_tick(self):
        if self.state == "baseline":
            self.elapsed += 1

        elif self.state == "running":
            self.remaining -= 1
            if self.remaining <= 0:
                self.tick.stop()
                self.state = "ringing"
                self.play_beep()
                self.beep_timer.start(4000)

        self.update_ui()

    # ---------------- Sound ----------------

    def play_beep(self):
        self.beep.play()
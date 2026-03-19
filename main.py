import os
# Force Qt to use the native Windows Media Foundation instead of FFmpeg
os.environ["QT_MEDIA_BACKEND"] = "windows"
from PySide6.QtWidgets import (
    QApplication, QFrame, QWidget, QLabel, QPushButton,
    QHBoxLayout, QVBoxLayout, QLineEdit, QInputDialog,
)
from PySide6.QtCore import QTimer, Qt, QUrl
from PySide6.QtMultimedia import QSoundEffect
import json
import sys

class FocusCat(QWidget):
    padding = 20
    def __init__(self):
        super().__init__()

        self.state = "startup"
        self.attention_span = None
        self.goal_minutes = 60
        self.remaining = 0
        self.sessions = []

        self.load_or_create_today()
        self.build_ui()
        self.update_ui()

        self.tick = QTimer()
        self.tick.timeout.connect(self.on_tick)

        self.beep_timer = QTimer()
        self.beep_timer.timeout.connect(self.play_beep)

        QTimer.singleShot(0, self.init_sound)


    # -------------- sound ---------------
    def resource_path(self, relative_path):
        """ Get absolute path to resource, works for dev and for PyInstaller """
        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")

        return os.path.join(base_path, relative_path)
    
    def init_sound(self):
        self.beep = QSoundEffect(self)
        self.beep.setSource(QUrl.fromLocalFile(self.resource_path("beep.wav")))
        self.beep.setLoopCount(1)
        self.beep.setVolume(1.0)

    # ---------------- UI ----------------

    def build_ui(self):
        self.setWindowTitle("Focus Cat")
        self.resize(480, 160)

        # Cat
        self.cat = QLabel("/ᐠ– ˕ –ᐟ\\")
        self.cat.setAlignment(Qt.AlignCenter)
        self.cat.setStyleSheet("font-family: 'monospace'; font-size: 20px;")
        self.encouragement = QLabel("You got this.")
        self.encouragement.setWordWrap(True)
        self.encouragement.setMinimumHeight(30)
        self.encouragement.setAlignment(Qt.AlignTop)

        # Timer
        self.timer_label = QLabel("00:00")
        self.timer_label.setAlignment(Qt.AlignCenter)
        self.timer_label.setStyleSheet("font-size: 32px; font-weight: bold;")

        # Baseline buttons
        self.btn_start_baseline = QPushButton("Start baseline")
        self.btn_start_baseline.clicked.connect(self.start_baseline)

        self.btn_stop_baseline = QPushButton("Stop baseline")
        self.btn_stop_baseline.clicked.connect(self.stop_baseline)

        # Session buttons
        self.btn_start_session = QPushButton("Start session")
        self.btn_start_session.clicked.connect(self.start_session)

        self.btn_pause_session = QPushButton("Pause session")
        self.btn_pause_session.clicked.connect(self.pause_session)

        self.btn_resume_session = QPushButton("Resume session")
        self.btn_resume_session.clicked.connect(self.resume_session)

        self.btn_reset_session = QPushButton("Reset session")
        self.btn_reset_session.clicked.connect(self.reset_session)

        # Ringing button
        self.btn_stop_ringing = QPushButton("Stop ringing")
        self.btn_stop_ringing.clicked.connect(self.stop_ringing)

        # Reset button
        self.reset_button = QPushButton("Reset day")
        self.reset_button.clicked.connect(self.reset_day)                 

        # Manual span
        self.manual_span_button = QPushButton("Set span manually")
        self.manual_span_button.clicked.connect(self.set_span_manually)

        # Stats
        self.stats = QLabel("Sessions: 0")

        # Goal editor
        self.goal_edit = QLineEdit(str(self.goal_minutes))
        self.goal_edit.setFixedWidth(50)
        self.goal_button = QPushButton("⚙")
        self.goal_button.setFixedWidth(30)
        self.goal_button.clicked.connect(self.on_goal_button)
        self.goal_label = QLabel(f"{self.goal_minutes} mins")
        self.is_editing_goal = False

        # Layout
        # cat column
        cat_column = QVBoxLayout()
        cat_column.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        cat_column.addSpacing(self.padding)
        cat_column.addWidget(self.cat)
        cat_column.addSpacing(5)
        cat_column.addWidget(self.encouragement)

        # timer column
        timer_column = QVBoxLayout()
        timer_column.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        timer_column.addSpacing(self.padding)
        timer_column.addWidget(self.timer_label)
        timer_column.addWidget(self.stats)

        # action column
        self.action_column = QVBoxLayout()
        self.action_column.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        self.action_column.setSpacing(5)

        # --- Top row: cat + timer + action buttons ---
        top_row = QHBoxLayout()
        top_row.addSpacing(self.padding)
        top_row.addLayout(cat_column, 1)
        top_row.addSpacing(50)
        top_row.addLayout(timer_column, 1)
        top_row.addSpacing(50)
        top_row.addLayout(self.action_column, 1)
        top_row.addSpacing(self.padding)

        # goal section
        self.goal_row = QHBoxLayout()
        self.goal_row.addWidget(QLabel("Goal:"))
        self.goal_row.addWidget(self.goal_label)
        self.goal_row.addWidget(self.goal_button)
        self.goal_row.addStretch()

        # --- bottom row ---
        bottom_row = QHBoxLayout()
        bottom_row.addSpacing(self.padding)
        bottom_row.addLayout(self.goal_row)
        bottom_row.addStretch()
        bottom_row.addWidget(self.reset_button)
        bottom_row.addSpacing(self.padding)

        # divider
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)

        # --- Main layout ---
        layout = QVBoxLayout()
        layout.addLayout(top_row)
        layout.addSpacing(50)
        layout.addWidget(line)
        layout.addLayout(bottom_row)

        self.setLayout(layout)

    # ---------------- JSON ----------------

    def load_or_create_today(self):
        path = f"focus-today.json"
        if os.path.exists(path):
            with open(path, "r") as f:
                data = json.load(f)
            self.attention_span = data.get("attention_span_seconds")
            self.goal_minutes = data.get("goal_minutes", 60)
            self.sessions = data.get("sessions", [])
        else:
            self.save_today()

        if self.attention_span is None:
            self.state = "no_span"
        else:
            self.state = "idle"

    def save_today(self):
        path = f"focus-today.json"
        data = {
            "attention_span_seconds": self.attention_span,
            "goal_minutes": self.goal_minutes,
            "sessions": self.sessions
        }
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    # ---------------- UI updates ----------------

    def update_ui(self):
        if self.attention_span == None:
            self.stats.setText(f"Sessions: {len(self.sessions)}")
            self.stats.setStyleSheet("color: white")
        else:
            goal_sessions = int(self.goal_minutes// (self.attention_span/60))
            current_sessions = len(self.sessions)
            self.stats.setText(
                f"Sessions: {current_sessions} / {goal_sessions}"
            )
            if current_sessions >= goal_sessions:
                self.stats.setStyleSheet("color: #68ff77")
            else:
                self.stats.setStyleSheet("color: white")                

        if self.state == "no_span":
            self.cat.setText("/`｡ꞈ｡'\\")
            self.encouragement.setText("Let's measure your attention span for today")
            self.timer_label.setText("00:00")
            self.timer_label.setStyleSheet("font-size: 32px; font-weight: bold;")
            self.set_action_column([self.btn_start_baseline, self.manual_span_button])

        elif self.state == "baseline":
            self.cat.setText("/`｡ꞈ｡'\\")
            self.encouragement.setText("Focus time!")
            self.timer_label.setStyleSheet("font-size: 32px; font-weight: bold;")
            self.set_action_column([self.btn_stop_baseline])

        elif self.state == "idle":
            self.cat.setText("/`｡ꞈ｡'\\")
            self.encouragement.setText("Ready when you are")
            m = self.attention_span // 60 if self.attention_span else 0
            s = self.attention_span % 60 if self.attention_span else 0
            self.timer_label.setText(f"{m:02d}:{s:02d}")
            self.timer_label.setStyleSheet("font-size: 32px; font-weight: bold;")
            self.set_action_column([self.btn_start_session])

        elif self.state == "running":
            self.encouragement.setText("Focus time!")
            self.timer_label.setStyleSheet("font-size: 32px; font-weight: bold;")
            self.set_action_column([self.btn_pause_session])

        elif self.state == "paused":
            self.encouragement.setText("I'll be waiting right here")
            self.timer_label.setStyleSheet("font-size: 32px; font-weight: bold; color: grey;")
            self.set_action_column([self.btn_resume_session, self.btn_reset_session])

        elif self.state == "ringing":
            self.cat.setText("/`– ⩊ –'\\")
            self.encouragement.setText("Damn, look at you~")
            self.timer_label.setStyleSheet(
                "font-size: 32px; font-weight: bold; ; color: #68ff77;"
            )
            self.set_action_column([self.btn_stop_ringing])
    # ---------------- Logic ----------------


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

    def cancel_session(self):
        self.tick.stop()
        self.state = "idle"
        self.update_ui()

    def stop_ringing(self):
        self.state = "idle"
        self.sessions.append({"type": "study", "seconds": self.attention_span})
        self.save_today()
        self.update_ui()
        self.beep_timer.stop()

    def on_tick(self):
        if self.state == "baseline":
            self.elapsed += 1
            m = self.elapsed // 60
            s = self.elapsed % 60
            self.timer_label.setText(f"{m:02d}:{s:02d}")

        elif self.state == "running":
            self.remaining -= 1
            m = self.remaining // 60
            s = self.remaining % 60
            self.timer_label.setText(f"{m:02d}:{s:02d}")
            if self.remaining <= 0:
                self.tick.stop()
                self.state = "ringing"
                self.play_beep()
                print("playing beep!")
                self.beep_timer.start(4000)
                self.update_ui()

    # ---------------- Goal editing ----------------

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
            self.goal_label.show()
            self.goal_edit.hide()
            self.goal_button.setText("⚙")
            self.is_editing_goal = False
            self.save_today()
            self.update_ui()

    def reset_day(self):
        self.attention_span = None
        self.sessions = []
        # keep goal_minutes as-is
        self.state = "no_span"
        self.cat.setText("/`– ˕ –'\\")  # sleepy cat
        self.save_today()
        self.update_ui()
        self.manual_span_button.show()
    
    def set_span_manually(self):
        minutes, ok = QInputDialog.getInt(
            self,
            "Set attention span",
            "Minutes:",
            25,  # default
            1,   # min
            300  # max
        )
        if ok:
            self.attention_span = minutes * 60
            self.state = "idle"
            self.save_today()
            self.update_ui()
            self.manual_span_button.hide()

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

    def play_beep(self):
        print(self.beep)
        self.beep.play()
    
    def set_action_column(self, widgets):
        # Clear old widgets
        while self.action_column.count():
            item = self.action_column.takeAt(0)
            if item.widget():
                item.widget().setParent(None)

        # Add new widgets
        self.action_column.addStretch()
        for w in widgets:
            self.action_column.addWidget(w)
        self.action_column.addStretch()



if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = FocusCat()
    w.show()
    sys.exit(app.exec())
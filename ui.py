from PySide6.QtWidgets import (
    QWidget, QLabel, QPushButton, QHBoxLayout, QVBoxLayout,
    QLineEdit, QFrame
)
from PySide6.QtCore import Qt


def build_ui(self):
    self.setWindowTitle("Focus Cat")
    self.resize(480, 160)

    # --- Cat + encouragement ---
    self.cat = QLabel("/`– ˕ –'\\")
    self.cat.setAlignment(Qt.AlignCenter)
    self.cat.setStyleSheet("font-family: monospace; font-size: 20px;")

    self.encouragement = QLabel("You got this.")
    self.encouragement.setWordWrap(True)
    self.encouragement.setMinimumHeight(30)
    self.encouragement.setAlignment(Qt.AlignTop)

    # --- Timer ---
    self.timer_label = QLabel("00:00")
    self.timer_label.setAlignment(Qt.AlignCenter)
    self.timer_label.setStyleSheet("font-size: 32px; font-weight: bold;")

    # --- Stats ---
    self.stats = QLabel("Sessions: 0")

    # --- Goal editor ---
    self.goal_edit = QLineEdit(str(self.goal_minutes))
    self.goal_edit.setFixedWidth(50)
    self.goal_edit.hide()

    self.goal_label = QLabel(f"{self.goal_minutes} mins")
    self.goal_button = QPushButton("⚙")
    self.goal_button.setFixedWidth(30)
    self.goal_button.clicked.connect(self.on_goal_button)
    self.is_editing_goal = False

    # --- Buttons ---
    self.create_buttons()

    # --- Columns ---
    cat_column = column(self, [self.cat, self.encouragement])
    timer_column = column(self, [self.timer_label, self.stats])

    self.action_column = QVBoxLayout()
    self.action_column.setAlignment(Qt.AlignTop)
    self.action_column.setSpacing(5)

    # --- Top row ---
    top_row = QHBoxLayout()
    top_row.addSpacing(self.padding)
    top_row.addLayout(cat_column, 1)
    top_row.addSpacing(50)
    top_row.addLayout(timer_column, 1)
    top_row.addSpacing(50)
    top_row.addLayout(self.action_column, 1)
    top_row.addSpacing(self.padding)

    # --- Goal row ---
    self.goal_row = QHBoxLayout()
    self.goal_row.addWidget(QLabel("Goal:"))
    self.goal_row.addWidget(self.goal_label)
    self.goal_row.addWidget(self.goal_button)
    self.goal_row.addStretch()

    # --- Bottom row ---
    bottom_row = QHBoxLayout()
    bottom_row.addSpacing(self.padding)
    bottom_row.addLayout(self.goal_row)
    bottom_row.addStretch()
    bottom_row.addWidget(self.reset_button)
    bottom_row.addSpacing(self.padding)

    # --- Divider ---
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


def column(self, widgets):
    col = QVBoxLayout()
    col.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
    col.addSpacing(self.padding)
    for w in widgets:
        col.addWidget(w)
    return col
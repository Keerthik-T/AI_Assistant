import sys
import threading
import time

import speech_recognition as sr
from PyQt5.QtCore import (QPoint, QPropertyAnimation, Qt, QThread, QTimer,
                          pyqtSignal)
from PyQt5.QtGui import QBrush, QColor, QPainter, QRadialGradient
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget

# Import ML/Torch modules FIRST to avoid DLL load order conflicts with PyQt5 on Windows
from orchestrator import FurinaOrchestrator
from run_terminal import listen_for_wake_word, play_activation_sound
from stt_engine import STTEngine


class FurinaWorker(QThread):
    state_changed = pyqtSignal(str)  # idle, listening, thinking, speaking

    def __init__(self):
        super().__init__()
        self.orchestrator = None
        self.r = sr.Recognizer()
        self.mic = None
        self.stt = None

    def run(self):
        self.orchestrator = FurinaOrchestrator()
        self.stt = STTEngine()
        self.mic = sr.Microphone()

        # Calibration
        with self.mic as source:
            self.r.adjust_for_ambient_noise(source, duration=2)
            self.r.energy_threshold = max(self.r.energy_threshold, 300)

        self.state_changed.emit("idle")

        while True:
            try:
                # Wait for wake word
                if not listen_for_wake_word(self.r, self.mic):
                    continue

                # Woke up!
                self.state_changed.emit("listening")
                play_activation_sound()

                prompt = self.stt.record_and_transcribe(duration=5.0).strip()
                if not prompt:
                    self.state_changed.emit("idle")
                    continue

                self.state_changed.emit("thinking")

                # Pass callback so UI updates right before she speaks
                def on_speak():
                    self.state_changed.emit("speaking")

                result = self.orchestrator.route_and_execute(
                    prompt, on_speak_callback=on_speak
                )

                self.state_changed.emit("idle")

            except Exception as e:
                print(f"Error in Furina loop: {e}")
                self.state_changed.emit("idle")
                time.sleep(1)


class OrbWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.pulse_radius = 50
        self.max_radius = 60
        self.min_radius = 45
        self.pulse_dir = 1

        # Colors: Blue (idle), Green (listening), Purple (thinking), Cyan (speaking)
        self.current_color = QColor(0, 100, 255, 200)
        self.target_color = self.current_color

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.pulse_speed = 1
        self.timer.start(30)

    def set_state(self, state):
        if state == "idle":
            self.target_color = QColor(0, 100, 255, 200)  # Deep Hydro Blue
            self.pulse_speed = 0.5
        elif state == "listening":
            self.target_color = QColor(50, 255, 100, 255)  # Bright Green
            self.pulse_speed = 3
        elif state == "thinking":
            self.target_color = QColor(180, 50, 255, 230)  # Mystical Purple
            self.pulse_speed = 1.5
        elif state == "speaking":
            self.target_color = QColor(0, 255, 255, 255)  # Bright Cyan/White
            self.pulse_speed = 5

    def animate(self):
        # Pulse animation
        self.pulse_radius += self.pulse_dir * self.pulse_speed
        if self.pulse_radius >= self.max_radius:
            self.pulse_dir = -1
        elif self.pulse_radius <= self.min_radius:
            self.pulse_dir = 1

        # Color transition (lerp)
        r = (
            self.current_color.red()
            + (self.target_color.red() - self.current_color.red()) * 0.1
        )
        g = (
            self.current_color.green()
            + (self.target_color.green() - self.current_color.green()) * 0.1
        )
        b = (
            self.current_color.blue()
            + (self.target_color.blue() - self.current_color.blue()) * 0.1
        )
        a = (
            self.current_color.alpha()
            + (self.target_color.alpha() - self.current_color.alpha()) * 0.1
        )
        self.current_color = QColor(int(r), int(g), int(b), int(a))

        self.update()  # trigger paintEvent

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        center = self.rect().center()

        # Outer glow
        gradient = QRadialGradient(center, self.pulse_radius)
        gradient.setColorAt(0, self.current_color)
        gradient.setColorAt(
            0.8,
            QColor(
                self.current_color.red(),
                self.current_color.green(),
                self.current_color.blue(),
                50,
            ),
        )
        gradient.setColorAt(1, QColor(0, 0, 0, 0))

        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(center, int(self.pulse_radius), int(self.pulse_radius))

        # Inner solid core
        core_radius = self.pulse_radius * 0.6
        painter.setBrush(QBrush(self.current_color))
        painter.drawEllipse(center, int(core_radius), int(core_radius))


class FurinaDesktopApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(150, 150)

        # Position in bottom right corner
        screen = QApplication.primaryScreen().geometry()
        self.move(screen.width() - 200, screen.height() - 200)

        self.orb = OrbWidget(self)
        self.setCentralWidget(self.orb)

        # Dragging variables
        self.old_pos = self.pos()

        # Start backend thread
        self.worker = FurinaWorker()
        self.worker.state_changed.connect(self.orb.set_state)
        self.worker.start()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.old_pos = event.globalPos()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            delta = QPoint(event.globalPos() - self.old_pos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPos()

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            QApplication.quit()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FurinaDesktopApp()
    window.show()
    sys.exit(app.exec_())

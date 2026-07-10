#!/usr/bin/env python3
"""
WebDev IDE - Professional PySide6-based IDE for HTML/CSS/JavaScript development
Features:
- Multi-tab code editor with syntax highlighting
- File explorer sidebar
- Search and replace with regex support
- HTML live preview
- Integrated terminal/output panel
- AI assistant integration (Ollama, Qwen, OpenAI)
- Modern Material Design UI with smooth animations
- Professional AI panel with animated colorful logo
- Configurable themes and settings
"""

import sys
import os
import re
import json
import random
import webbrowser
import subprocess
import threading
import queue
from pathlib import Path
from datetime import datetime

from dataclasses import dataclass, field
from typing import List, Optional

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
    QTextBrowser,
    QTextEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QSplitter,
    QLabel,
    QPushButton,
    QDialog,
    QLineEdit,
    QCheckBox,
    QSpinBox,
    QDoubleSpinBox,
    QComboBox,
    QFileDialog,
    QMessageBox,
    QFrame,
    QScrollArea,
    QProgressBar,
    QListWidget,
    QListWidgetItem,
    QHeaderView,
    QTableWidget,
    QTableWidgetItem,
    QStatusBar,
    QMenuBar,
    QMenu,
    QToolBar,
    QInputDialog,
    QFontComboBox,
    QButtonGroup,
    QSplashScreen,
    QGraphicsDropShadowEffect,
)
from PySide6.QtCore import (
    Qt,
    QTimer,
    QThread,
    Signal,
    Slot,
    QObject,
    QUrl,
    QSize,
    QRect,
    QPoint,
    QPropertyAnimation,
    QEasingCurve,
    QSequentialAnimationGroup,
    QParallelAnimationGroup,
    QVariantAnimation,
    QPointF,
    QRectF,
    QFileSystemWatcher,
)
from PySide6.QtGui import (
    QFont,
    QColor,
    QIcon,
    QPixmap,
    QPalette,
    QTextCursor,
    QSyntaxHighlighter,
    QTextDocument,
    QTextCharFormat,
    QAction,
    QActionGroup,
    QKeySequence,
    QShortcut,
    QPainter,
    QBrush,
    QPen,
    QRadialGradient,
    QConicalGradient,
    QTextOption,
    QLinearGradient,
    QPolygonF,
)

# Try to import optional dependencies
try:
    import ollama

    HAS_OLLAMA = True
except ImportError:
    HAS_OLLAMA = False

try:
    import requests

    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


AGENT_SYSTEM_PROMPT = """You are an Autonomous Senior Software Engineer Agent with access to the user's workspace.
You can perform actions on the local computer by wrapping instructions inside specific tool blocks.

AVAILABLE TOOLS:

1. READ DIRECTORY: To see all files in the active workspace.
   <tool_list_dir/>

2. CREATE / OVERWRITE FILE: Write out full files directly to a specific target path.
   <tool_write_file path="relative/path/to/file.js">
   [Full code content here]
   </tool_write_file>

3. RUN TERMINAL COMMAND: Execute build scripts, install npm tools, or run diagnostics.
   <tool_run_command>
   npm run build
   </tool_run_command>
   this is just an example of how you are going to run commands!

RULES:
- When using a tool block, do  explain what you are doing inside the block. DONT write the tag .
- After a command finishes executing, you will see a [SYSTEM TELEMETRY] message containing the output or errors(if it has errors). Analyze it, speak out what error or warning is, tell me how are you going to fix it, fix any issues, and use more tools if required!
"""
# ============================================================================
# Visual system
# ============================================================================


class ThemeManager:
    """Central dark-theme tokens used by the IDE's persistent UI surfaces.

    The project predates this manager and has a number of component-level
    stylesheets. ``resolve`` lets those styles migrate to named tokens without
    changing widget behaviour or the existing visual hierarchy.
    """

    TOKENS = {
        "window": "#10131a",
        "panel": "#171b24",
        "toolbar": "#1d2330",
        "control": "#262d3a",
        "control_hover": "#313a49",
        "border": "#394353",
        "border_subtle": "#0b0e14",
        "text": "#c7d0dd",
        "text_primary": "#e7edf5",
        "text_strong": "#f7fbff",
        "text_muted": "#92a0b3",
        "accent": "#4aa3ff",
        "accent_hover": "#73bdff",
        "accent_dark": "#2877d4",
        "accent_pressed": "#1c5fae",
        "selection": "#1d4d77",
        "editor_selection": "#234f78",
        "danger": "#ff5d73",
        "success": "#67c587",
    }

    _LEGACY_COLORS = {
        "#1e1e1e": "window",
        "#252526": "panel",
        "#2d2d2d": "toolbar",
        "#3c3c3c": "control",
        "#3e3e42": "control_hover",
        "#454545": "border",
        "#1a1a1a": "border_subtle",
        "#cccccc": "text",
        "#d4d4d4": "text_primary",
        "#ffffff": "text_strong",
        "#aaaaaa": "text_muted",
        "#007acc": "accent",
        "#1177bb": "accent_hover",
        "#0e639c": "accent_dark",
        "#0a4d7d": "accent_pressed",
        "#094771": "selection",
        "#264f78": "editor_selection",
        "#e81123": "danger",
        "#6a9955": "success",
        "#323233": "toolbar",
        "#4a4a4d": "control_hover",
    }

    @classmethod
    def color(cls, name):
        return cls.TOKENS[name]

    @classmethod
    def resolve(cls, stylesheet):
        """Replace legacy literals with the canonical visual-system tokens."""
        for legacy, token in cls._LEGACY_COLORS.items():
            stylesheet = stylesheet.replace(legacy, cls.color(token))
        return stylesheet

    @classmethod
    def apply_application_palette(cls, app):
        """Set Qt defaults so native dialogs match the stylesheet surfaces."""
        palette = app.palette()
        palette.setColor(QPalette.Window, QColor(cls.color("window")))
        palette.setColor(QPalette.WindowText, QColor(cls.color("text")))
        palette.setColor(QPalette.Base, QColor(cls.color("window")))
        palette.setColor(QPalette.AlternateBase, QColor(cls.color("panel")))
        palette.setColor(QPalette.Text, QColor(cls.color("text_primary")))
        palette.setColor(QPalette.Button, QColor(cls.color("toolbar")))
        palette.setColor(QPalette.ButtonText, QColor(cls.color("text")))
        palette.setColor(QPalette.Highlight, QColor(cls.color("selection")))
        palette.setColor(QPalette.HighlightedText, QColor(cls.color("text_strong")))
        app.setPalette(palette)


class FluidButton(QPushButton):
    """Button with a subtle macOS-like elevation transition on hover."""

    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self._shadow = QGraphicsDropShadowEffect(self)
        self._shadow.setBlurRadius(0)
        self._shadow.setOffset(0, 2)
        self._shadow.setColor(QColor(74, 163, 255, 0))
        self.setGraphicsEffect(self._shadow)

        self._shadow_animation = QPropertyAnimation(self._shadow, b"blurRadius", self)
        self._shadow_animation.setDuration(160)
        self._shadow_animation.setEasingCurve(QEasingCurve.OutCubic)

    def _animate_elevation(self, blur_radius, alpha):
        self._shadow_animation.stop()
        self._shadow_animation.setStartValue(self._shadow.blurRadius())
        self._shadow_animation.setEndValue(blur_radius)
        self._shadow.setColor(QColor(74, 163, 255, alpha))
        self._shadow_animation.start()

    def enterEvent(self, event):
        if self.isEnabled():
            self._animate_elevation(14, 95)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._animate_elevation(0, 0)
        super().leaveEvent(event)


# ============================================================================
# Splash Screen
# ============================================================================


class SplashScreen(QSplashScreen):
    """Custom splash screen that displays splash.png for 2.5 seconds"""

    def __init__(self):
        # Try to load splash.png from the current directory or script directory
        splash_paths = [
            "splash.png",
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "splash.png"),
            os.path.join(os.getcwd(), "splash.png"),
        ]

        pixmap = None
        for path in splash_paths:
            if os.path.exists(path):
                pixmap = QPixmap(path)
                if not pixmap.isNull():
                    break

        # If splash.png not found, create a simple default splash
        if pixmap is None or pixmap.isNull():
            pixmap = QPixmap(600, 400)
            pixmap.fill(QColor(45, 45, 48))  # Dark background

            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.Antialiasing)

            # Draw a gradient background
            gradient = QLinearGradient(0, 0, 600, 400)
            gradient.setColorAt(0, QColor(66, 133, 244))
            gradient.setColorAt(1, QColor(52, 168, 224))
            painter.fillRect(0, 0, 600, 400, QBrush(gradient))

            # Draw application name
            painter.setPen(QColor(255, 255, 255))
            font = QFont("Arial", 36, QFont.Bold)
            painter.setFont(font)
            painter.drawText(pixmap.rect(), Qt.AlignCenter, "WebDev IDE")

            painter.end()

        super().__init__(pixmap, Qt.WindowStaysOnTopHint)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)


# ============================================================================
# Custom Widgets - Animated Logo
# ============================================================================

import math as _math

# ============================================================================
# Particle System for Star Effects
# ============================================================================


class Particle:
    """Individual particle (star) for visual effects"""

    def __init__(self, x, y, vx, vy, life=1.0, color=None):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.life = life
        self.max_life = life
        self.color = color or QColor(150, 200, 255)
        self.scale = 1.0

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.life -= dt
        self.scale = self.life / self.max_life

    def is_alive(self):
        return self.life > 0

    def get_alpha(self):
        # Fade out at the end
        return int(255 * max(0, self.life / self.max_life))


class ParticleSystem(QWidget):
    """Particle system for star pop-ups and effects"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.particles = []
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.setStyleSheet("background: transparent;")

        self.timer = QTimer()
        self.timer.timeout.connect(self._update_particles)
        self.timer.start(16)  # 60fps

    def emit_stars(self, x, y, count=8, colors=None):
        """Emit particles (stars) from a position"""
        if colors is None:
            colors = [
                QColor(100, 200, 255),  # Cyan
                QColor(150, 100, 255),  # Purple
                QColor(255, 150, 200),  # Pink
                QColor(100, 255, 200),  # Mint
                QColor(255, 200, 100),  # Orange
            ]

        for i in range(count):
            angle = (i / count) * _math.pi * 2 + random.uniform(-0.3, 0.3)
            speed = random.uniform(80, 150)
            vx = _math.cos(angle) * speed
            vy = _math.sin(angle) * speed
            color = random.choice(colors)

            particle = Particle(x, y, vx, vy, life=0.6, color=color)
            self.particles.append(particle)

    def _update_particles(self):
        dt = 0.016
        for particle in self.particles[:]:
            particle.update(dt)
            if not particle.is_alive():
                self.particles.remove(particle)

        if self.particles:
            self.update()

    def paintEvent(self, event):
        if not self.particles:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        for particle in self.particles:
            size = 4 + 2 * particle.scale
            particle.color.setAlpha(particle.get_alpha())
            painter.setBrush(QBrush(particle.color))
            painter.setPen(Qt.NoPen)

            # Draw star shape
            self._draw_star(painter, particle.x, particle.y, size * particle.scale)

    def _draw_star(self, painter, cx, cy, size):
        """Draw a 5-pointed star"""
        points = []
        for i in range(10):
            angle = (_math.pi / 2) + (i * _math.pi / 5)
            r = size if i % 2 == 0 else size * 0.4
            x = cx + r * _math.cos(angle)
            y = cy - r * _math.sin(angle)
            points.append(QPointF(x, y))

        star_path = painter.font().pointSize()  # placeholder
        painter.drawPolygon(points)

    def closeEvent(self, event):
        self.timer.stop()
        super().closeEvent(event)


class AnimatedAILogo(QWidget):
    """
    ENHANCED AI logo with three animation states (60fps):
      idle       – calm orbiting orbs with breathe effect
      thinking   – fast spinning arcs with pulsing core
      generating – outward ripples with spinning dots
    Features: Smooth animations, gradient effects, state transitions
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(80, 80)
        self.setMaximumSize(120, 120)
        self._mode = "idle"
        self._t = 0.0
        self._ripples = []
        self._state_transition = 0.0  # Smooth state transitions
        self._previous_mode = "idle"
        self.hover_state = 0.0

        self._timer = QTimer()
        self._timer.timeout.connect(self._tick)
        self._timer.start(16)  # 60 fps

    def set_state(self, mode: str):
        if mode == self._mode:
            return
        self._previous_mode = self._mode
        self._mode = mode
        self._state_transition = 0.0
        if mode == "generating":
            self._ripples = []
        self.update()

    def enterEvent(self, event):
        self.hover_state = min(1.0, self.hover_state + 0.15)
        self.update()

    def leaveEvent(self, event):
        self.hover_state = max(0.0, self.hover_state - 0.15)
        self.update()

    def _tick(self):
        dt = 0.016
        self._t += dt
        self._state_transition = min(1.0, self._state_transition + dt * 2)

        if self._mode == "generating":
            if int(self._t / 0.35) > int((self._t - dt) / 0.35):
                self._ripples.append(0.0)
            self._ripples = [r + dt for r in self._ripples if r + dt < 1.3]

        self.update()

    def closeEvent(self, event):
        self._timer.stop()
        super().closeEvent(event)

    def __del__(self):
        try:
            if hasattr(self, "_timer") and self._timer:
                self._timer.stop()
        except (RuntimeError, AttributeError):
            pass

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.SmoothPixmapTransform)

        # Draw background with hover effect
        self._draw_background(p)

        if self._mode == "idle":
            self._draw_idle(p)
        elif self._mode == "thinking":
            self._draw_thinking(p)
        else:
            self._draw_generating(p)
        p.end()

    def _cx_cy(self):
        return self.width() / 2, self.height() / 2

    def _max_r(self):
        return min(self.width(), self.height()) * 0.38

    def _draw_background(self, p):
        """Draw animated background"""
        cx, cy = self._cx_cy()
        mr = self._max_r()

        # Base background
        bg_color = QColor(20, 20, 35)
        p.fillRect(self.rect(), bg_color)

        # Animated gradient background based on mode
        if self._mode == "idle":
            grad = QRadialGradient(cx, cy, mr * 1.2)
            grad.setColorAt(0, QColor(25, 35, 50, 100))
            grad.setColorAt(1, QColor(15, 15, 25, 200))
        elif self._mode == "thinking":
            grad = QRadialGradient(cx, cy, mr * 1.2)
            grad.setColorAt(0, QColor(50, 30, 15, 120))
            grad.setColorAt(1, QColor(20, 15, 20, 200))
        else:  # generating
            grad = QRadialGradient(cx, cy, mr * 1.2)
            grad.setColorAt(0, QColor(20, 40, 60, 120))
            grad.setColorAt(1, QColor(10, 20, 35, 200))

        p.setBrush(QBrush(grad))
        p.setPen(Qt.NoPen)
        p.drawEllipse(QRectF(cx - mr * 1.15, cy - mr * 1.15, mr * 2.3, mr * 2.3))

        # Hover effect - outer ring
        if self.hover_state > 0:
            hover_alpha = int(100 * self.hover_state)
            hover_pen = QPen(QColor(100, 180, 255, hover_alpha), 1.5)
            p.setPen(hover_pen)
            p.setBrush(Qt.NoBrush)
            p.drawEllipse(QRectF(cx - mr * 1.2, cy - mr * 1.2, mr * 2.4, mr * 2.4))

    def _draw_idle(self, p):
        """Draw idle state with smooth orbiting orbs"""
        cx, cy = self._cx_cy()
        mr = self._max_r()

        orb_colors = [
            QColor(100, 180, 255),  # Bright cyan
            QColor(150, 120, 255),  # Purple
            QColor(80, 220, 200),  # Mint
        ]
        orbit_r = mr * 0.65
        speed = 0.35

        # Draw orbital paths (faint)
        p.setPen(QPen(QColor(100, 150, 200, 30), 0.5))
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(QRectF(cx - orbit_r, cy - orbit_r, orbit_r * 2, orbit_r * 2))

        # Draw orbiting orbs
        for i, col in enumerate(orb_colors):
            angle = self._t * speed + i * (_math.pi * 2 / 3)
            ox = cx + orbit_r * _math.cos(angle)
            oy = cy + orbit_r * _math.sin(angle)

            # Enhanced glow with gradient
            glow = QRadialGradient(ox, oy, 15)
            gc = QColor(col)
            gc.setAlpha(80)
            glow.setColorAt(0, gc)
            glow.setColorAt(0.6, QColor(col.red(), col.green(), col.blue(), 40))
            glow.setColorAt(1, QColor(0, 0, 0, 0))
            p.setBrush(QBrush(glow))
            p.setPen(Qt.NoPen)
            p.drawEllipse(QRectF(ox - 15, oy - 15, 30, 30))

            # Breathing core
            orb_r = 3.8 + 1.8 * _math.sin(self._t * 1.6 + i * 1.2)
            p.setBrush(QBrush(col))
            p.drawEllipse(QRectF(ox - orb_r, oy - orb_r, orb_r * 2, orb_r * 2))

            # Highlight
            p.setBrush(QBrush(QColor(255, 255, 255, 100)))
            p.drawEllipse(
                QRectF(ox - orb_r * 0.4, oy - orb_r * 0.4, orb_r * 0.8, orb_r * 0.8)
            )

        # Pulsing center
        cr = 6 + 2.5 * _math.sin(self._t * 0.8)
        cg = QRadialGradient(cx, cy, cr * 2)
        cg.setColorAt(0, QColor(200, 230, 255, 240))
        cg.setColorAt(0.5, QColor(100, 160, 255, 100))
        cg.setColorAt(1, QColor(50, 100, 200, 0))
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(cg))
        p.drawEllipse(QRectF(cx - cr * 2, cy - cr * 2, cr * 4, cr * 4))

    def _draw_thinking(self, p):
        """Draw thinking state with fast spinning arcs"""
        cx, cy = self._cx_cy()
        mr = self._max_r()

        # Multiple rotating rings with different speeds
        rings = [
            (mr * 0.85, 3.5, QColor(255, 160, 40), 140),
            (mr * 0.60, -2.8, QColor(255, 220, 80), 100),
            (mr * 0.35, 5.2, QColor(255, 110, 60), 70),
        ]

        for radius, spd, col, span in rings:
            start_deg = (_math.degrees(self._t * spd)) % 360

            # Main arc
            pen = QPen(col, 3, Qt.SolidLine, Qt.RoundCap)
            p.setPen(pen)
            p.setBrush(Qt.NoBrush)
            rect = QRectF(cx - radius, cy - radius, radius * 2, radius * 2)
            p.drawArc(rect, int(start_deg * 16), int(span * 16))

            # Ghost arc
            ghost_col = QColor(col.red(), col.green(), col.blue(), 80)
            p.setPen(QPen(ghost_col, 1.5, Qt.SolidLine, Qt.RoundCap))
            p.drawArc(rect, int((start_deg + 180) * 16), int(span // 2 * 16))

        # Frantic center pulse with glow
        pulse = abs(_math.sin(self._t * 10))
        cr = 5 + 4 * pulse

        # Outer glow
        glow = QRadialGradient(cx, cy, cr * 2.5)
        glow.setColorAt(0, QColor(255, 200, 80, 150))
        glow.setColorAt(0.5, QColor(255, 100, 30, 80))
        glow.setColorAt(1, QColor(255, 50, 0, 0))
        p.setBrush(QBrush(glow))
        p.setPen(Qt.NoPen)
        p.drawEllipse(QRectF(cx - cr * 2.5, cy - cr * 2.5, cr * 5, cr * 5))

        # Inner bright core
        cg = QRadialGradient(cx, cy, cr)
        cg.setColorAt(0, QColor(255, 230, 100, 255))
        cg.setColorAt(0.7, QColor(255, 150, 50, 200))
        cg.setColorAt(1, QColor(255, 80, 20, 0))
        p.setBrush(QBrush(cg))
        p.drawEllipse(QRectF(cx - cr, cy - cr, cr * 2, cr * 2))

    def _draw_generating(self, p):
        """Draw generating state with ripples and dots"""
        cx, cy = self._cx_cy()
        mr = self._max_r()

        # Expanding ripple rings
        for age in self._ripples:
            prog = age / 1.3
            ring_r = prog * mr * 1.1
            alpha = int(255 * (1 - prog) ** 2.5)

            # Color gradient for ripple
            r_val = int(50 + 100 * _math.sin(prog * _math.pi))
            g_val = int(160 + 90 * prog)
            b_val = 255

            col = QColor(r_val, g_val, b_val, alpha)
            pen_w = max(0.6, 3 * (1 - prog))
            p.setPen(QPen(col, pen_w))
            p.setBrush(Qt.NoBrush)
            p.drawEllipse(QRectF(cx - ring_r, cy - ring_r, ring_r * 2, ring_r * 2))

        # Spinning dots with color shift
        dot_r = mr * 0.50
        spd = 3.0
        dot_colors = [
            QColor(80, 220, 255),
            QColor(150, 200, 255),
            QColor(200, 150, 255),
        ]

        for i in range(3):
            angle = self._t * spd + i * (_math.pi * 2 / 3)
            dx = cx + dot_r * _math.cos(angle)
            dy = cy + dot_r * _math.sin(angle)
            da = int(180 + 75 * _math.sin(self._t * 5.5 + i * 2.1))

            # Dot with glow
            glow = QRadialGradient(dx, dy, 6)
            glow.setColorAt(
                0,
                QColor(
                    dot_colors[i].red(), dot_colors[i].green(), dot_colors[i].blue(), da
                ),
            )
            glow.setColorAt(
                1,
                QColor(
                    dot_colors[i].red(), dot_colors[i].green(), dot_colors[i].blue(), 50
                ),
            )
            p.setBrush(QBrush(glow))
            p.setPen(Qt.NoPen)
            p.drawEllipse(QRectF(dx - 5, dy - 5, 10, 10))

        # Glowing center with dual gradient
        gr = mr * 0.35
        cg = QRadialGradient(cx, cy, gr * 1.5)
        cg.setColorAt(0, QColor(150, 240, 255, 230))
        cg.setColorAt(0.5, QColor(50, 180, 255, 120))
        cg.setColorAt(1, QColor(0, 100, 200, 0))
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(cg))
        p.drawEllipse(QRectF(cx - gr * 1.5, cy - gr * 1.5, gr * 3, gr * 3))


class WaterfallAnimation(QWidget):
    """Smooth 60fps waterfall animation overlay"""

    finished = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)

        # Droplet system
        self.droplets = []
        self.num_droplets = 150
        self.init_droplets()

        # Animation progress
        self.progress = 0
        self.max_progress = 120  # ~2 seconds at 60fps

        # Timer for 60fps
        self.timer = QTimer()
        self.timer.timeout.connect(self.animate)

    def init_droplets(self):
        """Initialize waterfall droplets"""
        import random

        self.droplets = []
        for i in range(self.num_droplets):
            self.droplets.append(
                {
                    "x": random.randint(0, 100),  # Percentage
                    "y": random.randint(-50, 0),  # Start above screen
                    "speed": random.uniform(2, 5),
                    "length": random.randint(20, 60),
                    "delay": random.randint(0, 30),
                }
            )

    def start(self):
        """Start waterfall animation"""
        if self.parent():
            self.setGeometry(self.parent().rect())
        self.show()
        self.raise_()
        self.timer.start(16)  # ~60fps (16ms)

    def animate(self):
        """Animate droplets falling"""
        import random

        for droplet in self.droplets:
            if droplet["delay"] > 0:
                droplet["delay"] -= 1
                continue

            droplet["y"] += droplet["speed"]

            # Reset droplet if it falls off screen
            if droplet["y"] > 110:
                droplet["y"] = random.randint(-50, -10)
                droplet["x"] = random.randint(0, 100)

        self.progress += 1
        self.update()

        # Finish animation
        if self.progress >= self.max_progress:
            self.timer.stop()
            self.finished.emit()
            self.close()

    def paintEvent(self, event):
        """Draw waterfall droplets"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Semi-transparent background
        opacity = min(255, self.progress * 4)
        painter.fillRect(self.rect(), QColor(0, 0, 0, opacity))

        # Draw droplets
        w, h = self.width(), self.height()

        for droplet in self.droplets:
            if droplet["delay"] > 0:
                continue

            x = int(w * droplet["x"] / 100)
            y = int(h * droplet["y"] / 100)
            length = droplet["length"]

            # Gradient from transparent to blue-white
            gradient = QLinearGradient(x, y, x, y + length)
            gradient.setColorAt(0, QColor(135, 206, 250, 0))  # Transparent
            gradient.setColorAt(0.5, QColor(135, 206, 250, 180))  # Sky blue
            gradient.setColorAt(1, QColor(255, 255, 255, 220))  # White

            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(gradient))
            painter.drawRoundedRect(x - 2, y, 4, length, 2, 2)

        painter.end()


# ============================================================================
# Syntax Highlighter
# ============================================================================


class CodeHighlighter(QSyntaxHighlighter):
    """Enhanced syntax highlighter with multiple theme support"""

    # Popular IDE themes
    THEMES = {
        "VS Code Dark+": {
            "keyword": "#C586C0",
            "string": "#CE9178",
            "comment": "#6A9955",
            "number": "#B5CEA8",
            "function": "#DCDCAA",
            "class": "#4EC9B0",
            "tag": "#569CD6",
            "attribute": "#9CDCFE",
            "operator": "#D4D4D4",
            "variable": "#9CDCFE",
            "constant": "#4FC1FF",
            "decorator": "#C586C0",
        },
        "Monokai": {
            "keyword": "#F92672",
            "string": "#E6DB74",
            "comment": "#75715E",
            "number": "#AE81FF",
            "function": "#A6E22E",
            "class": "#66D9EF",
            "tag": "#F92672",
            "attribute": "#A6E22E",
            "operator": "#F92672",
            "variable": "#FD971F",
            "constant": "#AE81FF",
            "decorator": "#66D9EF",
        },
        "Dracula": {
            "keyword": "#FF79C6",
            "string": "#F1FA8C",
            "comment": "#6272A4",
            "number": "#BD93F9",
            "function": "#50FA7B",
            "class": "#8BE9FD",
            "tag": "#FF79C6",
            "attribute": "#50FA7B",
            "operator": "#FF79C6",
            "variable": "#F8F8F2",
            "constant": "#BD93F9",
            "decorator": "#8BE9FD",
        },
        "One Dark": {
            "keyword": "#C678DD",
            "string": "#98C379",
            "comment": "#5C6370",
            "number": "#D19A66",
            "function": "#61AFEF",
            "class": "#E5C07B",
            "tag": "#E06C75",
            "attribute": "#D19A66",
            "operator": "#ABB2BF",
            "variable": "#E06C75",
            "constant": "#D19A66",
            "decorator": "#C678DD",
        },
        "GitHub Dark": {
            "keyword": "#FF7B72",
            "string": "#A5D6FF",
            "comment": "#8B949E",
            "number": "#79C0FF",
            "function": "#D2A8FF",
            "class": "#FFA657",
            "tag": "#7EE787",
            "attribute": "#79C0FF",
            "operator": "#FF7B72",
            "variable": "#FFA657",
            "constant": "#79C0FF",
            "decorator": "#FF7B72",
        },
        "Tokyo Night": {
            "keyword": "#BB9AF7",
            "string": "#9ECE6A",
            "comment": "#565F89",
            "number": "#FF9E64",
            "function": "#7AA2F7",
            "class": "#2AC3DE",
            "tag": "#F7768E",
            "attribute": "#BB9AF7",
            "operator": "#89DDFF",
            "variable": "#7DCFFF",
            "constant": "#FF9E64",
            "decorator": "#BB9AF7",
        },
    }

    def __init__(self, document, language="html", theme="VS Code Dark+"):
        super().__init__(document)
        self.language = language
        self.theme = theme
        self.setup_formats()

    def set_theme(self, theme_name):
        """Change the color theme"""
        if theme_name in self.THEMES:
            self.theme = theme_name
            self.setup_formats()
            self.rehighlight()

    def setup_formats(self):
        """Setup text formats based on current theme"""
        self.formats = {}
        colors = self.THEMES.get(self.theme, self.THEMES["VS Code Dark+"])

        for token_type, color in colors.items():
            fmt = QTextCharFormat()
            fmt.setForeground(QColor(color))
            if token_type in ["keyword", "tag", "class"]:
                fmt.setFontWeight(QFont.Bold)
            if token_type == "comment":
                fmt.setFontItalic(True)
            self.formats[token_type] = fmt

    def highlightBlock(self, text):
        """Highlight a code block with enhanced syntax detection"""
        if self.language == "html":
            self.highlight_html(text)
        elif self.language == "css":
            self.highlight_css(text)
        elif self.language == "javascript":
            self.highlight_javascript(text)
        else:
            # Generic highlighting
            self.highlight_generic(text)

    def highlight_html(self, text):
        """Enhanced HTML highlighting"""
        # Comments
        for match in re.finditer(r"<!--.*?-->", text):
            self.setFormat(
                match.start(), match.end() - match.start(), self.formats.get("comment")
            )

        # Tags with attributes
        for match in re.finditer(r"</?([a-zA-Z][a-zA-Z0-9]*)", text):
            self.setFormat(
                match.start(), match.end() - match.start(), self.formats.get("tag")
            )

        # Attributes
        for match in re.finditer(r"\b([a-zA-Z-]+)(?=\s*=)", text):
            self.setFormat(
                match.start(),
                match.end() - match.start(),
                self.formats.get("attribute"),
            )

        # String values in quotes
        for match in re.finditer(r'"[^"]*"', text):
            self.setFormat(
                match.start(), match.end() - match.start(), self.formats.get("string")
            )
        for match in re.finditer(r"'[^']*'", text):
            self.setFormat(
                match.start(), match.end() - match.start(), self.formats.get("string")
            )

    def highlight_css(self, text):
        """Enhanced CSS highlighting"""
        # Comments
        for match in re.finditer(r"/\*.*?\*/", text):
            self.setFormat(
                match.start(), match.end() - match.start(), self.formats.get("comment")
            )

        # Selectors (class, id, element)
        for match in re.finditer(r"\.[a-zA-Z][a-zA-Z0-9_-]*", text):
            self.setFormat(
                match.start(), match.end() - match.start(), self.formats.get("class")
            )
        for match in re.finditer(r"#[a-zA-Z][a-zA-Z0-9_-]*", text):
            self.setFormat(
                match.start(), match.end() - match.start(), self.formats.get("constant")
            )

        # Properties
        for match in re.finditer(r"[a-z-]+(?=\s*:)", text):
            self.setFormat(
                match.start(),
                match.end() - match.start(),
                self.formats.get("attribute"),
            )

        # Values (strings, numbers, colors)
        for match in re.finditer(r'"[^"]*"', text):
            self.setFormat(
                match.start(), match.end() - match.start(), self.formats.get("string")
            )
        for match in re.finditer(r"'[^']*'", text):
            self.setFormat(
                match.start(), match.end() - match.start(), self.formats.get("string")
            )
        for match in re.finditer(r"\b\d+(\.\d+)?(px|em|rem|%|vh|vw|pt)?\b", text):
            self.setFormat(
                match.start(), match.end() - match.start(), self.formats.get("number")
            )
        for match in re.finditer(r"#[0-9A-Fa-f]{3,6}\b", text):
            self.setFormat(
                match.start(), match.end() - match.start(), self.formats.get("number")
            )

    def highlight_javascript(self, text):
        """Enhanced JavaScript highlighting"""
        # Comments
        for match in re.finditer(r"//.*$", text, re.MULTILINE):
            self.setFormat(
                match.start(), match.end() - match.start(), self.formats.get("comment")
            )
        for match in re.finditer(r"/\*.*?\*/", text, re.DOTALL):
            self.setFormat(
                match.start(), match.end() - match.start(), self.formats.get("comment")
            )

        # Keywords
        keywords = r"\b(const|let|var|function|return|if|else|for|while|do|switch|case|break|continue|class|extends|import|export|from|async|await|try|catch|finally|throw|new|this|super|static|get|set|typeof|instanceof|in|of|delete|void|yield|default)\b"
        for match in re.finditer(keywords, text):
            self.setFormat(
                match.start(), match.end() - match.start(), self.formats.get("keyword")
            )

        # Function names
        for match in re.finditer(r"\b([a-zA-Z_$][a-zA-Z0-9_$]*)\s*\(", text):
            name_start = match.start(1)
            name_end = match.end(1)
            self.setFormat(
                name_end - name_start,
                name_end - name_start,
                self.formats.get("function"),
            )

        # Class names
        for match in re.finditer(r"\bclass\s+([A-Z][a-zA-Z0-9_]*)", text):
            self.setFormat(
                match.start(1), match.end(1) - match.start(1), self.formats.get("class")
            )

        # Strings
        for match in re.finditer(r'"(?:[^"\\]|\\.)*"', text):
            self.setFormat(
                match.start(), match.end() - match.start(), self.formats.get("string")
            )
        for match in re.finditer(r"'(?:[^'\\]|\\.)*'", text):
            self.setFormat(
                match.start(), match.end() - match.start(), self.formats.get("string")
            )
        for match in re.finditer(r"`(?:[^`\\]|\\.)*`", text):
            self.setFormat(
                match.start(), match.end() - match.start(), self.formats.get("string")
            )

        # Numbers
        for match in re.finditer(r"\b\d+\.?\d*([eE][+-]?\d+)?\b", text):
            self.setFormat(
                match.start(), match.end() - match.start(), self.formats.get("number")
            )

        # Constants (UPPERCASE)
        for match in re.finditer(r"\b[A-Z_][A-Z0-9_]{2,}\b", text):
            self.setFormat(
                match.start(), match.end() - match.start(), self.formats.get("constant")
            )

    def highlight_generic(self, text):
        """Generic highlighting for unknown languages"""
        # Comments
        for match in re.finditer(r"#.*$|//.*$", text, re.MULTILINE):
            self.setFormat(
                match.start(), match.end() - match.start(), self.formats.get("comment")
            )

        # Strings
        for match in re.finditer(r'"[^"]*"|\'[^\']*\'', text):
            self.setFormat(
                match.start(), match.end() - match.start(), self.formats.get("string")
            )

        # Numbers
        for match in re.finditer(r"\b\d+\.?\d*\b", text):
            self.setFormat(
                match.start(), match.end() - match.start(), self.formats.get("number")
            )


# ============================================================================
# AI Response Worker Thread
# ============================================================================


class AIWorkerThread(QThread):
    """Worker thread for AI API calls"""

    response_received = Signal(str)
    error_occurred = Signal(str)
    finished_signal = Signal()

    def __init__(self, provider, messages, model, **kwargs):
        super().__init__()
        self.provider = provider
        self.messages = messages
        self.model = model
        self.kwargs = kwargs

    def run(self):
        try:
            if self.provider == "ollama":
                self.call_ollama()
            elif self.provider == "qwen":
                self.call_qwen()
            elif self.provider == "openai":
                self.call_openai()
        except Exception as e:
            self.error_occurred.emit(str(e))
        finally:
            self.finished_signal.emit()

    def call_ollama(self):
        if not HAS_OLLAMA:
            self.error_occurred.emit("Ollama not installed")
            return

        try:
            stream = ollama.chat(model=self.model, messages=self.messages, stream=True)
            for chunk in stream:
                token = chunk.get("message", {}).get("content", "")
                if token:
                    self.response_received.emit(token)
        except Exception as e:
            self.error_occurred.emit(f"Ollama error: {str(e)}")

    def call_qwen(self):
        if not HAS_REQUESTS:
            self.error_occurred.emit("Requests library not installed")
            return

        api_key = os.environ.get("QWEN_API_KEY", "")
        if not api_key:
            self.error_occurred.emit("QWEN_API_KEY not set")
            return

        try:
            response = requests.post(
                "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={"model": "qwen-plus", "messages": self.messages},
                timeout=60,
            )
            result = response.json()
            if response.status_code == 200:
                self.response_received.emit(result.get("output", {}).get("text", ""))
        except Exception as e:
            self.error_occurred.emit(str(e))

    def call_openai(self):
        if not HAS_REQUESTS:
            self.error_occurred.emit("Requests library not installed")
            return

        api_key = os.environ.get("OPENAI_API_KEY", "")
        if not api_key:
            self.error_occurred.emit("OPENAI_API_KEY not set")
            return

        try:
            base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
            response = requests.post(
                f"{base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={"model": self.model, "messages": self.messages},
                timeout=60,
            )
            result = response.json()
            if response.status_code == 200:
                self.response_received.emit(result["choices"][0]["message"]["content"])
        except Exception as e:
            self.error_occurred.emit(str(e))


# ============================================================================
# In-Editor AI Assistant - Real-time Code Suggestions & Quick Fixes
# ============================================================================


class QuickFixDialog(QDialog):
    """Dialog for showing AI-powered quick fix suggestions"""

    def __init__(self, parent, original_code, suggested_code, issue_description):
        super().__init__(parent)
        self.setWindowTitle("AI Quick Fix Suggestion")
        self.setModal(True)
        self.setMinimumSize(700, 500)
        self.result_action = None  # 'fix', 'keep', or 'cancel'

        self.setup_ui(original_code, suggested_code, issue_description)

    def setup_ui(self, original_code, suggested_code, issue_description):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # Title and description
        title_label = QLabel("🤖 AI Code Suggestion")
        title_label.setStyleSheet(
            "font-size: 16px; font-weight: bold; color: #569CD6; padding: 8px;"
        )
        layout.addWidget(title_label)

        issue_label = QLabel(f"Issue: {issue_description}")
        issue_label.setWordWrap(True)
        issue_label.setStyleSheet(
            "font-size: 12px; color: #CE9178; padding: 4px; background-color: #2d2d2d; border-radius: 4px;"
        )
        layout.addWidget(issue_label)

        # Comparison layout
        comparison_layout = QHBoxLayout()

        # Original code
        original_group = QVBoxLayout()
        original_label = QLabel("📄 Original Code:")
        original_label.setStyleSheet("font-weight: bold; color: #d4d4d4;")
        original_group.addWidget(original_label)

        self.original_text = QTextEdit()
        self.original_text.setPlainText(original_code)
        self.original_text.setReadOnly(True)
        self.original_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 2px solid #ff6b6b;
                border-radius: 4px;
                font-family: Consolas;
                font-size: 11px;
                padding: 8px;
            }
        """)
        original_group.addWidget(self.original_text)
        comparison_layout.addLayout(original_group)

        # Arrow separator
        arrow_label = QLabel("→")
        arrow_label.setStyleSheet("font-size: 24px; color: #6A9955; font-weight: bold;")
        arrow_label.setAlignment(Qt.AlignCenter)
        comparison_layout.addWidget(arrow_label)

        # Suggested code
        suggested_group = QVBoxLayout()
        suggested_label = QLabel("✨ AI Suggestion:")
        suggested_label.setStyleSheet("font-weight: bold; color: #6A9955;")
        suggested_group.addWidget(suggested_label)

        self.suggested_text = QTextEdit()
        self.suggested_text.setPlainText(suggested_code)
        self.suggested_text.setReadOnly(True)
        self.suggested_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 2px solid #6A9955;
                border-radius: 4px;
                font-family: Consolas;
                font-size: 11px;
                padding: 8px;
            }
        """)
        suggested_group.addWidget(self.suggested_text)
        comparison_layout.addLayout(suggested_group)

        layout.addLayout(comparison_layout)

        # Action buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        btn_fix = QPushButton("✓ Apply Fix")
        btn_fix.setStyleSheet("""
            QPushButton {
                background-color: #6A9955;
                color: white;
                border: none;
                padding: 10px 24px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #7fb069;
            }
        """)
        btn_fix.clicked.connect(lambda: self.set_action("fix"))
        button_layout.addWidget(btn_fix)

        btn_keep = QPushButton("Keep Original")
        btn_keep.setStyleSheet("""
            QPushButton {
                background-color: #569CD6;
                color: white;
                border: none;
                padding: 10px 24px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #6aacff;
            }
        """)
        btn_keep.clicked.connect(lambda: self.set_action("keep"))
        button_layout.addWidget(btn_keep)

        btn_cancel = QPushButton("✗ Cancel")
        btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: #3e3e3e;
                color: white;
                border: none;
                padding: 10px 24px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #505050;
            }
        """)
        btn_cancel.clicked.connect(lambda: self.set_action("cancel"))
        button_layout.addWidget(btn_cancel)

        layout.addLayout(button_layout)

    def set_action(self, action):
        """Set the user's choice and close dialog"""
        self.result_action = action
        self.accept()

    def get_action(self):
        """Return the user's choice"""
        return self.result_action


class AICodeAnalyzer(QThread):
    """Background thread for analyzing code with AI"""

    analysis_complete = Signal(str, str, str)  # issue, original, suggestion
    error_occurred = Signal(str)

    def __init__(self, code, language, model="gpt-oss:20b-cloud"):
        super().__init__()
        self.code = code
        self.language = language
        self.model = model

    def run(self):
        """Analyze code using Ollama"""
        if not HAS_OLLAMA:
            self.error_occurred.emit("Ollama not installed")
            return

        try:
            # Create analysis prompt - FOCUS ON ERRORS ONLY
            prompt = f"""You are a code error checker. Analyze this {self.language} code for ACTUAL ERRORS ONLY.

ONLY report:
- Syntax errors
- Undefined variables or functions
- Type mismatches
- Logic errors that will cause crashes

DO NOT report:
- Style suggestions
- Optimizations
- Best practices
- Formatting issues

Code:
```{self.language}
{self.code}
```

If there are NO ERRORS, respond with exactly: "NO_ERRORS"

If there ARE errors, respond in this exact format:
ISSUE: <brief description of the error>
ORIGINAL: <the problematic code snippet>
SUGGESTION: <the corrected code snippet>

Keep it concise and focused on ONE error."""

            messages = [{"role": "user", "content": prompt}]

            # Call Ollama API
            response = ollama.chat(model=self.model, messages=messages, stream=False)
            content = response.get("message", {}).get("content", "")

            # Check if no errors found
            if "NO_ERRORS" in content.upper():
                self.analysis_complete.emit("NO_ERRORS", "NO_ERRORS", "NO_ERRORS")
                return

            # Parse response with improved regex patterns
            # Try to match with code fences first
            issue_match = re.search(
                r"ISSUE:\s*(.+?)(?=\n(?:ORIGINAL|$))",
                content,
                re.DOTALL | re.IGNORECASE,
            )

            # Match ORIGINAL with or without code fences
            original_match = re.search(
                r"ORIGINAL:\s*(?:```\w*\n)?([\s\S]+?)(?:```\s*)?(?=\n(?:SUGGESTION|$))",
                content,
                re.IGNORECASE,
            )

            # Match SUGGESTION with or without code fences
            suggestion_match = re.search(
                r"SUGGESTION:\s*(?:```\w*\n)?([\s\S]+?)(?:```\s*)?$",
                content,
                re.IGNORECASE,
            )

            if issue_match and original_match and suggestion_match:
                issue = issue_match.group(1).strip()
                original = original_match.group(1).strip()
                suggestion = suggestion_match.group(1).strip()

                # Remove any remaining markdown code fence markers
                original = re.sub(r"^```\w*\s*|\s*```$", "", original).strip()
                suggestion = re.sub(r"^```\w*\s*|\s*```$", "", suggestion).strip()

                self.analysis_complete.emit(issue, original, suggestion)
            else:
                # Enhanced fallback parsing - split by labels
                issue = "Code improvement suggestion"
                original = self.code[:100]
                suggestion = ""

                # Try to extract suggestion by looking for the SUGGESTION: label
                if "SUGGESTION:" in content.upper():
                    # Find everything after SUGGESTION:
                    suggestion_part = re.split(
                        r"SUGGESTION:\s*", content, flags=re.IGNORECASE
                    )
                    if len(suggestion_part) > 1:
                        suggestion = suggestion_part[-1].strip()
                        # Remove code fences if present
                        suggestion = re.sub(
                            r"^```\w*\s*|\s*```$", "", suggestion, flags=re.MULTILINE
                        ).strip()

                if suggestion:
                    self.analysis_complete.emit(issue, original, suggestion)
                else:
                    # Last resort - use last few lines
                    lines = content.strip().split("\n")
                    if len(lines) >= 3:
                        self.analysis_complete.emit(
                            "Code improvement suggestion",
                            self.code[:100],
                            lines[-1],
                        )
        except Exception as e:
            self.error_occurred.emit(f"Analysis error: {str(e)}")


class CodePolisher(QThread):
    """Background thread for polishing code with AI"""

    polishing_complete = Signal(str)  # polished code
    error_occurred = Signal(str)

    def __init__(self, code, language, model="gpt-oss:20b-cloud"):
        super().__init__()
        self.code = code
        self.language = language
        self.model = model

    def run(self):
        """Polish code using Ollama"""
        if not HAS_OLLAMA:
            self.error_occurred.emit("Ollama not installed")
            return

        try:
            # Create polishing prompt
            prompt = f"""You are a code formatter and organizer. Polish and format this {self.language} code to make it clean, organized, and professional.

Tasks:
- Fix indentation and spacing
- Organize code logically
- Add proper line breaks
- Format consistently
- Keep functionality EXACTLY the same
- DO NOT change variable names or logic

Code to polish:
```{self.language}
{self.code}
```

Respond with ONLY the polished code, no explanations. Start directly with the code."""

            messages = [{"role": "user", "content": prompt}]

            # Call Ollama API
            response = ollama.chat(model=self.model, messages=messages, stream=False)
            content = response.get("message", {}).get("content", "")

            # Extract code from response (remove code fences if present)
            polished = content.strip()

            # Remove markdown code fences
            if polished.startswith("```"):
                lines = polished.split("\n")
                # Remove first line if it's a fence
                if lines[0].startswith("```"):
                    lines = lines[1:]
                # Remove last line if it's a fence
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                polished = "\n".join(lines)

            self.polishing_complete.emit(polished)
        except Exception as e:
            self.error_occurred.emit(f"Polishing error: {str(e)}")


class AIMessageGenerator(QThread):
    """Background thread for generating creative AI status messages"""

    messages_generated = Signal(list)  # list of messages
    error_occurred = Signal(str)

    def __init__(self, model="gpt-oss:20b-cloud"):
        super().__init__()
        self.model = model

    def run(self):
        """Generate creative status messages using Ollama"""
        if not HAS_OLLAMA:
            # Fallback to defaults
            self.messages_generated.emit(
                [
                    "✨ Wait for magic to happen...",
                    "🔮 Counting lines of brilliance...",
                    "🪄 Doing the magic...",
                    "⚡ Sprinkling AI dust...",
                    "🌟 Weaving code perfection...",
                ]
            )
            return

        try:
            prompt = """Generate 10 creative, fun status messages for a code polishing animation in an IDE. 
Each message should be:
- Short (3-6 words)
- Start with an emoji
- Be playful and tech/AI themed
- Different from each other

Examples: "✨ Wait for magic to happen...", "🔮 Counting lines of brilliance..."

Respond with ONLY the 10 messages, one per line, no numbering, no explanations."""

            messages = [{"role": "user", "content": prompt}]

            # Call Ollama API
            response = ollama.chat(model=self.model, messages=messages, stream=False)
            content = response.get("message", {}).get("content", "")

            # Parse messages from response
            lines = [
                line.strip() for line in content.strip().split("\n") if line.strip()
            ]

            # Remove any numbering (1. 2. etc.)
            messages_list = []
            for line in lines:
                # Remove leading numbers/bullets
                cleaned = re.sub(r"^\d+\.\s*|\*\s*|-\s*", "", line).strip()
                if cleaned and len(cleaned) > 5:  # Valid message
                    messages_list.append(cleaned)

            # Ensure we have at least 5 messages
            if len(messages_list) >= 5:
                self.messages_generated.emit(messages_list[:10])
            else:
                # Fallback if AI response was bad
                self.messages_generated.emit(
                    [
                        "✨ Wait for magic to happen...",
                        "🔮 Counting lines of brilliance...",
                        "🪄 Doing the magic...",
                        "⚡ Sprinkling AI dust...",
                        "🌟 Weaving code perfection...",
                    ]
                )
        except Exception as e:
            self.error_occurred.emit(f"Message generation error: {str(e)}")
            # Fallback to defaults
            self.messages_generated.emit(
                [
                    "✨ Wait for magic to happen...",
                    "🔮 Counting lines of brilliance...",
                    "🪄 Doing the magic...",
                    "⚡ Sprinkling AI dust...",
                    "🌟 Weaving code perfection...",
                ]
            )


class PolishingOverlay(QWidget):
    """Animated overlay with sweeping line, blur effect, and AI stars"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)  # Block interaction
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.line_position = 0
        self.animation_running = False
        self.stars = []

        # Default messages (fallback if AI not available)
        self.status_messages = [
            "✨ Wait for magic to happen...",
            "🔮 Counting lines of brilliance...",
            "🪄 Doing the magic...",
            "⚡ Sprinkling AI dust...",
            "🌟 Weaving code perfection...",
        ]
        self.current_message = random.choice(self.status_messages)
        self.message_generator = None

        # Initialize stars
        for _ in range(20):
            self.stars.append(
                {
                    "x": random.randint(0, 800),
                    "y": random.randint(0, 600),
                    "size": random.randint(2, 6),
                    "speed": random.uniform(0.5, 2.0),
                    "opacity": random.randint(100, 255),
                    "twinkle_speed": random.uniform(0.02, 0.08),
                }
            )

        # Animation timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.animate)

        # Message rotation timer
        self.message_timer = QTimer()
        self.message_timer.timeout.connect(self.rotate_message)

    def start_animation(self):
        """Start the sweeping line animation with blur and generate fresh AI messages"""
        self.animation_running = True
        self.line_position = 0
        self.timer.start(16)  # ~60 FPS
        self.message_timer.start(2000)  # Change message every 2 seconds
        self.show()
        self.raise_()

        # Generate fresh AI messages in background
        if HAS_OLLAMA:
            self.message_generator = AIMessageGenerator()
            self.message_generator.messages_generated.connect(self.update_messages)
            self.message_generator.start()

    def update_messages(self, new_messages):
        """Update status messages with fresh AI-generated ones"""
        if new_messages and len(new_messages) >= 5:
            self.status_messages = new_messages
            self.current_message = random.choice(self.status_messages)

    def stop_animation(self):
        """Stop the animation"""
        self.animation_running = False
        self.timer.stop()
        self.message_timer.stop()
        self.hide()

    def rotate_message(self):
        """Rotate to a new random message"""
        self.current_message = random.choice(self.status_messages)
        self.update()

    def animate(self):
        """Animate the sweeping line and stars"""
        if not self.animation_running:
            return

        # Move sweep line across the screen
        self.line_position += 4

        # Reset if line goes off screen
        if self.line_position > self.width():
            self.line_position = 0

        # Animate stars
        for star in self.stars:
            star["x"] += star["speed"]
            if star["x"] > self.width():
                star["x"] = -10
                star["y"] = random.randint(0, self.height())

            # Twinkle effect
            star["opacity"] += star["twinkle_speed"] * 50
            if star["opacity"] > 255 or star["opacity"] < 100:
                star["twinkle_speed"] *= -1

        self.update()

    def paintEvent(self, event):
        """Draw the overlay with blur, sweep line, stars, and status text"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Semi-transparent blurred background
        painter.fillRect(self.rect(), QColor(0, 0, 0, 120))

        # Draw stars
        for star in self.stars:
            # Create gradient for star glow
            gradient = QRadialGradient(star["x"], star["y"], star["size"] * 2)
            color = QColor(82, 168, 224, int(star["opacity"]))  # Cyan stars
            gradient.setColorAt(0, color)
            gradient.setColorAt(1, QColor(82, 168, 224, 0))

            painter.setBrush(QBrush(gradient))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(
                int(star["x"] - star["size"]),
                int(star["y"] - star["size"]),
                star["size"] * 2,
                star["size"] * 2,
            )

        # Draw full horizontal sweep line
        sweep_height = 60
        sweep_y = self.height() // 2 - sweep_height // 2

        # Create gradient for sweep line (left to right)
        gradient = QLinearGradient(
            self.line_position - 150, 0, self.line_position + 150, 0
        )
        gradient.setColorAt(0, QColor(106, 153, 85, 0))  # Transparent green
        gradient.setColorAt(0.3, QColor(106, 153, 85, 180))  # Green
        gradient.setColorAt(0.5, QColor(82, 168, 224, 220))  # Cyan peak
        gradient.setColorAt(0.7, QColor(106, 153, 85, 180))  # Green
        gradient.setColorAt(1, QColor(106, 153, 85, 0))  # Transparent

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(gradient))

        # Draw the full-width sweep bar
        sweep_rect = QRect(self.line_position - 150, sweep_y, 300, sweep_height)
        painter.drawRect(sweep_rect)

        # Draw status text in the center
        painter.setPen(QColor(255, 255, 255, 230))
        font = QFont("Segoe UI", 16, QFont.Bold)
        painter.setFont(font)

        text_rect = self.rect()
        painter.drawText(text_rect, Qt.AlignCenter, self.current_message)

        painter.end()


class InEditorAIAssistant(QWidget):
    """In-editor AI assistant for manual error checking"""

    def __init__(self, editor, parent=None):
        super().__init__(parent)
        self.editor = editor
        self.model = "gpt-oss:20b-cloud"
        self.analyzer_thread = None
        self.enabled = True

        # Create horizontal layout for button and status
        self.container = QWidget()
        layout = QHBoxLayout(self.container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Check button
        self.check_button = QPushButton("Check Errors")
        self.check_button.setStyleSheet("""
            QPushButton {
                background-color: #2a3d50;
                color: #9cdcfe;
                border: 1px solid #2f5475;
                padding: 3px 10px;
                border-radius: 4px;
                font-family: "Segoe UI";
                font-size: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #094771;
                border-color: #007acc;
                color: #ffffff;
            }
            QPushButton:pressed {
                background-color: #063655;
            }
        """)
        self.check_button.setCursor(Qt.PointingHandCursor)
        self.check_button.clicked.connect(self.analyze_current_code)
        layout.addWidget(self.check_button)

        # Polish button
        self.polish_button = QPushButton("Polish Code")
        self.polish_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #1a6b3c, stop:1 #1a5c80);
                color: #b5e8c8;
                border: 1px solid #2a7a50;
                padding: 3px 10px;
                border-radius: 4px;
                font-family: "Segoe UI";
                font-size: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #237a48, stop:1 #226e99);
                color: #ffffff;
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #134f2c, stop:1 #134a62);
            }
        """)
        self.polish_button.setCursor(Qt.PointingHandCursor)
        self.polish_button.clicked.connect(self.polish_code)
        layout.addWidget(self.polish_button)

        # Status indicator
        self.status_label = QLabel("AI: Ready")
        self.status_label.setStyleSheet("""
            QLabel {
                background-color: rgba(106,153,85,0.15);
                color: #6A9955;
                padding: 3px 10px;
                border-radius: 4px;
                font-family: "Segoe UI";
                font-size: 10px;
                font-weight: bold;
                border: 1px solid rgba(106,153,85,0.3);
            }
        """)
        layout.addWidget(self.status_label)

        # NO auto-analysis - button trigger only!

    def analyze_current_code(self):
        """Analyze ALL editor code for errors (manual trigger)"""
        if not self.enabled or not HAS_OLLAMA:
            self.status_label.setText("AI: Disabled")
            return

        # Get ALL code from editor
        code = self.editor.toPlainText()

        if len(code.strip()) < 5:
            self.status_label.setText("AI: No code to check")
            self.status_label.setStyleSheet("""
                QLabel {
                    background-color: transparent;
                    color: #CE9178;
                    padding: 3px 10px;
                    border-radius: 4px;
                    font-family: "Segoe UI";
                    font-size: 10px;
                    font-weight: bold;
                }
            """)
            return

        # Show analyzing status
        self.status_label.setText("AI: Checking...")
        self.status_label.setStyleSheet("""
            QLabel {
                background-color: transparent;
                color: #CE9178;
                padding: 3px 10px;
                border-radius: 4px;
                font-family: "Segoe UI";
                font-size: 10px;
                font-weight: bold;
            }
        """)
        self.check_button.setEnabled(False)

        # Start analysis in background
        self.analyzer_thread = AICodeAnalyzer(code, self.editor.language, self.model)
        self.analyzer_thread.analysis_complete.connect(self.show_quick_fix)
        self.analyzer_thread.error_occurred.connect(self.on_analysis_error)
        self.analyzer_thread.finished.connect(
            lambda: self.check_button.setEnabled(True)
        )
        self.analyzer_thread.start()

    def show_quick_fix(self, issue, original, suggestion):
        """Show quick fix dialog with suggestions or success message"""
        # Check if AI found no errors
        if issue == "NO_ERRORS" or "NO_ERRORS" in original or "NO_ERRORS" in suggestion:
            self.status_label.setText("✅ Code is Correct!")
            self.status_label.setStyleSheet("""
                QLabel {
                    background-color: transparent;
                    color: #6A9955;
                    padding: 3px 10px;
                    border-radius: 4px;
                    font-family: "Segoe UI";
                    font-size: 10px;
                    font-weight: bold;
                }
            """)
            # Reset after 3 seconds
            QTimer.singleShot(3000, lambda: self.status_label.setText("AI: Ready ✓"))
            return

        # Found error - show dialog
        self.status_label.setText("⚠️ Error Found")
        self.status_label.setStyleSheet("""
            QLabel {
                background-color: transparent;
                color: #ff6b6b;
                padding: 3px 10px;
                border-radius: 4px;
                font-family: "Segoe UI";
                font-size: 10px;
                font-weight: bold;
            }
        """)

        # Show dialog
        dialog = QuickFixDialog(self.editor, original, suggestion, issue)
        dialog.exec()

        action = dialog.get_action()
        if action == "fix":
            self.apply_suggestion(original, suggestion)
        elif action == "keep":
            self.status_label.setText("AI: Original Kept")
        else:
            self.status_label.setText("AI: Cancelled")

        # Reset after 3 seconds
        QTimer.singleShot(
            3000,
            lambda: self.status_label.setText("AI: Ready ✓")
            or self.status_label.setStyleSheet(
                """
                QLabel {
                    background-color: transparent;
                    color: #6A9955;
                    padding: 3px 10px;
                    border-radius: 4px;
                    font-family: "Segoe UI";
                    font-size: 10px;
                    font-weight: bold;
                }
            """
            ),
        )

    def apply_suggestion(self, original, suggestion):
        """Apply the AI suggestion to the editor"""
        content = self.editor.toPlainText()

        # Normalize line endings - original might have \n from AI but content uses actual newlines
        original_normalized = original.strip()
        suggestion_normalized = suggestion.strip()

        # Try to find and replace the original code
        if original_normalized in content:
            new_content = content.replace(original_normalized, suggestion_normalized, 1)
            self.editor.setPlainText(new_content)
            self.status_label.setText("AI: Fix Applied ✓")
            self.status_label.setStyleSheet("""
                QLabel {
                    background-color: transparent;
                    color: #6A9955;
                    padding: 3px 10px;
                    border-radius: 4px;
                    font-family: "Segoe UI";
                    font-size: 10px;
                    font-weight: bold;
                }
            """)
        else:
            # Fallback: if exact match fails, try fuzzy matching by removing extra whitespace
            import difflib

            lines = content.split("\n")
            best_match_idx = -1
            best_ratio = 0.0

            # Find the best matching section
            original_lines = original_normalized.split("\n")
            for i in range(len(lines) - len(original_lines) + 1):
                section = "\n".join(lines[i : i + len(original_lines)])
                ratio = difflib.SequenceMatcher(
                    None, original_normalized, section
                ).ratio()
                if ratio > best_ratio:
                    best_ratio = ratio
                    best_match_idx = i

            # If we found a good match (>80% similar), replace it
            if best_ratio > 0.8 and best_match_idx >= 0:
                lines[best_match_idx : best_match_idx + len(original_lines)] = (
                    suggestion_normalized.split("\n")
                )
                self.editor.setPlainText("\n".join(lines))
                self.status_label.setText("AI: Fix Applied ✓")
                self.status_label.setStyleSheet("""
                    QLabel {
                        background-color: transparent;
                        color: #6A9955;
                        padding: 3px 10px;
                        border-radius: 4px;
                        font-family: "Segoe UI";
                        font-size: 10px;
                        font-weight: bold;
                    }
                """)
            else:
                self.status_label.setText("AI: Match Failed ⚠")
                self.status_label.setStyleSheet("""
                    QLabel {
                        background-color: transparent;
                        color: #ff6b6b;
                        padding: 3px 10px;
                        border-radius: 4px;
                        font-family: "Segoe UI";
                        font-size: 10px;
                        font-weight: bold;
                    }
                """)

    def on_analysis_error(self, error_msg):
        """Handle analysis errors"""
        self.status_label.setText(f"AI: Error")
        self.status_label.setStyleSheet("""
            QLabel {
                background-color: transparent;
                color: #ff6b6b;
                padding: 3px 10px;
                border-radius: 4px;
                font-family: "Segoe UI";
                font-size: 10px;
                font-weight: bold;
            }
        """)
        print(f"AI Analysis Error: {error_msg}")

    def polish_code(self):
        """Polish and format code with animated overlay"""
        if not self.enabled or not HAS_OLLAMA:
            self.status_label.setText("AI: Disabled")
            return

        # Get ALL code from editor
        code = self.editor.toPlainText()

        if len(code.strip()) < 5:
            self.status_label.setText("AI: No code to polish")
            self.status_label.setStyleSheet("""
                QLabel {
                    background-color: transparent;
                    color: #CE9178;
                    padding: 3px 10px;
                    border-radius: 4px;
                    font-family: "Segoe UI";
                    font-size: 10px;
                    font-weight: bold;
                }
            """)
            return

        # Show polishing status
        self.status_label.setText("✨ Polishing...")
        self.status_label.setStyleSheet("""
            QLabel {
                background-color: transparent;
                color: #52A8E0;
                padding: 3px 10px;
                border-radius: 4px;
                font-family: "Segoe UI";
                font-size: 10px;
                font-weight: bold;
            }
        """)
        self.polish_button.setEnabled(False)
        self.check_button.setEnabled(False)

        # Make editor read-only during polishing
        self.editor.setReadOnly(True)

        # Create and show polishing overlay
        self.polishing_overlay = PolishingOverlay(self.editor)
        self.polishing_overlay.setGeometry(self.editor.rect())
        self.polishing_overlay.start_animation()

        # Start polishing in background
        self.polisher_thread = CodePolisher(code, self.editor.language, self.model)
        self.polisher_thread.polishing_complete.connect(self.on_polishing_complete)
        self.polisher_thread.error_occurred.connect(self.on_polishing_error)
        self.polisher_thread.start()

    def on_polishing_complete(self, polished_code):
        """Handle polished code result"""
        # Keep animation running for a smooth finish
        QTimer.singleShot(800, lambda: self._apply_polished_code(polished_code))

    def _apply_polished_code(self, polished_code):
        """Apply the polished code after animation"""
        # Stop animation
        if hasattr(self, "polishing_overlay"):
            self.polishing_overlay.stop_animation()
            self.polishing_overlay.deleteLater()

        # Restore editor to editable
        self.editor.setReadOnly(False)

        # Apply polished code
        self.editor.setPlainText(polished_code)

        # Update status
        self.status_label.setText("✅ Code Polished!")
        self.status_label.setStyleSheet("""
            QLabel {
                background-color: transparent;
                color: #6A9955;
                padding: 3px 10px;
                border-radius: 4px;
                font-family: "Segoe UI";
                font-size: 10px;
                font-weight: bold;
            }
        """)

        # Re-enable buttons
        self.polish_button.setEnabled(True)
        self.check_button.setEnabled(True)

        # Reset after 3 seconds
        QTimer.singleShot(3000, lambda: self.status_label.setText("AI: Ready ✓"))

    def on_polishing_error(self, error_msg):
        """Handle polishing errors"""
        # Stop animation
        if hasattr(self, "polishing_overlay"):
            self.polishing_overlay.stop_animation()
            self.polishing_overlay.deleteLater()

        # Restore editor to editable
        self.editor.setReadOnly(False)

        self.status_label.setText("AI: Polish Failed")
        self.status_label.setStyleSheet("""
            QLabel {
                background-color: transparent;
                color: #ff6b6b;
                padding: 3px 10px;
                border-radius: 4px;
                font-family: "Segoe UI";
                font-size: 10px;
                font-weight: bold;
            }
        """)

        # Re-enable buttons
        self.polish_button.setEnabled(True)
        self.check_button.setEnabled(True)

        print(f"AI Polishing Error: {error_msg}")

    def toggle_enabled(self):
        """Enable/disable the AI assistant"""
        self.enabled = not self.enabled
        if self.enabled:
            self.status_label.setText("AI: Enabled ✓")
        else:
            self.status_label.setText("AI: Disabled")

    def cleanup(self):
        """Cleanup threads and overlays"""
        try:
            if self.analyzer_thread and self.analyzer_thread.isRunning():
                self.analyzer_thread.wait(1000)  # Wait up to 1 second
        except (RuntimeError, AttributeError):
            pass

        try:
            if (
                hasattr(self, "polisher_thread")
                and self.polisher_thread
                and self.polisher_thread.isRunning()
            ):
                self.polisher_thread.wait(1000)
        except (RuntimeError, AttributeError):
            pass

        try:
            if hasattr(self, "polishing_overlay") and self.polishing_overlay:
                self.polishing_overlay.stop_animation()
                self.polishing_overlay.deleteLater()
                # Ensure editor is editable again
                self.editor.setReadOnly(False)
        except (RuntimeError, AttributeError):
            pass

    def __del__(self):
        """Destructor to ensure cleanup"""
        try:
            self.cleanup()
        except:
            pass  # Ignore all errors during destruction


# ============================================================================
# Editor Widget
# ============================================================================


# ============================================================================
# Offline Suggestion Popup Widget
# ============================================================================


class SuggestionPopup(QListWidget):
    """Floating autocomplete popup styled with live visual system tokens."""

    def __init__(self, parent_editor):
        super().__init__(parent_editor)
        self.editor = parent_editor
        self.setWindowFlags(Qt.ToolTip | Qt.FramelessWindowHint)
        self.setFocusPolicy(Qt.NoFocus)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # Style matching the editor theme tokens
        self.setStyleSheet(ThemeManager.resolve("""
            QListWidget {
                background-color: #171b24;
                color: #c7d0dd;
                border: 1px solid #394353;
                border-radius: 6px;
                padding: 4px;
            }
            QListWidget::item {
                padding: 4px 8px;
                border-radius: 4px;
            }
            QListWidget::item:hover {
                background-color: #262d3a;
                color: #e7edf5;
            }
            QListWidget::item:selected {
                background-color: #1d4d77;
                color: #f7fbff;
            }
        """))

        # Dictionary for lookups based on language selection
        self.keywords = {
            "html": [
                "div",
                "span",
                "section",
                "article",
                "nav",
                "header",
                "footer",
                "button",
                "input",
                "script",
                "style",
                "class",
                "id",
                "href",
                "src",
                "alt",
            ],
            "css": [
                "background-color",
                "color",
                "margin",
                "padding",
                "display",
                "flex",
                "grid",
                "border",
                "width",
                "height",
                "font-family",
                "font-size",
                "position",
                "absolute",
                "relative",
            ],
            "javascript": [
                "function",
                "const",
                "let",
                "var",
                "if",
                "else",
                "for",
                "while",
                "return",
                "console.log",
                "document",
                "window",
                "addEventListener",
                "querySelector",
                "async",
                "await",
            ],
            "js": [
                "function",
                "const",
                "let",
                "var",
                "if",
                "else",
                "for",
                "while",
                "return",
                "console.log",
                "document",
                "window",
                "addEventListener",
                "querySelector",
                "async",
                "await",
            ],
        }

    def update_suggestions(self, current_word):
        self.clear()
        if not current_word:
            self.hide()
            return

        lang = self.editor.language.lower()
        candidates = set(self.keywords.get(lang, []))

        # Dynamic local scanning: Extract existing variables/functions from current text
        document_text = self.editor.toPlainText()
        found_words = re.findall(r"\b\w+\b", document_text)
        for w in found_words:
            if w != current_word and len(w) > 1:
                candidates.add(w)

        # Filter candidates containing the typed letters anywhere inside them
        filtered = sorted([c for c in candidates if current_word.lower() in c.lower()])

        if not filtered:
            self.hide()
            return

        # Style list rows using theme tokens
        for item in filtered:
            list_item = QListWidgetItem(item)
            if item in self.keywords.get(lang, []):
                list_item.setForeground(QColor(ThemeManager.color("accent")))
            else:
                list_item.setForeground(QColor(ThemeManager.color("text_primary")))
            self.addItem(list_item)

        self.setCurrentRow(0)

        # Size and place the widget directly under the text cursor
        self.resize(220, min(160, self.count() * 26 + 10))
        cursor_rect = self.editor.cursorRect()
        global_pos = self.editor.mapToGlobal(cursor_rect.bottomLeft())
        self.move(global_pos + QPoint(0, 4))
        self.show()


# ============================================================================
# Offline Suggestion Popup Widget
# ============================================================================


class SuggestionPopup(QListWidget):
    """Floating autocomplete popup styled with live visual system tokens."""

    def __init__(self, parent_editor):
        super().__init__(parent_editor)
        self.editor = parent_editor
        self.setWindowFlags(Qt.ToolTip | Qt.FramelessWindowHint)
        self.setFocusPolicy(Qt.NoFocus)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # Style matching the editor theme tokens
        self.setStyleSheet(ThemeManager.resolve("""
            QListWidget {
                background-color: #171b24;
                color: #c7d0dd;
                border: 1px solid #394353;
                border-radius: 6px;
                padding: 4px;
            }
            QListWidget::item {
                padding: 4px 8px;
                border-radius: 4px;
            }
            QListWidget::item:hover {
                background-color: #262d3a;
                color: #e7edf5;
            }
            QListWidget::item:selected {
                background-color: #1d4d77;
                color: #f7fbff;
            }
        """))

        # Dictionary for lookups based on language selection
        self.keywords = {
            "html": [
                "div",
                "span",
                "section",
                "article",
                "nav",
                "header",
                "footer",
                "button",
                "input",
                "script",
                "style",
                "class",
                "id",
                "href",
                "src",
                "alt",
            ],
            "css": [
                "background-color",
                "color",
                "margin",
                "padding",
                "display",
                "flex",
                "grid",
                "border",
                "width",
                "height",
                "font-family",
                "font-size",
                "position",
                "absolute",
                "relative",
            ],
            "javascript": [
                "function",
                "const",
                "let",
                "var",
                "if",
                "else",
                "for",
                "while",
                "return",
                "console.log",
                "document",
                "window",
                "addEventListener",
                "querySelector",
                "async",
                "await",
            ],
            "js": [
                "function",
                "const",
                "let",
                "var",
                "if",
                "else",
                "for",
                "while",
                "return",
                "console.log",
                "document",
                "window",
                "addEventListener",
                "querySelector",
                "async",
                "await",
            ],
        }

    def update_suggestions(self, current_word):
        self.clear()
        if not current_word:
            self.hide()
            return

        lang = self.editor.language.lower()
        candidates = set(self.keywords.get(lang, []))

        # Dynamic local scanning: Extract existing variables/functions from current text
        document_text = self.editor.toPlainText()
        found_words = re.findall(r"\b\w+\b", document_text)
        for w in found_words:
            if w != current_word and len(w) > 1:
                candidates.add(w)

        # Filter candidates containing the typed letters anywhere inside them
        filtered = sorted([c for c in candidates if current_word.lower() in c.lower()])

        if not filtered:
            self.hide()
            return

        # Style list rows using theme tokens
        for item in filtered:
            list_item = QListWidgetItem(item)
            if item in self.keywords.get(lang, []):
                list_item.setForeground(QColor(ThemeManager.color("accent")))
            else:
                list_item.setForeground(QColor(ThemeManager.color("text_primary")))
            self.addItem(list_item)

        self.setCurrentRow(0)

        # Size and place the widget directly under the text cursor
        self.resize(220, min(160, self.count() * 26 + 10))
        cursor_rect = self.editor.cursorRect()
        global_pos = self.editor.mapToGlobal(cursor_rect.bottomLeft())
        self.move(global_pos + QPoint(0, 4))
        self.show()


# ============================================================================
# Upgraded Editor Widget (With Auto-Closing Tags and Auto-Suggestion hooks)
# ============================================================================


class CodeEditor(QTextEdit):
    """Code editor with offline auto-suggestions and instant HTML tag auto-closing"""

    def __init__(self, parent=None, language="html"):
        super().__init__(parent)
        self.language = language

        # Auto-closing bracket/quote configurations
        self.auto_pairs = {"(": ")", "[": "]", "{": "}", '"': '"', "'": "'"}

        # Set up font
        font = QFont("Consolas", 11)
        font.setFixedPitch(True)
        self.setFont(font)

        # Style
        self.setStyleSheet(ThemeManager.resolve("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: none;
                padding: 0px;
            }
        """))

        # Attach syntax highlighter
        self.highlighter = CodeHighlighter(self.document(), language)

        # Initialize floating autocomplete menu
        self.completer_popup = SuggestionPopup(self)

        self.setWordWrapMode(QTextOption.WrapMode.NoWrap)
        self.setTabStopDistance(40)

        # Dark palette colors
        palette = self.palette()
        palette.setColor(QPalette.Base, QColor(ThemeManager.color("window")))
        palette.setColor(QPalette.Text, QColor(ThemeManager.color("text_primary")))
        palette.setColor(
            QPalette.Highlight, QColor(ThemeManager.color("editor_selection"))
        )
        self.setPalette(palette)

    def set_language(self, language):
        self.language = language
        self.highlighter = CodeHighlighter(self.document(), language)

    def get_current_word(self):
        """Extract the exact string prefix right before the text cursor."""
        cursor = self.textCursor()
        pos = cursor.position()
        text = self.toPlainText()

        start = pos
        while start > 0 and (text[start - 1].isalnum() or text[start - 1] in "-_"):
            start -= 1
        return text[start:pos]

    def insert_completion(self):
        """Insert chosen suggestion word into the current text position."""
        if (
            not self.completer_popup.isVisible()
            or not self.completer_popup.currentItem()
        ):
            return False

        completion = self.completer_popup.currentItem().text()
        current_word = self.get_current_word()

        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.Left, QTextCursor.KeepAnchor, len(current_word))
        cursor.removeSelectedText()
        cursor.insertText(completion)
        self.setTextCursor(cursor)

        self.completer_popup.hide()
        return True

    def keyPressEvent(self, event):
        """Intercept key input for tag closing, pairs matching, and auto-completion navigation."""
        key = event.key()
        text = event.text()

        # 1. Menu popup navigation
        if self.completer_popup.isVisible():
            if key in (Qt.Key_Enter, Qt.Key_Return, Qt.Key_Tab):
                if self.insert_completion():
                    return
            elif key == Qt.Key_Escape:
                self.completer_popup.hide()
                return
            elif key == Qt.Key_Up:
                row = self.completer_popup.currentRow()
                if row > 0:
                    self.completer_popup.setCurrentRow(row - 1)
                return
            elif key == Qt.Key_Down:
                row = self.completer_popup.currentRow()
                if row < self.completer_popup.count() - 1:
                    self.completer_popup.setCurrentRow(row + 1)
                return

        # 2. HTML Tag Auto-Closing logic
        if text == ">" and self.language.lower() == "html":
            cursor = self.textCursor()
            pos = cursor.position()
            content = self.toPlainText()

            last_open = content.rfind("<", 0, pos)
            if last_open != -1 and ">" not in content[last_open:pos]:
                tag_guts = content[last_open + 1 : pos].strip()
                tag_match = re.match(r"^(\w+)", tag_guts)
                if tag_match:
                    tag_name = tag_match.group(1)
                    # Skip self-closing void elements
                    if tag_name not in ["img", "br", "hr", "input", "meta", "link"]:
                        cursor.insertText(f"></{tag_name}>")
                        cursor.movePosition(
                            QTextCursor.Left, QTextCursor.MoveAnchor, len(tag_name) + 3
                        )
                        self.setTextCursor(cursor)
                        return

        # Auto-closing brackets & quote strings
        if text in self.auto_pairs:
            cursor = self.textCursor()
            if text in ['"', "'"]:
                if self.get_char_after_cursor() == text:
                    cursor.movePosition(QTextCursor.Right)
                    self.setTextCursor(cursor)
                    return
            cursor.insertText(text + self.auto_pairs[text])
            cursor.movePosition(QTextCursor.Left)
            self.setTextCursor(cursor)
            return

        if text in self.auto_pairs.values():
            if self.get_char_after_cursor() == text:
                cursor = self.textCursor()
                cursor.movePosition(QTextCursor.Right)
                self.setTextCursor(cursor)
                return

        # Structural return/enter line break indentation formatting
        if key == Qt.Key_Return and self.language == "html":
            line = self.get_current_line()
            match = re.search(r"<(\w+)[^>]*>$", line.strip())
            if match:
                tag = match.group(1)
                if tag not in ["img", "br", "hr", "input", "meta", "link"]:
                    cursor = self.textCursor()
                    indent = self.get_current_indent()
                    cursor.insertText("\n" + indent + "    ")
                    pos = cursor.position()
                    cursor.insertText("\n" + indent + f"</{tag}>")
                    cursor.setPosition(pos)
                    self.setTextCursor(cursor)
                    return

        # Dual bracket/quote deletion
        if key == Qt.Key_Backspace:
            cursor = self.textCursor()
            if not cursor.hasSelection():
                prev = self.get_char_before_cursor()
                next_char = self.get_char_after_cursor()
                if prev in self.auto_pairs and self.auto_pairs[prev] == next_char:
                    cursor.deletePreviousChar()
                    cursor.deleteChar()
                    self.completer_popup.hide()
                    return

        super().keyPressEvent(event)

        # Trigger dropdown evaluation on alpha-numeric strings or deletion backspaces
        if text.isalnum() or text in ["-", "_"] or key == Qt.Key_Backspace:
            current_word = self.get_current_word()
            self.completer_popup.update_suggestions(current_word)
        else:
            self.completer_popup.hide()

    def get_current_line(self):
        cursor = self.textCursor()
        cursor.select(QTextCursor.LineUnderCursor)
        return cursor.selectedText()

    def get_current_indent(self):
        line = self.get_current_line()
        indent = ""
        for char in line:
            if char in [" ", "\t"]:
                indent += char
            else:
                break
        return indent

    def get_char_before_cursor(self):
        pos = self.textCursor().position()
        if pos == 0:
            return ""
        text = self.toPlainText()
        return text[pos - 1] if pos <= len(text) else ""

    def get_char_after_cursor(self):
        pos = self.textCursor().position()
        text = self.toPlainText()
        return text[pos] if pos < len(text) else ""


# ============================================================================
# Claude Code Panel
# ============================================================================


class ClaudeCodeBridge(QObject):
    """Bridge for Claude Code (claude) xterm.js terminal."""

    writeToTerminal = Signal(str)
    clearScreen = Signal()
    codeChunkReady = Signal(str)  # real-time code chunk → active editor
    sessionStateChanged = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._proc = None
        self._cwd: str = os.path.expanduser("~")
        self._js_ready = False
        self._defer_start = False
        self._model: str = ""
        self._effort: str = "medium"
        self._permission_mode: str = "default"
        self._in_code_block = False
        self._raw_buf = ""
        self._launch_requested = False
        self._session_token = 0

    @Slot(str)
    def receiveInput(self, data: str):
        if self._proc:
            try:
                self._proc.write(data)
            except Exception:
                pass

    @Slot(int, int)
    def onResize(self, cols: int, rows: int):
        if self._proc:
            try:
                self._proc.setwinsize(rows, cols)
            except Exception:
                pass

    @Slot()
    def terminalReady(self):
        self._js_ready = True
        if self._defer_start:
            self._defer_start = False
            self._launch()

    def launch_model(
        self,
        model: str,
        cwd: str = "",
        effort: str = "medium",
        permission_mode: str = "default",
    ):
        """Launch Claude once in the requested directory; never auto-restart."""
        if self._proc or self._launch_requested:
            return False
        if cwd and os.path.isdir(cwd):
            self._cwd = cwd
        self._model = model
        self._effort = effort
        self._permission_mode = permission_mode
        self._launch_requested = True
        self.clearScreen.emit()
        if self._js_ready:
            self._launch()
        else:
            self._defer_start = True
        return True

    def send_prompt(self, prompt: str):
        """Send a prompt line to the running claude session."""
        if self._proc:
            try:
                self._proc.write(prompt + "\n")
            except Exception:
                pass

    def kill(self):
        # Cancel a pending launch as well as an already-running PTY.
        self._session_token += 1
        self._defer_start = False
        self._launch_requested = False
        self._kill()
        self.sessionStateChanged.emit(False)

    def _kill(self):
        old, self._proc = self._proc, None
        if old:
            try:
                old.terminate(force=True)
            except Exception:
                pass

    def _launch(self):
        if not HAS_WINPTY:
            self._launch_requested = False
            self.writeToTerminal.emit(
                "\r\n\x1b[1;31mError:\x1b[0m pywinpty is not installed.\r\n"
                "    \x1b[33mpip install pywinpty\x1b[0m\r\n"
            )
            return
        self._session_token += 1
        token = self._session_token
        threading.Thread(target=self._worker, args=(token,), daemon=True).start()

    def _worker(self, token):
        try:
            command = ["claude"]
            if self._model and self._model != "default":
                command.extend(["--model", self._model])
            if self._effort:
                command.extend(["--effort", self._effort])
            if self._permission_mode and self._permission_mode != "default":
                command.extend(["--permission-mode", self._permission_mode])
            proc = _WinPtyProcess.spawn(
                subprocess.list2cmdline(command),
                cwd=self._cwd,
                dimensions=(40, 160),
            )
            if token != self._session_token:
                proc.terminate(force=True)
                return
            self._proc = proc
            self.sessionStateChanged.emit(True)
            self._raw_buf = ""
            self._in_code_block = False

            while True:
                try:
                    data = proc.read(4096)
                    if not data:
                        if not proc.isalive():
                            break
                        continue
                    if isinstance(data, bytes):
                        data = data.decode("utf-8", errors="replace")
                    self.writeToTerminal.emit(data)
                    self._parse_output(data)
                except (EOFError, Exception):
                    break
        except Exception as exc:
            self.writeToTerminal.emit(
                f"\r\n\x1b[1;31m[Could not start claude: {exc}]\x1b[0m\r\n"
            )
        finally:
            if token == self._session_token:
                self._proc = None
                self._launch_requested = False
                self.sessionStateChanged.emit(False)
                self.writeToTerminal.emit("\r\n\x1b[33m[Session ended]\x1b[0m\r\n")

    # ── ANSI + code-fence parser ───────────────────────────────────────
    _ANSI_RE = re.compile(r"\x1b\][\s\S]*?(?:\x07|\x1b\\)|\x1b\[[0-?]*[ -/]*[@-~]|\r")

    def _strip_ansi(self, text: str) -> str:
        return self._ANSI_RE.sub("", text)

    def _parse_output(self, raw: str):
        """Detect ```...``` fences and emit enclosed text as codeChunkReady."""
        clean = self._strip_ansi(raw)
        self._raw_buf += clean
        FENCE = "```"
        buf = self._raw_buf
        while buf:
            if not self._in_code_block:
                idx = buf.find(FENCE)
                if idx == -1:
                    buf = buf[max(0, len(buf) - 2) :]
                    break
                rest = buf[idx + 3 :]
                nl = rest.find("\n")
                if nl == -1:
                    buf = buf[idx:]
                    break
                self._in_code_block = True
                buf = rest[nl + 1 :]
            else:
                idx = buf.find(FENCE)
                if idx == -1:
                    safe = max(0, len(buf) - 2)
                    if safe > 0:
                        self.codeChunkReady.emit(buf[:safe])
                        buf = buf[safe:]
                    break
                else:
                    if idx > 0:
                        self.codeChunkReady.emit(buf[:idx])
                    self._in_code_block = False
                    rest = buf[idx + 3 :]
                    nl = rest.find("\n")
                    buf = rest[nl + 1 :] if nl != -1 else rest
        self._raw_buf = buf


class ClaudeGUIRequestWorker(QThread):
    """Run one clean, non-interactive Claude response for the native GUI."""

    outputReady = Signal(str)
    failed = Signal(str)

    def __init__(self, prompt, cwd, model, effort, permission_mode, parent=None):
        super().__init__(parent)
        self.prompt = prompt
        self.cwd = cwd
        self.model = model
        self.effort = effort
        self.permission_mode = permission_mode
        self._process = None

    def stop(self):
        if self._process:
            try:
                self._process.terminate(force=True)
            except TypeError:
                self._process.terminate()
            except Exception:
                pass

    def run(self):
        command = ["claude", "-p", self.prompt]
        if self.model != "default":
            command.extend(["--model", self.model])
        if self.effort:
            command.extend(["--effort", self.effort])
        if self.permission_mode and self.permission_mode != "default":
            command.extend(["--permission-mode", self.permission_mode])
        try:
            if HAS_WINPTY:
                self._run_with_winpty(command)
            else:
                self._run_with_subprocess(command)
        except Exception as exc:
            self.failed.emit(f"Could not run Claude GUI request: {exc}")
        finally:
            self._process = None

    def _run_with_winpty(self, command):
        """Use the same Windows command resolution as the interactive TUI."""
        self._process = _WinPtyProcess.spawn(
            subprocess.list2cmdline(command),
            cwd=self.cwd,
            dimensions=(40, 160),
        )
        while True:
            try:
                data = self._process.read(4096)
            except EOFError:
                break
            if not data:
                if not self._process.isalive():
                    break
                continue
            if isinstance(data, bytes):
                data = data.decode("utf-8", errors="replace")
            self.outputReady.emit(data)

    def _run_with_subprocess(self, command):
        self._process = subprocess.Popen(
            command,
            cwd=self.cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        )
        for line in iter(self._process.stdout.readline, ""):
            self.outputReady.emit(line)
        if self._process.wait() != 0:
            self.failed.emit("Claude GUI request ended without a successful response.")


class ClaudeCodePanel(QWidget):
    """Claude Code panel — full-screen xterm.js terminal running `claude`."""

    _FALLBACK_MODELS: list[str] = [
        "deepseek-coder:6.7b",
        "qwen2.5-coder:1.5b",
        "qwen3.5:latest",
        "deepseek-r1:1.5b",
        "gemma3:4b",
    ]

    def __init__(self, ide, parent=None):
        super().__init__(parent)
        self.ide = ide
        self._bridge = ClaudeCodeBridge(self)
        self._editor_first_chunk = True
        self._launch_directory = None
        self._session_active = False
        self._interface_mode = 0
        self._gui_request = None
        self._fit_timer = QTimer(self)
        self._fit_timer.setSingleShot(True)
        self._fit_timer.setInterval(80)
        self._fit_timer.timeout.connect(self.refresh_terminal_size)
        self._bridge.codeChunkReady.connect(self._on_code_chunk)
        self._bridge.sessionStateChanged.connect(self._on_session_state_changed)
        self._setup_ui()
        self.set_working_directory(self._default_cwd())

    # ── UI ─────────────────────────────────────────────────────────────────

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(8)
        root.setContentsMargins(10, 10, 10, 10)

        # ── Top bar: model combo + refresh + launch + stop ────────────────
        top_row = QHBoxLayout()
        top_row.setSpacing(6)

        self._selected_model_name = "Default"
        self._selected_model_command = "default"
        self._selected_effort = "medium"
        self._selected_mode = "default"
        self._auto_accept_edits = False

        logo = QLabel()
        logo_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "assets", "claude-code-logo.png"
        )
        logo_pixmap = QPixmap(logo_path)
        if not logo_pixmap.isNull():
            logo.setPixmap(
                logo_pixmap.scaled(28, 28, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )
        logo.setFixedSize(30, 30)
        top_row.addWidget(logo)

        brand = QVBoxLayout()
        brand.setSpacing(0)
        brand_title = QLabel("CLAUDE CODE")
        brand_title.setStyleSheet(
            "color:#fff3ed;font-family:'Segoe UI';font-size:10px;font-weight:700;"
            "letter-spacing:1px;"
        )
        self.active_model_label = QLabel()
        self.active_model_label.setStyleSheet(
            "color:#d7a08c;font-family:'Segoe UI';font-size:9px;font-weight:600;"
        )
        brand.addWidget(brand_title)
        brand.addWidget(self.active_model_label)
        top_row.addLayout(brand)
        top_row.addStretch()

        self.model_menu_btn = FluidButton("Model")
        self.model_menu_btn.setToolTip("Choose the Claude model command")
        self.model_menu_btn.setCursor(Qt.PointingHandCursor)
        self.model_menu_btn.setMinimumHeight(30)
        self.model_menu_btn.setStyleSheet(self._quick_button_style())
        self.launch_btn = FluidButton("Run")
        self.launch_btn.setCursor(Qt.PointingHandCursor)
        self.launch_btn.setMinimumHeight(30)
        self.launch_btn.setStyleSheet("""
            QPushButton{
                background:qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #ed8258,stop:1 #b84e2f);
                color:#fff8f4;border:none;border-radius:7px;
                padding:4px 10px;font-weight:700;
                font-family:"Segoe UI";font-size:10px;
            }
            QPushButton:hover{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,
                stop:0 #ffad82,stop:1 #ed8258);}
            QPushButton:pressed{background:#8f3a24;}
        """)
        self.launch_btn.clicked.connect(self._launch_model)
        top_row.addWidget(self.launch_btn)

        self.kill_btn = FluidButton("Stop")
        self.kill_btn.setCursor(Qt.PointingHandCursor)
        self.kill_btn.setMinimumHeight(30)
        self.kill_btn.setEnabled(False)
        self.kill_btn.setStyleSheet("""
            QPushButton{
                background:#311d26;color:#ff9bab;
                border:1px solid #6f3546;border-radius:7px;
                padding:4px 8px;font-weight:700;
                font-family:"Segoe UI";font-size:10px;
            }
            QPushButton:hover{background:#512534;border-color:#ff9bab;color:#fff;}
            QPushButton:disabled{background:#242a34;color:#697386;border-color:#394353;}
        """)
        self.kill_btn.clicked.connect(self._stop_model)
        top_row.addWidget(self.kill_btn)

        root.addLayout(top_row)

        directory_row = QHBoxLayout()
        directory_row.setSpacing(6)
        directory_label = QLabel("Directory")
        directory_label.setStyleSheet(
            "color:#d7a08c;font-family:'Segoe UI';font-size:9px;font-weight:600;"
        )
        directory_row.addWidget(directory_label)

        self.directory_field = QLineEdit()
        self.directory_field.setReadOnly(True)
        self.directory_field.setMinimumHeight(26)
        self.directory_field.setStyleSheet("""
            QLineEdit {
                background:#130d0a;color:#f0d8cd;border:1px solid #5f392c;
                border-radius:6px;padding:3px 7px;font-family:Consolas;font-size:9px;
            }
        """)
        directory_row.addWidget(self.directory_field, 1)

        self.session_label = QLabel("Stopped")
        self.session_label.setStyleSheet(
            "color:#92a0b3;font-family:'Segoe UI';font-size:9px;font-weight:600;"
        )
        directory_row.addWidget(self.session_label)
        root.addLayout(directory_row)

        settings_row = QHBoxLayout()
        settings_row.setSpacing(5)
        self.effort_menu_btn = FluidButton("Effort")
        self.mode_menu_btn = FluidButton("Mode")
        self.auto_accept_btn = FluidButton("Accept: Off")
        for button, handler in [
            (self.model_menu_btn, self._show_model_menu),
            (self.effort_menu_btn, self._show_effort_menu),
            (self.mode_menu_btn, self._show_mode_menu),
            (self.auto_accept_btn, self._toggle_auto_accept_edits),
        ]:
            button.setCursor(Qt.PointingHandCursor)
            button.setMinimumHeight(27)
            button.setStyleSheet(self._quick_button_style())
            button.clicked.connect(handler)
            settings_row.addWidget(button)
        settings_row.addStretch()
        root.addLayout(settings_row)

        view_toggle = QHBoxLayout()
        view_toggle.setSpacing(5)
        view_label = QLabel("Interface")
        view_label.setStyleSheet(
            "color:#92a0b3;font-family:'Segoe UI';font-size:9px;font-weight:600;"
        )
        view_toggle.addWidget(view_label)
        self.gui_view_btn = FluidButton("GUI")
        self.tui_view_btn = FluidButton("TUI")
        for button, active in [(self.gui_view_btn, True), (self.tui_view_btn, False)]:
            button.setCheckable(True)
            button.setChecked(active)
            button.setMinimumHeight(26)
            button.setCursor(Qt.PointingHandCursor)
            button.setStyleSheet(self._view_toggle_style())
            view_toggle.addWidget(button)
        view_toggle.addStretch()
        root.addLayout(view_toggle)

        from PySide6.QtWidgets import QStackedWidget

        self._interface_stack = QStackedWidget()
        gui_page = QWidget()
        gui_layout = QVBoxLayout(gui_page)
        gui_layout.setContentsMargins(0, 0, 0, 0)
        gui_layout.setSpacing(7)

        self.gui_output = QTextEdit()
        self.gui_output.setReadOnly(True)
        self.gui_output.setMinimumHeight(180)
        self.gui_output.document().setMaximumBlockCount(1500)
        self.gui_output.setStyleSheet("""
            QTextEdit {
                background:#0d0907;color:#f1ded6;border:1px solid #5f392c;
                border-radius:9px;padding:9px;font-family:Consolas;font-size:10px;
                selection-background-color:#633424;
            }
        """)
        gui_layout.addWidget(self.gui_output, 1)

        tui_page = QWidget()
        tui_layout = QVBoxLayout(tui_page)
        tui_layout.setContentsMargins(0, 0, 0, 0)
        tui_layout.setSpacing(0)

        prompt_row = QHBoxLayout()
        prompt_row.setSpacing(6)
        self.prompt_input = QLineEdit()
        self.prompt_input.setPlaceholderText("Message Claude...")
        self.prompt_input.setMinimumHeight(30)
        self.prompt_input.setStyleSheet("""
            QLineEdit {
                background:#21130e;color:#f1ded6;border:1px solid #5f392c;
                border-radius:7px;padding:4px 8px;font-family:'Segoe UI';font-size:10px;
            }
            QLineEdit:focus { border-color:#ed8258; }
        """)
        self.prompt_input.returnPressed.connect(self._send_tui_prompt)
        prompt_row.addWidget(self.prompt_input, 1)

        self.send_prompt_btn = FluidButton("Send")
        self.send_prompt_btn.setMinimumHeight(30)
        self.send_prompt_btn.setCursor(Qt.PointingHandCursor)
        self.send_prompt_btn.setStyleSheet(self._prompt_button_style())
        self.send_prompt_btn.clicked.connect(self._send_tui_prompt)
        prompt_row.addWidget(self.send_prompt_btn)
        gui_layout.addLayout(prompt_row)

        quick_row = QHBoxLayout()
        quick_row.setSpacing(5)
        for label, prompt in [
            (
                "Plan",
                "Analyze this project and propose a concise implementation plan. Do not change files yet.",
            ),
            (
                "Explain",
                "Explain the current codebase structure and the active file in clear, practical terms.",
            ),
            (
                "Fix",
                "Inspect the current project for relevant errors and fix them. Summarize each change.",
            ),
            (
                "Test",
                "Run the relevant project tests or checks and report the results.",
            ),
            ("Clear", "/clear"),
        ]:
            button = FluidButton(label)
            button.setMinimumHeight(26)
            button.setCursor(Qt.PointingHandCursor)
            button.setStyleSheet(self._quick_button_style())
            button.clicked.connect(
                lambda checked=False, text=prompt: self._send_tui_prompt(text)
            )
            quick_row.addWidget(button)
        gui_layout.addLayout(quick_row)

        # ── xterm.js terminal (fills everything below the top bar) ────────
        if HAS_WEBENGINE:
            self._view = QWebEngineView(self)
            self._view.page().settings().setAttribute(
                QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True
            )
            channel = QWebChannel(self._view.page())
            channel.registerObject("bridge", self._bridge)
            self._view.page().setWebChannel(channel)
            self._view.setHtml(_XTERM_HTML, QUrl("qrc:///"))
            self._view.setFocusPolicy(Qt.StrongFocus)
            tui_layout.addWidget(self._view, 1)
        else:
            notice = QLabel("PySide6 WebEngine required.\npip install PySide6", self)
            notice.setStyleSheet(
                "color:#f44747;background:#1a1a1a;padding:12px;"
                "font-family:Consolas;font-size:10px;"
            )
            tui_layout.addWidget(notice, 1)

        self._interface_stack.addWidget(gui_page)
        self._interface_stack.addWidget(tui_page)
        root.addWidget(self._interface_stack, 1)
        self.gui_view_btn.clicked.connect(
            lambda checked=False: self._switch_interface(0)
        )
        self.tui_view_btn.clicked.connect(
            lambda checked=False: self._switch_interface(1)
        )
        self._refresh_header_state()
        self.setStyleSheet(ThemeManager.resolve("""
            ClaudeCodePanel{
                background:#0d0907;
                border:1px solid #5f392c;border-radius:12px;
            }
        """))

    @staticmethod
    def _prompt_button_style():
        return """
            QPushButton {
                background:#b84e2f;color:#fff8f4;border:none;border-radius:7px;
                padding:4px 11px;font-family:'Segoe UI';font-size:10px;font-weight:700;
            }
            QPushButton:hover { background:#ed8258; }
            QPushButton:disabled { background:#24130e;color:#806356; }
        """

    @staticmethod
    def _quick_button_style():
        return """
            QPushButton {
                background:#21130e;color:#edc6b7;border:1px solid #5f392c;border-radius:6px;
                padding:3px 7px;font-family:'Segoe UI';font-size:9px;font-weight:600;
            }
            QPushButton:hover { background:#3a1d14;color:#fff3ed;border-color:#ed8258; }
            QPushButton:disabled { background:#17100d;color:#806356;border-color:#3d241b; }
        """

    @staticmethod
    def _view_toggle_style():
        return """
            QPushButton {
                background:#21130e;color:#d7a08c;border:1px solid #5f392c;border-radius:6px;
                padding:3px 9px;font-family:'Segoe UI';font-size:9px;font-weight:700;
            }
            QPushButton:checked { background:#b84e2f;color:#fff8f4;border-color:#ffad82; }
            QPushButton:hover:!checked { background:#3a1d14;color:#fff3ed; }
        """

    def _switch_interface(self, index):
        if index != self._interface_mode and self._session_active:
            self.session_label.setText("Stop Claude before switching interfaces")
            self.gui_view_btn.setChecked(self._interface_mode == 0)
            self.tui_view_btn.setChecked(self._interface_mode == 1)
            return
        self._interface_mode = index
        self._interface_stack.setCurrentIndex(index)
        self.gui_view_btn.setChecked(index == 0)
        self.tui_view_btn.setChecked(index == 1)
        if index == 1:
            QTimer.singleShot(0, self.refresh_terminal_size)

    def _append_gui_output(self, raw_output):
        """Append clean print-mode output to the native GUI transcript."""
        clean_output = self._bridge._strip_ansi(raw_output).replace("\r", "")
        if not clean_output:
            return
        cursor = self.gui_output.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(clean_output)
        self.gui_output.setTextCursor(cursor)
        self.gui_output.ensureCursorVisible()

    def _show_model_menu(self):
        menu = QMenu(self)
        for label, command in [
            ("Default", "default"),
            ("Fable", "fable"),
            ("Opus", "opus"),
            ("Sonnet", "sonnet"),
            ("Haiku", "haiku"),
        ]:
            action = menu.addAction(label)
            action.triggered.connect(
                lambda checked=False, name=label, value=command: self._select_model(
                    name, value
                )
            )
        menu.exec(
            self.model_menu_btn.mapToGlobal(self.model_menu_btn.rect().bottomLeft())
        )

    def _select_model(self, name, command):
        self._selected_model_name = name
        self._selected_model_command = command
        self._refresh_header_state()
        if self._session_active and self._interface_mode == 1 and command != "default":
            self._bridge.send_prompt(f"/model {command}")
            self.session_label.setText(f"Switching to {name}")
        elif self._session_active and self._interface_mode == 1:
            self.session_label.setText("Default model selected")
        elif self._session_active:
            self.session_label.setText(f"{name} will be used for the next GUI prompt")
        else:
            self.session_label.setText(f"{name} selected for next launch")

    def _show_effort_menu(self):
        menu = QMenu(self)
        for effort in ("low", "medium", "high", "xhigh", "max"):
            action = menu.addAction(effort.title())
            action.triggered.connect(
                lambda checked=False, value=effort: self._select_effort(value)
            )
        menu.exec(
            self.effort_menu_btn.mapToGlobal(self.effort_menu_btn.rect().bottomLeft())
        )

    def _select_effort(self, effort):
        self._selected_effort = effort
        self._refresh_header_state()
        if self._session_active and self._interface_mode == 1:
            self._bridge.send_prompt(f"/effort {effort}")
            self.session_label.setText(f"Effort set to {effort}")
        elif self._session_active:
            self.session_label.setText(
                f"{effort.title()} effort will be used for the next prompt"
            )
        else:
            self.session_label.setText(
                f"{effort.title()} effort selected for next launch"
            )

    def _show_mode_menu(self):
        menu = QMenu(self)
        for label, mode in [("Default", "default"), ("Plan", "plan"), ("Auto", "auto")]:
            action = menu.addAction(label)
            action.triggered.connect(
                lambda checked=False, name=label, value=mode: self._select_mode(
                    name, value
                )
            )
        menu.exec(
            self.mode_menu_btn.mapToGlobal(self.mode_menu_btn.rect().bottomLeft())
        )

    def _select_mode(self, name, mode):
        self._selected_mode = mode
        self._refresh_header_state()
        if self._session_active and self._interface_mode == 1:
            self.session_label.setText(f"{name} mode will apply after Stop and Launch")
        elif self._session_active:
            self.session_label.setText(f"{name} mode will be used for the next prompt")
        else:
            self.session_label.setText(f"{name} mode selected for next launch")

    def _toggle_auto_accept_edits(self):
        self._auto_accept_edits = not self._auto_accept_edits
        self._refresh_header_state()
        state = "on" if self._auto_accept_edits else "off"
        if self._session_active and self._interface_mode == 1:
            self.session_label.setText(
                f"Accept edits {state} applies after Stop and Launch"
            )
        else:
            self.session_label.setText(f"Accept edits {state}")

    def _effective_permission_mode(self):
        return "acceptEdits" if self._auto_accept_edits else self._selected_mode

    def _refresh_header_state(self):
        mode_label = (
            "Accept edits" if self._auto_accept_edits else self._selected_mode.title()
        )
        self.active_model_label.setText(
            f"{self._selected_model_name} / {self._selected_effort} / {mode_label}"
        )
        self.model_menu_btn.setText(f"Model: {self._selected_model_name}")
        if hasattr(self, "effort_menu_btn"):
            self.effort_menu_btn.setText(f"Effort: {self._selected_effort}")
            self.mode_menu_btn.setText(f"Mode: {self._selected_mode.title()}")
            self.auto_accept_btn.setText(
                "Accept: On" if self._auto_accept_edits else "Accept: Off"
            )

    # ── Slots ───────────────────────────────────────────────────────────

    @staticmethod
    def _fetch_ollama_models() -> list:
        try:
            result = subprocess.run(
                ["ollama", "list"], capture_output=True, text=True, timeout=10
            )
            lines = result.stdout.strip().splitlines()
            models = []
            for line in lines[1:]:
                parts = line.split()
                if parts:
                    models.append(parts[0])
            return models if models else ClaudeCodePanel._FALLBACK_MODELS
        except Exception:
            return ClaudeCodePanel._FALLBACK_MODELS

    def _populate_models(self):
        self.model_combo.setEnabled(False)
        self.model_combo.clear()
        self.model_combo.addItem("Loading models…")

        def _worker():
            models = ClaudeCodePanel._fetch_ollama_models()
            QTimer.singleShot(0, lambda: self._on_models_loaded(models))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_models_loaded(self, models: list):
        self.model_combo.clear()
        for m in models:
            self.model_combo.addItem(m)
        self.model_combo.setEnabled(True)
        saved = self._bridge._model
        if saved:
            idx = self.model_combo.findText(saved)
            if idx >= 0:
                self.model_combo.setCurrentIndex(idx)

    def _default_cwd(self) -> str:
        """Return the IDE's project root, current file directory, or home."""
        root = getattr(self.ide, "project_root", None)
        if root and os.path.isdir(root):
            return root
        if self.ide.current_file_path:
            d = os.path.dirname(self.ide.current_file_path)
            if os.path.isdir(d):
                return d
        return os.path.expanduser("~")

    def set_working_directory(self, path):
        """Stage a folder for the next explicit launch without touching a live TUI."""
        if not path or not os.path.isdir(path):
            return False
        if self._session_active:
            self.session_label.setText("Stop Claude before changing folders")
            self.session_label.setStyleSheet(
                "color:#ff9bab;font-family:'Segoe UI';font-size:9px;font-weight:600;"
            )
            return False

        self._launch_directory = os.path.abspath(path)
        self.directory_field.setText(self._launch_directory)
        self.directory_field.setToolTip(self._launch_directory)
        self.session_label.setText("Ready")
        self.session_label.setStyleSheet(
            "color:#67c587;font-family:'Segoe UI';font-size:9px;font-weight:600;"
        )
        return True

    def _launch_model(self):
        if self._session_active:
            return
        cwd = self._launch_directory or self._default_cwd()
        if not os.path.isdir(cwd):
            self.session_label.setText("Select a valid folder first")
            return

        if self._interface_mode == 0:
            self._session_active = True
            self.launch_btn.setEnabled(False)
            self.kill_btn.setEnabled(True)
            self.session_label.setText("GUI ready")
            self._append_gui_output(
                "\nClaude GUI is ready. Send a message below for a clean response.\n\n"
            )
            return

        self._editor_first_chunk = True
        self._bridge._in_code_block = False
        self._bridge._raw_buf = ""
        if not self._bridge.launch_model(
            self._selected_model_command,
            cwd,
            self._selected_effort,
            self._effective_permission_mode(),
        ):
            return
        self._session_active = True
        self.launch_btn.setEnabled(False)
        self.kill_btn.setEnabled(True)
        self.session_label.setText("Starting")
        self.session_label.setStyleSheet(
            "color:#73bdff;font-family:'Segoe UI';font-size:9px;font-weight:600;"
        )
        if HAS_WEBENGINE:
            QTimer.singleShot(150, self._view.setFocus)

    def _on_code_chunk(self, chunk: str):
        """Stream code fenced output directly into the active editor."""
        editor = getattr(self.ide, "current_editor", None)
        if not editor or not chunk:
            return
        if self._editor_first_chunk:
            editor.clear()
            self._editor_first_chunk = False
        cursor = editor.textCursor()
        cursor.movePosition(QTextCursor.End)
        editor.setTextCursor(cursor)
        editor.insertPlainText(chunk)

    def _stop_model(self):
        if self._interface_mode == 0:
            if self._gui_request and self._gui_request.isRunning():
                self._gui_request.stop()
        else:
            self._bridge.kill()
        self._session_active = False
        self.launch_btn.setEnabled(True)
        self.kill_btn.setEnabled(False)
        self.session_label.setText("Stopped - choose a folder, then launch")
        self.session_label.setStyleSheet(
            "color:#92a0b3;font-family:'Segoe UI';font-size:9px;font-weight:600;"
        )

    def _on_session_state_changed(self, running):
        if self._interface_mode == 0:
            return
        self._session_active = running
        self.launch_btn.setEnabled(not running)
        self.kill_btn.setEnabled(running)
        if running:
            self.session_label.setText("Running")
            self.session_label.setStyleSheet(
                "color:#67c587;font-family:'Segoe UI';font-size:9px;font-weight:600;"
            )
        else:
            self.session_label.setText("Stopped - choose a folder, then launch")
            self.session_label.setStyleSheet(
                "color:#92a0b3;font-family:'Segoe UI';font-size:9px;font-weight:600;"
            )

    def _send_tui_prompt(self, prompt=None):
        """Dispatch GUI actions to the selected Claude interface."""
        if self._interface_mode == 0:
            self._send_gui_prompt(prompt)
            return
        if not self._session_active:
            self.session_label.setText("Launch Claude before sending a prompt")
            return
        text = (prompt if isinstance(prompt, str) else self.prompt_input.text()).strip()
        if not text:
            return
        self._bridge.send_prompt(text)
        if not isinstance(prompt, str):
            self.prompt_input.clear()
        self.session_label.setText("Prompt sent")

    def _send_gui_prompt(self, prompt=None):
        if not self._session_active:
            self.session_label.setText("Launch Claude before sending a prompt")
            return
        if self._gui_request and self._gui_request.isRunning():
            self.session_label.setText("Claude is still responding")
            return

        text = (prompt if isinstance(prompt, str) else self.prompt_input.text()).strip()
        if not text:
            return
        if not isinstance(prompt, str):
            self.prompt_input.clear()

        self._append_gui_output(f"\nYou\n{text}\n\nClaude\n")
        self.session_label.setText("Claude is responding")
        self._gui_request = ClaudeGUIRequestWorker(
            text,
            self._launch_directory or self._default_cwd(),
            self._selected_model_command,
            self._selected_effort,
            self._effective_permission_mode(),
            self,
        )
        self._gui_request.outputReady.connect(self._append_gui_output)
        self._gui_request.failed.connect(self._append_gui_error)
        self._gui_request.finished.connect(self._on_gui_request_finished)
        self._gui_request.start()

    def _append_gui_error(self, message):
        self._append_gui_output(f"\n[Claude GUI] {message}\n")

    def _on_gui_request_finished(self):
        self._gui_request = None
        if self._session_active and self._interface_mode == 0:
            self.session_label.setText("GUI ready")

    def refresh_terminal_size(self):
        """Ask xterm to re-fit after the surrounding AI panel changes width."""
        if HAS_WEBENGINE and hasattr(self, "_view"):
            self._view.page().runJavaScript(
                "window.dispatchEvent(new Event('resize'));"
            )

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if HAS_WEBENGINE:
            self._fit_timer.start()

    def cleanup(self):
        self._bridge.kill()


# ============================================================================
# AI Panel  (wraps Cody + Claude Code with a top-switcher)
# ============================================================================


@dataclass
class MessageData:
    role: str
    content: str = ""
    tool_calls: str = ""
    thinking: str = ""
    raw_response: str = ""
    show_tools: bool = False
    show_thinking: bool = False


class AIPanelWidget(QWidget):
    """ENHANCED Professional AI Assistant Panel with advanced animations"""

    expansion_requested = Signal(bool)

    def update_live_directory_display(self, absolute_path):
        """Updates the top bar in Cody with the live working folder location."""
        if hasattr(self, "directory_bar"):
            # Cleanly format or shorten the path string if needed
            folder_name = os.path.basename(absolute_path) or absolute_path
            self.directory_bar.setText(f"📂 Workspace: {folder_name} ({absolute_path})")

            # ====================================================================
        # ADD THIS VISUAL BAR AT THE TOP OF CODY PANEL:
        # ====================================================================
        self.directory_bar = QLabel("📂 Workspace: Tracking active folder...")
        self.directory_bar.setStyleSheet("""
            QLabel {
                background-color: #171b24;
                color: #8fa1b3;
                font-family: 'Consolas', 'Segoe UI';
                font-size: 11px;
                padding: 6px 10px;
                border: 1px solid #232b38;
                border-radius: 4px;
                margin-bottom: 4px;
                font-weight: bold;
            }
        """)

    def update_live_directory_display(self, absolute_path):
        """Updates the visual path tracking element at the top of Cody"""
        if hasattr(self, "directory_bar"):
            folder_name = os.path.basename(absolute_path) or absolute_path
            self.directory_bar.setText(f"📂 Workspace: {folder_name}")

    def _resolve_workspace_directory(self, requested_path=None):
        """Return the active workspace directory for tool execution and agent actions."""
        if requested_path:
            candidate = requested_path.strip()
            if candidate:
                return candidate

        if hasattr(self, "ide") and self.ide:
            ide = self.ide
            for candidate in (
                getattr(ide, "project_root", None),
                getattr(getattr(ide, "file_explorer", None), "project_root", None),
            ):
                if candidate and os.path.isdir(candidate):
                    return candidate

            current_file = getattr(ide, "current_file_path", None)
            if current_file:
                current_dir = os.path.dirname(current_file)
                if os.path.isdir(current_dir):
                    return current_dir

        return os.getcwd()

    def __init__(self, ide, parent=None):
        super().__init__(parent)
        self.ide = ide
        self.conversation_history = []
        self.current_file = None
        self.ai_provider = "ollama"
        self.ollama_model = "deepseek-coder:6.7b"
        self.auto_accept_edits = True
        self._last_code_block = None
        self.action_buttons = []
        self.particle_system = None
        self._expanded = False
        self.directory_bar = QLabel("📂 Workspace: Loading...")
        self.directory_bar.setStyleSheet("""
            QLabel {
                background-color: #1a1f29;
                color: #8fa1b3;
                font-family: 'Consolas', 'Segoe UI';
                font-size: 11px;
                padding: 6px 10px;
                border-bottom: 1px solid #232b38;
                font-weight: bold;
            }
        """)

        # Chat management
        self.chats_directory = os.path.join(os.path.expanduser("~"), ".ide_chats")
        os.makedirs(self.chats_directory, exist_ok=True)
        self.current_chat_file = None

        # Structured message store for clean rendering with collapsible sections
        self.messages: List[MessageData] = []

        # Available models
        # --- REPLACE THE HARDCODED MODELS WITH THIS ---
        try:
            import urllib.request
            import json

            url = "http://localhost:11434/api/tags"
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=1.5) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode("utf-8"))
                    models = [model["name"] for model in data.get("models", [])]
                    if models:
                        self.available_models = {m: m for m in models}
                    else:
                        self.available_models = {
                            "minimax-m2.1": "minimax-m2.1",
                            "deepseek-coder:6.7b": "deepseek-coder:6.7b",
                        }
                else:
                    self.available_models = {
                        "minimax-m2.1": "minimax-m2.1",
                        "deepseek-coder:6.7b": "deepseek-coder:6.7b",
                    }
        except Exception:
            self.available_models = {
                "minimax-m2.1": "minimax-m2.1",
                "deepseek-coder:6.7b": "deepseek-coder:6.7b",
            }

        # Then fill your QComboBox items using the dynamic keys:
        if hasattr(self, "model_combo"):
            self.model_combo.clear()
            self.model_combo.addItems(list(self.available_models.keys()))
        # ----------------------------------------------

        # Initialize AI response streaming state variables
        # FULL raw response accumulator (includes tool tags) — used by on_ai_finished
        # for history storage and for the IDE-level process_agent_response() tool scanner.
        self._current_response = ""
        # Unprocessed tail of the live token stream (tool-interception buffer).
        self._raw_buffer = ""
        # Visible text that has cleared the tool interceptor and is queued for
        # code-fence / chat routing.
        self._visible_buffer = ""
        # Tool-interception state machine.
        self._in_hidden_tool = False
        self._current_tool_tag = ""
        self._tool_buffer = ""
        # Collected completed tool payloads during a single stream cycle.
        # Executed AFTER the worker thread terminates (see on_ai_finished).
        self._intercepted_tools = []
        # Code-fence routing state.
        self._in_code_block = False
        self._code_block_count = 0
        self._code_accumulator = ""
        self._chat_header_added = False
        # Thread-safety guards for the autonomous continuation engine.
        self._streaming_active = False
        self._continuation_queued = False

        self.setup_ui()

    def setup_ui(self):
        # ── Outer layout holds switcher + stacked widget ──────────────
        outer = QVBoxLayout(self)
        outer.setSpacing(0)
        outer.setContentsMargins(0, 0, 0, 0)

        # ===== TOP MODE SWITCHER =====
        switcher_bar = QWidget()
        switcher_bar.setFixedHeight(48)
        switcher_bar.setStyleSheet(
            ThemeManager.resolve("background:#171b24;border-bottom:1px solid #394353;")
        )
        sw_layout = QHBoxLayout(switcher_bar)
        sw_layout.setContentsMargins(12, 7, 10, 7)
        sw_layout.setSpacing(6)

        mode_lbl = QLabel("AI")
        mode_lbl.setToolTip("AI workspace")
        mode_lbl.setStyleSheet(
            "color:#92a0b3;font-family:'Segoe UI';font-size:9px;font-weight:700;"
            "letter-spacing:1px;"
        )
        sw_layout.addWidget(mode_lbl)

        self._btn_cody = FluidButton("Cody")
        self._btn_claude = FluidButton("Claude")
        for btn, active in [(self._btn_cody, True), (self._btn_claude, False)]:
            btn.setCursor(Qt.PointingHandCursor)
            btn.setCheckable(True)
            btn.setChecked(active)
            btn.setMinimumHeight(32)
            btn.setStyleSheet(self._mode_btn_style())
        sw_layout.addWidget(self._btn_cody)
        sw_layout.addWidget(self._btn_claude)
        sw_layout.addStretch()

        self.expand_btn = FluidButton("Expand")
        self.expand_btn.setToolTip(
            "Expand the AI workspace for a wider Claude terminal"
        )
        self.expand_btn.setCursor(Qt.PointingHandCursor)
        self.expand_btn.setMinimumHeight(30)
        self.expand_btn.setStyleSheet(self._expand_btn_style())
        self.expand_btn.clicked.connect(self._request_expansion)
        sw_layout.addWidget(self.expand_btn)

        outer.addWidget(switcher_bar)

        # ===== STACKED WIDGET (page 0 = Cody, page 1 = Claude Code) =====
        from PySide6.QtWidgets import QStackedWidget, QScrollArea

        self._stack = QStackedWidget()
        outer.addWidget(self._stack)

        # ── Page 0: Cody (scroll area wrapping existing content) ─────
        cody_scroll = QScrollArea()
        cody_scroll.setWidgetResizable(True)
        cody_scroll.setFrameShape(QFrame.NoFrame)
        cody_scroll.setStyleSheet("QScrollArea{background:transparent;border:none;}")
        cody_page = QWidget()
        cody_scroll.setWidget(cody_page)
        self._stack.addWidget(cody_scroll)

        # Keep the terminal out of a scroll area so xterm receives its real size.
        self.claude_panel = ClaudeCodePanel(self.ide, self)
        self._stack.addWidget(self.claude_panel)

        # Wire switcher buttons
        self._btn_cody.clicked.connect(lambda: self._switch_mode(0))
        self._btn_claude.clicked.connect(lambda: self._switch_mode(1))

        # Cody content goes into cody_page
        layout = QVBoxLayout(cody_page)
        layout.setSpacing(12)
        layout.setContentsMargins(14, 16, 14, 14)

        # ===== HEADER SECTION =====
        header_layout = QHBoxLayout()
        header_layout.setSpacing(14)

        # Animated logo - BIGGER
        self.logo = AnimatedAILogo()
        self.logo.setMaximumSize(100, 100)
        self.logo.setMinimumSize(100, 100)
        header_layout.addWidget(self.logo)

        # Title and status with better styling
        title_layout = QVBoxLayout()
        title_layout.setSpacing(4)

        title_label = QLabel("Cody - Your AI Coding Companion")
        title_font = QFont("Segoe UI", 14, QFont.Bold)
        title_label.setFont(title_font)
        title_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
            }
        """)
        title_layout.addWidget(title_label)

        self.model_label = QLabel("Powered by: DeepSeek and MiniMax")
        self.model_label.setStyleSheet("""
            QLabel {
                color: #7acc7a;
                font-family: 'Segoe UI';
                font-size: 9px;
                font-weight: 500;
                letter-spacing: 0.5px;
            }
        """)
        title_layout.addWidget(self.model_label)

        # Status indicator
        self.status_indicator = QLabel("● Ready")
        self.status_indicator.setStyleSheet("""
            QLabel {
                color: #00ff88;
                font-family: 'Segoe UI';
                font-size: 9px;
                font-weight: bold;
            }
        """)
        title_layout.addWidget(self.status_indicator)

        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # ====================================================================
        # STEP 1: ADD THIS LIVE DIRECTORY DISPLAY BAR RIGHT BELOW THE LOGO
        # ====================================================================
        self.directory_bar = QLabel("📂 Workspace: Tracking active folder...")
        self.directory_bar.setStyleSheet("""
            QLabel {
                background-color: #10131a;
                color: #8fa1b3;
                font-family: 'Consolas', 'Segoe UI';
                font-size: 11px;
                padding: 6px 10px;
                border: 1px solid #232b38;
                border-radius: 6px;
                margin: 4px 0px 8px 0px;
                font-weight: bold;
            }
        """)
        layout.addWidget(self.directory_bar)

        # Enhanced header divider with gradient
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setFixedHeight(2)
        divider.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 transparent, 
                    stop:0.2 #007acc,
                    stop:0.5 #0e639c,
                    stop:0.8 #007acc,
                    stop:1 transparent);
                border: none;
            }
        """)
        layout.addWidget(divider)

        # ===== CONVERSATION DISPLAY =====
        conv_label = QLabel("Conversation")
        conv_label.setStyleSheet("""
            QLabel {
                color: #aaaaaa;
                font-family: 'Segoe UI';
                font-size: 9px;
                font-weight: bold;
                letter-spacing: 0.8px;
                padding: 4px 0px;
            }
        """)
        layout.addWidget(conv_label)

        self.conversation_text = QTextBrowser()
        self.conversation_text.setReadOnly(True)
        self.conversation_text.setOpenExternalLinks(False)
        self.conversation_text.setOpenLinks(False)
        font_ui = QFont("Segoe UI", 10)
        font_ui.setPointSize(10)
        self.conversation_text.setFont(font_ui)
        self.conversation_text.setMinimumHeight(150)
        self.conversation_text.setStyleSheet("""
            QTextBrowser {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1a1a1e,
                    stop:1 #2a2a2e);
                color: #e0e0e0;
                border: 1px solid #404050;
                border-radius: 8px;
                padding: 12px;
                line-height: 1.5;
                font-family: "Segoe UI";
                font-size: 10px;
            }
            QTextBrowser:focus {
                border: 2px solid #0099ff;
            }
        """)
        self.conversation_text.anchorClicked.connect(self._on_anchor_click)
        layout.addWidget(self.conversation_text)

        # ===== CHAT MANAGEMENT SECTION =====
        chat_mgmt_label = QLabel("Chat Management")
        chat_mgmt_label.setStyleSheet("""
            QLabel {
                color: #aaaaaa;
                font-family: 'Segoe UI';
                font-size: 9px;
                font-weight: bold;
                letter-spacing: 0.8px;
                padding: 6px 0px 2px 0px;
            }
        """)
        layout.addWidget(chat_mgmt_label)

        chat_mgmt_layout = QHBoxLayout()
        chat_mgmt_layout.setSpacing(6)

        # Clear Chat button
        self.clear_chat_btn = FluidButton("🗑 Clear Chat")
        self.clear_chat_btn.setMinimumHeight(28)
        self.clear_chat_btn.setCursor(Qt.PointingHandCursor)
        self.clear_chat_btn.clicked.connect(self.clear_and_save_chat)
        self.clear_chat_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4a3a3a,
                    stop:1 #2a1a1a);
                color: #ff9999;
                border: 1px solid #8844443a;
                border-radius: 5px;
                padding: 5px 8px;
                font-weight: 600;
                font-family: "Segoe UI";
                font-size: 9px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ff6b6baa,
                    stop:1 #cc3333);
                color: #ffffff;
                border: 2px solid #ff6b6b;
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #cc3333,
                    stop:1 #991111);
            }
        """)
        chat_mgmt_layout.addWidget(self.clear_chat_btn)

        # Load Chat button
        self.load_chat_btn = FluidButton("📂 Load Chat")
        self.load_chat_btn.setMinimumHeight(28)
        self.load_chat_btn.setCursor(Qt.PointingHandCursor)
        self.load_chat_btn.clicked.connect(self.load_chat)
        self.load_chat_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3a4a4a,
                    stop:1 #1a2a2a);
                color: #99ccff;
                border: 1px solid #44888899;
                border-radius: 5px;
                padding: 5px 8px;
                font-weight: 600;
                font-family: "Segoe UI";
                font-size: 9px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #6b9bffaa,
                    stop:1 #3366cc);
                color: #ffffff;
                border: 2px solid #6b9bff;
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3366cc,
                    stop:1 #1a4488);
            }
        """)
        chat_mgmt_layout.addWidget(self.load_chat_btn)
        chat_mgmt_layout.addStretch()

        layout.addLayout(chat_mgmt_layout)

        # ===== MODEL SWITCHER SECTION =====
        model_label = QLabel("AI Model")
        model_label.setStyleSheet("""
            QLabel {
                color: #aaaaaa;
                font-family: 'Segoe UI';
                font-size: 9px;
                font-weight: bold;
                letter-spacing: 0.8px;
                padding: 6px 0px 2px 0px;
            }
        """)
        layout.addWidget(model_label)

        self.model_combo = QComboBox()
        self.model_combo.addItems(list(self.available_models.keys()))
        self.model_combo.setCurrentText("DeepSeek Coder 6.7B (Local)")
        self.model_combo.currentTextChanged.connect(self.switch_model)
        self.model_combo.setCursor(Qt.PointingHandCursor)
        self.model_combo.setMinimumHeight(28)
        self.model_combo.setStyleSheet("""
            QComboBox {
                background-color: #2a2a30;
                color: #d0d0d0;
                border: 1px solid #404050;
                border-radius: 5px;
                padding: 5px 8px;
                font-family: "Segoe UI";
                font-size: 10px;
                font-weight: 500;
            }
            QComboBox:hover {
                background-color: #323238;
                border-color: #0099ff;
            }
            QComboBox::drop-down {
                border: none;
                width: 22px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid #aaaaaa;
                width: 0;
                height: 0;
            }
            QComboBox QAbstractItemView {
                background-color: #1a1a1e;
                color: #d0d0d0;
                selection-background-color: #0099ff;
                selection-color: #ffffff;
                border: 1px solid #404050;
                border-radius: 4px;
                padding: 3px 0;
                outline: none;
            }
            QComboBox QAbstractItemView::item {
                padding: 6px 12px;
                min-height: 24px;
            }
        """)
        layout.addWidget(self.model_combo)

        # ===== ACTION BUTTONS - WITH GRADIENT HOVER =====
        buttons_label = QLabel("Quick Actions")
        buttons_label.setStyleSheet("""
            QLabel {
                color: #aaaaaa;
                font-family: 'Segoe UI';
                font-size: 9px;
                font-weight: bold;
                letter-spacing: 0.8px;
                padding: 8px 0px 4px 0px;
            }
        """)
        layout.addWidget(buttons_label)

        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(7)

        button_configs = [
            ("📚 Explain", self.explain_code, "#0066cc"),
            ("✨ Generate", self.generate_code, "#6600cc"),
            ("🔧 Fix", self.fix_errors, "#cc3300"),
            ("⚡ Refactor", self.refactor_code, "#00cc66"),
        ]

        for label, handler, color in button_configs:
            btn = self._create_fancy_button(label, handler, color)
            self.action_buttons.append(btn)
            buttons_layout.addWidget(btn)

        layout.addLayout(buttons_layout)

        # ===== APPLY CONTROLS =====
        apply_layout = QHBoxLayout()
        apply_layout.setSpacing(8)

        self.auto_apply_checkbox = QCheckBox("Auto-apply")
        self.auto_apply_checkbox.setChecked(self.auto_accept_edits)
        self.auto_apply_checkbox.setStyleSheet(self._get_checkbox_style())
        self.auto_apply_checkbox.stateChanged.connect(self.toggle_auto_apply)
        apply_layout.addWidget(self.auto_apply_checkbox)

        apply_layout.addStretch()

        self.apply_btn = FluidButton("Apply to Editor")
        self.apply_btn.setMinimumHeight(32)
        self.apply_btn.setStyleSheet(self._get_apply_button_style())
        self.apply_btn.clicked.connect(self.apply_code_to_editor)
        self.apply_btn.setEnabled(False)
        self.apply_btn.setCursor(Qt.PointingHandCursor)
        apply_layout.addWidget(self.apply_btn)

        layout.addLayout(apply_layout)

        # ===== INPUT AREA =====
        input_label = QLabel("Send Message")
        input_label.setStyleSheet("""
            QLabel {
                color: #aaaaaa;
                font-family: 'Segoe UI';
                font-size: 9px;
                font-weight: bold;
                letter-spacing: 0.8px;
                padding: 8px 0px 4px 0px;
            }
        """)
        layout.addWidget(input_label)

        self.input_text = QTextEdit()
        self.input_text.setMaximumHeight(80)
        self.input_text.setMinimumHeight(50)
        self.input_text.setPlaceholderText("Ask Cody about your code...")
        font_ui2 = QFont("Segoe UI", 10)
        self.input_text.setFont(font_ui2)
        self.input_text.setStyleSheet("""
            QTextEdit {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #262629,
                    stop:1 #1e1e23);
                color: #e0e0e0;
                border: 1px solid #404050;
                border-radius: 6px;
                padding: 10px;
                font-family: "Segoe UI";
                font-size: 10px;
                selection-background-color: #0099ff;
            }
            QTextEdit:focus {
                border: 2px solid #0099ff;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2a2a30,
                    stop:1 #222227);
            }
        """)
        layout.addWidget(self.input_text)

        # Send button - ENHANCED
        self.send_btn = FluidButton("▶ Send Message")
        self.send_btn.setMinimumHeight(36)
        self.send_btn.setStyleSheet(self._get_send_button_style())
        self.send_btn.clicked.connect(self.send_message)
        self.send_btn.setCursor(Qt.PointingHandCursor)
        layout.addWidget(self.send_btn)

        # Status label with animations
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("""
            QLabel {
                color: #88ddaa;
                font-style: italic;
                font-family: 'Segoe UI';
                font-size: 9px;
                padding: 4px 0px;
            }
        """)
        layout.addWidget(self.status_label)

        layout.addStretch()

        # Panel background
        self.setStyleSheet(ThemeManager.resolve("""
            AIPanelWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #1a1a20,
                    stop:0.5 #1e1e28,
                    stop:1 #1a1a24);
                border-left: 2px solid #0099ff;
                border-radius: 2px;
            }
        """))

    # ── Mode switcher helpers ─────────────────────────────────────────────

    def _mode_btn_style(self):
        return """
            QPushButton {
                background:#252c37;color:#92a0b3;
                border:1px solid #394353;border-radius:8px;
                padding:5px 11px;font-weight:600;
                font-family:"Segoe UI";font-size:10px;
            }
            QPushButton:checked {
                background:qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #4aa3ff,stop:1 #2877d4);
                color:#f7fbff;border:1px solid #73bdff;
            }
            QPushButton:hover:!checked {
                background:#313a49;color:#f7fbff;border-color:#73bdff;
            }
        """

    def _expand_btn_style(self):
        return """
            QPushButton {
                background:transparent;color:#c7d0dd;
                border:1px solid #394353;border-radius:8px;
                padding:5px 10px;font-family:"Segoe UI";font-size:10px;
            }
            QPushButton:hover {
                background:#313a49;color:#f7fbff;border-color:#73bdff;
            }
        """

    def _switch_mode(self, index: int):
        self._stack.setCurrentIndex(index)
        self._btn_cody.setChecked(index == 0)
        self._btn_claude.setChecked(index == 1)
        if index == 1:
            QTimer.singleShot(0, self.refresh_terminal_size)

    def _request_expansion(self):
        self.expansion_requested.emit(not self._expanded)

    def set_expanded(self, expanded):
        self._expanded = expanded
        self.expand_btn.setText("Compact" if expanded else "Expand")
        self.expand_btn.setToolTip(
            "Return the AI workspace to its compact width"
            if expanded
            else "Expand the AI workspace for a wider Claude terminal"
        )

    def refresh_terminal_size(self):
        self.claude_panel.refresh_terminal_size()

    def _create_fancy_button(self, label, handler, accent_color):
        """Create a button with fancy hover effects and gradients"""
        btn = FluidButton(label)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setMinimumHeight(34)

        style = f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2a3a4a,
                    stop:1 #1a2a3a);
                color: #d0d0d0;
                border: 1px solid {accent_color}40;
                border-radius: 6px;
                padding: 8px 6px;
                font-weight: 600;
                font-family: "Segoe UI";
                font-size: 10px;
                letter-spacing: 0.3px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {accent_color}aa,
                    stop:0.5 {accent_color}88,
                    stop:1 {accent_color}66);
                color: #ffffff;
                border: 2px solid {accent_color};
            }}
            QPushButton:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {accent_color}88,
                    stop:1 {accent_color}44);
                border: 2px solid {accent_color}ff;
            }}
        """
        btn.setStyleSheet(style)
        btn.clicked.connect(handler)
        return btn

    def _get_checkbox_style(self):
        return """
            QCheckBox {
                color: #aaaaaa;
                font-family: "Segoe UI";
                font-size: 10px;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border-radius: 4px;
                border: 1px solid #555555;
                background-color: #2a2a2a;
            }
            QCheckBox::indicator:hover {
                background-color: #3a3a3a;
                border-color: #0099ff;
            }
            QCheckBox::indicator:checked {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0099ff,
                    stop:1 #0066cc);
                border-color: #0099ff;
            }
        """

    def _get_apply_button_style(self):
        return """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #0e639c,
                    stop:1 #0a4d7d);
                color: #ffffff;
                border: 1px solid #007acc;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 600;
                font-family: "Segoe UI";
                font-size: 10px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1177bb,
                    stop:1 #0e639c);
                border: 2px solid #00ddff;
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #0a4d7d,
                    stop:1 #063a5a);
                border: 2px solid #00ddff;
            }
            QPushButton:disabled {
                background-color: #2a2a2a;
                color: #555555;
                border: 1px solid #404040;
            }
        """

    def _get_send_button_style(self):
        return """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #0099ff,
                    stop:0.5 #0066ff,
                    stop:1 #0044ff);
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 10px 16px;
                font-weight: 700;
                font-family: "Segoe UI";
                font-size: 11px;
                letter-spacing: 0.5px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00ccff,
                    stop:0.5 #0099ff,
                    stop:1 #0077ff);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #0077dd,
                    stop:0.5 #0055dd,
                    stop:1 #0033dd);
            }
            QPushButton:disabled {
                background: #2a2a2a;
                color: #555555;
            }
        """

    def get_button_style(self):
        """Legacy method - kept for compatibility"""
        return """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2a3d50,
                    stop:1 #1a2a3a);
                color: #9cdcfe;
                border: 1px solid #2f5475;
                border-radius: 5px;
                padding: 7px 4px;
                font-weight: bold;
                font-family: "Segoe UI";
                font-size: 10px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #094771,
                    stop:1 #063a55);
                border-color: #007acc;
                color: #ffffff;
                box-shadow: 0px 0px 8px #007acc66;
            }
            QPushButton:pressed {
                background-color: #063655;
                color: #ffffff;
            }
        """

    def get_send_button_style(self):
        """Legacy method - overridden in setup_ui"""
        return self._get_send_button_style()

    def add_message(self, role, content):
        """Add a message to conversation with enhanced styling and animations"""
        msg = MessageData(role=role, content=content)
        self.messages.append(msg)
        self.conversation_history.append({"role": role, "content": content})
        self._render_conversation()

        # Update status indicator
        self.status_indicator.setText(
            "● Processing<br>"
            '<span style="font-size:8px;color:#ffaa00;">'
            "Tip: Tell cody to plan and keep sharing live tasks to immeditatly stop it when in its thinking it goes in wrong directions!"
            "</span>"
        )
        self.status_indicator.setStyleSheet("""
            QLabel {
                color: #ffaa00;
                font-family: 'Segoe UI';
                font-size: 9px;
                font-weight: bold;
            }
        """)

    def send_message(self, custom_prompt=None):
        """Send message to AI with automated live directory & open file context tracking"""
        prompt = custom_prompt or self.input_text.toPlainText().strip()
        if not prompt:
            return

        # ── THREAD-SAFE CONTINUATION GUARD ──────────────────────────────
        # If a worker is still streaming, do NOT spawn a second one — that
        # corrupts the network pipe and drops buffers (the original crash).
        # Queue the message; on_ai_finished will drain it once the stream
        # has fully terminated and state has been reset.
        if getattr(self, "_streaming_active", False):
            self._continuation_queued = True
            self._pending_continuation_prompt = prompt
            return

        # 1. Gather dynamic environment awareness data
        active_dir = self._resolve_workspace_directory()
        try:
            visible_files = [f for f in os.listdir(active_dir) if not f.startswith(".")]
        except Exception:
            visible_files = []

        # 2. Extract active open editor tab context tracking
        open_file_name = "No open file"
        open_file_content = ""
        if (
            hasattr(self, "ide")
            and self.ide
            and hasattr(self.ide, "get_active_workspace_context")
        ):
            open_file_name, open_file_content = self.ide.get_active_workspace_context()

        # 3. Bake live workspace telemetry straight into the agent's message payload
        telemetry_envelope = (
            f"[LIVE WORKSPACE CONTEXT]\n"
            f"- ACTIVE DIRECTORY: {active_dir}\n"
            f"- PROJECT ROOT FILES: {visible_files}\n"
            f"- CURRENTLY FOCUSED FILE: {open_file_name}\n"
            f"--- START FILE FOCUS CONTENT ---\n{open_file_content}\n--- END FILE FOCUS CONTENT ---\n\n"
            f"User Instruction: {prompt}"
        )

        self.add_message("user", prompt)
        self.input_text.clear()
        self.send_btn.setEnabled(False)

        # Clear active stream state context buffers (FULL reset so deferred
        # continuation hooks from the previous cycle can never see stale state).
        self._current_response = ""
        self._raw_buffer = ""
        self._visible_buffer = ""
        self._in_hidden_tool = False
        self._current_tool_tag = ""
        self._tool_buffer = ""
        self._intercepted_tools = []
        self._in_code_block = False
        self._code_block_count = 0
        self._code_accumulator = ""
        self._chat_header_added = False
        self._continuation_queued = False
        self._pending_continuation_prompt = None
        self._streaming_active = True

        # Build message history chain payload array
        messages = []
        if AGENT_SYSTEM_PROMPT:
            messages.append({"role": "system", "content": AGENT_SYSTEM_PROMPT})

        # Append historical records
        for msg in self.conversation_history[-10:]:  # Keep recent history context
            messages.append({"role": msg["role"], "content": msg["content"]})

        # Swap out the last user message string with our enriched context container
        if messages and messages[-1]["role"] == "user":
            messages[-1]["content"] = telemetry_envelope

        # Update visual animations state
        self.logo.set_state("thinking")
        self.status_label.setText("Thinking...")

        self.status_indicator.setText("● Processing")
        self.status_indicator.setStyleSheet("""
            QLabel {
                color: #ffaa00;
                font-family: 'Segoe UI';
                font-size: 9px;
                font-weight: bold;
            }
        """)

        # Execute stream background thread dispatch
        self.worker = AIWorkerThread(self.ai_provider, messages, self.ollama_model)
        self.worker.response_received.connect(self.on_ai_response)
        self.worker.error_occurred.connect(self.on_ai_error)
        self.worker.finished_signal.connect(self.on_ai_finished)
        self.worker.start()

    def on_ai_response(self, text):
        """Triggered whenever new tokens are streamed from the AI backend.

        CRITICAL: we append to BOTH buffers:
          * _raw_buffer      — feed to the tool interceptor (UI-visible stream)
          * _current_response — the PRISTINE full raw response INCLUDING tool
                                 tags, used by on_ai_finished for history
                                 storage and by ide.process_agent_response()
                                 for tool detection / execution.

        The previous implementation only fed _raw_buffer, so _current_response
        stayed empty and the post-stream agent engine silently did nothing —
        which is exactly why long responses vanished and follow-up messages
        returned empty.
        """
        if not text:
            return
        # Pristine accumulator — never filtered, never flushed early.
        self._current_response += text
        # Live interception buffer — consumed by _process_buffer below.
        self._raw_buffer += text
        self._process_buffer()

    def _process_buffer(self):
        """Universal Interception Pipeline.

        Scans the live token stream for ANY tag matching ``<tool_...`` and:
          * extracts the COMPLETE tool block (open tag + payload + close tag,
            or self-closing tag) into ``_intercepted_tools``;
          * NEVER lets the raw tag, its attributes, or its payload reach
            _route_visible_text / _flush_to_chat / _stream_to_editor;
          * preserves any natural text before/after the tool block and routes
            it to the visible UI pipeline.

        This method performs NO tool execution and NO network continuation.
        Execution + continuation happen in on_ai_finished AFTER the worker
        thread has terminated — see _execute_intercepted_tools_batch.
        """
        # Defensive lazy init (in case __init__ was bypassed by a subclass).
        if not hasattr(self, "_in_hidden_tool"):
            self._in_hidden_tool = False
            self._current_tool_tag = ""
            self._tool_buffer = ""
        if not hasattr(self, "_visible_buffer"):
            self._visible_buffer = ""
        if not hasattr(self, "_intercepted_tools"):
            self._intercepted_tools = []

        # Safety margin: longest possible partial opener is "<tool_" (6 chars).
        OPENER = "<tool_"
        OPENER_MARGIN = len(OPENER)

        while self._raw_buffer:
            buf = self._raw_buffer

            if not self._in_hidden_tool:
                # ── OUTSIDE a tool block: look for the start of any tool tag ──
                tag_start = buf.find(OPENER)

                if tag_start == -1:
                    # No tool tag in sight. Flush everything except a small tail
                    # that could be the prefix of a future "<tool_" opener.
                    safe_len = max(0, len(buf) - OPENER_MARGIN)
                    if safe_len > 0:
                        self._visible_buffer += buf[:safe_len]
                        self._raw_buffer = buf[safe_len:]
                        self._route_visible_text()
                    # If safe_len == 0 (very short buffer), wait for more tokens.
                    break

                # Flush any natural text that preceded the tag.
                if tag_start > 0:
                    self._visible_buffer += buf[:tag_start]
                    self._route_visible_text()

                # Is the opening tag fully formed (does it end with '>')?
                tag_end = buf.find(">", tag_start)
                if tag_end == -1:
                    # Partial opener — keep it buffered, wait for more tokens.
                    self._raw_buffer = buf[tag_start:]
                    break

                full_open_tag = buf[tag_start : tag_end + 1]

                # Case A: self-closing tag  e.g. <tool_list_dir/>
                if full_open_tag.endswith("/>"):
                    self._intercepted_tools.append(full_open_tag)
                    self._raw_buffer = buf[tag_end + 1 :]
                    continue

                # Case B: opening tag of a block  e.g. <tool_write_file path="...">
                tag_match = re.match(r"<([a-zA-Z0-9_]+)", full_open_tag)
                if tag_match:
                    self._in_hidden_tool = True
                    self._current_tool_tag = tag_match.group(1)
                    # Seed the tool buffer with the full opening tag so the
                    # later execution engine receives a complete XML payload.
                    self._tool_buffer = full_open_tag
                    self._raw_buffer = buf[tag_end + 1 :]
                    continue

                # Fallback: not a valid identifier — emit the '<' literally.
                self._visible_buffer += buf[tag_start : tag_start + 1]
                self._raw_buffer = buf[tag_start + 1 :]
                self._route_visible_text()
                continue

            else:
                # ── INSIDE a hidden tool block: hunt for the closing tag ──
                closing_tag = f"</{self._current_tool_tag}>"
                close_idx = buf.find(closing_tag)

                if close_idx == -1:
                    # Closing tag not yet seen. Buffer everything except a tail
                    # that could be the prefix of the closing tag.
                    safe_len = max(0, len(buf) - (len(closing_tag) - 1))
                    if safe_len > 0:
                        self._tool_buffer += buf[:safe_len]
                        self._raw_buffer = buf[safe_len:]
                    break

                # Closing tag found — finalize the complete tool payload.
                self._tool_buffer += buf[: close_idx + len(closing_tag)]
                self._intercepted_tools.append(self._tool_buffer)

                # Reset the interception state machine BEFORE advancing, so a
                # follow-up token arriving in the same chunk starts clean.
                self._in_hidden_tool = False
                self._current_tool_tag = ""
                self._tool_buffer = ""

                self._raw_buffer = buf[close_idx + len(closing_tag) :]
                continue

    def _finalize_visible_buffers(self):
        """End-of-stream drain.

        Called by on_ai_finished to flush any text still sitting in the
        visible / raw buffers WITHOUT the partial-tag safety margin, so the
        final characters of the response are never silently dropped.

        This is the fix for 'long responses vanish mid-stream': the old
        on_ai_finished flushed _raw_buffer straight to _flush_to_chat /
        _stream_to_editor, bypassing the interceptor and leaking partial
        tool tags to the UI; or worse, it left text trapped behind the
        safety margin and never emitted it at all.
        """
        # Drain anything still pending in the raw buffer through the
        # interceptor one last time (no safety margin → emit everything).
        if self._raw_buffer:
            tail = self._raw_buffer
            self._raw_buffer = ""
            if self._in_hidden_tool:
                # Stream ended mid-tool-block. Append to the tool buffer and
                # collect it as an intercepted tool so the engine still gets a
                # chance to execute whatever was captured.
                self._tool_buffer += tail
                self._intercepted_tools.append(self._tool_buffer)
                self._in_hidden_tool = False
                self._current_tool_tag = ""
                self._tool_buffer = ""
            else:
                self._visible_buffer += tail

        # Force-flush the visible buffer through the code-fence router. We
        # temporarily bypass the safety margin by directly emitting whatever
        # remains.
        if self._visible_buffer:
            remaining = self._visible_buffer
            self._visible_buffer = ""
            if getattr(self, "_in_code_block", False):
                # We were inside a ``` fence when the stream ended — emit the
                # remaining chunk to the editor and close out the block.
                self._stream_to_editor(remaining)
            else:
                self._flush_to_chat(remaining)

    def _route_visible_text(self):
        """Feeds code-fence blocks to the active editor and plain text to chat.

        This is the ONLY path from the interceptor to the user-visible UI.
        Tool tags never reach here — _process_buffer guarantees that.
        """
        FENCE = "```"
        FENCE_LEN = len(FENCE)

        while self._visible_buffer:
            buf = self._visible_buffer
            if not getattr(self, "_in_code_block", False):
                idx = buf.find(FENCE)
                if idx == -1:
                    # Hold back a tail that could be the start of "```".
                    safe = max(0, len(buf) - (FENCE_LEN - 1))
                    if safe > 0:
                        self._flush_to_chat(buf[:safe])
                        self._visible_buffer = buf[safe:]
                    break
                else:
                    if idx > 0:
                        self._flush_to_chat(buf[:idx])
                    rest = buf[idx + FENCE_LEN :]
                    nl = rest.find("\n")
                    if nl == -1:
                        # Incomplete fence header — wait for more tokens.
                        self._visible_buffer = buf[idx:]
                        break
                    self._in_code_block = True
                    self._code_block_count = getattr(self, "_code_block_count", 0) + 1
                    if hasattr(self, "_init_editor_stream"):
                        self._init_editor_stream()
                    self._visible_buffer = rest[nl + 1 :]
            else:
                idx = buf.find(FENCE)
                if idx == -1:
                    safe = max(0, len(buf) - (FENCE_LEN - 1))
                    if safe > 0:
                        self._stream_to_editor(buf[:safe])
                        self._visible_buffer = buf[safe:]
                    break
                else:
                    self._stream_to_editor(buf[:idx])
                    self._in_code_block = False
                    rest = buf[idx + FENCE_LEN :]
                    nl = rest.find("\n")
                    self._visible_buffer = rest[nl + 1 :] if nl != -1 else rest

    def _execute_intercepted_tools_batch(self):
        """Thread-safe continuation engine.

        Runs ONLY from a ``QTimer.singleShot(0, ...)`` deferred out of
        ``on_ai_finished``, which guarantees:
          * the AIWorkerThread.run() has returned (finished_signal was emitted
            in its ``finally`` block);
          * all stream state has been fully reset;
          * we are back in a clean main-thread event-loop iteration with no
            in-flight network callback on the stack.

        Routing policy (one tool per continuation turn — matches the
        existing ``process_agent_response`` single-branch contract):
          * ``write_file`` / ``run_command`` / ``list_dir`` → IDE engine
            (``ide.process_agent_response``), which executes the tool and
            schedules its own ``QTimer.singleShot(100, send_message(telemetry))``
            continuation internally.
          * ``read_file`` / ``current_dir`` → local ``_execute_tool_calls``
            runner; we trigger the continuation ourselves.
          * unknown tool → fall back to the IDE engine as a catch-all.

        CRITICAL: ``_streaming_active`` is cleared BEFORE the continuation
        is triggered, so the deferred ``send_message(telemetry)`` sees a
        clean state and is allowed to spawn the next worker. This is the
        core fix for the re-entrancy deadlock.
        """
        if not self._intercepted_tools:
            # Nothing to execute — terminal cleanup.
            self._complete_response_cycle()
            return False

        # Take the first intercepted tool payload (one tool per turn).
        tool_xml = self._intercepted_tools.pop(0)

        # Extract clean tool name for routing + user-visible notice.
        tool_name_match = re.search(r"<tool_(\w+)", tool_xml)
        tool_name = tool_name_match.group(1) if tool_name_match else ""
        tool_display = tool_name.replace("_", " ").upper() if tool_name else "TOOL CALL"

        try:
            cursor = self.conversation_text.textCursor()
            cursor.movePosition(QTextCursor.End)
            fmt = QTextCharFormat()
            fmt.setForeground(QColor(140, 140, 160))
            fmt.setFontItalic(True)
            cursor.insertText(
                f"\n[INTERCEPTED TOOL]: {tool_display} captured — executing...\n",
                fmt,
            )
            self.conversation_text.setTextCursor(cursor)
            self.conversation_text.ensureCursorVisible()
        except Exception:
            pass

        # CRITICAL: clear the streaming flag BEFORE triggering continuation
        # so the deferred send_message(telemetry) is allowed to proceed.
        self._streaming_active = False

        # Route 1 — IDE-handled tools (write_file, run_command, list_dir).
        IDE_HANDLED = {"write_file", "run_command", "list_dir"}
        if tool_name in IDE_HANDLED and hasattr(self, "ide") and self.ide \
                and hasattr(self.ide, "process_agent_response"):
            try:
                self.ide.process_agent_response(tool_xml)
            except Exception:
                pass
            return True

        # Route 2 — locally-handled tools (read_file, current_dir).
        if hasattr(self, "_execute_tool_calls"):
            try:
                result = self._execute_tool_calls(tool_xml)
            except Exception:
                result = ""
            if result:
                telemetry = f"[SYSTEM TELEMETRY]: {result}"
                # Defer the continuation to the next event-loop iteration so
                # this slot returns cleanly before the new worker spawns.
                QTimer.singleShot(0, lambda: self.send_message(custom_prompt=telemetry))
                return True

        # Route 3 — unknown tool, try the IDE engine as a catch-all.
        if hasattr(self, "ide") and self.ide and hasattr(self.ide, "process_agent_response"):
            try:
                self.ide.process_agent_response(tool_xml)
            except Exception:
                pass
            return True

        # No handler matched — if more tools remain, process the next one;
        # otherwise fall through to terminal cleanup.
        if self._intercepted_tools:
            QTimer.singleShot(0, self._execute_intercepted_tools_batch)
        else:
            self._complete_response_cycle()
        return False

    def _complete_response_cycle(self):
        """Terminal cleanup shared by on_ai_finished (no-tools path) and
        _execute_intercepted_tools_batch (no-handler / no-more-tools path).

        Renders the conversation, flips the UI back to idle, clears the
        streaming guard, and drains any user message that was queued while
        streaming was active.
        """
        self._streaming_active = False
        self._render_conversation()

        self.status_label.setStyleSheet("""
            QLabel {
                color: #88ddaa;
                font-style: italic;
                font-family: 'Segoe UI';
                font-size: 9px;
                padding: 4px 0px;
            }
        """)
        block_count = getattr(self, "_code_block_count", 0)
        if block_count > 0:
            self.status_label.setText(
                f"✓ Code streamed to editor ({block_count} block(s))"
            )
        else:
            self.status_label.setText("✓ Response complete")

        self.status_indicator.setText("● Ready")
        self.status_indicator.setStyleSheet("""
            QLabel {
                color: #00ff88;
                font-family: 'Segoe UI';
                font-size: 9px;
                font-weight: bold;
            }
        """)
        self.logo.set_state("idle")
        self.send_btn.setEnabled(True)

        # Drain any user message that was queued while streaming was active.
        if getattr(self, "_continuation_queued", False):
            pending = getattr(self, "_pending_continuation_prompt", None)
            self._continuation_queued = False
            self._pending_continuation_prompt = None
            if pending:
                QTimer.singleShot(0, lambda: self.send_message(custom_prompt=pending))

    def _flush_to_chat(self, text):
        """Write plain text to the chat panel during streaming"""
        if not text:
            return
        cursor = self.conversation_text.textCursor()
        cursor.movePosition(QTextCursor.End)
        # Add header on first visible chat text
        if not self._chat_header_added and text.strip():
            hdr_fmt = QTextCharFormat()
            hdr_fmt.setForeground(QColor(100, 220, 150))
            hdr_fmt.setFontWeight(600)
            cursor.insertText("\n🤖 Cody:  ", hdr_fmt)
            self._chat_header_added = True
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(180, 220, 255))
        cursor.insertText(text, fmt)
        self.conversation_text.setTextCursor(cursor)
        self.conversation_text.ensureCursorVisible()

    def _init_editor_stream(self):
        """Prepare the editor to receive streamed code"""
        if self.ide.current_editor:
            if self._code_block_count == 1:
                self.ide.current_editor.clear()
            else:
                cursor = self.ide.current_editor.textCursor()
                cursor.movePosition(QTextCursor.End)
                self.ide.current_editor.setTextCursor(cursor)
                self.ide.current_editor.insertPlainText("\n\n")
        # Show a small indicator in chat
        self._flush_to_chat("\n📝 [Writing code to editor...]\n")

    def _stream_to_editor(self, code_chunk):
        """Append a code chunk directly to the editor in real-time"""
        if not code_chunk or not self.ide.current_editor:
            return
        self._code_accumulator += code_chunk
        cursor = self.ide.current_editor.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.ide.current_editor.setTextCursor(cursor)
        self.ide.current_editor.insertPlainText(code_chunk)

    def on_ai_error(self, error):
        """Handle AI error with visual feedback"""
        self.logo.set_state("idle")
        self.status_label.setText(f"⚠ Error: {error[:50]}")
        self.status_label.setStyleSheet("""
            QLabel {
                color: #ff6b6b;
                font-style: italic;
                font-family: 'Segoe UI';
                font-size: 9px;
            }
        """)

        # Update status indicator
        self.status_indicator.setText("● Error")
        self.status_indicator.setStyleSheet("""
            QLabel {
                color: #ff5555;
                font-family: 'Segoe UI';
                font-size: 9px;
                font-weight: bold;
            }
        """)

    def on_ai_finished(self):
        """Handle AI finished — finalize buffers, store history, and run the
        thread-safe continuation engine.

        ARCHITECTURE (the core fix):
          1. Drain ALL remaining buffers through the interceptor via
             ``_finalize_visible_buffers`` — NEVER bypass it. The old code
             flushed ``_raw_buffer`` straight to ``_flush_to_chat`` /
             ``_stream_to_editor``, which leaked partial tool tags to the UI
             and dropped any text trapped behind the safety margin. That was
             the 'long responses vanish mid-stream' bug.
          2. Store the FULL ``_current_response`` (which now includes tool
             tags, because ``on_ai_response`` populates it) in history. The
             old code never populated ``_current_response``, so the assistant
             message was empty and follow-up messages returned nothing. That
             was the 'Hey? → Response Complete with no text' bug.
          3. Reset ALL stream state so deferred continuation hooks see a
             clean slate.
          4. If tools were intercepted during the stream, defer their
             execution to ``QTimer.singleShot(0, _execute_intercepted_tools_batch)``.
             By the time that fires, the QThread has fully terminated and we
             are in a clean main-thread event-loop iteration — this is what
             breaks the re-entrancy deadlock that crashed previous attempts
             at continuation.
          5. If no tools were intercepted, run terminal cleanup (render,
             mark idle, drain queued message) and invoke the IDE agent
             engine for any non-tool blocks (e.g. ``<patch_editor>``).
        """
        # 1. Finalize ALL buffers through the interceptor (never bypass it).
        self._finalize_visible_buffers()

        # 2. Store the FULL raw response (including tool tags) in history.
        #    This is the root-cause fix: _current_response is now populated
        #    by on_ai_response, so the assistant turn is always recorded.
        if self._current_response.strip():
            clean, tool_calls, thinking = self._parse_response(self._current_response)
            display_content = clean if clean else self._current_response
            msg = MessageData(
                role="assistant",
                content=display_content,
                tool_calls=tool_calls,
                thinking=thinking,
                raw_response=self._current_response,
            )
            self.messages.append(msg)
            self.conversation_history.append(
                {"role": "assistant", "content": self._current_response}
            )

        # 3. Snapshot whether tools were intercepted, then reset ALL state.
        has_intercepted_tools = bool(self._intercepted_tools)
        self._raw_buffer = ""
        self._visible_buffer = ""
        self._in_hidden_tool = False
        self._current_tool_tag = ""
        self._tool_buffer = ""
        self._in_code_block = False
        self._chat_header_added = False
        # NOTE: _streaming_active is NOT cleared here when tools are pending,
        # because the continuation chain is still active. It is cleared inside
        # _execute_intercepted_tools_batch / _complete_response_cycle.
        if not has_intercepted_tools:
            self._streaming_active = False

        self.send_btn.setEnabled(True)

        # 4. Thread-safe continuation engine — deferred to the next event-loop
        #    iteration so the QThread has fully terminated before we spawn a
        #    new network request.
        if has_intercepted_tools:
            self.status_label.setText("⚙️ Executing intercepted tools...")
            self.logo.set_state("thinking")
            QTimer.singleShot(0, self._execute_intercepted_tools_batch)
            # Do NOT render or mark idle — the continuation will produce more
            # text that gets appended in the next on_ai_finished cycle.
            return

        # 5. No tools intercepted — terminal cleanup. But first, invoke the
        #    IDE agent engine for any NON-tool blocks (e.g. <patch_editor>)
        #    that the interceptor does not catch. We pass _current_response
        #    directly: since has_intercepted_tools is False, _current_response
        #    contains no <tool_...> tags, so process_agent_response's tool
        #    branches will not match — only the <patch_editor> fallback can.
        if hasattr(self, "ide") and self.ide:
            try:
                self.ide.process_agent_response(self._current_response)
            except Exception:
                pass

        # 6. Terminal cleanup: render, mark idle, drain queued message.
        self._complete_response_cycle()

        # 7. Clear the pristine accumulator for the next turn.
        self._current_response = ""

    # ====================================================================
    # TOOL CALLING & EXECUTION ENGINE
    # ====================================================================

    def _has_tool_calls(self, text: str) -> bool:
        """Check if response contains tool call tags (both formats: self-closing and opening/closing)"""
        return "<tool_" in text

    @staticmethod
    def _escape_html(text: str) -> str:
        return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    @staticmethod
    def _parse_response(text: str):
        """Split AI response into (clean_text, tool_calls_text, thinking_text)."""
        text = text or ""
        # Extract [THINKING]...[/THINKING]
        thinking = ""
        m = re.findall(r"\[THINKING\](.*?)\[/THINKING\]", text, re.DOTALL)
        if m:
            thinking = "\n".join(m)
            text = re.sub(r"\[THINKING\].*?\[/THINKING\]", "", text, flags=re.DOTALL)
        # Extract <think>...</think>
        m = re.findall(r"<think>(.*?)</think>", text, re.DOTALL)
        if m:
            thinking += ("\n" if thinking else "") + "\n".join(m)
            text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
        # Extract tool call tags (including their content)
        tool_parts = re.findall(
            r"<tool_\w+[^>]*>.*?</tool_\w+>|<tool_\w+\s*/>", text, re.DOTALL
        )
        tool_calls = "\n".join(tool_parts) if tool_parts else ""
        text = re.sub(
            r"<tool_\w+[^>]*>.*?</tool_\w+>|<tool_\w+\s*/>", "", text, flags=re.DOTALL
        )
        clean = "\n".join(line for line in text.split("\n") if line.strip())
        return clean.strip(), tool_calls.strip(), thinking.strip()

    def _render_conversation(self):
        """Render full conversation as HTML with collapsible tool/thinking sections."""
        parts = []
        parts.append(
            '<div style="color:#e0e0e0;font-family:Segoe UI;font-size:10px;line-height:1.6;">'
        )
        for idx, msg in enumerate(self.messages):
            if msg.role == "user":
                parts.append(
                    f'<p><b style="color:#96c8ff;">👤 You:</b> '
                    f'<span style="color:#dcdcdc;">{self._escape_html(msg.content)}</span></p>'
                )
            else:
                parts.append(
                    f'<p><b style="color:#64dc96;">🤖 Cody:</b> '
                    f'<span style="color:#b4dcff;">{self._escape_html(msg.content)}</span></p>'
                )
                # Tool calls toggle
                if msg.tool_calls:
                    if msg.show_tools:
                        parts.append(
                            f'<p><a href="toggle:tools:{idx}" style="color:#ffaa00;text-decoration:none;">'
                            f"▼ Hide tool calls</a></p>"
                            f'<pre style="background:#1a1a24;color:#88ddaa;padding:8px;border-radius:4px;'
                            f'margin:0 0 8px 0;white-space:pre-wrap;font-size:9px;">'
                            f"{self._escape_html(msg.tool_calls)}</pre>"
                        )
                    else:
                        parts.append(
                            f'<p><a href="toggle:tools:{idx}" style="color:#ffaa00;text-decoration:none;">'
                            f"▶ Show tool calls</a></p>"
                        )
                # Thinking toggle
                if msg.thinking:
                    if msg.show_thinking:
                        parts.append(
                            f'<p><a href="toggle:thinking:{idx}" style="color:#88aaff;text-decoration:none;">'
                            f"▼ Hide thinking</a></p>"
                            f'<pre style="background:#1a1a24;color:#88aaff;padding:8px;border-radius:4px;'
                            f'margin:0 0 8px 0;white-space:pre-wrap;font-size:9px;">'
                            f"{self._escape_html(msg.thinking)}</pre>"
                        )
                    else:
                        parts.append(
                            f'<p><a href="toggle:thinking:{idx}" style="color:#88aaff;text-decoration:none;">'
                            f"▶ Show thinking</a></p>"
                        )
        parts.append("</div>")
        self.conversation_text.setHtml("\n".join(parts))
        # Scroll to bottom
        sb = self.conversation_text.verticalScrollBar()
        if sb:
            sb.setValue(sb.maximum())

    def _on_anchor_click(self, url):
        """Handle toggle anchor clicks."""
        try:
            parts = url.toString().split(":")
            if len(parts) == 3 and parts[0] == "toggle":
                action = parts[1]
                idx = int(parts[2])
                if 0 <= idx < len(self.messages):
                    msg = self.messages[idx]
                    if action == "tools":
                        msg.show_tools = not msg.show_tools
                    elif action == "thinking":
                        msg.show_thinking = not msg.show_thinking
                    self._render_conversation()
        except Exception:
            pass

    _KNOWN_TOOLS = {"list_dir", "read_file", "current_dir"}

    def _execute_tool_calls(self, text: str) -> str:
        """Parse and execute tool calls from AI response, return results.
        Only handles known tools (list_dir, read_file, current_dir).
        Unknown tools like run_command are left for the IDE-level engine."""
        import re

        results = []
        known_tools = self._KNOWN_TOOLS

        # Match both formats:
        # 1. Self-closing: <tool_list_dir/>
        # 2. Self-closing with args: <tool_list_dir path="/some/path"/>
        # 3. Opening/closing: <tool_list_dir>args</tool_list_dir>

        # Self-closing tags with optional attributes
        self_closing_pattern = r"<tool_(\w+)(?:\s+([^/>]*))?\s*/>"
        matches = re.findall(self_closing_pattern, text)

        for tool_name, attributes in matches:
            if tool_name in known_tools:
                result = self._execute_single_tool(tool_name, attributes or "")
                results.append(
                    f"<tool_{tool_name}_result>\n{result}\n</tool_{tool_name}_result>"
                )

        # Opening/closing tags
        opening_closing_pattern = r"<tool_(\w+)>(.*?)</tool_\1>"
        matches = re.findall(opening_closing_pattern, text, re.DOTALL)

        for tool_name, args in matches:
            if tool_name in known_tools:
                result = self._execute_single_tool(tool_name, args.strip())
                results.append(
                    f"<tool_{tool_name}_result>\n{result}\n</tool_{tool_name}_result>"
                )

        return "\n".join(results) if results else ""

    def _execute_single_tool(self, tool_name: str, args: str) -> str:
        """Execute a single known tool and return the result"""
        try:
            if tool_name == "list_dir":
                path = args.strip() or self._resolve_workspace_directory()
                if os.path.isdir(path):
                    files = os.listdir(path)
                    return f"Files in {path}:\n" + "\n".join(f"  - {f}" for f in files)
                else:
                    return f"Path not found: {path}"

            elif tool_name == "read_file":
                path = args.strip()
                if os.path.isfile(path):
                    with open(path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                    return f"Content of {path}:\n{content[:2000]}"
                else:
                    return f"File not found: {path}"

            elif tool_name == "current_dir":
                return f"Current directory: {os.getcwd()}"

            return ""

        except Exception as e:
            return f"Error executing tool {tool_name}: {str(e)}"

    def _send_tool_result_to_ai(self, tool_results: str):
        """Send tool results back to AI for continuation"""
        self.status_label.setText("⚙️ Processing tool results...")

        # Append tool results to conversation and ask for continuation
        enriched_prompt = (
            f"Tool execution results:\n{tool_results}\n\n"
            f"Based on these tool results, please provide a final response to the user's original question."
        )

        # Build continuation message
        messages = []
        if AGENT_SYSTEM_PROMPT:
            messages.append({"role": "system", "content": AGENT_SYSTEM_PROMPT})

        # Add conversation history
        for msg in self.conversation_history[-10:]:
            messages.append({"role": msg["role"], "content": msg["content"]})

        # Add tool results as assistant response
        messages.append({"role": "assistant", "content": self._current_response})
        messages.append({"role": "user", "content": enriched_prompt})

        # Reset for new response (full state reset so deferred hooks from the
        # previous cycle can never see stale state).
        self._current_response = ""
        self._raw_buffer = ""
        self._visible_buffer = ""
        self._in_hidden_tool = False
        self._current_tool_tag = ""
        self._tool_buffer = ""
        self._intercepted_tools = []
        self._in_code_block = False
        self._code_block_count = 0
        self._code_accumulator = ""
        self._chat_header_added = False
        self._continuation_queued = False
        self._pending_continuation_prompt = None
        self._streaming_active = True

        # Get continuation from AI
        self.worker = AIWorkerThread(self.ai_provider, messages, self.ollama_model)
        self.worker.response_received.connect(self.on_ai_response)
        self.worker.error_occurred.connect(self.on_ai_error)
        self.worker.finished_signal.connect(self.on_ai_finished)
        self.worker.start()

    # ===== CHAT MANAGEMENT METHODS =====
    def save_chat(self, filename=None):
        """Save current conversation to a file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"chat_{timestamp}.json"

        filepath = os.path.join(self.chats_directory, filename)

        chat_data = {
            "timestamp": datetime.now().isoformat(),
            "model": self.ollama_model,
            "conversation": self.conversation_history,
            "display_text": self.conversation_text.toPlainText(),
            "messages": [
                {
                    "role": m.role,
                    "content": m.content,
                    "tool_calls": m.tool_calls,
                    "thinking": m.thinking,
                    "show_tools": m.show_tools,
                    "show_thinking": m.show_thinking,
                }
                for m in self.messages
            ],
        }

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(chat_data, f, indent=2, ensure_ascii=False)
            self.current_chat_file = filepath
            self.status_label.setText(f"✓ Chat saved to {filename}")
            return filepath
        except Exception as e:
            self.status_label.setText(f"⚠ Failed to save chat: {str(e)}")
            return None

    def load_chat(self):
        """Load a saved chat conversation"""
        files = []
        try:
            files = sorted(
                [f for f in os.listdir(self.chats_directory) if f.endswith(".json")],
                reverse=True,
            )
        except:
            pass

        if not files:
            QMessageBox.information(
                self, "No Chats", "No saved chat conversations found."
            )
            return

        # Create a simple file selector dialog
        items = [f.replace("chat_", "").replace(".json", "") for f in files]
        filename, ok = QInputDialog.getItem(
            self, "Load Chat", "Select a chat to load:", items, 0, False
        )

        if not ok:
            return

        # Find the full filename
        selected_file = files[items.index(filename)]
        filepath = os.path.join(self.chats_directory, selected_file)

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                chat_data = json.load(f)

            # Load the conversation
            self.conversation_history = chat_data.get("conversation", [])
            raw_messages = chat_data.get("messages", [])
            self.messages = []
            for rm in raw_messages:
                self.messages.append(
                    MessageData(
                        role=rm.get("role", "assistant"),
                        content=rm.get("content", ""),
                        tool_calls=rm.get("tool_calls", ""),
                        thinking=rm.get("thinking", ""),
                        show_tools=rm.get("show_tools", False),
                        show_thinking=rm.get("show_thinking", False),
                    )
                )
            self._render_conversation()
            self.current_chat_file = filepath

            # Switch to the model that was used in this chat
            saved_model = chat_data.get("model", self.ollama_model)
            for key, value in self.available_models.items():
                if value == saved_model:
                    self.model_combo.blockSignals(True)
                    self.model_combo.setCurrentText(key)
                    self.model_combo.blockSignals(False)
                    self.ollama_model = saved_model
                    break

            self.status_label.setText(f"✓ Loaded chat from {selected_file}")
            self.conversation_text.ensureCursorVisible()
        except Exception as e:
            QMessageBox.critical(self, "Load Error", f"Failed to load chat: {str(e)}")

    def clear_and_save_chat(self):
        """Clear conversation and save it first"""
        if not self.conversation_history and not self.messages:
            self.conversation_text.clear()
            self.conversation_history = []
            self.messages = []
            self.status_label.setText("Chat cleared (nothing to save)")
            return

        # Save current chat first
        saved_file = self.save_chat()

        # Clear the conversation
        self.conversation_text.clear()
        self.conversation_history = []
        self.messages = []
        self.current_chat_file = None

        if saved_file:
            self.status_label.setText(f"✓ Chat saved and cleared")
        else:
            self.status_label.setText("Chat cleared")

    def switch_model(self, model_name):
        """Switch to a different AI model"""
        if model_name not in self.available_models:
            return

        new_model = self.available_models[model_name]
        if new_model != self.ollama_model:
            self.ollama_model = new_model
            self.model_label.setText(f"Powered by {model_name.split('(')[0].strip()}")
            self.status_label.setText(f"✓ Switched to {model_name}")

    # ===== CODE ASSISTANCE METHODS =====
    def explain_code(self):
        selected = self.ide.get_selected_text()
        if selected:
            self.send_message(f"Explain this code:\n```\n{selected}\n```")

    def generate_code(self):
        description, ok = QInputDialog.getText(
            self, "Generate Code", "Describe what to generate:"
        )
        if ok and description:
            lang = (
                self.ide.current_editor.language if self.ide.current_editor else "HTML"
            )
            self.send_message(f"Generate {lang} code for: {description}")

    def fix_errors(self):
        self.send_message("Please identify and fix any errors in this code.")

    def refactor_code(self):
        self.send_message(
            "Please refactor this code to make it cleaner and more efficient."
        )

    def toggle_auto_apply(self, state):
        """Toggle auto-apply feature"""
        self.auto_accept_edits = state == Qt.CheckState.Checked.value
        status = "enabled" if self.auto_accept_edits else "disabled"
        self.status_label.setText(f"Auto-apply {status}")

    def _extract_code_blocks(self, text):
        """Extract code blocks from AI response"""
        # Pattern to match code blocks like ```language\ncode\n```
        pattern = r"```(?:html|css|javascript|js|python|py)?\n([\s\S]*?)```"
        matches = re.findall(pattern, text, re.IGNORECASE)

        if matches:
            # Get the last code block (usually the most relevant)
            self._last_code_block = matches[-1].strip()
            self.apply_btn.setEnabled(True)

            # Auto-apply if enabled and editor is open
            if self.auto_accept_edits and self.ide.current_editor:
                self.apply_code_to_editor()
                self.status_label.setText("✅ Code auto-applied to editor")
            else:
                self.status_label.setText("💾 Code ready - click 'Apply to Editor'")
        else:
            self._last_code_block = None
            self.apply_btn.setEnabled(False)

    def apply_code_to_editor(self):
        """Apply extracted code to the current editor"""
        if not self._last_code_block:
            QMessageBox.warning(self, "No Code", "No code block found to apply.")
            return

        if not self.ide.current_editor:
            QMessageBox.warning(
                self, "No Editor", "Please open or create a file first."
            )
            return

        # Check if user wants to replace or append
        current_text = self.ide.current_editor.toPlainText().strip()

        if current_text and not self.auto_accept_edits:
            reply = QMessageBox.question(
                self,
                "Apply Code",
                "Replace current content or append?",
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.No
                | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Yes,
            )

            if reply == QMessageBox.StandardButton.Cancel:
                return
            elif reply == QMessageBox.StandardButton.Yes:
                # Replace
                self.ide.current_editor.setPlainText(self._last_code_block)
            else:
                # Append
                self.ide.current_editor.append("\n" + self._last_code_block)
        else:
            # Auto-apply or empty editor - just set the text
            self.ide.current_editor.setPlainText(self._last_code_block)

        self.status_label.setText("✅ Code applied successfully")
        self.apply_btn.setEnabled(False)

    # ====================================================================
    # STEP 2: PASTE THIS UPDATE METHOD ANYWHERE INSIDE AIPanelWidget
    # ====================================================================
    def update_live_directory_display(self, absolute_path):
        """Updates the visual path tracking text at the top of Cody"""
        if hasattr(self, "directory_bar"):
            folder_name = os.path.basename(absolute_path) or absolute_path
            self.directory_bar.setText(f"📂 Workspace: {folder_name}")


# ============================================================================
# File Explorer
# ============================================================================


class FileExplorerWidget(QWidget):
    """Professional file explorer"""

    file_opened = Signal(str)
    directory_opened = Signal(str)

    def __init__(self, ide, parent=None):
        super().__init__(parent)
        self.ide = ide
        self.project_root = None
        self._watcher = QFileSystemWatcher(self)
        self._watcher.directoryChanged.connect(self._on_fs_changed)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header_widget = QWidget()
        header_widget.setFixedHeight(36)
        header_widget.setStyleSheet(ThemeManager.resolve("background-color: #252526;"))
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(10, 0, 6, 0)
        header_layout.setSpacing(4)

        title = QLabel("EXPLORER")
        title_font = QFont("Segoe UI", 9, QFont.Bold)
        title.setFont(title_font)
        title.setStyleSheet("color: #bbbbbb; letter-spacing: 1px;")
        header_layout.addWidget(title)
        header_layout.addStretch()

        btn_refresh = QPushButton("🔄")
        btn_refresh.setToolTip("Refresh Explorer (F5)")
        btn_refresh.setMaximumSize(26, 26)
        btn_refresh.setCursor(Qt.PointingHandCursor)
        btn_refresh.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #aaaaaa;
                border: none;
                border-radius: 4px;
                font-size: 14px;
                padding: 0;
            }
            QPushButton:hover {
                background-color: #3e3e42;
                color: #ffffff;
            }
        """)
        btn_refresh.clicked.connect(self.refresh_tree)
        header_layout.addWidget(btn_refresh)

        btn_folder = QPushButton("⊕")
        btn_folder.setToolTip("Open Folder")
        btn_folder.setMaximumSize(26, 26)
        btn_folder.setCursor(Qt.PointingHandCursor)
        btn_folder.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #aaaaaa;
                border: none;
                border-radius: 4px;
                font-size: 16px;
                padding: 0;
            }
            QPushButton:hover {
                background-color: #3e3e42;
                color: #ffffff;
            }
        """)
        btn_folder.clicked.connect(self.open_folder)
        header_layout.addWidget(btn_folder)

        layout.addWidget(header_widget)

        # Thin separator
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFixedHeight(1)
        sep.setStyleSheet("background-color: #1a1a1a; border: none;")
        layout.addWidget(sep)

        # Tree view
        self.tree = QTreeWidget()
        self.tree.setColumnCount(1)
        self.tree.setHeaderHidden(True)
        self.tree.setIndentation(14)
        self.tree.setAnimated(True)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.open_context_menu)
        self.tree.setStyleSheet(ThemeManager.resolve("""
            QTreeWidget {
                background-color: #252526;
                color: #cccccc;
                border: none;
                outline: none;
                font-family: "Segoe UI";
                font-size: 12px;
            }
            QTreeWidget::item {
                height: 22px;
                padding-left: 2px;
            }
            QTreeWidget::item:hover {
                background-color: #2a2d2e;
            }
            QTreeWidget::item:selected {
                background-color: #37373d;
                color: #ffffff;
            }
            QTreeWidget::branch {
                background-color: #252526;
            }
            QTreeWidget::branch:open:has-children {
                color: #cccccc;
            }
        """))
        self.tree.itemDoubleClicked.connect(self.on_item_double_clicked)
        layout.addWidget(self.tree)

        self.setStyleSheet(ThemeManager.resolve("background-color: #252526;"))

    def _on_fs_changed(self, path):
        """Handle filesystem change with debounce."""
        QTimer.singleShot(100, self.refresh_tree)

    def _register_watcher(self):
        """Add project_root and all subdirectories to the watcher."""
        self._clear_watcher()
        if not self.project_root or not os.path.isdir(self.project_root):
            return
        dirs = [self.project_root]
        for dirpath, _, _ in os.walk(self.project_root):
            dirs.append(dirpath)
        # Add all directories (Qt ignores duplicates)
        self._watcher.addPaths(dirs)

    def _clear_watcher(self):
        """Remove all watched paths."""
        if self._watcher:
            for p in list(self._watcher.directories()):
                self._watcher.removePath(p)
            for p in list(self._watcher.files()):
                self._watcher.removePath(p)

    def open_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Open Project Folder")
        if folder:
            self.load_directory(folder)

            # ====================================================================
            # STEP 3: UPDATE CODY LIVE DIRECTORY ON TOP BAR
            # ====================================================================
            if (
                hasattr(self, "ide")
                and self.ide
                and hasattr(self.ide, "ai_panel")
                and self.ide.ai_panel
            ):
                self.ide.ai_panel.update_live_directory_display(folder)

    def load_directory(self, path, notify=True):
        self.project_root = os.path.abspath(path)
        self.tree.clear()

        root_item = QTreeWidgetItem()
        root_item.setText(0, os.path.basename(self.project_root))
        root_item.setData(0, Qt.UserRole, self.project_root)
        self.tree.addTopLevelItem(root_item)

        self._populate_tree(root_item, self.project_root)
        root_item.setExpanded(True)
        self._register_watcher()
        if notify:
            self.directory_opened.emit(self.project_root)

    def _populate_tree(self, parent_item, path):
        try:
            items = sorted(os.listdir(path))

            for item in items:
                if item.startswith("."):
                    continue

                item_path = os.path.join(path, item)

                if os.path.isdir(item_path):
                    node = QTreeWidgetItem(parent_item)
                    node.setText(0, f"📁 {item}")
                    node.setData(0, Qt.UserRole, item_path)
                    self._populate_tree(node, item_path)
                elif os.path.isfile(item_path):
                    node = QTreeWidgetItem(parent_item)
                    icon = self._get_file_icon(item)
                    node.setText(0, f"{icon} {item}")
                    node.setData(0, Qt.UserRole, item_path)
        except PermissionError:
            pass

    def _get_file_icon(self, filename):
        ext = os.path.splitext(filename)[1].lower()
        icons = {
            ".html": "🌐",
            ".htm": "🌐",
            ".css": "🎨",
            ".js": "📜",
            ".jsx": "📜",
            ".ts": "📜",
            ".tsx": "📜",
            ".py": "🐍",
            ".json": "📋",
            ".xml": "📄",
            ".md": "📝",
            ".txt": "📃",
        }
        return icons.get(ext, "📄")

    def refresh_tree(self):
        """Refresh the file explorer tree, preserving expanded folders."""
        if not self.project_root:
            return
        # Save expanded state
        expanded = set()

        def _save_expanded(item):
            for i in range(item.childCount()):
                child = item.child(i)
                path = child.data(0, Qt.UserRole)
                if path and child.isExpanded():
                    expanded.add(path)
                _save_expanded(child)

        for i in range(self.tree.topLevelItemCount()):
            top = self.tree.topLevelItem(i)
            _save_expanded(top)

        # Rebuild tree
        self.load_directory(self.project_root, notify=False)

        # Restore expanded state
        def _restore_expanded(item):
            for i in range(item.childCount()):
                child = item.child(i)
                path = child.data(0, Qt.UserRole)
                if path in expanded:
                    child.setExpanded(True)
                _restore_expanded(child)

        for i in range(self.tree.topLevelItemCount()):
            top = self.tree.topLevelItem(i)
            _restore_expanded(top)

    def on_item_double_clicked(self, item):
        path = item.data(0, Qt.UserRole)
        if path and os.path.isfile(path):
            self.file_opened.emit(path)

    def open_context_menu(self, position):
        """Open context menu for file/folder operations"""
        item = self.tree.itemAt(position)
        if not item:
            return

        path = item.data(0, Qt.UserRole)
        if not path:
            return

        menu = QMenu()

        # Add actions based on whether it's a file or directory
        if os.path.isdir(path):
            new_file_action = QAction("New File", self)
            new_file_action.triggered.connect(lambda: self.create_new_file(path))
            menu.addAction(new_file_action)

            new_folder_action = QAction("New Folder", self)
            new_folder_action.triggered.connect(lambda: self.create_new_folder(path))
            menu.addAction(new_folder_action)

            menu.addSeparator()

            delete_action = QAction("Delete Folder", self)
            delete_action.triggered.connect(lambda: self.delete_item(item, path))
            menu.addAction(delete_action)
        else:
            open_action = QAction("Open", self)
            open_action.triggered.connect(lambda: self.file_opened.emit(path))
            menu.addAction(open_action)

            menu.addSeparator()

            delete_action = QAction("Delete File", self)
            delete_action.triggered.connect(lambda: self.delete_item(item, path))
            menu.addAction(delete_action)

        menu.exec(self.tree.viewport().mapToGlobal(position))

    def create_new_file(self, parent_path):
        """Create a new file in the specified directory"""
        filename, ok = QInputDialog.getText(self, "New File", "Enter file name:")
        if ok and filename:
            file_path = os.path.join(parent_path, filename)
            try:
                # Create empty file
                with open(file_path, "w") as f:
                    pass

                # Refresh the tree view
                self.refresh_tree()

                # Emit signal to open the new file
                self.file_opened.emit(file_path)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not create file: {str(e)}")

    def create_new_folder(self, parent_path):
        """Create a new folder in the specified directory"""
        folder_name, ok = QInputDialog.getText(self, "New Folder", "Enter folder name:")
        if ok and folder_name:
            folder_path = os.path.join(parent_path, folder_name)
            try:
                os.makedirs(folder_path, exist_ok=True)
                self.refresh_tree()
            except Exception as e:
                QMessageBox.critical(
                    self, "Error", f"Could not create folder: {str(e)}"
                )

    def delete_item(self, item, path):
        """Delete a file or folder"""
        # Determine item type for the confirmation message
        item_type = "Folder" if os.path.isdir(path) else "File"

        reply = QMessageBox.question(
            self,
            f"Delete {item_type}",
            f"Are you sure you want to delete '{os.path.basename(path)}'?\n\nThis action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            try:
                if os.path.isdir(path):
                    # Delete directory and all its contents
                    import shutil

                    shutil.rmtree(path)
                else:
                    # Delete file
                    os.remove(path)

                # Remove item from tree and refresh
                parent = item.parent()
                if parent:
                    parent.removeChild(item)
                else:
                    # If it's a top-level item, refresh the whole tree
                    self.refresh_tree()

            except Exception as e:
                QMessageBox.critical(
                    self, "Error", f"Could not delete {item_type.lower()}: {str(e)}"
                )


# ============================================================================
# Integrated Terminal Widget — xterm.js + ConPTY (pywinpty)
# ============================================================================

try:
    from winpty import PtyProcess as _WinPtyProcess

    HAS_WINPTY = True
except ImportError:
    HAS_WINPTY = False

try:
    from PySide6.QtWebEngineWidgets import QWebEngineView
    from PySide6.QtWebEngineCore import QWebEngineSettings
    from PySide6.QtWebChannel import QWebChannel

    HAS_WEBENGINE = True
except ImportError:
    HAS_WEBENGINE = False

# ── xterm.js single-page app (CDN-loaded, rendered by Qt WebEngine) ───────────
_XTERM_HTML = r"""<!DOCTYPE html>
<html><head>
  <meta charset="UTF-8">
  <link rel="stylesheet"
        href="https://cdn.jsdelivr.net/npm/xterm@5.3.0/css/xterm.css"/>
  <style>
    *{margin:0;padding:0;box-sizing:border-box}
    html,body{width:100%;height:100%;background:#1a1a1a;overflow:hidden}
    #t{width:100%;height:100%}
    .xterm{height:100%!important}
    .xterm-viewport{overflow-y:hidden!important}
  </style>
</head><body>
<div id="t"></div>
<script src="https://cdn.jsdelivr.net/npm/xterm@5.3.0/lib/xterm.js"></script>
<script src="https://cdn.jsdelivr.net/npm/@xterm/addon-fit@0.10.0/lib/addon-fit.js"></script>
<script src="qrc:///qtwebchannel/qwebchannel.js"></script>
<script>
(function () {
  if (typeof Terminal === 'undefined') {
    document.getElementById('t').innerHTML =
      '<div style="color:#f44747;font-family:Consolas;padding:16px">' +
      '<b>xterm.js failed to load from CDN.</b><br>' +
      'Check your internet connection and restart the IDE.</div>';
    return;
  }

  var term = new Terminal({
    cursorBlink : true,
    fontFamily  : '"Cascadia Code","Consolas","Courier New",monospace',
    fontSize    : 13,
    lineHeight  : 1.2,
    scrollback  : 10000,
    convertEol  : false,
    allowProposedApi: true,
    theme: {
      background:'#1a1a1a', foreground:'#d4d4d4',
      cursor:'#d4d4d4',     selectionBackground:'#264f78',
      black:'#1e1e1e',   red:'#f44747',    green:'#6a9955',  yellow:'#dcdcaa',
      blue:'#569cd6',    magenta:'#c586c0', cyan:'#4ec9b0',  white:'#d4d4d4',
      brightBlack:'#808080', brightRed:'#f44747',  brightGreen:'#b5cea8',
      brightYellow:'#dcdcaa',brightBlue:'#9cdcfe', brightMagenta:'#c586c0',
      brightCyan:'#4ec9b0',  brightWhite:'#ffffff'
    }
  });

  var fit = new FitAddon.FitAddon();
  term.loadAddon(fit);
  term.open(document.getElementById('t'));

  function doFit() { try { fit.fit(); } catch (e) {} }
  doFit();
  window.addEventListener('resize', doFit);

  new QWebChannel(qt.webChannelTransport, function (ch) {
    var bridge = ch.objects.bridge;

    // Forward all keystrokes / paste / special sequences to Python/PTY
    term.onData(function (d) { bridge.receiveInput(d); });

    // Notify Python when the terminal panel is resized
    term.onResize(function (s) { bridge.onResize(s.cols, s.rows); });

    // Receive raw PTY output (ANSI intact) and render it
    bridge.writeToTerminal.connect(function (d) { term.write(d); });
    bridge.clearScreen.connect(function () { term.reset(); doFit(); });

    // Send current dimensions then signal ready
    bridge.onResize(term.cols, term.rows);
    bridge.terminalReady();
    term.focus();
  });
})();
</script>
</body></html>"""


class TerminalBridge(QObject):
    """Qt/JS bridge for the xterm.js terminal panel.

    Signals  (Python → JS via QWebChannel):
        writeToTerminal(str)  — raw PTY bytes decoded as UTF-8; ANSI intact
        clearScreen()         — reset the xterm.js viewport

    Slots  (JS → Python via QWebChannel):
        receiveInput(str)     — keystrokes / paste from xterm.js
        onResize(cols, rows)  — terminal panel was resized
        terminalReady()       — xterm.js has finished initialising
    """

    writeToTerminal = Signal(str)
    clearScreen = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._proc = None  # winpty.PtyProcess or None
        self._cwd: str = os.path.expanduser("~")
        self._js_ready = False
        self._defer_start = False  # start requested before JS ready

    # ── Slots (called from JavaScript) ───────────────────────────────────────

    @Slot(str)
    def receiveInput(self, data: str):
        """Forward xterm.js key events straight to the PTY."""
        if self._proc:
            try:
                self._proc.write(data)
            except Exception:
                pass

    @Slot(int, int)
    def onResize(self, cols: int, rows: int):
        """Resize the underlying PTY to match the terminal viewport."""
        if self._proc:
            try:
                self._proc.setwinsize(rows, cols)
            except Exception:
                pass

    @Slot()
    def terminalReady(self):
        """Called by JS once xterm.js has initialised successfully."""
        self._js_ready = True
        if self._defer_start:
            self._defer_start = False
            self._launch()

    # ── Public helpers ────────────────────────────────────────────────────────

    def start(self, cwd: str = ""):
        """Request a shell session.  Deferred if xterm.js is not ready yet."""
        if cwd and os.path.isdir(cwd):
            self._cwd = cwd
        if self._proc:
            return  # already running
        if self._js_ready:
            self._launch()
        else:
            self._defer_start = True

    def restart(self):
        """Kill the current session and start a fresh PowerShell."""
        self._kill()
        self.clearScreen.emit()
        if self._js_ready:
            self._launch()
        else:
            self._defer_start = True

    def send_ctrl_c(self):
        """Send Ctrl+C (ETX) to the running process."""
        if self._proc:
            try:
                self._proc.write("\x03")
            except Exception:
                pass

    def kill(self):
        self._kill()

    # ── Internal ─────────────────────────────────────────────────────────────

    def _kill(self):
        old, self._proc = self._proc, None
        if old:
            try:
                old.terminate(force=True)
            except Exception:
                pass

    def _launch(self):
        if not HAS_WINPTY:
            self.writeToTerminal.emit(
                "\r\n\x1b[1;31mError:\x1b[0m pywinpty is not installed.\r\n"
                "Open an external terminal and run:\r\n\r\n"
                "    \x1b[33mpip install pywinpty\x1b[0m\r\n\r\n"
                "Then restart the IDE.\r\n"
            )
            return
        threading.Thread(target=self._worker, daemon=True).start()

    def _worker(self):
        """Background thread — owns the PowerShell lifetime."""
        try:
            proc = _WinPtyProcess.spawn(
                "powershell.exe",
                cwd=self._cwd,
                dimensions=(24, 80),
            )
            self._proc = proc
            while True:
                try:
                    data = proc.read(4096)
                    if not data:
                        if not proc.isalive():
                            break
                        continue
                    if isinstance(data, bytes):
                        data = data.decode("utf-8", errors="replace")
                    # ANSI escape codes are passed through unchanged —
                    # xterm.js is a full terminal emulator and renders them.
                    self.writeToTerminal.emit(data)
                except (EOFError, Exception):
                    break
        except Exception as exc:
            self.writeToTerminal.emit(
                f"\r\n\x1b[1;31m[Could not start PowerShell: {exc}]\x1b[0m\r\n"
            )
        finally:
            self._proc = None
            self.writeToTerminal.emit(
                "\r\n\x1b[33m[Session ended — press \x1b[1m+\x1b[22m to restart]"
                "\x1b[0m\r\n"
            )


class TerminalWidget(QWidget):
    """Embedded interactive terminal.

    Renders via xterm.js (inside a QWebEngineView) for full VT100/ANSI
    emulation — arrow-key menus, colours, cursor movement, ollama, etc.
    powershell.exe runs inside a Windows ConPTY (pywinpty) so isatty()==True.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._bridge = TerminalBridge(self)
        self._started = False
        self._setup_ui()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Title bar ────────────────────────────────────────────────────
        bar = QWidget()
        bar.setFixedHeight(30)
        bar.setStyleSheet(
            ThemeManager.resolve("background:#252526; border-top:1px solid #111;")
        )
        bl = QHBoxLayout(bar)
        bl.setContentsMargins(10, 0, 8, 0)
        bl.setSpacing(6)

        icon = QLabel("⬡")
        icon.setStyleSheet("color:#569cd6; font-size:13px;")
        lbl = QLabel("PowerShell")
        lbl.setStyleSheet(
            "color:#ccc; font-family:'Segoe UI'; font-size:12px; font-weight:bold;"
        )
        bl.addWidget(icon)
        bl.addWidget(lbl)
        bl.addStretch()

        for text, tip, cb in [
            ("Ctrl+C", "Send interrupt (Ctrl+C)", self._bridge.send_ctrl_c),
            ("+", "New session", self._bridge.restart),
            ("\u2715", "Close  (Ctrl+Shift+`)", self.hide),
        ]:
            btn = QPushButton(text)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setToolTip(tip)
            if text in ("+", "\u2715"):
                btn.setFixedSize(22, 22)
                hbg = "#e81123" if text == "\u2715" else "#3e3e42"
                btn.setStyleSheet(
                    "QPushButton{background:transparent;color:#888;border:none;"
                    "font-size:13px;border-radius:3px;}"
                    f"QPushButton:hover{{background:{hbg};color:#fff;}}"
                )
            else:
                btn.setFixedHeight(20)
                btn.setStyleSheet(
                    "QPushButton{background:transparent;color:#888;"
                    "border:1px solid #444;border-radius:3px;"
                    "font-family:'Segoe UI';font-size:10px;padding:0 6px;}"
                    "QPushButton:hover{color:#f48771;border-color:#f48771;}"
                )
            btn.clicked.connect(cb)
            bl.addWidget(btn)

        root.addWidget(bar)

        # ── xterm.js WebView (or fallback notice) ────────────────────────
        if HAS_WEBENGINE:
            self._view = QWebEngineView(self)
            # Allow the qrc:// page to fetch CDN resources
            self._view.page().settings().setAttribute(
                QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls,
                True,
            )
            channel = QWebChannel(self._view.page())
            channel.registerObject("bridge", self._bridge)
            self._view.page().setWebChannel(channel)
            self._view.setHtml(_XTERM_HTML, QUrl("qrc:///"))
            self._view.setFocusPolicy(Qt.StrongFocus)
            root.addWidget(self._view)
        else:
            notice = QLabel(
                "PySide6 WebEngine is required for the embedded terminal.\n\n"
                "Run:  pip install PySide6\n\nThen restart the IDE.",
                self,
            )
            notice.setStyleSheet(
                "color:#f44747;background:#1a1a1a;padding:16px;"
                "font-family:Consolas;font-size:11px;"
            )
            notice.setAlignment(Qt.AlignTop)
            root.addWidget(notice)

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def set_working_directory(self, path: str):
        """Set the initial working directory (must be called before first show)."""
        if path and os.path.isdir(path):
            self._bridge._cwd = path

    def showEvent(self, event):
        super().showEvent(event)
        if not self._started:
            self._started = True
            self._bridge.start()
        if HAS_WEBENGINE:
            QTimer.singleShot(50, self._view.setFocus)

    def closeEvent(self, event):
        self._bridge.kill()
        super().closeEvent(event)


# ============================================================================
# Main IDE Window
# ============================================================================


class WebDevIDEPySide6(QMainWindow):
    """Main IDE window"""

    def detect_hardware_and_recommend_models(self):
        """
        Scans machine resources, lists installed Ollama models, recommends 4 distinct tiers,
        and prompts the user to download their choice.
        """
        import os
        import subprocess
        import threading

        # 1. Gather System Hardware Information
        try:
            import psutil
            total_ram_gb = psutil.virtual_memory().total / (1024**3)
        except ImportError:
            total_ram_gb = 8.0
            if os.name == "posix":
                try:
                    mem_str = os.popen("free -g").readlines()[1].split()[1]
                    total_ram_gb = float(mem_str)
                except:
                    pass

        has_gpu = False
        gpu_name = "CPU Only"
        try:
            res = subprocess.run(
                ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
                capture_output=True,
                text=True,
                check=True,
                )
            if res.stdout.strip():
                has_gpu = True
                gpu_name = res.stdout.strip().split("\n")[0]
        except:
            pass

        # 2. Map out the 4 Specific Tier Recommendations
        tiers = {
            "1": {"name": "1) Ultra smooth (Low reasoning & weak)", "model": "qwen2.5-coder:1.5b"},
            "2": {"name": "2) Medium Balanced (Recommended)", "model": "deepseek-coder:6.7b" if has_gpu else "qwen2.5-coder:7b"},
            "3": {"name": "3) Bit Laggy (Highest Reasoning & best for coding)", "model": "qwen2.5-coder:14b" if total_ram_gb > 16 else "deepseek-coder:33b"},
            "4": {"name": "4) Best cloud model (Ultra low local usage)", "model": "gpt-oss:20b-cloud"}
        }

        # 3. Check Current Installed Ollama Models
        installed_models = []
        try:
            import ollama
            models_list = ollama.list()
            installed_models = [m["model"] for m in models_list.get("models", [])]
        except Exception:
            try:
                res = subprocess.run(["ollama", "list"], capture_output=True, text=True)
                lines = res.stdout.strip().split("\n")[1:]
                installed_models = [line.split()[0] for line in lines if line]
            except:
                pass

        installed_str = ", ".join(installed_models) if installed_models else "None detected"

        # Build Status Message
        hw_report = (
            f"📊 **Hardware Report**:\n"
            f"• System RAM: {total_ram_gb:.1f} GB\n"
            f"• Graphics Accelerator: {gpu_name}\n\n"
            f"📦 **Ollama Environment**:\n"
            f"• Local Models Found: {installed_str}\n\n"
            f"💡 **Multi-Tier Model Choices Available**:\n"
            f"• {tiers['1']['name']} ➔ **`{tiers['1']['model']}`**\n"
            f"• {tiers['2']['name']} ➔ **`{tiers['2']['model']}`**\n"
            f"• {tiers['3']['name']} ➔ **`{tiers['3']['model']}`**\n"
            f"• {tiers['4']['name']} ➔ **`{tiers['4']['model']}`**\n"
        )

        # 4. Prompt User to select one of the Tiers to configure/pull
        options = ["1", "2", "3", "4"]
        choice, ok = QInputDialog.getItem(
            self, 
            "Hardware Audit & Multi-Tier Optimization",
            f"{hw_report}\nSelect which model tier option you would like to automatically pull/setup:",
            [tiers[k]["name"] for k in options],
            1, # Default index to choice 2
            False
        )

        if ok and choice:
            # Find which tier was chosen
            selected_tier = None
            for k, v in tiers.items():
                if v["name"] == choice:
                    selected_tier = v
                    break
            
            if not selected_tier:
                return

            recommended_model = selected_tier["model"]

            if recommended_model == "gpt-oss:20b-cloud":
                QMessageBox.information(
                    self, "Cloud Setup", 
                    f"✨ Cloud Tier selected: `{recommended_model}` requires ultra low usage on your machine hardware!\nNo local download is required."
                )
                return

            if recommended_model in installed_models or any(recommended_model in m for m in installed_models):
                QMessageBox.information(
                    self, "Ready", 
                    f"🎉 `{recommended_model}` is already installed and ready to go!"
                )
            else:
                self.statusbar.showMessage(f"📥 Pulling model {recommended_model}... Please check background console logs.")
                
                def download_worker():
                    try:
                        self.bottom_panel.append(f"\n[Ollama] Initiating download for {recommended_model}...\n")
                        process = subprocess.Popen(
                            ["ollama", "pull", recommended_model],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT,
                            text=True,
                        )
                        for line in iter(process.stdout.readline, ""):
                            if line.strip():
                                QTimer.singleShot(0, lambda l=line: self.bottom_panel.append(f"[Ollama Pull] {l.strip()}"))
                        process.wait()
                        QTimer.singleShot(0, lambda: QMessageBox.information(self, "Success", f"✨ `{recommended_model}` successfully downloaded!"))
                    except Exception as e:
                        QTimer.singleShot(0, lambda err=e: QMessageBox.critical(self, "Download Error", f"Failed to download model: {err}"))

                threading.Thread(target=download_worker, daemon=True).start()


    def _resolve_workspace_directory(self, requested_path=None):
        """Return the active workspace directory for tool execution and agent actions."""
        if requested_path:
            candidate = requested_path.strip()
            if candidate:
                return candidate
        for candidate in (
            getattr(self, "project_root", None),
            getattr(getattr(self, "file_explorer", None), "project_root", None),
        ):
            if candidate and os.path.isdir(candidate):
                return candidate
        current_file = getattr(self, "current_file_path", None)
        if current_file:
            current_dir = os.path.dirname(current_file)
            if os.path.isdir(current_dir):
                return current_dir
        return os.getcwd()

    def process_agent_response(self, full_ai_text):
        """
        Scans for autonomous agent block signatures.
        Executes file management, runs backend sub-processes, or lists directory contexts seamlessly.
        """
        active_dir = self._resolve_workspace_directory()

        # 1. Handle Automatic Directory Scanning Tool (Checks for self-closing, opening, or wrapped variations)
        if any(
            tag in full_ai_text
            for tag in ["<tool_list_dir/>", "<tool_list_dir>", "<tool_list_dir ]"]
        ):
            self.append_agent_log(
                "\n📂 **[Agent Tool]**: Reading workspace file registry..."
            )
            try:
                visible_files = [
                    f for f in os.listdir(active_dir) if not f.startswith(".")
                ]
                telemetry = f"[SYSTEM TELEMETRY - DIRECTORY LIST]:\n{visible_files}"
                self.append_agent_log("✅ Scanned project folder.")
            except Exception as e:
                telemetry = (
                    f"[SYSTEM TELEMETRY - ERROR]: Failed to read folder: {str(e)}"
                )

            QTimer.singleShot(
                100,
                lambda: (
                    self.ai_panel.send_message(custom_prompt=telemetry)
                    if hasattr(self.ai_panel, "send_message")
                    else None
                ),
            )
            return

        # 2. Handle Autonomous File Creation Tool
        if "<tool_write_file" in full_ai_text and "</tool_write_file>" in full_ai_text:
            try:
                path_match = re.search(
                    r'<tool_write_file\s+path=["\']([^"\']+)["\']\s*>', full_ai_text
                )
                content_match = re.search(
                    r"<tool_write_file[^>]*>([\s\S]*?)</tool_write_file>", full_ai_text
                )

                if path_match and content_match:
                    target_rel_path = path_match.group(1).strip()
                    new_code_content = content_match.group(1)

                    # Remove syntax highlight fences if present inside the tool block
                    new_code_content = re.sub(
                        r"^```\w*\s*|\s*```$", "", new_code_content.strip()
                    )

                    target_abs_path = os.path.join(active_dir, target_rel_path)
                    os.makedirs(os.path.dirname(target_abs_path), exist_ok=True)

                    with open(target_abs_path, "w", encoding="utf-8") as f:
                        f.write(new_code_content)

                    self.append_agent_log(
                        f"\n💾 **[Agent Tool]**: Writing code payload to: `{target_rel_path}`"
                    )
                    telemetry = f"[SYSTEM TELEMETRY - WRITE SUCCESS]: File written cleanly to {target_rel_path}."

                    if hasattr(self, "file_explorer"):
                        self.file_explorer.load_directory(active_dir)
                else:
                    telemetry = "[SYSTEM TELEMETRY - WRITE ERROR]: Invalid tag format."
            except Exception as e:
                telemetry = f"[SYSTEM TELEMETRY - WRITE ERROR]: {str(e)}"

            QTimer.singleShot(
                100,
                lambda: (
                    self.ai_panel.send_message(custom_prompt=telemetry)
                    if hasattr(self.ai_panel, "send_message")
                    else None
                ),
            )
            return

        # 3. Handle Autonomous Shell Command Terminal Tool
        if (
            "<tool_run_command>" in full_ai_text
            and "</tool_run_command>" in full_ai_text
        ):
            cmd_match = re.search(
                r"<tool_run_command>([\s\S]*?)</tool_run_command>", full_ai_text
            )
            if cmd_match:
                command = cmd_match.group(1).strip()
                self.append_agent_log(
                    f"\n⚙️ **[Agent Tool]**: Running subprocess command: `{command}`"
                )

                def run_proc():
                    try:
                        res = subprocess.run(
                            command,
                            shell=True,
                            capture_output=True,
                            text=True,
                            cwd=active_dir,
                            timeout=30,
                        )
                        output = (
                            f"STDOUT:\n{res.stdout}\nSTDERR:\n{res.stderr}"
                            if (res.stdout or res.stderr)
                            else "Command ran with exit code 0."
                        )
                    except Exception as proc_err:
                        output = f"EXECUTION ERROR: {str(proc_err)}"

                    QTimer.singleShot(
                        0,
                        lambda: (
                            self.ai_panel.send_message(
                                custom_prompt=f"[SYSTEM TELEMETRY - TERMINAL OUTPUT]:\n{output}"
                            )
                            if hasattr(self.ai_panel, "send_message")
                            else None
                        ),
                    )

                threading.Thread(target=run_proc, daemon=True).start()
                return

        # Default fallback: Handle classic patch updates if no structural tools are invoked
        if "<patch_editor>" in full_ai_text and "</patch_editor>" in full_ai_text:
            pattern = r"<patch_editor>([\s\S]*?)</patch_editor>"
            match = re.search(pattern, full_ai_text)
            if match:
                current_tab = self.tab_widget.currentWidget()
                if current_tab and hasattr(current_tab, "setPlainText"):
                    current_tab.setPlainText(match.group(1).strip())
                    self.append_agent_log(
                        "\n🤖 **[Agent Action]**: Active editor workspace updated."
                    )

    def __init__(self):
        super().__init__()
        self.setWindowTitle("WebDev IDE - Professional Edition")
        self.setGeometry(100, 100, 1400, 900)

        self.current_file_path = None
        self.current_editor = None
        self.editors = {}
        self.open_files = []
        self.project_root = os.getcwd()

        self.setup_ui()
        self.setup_styles()
        self.setup_connections()

        # Create initial file
        self.new_file()

    def setup_ui(self):
        """Set up the main UI"""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # --- ADD THIS SYSTEM TOOLBAR CONFIGURATION HERE ---
        self.toolbar = QToolBar("Main Toolbar", self)
        self.toolbar.setMovable(False)
        self.toolbar.setStyleSheet(ThemeManager.resolve("""
            QToolBar {
                background-color: #1d2330;
                border-bottom: 1px solid #394353;
                spacing: 8px;
                padding: 4px;
            }
            QToolButton {
                background-color: #262d3a;
                color: #c7d0dd;
                border: 1px solid #394353;
                border-radius: 4px;
                padding: 4px 10px;
                font-family: 'Segoe UI';
                font-size: 11px;
            }
            QToolButton:hover {
                background-color: #313a49;
                color: #e7edf5;
            }
        """))
        self.addToolBar(self.toolbar)

        # Add actions to the toolbar instance explicitly
        hardware_action = self.toolbar.addAction("🔍 Optimize AI Hardware")
        hardware_action.setToolTip(
            "Scan local machine hardware capabilities and configure optimized Ollama models"
        )
        hardware_action.triggered.connect(self.detect_hardware_and_recommend_models)
        # --------------------------------------------------

        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Splitter for left and main area
        main_splitter = QSplitter(Qt.Horizontal)
        self.main_splitter = main_splitter
        # Splitter for left and main area
        main_splitter = QSplitter(Qt.Horizontal)
        self.main_splitter = main_splitter

        # File explorer
        self.file_explorer = FileExplorerWidget(self)
        self.file_explorer.file_opened.connect(self.open_file)
        self.file_explorer.directory_opened.connect(self._on_project_directory_changed)
        self.file_explorer.setMaximumWidth(250)
        self.file_explorer.setMinimumWidth(150)
        main_splitter.addWidget(self.file_explorer)

        # Editor area splitter
        editor_splitter = QSplitter(Qt.Vertical)

        # Tab widget for editors
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        self.tab_widget.setDocumentMode(True)
        self.tab_widget.setStyleSheet(ThemeManager.resolve("""
            QTabWidget::pane {
                border: 1px solid #394353;
                border-top: none;
                background-color: #1e1e1e;
            }
            QTabWidget::tab-bar {
                alignment: left;
            }
            QTabBar {
                background-color: #2d2d2d;
                padding: 5px 6px 3px 6px;
            }
            QTabBar::tab {
                background-color: #2d2d2d;
                color: #9d9d9d;
                padding: 7px 13px;
                border: 1px solid transparent;
                border-radius: 7px 7px 0 0;
                margin: 0 2px;
                font-family: "Segoe UI";
                font-size: 11px;
                min-width: 80px;
            }
            QTabBar::tab:hover {
                background-color: #3e3e42;
                color: #ffffff;
            }
            QTabBar::tab:selected {
                background-color: #1e1e1e;
                color: #ffffff;
                border: 1px solid #394353;
                border-bottom: 1px solid #1e1e1e;
            }
            QTabBar::close-button {
                subcontrol-position: right;
                padding: 2px;
                border-radius: 3px;
            }
            QTabBar::close-button:hover {
                background-color: #e81123;
            }
        """))
        editor_splitter.addWidget(self.tab_widget)

        # Bottom panel
        self.bottom_panel = QTextEdit()
        self.bottom_panel.setMaximumHeight(150)
        self.bottom_panel.setReadOnly(True)
        font_mono = QFont("Consolas", 10)
        font_mono.setFixedPitch(True)
        self.bottom_panel.setFont(font_mono)
        self.bottom_panel.setStyleSheet(ThemeManager.resolve("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #9cdcfe;
                border: 1px solid #394353;
                border-radius: 9px 9px 0 0;
                padding: 7px 10px;
                font-family: Consolas;
                font-size: 10px;
            }
        """))
        editor_splitter.addWidget(self.bottom_panel)

        # Integrated terminal (hidden by default, toggled with Ctrl+Shift+`)
        self.terminal_widget = TerminalWidget(self)
        self.terminal_widget.setMinimumHeight(100)
        self.terminal_widget.hide()
        editor_splitter.addWidget(self.terminal_widget)

        editor_splitter.setStretchFactor(0, 4)
        editor_splitter.setStretchFactor(1, 1)
        editor_splitter.setStretchFactor(2, 2)
        self.editor_splitter = editor_splitter

        main_splitter.addWidget(editor_splitter)

        # AI Panel
        self.ai_panel = AIPanelWidget(self)
        self.ai_panel.setMaximumWidth(640)
        self.ai_panel.setMinimumWidth(280)
        main_splitter.addWidget(self.ai_panel)

        self._ai_width_animation = QVariantAnimation(self)
        self._ai_width_animation.setDuration(260)
        self._ai_width_animation.setEasingCurve(QEasingCurve.OutCubic)
        self._ai_width_animation.valueChanged.connect(self._set_ai_panel_width)
        self._ai_width_animation.finished.connect(self.ai_panel.refresh_terminal_size)
        self.ai_panel.expansion_requested.connect(self.set_ai_panel_expanded)

        main_splitter.setStretchFactor(0, 1)
        main_splitter.setStretchFactor(1, 3)
        main_splitter.setStretchFactor(2, 1)
        main_splitter.setCollapsible(0, True)
        main_splitter.setCollapsible(2, True)

        main_layout.addWidget(main_splitter)

        # Status bar
        self.statusbar = self.statusBar()
        self.statusbar.setSizeGripEnabled(False)

        self.position_label = QLabel("  Ln 1, Col 1  ")
        self.position_label.setStyleSheet(
            "color: #ffffff; font-family: 'Segoe UI'; font-size: 11px; padding: 0 6px;"
        )
        self.language_label = QLabel("  HTML  ")
        self.language_label.setStyleSheet(
            "color: #ffffff; font-family: 'Segoe UI'; font-size: 11px;"
            " padding: 0 10px; background-color: rgba(0,0,0,0.15); border-radius: 2px;"
        )
        self.status_label = QLabel("  Ready")
        self.status_label.setStyleSheet(
            "color: #ffffff; font-family: 'Segoe UI'; font-size: 11px; padding: 0 6px;"
        )

        self.ai_status_widget = None  # Will be set when editor is created

        self.statusbar.addWidget(self.status_label)
        self.statusbar.addPermanentWidget(self.language_label)
        self.statusbar.addPermanentWidget(self.position_label)

        # Menu and toolbar
        self.create_menu()
        self.create_toolbar()

    def create_menu(self):
        """Create menu bar"""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("File")
        file_menu.addAction("New File", self.new_file, QKeySequence.New)
        file_menu.addAction("Open File", self.open_file_dialog, QKeySequence.Open)
        file_menu.addAction(
            "Open Folder", self.open_folder, QKeySequence(Qt.CTRL | Qt.SHIFT | Qt.Key_O)
        )
        file_menu.addSeparator()
        file_menu.addAction("Save", self.save_file, QKeySequence.Save)
        file_menu.addAction(
            "Save As", self.save_file_as, QKeySequence(Qt.CTRL | Qt.SHIFT | Qt.Key_S)
        )
        file_menu.addSeparator()
        file_menu.addAction("Exit", self.close, QKeySequence.Quit)

        # Edit menu
        edit_menu = menubar.addMenu("Edit")
        edit_menu.addAction("Undo", self.undo, QKeySequence.Undo)
        edit_menu.addAction("Redo", self.redo, QKeySequence.Redo)
        edit_menu.addSeparator()
        edit_menu.addAction("Find", self.find, QKeySequence.Find)
        edit_menu.addAction("Replace", self.replace, QKeySequence.Replace)

        # View menu
        view_menu = menubar.addMenu("View")
        view_menu.addAction("Toggle AI Panel", self.toggle_ai_panel)
        view_menu.addAction(
            "Toggle In-Editor AI",
            self.toggle_ai_assistant,
            QKeySequence(Qt.CTRL | Qt.SHIFT | Qt.Key_A),
        )
        view_menu.addAction(
            "Toggle Terminal",
            self.toggle_terminal,
            QKeySequence(Qt.CTRL | Qt.SHIFT | Qt.Key_QuoteLeft),
        )
        view_menu.addSeparator()

        # Theme submenu
        theme_menu = view_menu.addMenu("🎨 Editor Theme")
        theme_group = QActionGroup(self)
        theme_group.setExclusive(True)

        for theme_name in CodeHighlighter.THEMES.keys():
            action = theme_menu.addAction(theme_name)
            action.setCheckable(True)
            action.setActionGroup(theme_group)
            if theme_name == "VS Code Dark+":
                action.setChecked(True)
            action.triggered.connect(lambda checked, t=theme_name: self.change_theme(t))

        view_menu.addSeparator()
        view_menu.addAction("Zoom In", self.zoom_in, QKeySequence.ZoomIn)
        view_menu.addAction("Zoom Out", self.zoom_out, QKeySequence.ZoomOut)

        # Run menu
        run_menu = menubar.addMenu("Run")
        run_menu.addAction(
            "Run in Browser", self.run_in_browser, QKeySequence(Qt.CTRL | Qt.Key_F5)
        )

        # Help menu
        help_menu = menubar.addMenu("Help")
        help_menu.addAction("About", self.show_about)

    def create_toolbar(self):
        """Create toolbar"""
        toolbar = self.addToolBar("Main Toolbar")
        self.toolbar = toolbar
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(16, 16))
        toolbar.setStyleSheet(ThemeManager.resolve("""
            QToolBar {
                background-color: #2d2d2d;
                border: none;
                border-bottom: 1px solid #394353;
                spacing: 4px;
                padding: 6px 10px;
            }
            QToolBar::separator {
                background-color: #3c3c3c;
                width: 1px;
                margin: 5px 8px;
            }
            QToolButton {
                background-color: transparent;
                border: 1px solid transparent;
                border-radius: 7px;
                padding: 6px 9px;
                color: #cccccc;
                font-family: "Segoe UI";
                font-size: 11px;
            }
            QToolButton:hover {
                background-color: #3e3e42;
                color: #ffffff;
                border-color: #394353;
            }
            QToolButton:pressed {
                background-color: #007acc;
                color: #ffffff;
            }
        """))

        toolbar.addAction("New", self.new_file)
        toolbar.addAction("Open", self.open_file_dialog)
        toolbar.addAction("Save", self.save_file)
        toolbar.addSeparator()
        toolbar.addAction("Undo", self.undo)
        toolbar.addAction("Redo", self.redo)
        toolbar.addSeparator()
        toolbar.addAction("Find", self.find)
        toolbar.addSeparator()

        # New Hardware Detection Addition
        hardware_action = toolbar.addAction(
            "🔍 Optimize AI Hardware", self.detect_hardware_and_recommend_models
        )
        hardware_action.setToolTip(
            "Scan local machine hardware capabilities and configure optimized Ollama models"
        )
        toolbar.addSeparator()
        # Theme selector dropdown
        theme_label = QLabel("  Theme: ")
        theme_label.setStyleSheet(
            "color: #aaaaaa; padding: 0 4px; font-family: 'Segoe UI'; font-size: 11px;"
        )
        toolbar.addWidget(theme_label)

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(CodeHighlighter.THEMES.keys())
        self.theme_combo.setCurrentText("VS Code Dark+")
        self.theme_combo.currentTextChanged.connect(self.change_theme)
        self.theme_combo.setCursor(Qt.PointingHandCursor)
        self.theme_combo.setStyleSheet(ThemeManager.resolve("""
            QComboBox {
                background-color: #3c3c3c;
                color: #cccccc;
                border: 1px solid #505050;
                border-radius: 4px;
                padding: 4px 10px;
                min-width: 140px;
                font-family: "Segoe UI";
                font-size: 11px;
            }
            QComboBox:hover {
                background-color: #4a4a4d;
                border-color: #007acc;
            }
            QComboBox::drop-down {
                border: none;
                width: 22px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid #aaaaaa;
                width: 0;
                height: 0;
            }
            QComboBox QAbstractItemView {
                background-color: #252526;
                color: #cccccc;
                selection-background-color: #094771;
                selection-color: #ffffff;
                border: 1px solid #454545;
                border-radius: 4px;
                padding: 3px 0;
                outline: none;
            }
            QComboBox QAbstractItemView::item {
                padding: 5px 12px;
                min-height: 22px;
            }
        """))
        toolbar.addWidget(self.theme_combo)

        toolbar.addSeparator()
        toolbar.addAction("AI Panel", self.toggle_ai_panel)
        toolbar.addAction("In-Editor AI", self.toggle_ai_assistant)

        toolbar.addSeparator()

        # Scrap Code button as a styled widget
        scrap_btn = QPushButton("Scrap Code")
        scrap_btn.setToolTip("Delete all code and start fresh")
        scrap_btn.setCursor(Qt.PointingHandCursor)
        scrap_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(200, 50, 50, 0.15);
                color: #f48771;
                border: 1px solid rgba(200, 80, 80, 0.35);
                border-radius: 4px;
                padding: 5px 10px;
                font-family: "Segoe UI";
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(200, 50, 50, 0.3);
                border-color: #f48771;
                color: #ff9999;
            }
            QPushButton:pressed {
                background-color: rgba(200, 50, 50, 0.5);
            }
        """)
        scrap_btn.clicked.connect(self.scrap_code)
        toolbar.addWidget(scrap_btn)

        toolbar.addSeparator()
        # Placeholder — AI assistant buttons are added here dynamically via update_ai_status()

    def setup_styles(self):
        """Set up application styles"""
        self.setStyleSheet(ThemeManager.resolve("""
            QMainWindow {
                background-color: #1e1e1e;
                color: #cccccc;
            }

            /* ── Menu Bar ── */
            QMenuBar {
                background-color: #323233;
                color: #cccccc;
                border: none;
                border-bottom: 1px solid #454545;
                padding: 4px 8px;
                font-family: "Segoe UI";
                font-size: 12px;
            }
            QMenuBar::item {
                padding: 5px 11px;
                border-radius: 6px;
                margin: 1px 2px;
            }
            QMenuBar::item:selected {
                background-color: #4a4a4d;
                color: #ffffff;
            }
            QMenuBar::item:pressed {
                background-color: #007acc;
                color: #ffffff;
            }

            /* ── Drop-down Menu ── */
            QMenu {
                background-color: #252526;
                color: #cccccc;
                border: 1px solid #454545;
                border-radius: 9px;
                padding: 6px 0;
                font-family: "Segoe UI";
                font-size: 12px;
            }
            QMenu::item {
                padding: 6px 28px 6px 14px;
                border-radius: 5px;
                margin: 1px 4px;
            }
            QMenu::item:selected {
                background-color: #094771;
                color: #ffffff;
            }
            QMenu::separator {
                height: 1px;
                background-color: #3c3c3c;
                margin: 4px 8px;
            }
            QMenu::indicator {
                width: 14px;
                height: 14px;
                margin-left: 4px;
            }

            /* ── Status Bar ── */
            QStatusBar {
                background-color: #2d2d2d;
                color: #cccccc;
                border-top: 1px solid #454545;
                font-family: "Segoe UI";
                font-size: 11px;
            }
            QStatusBar::item {
                border: none;
            }

            /* ── Splitter ── */
            QSplitter::handle {
                background-color: #252526;
            }
            QSplitter::handle:horizontal {
                width: 5px;
            }
            QSplitter::handle:vertical {
                height: 5px;
            }
            QSplitter::handle:hover {
                background-color: #4aa3ff;
            }

            /* ── Scrollbars ── */
            QScrollBar:vertical {
                background-color: transparent;
                width: 10px;
                border: none;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background-color: #3c3c3c;
                border-radius: 5px;
                min-height: 24px;
                margin: 2px 2px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #5b6779;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: transparent;
            }
            QScrollBar:horizontal {
                background-color: transparent;
                height: 10px;
                border: none;
                margin: 0;
            }
            QScrollBar::handle:horizontal {
                background-color: #3c3c3c;
                border-radius: 5px;
                min-width: 24px;
                margin: 2px 2px;
            }
            QScrollBar::handle:horizontal:hover {
                background-color: #5b6779;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0;
            }
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                background: transparent;
            }

            /* ── Tooltips ── */
            QToolTip {
                background-color: #2d2d2d;
                color: #cccccc;
                border: 1px solid #555555;
                padding: 5px 8px;
                border-radius: 7px;
                font-family: "Segoe UI";
                font-size: 11px;
            }

            /* ── Input Dialogs / Message Boxes ── */
            QDialog {
                background-color: #252526;
                color: #cccccc;
                font-family: "Segoe UI";
            }
            QInputDialog QLabel, QMessageBox QLabel {
                color: #cccccc;
                font-family: "Segoe UI";
                font-size: 12px;
            }
            QInputDialog QLineEdit, QMessageBox QLineEdit {
                background-color: #3c3c3c;
                color: #d4d4d4;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 5px 8px;
                selection-background-color: #094771;
            }
            QMessageBox QPushButton, QInputDialog QPushButton {
                background-color: #0e639c;
                color: #ffffff;
                border: none;
                border-radius: 4px;
                padding: 7px 18px;
                font-weight: bold;
                font-size: 11px;
                min-width: 70px;
            }
            QMessageBox QPushButton:hover, QInputDialog QPushButton:hover {
                background-color: #1177bb;
            }
            QMessageBox QPushButton:pressed, QInputDialog QPushButton:pressed {
                background-color: #0a4d7d;
            }
        """))

    def setup_connections(self):
        """Set up signal/slot connections"""
        # Application-level shortcut so it fires even when editor has focus
        sc = QShortcut(QKeySequence(Qt.CTRL | Qt.SHIFT | Qt.Key_QuoteLeft), self)
        sc.setContext(Qt.ApplicationShortcut)
        sc.activated.connect(self.toggle_terminal)

    def set_ai_panel_expanded(self, expanded):
        """Smoothly resize the shared Cody/Claude workspace without hiding it."""
        if not self.ai_panel.isVisible():
            self.ai_panel.show()

        sizes = self.main_splitter.sizes()
        if len(sizes) < 3:
            return

        current_width = max(self.ai_panel.width(), sizes[2])
        max_ai_width = max(280, sum(sizes) - sizes[0] - 360)
        target_width = min(640, max_ai_width) if expanded else min(360, max_ai_width)

        self.ai_panel.set_expanded(expanded)
        if current_width == target_width:
            self.ai_panel.refresh_terminal_size()
            return

        self._ai_width_animation.stop()
        self._ai_width_animation.setStartValue(current_width)
        self._ai_width_animation.setEndValue(target_width)
        self._ai_width_animation.start()

    def _set_ai_panel_width(self, width):
        """Reserve the animated width while keeping the editor usable."""
        sizes = self.main_splitter.sizes()
        if len(sizes) < 3:
            return

        total_width = sum(sizes)
        left_width = sizes[0]
        ai_width = int(width)
        editor_width = max(360, total_width - left_width - ai_width)
        self.main_splitter.setSizes([left_width, editor_width, ai_width])

    def _on_project_directory_changed(self, directory):
        """Stage a newly opened project folder for the next Claude launch only."""
        self.project_root = directory
        self.ai_panel.claude_panel.set_working_directory(directory)

    def new_file(self):
        """Create new file"""
        editor = CodeEditor(language="html")
        tab_count = self.tab_widget.count()
        tab_name = f"Untitled-{tab_count + 1}"

        self.tab_widget.addTab(editor, tab_name)
        self.tab_widget.setCurrentWidget(editor)

        self.editors[editor] = {"path": None, "modified": False, "language": "html"}

        # Add in-editor AI assistant
        ai_assistant = InEditorAIAssistant(editor)
        self.editors[editor]["ai_assistant"] = ai_assistant

        self.current_editor = editor
        editor.setFocus()

        # Update AI status in status bar
        self.update_ai_status(ai_assistant)

    def open_file_dialog(self):
        """Open file dialog"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open File", filter="Web Files (*.html *.css *.js);;All Files (*.*)"
        )
        if file_path:
            self.open_file(file_path)

    def open_folder(self):
        """Open folder"""
        folder = QFileDialog.getExistingDirectory(self, "Open Project Folder")
        if folder:
            self.file_explorer.load_directory(folder)

    def open_file(self, file_path):
        """Open file"""
        # Check if already open
        for editor, info in self.editors.items():
            if info["path"] == file_path:
                self.tab_widget.setCurrentWidget(editor)
                return

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not open file: {e}")
            return

        # Detect language
        ext = os.path.splitext(file_path)[1].lower()
        language = {
            ".html": "html",
            ".htm": "html",
            ".css": "css",
            ".js": "javascript",
            ".jsx": "javascript",
            ".ts": "javascript",
        }.get(ext, "html")

        editor = CodeEditor(language=language)
        editor.setPlainText(content)

        tab_name = os.path.basename(file_path)
        self.tab_widget.addTab(editor, tab_name)
        self.tab_widget.setCurrentWidget(editor)

        # Add in-editor AI assistant
        ai_assistant = InEditorAIAssistant(editor)

        self.editors[editor] = {
            "path": file_path,
            "modified": False,
            "language": language,
            "ai_assistant": ai_assistant,
        }

        self.current_editor = editor
        self.current_file_path = file_path
        self.language_label.setText(language.upper())
        self.status_label.setText(f"Opened: {file_path}")

        # Update AI status in status bar
        self.update_ai_status(ai_assistant)

        # Connect text changed signal
        editor.textChanged.connect(lambda: self.on_editor_changed(editor))

    def save_file(self):
        """Save file"""
        if not self.current_editor:
            return

        info = self.editors.get(self.current_editor)
        if info and info["path"]:
            self._save_to_path(self.current_editor, info["path"])
        else:
            self.save_file_as()

    def save_file_as(self):
        """Save file as"""
        if not self.current_editor:
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save File",
            filter="HTML Files (*.html);;CSS Files (*.css);;JS Files (*.js);;All Files (*.*)",
        )
        if file_path:
            self._save_to_path(self.current_editor, file_path)

            info = self.editors[self.current_editor]
            info["path"] = file_path
            info["language"] = self._detect_language(file_path)

            tab_index = self.tab_widget.indexOf(self.current_editor)
            self.tab_widget.setTabText(tab_index, os.path.basename(file_path))

    def _save_to_path(self, editor, file_path):
        """Save editor content to path"""
        try:
            content = editor.toPlainText()
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

            info = self.editors[editor]
            info["modified"] = False

            tab_index = self.tab_widget.indexOf(editor)
            tab_text = self.tab_widget.tabText(tab_index)
            if tab_text.startswith("●"):
                self.tab_widget.setTabText(tab_index, tab_text[1:])

            self.status_label.setText(f"Saved: {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not save file: {e}")

    def close_tab(self, index):
        """Close tab"""
        widget = self.tab_widget.widget(index)
        if widget in self.editors:
            info = self.editors[widget]
            if info["modified"]:
                reply = QMessageBox.question(
                    self,
                    "Unsaved Changes",
                    "Do you want to save changes?",
                    QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                )
                if reply == QMessageBox.Cancel:
                    return
                elif reply == QMessageBox.Yes and info["path"]:
                    self._save_to_path(widget, info["path"])

            # If this tab's AI widget is currently shown, detach it cleanly
            closing_assistant = info.get("ai_assistant")
            if (
                closing_assistant
                and self.ai_status_widget is closing_assistant.container
            ):
                for action in self.toolbar.actions():
                    if self.toolbar.widgetForAction(action) is self.ai_status_widget:
                        self.toolbar.removeAction(action)
                        break
                self.ai_status_widget = None

            self.tab_widget.removeTab(index)
            del self.editors[widget]

    def on_tab_changed(self, index):
        """Handle tab change"""
        if index >= 0:
            widget = self.tab_widget.widget(index)
            self.current_editor = widget

            info = self.editors.get(widget)
            if info:
                self.current_file_path = info["path"]
                self.language_label.setText(info["language"].upper())
                if info["path"]:
                    self.status_label.setText(f"Editing: {info['path']}")

                # Update AI status for current editor
                if "ai_assistant" in info:
                    self.update_ai_status(info["ai_assistant"])

    def on_editor_changed(self, editor):
        """Handle editor text change"""
        info = self.editors.get(editor)
        if info and not info["modified"]:
            info["modified"] = True

            tab_index = self.tab_widget.indexOf(editor)
            tab_text = self.tab_widget.tabText(tab_index)
            if not tab_text.startswith("●"):
                self.tab_widget.setTabText(tab_index, f"● {tab_text}")

    def update_ai_status(self, ai_assistant):
        """Update AI status widget in toolbar"""
        new_container = ai_assistant.container

        # Already showing this container — just ensure it's visible
        if self.ai_status_widget is new_container:
            self.ai_status_widget.show()
            return

        # Remove old AI status widget if present
        if self.ai_status_widget:
            for action in self.toolbar.actions():
                if self.toolbar.widgetForAction(action) is self.ai_status_widget:
                    self.toolbar.removeAction(action)
                    break
            self.ai_status_widget.setParent(None)

        # Add new AI button and status widget to toolbar
        self.ai_status_widget = new_container
        self.toolbar.addWidget(self.ai_status_widget)
        self.ai_status_widget.show()

    def toggle_ai_assistant(self):
        """Toggle AI assistant for current editor"""
        if self.current_editor and self.current_editor in self.editors:
            info = self.editors[self.current_editor]
            if "ai_assistant" in info:
                info["ai_assistant"].toggle_enabled()
                status = "enabled" if info["ai_assistant"].enabled else "disabled"
                self.status_label.setText(f"In-Editor AI {status}")

    def scrap_code(self):
        """Clear all code with waterfall animation"""
        # Confirm action
        reply = QMessageBox.question(
            self,
            "Scrap Code",
            "Are you sure you want to delete all code and start fresh?\nThis action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            # Create and start waterfall animation
            self.waterfall = WaterfallAnimation(self)
            self.waterfall.finished.connect(self.complete_scrap)
            self.waterfall.start()

    def complete_scrap(self):
        """Complete the scrapping process after animation"""
        # Clear all tabs
        for i in range(self.tab_widget.count()):
            editor = self.tab_widget.widget(i)
            if isinstance(editor, CodeEditor):
                editor.clear()

        # Save cleared state
        self.save_file()

        # Show confirmation
        self.statusbar.showMessage("✨ Code scrapped! Starting fresh...", 3000)

    def get_selected_text(self):
        """Get selected text from editor"""
        if self.current_editor:
            return self.current_editor.textCursor().selectedText()
        return ""

    def undo(self):
        if self.current_editor:
            self.current_editor.undo()

    def redo(self):
        if self.current_editor:
            self.current_editor.redo()

    def find(self):
        """Open find dialog"""
        text = QInputDialog.getText(self, "Find", "Search text:")[0]
        if text and self.current_editor:
            self.current_editor.find(text)

    def replace(self):
        """Open replace dialog"""
        text, ok = QInputDialog.getText(self, "Replace", "Search text:")
        if ok and text and self.current_editor:
            new_text, ok = QInputDialog.getText(self, "Replace", "Replace with:")
            if ok and self.current_editor:
                content = self.current_editor.toPlainText()
                new_content = content.replace(text, new_text)
                self.current_editor.setPlainText(new_content)

    def zoom_in(self):
        if self.current_editor:
            font = self.current_editor.font()
            font.setPointSize(font.pointSize() + 1)
            self.current_editor.setFont(font)

    def zoom_out(self):
        if self.current_editor:
            font = self.current_editor.font()
            if font.pointSize() > 8:
                font.setPointSize(font.pointSize() - 1)
                self.current_editor.setFont(font)

    def change_theme(self, theme_name):
        """Change syntax highlighting theme for all editors"""
        for editor_widget in self.editors.keys():
            if hasattr(editor_widget, "highlighter") and editor_widget.highlighter:
                editor_widget.highlighter.set_theme(theme_name)

        # Sync combo box if changed from menu
        if (
            hasattr(self, "theme_combo")
            and self.theme_combo.currentText() != theme_name
        ):
            self.theme_combo.blockSignals(True)
            self.theme_combo.setCurrentText(theme_name)
            self.theme_combo.blockSignals(False)

        # Update status
        self.status_label.setText(f"Theme: {theme_name}")
        QTimer.singleShot(3000, lambda: self.status_label.setText("Ready"))

    def run_in_browser(self):
        """Run HTML in browser"""
        if self.current_file_path and self.current_file_path.endswith(".html"):
            webbrowser.open(f"file:///{self.current_file_path}")
        elif self.current_editor:
            import tempfile

            content = self.current_editor.toPlainText()
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".html", delete=False
            ) as f:
                f.write(content)
                webbrowser.open(f"file:///{f.name}")

    def toggle_ai_panel(self):
        """Toggle AI panel visibility"""
        if self.ai_panel.isVisible():
            self.ai_panel.hide()
        else:
            self.ai_panel.show()

    def toggle_terminal(self):
        """Toggle the integrated terminal panel (Ctrl+Shift+`)"""
        if self.terminal_widget.isVisible():
            self.terminal_widget.hide()
        else:
            # Set the starting directory BEFORE show() so the session
            # spawns PowerShell in the right folder on the very first open.
            if self.current_file_path:
                cwd = os.path.dirname(self.current_file_path)
                if os.path.isdir(cwd):
                    self.terminal_widget.set_working_directory(cwd)

            self.terminal_widget.show()

            # Resize splitter on first open
            sizes = self.editor_splitter.sizes()
            if len(sizes) >= 3 and sizes[2] < 50:
                want = 240
                avail = sizes[0]
                if avail > want + 80:
                    self.editor_splitter.setSizes([avail - want, sizes[1], want])

            # Focus is handed to the xterm.js WebView inside showEvent

    def show_about(self):
        QMessageBox.information(
            self,
            "About WebDev IDE",
            "WebDev IDE Professional Edition\n\n"
            "A modern, professional IDE for web development.\n"
            "Built with PySide6 featuring:\n\n"
            "✨ Features:\n"
            "• Syntax highlighting for HTML/CSS/JavaScript\n"
            "• AI-powered code assistance (DeepSeek/Ollama)\n"
            "• Professional Material Design UI\n"
            "• Smooth animations and transitions\n"
            "• Multi-file editing with tabs\n"
            "• Real-time code analysis\n"
            "• File explorer with project support\n\n"
            "🎨 Enhanced Features:\n"
            "• Animated AI logo (Gemini-style)\n"
            "• Professional color scheme\n"
            "• Live syntax highlighting\n"
            "• Responsive layout\n",
        )

    def _detect_language(self, file_path):
        """Detect language from file extension"""
        ext = os.path.splitext(file_path)[1].lower()
        return {
            ".html": "html",
            ".htm": "html",
            ".css": "css",
            ".js": "javascript",
            ".jsx": "javascript",
            ".ts": "javascript",
        }.get(ext, "html")

    def closeEvent(self, event):
        """Handle application close - cleanup AI assistants"""
        # Cleanup all AI assistants in editors
        for editor, info in self.editors.items():
            if "ai_assistant" in info:
                info["ai_assistant"].cleanup()

        # Cleanup Claude Code panel
        if hasattr(self, "ai_panel") and hasattr(self.ai_panel, "claude_panel"):
            self.ai_panel.claude_panel.cleanup()

        # Stop AI panel logo animation
        if hasattr(self, "ai_panel") and hasattr(self.ai_panel, "logo"):
            if hasattr(self.ai_panel.logo, "timer"):
                self.ai_panel.logo.timer.stop()

        event.accept()

    def verify_and_auto_correct_agent_code(self, written_code):
        """
        The Auto-Fix Loop: Scans the code for structural bugs.
        If any errors are detected, it re-invokes the model with specific telemetry feedback.
        """
        has_error = False
        error_report = ""

        # Perform basic structural integrity validation checks
        if written_code.count("{") != written_code.count("}"):
            has_error = True
            error_report = (
                "SyntaxError: Mismatched curly braces '{ }' detected in layout."
            )
        elif written_code.count("<") != written_code.count(">"):
            has_error = True
            error_report = (
                "SyntaxError: Mismatched HTML markup angle-brackets '< >' detected."
            )

        if has_error:
            self.append_agent_log(
                f"\n🚨 **[Validation Alert]**: Found anomaly: `{error_report}`. Re-triggering Agent loop..."
            )

            # Formulate full historical context containing the system prompt and error description
            correction_payload = (
                f"The code you just applied threw an immediate runtime validation error:\n"
                f'"{error_report}"\n\n'
                f"Please inspect the script layout, correct the syntax failure, and output the clean version wrapped in <patch_editor> tags."
            )

            # Automatically send the correction payload back to Ollama / MiniMax context
            if hasattr(self, "ai_panel") and hasattr(self.ai_panel, "send_prompt"):
                self.ai_panel.send_prompt(correction_payload)

    def append_agent_log(self, text):
        """Post system updates directly inside the side panel chat interface."""
        if hasattr(self, "ai_panel") and hasattr(self.ai_panel, "chat_log"):
            self.ai_panel.chat_log.append(text)

    def get_active_workspace_context(self):
        """
        Dynamically grabs the currently open file path and context content.
        This keeps the Agent updated when you switch or change folders!
        """
        current_tab = self.tab_widget.currentWidget()
        if current_tab and hasattr(current_tab, "toPlainText"):
            # Check if editor tracking tracks an active file path
            file_path = getattr(current_tab, "file_path", "Untitled File")
            return file_path, current_tab.toPlainText()
        return "No file open", ""


# ============================================================================
# Main Entry Point
# ============================================================================


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    ThemeManager.apply_application_palette(app)

    # Create and show splash screen
    splash = SplashScreen()
    splash.show()
    app.processEvents()  # Ensure splash is displayed

    # Create main window (but don't show it yet)
    window = WebDevIDEPySide6()

    # Function to close splash and show main window
    def show_main_window():
        splash.close()
        window.show()

    # Set timer to show main window after 2.5 seconds (2500 ms)
    QTimer.singleShot(2500, show_main_window)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

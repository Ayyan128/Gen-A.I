"""
J.A.R.V.I.S.-style glowing globe widget, built with PyQt5.

Install dependency:
    pip install PyQt5

Run:
    python jarvis_globe.py
"""

import sys
import math
import random

from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtGui import QPainter, QColor, QRadialGradient, QPen, QBrush
from PyQt5.QtCore import Qt, QTimer, QPointF, QRectF


ORANGE = QColor(255, 150, 40)
ORANGE_DIM = QColor(255, 150, 40, 90)
BG = QColor(8, 4, 0)

# Starting ray counts and the step size / limits used by the on-screen controls.
INITIAL_OUTER_RAYS = 0
INITIAL_MIDDLE_RAYS = 0
RAY_STEP = 10
MIN_RAYS = 2
MAX_RAYS = 1000

# Fixed-cap spawn: every SPAWN_INTERVAL_MS, add a random number of new rays
# (between SPAWN_MIN and SPAWN_MAX) until each list reaches its target cap,
# then spawning stops.
SPAWN_INTERVAL_MS = 5000
SPAWN_MIN = 3
SPAWN_MAX = 5
TARGET_OUTER_RAYS = 10
TARGET_MIDDLE_RAYS = 5

# Flicker behavior: chance per frame that a ray blinks fully off/on, likea
# lightning, instead of smoothly fading in and out.
FLICKER_CHANCE = 0.02

# Minimum angular separation (degrees) enforced between newly spawned rays
# in the same list, so new rays don't land right next to an existing one.
MIN_RAY_GAP_DEG = 60


def _angular_gap(a, b):
    """Smallest distance between two angles on a circle, in degrees."""
    d = abs(a - b) % 360
    return min(d, 360 - d)


def _pick_spaced_angle(existing_angles, min_gap=MIN_RAY_GAP_DEG, max_tries=300):
    """Random angle that's at least min_gap degrees from every angle in
    existing_angles. Falls back to the last attempt if the list is too
    crowded to satisfy the gap (e.g. many rays packed into 360 degrees)."""
    if not existing_angles:
        return random.uniform(0, 360)
    angle = random.uniform(0, 360)
    for _ in range(max_tries):
        angle = random.uniform(0, 360)
        if all(_angular_gap(angle, a) >= min_gap for a in existing_angles):
            return angle
    return angle


class Ray:
    """A single flickering spike radiating from the core."""

    def __init__(self, existing_angles=None):
        self.reset(existing_angles)

    def reset(self, existing_angles=None):
        self.angle = _pick_spaced_angle(existing_angles)
        self.length = 0.55
        self.width = random.uniform(0.6, 2.2)
        self.life = random.uniform(150, 200)
        self.age = 0
        self.visible = True

    def step(self):
        self.age = 1
        if self.age > self.life:
            self.reset()
            return
        # Lightning-style flicker: snap fully on or off instead of fading.
        if random.random() < FLICKER_CHANCE:
            self.visible = not self.visible


class GlobeWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("J.A.R.V.I.S.")
        self.setStyleSheet("background-color: black;")
        self.resize(800, 800)

        self.rays = []
        self._resize_ray_list(self.rays, INITIAL_OUTER_RAYS)
        self.middle_rays = []
        self._resize_ray_list(self.middle_rays, INITIAL_MIDDLE_RAYS)
        self.ring_rotation = 0.0
        self.tick_rotation = 0.0
        self.pulse_phase = 0.0

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(30)

        self.spawn_timer = QTimer(self)
        self.spawn_timer.timeout.connect(self.spawn_rays)
        self.spawn_timer.start(SPAWN_INTERVAL_MS)

        self.setFocusPolicy(Qt.StrongFocus)
        self._update_title()

    def spawn_rays(self):
        # Add a handful of new outer + middle rays each interval, but never
        # go past each list's target cap. Once both caps are hit, this timer
        # keeps firing but stops adding anything.
        if len(self.rays) < TARGET_OUTER_RAYS:
            n_outer = min(random.randint(SPAWN_MIN, SPAWN_MAX),
                          TARGET_OUTER_RAYS - len(self.rays))
            self._resize_ray_list(self.rays, n_outer)
        if len(self.middle_rays) < TARGET_MIDDLE_RAYS:
            n_middle = min(random.randint(SPAWN_MIN, SPAWN_MAX),
                           TARGET_MIDDLE_RAYS - len(self.middle_rays))
            self._resize_ray_list(self.middle_rays, n_middle)
        self._update_title()

    # -- ray count controls ------------------------------------------------

    def _update_title(self):
        self.setWindowTitle(f"J.A.R.V.I.S.")

    def _resize_ray_list(self, ray_list, delta):
        new_count = max(MIN_RAYS, min(MAX_RAYS, len(ray_list) + delta))
        if delta > 0:
            for _ in range(new_count - len(ray_list)):
                # Rebuild the angle list each time so every new ray also
                # keeps its distance from the ones just added this call.
                existing_angles = [r.angle for r in ray_list]
                ray_list.append(Ray(existing_angles))
        elif delta < 0:
            del ray_list[new_count:]
        return ray_list

    def keyPressEvent(self, event):
        key = event.key()
        if key in (Qt.Key_Plus, Qt.Key_Equal):
            self._resize_ray_list(self.rays, RAY_STEP)
        elif key in (Qt.Key_Minus, Qt.Key_Underscore):
            self._resize_ray_list(self.rays, -RAY_STEP)
        elif key == Qt.Key_BracketRight:
            self._resize_ray_list(self.middle_rays, RAY_STEP)
        elif key == Qt.Key_BracketLeft:
            self._resize_ray_list(self.middle_rays, -RAY_STEP)
        else:
            super().keyPressEvent(event)
            return
        self._update_title()
        self.update()

    def tick(self):
        for r in self.rays:
            r.step()
        for r in self.middle_rays:
            r.step()
        self.ring_rotation = (self.ring_rotation + 0.15) % 360
        self.tick_rotation = (self.tick_rotation - 0.05) % 360
        self.pulse_phase += 0.05
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), BG)

        side = min(self.width(), self.height())
        cx, cy = self.width() / 2, self.height() / 2
        radius = side * 0.38

        self._draw_core_glow(painter, cx, cy, radius)
        self._draw_rays(painter, cx, cy, radius)
        self._draw_tick_ring(painter, cx, cy, radius)
        self._draw_arc_ring(painter, cx, cy, radius)
        self._draw_outer_circle(painter, cx, cy, radius)
        self._draw_middle_circle(painter, cx, cy, radius)
        self._draw_middle_ticks(painter, cx, cy, radius)
        self._draw_inner_circle(painter, cx, cy, radius)

        painter.end()

    def _draw_core_glow(self, painter, cx, cy, radius):
        # pulse = 0.45 + 0.05 * math.sin(self.pulse_phase)
        glow_r = radius * 0.35
        gradient = QRadialGradient(QPointF(cx, cy), glow_r)
        gradient.setColorAt(0.0, QColor(255, 245, 220, 255))
        gradient.setColorAt(0.15, QColor(255, 200, 100, 220))
        gradient.setColorAt(0.4, QColor(255, 140, 30, 120))
        gradient.setColorAt(1.0, QColor(255, 100, 0, 0))
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(gradient))
        painter.drawEllipse(QPointF(cx, cy), glow_r, glow_r)

    def _draw_rays(self, painter, cx, cy, radius):
        for r in self.rays:
            if not r.visible:
                continue
            length = radius * r.length
            rad = math.radians(r.angle)
            x1 = cx + math.cos(rad) * radius * 0.05
            y1 = cy + math.sin(rad) * radius * 0.05
            x2 = cx + math.cos(rad) * length
            y2 = cy + math.sin(rad) * length

            color = QColor(255, 170, 60, 255)
            pen = QPen(color, r.width)
            pen.setCapStyle(Qt.RoundCap)
            painter.setPen(pen)
            painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))

    def _draw_tick_ring(self, painter, cx, cy, radius):
        tick_radius = radius * 1.18
        pen = QPen(ORANGE_DIM, 1)
        painter.setPen(pen)
        for i in range(120):
            angle = math.radians(i * 3 + self.tick_rotation)
            inner = tick_radius
            outer = tick_radius + (6 if i % 5 == 0 else 3)
            x1 = cx + math.cos(angle) * inner
            y1 = cy + math.sin(angle) * inner
            x2 = cx + math.cos(angle) * outer
            y2 = cy + math.sin(angle) * outer
            painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))

    def _draw_arc_ring(self, painter, cx, cy, radius):
        # Broken circular arcs, like the reference image, slowly rotating.
        # Sits outside the outer circle rather than hugging it.
        pen = QPen(ORANGE, 1.4)
        painter.setPen(pen)
        arc_radius = radius * 1.10
        rect = QRectF(cx - arc_radius, cy - arc_radius, arc_radius * 2, arc_radius * 2)
        arc_specs = [(10, 70), (100, 40), (170, 25), (220, 90), (330, 20)]
        for start_deg, span_deg in arc_specs:
            start = int((start_deg + self.ring_rotation) * 16)
            span = int(span_deg * 16)
            painter.drawArc(rect, start, span)

    def _draw_inner_circle(self, painter, cx, cy, radius):
        pen = QPen(QColor(255, 150, 40, 160), 1.2)
        painter.setPen(pen)
        inner_radius = radius * 0.05
        painter.drawEllipse(QPointF(cx, cy), inner_radius, inner_radius)

    def _draw_middle_circle(self, painter, cx, cy, radius):
        pen = QPen(QColor(255, 150, 40, 160), 1.2)
        painter.setPen(pen)
        middle_radius = radius * 0.55
        painter.drawEllipse(QPointF(cx, cy), middle_radius, middle_radius)

    def _draw_middle_ticks(self, painter, cx, cy, radius):
        # Flickering spikes anchored to the middle circle, radiating outward
        # toward the tick ring but staying in the inner portion (they don't
        # reach the outer ring). Each spike is drawn along the radial
        # direction, i.e. perpendicular to the circle it starts on, and the
        # whole group rotates together with the ring so they always stay
        # perpendicular to it.
        middle_radius = radius * 0.55
        tick_radius = radius * 1.18
        band = (tick_radius - middle_radius) * 0.75

        for r in self.middle_rays:
            if not r.visible:
                continue
            spike_len = band * (r.length / 0.55)
            angle = math.radians(r.angle )
            dx, dy = math.cos(angle), math.sin(angle)

            x1 = cx + dx * middle_radius
            y1 = cy + dy * middle_radius
            x2 = cx + dx * (middle_radius + spike_len)
            y2 = cy + dy * (middle_radius + spike_len)

            color = QColor(255, 170, 60, 255)
            pen = QPen(color, r.width * 0.6)
            pen.setCapStyle(Qt.RoundCap)
            painter.setPen(pen)
            painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))

    def _draw_outer_circle(self, painter, cx, cy, radius):
        pen = QPen(QColor(255, 150, 40, 160), 1.2)
        painter.setPen(pen)
        outer_radius = radius * 1.02
        painter.drawEllipse(QPointF(cx, cy), outer_radius, outer_radius)


def main():
    app = QApplication(sys.argv)
    widget = GlobeWidget()
    widget.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""Run: python3 test_build_reels.py"""
from build_reels import pan_x, visible_box

# 1280x720 fills the canvas width at zoom 1, so there is nothing to pan.
assert pan_x(1280, 720, 1.0, 0.0) == 0.0
assert pan_x(1280, 720, 1.7, 0.5) == 0.0
# At zoom 2 the clip is 2160 px wide: focus on the left edge shifts right by the 540 px of slack, no more.
assert abs(pan_x(1280, 720, 2.0, 0.0) - 1.0) < 1e-9
assert abs(pan_x(1280, 720, 2.0, 0.4) - 0.4) < 1e-9
assert abs(pan_x(1280, 720, 2.0, 1.0) + 1.0) < 1e-9
# The same zoom shows the left half of the source at full height.
assert all(abs(a - b) < 1e-9 for a, b in zip(visible_box(1280, 720, 2.0, 0.0), (0, 0, 640, 720)))
print("ok")

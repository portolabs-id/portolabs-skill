"""Transparent PNG overlays for the minimal style, drawn with ffmpeg alone.

Each function writes its PNG into out_dir once (the name carries the parameters) and returns the path.
Pixel sizes are canvas pixels: build_draft places a PNG at its native size on the 1080x1920 canvas.
"""
import subprocess
from pathlib import Path

CANVAS = (1080, 1920)
CAPCUT_FONT = "/Applications/CapCut.app/Contents/Resources/Font/SystemFont/en.ttf"
RING_RGB = (255, 241, 222)
REC_INSET = 64
REC_CORNER = 84
REC_LINE = 5


def ring(out_dir, diameter, thickness=6, glow=26):
    """A warm white circle with a soft glow, for circling a face."""
    pad = 3 * glow
    size = diameter + 2 * pad
    centre, radius = size / 2, diameter / 2
    distance = f"abs(hypot(X-{centre},Y-{centre})-{radius})"
    alpha = f"255*max(clip(1-{distance}/{thickness / 2},0,1),0.55*exp(-pow({distance}/{glow},2)))"
    r, g, b = RING_RGB
    return _render(out_dir, f"ring-{diameter}.png", (size, size), f"geq=r={r}:g={g}:b={b}:a='{alpha}'")


def rec_frame(out_dir):
    """Camera viewfinder over the whole canvas: four corner marks and a red dot with REC."""
    w, h = CANVAS
    m, n, t = REC_INSET, REC_CORNER, REC_LINE
    bars = []
    for x, y, dx, dy in ((m, m, 1, 1), (w - m, m, -1, 1), (m, h - m, 1, -1), (w - m, h - m, -1, -1)):
        bars.append((x if dx > 0 else x - n, y if dy > 0 else y - t, n, t))
        bars.append((x if dx > 0 else x - t, y if dy > 0 else y - n, t, n))
    filters = [f"drawbox=x={x}:y={y}:w={bw}:h={bh}:c=white@0.9:t=fill:replace=1" for x, y, bw, bh in bars]
    dot_x, dot_y, dot = m + 34, m + 30, 20
    radius = dot / 2
    filters.append(f"geq=r='if(lt(hypot(X-{dot_x + radius},Y-{dot_y + radius}),{radius}),224,r(X,Y))'"
                   f":g='if(lt(hypot(X-{dot_x + radius},Y-{dot_y + radius}),{radius}),38,g(X,Y))'"
                   f":b='if(lt(hypot(X-{dot_x + radius},Y-{dot_y + radius}),{radius}),43,b(X,Y))'"
                   f":a='if(lt(hypot(X-{dot_x + radius},Y-{dot_y + radius}),{radius}),255,alpha(X,Y))'")
    filters.append(f"drawtext=fontfile='{CAPCUT_FONT}':text=REC:fontcolor=white:fontsize=30"
                   f":x={dot_x + dot + 12}:y={dot_y - 3}")
    return _render(out_dir, "rec-frame.png", CANVAS, ",".join(filters))


def vignette(out_dir, strength=0.8):
    """Black edges fading to clear in the middle: the moody frame of the minimal style."""
    w, h = CANVAS
    edge = f"hypot((X-{w / 2})/{w / 2},(Y-{h / 2})/{h / 2})"
    alpha = f"255*{strength}*pow(clip(({edge}-0.55)/0.85,0,1),1.4)"
    return _render(out_dir, f"vignette-{strength}.png", CANVAS, f"geq=r=0:g=0:b=0:a='{alpha}'")


def black(out_dir):
    return _render(out_dir, "black.png", CANVAS, "drawbox=c=black:t=fill:replace=1")


def _render(out_dir, name, size, filters):
    out = Path(out_dir) / name
    if not out.exists():
        out.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "lavfi", "-i",
                        f"color=c=black@0.0:s={size[0]}x{size[1]},format=rgba", "-vf", f"format=rgba,{filters}",
                        "-frames:v", "1", str(out)], check=True)
    return out

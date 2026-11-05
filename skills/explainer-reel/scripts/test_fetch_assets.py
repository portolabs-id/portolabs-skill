"""Self-check for the logo source order: python3 scripts/test_fetch_assets.py"""
import tempfile
from pathlib import Path

from fetch_assets import find_logo

SVG = b"<svg xmlns='http://www.w3.org/2000/svg'/>"


def no_network(url):
    return None


def test_brand_kit_wins_over_everything():
    with tempfile.TemporaryDirectory() as tmp:
        brand, out = Path(tmp, "brand"), Path(tmp, "out")
        brand.mkdir()
        out.mkdir()
        (brand / "portolabs.svg").write_bytes(SVG)
        found = find_logo({"name": "portolabs", "domain": "portolabs.id", "logo": "x"}, out, brand,
                          fetch=lambda url: SVG, site_icons=lambda d: {"svg": SVG})
        assert found["source"] == "brand"


def test_site_svg_beats_one_colour_simple_icon():
    with tempfile.TemporaryDirectory() as tmp:
        found = find_logo({"name": "x", "domain": "x.com", "logo": "x"}, Path(tmp), None,
                          fetch=lambda url: SVG, site_icons=lambda d: {"svg": SVG})
        assert found["source"] == "site-svg"


def test_sharp_site_raster_beats_simple_icon_colour_guess():
    with tempfile.TemporaryDirectory() as tmp:
        found = find_logo({"name": "x", "domain": "x.com", "logo": "x"}, Path(tmp), None,
                          fetch=lambda url: SVG, site_icons=lambda d: {"svg": None, "raster": (b"png", ".png", 180)})
        assert found["source"] == "site-raster"


def test_small_site_raster_loses_to_vector_simple_icon():
    with tempfile.TemporaryDirectory() as tmp:
        found = find_logo({"name": "x", "domain": "x.com", "logo": "x"}, Path(tmp), None,
                          fetch=lambda url: SVG, site_icons=lambda d: {"svg": None, "raster": (b"ico", ".ico", 64)})
        assert found["source"] == "simpleicons"


def test_bot_checked_site_falls_back_to_simple_icon():
    with tempfile.TemporaryDirectory() as tmp:
        found = find_logo({"name": "x", "domain": "x.com", "logo": "x"}, Path(tmp), None,
                          fetch=lambda url: SVG, site_icons=lambda d: {"svg": None, "raster": None})
        assert found["source"] == "simpleicons"


def test_unknown_everywhere_falls_back_to_monogram():
    with tempfile.TemporaryDirectory() as tmp:
        found = find_logo({"name": "nope", "logo": "nope", "domain": "nope.invalid"}, Path(tmp), None,
                          fetch=no_network)
        assert found == {"file": None, "source": "missing"}


if __name__ == "__main__":
    for name, test in list(globals().items()):
        if name.startswith("test_"):
            test()
    print("ok")

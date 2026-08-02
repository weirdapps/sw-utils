import numpy as np
from PIL import Image
from farmbot import vision


def _marker():
    m = np.zeros((20, 20), dtype=np.uint8)
    np.fill_diagonal(m, 255)          # textured, asymmetric
    m[0, :] = 255
    return m


def _gradient(h=120, w=160):
    row = np.linspace(0, 255, w, dtype=np.uint8)
    return np.tile(row, (h, 1))


def test_to_gray_from_pil():
    g = vision.to_gray(Image.new("RGB", (5, 4), (255, 255, 255)))
    assert g.shape == (4, 5) and g.dtype == np.uint8


def test_find_locates_template_center():
    screen = _gradient()
    marker = _marker()
    screen[50:70, 90:110] = marker
    m = vision.find(screen, marker, threshold=0.9)
    assert m is not None
    assert abs(m.cx - 100) <= 1 and abs(m.cy - 60) <= 1   # center of [90:110, 50:70]
    assert m.confidence >= 0.9


def test_find_returns_none_when_absent():
    screen = _gradient()          # marker never pasted
    assert vision.find(screen, _marker(), threshold=0.9) is None


def test_load_templates_reads_pngs(tmp_path):
    Image.fromarray(_marker()).save(tmp_path / "sim_button.png")
    tpls = vision.load_templates(str(tmp_path))
    assert "sim_button" in tpls
    assert tpls["sim_button"].ndim == 2

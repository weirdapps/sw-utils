import os
from PIL import Image
from farmbot import capture


def test_crop_and_save_writes_png_of_box_size(tmp_path):
    img = Image.new("RGB", (100, 80), (0, 0, 0))
    path = capture.crop_and_save(img, (10, 20, 40, 60), "sim_button", str(tmp_path))
    assert os.path.basename(path) == "sim_button.png"
    saved = Image.open(path)
    assert saved.size == (30, 40)      # (40-10) x (60-20)

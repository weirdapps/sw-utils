"""vision.py — OpenCV template matching. Device/image concerns live here (with adb)."""
import glob
import os
from collections import namedtuple

import cv2
import numpy as np
from PIL import Image

Match = namedtuple("Match", ["cx", "cy", "confidence"])


def to_gray(img):
    if isinstance(img, Image.Image):
        img = np.array(img)
    if img.ndim == 3:
        return cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    return img


def find(screen, template, threshold=0.88):
    s = to_gray(screen)
    t = to_gray(template)
    res = cv2.matchTemplate(s, t, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(res)
    if max_val < threshold:
        return None
    h, w = t.shape[:2]
    return Match(cx=int(max_loc[0] + w // 2), cy=int(max_loc[1] + h // 2), confidence=float(max_val))


def load_templates(dir_path):
    out = {}
    for path in glob.glob(os.path.join(dir_path, "*.png")):
        stem = os.path.splitext(os.path.basename(path))[0]
        out[stem] = to_gray(Image.open(path).convert("RGB"))
    return out

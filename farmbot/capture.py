"""capture.py — bootstrap reference templates from the live emulator (supervised, one-time)."""
import os

from farmbot.adb import ADB


def crop_and_save(image, box, name, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"{name}.png")
    image.crop(box).save(path)
    return path


def main(cfg, args):
    root = os.path.dirname(os.path.abspath(__file__))
    out_dir = os.path.join(root, "templates")
    adb = ADB(cfg["device_serial"])
    if not adb.device_ready():
        print(f"device not ready: {cfg['device_serial']}")
        return 2
    img = adb.screencap()
    print(f"screen size: {img.size}. Enter template name and box to crop.")
    name = input("template name (e.g. sim_button): ").strip()
    coords = input("box as left,top,right,bottom: ").strip()
    left, top, right, bottom = (int(v) for v in coords.split(","))
    path = crop_and_save(img, (left, top, right, bottom), name, out_dir)
    print(f"saved {path}")
    return 0

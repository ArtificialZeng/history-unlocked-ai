"""Source-only crop generation. No inference, OCR, or image enhancement."""
from pathlib import Path
import hashlib, json
from PIL import Image

BASE = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
SOURCE = BASE / "sources/raw/HC696_original.jpg"

def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    image = Image.open(SOURCE)
    assert image.size == (3024, 4032)
    regions = {
        "header": [65, 90, 2740, 675],
        "line_01": [100, 680, 2980, 875],
        "line_02": [120, 905, 2980, 1110],
        "line_03": [120, 1135, 2980, 1340],
        "line_04": [120, 1370, 2980, 1560],
        "line_05": [120, 1590, 2980, 1780],
        "line_06": [120, 1800, 2980, 2000],
        "E01_P_overwrite": [2160, 690, 2260, 825],
        "E02_N_overwrite": [640, 1180, 745, 1290],
        "E03_W_crossing": [1660, 1160, 1770, 1290],
        "E04_B_overwrite": [1865, 1145, 1965, 1280],
        "E05_H_overwrite": [1180, 1595, 1290, 1745],
        "E06_W_overwrite": [2090, 1800, 2210, 1940],
        "E07_line1_W_I_underline": [470, 760, 715, 875],
        "E08_line1_E_R_underline": [1090, 740, 1260, 850],
        "E09_line4_W_I_underline": [1090, 1430, 1280, 1550],
        "E10_line4_E_Q_underline": [1630, 1400, 1830, 1510],
        "E11_left_red_stroke": [0, 710, 110, 910],
        "E12_below_cipher_blue_stroke": [350, 2000, 460, 2240],
        "E13_header_text": [120, 440, 985, 560],
        "E14_header_dashed_rule": [120, 553, 960, 610],
        "E15_header_red_stroke": [75, 395, 1240, 610],
        "E16_header_magenta_4": [2490, 95, 2710, 360],
        "E17_header_check_mark": [2120, 470, 2250, 600],
        "E18_line5_terminal_I_ink": [2830, 1585, 2915, 1740],
    }
    crops = OUT / "crops"
    crops.mkdir(exist_ok=True)
    entries=[]
    for name, box in regions.items():
        path = crops / (name + "_native.png")
        crop = image.crop(box)
        crop.save(path)
        entries.append({"crop_id":name,"path":str(path.relative_to(BASE)),
                        "bbox_original_xyxy":box,"transform":"PIL.Image.crop only; native RGB pixels; no resize/rotation/filter",
                        "output_size":list(crop.size),"sha256":sha256(path)})
        if name.startswith("E"):
            enlarged_path = crops / (name + "_nearest3x.png")
            enlarged = crop.resize((crop.width*3,crop.height*3),Image.Resampling.NEAREST)
            enlarged.save(enlarged_path)
            entries.append({"crop_id":name+"_nearest3x","path":str(enlarged_path.relative_to(BASE)),
                            "bbox_original_xyxy":box,"transform":"native crop followed by exactly 3x nearest-neighbor resize; no filtering",
                            "output_size":list(enlarged.size),"sha256":sha256(enlarged_path)})
    manifest={"source":str(SOURCE.relative_to(BASE)),"source_sha256":sha256(SOURCE),
              "source_size":list(image.size),"bbox_convention":"[left, top, right, bottom); zero-based original pixels",
              "crops":entries}
    (OUT/"crop_manifest_v1.json").write_text(json.dumps(manifest,indent=2)+"\n")

if __name__ == "__main__": main()

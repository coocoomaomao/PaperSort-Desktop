from pathlib import Path
from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parents[1] / "build" / "papersort.ico"
OUT.parent.mkdir(parents=True, exist_ok=True)
size = 256
img = Image.new("RGBA", (size, size), (246, 248, 251, 255))
d = ImageDraw.Draw(img)
ink = (17, 24, 32, 255)
teal = (44, 177, 161, 255)
orange = (244, 162, 97, 255)
# head + ears
d.ellipse((42, 54, 214, 226), fill=ink)
d.polygon([(54, 88), (64, 20), (112, 74)], fill=ink)
d.polygon([(202, 88), (192, 20), (144, 74)], fill=ink)
# eyes
d.ellipse((84, 116, 105, 134), fill=teal)
d.ellipse((151, 116, 172, 134), fill=teal)
# check mark
d.line((95, 172, 121, 196), fill=orange, width=18)
d.line((121, 196, 170, 152), fill=orange, width=18)
img.save(OUT, sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
print(OUT)

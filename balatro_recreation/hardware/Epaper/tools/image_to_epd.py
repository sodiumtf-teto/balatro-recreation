from pathlib import Path
from PIL import Image
import sys

WIDTH = 184
HEIGHT = 384


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: python image_to_epd.py input.png output.h")

    src = Path(sys.argv[1])
    dst = Path(sys.argv[2])

    img = Image.open(src).convert("L")
    if img.size != (WIDTH, HEIGHT):
        img = img.resize((WIDTH, HEIGHT), Image.Resampling.NEAREST)

    with dst.open("w", encoding="utf-8") as f:
        f.write("#pragma once\n\n")
        f.write("// 184 x 384, 1 bit/pixel, white=1, black=0, MSB first.\n")
        f.write(f"const unsigned char gImage_test[{WIDTH * HEIGHT // 8}] = {{\n")

        for y in range(HEIGHT):
            row = []
            for x in range(0, WIDTH, 8):
                byte = 0
                for bit in range(8):
                    if img.getpixel((x + bit, y)) >= 128:
                        byte |= 1 << (7 - bit)
                row.append(byte)
            f.write("    " + ", ".join(f"0x{b:02X}" for b in row) + ",\n")

        f.write("};\n")


if __name__ == "__main__":
    main()

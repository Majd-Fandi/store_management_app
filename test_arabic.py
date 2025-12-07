from escpos.printer import Usb
from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper
from bidi.algorithm import get_display

VENDOR_ID = 0x1FC9
PRODUCT_ID = 0x2016
INTERFACE = 0x00
OUT_EP = 0x01
IN_EP = 0x82

def process_arabic_text(text):
    if not text:
        return ""
    reshaped = arabic_reshaper.reshape(text)
    return get_display(reshaped)

def render_arabic_word_image(word, font_path="Amiri-Regular.ttf", font_size=28, padding=10):
    bidi_text = process_arabic_text(word)
    font = ImageFont.truetype(font_path, font_size)
    # Measure text
    tmp = Image.new("RGB", (1, 1), "white")
    draw = ImageDraw.Draw(tmp)
    bbox = draw.textbbox((0, 0), bidi_text, font=font)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    # Create final image
    img = Image.new("L", (w + 2 * padding, h + 2 * padding), 255)  # L = grayscale, white background
    draw = ImageDraw.Draw(img)
    draw.text((padding, padding), bidi_text, font=font, fill=0)     # 0 = black text
    # Convert to 1-bit
    img = img.convert("1")
    return img

def pack_raster_data(img_1bit):
    # Ensure mode '1'
    if img_1bit.mode != "1":
        img_1bit = img_1bit.convert("1")
    width, height = img_1bit.size
    # ESC/POS raster expects width in bytes (ceil to 8 pixels)
    row_bytes = (width + 7) // 8
    # Get raw pixels (0 or 255). In PIL '1', 0 = black (dot), 255 = white.
    pixels = img_1bit.load()
    data = bytearray()
    for y in range(height):
        byte = 0
        bit_count = 0
        for x in range(width):
            # Black pixel -> set bit to 1
            bit = 1 if pixels[x, y] == 0 else 0
            byte = (byte << 1) | bit
            bit_count += 1
            if bit_count == 8:
                data.append(byte)
                byte = 0
                bit_count = 0
        # Pad remaining bits in the last byte of the row
        if bit_count != 0:
            byte <<= (8 - bit_count)
            data.append(byte)
        # If we padded columns, ensure row length == row_bytes
        while len(data) % row_bytes != 0:
            data.append(0)
    return data, row_bytes, height

def print_arabic_word_raster(word):
    try:
        p = Usb(VENDOR_ID, PRODUCT_ID, INTERFACE, OUT_EP, IN_EP)
    except Exception as e:
        return False, f"Printer Not Found or Access Denied: {e}"

    try:
        # Initialize printer
        p._raw(b"\x1b@")  # ESC @

        img = render_arabic_word_image(word, font_path="Amiri-Regular.ttf", font_size=32)
        # Optionally, resize to head width (common: 384 for 58mm, 576 for 80mm)
        # img = img.resize((384, int(img.height * 384 / img.width)))

        data, row_bytes, height = pack_raster_data(img)

        # GS v 0 m xL xH yL yH [data]
        # m=0 (normal)
        xL = row_bytes & 0xFF
        xH = (row_bytes >> 8) & 0xFF
        yL = height & 0xFF
        yH = (height >> 8) & 0xFF
        header = bytes([0x1D, 0x76, 0x30, 0x00, xL, xH, yL, yH])

        p._raw(header + bytes(data))
        p._raw(b"\n")   # feed
        p.cut()
        p.close()
        return True, "Printed Arabic word via raw raster."
    except Exception as e:
        try:
            p.close()
        except:
            pass
        return False, f"Error during raster print: {e}"

if __name__ == "__main__":
    ok, msg = print_arabic_word_raster("تفاح")
    print(ok, msg)


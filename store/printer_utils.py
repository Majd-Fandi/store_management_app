from escpos.printer import Usb
from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper
from bidi.algorithm import get_display

# Verified USB parameters
VENDOR_ID = 0x1FC9
PRODUCT_ID = 0x2016
INTERFACE = 0x00
OUT_EP = 0x01
IN_EP = 0x82

# --- Arabic helpers ---
def process_arabic_text(text):
    if not text:
        return ""
    reshaped = arabic_reshaper.reshape(text)
    return get_display(reshaped)

def render_arabic_word_image(word, font_path="Amiri-Regular.ttf", font_size=28, padding=5):
    bidi_text = process_arabic_text(word)
    font = ImageFont.truetype(font_path, font_size)
    tmp = Image.new("RGB", (1, 1), "white")
    draw = ImageDraw.Draw(tmp)
    bbox = draw.textbbox((0, 0), bidi_text, font=font)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    img = Image.new("L", (w + 2 * padding, h + 4 * padding), 255)
    draw = ImageDraw.Draw(img)
    draw.text((padding, padding), bidi_text, font=font, fill=0)
    return img.convert("1")

def pack_raster_data(img_1bit):
    width, height = img_1bit.size
    row_bytes = (width + 7) // 8
    pixels = img_1bit.load()
    data = bytearray()
    for y in range(height):
        byte = 0
        bit_count = 0
        for x in range(width):
            bit = 1 if pixels[x, y] == 0 else 0
            byte = (byte << 1) | bit
            bit_count += 1
            if bit_count == 8:
                data.append(byte)
                byte = 0
                bit_count = 0
        if bit_count != 0:
            byte <<= (8 - bit_count)
            data.append(byte)
        while len(data) % row_bytes != 0:
            data.append(0)
    return data, row_bytes, height

# def print_arabic_inline(p, word):
#     img = render_arabic_word_image(word)
#     data, row_bytes, height = pack_raster_data(img)
#     xL = row_bytes & 0xFF
#     xH = (row_bytes >> 8) & 0xFF
#     yL = height & 0xFF
#     yH = (height >> 8) & 0xFF
#     header = bytes([0x1D, 0x76, 0x30, 0x00, xL, xH, yL, yH])
#     p._raw(header + bytes(data))
#     p._raw(b"\n")

def print_arabic_inline(p, word, qty, price, qty_x=300, price_x=400):
    # Print product name as raster image
    img = render_arabic_word_image(word)
    data, row_bytes, height = pack_raster_data(img)
    xL = row_bytes & 0xFF
    xH = (row_bytes >> 8) & 0xFF
    yL = height & 0xFF
    yH = (height >> 8) & 0xFF
    header = bytes([0x1D, 0x76, 0x30, 0x00, xL, xH, yL, yH])
    p._raw(header + bytes(data))

    # Now move horizontally and print QTY
    # ESC $ nL nH sets absolute position (nL + nH*256 dots)
    p._raw(b"\x1B\x24" + bytes([qty_x & 0xFF, (qty_x >> 8) & 0xFF]))
    p.text(str(qty))

    # Move again for PRICE
    p._raw(b"\x1B\x24" + bytes([price_x & 0xFF, (price_x >> 8) & 0xFF]))
    p.text(str(price))

    # End line
    p._raw(b"\n")



# --- Main receipt ---
def print_receipt_usb(serial_number, cart_items, total_payable, date_str):
    print("<======================== printing the hybrid receipt now ========================>")
    try:
        p = Usb(VENDOR_ID, PRODUCT_ID, INTERFACE, OUT_EP, IN_EP)
    except Exception as e:
        return False, f"Printer Not Found or Access Denied: {e}"

    try:
        # Header
        p.set(align='center', double_height=True, double_width=True, bold=True)
        p.text("SALES RECEIPT\n")
        p.set(align='left', bold=False)
        p.text("-" * 24 + "\n")

        # Details
        p.set(align='left',double_height=False, double_width=False,normal_textsize=True, bold=True)
        p.text(f"Receipt No: {serial_number}\n")
        p.text("\n")
        p.text(f"Date: {date_str}\n")
        p.text("-" * 42 + "\n")

        # Items header
        p.set(bold=True)
        p.text("{:<25}{:>5}{:>12}\n".format("PRODUCT", "QTY", "PRICE"))
        p.set(bold=False)
        p.text("-" * 42 + "\n")

        # Items list
        for item in cart_items:
            name = item.get('product_name', 'N/A')
            qty = str(item.get('quantity', 0))
            try:
                price = "{:,.0f}".format(float(item.get('total_price', 0)))
            except ValueError:
                price = "Error"

            print_arabic_inline(p, name, qty, price)
            # # Print product name in Arabic as raster
            # print_arabic_inline(p, name)

            # # Then print qty and price as text
            # p.text("{:>5}{:>12}\n".format(qty, price))

        p.text("-" * 42 + "\n")

        # Total
        p.set(align='left', double_width=True, double_height=True, bold=True)
        try:
            total_str = "{:,.0f}".format(float(total_payable))
        except ValueError:
            total_str = "0.00"
        p.text(f"  {total_str} SYP \n")

        p.text("\n" * 3)
        p.cut()
        p.close()
        return True, "Printed successfully with Arabic product names."
    except Exception as e:
        try:
            p.close()
        except:
            pass
        return False, f"Error during printing: {str(e)}"














# from escpos.printer import Usb
# from PIL import Image, ImageDraw, ImageFont
# import arabic_reshaper
# from bidi.algorithm import get_display

# # Verified USB parameters
# VENDOR_ID = 0x1FC9
# PRODUCT_ID = 0x2016
# INTERFACE = 0x00
# OUT_EP = 0x01
# IN_EP = 0x82

# # --- Arabic helpers ---
# def process_arabic_text(text):
#     if not text:
#         return ""
#     reshaped = arabic_reshaper.reshape(text)
#     return get_display(reshaped)

# def render_arabic_word_image(word, font_path="Amiri-Regular.ttf", font_size=28, padding=5):
#     bidi_text = process_arabic_text(word)
#     font = ImageFont.truetype(font_path, font_size)
#     tmp = Image.new("RGB", (1, 1), "white")
#     draw = ImageDraw.Draw(tmp)
#     bbox = draw.textbbox((0, 0), bidi_text, font=font)
#     w = bbox[2] - bbox[0]
#     h = bbox[3] - bbox[1]
#     img = Image.new("L", (w + 2 * padding, h + 2 * padding), 255)
#     draw = ImageDraw.Draw(img)
#     draw.text((padding, padding), bidi_text, font=font, fill=0)
#     return img.convert("1")

# def pack_raster_data(img_1bit):
#     width, height = img_1bit.size
#     row_bytes = (width + 7) // 8
#     pixels = img_1bit.load()
#     data = bytearray()
#     for y in range(height):
#         byte = 0
#         bit_count = 0
#         for x in range(width):
#             bit = 1 if pixels[x, y] == 0 else 0
#             byte = (byte << 1) | bit
#             bit_count += 1
#             if bit_count == 8:
#                 data.append(byte)
#                 byte = 0
#                 bit_count = 0
#         if bit_count != 0:
#             byte <<= (8 - bit_count)
#             data.append(byte)
#         while len(data) % row_bytes != 0:
#             data.append(0)
#     return data, row_bytes, height

# def print_arabic_inline(p, word):
#     img = render_arabic_word_image(word)
#     data, row_bytes, height = pack_raster_data(img)
#     xL = row_bytes & 0xFF
#     xH = (row_bytes >> 8) & 0xFF
#     yL = height & 0xFF
#     yH = (height >> 8) & 0xFF
#     header = bytes([0x1D, 0x76, 0x30, 0x00, xL, xH, yL, yH])
#     p._raw(header + bytes(data))
#     p._raw(b"\n")

# # --- Main receipt ---
# def print_receipt_usb(serial_number, cart_items, total_payable, date_str):
#     print("<======================== printing the hybrid receipt now ========================>")
#     try:
#         p = Usb(VENDOR_ID, PRODUCT_ID, INTERFACE, OUT_EP, IN_EP)
#     except Exception as e:
#         return False, f"Printer Not Found or Access Denied: {e}"

#     try:
#         # Header
#         p.set(align='center', double_height=True, double_width=True, bold=True)
#         p.text("SALES RECEIPT\n")
#         p.set(align='left', bold=False)
#         p.text("-" * 24 + "\n")

#         # Details
#         p.set(align='left',double_height=False, double_width=False,normal_textsize=True, bold=True)
#         p.text(f"Receipt No: {serial_number}\n")
#         p.text("\n")
#         p.text(f"Date: {date_str}\n")
#         p.text("-" * 42 + "\n")

#         # Items header
#         p.set(bold=True)
#         p.text("{:<25}{:>5}{:>12}\n".format("PRODUCT", "QTY", "PRICE"))
#         p.set(bold=False)
#         p.text("-" * 42 + "\n")

#         # Items list
#         for item in cart_items:
#             name = item.get('product_name', 'N/A')
#             qty = str(item.get('quantity', 0))
#             try:
#                 price = "{:,.0f}".format(float(item.get('total_price', 0)))
#             except ValueError:
#                 price = "Error"

#             # Print product name in Arabic as raster
#             print_arabic_inline(p, name)

#             # Then print qty and price as text
#             p.text("{:>5}{:>12}\n".format(qty, price))

#         p.text("-" * 42 + "\n")

#         # Total
#         p.set(align='left', double_width=True, double_height=True, bold=True)
#         try:
#             total_str = "{:,.0f}".format(float(total_payable))
#         except ValueError:
#             total_str = "0.00"
#         p.text(f"  {total_str} SYP \n")

#         p.text("\n" * 3)
#         p.cut()
#         p.close()
#         return True, "Printed successfully with Arabic product names."
#     except Exception as e:
#         try:
#             p.close()
#         except:
#             pass
#         return False, f"Error during printing: {str(e)}"


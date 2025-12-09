from escpos.printer import Usb


# USB parameters
VENDOR_ID = 0x1FC9
PRODUCT_ID = 0x2016
INTERFACE = 0x00
OUT_EP = 0x01
IN_EP = 0x82
ARABIC_EENCODING='cp1256'


def print_receipt_usb(serial_number, cart_items, total_payable, date_str):
    try:
        p = Usb(VENDOR_ID, PRODUCT_ID, INTERFACE, OUT_EP, IN_EP)
    except Exception as e:
        return False, f"Printer Not Found: {e}"

    try:
        # Initialize printer
        p._raw(b"\x1b@")
        
        # HEADER - LARGE FONT
        p.set(align='center', double_height=True, double_width=True, bold=True)
        p.text("SALES RECEIPT\n")
        
        # Reset to normal font
        p.text("=" * 24 + "\n\n")
        p.set(align='left', double_height=False, double_width=False,normal_textsize=True, bold=False)
        
        # RECEIPT DETAILS - NORMAL FONT
        p.text(f"Receipt No: {serial_number}\n")
        p.text('\n')
        p.text(f"Date: {date_str}\n")
        p.text("-" * 48 + "\n\n")
        
        # ITEMS HEADER
        p.set(bold=True)
        p.text(f"{'PRICE':<15}{'QTY':>3}{'ITEM':>30}\n")
        p.set(bold=False)
        p.text("-" * 48 + "\n")
        
        # ITEMS LIST
        for item in cart_items:
            name = item.get('product_name', 'N/A')
            qty = str(item.get('quantity', 0))
            price = "{:,.0f}".format(float(item.get('total_price', 0)))
            
            p._raw(b'\x1B\x74\x21')
            line=f"{name:<30}{qty:>3}{price:>15}\n\n"
            p._raw(line.encode(ARABIC_EENCODING))
        
        p.text("-" * 48 + "\n\n")
        
        # TOTAL - LARGE FONT
        p.set(align='left', double_height=True, double_width=True, bold=True)
        try:
            total_str = "{:,.0f}".format(float(total_payable))
        except ValueError:
            total_str = "0"
        
        p.text(f"{total_str} SYP\n\n")
        
        # Feed and cut
        p.text("\n" * 3)
        p.cut()
        p.close()
        
        return True, "Printed successfully"
    
    except Exception as e:
        try:
            p.close()
        except:
            pass
        return False, f"Error: {str(e)}"
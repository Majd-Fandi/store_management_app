# import arabic_reshaper
# from bidi.algorithm import get_display

# # Verified USB parameters for the XP Printer (VID: 0x1FC9, PID: 0x2016)
# VENDOR_ID = 0x1FC9
# PRODUCT_ID = 0x2016
# INTERFACE = 0x00
# OUT_EP = 0x01
# IN_EP = 0x82

# # Helper Function: Must be defined outside or inside the main function
# def process_arabic_text(text):
#     """Reshapes and reverses Arabic text for LTR printer systems."""
#     if not text: return ""
#     # 1. Reshape: Connects letters
#     reshaped_text = arabic_reshaper.reshape(text)
#     print(reshaped_text)
#     print(get_display(reshaped_text))

#     # 2. Bidi: Reverses the text order (Right-to-Left becomes Left-to-Right)
#     # return reshaped_text
#     return get_display(reshaped_text) #trytrytry 

# def print_receipt_usb(serial_number, cart_items, total_payable, date_str):
#     """
#     Prints a hybrid English/Arabic receipt using text commands and Code Page 864.
#     """
#     print("<======================== printing the Arabic text receipt now ========================>")
    
#     try:
#         # Initialize Printer with the required USB parameters
#         p = Usb(VENDOR_ID, PRODUCT_ID, INTERFACE, OUT_EP, IN_EP)
#     except Exception as e:
#         return False, f"Printer Not Found or Access Denied: {e}"

#     try:

#         # --- CRITICAL CHANGE 1: Set Arabic Code Page ---
#         # PC864 is the standard code page for Arabic.
#         # This tells the printer to interpret incoming bytes as Arabic glyphs.

#         # p.charcode('CP864')
#         # p.charcode('CP1256')
#         p.charcode('Auto')

#         # -----------------------------------------------

           
#         # --- 1. Header (Static English Text) ---
#         # The font should handle English characters even in CP864 mode.
#         p.set(align='center', double_height=True, double_width=True, bold=True)
#         p.text("SALES RECEIPT\n")
        
#         p.set(align='left', double_height=False, double_width=False, bold=False)
#         p.text("-" * 42 + "\n") # Note: Increased width from 24 to 42 for consistency with below
        
#         p.set(align='left', normal_textsize=True, double_height=False, double_width=False, bold=False)
#         # --- 2. Receipt Details ---
#         p.text(f"Receipt No: {serial_number}\n")
#         p.text("\n")
#         p.text(f"Date: {date_str}\n")
        
#         p.text("-" * 42 + "\n")
        
#         # --- 3. Items Header ---
#         p.set(bold=True)
#         # Using a fixed width format for columns
#         p.text("{:<25}{:>5}{:>12}\n".format("PRODUCT", "QTY", "PRICE"))
#         p.set(bold=False)
#         p.text("-" * 42 + "\n")

#         # --- 4. Items List (Arabic Product Names) ---
#         for item in cart_items:
#             # --- CRITICAL CHANGE 2: Preprocess the Arabic Name ---
#             # Assume 'product_name' contains the raw Arabic string
#             name_raw = item.get('product_name', 'N/A')
#             name = process_arabic_text(name_raw) # Apply shaping and reversal
#             # ----------------------------------------------------
            
#             qty = str(item.get('quantity', 0))
            
#             # Ensure price is formatted nicely
#             try:
#                 price = "{:,.0f}".format(float(item.get('total_price', 0)))
#             except ValueError:
#                 price = "Error"

#             # Print the item line
#             # The name is now processed to look correct when printed LTR by the CP864 font.
#             p.text("{:<25}{:>5}{:>12}\n".format(name, qty, price))
            
#         p.text("-" * 42 + "\n")
        
#         # --- 5. Total Footer (English Text) ---
#         # ... (rest of your footer logic remains the same) ...
#         p.set(align='left', bold=True, double_width=True)
#         p.text("\n")
        
#         p.set(align='left', double_width=True, double_height=True, bold=True)
#         try:
#             total_str = "{:,.0f}".format(float(total_payable))
#         except ValueError:
#             total_str = "0.00"
            
#         p.text(f"  {total_str} SYP \n")
        
#         p.text("\n" * 3)

#         # --- 7. Final Commands ---
#         p.cut()
#         p.close()
        
#         return True, "Printed successfully using text commands with Arabic Code Page."
    
#     except Exception as e:
#         # Close the connection if an error occurs during printing
#         p.close()
#         return False, f"Error during printing: {str(e)}"





















# from escpos.printer import Usb

# # Verified USB parameters for the NXP Printer (VID: 0x1FC9, PID: 0x2016)
# # These remain the same for communicating with the physical USB device.
# VENDOR_ID = 0x1FC9
# PRODUCT_ID = 0x2016
# INTERFACE = 0x00
# OUT_EP = 0x01
# IN_EP = 0x82

# def print_receipt_usb(serial_number, cart_items, total_payable, date_str):
#     """
#     Prints an English-language receipt using basic ESC/POS text commands.

#     This function is much faster than the PIL/Image-based approach as it sends
#     raw text commands directly to the thermal printer.
#     """
#     print("<======================== printing the text receipt now ========================>")
    
#     try:
#         # Initialize Printer with the required USB parameters
#         p = Usb(VENDOR_ID, PRODUCT_ID, INTERFACE, OUT_EP, IN_EP)
#     except Exception as e:
#         # Return error if the printer is not found or access is denied
#         return False, f"Printer Not Found or Access Denied: {e}"

#     try:
#         # --- 1. Header ---
#         p.set(align='center', double_height=True, double_width=True, bold=True)
#         p.text("SALES RECEIPT\n")
        
#         p.set(align='left', double_height=False, double_width=False, bold=False)
#         p.text("-" * 24 + "\n")
        
#         p.set(align='left', normal_textsize=True, double_height=False, double_width=False, bold=False)
#         # --- 2. Receipt Details ---
#         p.text(f"Receipt No: {serial_number}\n")
#         p.text("\n")
#         p.text(f"Date: {date_str}\n")
        
#         p.text("-" * 42 + "\n")
        
#         # --- 3. Items Header ---
#         p.set(bold=True)
#         # Using a fixed width format for columns
#         p.text("{:<25}{:>5}{:>12}\n".format("PRODUCT", "QTY", "PRICE"))
#         p.set(bold=False)
#         p.text("-" * 42 + "\n")

#         # --- 4. Items List ---
#         for item in cart_items:
#             name = item.get('product_name', 'N/A')
#             qty = str(item.get('quantity', 0))
            
#             # Ensure price is formatted nicely
#             try:
#                 price = "{:,.0f}".format(float(item.get('total_price', 0)))
#             except ValueError:
#                 price = "Error"

#             # Print the item line
#             p.text("{:<25}{:>5}{:>12}\n".format(name, qty, price))
        
#         p.text("-" * 42 + "\n")
        
#         # --- 5. Total Footer ---
#         # Set alignment to right for the total amount line
#         p.set(align='left', bold=True, double_width=True)
#         # p.text(f"TOTAL :\n")
#         p.text("\n")
        
#         # Print the actual total value, set to left for currency look
#         # Note: You can align numbers left or right depending on preference.
#         p.set(align='left', double_width=True, double_height=True, bold=True)
#         try:
#             total_str = "{:,.0f}".format(float(total_payable))
#         except ValueError:
#             total_str = "0.00"
            
#         p.text(f"  {total_str} SYP \n")
        
#         p.text("\n" * 3) # Add extra blank lines for spacing

#         # --- 6. Final Message ---
#         # p.set(align='center', bold=False, double_height=False, double_width=False)
#         # p.text("Thank you for your visit!\n")
#         # p.text("Visit us again soon.\n")

#         # --- 7. Final Commands ---
#         p.cut()
#         p.close()
        
#         return True, "Printed successfully using text commands."
    
#     except Exception as e:
#         # This handles errors during the actual printing/communication process
#         return False, f"Error during printing: {str(e)}"



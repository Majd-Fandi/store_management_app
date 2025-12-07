from escpos.printer import Usb
import time

# --- CORRECTED PARAMETERS FROM USB VIEWER REPORT ---
VENDOR_ID = 0x1fc9  
PRODUCT_ID = 0x2016 
INTERFACE_NUMBER = 0x00  # From bInterfaceNumber
OUT_ENDPOINT = 0x01      # From bEndpointAddress (Direction=OUT)
IN_ENDPOINT = 0x82       # From bEndpointAddress (Direction=IN)

# The bus number is usually 0 and is often omitted, but we include it for clarity
BUS = 0 

print(f"--- Attempting connection via Direct USB (VID:{hex(VENDOR_ID)}, PID:{hex(PRODUCT_ID)}) ---")

try:
    # Use the verified parameters
    p = Usb(VENDOR_ID, PRODUCT_ID, BUS, OUT_ENDPOINT, IN_ENDPOINT) 
    
    print("✅ Connection Successful!")
    p.text("Majd Yousif Fandi \n")
    # p.text("TEST RECEIPT SUCCESS via VERIFIED DIRECT USB\n")
    # p.text("TEST RECEIPT SUCCESS via VERIFIED DIRECT USB\n")
    # p.text("TEST RECEIPT SUCCESS via VERIFIED DIRECT USB\n")
    # p.text("TEST RECEIPT SUCCESS via VERIFIED DIRECT USB\n")
    # p.text("TEST RECEIPT SUCCESS via VERIFIED DIRECT USB\n")
    p.cut()
    
    print("✅ Print command sent successfully.")
    
except Exception as e:
    print(f"❌ Connection Failed! Detailed Error: {e}")
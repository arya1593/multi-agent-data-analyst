"""Generates a QR code PNG for the public demo URL. Usage: python generate_qr.py <url>"""
import sys

try:
    import qrcode
except ImportError:
    print("Run: pip install qrcode[pil]")
    sys.exit(1)

url = sys.argv[1] if len(sys.argv) > 1 else input("Enter your Streamlit app URL: ").strip()
if not url:
    print("No URL provided.")
    sys.exit(1)

qr = qrcode.QRCode(version=1, box_size=10, border=4)
qr.add_data(url)
qr.make(fit=True)
img = qr.make_image(fill_color="black", back_color="white")
img.save("demo_qr.png")
print(f"QR code saved: demo_qr.png")
print(f"URL encoded:   {url}")

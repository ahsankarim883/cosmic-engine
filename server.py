import os
import time
import threading
import requests
from fpdf import FPDF
from flask import Flask

# ==========================================
# 1. SUPABASE CONNECTION
# ==========================================
SUPABASE_URL = "https://qxzydznbejrorfzjezxg.supabase.co"

# We removed the hardcoded key. It now securely pulls it from Render.com's secret vault!
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

# ==========================================
# 2. PDF GENERATOR CLASS
# ==========================================
class PDFCertificate(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 20)
        self.set_text_color(44, 62, 80)
        self.cell(0, 15, 'COSMIC FIELD INSPECTOR', 0, 1, 'C')
        
        self.set_font('Arial', 'B', 14)
        self.set_text_color(100, 100, 100)
        self.cell(0, 10, 'OFFICIAL ELECTRICAL INSPECTION CERTIFICATE (EICR)', 0, 1, 'C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

# ==========================================
# 3. BACKGROUND AUTOMATION ENGINE
# ==========================================
def run_background_loop():
    print("🚀 [BACKGROUND] PDF Engine Started!")
    
    if not SUPABASE_KEY:
        print("❌ CRITICAL ERROR: No Supabase Key found in environment variables!")
        return
        
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }
    
    processed_ids = set()
    
    while True:
        try:
            endpoint = f"{SUPABASE_URL}/rest/v1/inspections?select=*&order=created_at.desc&limit=1"
            response = requests.get(endpoint, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if data:
                    inspection = data[0]
                    insp_id = inspection['id']
                    
                    if insp_id not in processed_ids:
                        processed_ids.add(insp_id)
                        payload = inspection.get('payload', {})
                        circuit_name = str(payload.get('circuit_name', 'N/A'))
                        
                        print(f"🔔 [NEW DATA] Generating PDF for {circuit_name}...")
                        
                        # Generate PDF
                        pdf = PDFCertificate()
                        pdf.add_page()
                        
                        pdf.set_font('Arial', 'B', 12)
                        pdf.set_text_color(0, 0, 0)
                        pdf.cell(0, 10, 'INSPECTION DETAILS', 0, 1, 'L')
                        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
                        pdf.ln(5)
                        
                        pdf.set_font('Arial', '', 11)
                        pdf.cell(50, 8, 'Circuit / Asset Name:', 0, 0)
                        pdf.cell(0, 8, circuit_name, 0, 1)
                        pdf.cell(50, 8, 'Location:', 0, 0)
                        pdf.cell(0, 8, str(payload.get('location', 'N/A')), 0, 1)
                        pdf.ln(10)
                        
                        visual_pass = "PASS" if payload.get('visual_check_pass') else "FAIL"
                        earth_pass = "PASS" if payload.get('earth_loop_pass') else "FAIL"
                        
                        pdf.set_font('Arial', 'B', 12)
                        pdf.cell(0, 10, 'SAFETY CHECKS', 0, 1, 'L')
                        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
                        pdf.ln(5)
                        
                        pdf.set_font('Arial', '', 11)
                        pdf.cell(80, 8, 'Visual Inspection Satisfactory:', 0, 0)
                        pdf.cell(0, 8, visual_pass, 0, 1)
                        pdf.cell(80, 8, 'Earth Loop Impedance (Zs):', 0, 0)
                        pdf.cell(0, 8, earth_pass, 0, 1)
                        
                        filename = f"Certificate_{insp_id[:8]}.pdf"
                        pdf.output(filename)
                        
                        # Upload to Cloud
                        with open(filename, 'rb') as f:
                            pdf_bytes = f.read()
                            
                        upload_endpoint = f"{SUPABASE_URL}/storage/v1/object/certificates/{filename}"
                        upload_headers = {
                            "apikey": SUPABASE_KEY,
                            "Authorization": f"Bearer {SUPABASE_KEY}",
                            "Content-Type": "application/pdf"
                        }
                        
                        requests.post(upload_endpoint, headers=upload_headers, data=pdf_bytes)
                        print(f"✅ [SUCCESS] {filename} uploaded to cloud!")

        except Exception as e:
            print(f"⚠️ [WARNING] Network blip: {e}")
            
        time.sleep(3) # Check database every 3 seconds

# ==========================================
# 4. WEB SERVER (KEEPS THE CLOUD AWAKE)
# ==========================================
app = Flask(__name__)

@app.route('/')
def health_check():
    return "✅ Cosmic Field PDF Engine is online and listening 24/7!"

if __name__ == "__main__":
    listener_thread = threading.Thread(target=run_background_loop)
    listener_thread.daemon = True
    listener_thread.start()
    
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
import os
import time
import threading
import requests
from fpdf import FPDF
from flask import Flask

SUPABASE_URL = "https://qxzydznbejrorfzjezxg.supabase.co"
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

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

def run_background_loop():
    print("🚀 [BACKGROUND] PDF Engine Started!", flush=True)
    
    if not SUPABASE_KEY:
        print("❌ CRITICAL ERROR: The SUPABASE_KEY is blank in Render!", flush=True)
        return
        
    headers = {
        "apikey": SUPABASE_KEY.strip(),
        "Authorization": f"Bearer {SUPABASE_KEY.strip()}",
        "Content-Type": "application/json",
        "Cache-Control": "no-cache" # Prevent caching
    }
    
    processed_ids = set()
    print("📡 [SYSTEM] Successfully connected to loop. Waiting for Netlify App data...", flush=True)
    
    while True:
        try:
            # Removed the _ts parameter because Supabase PostgREST tries to read it as a column filter!
            endpoint = f"{SUPABASE_URL}/rest/v1/inspections?select=*&order=created_at.desc&limit=1"
            
            response = requests.get(endpoint, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if data:
                    inspection = data[0]
                    insp_id = inspection['id']
                    
                    if insp_id not in processed_ids:
                        payload = inspection.get('payload', {})
                        circuit_name = str(payload.get('circuit_name', 'N/A'))
                        
                        print(f"\n🔔 [NEW DATA] Caught inspection for: {circuit_name}! Generating PDF...", flush=True)
                        
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
                        
                        with open(filename, 'rb') as f:
                            pdf_bytes = f.read()
                            
                        upload_endpoint = f"{SUPABASE_URL}/storage/v1/object/certificates/{filename}"
                        upload_headers = {
                            "apikey": SUPABASE_KEY.strip(),
                            "Authorization": f"Bearer {SUPABASE_KEY.strip()}",
                            "Content-Type": "application/pdf"
                        }
                        
                        upload_res = requests.post(upload_endpoint, headers=upload_headers, data=pdf_bytes)
                        if upload_res.status_code in (200, 201):
                            print(f"✅ [SUCCESS] {filename} uploaded to cloud!", flush=True)
                            # ONLY add to processed_ids if the upload actually succeeds!
                            processed_ids.add(insp_id) 
                        else:
                            print(f"❌ [UPLOAD FAILED] Database blocked the upload: {upload_res.text}", flush=True)
            else:
                print(f"❌ [DATABASE REJECTION] Code: {response.status_code} | Reason: {response.text}", flush=True)

        except Exception as e:
            print(f"⚠️ [WARNING] System Error: {e}", flush=True)
            
        time.sleep(3)

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

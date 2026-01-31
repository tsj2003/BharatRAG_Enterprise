from fpdf import FPDF
import os

# Create data directory if it doesn't exist
os.makedirs("data", exist_ok=True)

class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'GOVERNMENT OF MADHYA PRADESH - OFFICIAL RECORD', 0, 1, 'C')
        self.ln(10)

def create_pdf(filename, content):
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, content)
    pdf.output(filename)
    print(f"Created: {filename}")

# 1. Land Record (Khasra) - Proof of Ownership
land_record_text = """
RECORD OF RIGHTS (KHASRA) - TEHSIL: HUZUR, DISTRICT: BHOPAL
Year: 2023-2024

Owner Name: Ramesh Patel (s/o Suresh Patel)
Village: Arera
Survey Number: 452/12
Area: 5.5 Acres
Crop: Soybean (Kharif)
Irrigation: Tube Well (Functional)

Encumbrances: None. The land is free from any mortgage or lien.
Mutation Status: Verified.
Digitally Signed by Patwari, Halka No. 12.
"""
create_pdf("data/land_record_ramesh.pdf", land_record_text)

# 2. Loan Policy Document (The Rules)
policy_text = """
MADHYA PRADESH KISAN CREDIT CARD (KCC) SCHEME - 2024 GUIDELINES

Eligibility Criteria for High-Value Agriculture Loans (> 2 Lakhs):
1. Applicant must be a resident of Madhya Pradesh.
2. Applicant must own at least 3 Acres of cultivable land.
3. Applicant must not have any pending criminal litigation regarding land disputes.
4. Primary crop must be insured under PMFBY.

Interest Rate: 4% per annum (Subsidized).
Collateral: Hypothecation of crops up to 1.6 Lakhs. Land mortgage for higher amounts.
"""
create_pdf("data/loan_policy_2024.pdf", policy_text)

# 3. Court Order (Clearance)
court_order_text = """
DISTRICT COURT OF BHOPAL
Case Status Report - Civil Suits

Search Query: Ramesh Patel
Father's Name: Suresh Patel
Address: Village Arera, Bhopal

Result: NO PENDING CASES FOUND.

Previous Litigation:
Case No: 44/2019 (Property Dispute) -> DISMISSED in favor of Ramesh Patel on 12/08/2021.
The subject property (Survey 452/12) is declared free of all claims.

Certified Copy.
Registrar, District Court.
"""
create_pdf("data/court_order_clearance.pdf", court_order_text)

print("LinkedIn Demo Data Created Successfully!")

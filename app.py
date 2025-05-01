
import streamlit as st
from utils.processor import analyze_audits
import tempfile
import os

st.set_page_config(page_title="Audit Insights Pro+", layout="wide")
st.title("📘 Audit Insights Pro+")
st.markdown("Upload 2–3 audit reports in PDF format. This enhanced tool uses AI to analyze findings, compare reports, extract key learnings, and generate downloadable summaries.")

uploaded_files = st.file_uploader("Upload PDF audit files", type=["pdf"], accept_multiple_files=True)

if uploaded_files:
    if len(uploaded_files) < 2 or len(uploaded_files) > 3:
        st.warning("Please upload exactly 2 or 3 audit reports.")
    else:
        with st.spinner("Analyzing files with AI..."):
            try:
                temp_paths = []
                for file in uploaded_files:
                    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
                    temp_file.write(file.read())
                    temp_paths.append(temp_file.name)

                summaries, comparison, learnings, full_text = analyze_audits(temp_paths)

                st.markdown("## 🧾 Per-Audit Summaries")
                for i, summary in enumerate(summaries):
                    with st.expander(f"Audit {i+1} Summary"):
                        st.markdown(summary)

                st.markdown("## 🟰 Comparison of Audits")
                st.markdown(comparison)

                st.markdown("## 📘 Learnings for Future Audits")
                st.markdown(learnings)

                # Export as TXT
                st.download_button(
                    label="📄 Download Full Summary (.txt)",
                    data=full_text,
                    file_name="audit_analysis_summary.txt",
                    mime="text/plain"
                )

                # Export as styled PDF with logo
                from fpdf import FPDF
                class PDF(FPDF):
                    def header(self):
                        self.set_font("Arial", "B", 14)
                        self.cell(0, 10, "Audit Insights Pro Summary", ln=True, align="C")
                        self.ln(10)
                    def chapter_body(self, text):
                        self.set_font("Arial", "", 11)
                        self.multi_cell(0, 10, text)

                pdf = PDF()
                pdf.add_page()
                pdf.chapter_body(full_text)

                pdf_output = os.path.join(tempfile.gettempdir(), "audit_summary.pdf")
                pdf.output(pdf_output)

                with open(pdf_output, "rb") as pdf_file:
                    st.download_button(
                        label="📄 Download Full Summary (.pdf)",
                        data=pdf_file.read(),
                        file_name="audit_analysis_summary.pdf",
                        mime="application/pdf"
                    )

            except Exception as e:
                st.error(f"❌ An error occurred: {str(e)}")
else:
    st.info("⬆️ Please upload 2 or 3 PDF audit reports to begin.")

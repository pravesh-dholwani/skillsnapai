import streamlit as st
import os
import tempfile

from main import main

st.title("SkillSnap AI")
st.subheader("Instant Insights. Better Resumes.")

os.environ["GROQ_API_KEY"] = st.secrets['GROQ_API_KEY']


file = st.file_uploader("Upload your resume.", accept_multiple_files=False, type=["pdf"])
if file is not None:
    if st.button("Analyze Resume"):
        # Use a temporary file to handle the upload safely, especially for deployed apps
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
            temp_pdf.write(file.getbuffer())
            pdf_path = temp_pdf.name

        try:
            with st.spinner("Analyzing your resume... This may take a moment."):
                analysis = main(pdf_path)

            if "is_resume" in analysis and analysis["is_resume"] is False:
                st.error("Not a Valid Resume. Please Upload a Valid Resume.")
            else:
                for section, detailed in analysis.items():
                    st.subheader(section.capitalize())
                    good_points = detailed.get('good', 'N/A')
                    wrong_points = detailed.get('wrong', 'N/A')
                    improvement_points = detailed.get('improvement', 'N/A')
 
                    if not wrong_points or len(wrong_points) == 0:
                        wrong_points = "Nothing wrong."
 
                    st.markdown(f"**What's Good:** {good_points}")
                    st.markdown(f"**What's Wrong:** {wrong_points}")
                    st.markdown(f"**What to Add/Improve:** {improvement_points}")
                    st.markdown("---")
        except Exception as e:
            st.error("Oops! Something went wrong during the analysis.")
            st.error("Please ensure your resume is a standard text-based PDF and try again.")
            print(f"An error occurred during the main analysis process: {e}") # This will print to your Streamlit logs
        finally:
            # Clean up the temporary file
            if 'pdf_path' in locals() and os.path.exists(pdf_path):
                os.remove(pdf_path)

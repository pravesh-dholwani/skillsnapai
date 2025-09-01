from dotenv import load_dotenv
import os
from langchain.document_loaders import PyPDFLoader

from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langchain_core.output_parsers import JsonOutputParser

section_wise_checklist = {
    "skills": [
        "Are they up-to-date (modern tools, frameworks, certifications)",
        "Is the skill list realistic (not a laundry list of everything under the sun)?",
        "Is the list clean and relevant (not overloaded with everything)?"
    ],
    "experience": [
        "Do job titles and companies show growth and progression?",
        "Do bullet points reflect impact, not just duties? (e.g., 'Increased sales by 20%' vs 'Responsible for sales.')",
        "Are achievements measurable and credible?",
        "each entry has company name, role, and dates?",
        "Each bullet starts with a strong action verb (Led, Designed, Increased, Built)?",
        "included numbers or measurable results (e.g., “Reduced cost by 15%”)?",
        "wrote achievements, not just responsibilities?",
    ],
    "achievements": [
        "Do projects show initiative, problem-solving, and results?",
        "Do certifications come from recognized sources (AWS, Google, Coursera, etc.)?",
        "Have they gone beyond the minimum (side projects, certifications, awards)?"
    ],
    "education": [
        "listed degree, college, and tenure years?",
        "low GPAs or percentage not included?"
    ],
    "contact_details": [
        "name is clear?",
        "added a phone number?",
        "added an email address?"
    ]
}

load_dotenv()

def get_section_analysis(section_name: str, section_content: any, llm: ChatGroq) -> dict:
    """
    Analyzes a specific section of a resume using an LLM based on what's good,
    what's wrong, and what can be improved.

    Args:
        section_name: The name of the resume section (e.g., "Skills").
        section_content: The content of the section to be analyzed.
        llm: An initialized ChatGroq instance.

    Returns:
        A dictionary containing the analysis with keys 'good', 'wrong', 'improvement'.
    """
    if not section_content:
        return {
            "good": "N/A",
            "wrong": "Section is empty or was not found in the resume.",
            "improvement": "Add content to this section."
        }
    
    checklist = "\n".join([f"- {item}" for item in section_wise_checklist.get(section_name, [])])

    analysis_prompt_template = """You are an expert career coach and resume reviewer. Your task is to analyze the '{section_name}' section of a resume.
Provide a critical analysis based on the following criteria:
1. What is good: Point out the strengths and well-presented information.
2. What is wrong: Identify weaknesses, vagueness, or formatting issues.
3. What needs to be added: Suggest specific additions, providing clear reasons and examples to enhance the section.
These are the points you have to check for {section_name}'
CheckList for {section_name}:
{checklist}
Please provide your analysis in a valid JSON format with three keys: "good", "wrong", and "improvement".
All three keys should have a string value and provide each and every thing in detail.
If there is nothing WRONG, dont comment on it.
Improvements should be mentioned in a very helpful way so the the reader will have some motivation to improve.
Dont comment on styling. Only focus on the content.
Here is the content of the '{section_name}' section to analyze:
---
{content}
---"""

    prompt = ChatPromptTemplate.from_template(analysis_prompt_template)

    chain = prompt | llm | JsonOutputParser()

    try:
        return chain.invoke({
            "section_name": section_name.capitalize(),
            "checklist": checklist,
            "content": str(section_content) # Ensure content is a string for the prompt
        })
    except Exception as e:
        print(f"Error analyzing section '{section_name}': {e}")
        return None

def get_pdf_content(pdf_path):
    """
    Loads content from a PDF file using PyPDFLoader.
    """
    try:
        loader = PyPDFLoader(pdf_path)
        pages = loader.load_and_split()
        return "".join(page.page_content for page in pages)
    except Exception as e:
        print(f"Error loading PDF: {e}")
        return None

def main(pdf_file):
    analysis = {}
    print("analysis started")
    # pdf_file = "resumes/resume_pravesh.pdf"  # Replace with your PDF file path
    if not os.path.exists(pdf_file):
        print(f"Error: PDF file '{pdf_file}' not found.")
    else:
        pdf_content = get_pdf_content(pdf_file)
        if pdf_content:
            print("Resume content loaded successfully. Analyzing with AI...")

            SYSTEM_PROMPT = '''
            You are an expert Resume Analyzer. Your task is to take out all information from the resume and divide it into 5 sections - skills, experience, achievements, education, Contact Details.
            Instructions:-
            1) Take the accurate information for each section.
            2) Give the output in valid JSON format. where the key is the section name and the value is the information.
            3) If the information for a specific section is not available, then leave it blank.

            The output should consider 5 keys - skills, experience, achievements, education, contact_details, is_resume.
            If the content is not looking or evaluating as resume you add the key is_resume in aoutput with value false.
            Each Key should have a json having all the information (not just summary) for specific section.

            '''
            # Define the prompt for the LLM
            prompt = ChatPromptTemplate.from_messages([
                ("system", SYSTEM_PROMPT),
                ("human", "Here is the resume content:\n\n{resume}")
            ])

            # Initialize the Groq LLM
            # llm = ChatGroq(model_name="llama3-8b-8192", temperature=0.2)
            # llm = ChatGroq(model_name="deepseek-r1-distill-llama-70b", temperature=0.0)
            llm = ChatGroq(model="openai/gpt-oss-120b", temperature=0.1)

            # Create the chain to process the input
            extraction_chain = prompt | llm | JsonOutputParser()

            extracted_data = extraction_chain.invoke({"resume": pdf_content})
            print("\n--- Groq LLM Initial Extraction ---\n")
            print(extracted_data)

            if "is_resume" in extracted_data and extracted_data["is_resume"] is False:
                return {
                    "is_resume": False
                }

            print("\n\n--- Detailed Section Analysis ---\n")
            # We can analyze a few key sections
            sections_to_analyze = ['skills', 'experience', 'achievements', 'education']
            
            for section_name in sections_to_analyze:
                if section_name in extracted_data and extracted_data[section_name]:
                    # print(f"----- Analyzing '{section_name.capitalize()}' Section -----")
                    section_content = extracted_data[section_name]
                    detailed_analysis = get_section_analysis(section_name, section_content, llm)
                    analysis[section_name] = {}
                    if detailed_analysis:
                        # print("\n[+] What's Good:")
                        # print(detailed_analysis.get('good', 'N/A'))
                        analysis[section_name]["good"] = detailed_analysis.get('good', 'N/A')
                        # print("\n[-] What's Wrong:")
                        # print(detailed_analysis.get('wrong', 'N/A'))
                        analysis[section_name]["wrong"] = detailed_analysis.get('wrong', 'N/A')
                        # print("\n[*] What to Add/Improve:")
                        # print(detailed_analysis.get('improvement', 'N/A'))
                        analysis[section_name]["improvement"] = detailed_analysis.get('improvement', 'N/A')
                    else:
                        print("-" * 40 + "\n")
                else:
                    print(f"----- Section '{section_name.capitalize()}' not found or is empty. Skipping analysis. -----\n")
    return analysis

from openai import OpenAI
import fitz  # PyMuPDF
import os
import time
from tenacity import retry, wait_random_exponential, stop_after_attempt, retry_if_exception_type
from openai import RateLimitError, APIError

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@retry(
    wait=wait_random_exponential(min=1, max=10),
    stop=stop_after_attempt(3),
    retry=retry_if_exception_type((RateLimitError, APIError))
)
def ask_openai(prompt):
    """Handles OpenAI API request with retry on errors."""
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
    return response.choices[0].message.content

def extract_text(pdf_path):
    """Extracts full text from a PDF using PyMuPDF."""
    doc = fitz.open(pdf_path)
    return "\n".join(page.get_text() for page in doc)

def chunk_text(text, max_tokens=3000):
    """Splits long audit text into manageable chunks."""
    paragraphs = text.split("\n\n")
    chunks, current_chunk = [], []
    current_len = 0
    for para in paragraphs:
        current_len += len(para)
        current_chunk.append(para)
        if current_len >= max_tokens:
            chunks.append("\n\n".join(current_chunk))
            current_chunk, current_len = [], 0
    if current_chunk:
        chunks.append("\n\n".join(current_chunk))
    return chunks

def summarize_audit(text):
    """Summarizes audit text using chunked analysis."""
    chunks = chunk_text(text)
    partial_summaries = []
    for chunk in chunks:
        prompt = (
            "You are an auditor. Analyze the following part of an audit report and summarize:\n"
            "- Key Findings\n"
            "- Measures Taken\n"
            "- Key Issues\n"
            "- Notable Outcomes\n\n"
            f"Report:\n{chunk}\n\n"
            "Return a clear summary."
        )
        partial_summaries.append(ask_openai(prompt))
    return "\n\n".join(partial_summaries)

def compare_audits(summaries):
    """Uses OpenAI to compare multiple audit summaries."""
    joined = "\n\n".join(f"Audit {i+1}:\n{summary}" for i, summary in enumerate(summaries))
    prompt = (
        "You are a senior auditor. Compare the following summaries:\n\n"
        f"{joined}\n\n"
        "Highlight:\n"
        "- Similarities\n"
        "- Differences\n"
        "- Common problems and solutions\n\n"
        "Return a clear, structured comparison."
    )
    return ask_openai(prompt)

def extract_learnings(summaries):
    """Extracts lessons and recommendations from audit summaries."""
    joined = "\n\n".join(summaries)
    prompt = (
        "From the following audit summaries, extract 3–5 key learnings or best practices "
        "that could improve future audits:\n\n"
        f"{joined}"
    )
    return ask_openai(prompt)

def analyze_audits(paths):
    """Main interface for the app: returns all outputs and exportable text."""
    summaries = []
    for path in paths:
        text = extract_text(path)
        summaries.append(summarize_audit(text))

    comparison = compare_audits(summaries)
    learnings = extract_learnings(summaries)

    full_text = "=== AUDIT SUMMARIES ===\n\n" + "\n\n".join(summaries)
    full_text += "\n\n=== COMPARISON ===\n\n" + comparison
    full_text += "\n\n=== LEARNINGS ===\n\n" + learnings

    return summaries, comparison, learnings, full_text

import streamlit as st
from rag_processor import process_queries
import os
import time
from pdf_processor import convert_pdf_to_text
from ollama_processor import OllamaProcessor
import tempfile

def get_demo_queries():
    """Returns a list of demo queries about AI."""
    return [
        "who is this contract from?",
        "what are the contact details of company?",
        "what are the clauses?",
        "overall summary"
    ]

def process_single_pdf(pdf_file, placeholder):
    # Create a temporary file to save the uploaded PDF
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
        tmp_file.write(pdf_file.getvalue())
        tmp_path = tmp_file.name

    # Convert PDF to text
    placeholder.text("Converting PDF to text...")
    text_content = convert_pdf_to_text(tmp_path)
    
    # Get queries
    queries = get_demo_queries()
    placeholder.text("Processing queries...")
    
    # Process queries and get answers
    start_time = time.time()
    results = process_queries(text_content, queries)
    end_time = time.time()
    processing_time = end_time - start_time
    
    # Initialize Ollama processor and generate bid evaluation
    placeholder.text("Generating evaluation report...")
    ollama = OllamaProcessor()
    evaluation_report = ollama.evaluate_bid(list(zip(queries, results)))
    
    # Clean up temporary file
    os.unlink(tmp_path)
    
    # Clear the placeholder
    placeholder.empty()
    
    return {
        'processing_time': processing_time,
        'queries': queries,
        'results': results,
        'evaluation_report': evaluation_report
    }

def main():
    st.set_page_config(page_title="Bid Analyzer", layout="wide")
    
    st.title("Bid Analyzer & Evaluator")
    st.write("Upload one or more PDF files to analyze contracts and generate evaluation reports.")
    
    # File uploader
    uploaded_files = st.file_uploader("Choose PDF files", type="pdf", accept_multiple_files=True)
    
    if uploaded_files:
        # Process all PDFs first
        all_results = []
        progress_container = st.container()
        
        with progress_container:
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for i, pdf_file in enumerate(uploaded_files):
                status_text.text(f"Processing {pdf_file.name}...")
                process_log = st.empty()  # Temporary placeholder for processing logs
                results = process_single_pdf(pdf_file, process_log)
                all_results.append((pdf_file.name, results))
                progress_bar.progress((i + 1) / len(uploaded_files))
        
        # Clear all processing indicators
        progress_container.empty()
        
        # Display results in two sections
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("Detailed Analysis")
            for file_name, results in all_results:
                with st.expander(f"📄 {file_name} - Details", expanded=False):
                    st.info(f"Processing completed in {results['processing_time']:.2f} seconds")
                    
                    # Display Q&A results
                    for query, answer in zip(results['queries'], results['results']):
                        st.markdown(f"**{query}**")
                        st.write(answer)
                        st.divider()
        
        with col2:
            st.subheader("Evaluation Reports")
            for file_name, results in all_results:
                with st.expander(f"📊 {file_name} - Evaluation Report", expanded=False):
                    st.markdown(results['evaluation_report'])

if __name__ == "__main__":
    main()
import streamlit as st
from ui import BidAnalyzerUI
from rag_processor import process_queries
from pdf_processor import convert_pdf_to_text
from ollama_processor import OllamaProcessor
from state_manager import StateManager
import tempfile
import os
import time

def get_demo_queries():
    """Returns a list of demo queries about the bid document."""
    return [
        "who issued this bid document and when?",
        "what are the product specifications required?",
        "what are the quantity and pricing details?",
        "what are the delivery and payment terms?",
        "what are the bid submission requirements and deadline?",
        "give me an overall summary of this bid document"
    ]

def process_single_pdf(pdf_file, ui_instance, state_manager):
    """Process a single PDF file and return results."""
    # Skip if already processed
    if state_manager.is_file_processed(pdf_file.name):
        return None

    # Create a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
        tmp_file.write(pdf_file.getvalue())
        tmp_path = tmp_file.name

    try:
        # Update processing state
        state_manager.update_processing_state(
            file_name=pdf_file.name,
            is_processing=True,
            status=f"Processing {pdf_file.name}..."
        )

        # Convert PDF to text
        ui_instance.update_progress(0.3, f"Converting {pdf_file.name} to text...")
        text_content = convert_pdf_to_text(tmp_path)
        
        # Get queries
        queries = get_demo_queries()
        ui_instance.update_progress(0.5, f"Processing queries for {pdf_file.name}...")
        
        # Process queries and get answers
        start_time = time.time()
        results = process_queries(text_content, queries)
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Generate evaluation report
        ui_instance.update_progress(0.8, f"Generating evaluation report for {pdf_file.name}...")
        ollama = OllamaProcessor()
        
        # Get tender context if available
        tender_context = st.session_state.get('tender_context')
        
        # Generate evaluation with tender context
        evaluation_report = ollama.evaluate_bid(
            list(zip(queries, results)),
            tender_context
        )
        
        # Store results
        result_data = {
            'processing_time': processing_time,
            'queries': queries,
            'results': results,
            'evaluation_report': evaluation_report
        }
        state_manager.store_result(pdf_file.name, result_data)
        
        return result_data

    except Exception as e:
        error_msg = f"Error processing {pdf_file.name}: {str(e)}"
        ui_instance.display_error(error_msg)
        return None

    finally:
        # Clean up temporary file
        try:
            os.unlink(tmp_path)
        except Exception as e:
            print(f"Error removing temporary file {tmp_path}: {str(e)}")
        
        # Remove from processing queue
        state_manager.remove_from_queue(pdf_file.name)

def main():
    # Initialize UI and state
    ui = BidAnalyzerUI()
    state_manager = StateManager()
    
    # Setup page
    ui.setup_page()
    
    # Get uploaded files from current tab
    uploaded_files = ui.render_current_tab()
    
    # Start processing if on upload tab and new files are uploaded
    if uploaded_files and st.session_state.current_tab == "Upload":
        new_files = [f for f in uploaded_files if not state_manager.is_file_processed(f.name)]
        if new_files and not state_manager.is_processing():
            state_manager.start_processing(new_files)
    
    # Continue processing if there are files in the queue
    if state_manager.is_processing():
        progress_container = ui.create_processing_container()
        
        for pdf_file in state_manager.get_processing_queue():
            ui.update_progress(0.0, f"Starting to process {pdf_file.name}...")
            process_single_pdf(pdf_file, ui, state_manager)
        
        # Clear progress indicators when done
        progress_container.empty()
        
        # Switch to Analysis tab after processing is complete
        st.session_state.current_tab = "Analysis"
        st.rerun()

if __name__ == "__main__":
    main()
import PyPDF2
from pathlib import Path
import logging
from typing import Optional
import os

class PDFProcessor:
    def __init__(self):
        """Initialize the PDF processor with logging configuration."""
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def pdf_to_text(self, pdf_path: str, output_path: Optional[str] = None) -> str:
        """
        Convert a PDF file to text and optionally save it to a file.
        
        Args:
            pdf_path (str): Path to the input PDF file
            output_path (str, optional): Path to save the output text file. 
                                       If None, creates a text file with the same name as PDF
        
        Returns:
            str: Path to the created text file
        
        Raises:
            FileNotFoundError: If the PDF file doesn't exist
            Exception: For other processing errors
        """
        try:
            # Convert paths to Path objects for better handling
            pdf_path = Path(pdf_path)
            
            # Check if PDF exists
            if not pdf_path.exists():
                raise FileNotFoundError(f"PDF file not found: {pdf_path}")
            
            # Generate output path if not provided
            if output_path is None:
                output_path = pdf_path.with_suffix('.txt')
            else:
                output_path = Path(output_path)
            
            self.logger.info(f"Processing PDF: {pdf_path}")
            
            # Read PDF
            extracted_text = []
            with open(pdf_path, 'rb') as file:
                # Create PDF reader object
                pdf_reader = PyPDF2.PdfReader(file)
                
                # Get number of pages
                num_pages = len(pdf_reader.pages)
                self.logger.info(f"Number of pages: {num_pages}")
                
                # Extract text from each page
                for page_num in range(num_pages):
                    page = pdf_reader.pages[page_num]
                    text = page.extract_text()
                    extracted_text.append(text)
                    
                    # Log progress for large documents
                    if (page_num + 1) % 10 == 0:
                        self.logger.info(f"Processed {page_num + 1} pages...")
            
            # Combine all text
            full_text = "\n".join(extracted_text)
            
            # Save to text file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(full_text)
            
            self.logger.info(f"Successfully created text file: {output_path}")
            return str(output_path)
            
        except FileNotFoundError as e:
            self.logger.error(f"File not found error: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Error processing PDF: {e}")
            raise

def convert_pdf_to_text(pdf_path: str, output_path: Optional[str] = None) -> str:
    """
    Convenience function to convert PDF to text without creating a class instance.
    
    Args:
        pdf_path (str): Path to the input PDF file
        output_path (str, optional): Path to save the output text file
    
    Returns:
        str: Path to the created text file
    """
    processor = PDFProcessor()
    return processor.pdf_to_text(pdf_path, output_path)

# Example usage
if __name__ == "__main__":
    try:
        # Example with direct function
        pdf_file = "example.pdf"
        text_file = convert_pdf_to_text(pdf_file)
        print(f"Created text file: {text_file}")
        
        # Example with class
        processor = PDFProcessor()
        text_file2 = processor.pdf_to_text(
            "another_example.pdf",
            "custom_output.txt"
        )
        print(f"Created text file: {text_file2}")
        
    except Exception as e:
        print(f"Error: {e}")
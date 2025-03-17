import os
import pymupdf

def extract_text_from_pdf(pdf_file, output_dir=None):
    """
    Extract text from a PDF file using PyMuPDF.
    
    Args:
        pdf_file: File-like object or path to PDF
        output_dir (str, optional): Directory to save text file. If None, text is only returned.
        
    Returns:
        str: Extracted text content
    """
    try:
        # Open the PDF file - works with path string or file-like object
        doc = pymupdf.open(pdf_file)
        
        # Initialize text content
        full_text = ""
        
        # Extract text from each page
        for page_num, page in enumerate(doc):
            page_text = page.get_text()
            full_text += f"\n\n----- Page {page_num + 1} -----\n\n"
            full_text += page_text
        
        # Save to file if output directory is specified
        if output_dir:
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            text_output_path = os.path.join(output_dir, "extracted_text.txt")
            with open(text_output_path, "w", encoding="utf-8") as text_out:
                text_out.write(full_text)
        
        # Close the document
        doc.close()
        
        return full_text
        
    except Exception as e:
        return f"Error extracting text: {str(e)}"

def extract_images_from_pdf(pdf_file, output_dir):
    """
    Extract images from a PDF file using PyMuPDF.
    
    Args:
        pdf_file: File-like object or path to PDF
        output_dir (str): Directory to save extracted images
        
    Returns:
        list: Paths to extracted images
    """
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    image_paths = []
    
    try:
        # Open the PDF file
        doc = pymupdf.open(pdf_file)
        
        # Extract images from each page
        for page_num in range(len(doc)):
            page = doc[page_num]
            image_list = page.get_images()
            
            for img_num, img in enumerate(image_list, start=1):
                xref = img[0]  # Get the XREF of the image
                
                try:
                    pix = pymupdf.Pixmap(doc, xref)
                    
                    # Convert CMYK to RGB if needed
                    if pix.n - pix.alpha > 3:
                        pix = pymupdf.Pixmap(pymupdf.csRGB, pix)
                    
                    # Save the image
                    img_filename = f"page_{page_num + 1}-image_{img_num}.png"
                    img_path = os.path.join(output_dir, img_filename)
                    pix.save(img_path)
                    image_paths.append(img_path)
                    
                    # Clean up pixmap
                    pix = None
                    
                except Exception as e:
                    continue  # Skip images that can't be extracted
        
        # Close the document
        doc.close()
        
        return image_paths
        
    except Exception as e:
        return f"Error extracting images: {str(e)}"

def extract_text_and_images(pdf_file, output_dir=None):
    """
    Extract both text and images from a PDF file.
    
    Args:
        pdf_file: File-like object or path to PDF
        output_dir (str, optional): Directory to save extracted content
        
    Returns:
        tuple: (extracted_text, list_of_image_paths)
    """
    # If output directory is specified, create it
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Extract text
    text_content = extract_text_from_pdf(pdf_file, output_dir)
    
    # Extract images if output directory is specified
    image_paths = []
    if output_dir:
        image_paths = extract_images_from_pdf(pdf_file, output_dir)
    
    return text_content, image_paths

def ocr_pdf_page(pdf_file, page_num=0):
    """
    Use OCR on a specific page of a PDF.
    Useful for image-based PDFs without embedded text.
    
    Args:
        pdf_file: File-like object or path to PDF
        page_num (int): Page number to OCR (0-based index)
        
    Returns:
        str: OCR extracted text
    """
    try:
        doc = pymupdf.open(pdf_file)
        
        if page_num >= len(doc):
            return "Error: Page number exceeds document length"
        
        page = doc[page_num]
        tp = page.get_textpage_ocr()
        text = page.get_text(textpage=tp)
        
        doc.close()
        return text
        
    except Exception as e:
        return f"OCR error: {str(e)}"

extract_text_and_images("/workspaces/ollama_dsr1_seervice/user_pdf/2312.10997v5.pdf","/workspaces/ollama_dsr1_seervice/user_pdf")
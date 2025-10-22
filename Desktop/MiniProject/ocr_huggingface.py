"""
Alternative OCR using HuggingFace TrOCR model
Install: pip install transformers torch easyocr
"""

from transformers import TrOCRProcessor, VisionEncoderDecoderModel
from PIL import Image
import torch
import easyocr
import json
import re

class HuggingFaceOCR:
    def __init__(self, use_gpu=False):
        """Initialize HuggingFace OCR models"""
        self.device = "cuda" if use_gpu and torch.cuda.is_available() else "cpu"
        
        # Option 1: Use EasyOCR (simpler, good for printed text)
        self.reader = easyocr.Reader(['en'], gpu=use_gpu)
        
        # Option 2: TrOCR (better for handwritten text - uncomment if needed)
        # self.processor = TrOCRProcessor.from_pretrained('microsoft/trocr-large-printed')
        # self.model = VisionEncoderDecoderModel.from_pretrained('microsoft/trocr-large-printed')
        # self.model.to(self.device)
    
    def extract_text_easyocr(self, image_path):
        """Extract text using EasyOCR"""
        try:
            result = self.reader.readtext(image_path)
            
            # Combine all detected text
            extracted_lines = []
            for detection in result:
                text = detection[1]
                confidence = detection[2]
                if confidence > 0.3:  # Filter low confidence
                    extracted_lines.append(text)
            
            return '\n'.join(extracted_lines)
        except Exception as e:
            return f"Error: {str(e)}"
    
    def extract_text_trocr(self, image_path):
        """Extract text using TrOCR (better for handwriting)"""
        try:
            image = Image.open(image_path).convert("RGB")
            
            # Split image into regions if needed
            pixel_values = self.processor(image, return_tensors="pt").pixel_values
            pixel_values = pixel_values.to(self.device)
            
            generated_ids = self.model.generate(pixel_values)
            generated_text = self.processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
            
            return generated_text
        except Exception as e:
            return f"Error: {str(e)}"
    
    def parse_prescription(self, raw_text):
        """Parse extracted text using regex patterns"""
        medicines = []
        
        lines = raw_text.split('\n')
        current_medicine = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Detect medicine name (usually starts with Tab/Cap/Syrup)
            if re.search(r'\b(tab|cap|syrup|syr|inj|tablet|capsule)\b', line, re.IGNORECASE):
                if current_medicine:
                    medicines.append(current_medicine)
                
                current_medicine = {
                    'medicine_name': line,
                    'dosage': 'Not specified',
                    'frequency': 'Not specified',
                    'duration': 'Not specified',
                    'instructions': ''
                }
            
            # Extract dosage
            dosage_match = re.search(r'(\d+\.?\d*)\s*(mg|ml|g|mcg|iu|tablet|tab)', line, re.IGNORECASE)
            if dosage_match and current_medicine:
                current_medicine['dosage'] = dosage_match.group(0)
            
            # Extract frequency
            freq_patterns = [
                r'\b(once|twice|thrice|1|2|3|4)\s*(daily|a day|per day|times)\b',
                r'\b(od|bd|tds|tid|qid)\b',
                r'\b(morning|afternoon|evening|night)\b'
            ]
            for pattern in freq_patterns:
                freq_match = re.search(pattern, line, re.IGNORECASE)
                if freq_match and current_medicine:
                    current_medicine['frequency'] = freq_match.group(0)
                    break
            
            # Extract duration
            duration_match = re.search(r'(\d+)\s*(day|week|month|year)s?', line, re.IGNORECASE)
            if duration_match and current_medicine:
                current_medicine['duration'] = duration_match.group(0)
            
            # Extract instructions
            instruction_keywords = ['before', 'after', 'with', 'empty stomach', 'food', 'water', 'meal']
            if any(keyword in line.lower() for keyword in instruction_keywords) and current_medicine:
                current_medicine['instructions'] = line
        
        # Add last medicine
        if current_medicine:
            medicines.append(current_medicine)
        
        return {'medicines': medicines if medicines else [self._create_default_entry(raw_text)]}
    
    def _create_default_entry(self, raw_text):
        """Create default entry when parsing fails"""
        return {
            'medicine_name': 'Could not parse automatically',
            'dosage': 'See original text',
            'frequency': 'See original text',
            'duration': 'See original text',
            'instructions': raw_text[:300]
        }
    
    def process_prescription(self, image_path):
        """Complete processing pipeline"""
        # Extract text using EasyOCR
        raw_text = self.extract_text_easyocr(image_path)
        
        # Parse into structured format
        structured_data = self.parse_prescription(raw_text)
        
        return raw_text, structured_data


# Usage in app.py:
# from ocr_huggingface import HuggingFaceOCR
# ocr = HuggingFaceOCR(use_gpu=False)
# raw_text, structured_data = ocr.process_prescription(image_path)
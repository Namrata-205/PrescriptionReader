import google.generativeai as genai
import os
from PIL import Image
import json
import re

from dotenv import load_dotenv
load_dotenv()

api_key=os.getenv("GEMINI_API_KEY")

class PrescriptionOCR:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("Gemini API key not found. Set GEMINI_API_KEY environment variable.")
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')

    def preprocess_image(self, image_path):
        """Preprocess image for better OCR"""
        try:
            img = Image.open(image_path)
            
            # Convert to RGB if needed
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Resize if too large (max 4096 pixels)
            max_size = 4096
            if max(img.size) > max_size:
                ratio = max_size / max(img.size)
                new_size = tuple(int(dim * ratio) for dim in img.size)
                img = img.resize(new_size, Image.Resampling.LANCZOS)
            
            return img
        except Exception as e:
            print(f"Error preprocessing image: {str(e)}")
            return Image.open(image_path)
    
    def extract_text(self, image_path):
        """Extract text from prescription image using enhanced Gemini Vision"""
        try:
            img = self.preprocess_image(image_path)
            
            # Enhanced prompt with specific instructions
            prompt = """
            You are an expert medical prescription reader. Analyze this prescription image carefully and extract ALL text visible.

            IMPORTANT INSTRUCTIONS:
            1. Read EVERY word, number, and symbol visible in the image
            2. Pay special attention to:
               - Medicine/Drug names (generic and brand names)
               - Dosage amounts (mg, ml, tablets, etc.)
               - Frequency (times per day, morning/evening, etc.)
               - Duration (days, weeks, months)
               - Doctor's instructions or notes
               - Any handwritten text
            3. Preserve the original format and order
            4. If text is unclear, make your best educated guess and mark it with [unclear: your_guess]
            5. Include ALL sections: patient info, medicines, dosage, frequency, duration, instructions
            
            Extract the complete text now:
            """
            
            # Generate with higher temperature for better recognition
            response = self.model.generate_content(
                [prompt, img],
                generation_config=genai.types.GenerationConfig(
                    temperature=0.4,
                    top_p=0.95,
                    top_k=40,
                    max_output_tokens=2048,
                )
            )
            
            extracted_text = response.text.strip()
            
            # Clean up the text
            extracted_text = self._clean_extracted_text(extracted_text)
            
            return extracted_text
            
        except Exception as e:
            return f"Error extracting text: {str(e)}"
    
    def _clean_extracted_text(self, text):
        """Clean and normalize extracted text"""
        # Remove excessive whitespace
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = re.sub(r' +', ' ', text)
        return text.strip()
    
    def parse_prescription(self, raw_text):
        """Parse raw text into structured JSON with enhanced accuracy"""
        try:
            # Multi-step parsing for better accuracy
            prompt = f"""
            You are a medical prescription parser. Parse the following prescription text into a structured JSON format.

            CRITICAL RULES:
            1. Extract EVERY medicine mentioned in the prescription
            2. For each medicine, find:
               - medicine_name: Full name (generic or brand)
               - dosage: Amount per dose (e.g., "500mg", "10ml", "1 tablet")
               - frequency: How often to take (e.g., "twice daily", "3 times a day", "every 8 hours", "morning and night")
               - duration: How long to continue (e.g., "7 days", "2 weeks", "1 month", "until finished")
               - instructions: Special notes (e.g., "after food", "before meals", "with water", "at bedtime")
            
            3. If any field is not found, use "Not specified" instead of leaving it empty
            4. Be thorough - don't skip any medicines
            5. Common medicine patterns to look for:
               - Tab (Tablet), Cap (Capsule), Syr (Syrup), Inj (Injection)
               - Dosage: numbers followed by mg, ml, g, mcg, IU, etc.
               - Frequency: OD (once daily), BD (twice daily), TDS/TID (three times), QID (four times)
               - Timing: morning, afternoon, evening, night, before/after meals
            
            Return ONLY valid JSON in this EXACT format (no extra text):
            {{
                "medicines": [
                    {{
                        "medicine_name": "Medicine Name Here",
                        "dosage": "dose amount",
                        "frequency": "frequency details",
                        "duration": "duration period",
                        "instructions": "special instructions"
                    }}
                ]
            }}

            Prescription text to parse:
            {raw_text}

            JSON output:
            """
            
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.2,  # Lower temperature for more structured output
                    top_p=0.8,
                    max_output_tokens=2048,
                )
            )
            
            result_text = response.text.strip()
            
            # Extract JSON from response
            structured_data = self._extract_json(result_text)
            
            # Validate and clean the data
            structured_data = self._validate_structured_data(structured_data)
            
            return structured_data
            
        except Exception as e:
            print(f"Error parsing prescription: {str(e)}")
            # Return fallback structure
            return self._create_fallback_structure(raw_text)
    
    def _extract_json(self, text):
        """Extract JSON from various response formats"""
        # Try to find JSON in markdown code blocks
        json_patterns = [
            r'```json\s*(\{.*?\})\s*```',
            r'```\s*(\{.*?\})\s*```',
            r'(\{.*\})'
        ]
        
        for pattern in json_patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1))
                except:
                    continue
        
        # Try parsing the entire text
        try:
            return json.loads(text)
        except:
            raise ValueError("Could not extract valid JSON from response")
    
    def _validate_structured_data(self, data):
        """Validate and clean structured data"""
        if not isinstance(data, dict) or 'medicines' not in data:
            raise ValueError("Invalid data structure")
        
        medicines = data.get('medicines', [])
        cleaned_medicines = []
        
        for med in medicines:
            # Ensure all required fields exist
            cleaned_med = {
                'medicine_name': med.get('medicine_name', 'Unknown Medicine'),
                'dosage': med.get('dosage', 'Not specified'),
                'frequency': med.get('frequency', 'Not specified'),
                'duration': med.get('duration', 'Not specified'),
                'instructions': med.get('instructions', 'No special instructions')
            }
            
            # Skip if medicine name is too generic or empty
            if cleaned_med['medicine_name'] not in ['Unknown Medicine', 'N/A', '']:
                cleaned_medicines.append(cleaned_med)
        
        return {'medicines': cleaned_medicines}
    
    def _create_fallback_structure(self, raw_text):
        """Create fallback structure when parsing fails"""
        # Try to extract medicine names using pattern matching
        lines = raw_text.split('\n')
        medicines = []
        
        # Common medicine patterns
        medicine_keywords = ['tab', 'cap', 'syrup', 'syr', 'injection', 'inj', 'tablet', 'capsule']
        
        for line in lines:
            line_lower = line.lower()
            # Check if line likely contains medicine info
            if any(keyword in line_lower for keyword in medicine_keywords) or re.search(r'\d+\s*mg|ml|g', line_lower):
                medicines.append({
                    'medicine_name': line.strip(),
                    'dosage': 'Please refer to prescription',
                    'frequency': 'Please refer to prescription',
                    'duration': 'Please refer to prescription',
                    'instructions': 'Please refer to original prescription'
                })
        
        if not medicines:
            medicines.append({
                'medicine_name': 'Unable to parse automatically',
                'dosage': 'Please consult doctor',
                'frequency': 'Please consult doctor',
                'duration': 'Please consult doctor',
                'instructions': 'Original text: ' + raw_text[:200]
            })
        
        return {'medicines': medicines}
    
    def process_prescription(self, image_path):
        """Complete pipeline: extract and parse with retries"""
        try:
            # Step 1: Extract text
            print("Extracting text from prescription...")
            raw_text = self.extract_text(image_path)
            
            if "Error" in raw_text:
                return raw_text, self._create_fallback_structure(raw_text)
            
            print(f"Extracted text length: {len(raw_text)} characters")
            
            # Step 2: Parse into structured format
            print("Parsing prescription into structured format...")
            structured_data = self.parse_prescription(raw_text)
            
            print(f"Found {len(structured_data.get('medicines', []))} medicines")
            
            return raw_text, structured_data
            
        except Exception as e:
            error_msg = f"Error processing prescription: {str(e)}"
            return error_msg, self._create_fallback_structure(error_msg)
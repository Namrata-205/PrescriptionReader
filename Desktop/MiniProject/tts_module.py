from gtts import gTTS
import os
import base64

class TextToSpeech:
    def __init__(self, language='en'):
        self.language = language
        self.audio_dir = "audio_files"
        if not os.path.exists(self.audio_dir):
            os.makedirs(self.audio_dir)
    
    def create_audio(self, text, filename="output.mp3"):
        """Convert text to speech and save as audio file"""
        try:
            filepath = os.path.join(self.audio_dir, filename)
            tts = gTTS(text=text, lang=self.language, slow=False)
            tts.save(filepath)
            return filepath
        except Exception as e:
            print(f"Error creating audio: {str(e)}")
            return None
    
    def get_audio_base64(self, filepath):
        """Get base64 encoded audio for Streamlit playback"""
        try:
            with open(filepath, "rb") as audio_file:
                audio_bytes = audio_file.read()
            return base64.b64encode(audio_bytes).decode()
        except Exception as e:
            print(f"Error encoding audio: {str(e)}")
            return None
    
    def generate_prescription_audio(self, structured_data, filename="prescription.mp3"):
        """Generate audio from structured prescription data"""
        medicines = structured_data.get('medicines', [])
        
        if not medicines:
            text = "No medicines found in the prescription."
        else:
            text_parts = ["Here is your prescription information."]
            
            for i, med in enumerate(medicines, 1):
                med_text = f"Medicine {i}: {med.get('medicine_name', 'Unknown')}. "
                
                if med.get('dosage'):
                    med_text += f"Dosage: {med['dosage']}. "
                
                if med.get('frequency'):
                    med_text += f"Take {med['frequency']}. "
                
                if med.get('duration'):
                    med_text += f"Continue for {med['duration']}. "
                
                if med.get('instructions'):
                    med_text += f"Special instructions: {med['instructions']}. "
                
                text_parts.append(med_text)
            
            text = " ".join(text_parts)
        
        filepath = self.create_audio(text, filename)
        return filepath, text
    
    def generate_medicine_audio(self, medicine_data, index, filename=None):
        """Generate audio for a single medicine"""
        if filename is None:
            filename = f"medicine_{index}.mp3"
        
        med_text = f"Medicine {index}: {medicine_data.get('medicine_name', 'Unknown')}. "
        
        if medicine_data.get('dosage'):
            med_text += f"Dosage: {medicine_data['dosage']}. "
        
        if medicine_data.get('frequency'):
            med_text += f"Take {medicine_data['frequency']}. "
        
        if medicine_data.get('duration'):
            med_text += f"Continue for {medicine_data['duration']}. "
        
        if medicine_data.get('instructions'):
            med_text += f"Special instructions: {medicine_data['instructions']}. "
        
        filepath = self.create_audio(med_text, filename)
        return filepath, med_text
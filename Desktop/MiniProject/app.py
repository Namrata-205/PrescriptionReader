import streamlit as st
from PIL import Image
import os
from datetime import datetime
import json

# Import custom modules
from db import Database
from ocr_module import PrescriptionOCR
from tts_module import TextToSpeech
from stt_module import render_voice_component, process_voice_command

# Page configuration
st.set_page_config(
    page_title="Voice-Assisted Prescription Reader",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'username' not in st.session_state:
    st.session_state.username = None
if 'current_prescription' not in st.session_state:
    st.session_state.current_prescription = None
if 'current_medicine_index' not in st.session_state:
    st.session_state.current_medicine_index = 0
if 'audio_playing' not in st.session_state:
    st.session_state.audio_playing = False

# Initialize database
db = Database()

# Initialize TTS
tts = TextToSpeech()

# Create uploads directory
if not os.path.exists("uploads"):
    os.makedirs("uploads")

def login_page():
    """Display login/signup page"""
    st.title("💊 Voice-Assisted Prescription Reader")
    st.subheader("For the Visually Impaired")
    
    tab1, tab2 = st.tabs(["Login", "Sign Up"])
    
    with tab1:
        st.subheader("Login to Your Account")
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login")
            
            if submit:
                if username and password:
                    success, user_id = db.authenticate_user(username, password)
                    if success:
                        st.session_state.authenticated = True
                        st.session_state.user_id = user_id
                        st.session_state.username = username
                        st.success("Login successful!")
                        st.rerun()
                    else:
                        st.error("Invalid username or password")
                else:
                    st.warning("Please enter both username and password")
    
    with tab2:
        st.subheader("Create New Account")
        with st.form("signup_form"):
            new_username = st.text_input("Choose Username")
            new_email = st.text_input("Email Address")
            new_password = st.text_input("Choose Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            submit_signup = st.form_submit_button("Sign Up")
            
            if submit_signup:
                if new_username and new_email and new_password and confirm_password:
                    if new_password != confirm_password:
                        st.error("Passwords do not match")
                    elif len(new_password) < 6:
                        st.error("Password must be at least 6 characters")
                    else:
                        success, user_id = db.create_user(new_username, new_email, new_password)
                        if success:
                            st.success("Account created successfully! Please login.")
                        else:
                            st.error("Username or email already exists")
                else:
                    st.warning("Please fill in all fields")

def main_app():
    """Main application after authentication"""
    
    # Sidebar
    with st.sidebar:
        st.title(f"Welcome, {st.session_state.username}!")
        
        if st.button("Logout", type="primary"):
            st.session_state.authenticated = False
            st.session_state.user_id = None
            st.session_state.username = None
            st.session_state.current_prescription = None
            st.rerun()
        
        st.divider()
        
        # Navigation
        page = st.radio(
            "Navigation",
            ["Upload New Prescription", "My Prescriptions"],
            label_visibility="collapsed"
        )
    
    if page == "Upload New Prescription":
        upload_prescription_page()
    else:
        view_prescriptions_page()

def upload_prescription_page():
    """Page for uploading and processing prescriptions"""
    st.title("📤 Upload New Prescription")
    st.write("Upload a prescription image to extract and read medicine information")
    
    # File uploader
    uploaded_file = st.file_uploader(
        "Choose a prescription image",
        type=['png', 'jpg', 'jpeg'],
        help="Upload a clear image of your prescription"
    )
    
    if uploaded_file is not None:
        # Display uploaded image
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("Uploaded Prescription")
            image = Image.open(uploaded_file)
            st.image(image, use_container_width=True)
        
        # Save uploaded file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{st.session_state.username}_{timestamp}.png"
        filepath = os.path.join("uploads", filename)
        image.save(filepath)
        
        # Process button
        if st.button("🔍 Extract Prescription Information", type="primary"):
            with st.spinner("Processing prescription..."):
                try:
                    # Initialize OCR
                    ocr = PrescriptionOCR()
                    
                    # Extract and parse
                    raw_text, structured_data = ocr.process_prescription(filepath)
                    
                    # Save to database
                    prescription_id = db.save_prescription(
                        st.session_state.user_id,
                        filepath,
                        raw_text,
                        structured_data
                    )
                    
                    # Store in session state
                    st.session_state.current_prescription = {
                        'id': prescription_id,
                        'structured_data': structured_data,
                        'raw_text': raw_text
                    }
                    st.session_state.current_medicine_index = 0
                    
                    st.success("Prescription processed successfully!")
                    
                except Exception as e:
                    st.error(f"Error processing prescription: {str(e)}")
                    st.info("Make sure you have set the GEMINI_API_KEY environment variable")
    
    # Display extracted information
    if st.session_state.current_prescription:
        st.divider()
        display_prescription_info(st.session_state.current_prescription)

def display_prescription_info(prescription):
    """Display extracted prescription information with audio"""
    st.subheader("📋 Extracted Prescription Information")
    
    structured_data = prescription['structured_data']
    medicines = structured_data.get('medicines', [])
    
    if not medicines:
        st.warning("No medicines found in the prescription")
        return
    
    # Display medicines in table
    st.write(f"**Total Medicines:** {len(medicines)}")
    
    for i, med in enumerate(medicines, 1):
        with st.expander(f"💊 Medicine {i}: {med.get('medicine_name', 'Unknown')}", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Dosage:** {med.get('dosage', 'N/A')}")
                st.write(f"**Frequency:** {med.get('frequency', 'N/A')}")
            
            with col2:
                st.write(f"**Duration:** {med.get('duration', 'N/A')}")
                st.write(f"**Instructions:** {med.get('instructions', 'N/A')}")
    
    st.divider()
    
    # Audio controls
    st.subheader("🔊 Audio Playback")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("▶️ Play All Medicines", use_container_width=True):
            audio_path, text = tts.generate_prescription_audio(structured_data)
            if audio_path:
                st.audio(audio_path)
                st.success("Playing all medicines")
    
    with col2:
        if st.button("▶️ Play Current Medicine", use_container_width=True):
            if st.session_state.current_medicine_index < len(medicines):
                med = medicines[st.session_state.current_medicine_index]
                audio_path, text = tts.generate_medicine_audio(
                    med, 
                    st.session_state.current_medicine_index + 1
                )
                if audio_path:
                    st.audio(audio_path)
                    st.info(f"Playing Medicine {st.session_state.current_medicine_index + 1}")
    
    with col3:
        if st.button("⏭️ Next Medicine", use_container_width=True):
            if st.session_state.current_medicine_index < len(medicines) - 1:
                st.session_state.current_medicine_index += 1
                st.success(f"Moved to Medicine {st.session_state.current_medicine_index + 1}")
                st.rerun()
            else:
                st.info("Already at the last medicine")
    
    # Voice commands section
    st.divider()
    st.subheader("🎤 Voice Commands (Optional)")
    st.info("Click the microphone button below and say: 'Read next', 'Repeat', or 'Stop'")
    
    # Render voice component
    render_voice_component()
    
    # Handle voice commands (would need JavaScript bridge in production)
    st.caption("Note: Voice commands require browser speech recognition support")

def view_prescriptions_page():
    """Page to view previous prescriptions"""
    st.title("📚 My Prescriptions")
    st.write("View your previously uploaded prescriptions")
    
    # Get user prescriptions
    prescriptions = db.get_user_prescriptions(st.session_state.user_id)
    
    if not prescriptions:
        st.info("No prescriptions uploaded yet. Upload your first prescription!")
        return
    
    # Display prescriptions
    for i, presc in enumerate(prescriptions):
        with st.expander(
            f"Prescription from {presc['upload_date']}", 
            expanded=(i == 0)
        ):
            col1, col2 = st.columns([1, 2])
            
            with col1:
                if os.path.exists(presc['image_path']):
                    st.image(presc['image_path'], use_container_width=True)
            
            with col2:
                st.subheader("Medicines")
                medicines = presc['structured_data'].get('medicines', [])
                
                for j, med in enumerate(medicines, 1):
                    st.write(f"**{j}. {med.get('medicine_name', 'Unknown')}**")
                    st.write(f"   - Dosage: {med.get('dosage', 'N/A')}")
                    st.write(f"   - Frequency: {med.get('frequency', 'N/A')}")
                    st.write(f"   - Duration: {med.get('duration', 'N/A')}")
                
                # Audio button for this prescription
                if st.button(f"🔊 Play Prescription", key=f"play_{presc['id']}"):
                    audio_path, text = tts.generate_prescription_audio(presc['structured_data'])
                    if audio_path:
                        st.audio(audio_path)

# Main execution
def main():
    """Main entry point"""
    if not st.session_state.authenticated:
        login_page()
    else:
        main_app()

if __name__ == "__main__":
    main()
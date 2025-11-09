from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth_router 
from app.models.user_model import Base 
from app.services.db_service import engine
from app.prescription_service import process_prescription
from app.routers import prescription_router
from app.prescription_service import 
from app.routers import settings_router # NEW
from app.models import settings_model # IMPORTANT: Need to import models for Base.metadata.create_all to find them
from app.models import medicine_model
import os

# ===== CHATBOT IMPORTS (ADD THESE) =====
import google.generativeai as genai
from pydantic import BaseModel
from typing import List, Optional
# ===== END CHATBOT IMPORTS =====

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Auth routes
app.include_router(auth_router.router)
app.include_router(prescription_router.router, prefix="/api") 
app.include_router(settings_router.router, prefix="/api") # NEW

# Create database tables 
Base.metadata.create_all(bind=engine) 

def read_root(): 
    return {"message": "Prescription Reader API is running"}
    
# ===== CHATBOT SETUP (ADD THIS) =====
# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Models
class ChatRequest(BaseModel):
    message: str
    medicines: List[dict]
    conversationHistory: List[dict] = []

class ChatResponse(BaseModel):
    success: bool
    response: str
    error: Optional[str] = None
# ===== END CHATBOT SETUP =====

def read_root(): 
    return {"message": "Prescription Reader API is running"}

# Prescription upload route
@app.post("/api/prescriptions/upload")
async def upload_prescription(file: UploadFile = File(...)):
    file_path = f"temp_{file.filename}"
    with open(file_path, "wb") as f:
        f.write(await file.read())
    try:
        result = process_prescription(file_path)  # call Gemini or OCR
    finally:
        os.remove(file_path)
    return result

# ===== CHATBOT ENDPOINT (ADD THIS) =====
@app.post("/api/chat", response_model=ChatResponse)
async def chat_with_assistant(request: ChatRequest):
    """Answer questions about medicines from prescription"""
    try:
        # Format medicines for context
        medicines_text = "USER'S MEDICINES FROM PRESCRIPTION:\n"
        for med in request.medicines:
            medicines_text += f"\n- {med.get('medicine_name', 'Unknown')}"
            medicines_text += f"\n  Dosage: {med.get('dosage', 'Not specified')}"
            medicines_text += f"\n  Frequency: {med.get('frequency', 'Not specified')}"
            if med.get('instructions'):
                medicines_text += f"\n  Instructions: {med.get('instructions')}"
        
        # Build conversation history
        conversation_context = ""
        if request.conversationHistory:
            for msg in request.conversationHistory[-4:]:
                role = "USER" if msg.get('role') == 'user' else "ASSISTANT"
                conversation_context += f"{role}: {msg.get('content', '')}\n"
        
        # System prompt
        system_prompt = f"""You are a helpful medicine assistant for visually impaired users.
Answer questions about medicines from prescriptions clearly and simply.

{medicines_text}

CONVERSATION HISTORY:
{conversation_context if conversation_context else "Start of conversation"}

GUIDELINES:
- Answer questions about medicines listed above ONLY
- Use simple, clear language
- If asked about medicine not in list, say "That medicine is not in your prescription"
- Always remind to consult doctor for medical concerns
- Be concise and helpful
- Never diagnose or change dosages
- If you don't know something, admit it"""

        # Call Gemini API
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(
            [system_prompt, f"\nUSER QUESTION: {request.message}"],
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=300,
                temperature=0.7,
            )
        )
        
        return ChatResponse(
            success=True,
            response=response.text.strip(),
            error=None
        )
    
    except Exception as e:
        print(f"Chat Error: {e}")
        return ChatResponse(
            success=False,
            response="",
            error=str(e)
        )
# ===== END CHATBOT ENDPOINT =====

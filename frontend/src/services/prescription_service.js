// src/services/prescription_service.js
// =========================================================
// Backend API Service for Prescription Upload + React UI
// =========================================================

import axios from "axios";
import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { Upload, ArrowLeft, Volume2, RotateCw, Check, Edit, Loader2 } from "lucide-react";
import { Progress } from "../components/ui/Progress";
import "../styles/theme.css";

// ===================== API SERVICE =====================
const API_BASE_URL = "http://127.0.0.1:8000/api";

/**
 * Upload a prescription image to the backend
 * @param {File|Blob} file - the uploaded image or blob
 * @returns {Promise<Object>} - returns { medicines: [...] }
 */
export const uploadPrescription = async (file) => {
  try {
    const formData = new FormData();
    formData.append("file", file);

    const response = await axios.post(`${API_BASE_URL}/prescriptions/upload`, formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });

    return response.data; // should contain { medicines: [...] }
  } catch (error) {
    console.error("Error uploading prescription:", error);
    throw error;
  }
};

// ===================== FRONTEND COMPONENT =====================

const UploadPrescription = () => {
  const navigate = useNavigate();
  const [uploadedImage, setUploadedImage] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [extractedMedicines, setExtractedMedicines] = useState([]);
  const [processingStep, setProcessingStep] = useState(0);

  const speakText = (text) => {
    if ("speechSynthesis" in window) {
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 0.9;
      utterance.pitch = 1;
      window.speechSynthesis.speak(utterance);
    }
  };

  const speakMedicine = (medicine) => {
    const text = `${medicine.medicine_name}, ${medicine.dosage}, ${medicine.frequency}.`;
    speakText(text);
  };

  const handleFileUpload = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => {
        setUploadedImage(reader.result);
        speakText("Image uploaded successfully. Click Process to extract prescription information.");
      };
      reader.readAsDataURL(file);
    }
  };

  const handleProcess = async () => {
    if (!uploadedImage) return;
    setIsProcessing(true);
    setProcessingStep(0);

    const stages = [
      "Preprocessing image...",
      "Running OCR...",
      "Extracting medicine names...",
      "Saving data...",
      "Complete!"
    ];

    for (let i = 0; i < stages.length; i++) {
      setProcessingStep((i + 1) * 20);
      speakText(stages[i]);
      await new Promise((resolve) => setTimeout(resolve, 500));
    }

    try {
      const blob = await fetch(uploadedImage).then(r => r.blob());
      const data = await uploadPrescription(blob);  // 🔗 Using shared API service
      setExtractedMedicines(data.structured_data?.medicines || []);
      speakText("Prescription processed successfully. Review the extracted medicines below.");
    } catch (error) {
      console.error(error);
      speakText("Error processing prescription. Please try again.");
    }

    setIsProcessing(false);
  };

  return (
    <div className="upload-page">
      <Button variant="outline" size="sm" className="back-btn" onClick={() => navigate("/dashboard")}>
        <ArrowLeft size={18} /> Back
      </Button>

      <h1 className="upload-title">Upload Prescription</h1>

      <main className="upload-main">
        {!uploadedImage && (
          <Card className="upload-card">
            <input type="file" accept="image/*" onChange={handleFileUpload} className="hidden" id="upload-file" />
            <label htmlFor="upload-file" className="upload-label">
              <Upload size={64} className="upload-icon" />
              <h3 className="upload-text">Upload File</h3>
              <p className="upload-desc">Select prescription image from your device</p>
            </label>
          </Card>
        )}

        {uploadedImage && !isProcessing && extractedMedicines.length === 0 && (
          <Card className="preview-card">
            <img src={uploadedImage} alt="Preview" className="preview-image" />
            <div className="preview-buttons">
              <Button variant="medical" size="lg" onClick={handleProcess}>
                <RotateCw size={18} /> Process
              </Button>
              <Button variant="outline" size="lg" onClick={() => setUploadedImage(null)}>Upload New</Button>
            </div>
          </Card>
        )}

        {isProcessing && (
          <Card className="processing-card">
            <Loader2 size={48} className="loader" />
            <h3>Processing...</h3>
            <Progress value={processingStep} className="progress-bar" />
            <p>{processingStep}% Complete</p>
          </Card>
        )}

        {extractedMedicines.length > 0 && (
          <div className="medicines-grid">
            {extractedMedicines.map((medicine, idx) => (
              <Card key={idx} className="medicine-card">
                <div>
                  <h4>{medicine.medicine_name}</h4>
                  <p><strong>Dosage:</strong> {medicine.dosage}</p>
                  <p><strong>Frequency:</strong> {medicine.frequency}</p>
                  <p><strong>Instructions:</strong> {medicine.instructions}</p>
                </div>
                <div className="medicine-actions">
                  <Button variant="outline" size="icon" onClick={() => speakMedicine(medicine)}>
                    <Volume2 size={18} />
                  </Button>
                  <Button variant="outline" size="icon"><Edit size={18} /></Button>
                  <Button variant="success" size="icon"><Check size={18} /></Button>
                </div>
              </Card>
            ))}
            <Button variant="medical" size="lg" className="save-btn">
              <Check size={18} /> Save All
            </Button>
          </div>
        )}
      </main>
    </div>
  );
};

export default UploadPrescription;

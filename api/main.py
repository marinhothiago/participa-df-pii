from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from src.detector import PIIDetector

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

detector = PIIDetector()

@app.post("/analyze")
async def analyze(data: dict):
    # Pega o texto e o ID (se não vier ID, usa None)
    text = data.get("text", "")
    request_id = data.get("id", None) 
    
    has_pii, findings, risco, confianca = detector.detect(text)
    
    return {
        "id": request_id, # Devolve o ID original aqui
        "classificacao": "NÃO PÚBLICO" if has_pii else "PÚBLICO",
        "risco": risco,
        "confianca": confianca,
        "detalhes": findings
    }
import os
import json
import google.generativeai as genai
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from dotenv import load_dotenv

# Importações locais dos nossos arquivos
from . import models, schemas
from .database import SessionLocal, create_db_and_tables

# Carrega as variáveis de ambiente (do arquivo .env na raiz)
load_dotenv()

# --- Configuração do Gemini ---
try:
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
    model = genai.GenerativeModel('gemini-1.5-flash')
    print("API do Gemini configurada com sucesso.")
except Exception as e:
    print(f"ERRO: Não foi possível configurar a API do Gemini. Verifique sua GOOGLE_API_KEY. Erro: {e}")
    model = None

# --- Configuração da API FastAPI ---
app = FastAPI(title="TDS Platform API")

# Middleware para permitir que o frontend acesse a API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Permite todas as origens
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Evento de inicialização: cria a tabela no banco quando a API sobe
@app.on_event("startup")
async def on_startup():
    await create_db_and_tables()
    print("Banco de dados conectado e tabelas criadas (se não existiam).")

# Dependência para obter uma sessão do banco de dados
async def get_db():
    async with SessionLocal() as db:
        yield db

# --- Endpoints da API ---

@app.get("/")
def read_root():
    return {"status": "API da TDS Platform no ar!", "database_connection": "OK"}

@app.post("/api/v1/analyze", response_model=schemas.InteractionResponse)
async def analyze_text(request_body: schemas.TextToAnalyze, db: AsyncSession = Depends(get_db)):
    if not model:
        raise HTTPException(status_code=500, detail="API do Gemini não configurada.")
    
    text_to_analyze = request_body.text
    prompt = f"""
    Aja como um especialista em análise de feedback de clientes.
    Analise o seguinte texto e retorne APENAS um JSON válido com a estrutura:
    {{"sentimento": "Positivo | Neutro | Negativo", "resumo": "Um resumo curto do feedback em uma frase.", "sugestao_de_resposta": "Uma sugestão de resposta profissional e empática para o cliente."}}

    Texto para analisar: "{text_to_analyze}"
    """
    
    response = model.generate_content(prompt)
    clean_response_text = response.text.strip().replace('```json', '').replace('```', '')
    analysis_data = json.loads(clean_response_text)
    
    new_interaction = models.Interaction(
        original_text=text_to_analyze,
        sentiment=analysis_data.get("sentimento"),
        summary=analysis_data.get("resumo"),
        suggested_response=analysis_data.get("sugestao_de_resposta")
    )
    
    db.add(new_interaction)
    await db.commit()
    await db.refresh(new_interaction)
    return new_interaction

@app.get("/api/v1/interactions", response_model=list[schemas.InteractionResponse])
async def get_all_interactions(db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    result = await db.execute(select(models.Interaction).order_by(models.Interaction.created_at.desc()))
    interactions = result.scalars().all()
    return interactions
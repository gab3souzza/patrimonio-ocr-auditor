import os
from pathlib import Path
from google import genai
from google.genai import types
from src.schemas import TermoResponsabilidadeExtraido

SYSTEM_INSTRUCTION = """
Você é um Auditor de Engenharia Patrimonial especializado na leitura óptica (OCR) de Termos de Responsabilidade de Bens Móveis (padrão SEPAT).
Regras estritas de extração:
1. Preserve rigorosamente os zeros à esquerda do número de PATRIMÔNIO (padrão de 10 dígitos, ex: 0050793749).
2. Caso o campo SÉRIE esteja em branco ou ilegível no documento físico, retorne null em `serie_ou_imei`. Nunca invente seriais.
3. Extraia o código numérico entre parênteses da DESCRIÇÃO para o campo `codigo_material`.
4. Converta valores monetários no formato brasileiro (ex: 20.990,80) para ponto flutuante padrão (20990.80).
"""


def extrair_termo_de_arquivo(caminho_arquivo: str, api_key: str | None = None) -> TermoResponsabilidadeExtraido:
    """
    Envia um PDF ou imagem escaneada de Termo de Responsabilidade para o Gemini 2.5 Flash
    e retorna o objeto validado pelo contrato Pydantic TermoResponsabilidadeExtraido.
    """
    chave = api_key or os.getenv("GEMINI_API_KEY")
    if not chave:
        raise ValueError("Variável de ambiente GEMINI_API_KEY não configurada.")

    client = genai.Client(api_key=chave)
    path = Path(caminho_arquivo)

    if not path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho_arquivo}")

    mime_type = "application/pdf" if path.suffix.lower() == ".pdf" else "image/jpeg"
    arquivo_bytes = path.read_bytes()

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            types.Part.from_bytes(data=arquivo_bytes, mime_type=mime_type),
            "Extraia todos os bens móveis e metadados deste Termo de Responsabilidade seguindo o schema."
        ],
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            response_mime_type="application/json",
            response_schema=TermoResponsabilidadeExtraido,
            temperature=0.0,
        ),
    )

    return TermoResponsabilidadeExtraido.model_validate_json(response.text)

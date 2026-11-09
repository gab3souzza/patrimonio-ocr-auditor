from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class SituacaoBem(str, Enum):
    BOM = "BOM"
    REGULAR = "REGULAR"
    ANTIECONOMICO = "ANTIECONÔMICO"
    IRRECUPERAVEL = "IRRECUPERÁVEL"


class StatusConciliacao(str, Enum):
    CONFORME = "CONFORME"
    DIVERGENCIA_SERIE = "DIVERGÊNCIA DE SÉRIE/IMEI"
    SEM_SERIE_NO_TERMO = "FALTA NÚMERO DE SÉRIE NO TERMO"
    VALOR_LOTE_CORRIGIDO = "VALOR DE LOTE NORMALIZADO"
    NAO_LOCALIZADO_NA_BASE = "TOMBO NÃO LOCALIZADO NA BASE MESTRE"


class ItemPatrimonialOCR(BaseModel):
    patrimonio: str = Field(
        description="Número de tombo patrimonial de 10 dígitos preservando zeros à esquerda (ex: '0050793749')."
    )
    codigo_material: Optional[str] = Field(
        default=None,
        description="Código numérico do material entre parênteses no início da descrição."
    )
    descricao: str = Field(
        description="Especificação técnica formal do equipamento extraída do termo."
    )
    marca: Optional[str] = Field(default=None, description="Fabricante do equipamento.")
    modelo: Optional[str] = Field(default=None, description="Modelo técnico do equipamento.")
    serie_ou_imei: Optional[str] = Field(
        default=None,
        description="Número de série alfanumérico ou IMEI de 15 dígitos. Nulo se estiver em branco no documento."
    )
    valor_impresso_brl: float = Field(
        description="Valor monetário impresso no termo em R$ (convertido para float)."
    )
    situacao: SituacaoBem = Field(default=SituacaoBem.BOM)

    @field_validator("patrimonio")
    @classmethod
    def formatar_tombo_dez_digitos(cls, v: str) -> str:
        apenas_digitos = "".join(filter(str.isdigit, v))
        return apenas_digitos.zfill(10)


class TermoResponsabilidadeExtraido(BaseModel):
    instituicao: str = Field(description="Nome da instituição no cabeçalho do termo.")
    unidade_setorial: str = Field(description="Laboratório ou setor responsável (ex: LISD2/IGM, ASCOM/IGM).")
    responsavel_setorial: str = Field(description="Nome do servidor responsável listado no rodapé.")
    itens: List[ItemPatrimonialOCR] = Field(description="Lista completa de bens móveis extraídos da página/documento.")


class ResultadoAuditoriaItem(BaseModel):
    patrimonio: str
    equipamento: str
    escola_destino: str
    serie_termo: Optional[str]
    serie_base_mestre: Optional[str]
    valor_unitario_auditado: float
    status: StatusConciliacao
    observacao_auditoria: str

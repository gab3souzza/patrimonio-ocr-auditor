import csv
from typing import Dict, List
from src.schemas import (
    ItemPatrimonialOCR,
    ResultadoAuditoriaItem,
    StatusConciliacao,
)


def carregar_base_mestre_csv(caminho_csv: str) -> Dict[str, dict]:
    """Carrega a planilha mestre de controle indexada pelo número de tombo (10 dígitos)."""
    base: Dict[str, dict] = {}
    with open(caminho_csv, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            tombo = "".join(filter(str.isdigit, row["patrimonio"])).zfill(10)
            base[tombo] = {
                "equipamento": row["equipamento"].strip(),
                "serie_esperada": row["serie_esperada"].strip() or None,
                "valor_unitario_referencia": float(row["valor_unitario_referencia"]),
                "escola_destino": row["escola_destino"].strip(),
            }
    return base


def auditar_itens_extraidos(
    itens_ocr: List[ItemPatrimonialOCR], base_mestre: Dict[str, dict]
) -> List[ResultadoAuditoriaItem]:
    """
    Cruza os itens extraídos via OCR com a Base Mestre de Estoque/Implantação,
    normalizando distorções tipográficas de lote e auditando números de série/IMEI.
    """
    relatorio: List[ResultadoAuditoriaItem] = []

    for item in itens_ocr:
        registro_mestre = base_mestre.get(item.patrimonio)

        if not registro_mestre:
            relatorio.append(
                ResultadoAuditoriaItem(
                    patrimonio=item.patrimonio,
                    equipamento=item.descricao[:50],
                    escola_destino="NÃO ALOCADO",
                    serie_termo=item.serie_ou_imei,
                    serie_base_mestre=None,
                    valor_unitario_auditado=item.valor_impresso_brl,
                    status=StatusConciliacao.NAO_LOCALIZADO_NA_BASE,
                    observacao_auditoria="Tombo extraído no PDF não consta na planilha mestre de solicitações.",
                )
            )
            continue

        valor_ref = registro_mestre["valor_unitario_referencia"]
        valor_auditado = item.valor_impresso_brl
        obs_lista = []
        status_final = StatusConciliacao.CONFORME

        # Regra de Negócio SEPAT: Detecção de valor de lote impresso no item unitário (ex: 10x o valor real)
        razao_lote = round(item.valor_impresso_brl / valor_ref, 1) if valor_ref > 0 else 1.0
        if razao_lote in (5.0, 10.0, 15.0, 20.0):
            valor_auditado = round(item.valor_impresso_brl / razao_lote, 2)
            status_final = StatusConciliacao.VALOR_LOTE_CORRIGIDO
            obs_lista.append(
                f"Anomalia tipográfica de lote ({int(razao_lote)} un.): R$ {item.valor_impresso_brl:.2f} normalizado para R$ {valor_auditado:.2f}."
            )

        # Regra de Negócio: Verificação estrita de Número de Série / IMEI
        serie_doc = (item.serie_ou_imei or "").strip().upper()
        serie_base = (registro_mestre["serie_esperada"] or "").strip().upper()

        if not serie_doc:
            status_final = StatusConciliacao.SEM_SERIE_NO_TERMO
            obs_lista.append("Termo físico sem número de série gravado. Necessária vistoria de chassi.")
        elif serie_base and serie_doc != serie_base:
            status_final = StatusConciliacao.DIVERGENCIA_SERIE
            obs_lista.append(f"Serial divergente! Termo: [{serie_doc}] vs Base: [{serie_base}].")
        else:
            obs_lista.append("Serial e tombamento validados com sucesso.")

        relatorio.append(
            ResultadoAuditoriaItem(
                patrimonio=item.patrimonio,
                equipamento=registro_mestre["equipamento"],
                escola_destino=registro_mestre["escola_destino"],
                serie_termo=serie_doc or None,
                serie_base_mestre=serie_base or None,
                valor_unitario_auditado=valor_auditado,
                status=status_final,
                observacao_auditoria=" | ".join(obs_lista),
            )
        )

    return relatorio

import json
import sys
from pathlib import Path

# Adiciona a raiz do projeto ao sys.path para execucao direta
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.schemas import ItemPatrimonialOCR, SituacaoBem
from src.reconciler import carregar_base_mestre_csv, auditar_itens_extraidos


def main():
    csv_path = Path(__file__).parent / "sample_master_inventory.csv"
    base_mestre = carregar_base_mestre_csv(str(csv_path))

    # Simulacao do payload retornado pelo Gemini 2.5 Flash apos ler um Termo SEPAT escaneado
    itens_extraidos_ocr = [
        ItemPatrimonialOCR(
            patrimonio="50793749",  # Testando auto-padding para 10 digitos ('0050793749')
            codigo_material="15042",
            descricao="(15042) IMPRESSORA 3D FDM FECHADA ALTA VELOCIDADE",
            marca="CREALITY",
            modelo="K1C",
            serie_ou_imei="CREALITY2026K1C098",
            valor_impresso_brl=4250.00,
            situacao=SituacaoBem.BOM,
        ),
        ItemPatrimonialOCR(
            patrimonio="0050793750",
            codigo_material="18920",
            descricao="(18920) SMART TV LED 50 POL 4K UHD",
            marca="LG",
            modelo="50UR8750",
            serie_ou_imei="YA50202509019",
            valor_impresso_brl=20990.80,  # Erro classico de lote (10x o valor unitario impresso no termo)
            situacao=SituacaoBem.BOM,
        ),
        ItemPatrimonialOCR(
            patrimonio="0052370897",
            codigo_material="19401",
            descricao="(19401) CORTADORA E GRAVADORA LASER DIODO 10W",
            marca="CREALITY",
            modelo="FALCON A1",
            serie_ou_imei=None,  # Termo escaneado sem numero de serie preenchido
            valor_impresso_brl=3890.00,
            situacao=SituacaoBem.BOM,
        ),
        ItemPatrimonialOCR(
            patrimonio="0052370898",
            codigo_material="11004",
            descricao="(11004) NOTEBOOK 15.6 CORE I7 16GB SSD 512GB",
            marca="DELL",
            modelo="LATITUDE 3540",
            serie_ou_imei="SN99999999ERR",  # Divergencia de chassi fisico vs planilha
            valor_impresso_brl=5400.00,
            situacao=SituacaoBem.BOM,
        ),
    ]

    resultados = auditar_itens_extraidos(itens_extraidos_ocr, base_mestre)

    print("\n=== RELATÓRIO DE AUDITORIA E CONCILIAÇÃO PATRIMONIAL (SEPAT/OCR) ===")
    print(json.dumps([r.model_dump() for r in resultados], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

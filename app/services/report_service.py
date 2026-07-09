import os
import json
from typing import Dict, Any, Tuple

def generate_text_report(report_data: Dict[str, Any]) -> str:
    """Generates a human-readable plain text audit report."""
    status_emoji = {
        "sucesso": "✅ SUCESSO",
        "sucesso_com_alertas": "⚠️ SUCESSO COM ALERTAS",
        "erro": "❌ ERRO"
    }
    
    status_text = status_emoji.get(report_data["status"], report_data["status"].upper())
    
    lines = [
        "======================================================================",
        "                     RELATÓRIO TÉCNICO DE CONVERSÃO                    ",
        "======================================================================",
        f"Data/Hora da Conversão:      {report_data['data_hora_conversao']}",
        f"Status Final:                {status_text}",
        f"Tempo de Processamento:      {report_data['tempo_processamento_segundos']} segundos",
        "----------------------------------------------------------------------",
        "ARQUIVO ORIGEM:",
        f"  Nome:                      {report_data['nome_original']}",
        f"  Caminho Completo:          {report_data['caminho_original']}",
        f"  Formato Detectado:         {report_data['formato_detectado'].upper()}",
        f"  Tamanho:                   {report_data['tamanho_bytes']} bytes",
        f"  SHA-256 Hash:              {report_data['hash_sha256']}",
        "----------------------------------------------------------------------"
    ]
    
    if report_data["formato_detectado"] == "csv":
        lines.extend([
            "CONFIGURAÇÃO CSV DETECTADA:",
            f"  Encoding:                  {report_data['csv_encoding']}",
            f"  Separador:                 {report_data['csv_separador']}",
            "----------------------------------------------------------------------"
        ])
    elif report_data["formato_detectado"] == "xlsx":
        lines.extend([
            "CONFIGURAÇÃO EXCEL PROCESSADA:",
            f"  Abas Convertidas:          {', '.join(report_data['xlsx_abas_processadas'])}",
            "----------------------------------------------------------------------"
        ])
        
    lines.extend([
        "DADOS GERADOS E ESTRUTURA:",
        f"  Total de Linhas Lidas:     {report_data['linhas_lidas']}",
        f"  Total de Colunas Lidas:    {report_data['colunas_lidas']}"
    ])
    
    if report_data["colunas_originais"]:
        lines.append("  Mapeamento de Colunas:")
        for orig, final in zip(report_data["colunas_originais"], report_data["colunas_finais"]):
            if orig != final:
                lines.append(f"    - '{orig}' -> '{final}'")
            else:
                lines.append(f"    - '{orig}'")
                
    if report_data["tipos_inferidos"]:
        lines.append("  Tipos de Campos Inferidos no Parquet:")
        for col, dtype in report_data["tipos_inferidos"].items():
            lines.append(f"    - {col}: {dtype}")
            
    lines.extend([
        "----------------------------------------------------------------------",
        "ARQUIVOS DESTINO GERADOS:",
    ])
    
    for path in report_data["caminho_parquet_gerado"]:
        lines.append(f"  - {path}")
        
    lines.extend([
        f"  Compressão Usada:          {report_data['compressao_usada'].upper()}",
        "----------------------------------------------------------------------"
    ])
    
    # Report errors or line skips
    if report_data["erros"]:
        lines.extend([
            "ERROS OCORRIDOS DURANTE O PROCESSO:",
            *[f"  - {err}" for err in report_data["erros"]],
            "----------------------------------------------------------------------"
        ])
        
    if report_data["ndjson_linhas_invalidas"]:
        lines.extend([
            f"LINHAS INVÁLIDAS PULADAS (NDJSON/JSONL) - Total: {len(report_data['ndjson_linhas_invalidas'])}:",
        ])
        # Display first 10 invalid lines
        for item in report_data["ndjson_linhas_invalidas"][:10]:
            lines.append(f"  - Linha {item['line_number']}: {item['error']}")
            lines.append(f"    Conteúdo: {item['content']}")
        if len(report_data["ndjson_linhas_invalidas"]) > 10:
            lines.append("  - ... e mais linhas inválidas (veja o relatório JSON para detalhes)")
        lines.append("----------------------------------------------------------------------")
        
    lines.append("======================================================================")
    return "\n".join(lines)

def write_reports(report_data: Dict[str, Any], output_dir: str) -> Tuple[str, str]:
    """
    Writes report_data to:
    - [original_name]_relatorio.json
    - [original_name]_relatorio.txt
    Returns paths to the written files.
    """
    original_name = report_data["nome_original"]
    base_name, _ = os.path.splitext(original_name)
    
    json_path = os.path.join(output_dir, f"{base_name}_relatorio.json")
    txt_path = os.path.join(output_dir, f"{base_name}_relatorio.txt")
    
    # Save JSON Report
    try:
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        # If we failed to write report, raise IOError but log it
        raise IOError(f"Falha ao gravar relatório JSON: {e}")
        
    # Save TXT Report
    try:
        txt_content = generate_text_report(report_data)
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(txt_content)
    except Exception as e:
        raise IOError(f"Falha ao gravar relatório TXT: {e}")
        
    return json_path, txt_path

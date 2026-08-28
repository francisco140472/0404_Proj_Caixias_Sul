import os
import re
import pdfplumber
import csv
import unicodedata

# 1. Caminhos dos arquivos
pasta_pdfs = r"Z:"
arquivo_saida = r"Z:\relatorio_ordens_completo.csv"

# 2. Definindo os nomes das colunas para o Excel / CSV
cabecalho = [
    "Nome_do_Arquivo", 
    "Inscricao_ZSQL", 
    "OS_Numero", 
    "Codigo_Processo", 
    "Data_Geracao", 
    "Gerado_Por",        
    "Secao", 
    "Tipo", 
    "Numero_Consumidor", 
    "Nome_Consumidor", 
    "Hidrometro"
]

dados_extraidos = []

print(f"Iniciando a extração completa na pasta:\n{pasta_pdfs}\n")
print("-" * 60)

# Função: Remove acentos e cedilhas
def remover_acentos(texto):
    if not texto:
        return ""
    texto_limpo = unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('utf-8')
    return texto_limpo

# Função: Busca textos no PDF e limpa sujeiras
def extrair_campo(padrao, texto):
    busca = re.search(padrao, texto, re.IGNORECASE)
    if busca:
        valor = busca.group(1).replace("|", "").strip()
        return valor
    return "Nao encontrado"

# 3. Loop de processamento dos arquivos
for nome_arquivo in os.listdir(pasta_pdfs):
    if nome_arquivo.lower().endswith(".pdf"):
        caminho_completo = os.path.join(pasta_pdfs, nome_arquivo)
        
        try:
            with pdfplumber.open(caminho_completo) as pdf:
                texto = pdf.pages[0].extract_text()
                
                if texto:
                    linha = {"Nome_do_Arquivo": nome_arquivo}
                    
                    # 3.1 Extração da Inscrição SEM PONTOS (Para bater com o SQL Server)
                    busca_zsql = re.search(r"Z/S/Q/L:\s*(\d+)\s+(\d+)\s+(\d+)\s+(\d+)", texto)
                    if busca_zsql:
                        zona = busca_zsql.group(1).zfill(2)    
                        setor = busca_zsql.group(2).zfill(2)   
                        quadra = busca_zsql.group(3).zfill(4)  
                        lote = busca_zsql.group(4).zfill(3)    
                        
                        # ALTERAÇÃO AQUI: Salva direto sem pontos (ex: 29253223003)
                        linha["Inscricao_ZSQL"] = f"{zona}{setor}{quadra}{lote}"
                    else:
                        linha["Inscricao_ZSQL"] = "Nao encontrado"
                        
                    # 3.2 Extração dos campos padrão
                    linha["OS_Numero"] = extrair_campo(r"ORDEM DE SERVI[CÇ]O N[UÚ]MERO:\s*\|?\s*(\d+)", texto)
                    linha["Codigo_Processo"] = extrair_campo(r"C[OÓ]DIGO DO PROCESSO:\s*\|?\s*(\d+)", texto)
                    linha["Data_Geracao"] = extrair_campo(r"DT GERA[CÇ][AÃ]O:\s*\|?\s*(\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2})", texto)
                    linha["Gerado_Por"] = extrair_campo(r"GERADO POR:\s*\|?\s*([^\n]+)", texto)
                    linha["Secao"] = extrair_campo(r"SE[CÇ][AÃ]O:\s*\|?\s*([^\n]+)", texto)
                    linha["Tipo"] = extrair_campo(r"TIPO:\s*\|?\s*([^\n]+)", texto)
                    linha["Hidrometro"] = extrair_campo(r"HIDR[OÔ]METRO:\s*\|?\s*([A-Z0-9]+)", texto)

                    # 3.3 Tratamento Especial para separar o Número e o Nome do Consumidor
                    consumidor_bruto = extrair_campo(r"CONSUMIDOR:\s*\|?\s*([^\n]+)", texto)
                    
                    if consumidor_bruto != "Nao encontrado":
                        consumidor_limpo = re.sub(r"\s+SITUA[CÇ][AÃ]O.*", "", consumidor_bruto, flags=re.IGNORECASE)
                        busca_separacao = re.search(r"(\d+-\d+)\s+(.*)", consumidor_limpo)
                        
                        if busca_separacao:
                            linha["Numero_Consumidor"] = busca_separacao.group(1) 
                            linha["Nome_Consumidor"] = busca_separacao.group(2).strip() 
                        else:
                            linha["Numero_Consumidor"] = "Nao encontrado"
                            linha["Nome_Consumidor"] = consumidor_limpo.strip()
                    else:
                        linha["Numero_Consumidor"] = "Nao encontrado"
                        linha["Nome_Consumidor"] = "Nao encontrado"

                    # 3.4 Formatação final da linha (removendo acentos)
                    registro_formatado = [remover_acentos(linha.get(coluna, "")) for coluna in cabecalho]
                    
                    dados_extraidos.append(registro_formatado)
                    print(f"[ OK ] {nome_arquivo} processado com sucesso!")
                else:
                    print(f"[ -- ] {nome_arquivo} -> Sem texto legível.")
                    
        except Exception as e:
            print(f"[ERRO] Falha no arquivo {nome_arquivo}: {e}")

print("-" * 60)

# 4. Criação do arquivo CSV para o join
if dados_extraidos:
    with open(arquivo_saida, mode='w', newline='', encoding='utf-8-sig') as arquivo_csv:
        escritor = csv.writer(arquivo_csv, delimiter=';')
        escritor.writerow(cabecalho)
        escritor.writerows(dados_extraidos)
        
    print(f"\nFinalizado! {len(dados_extraidos)} registros exportados.")
    print(f"O CSV foi salvo em:\n{arquivo_saida}")
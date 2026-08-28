import arcpy
import os

print("Iniciando o processamento definitivo...")
print("-" * 60)

# 1. Configurações e Caminhos base
arcpy.env.overwriteOutput = True # Permite sobrescrever arquivos se você rodar o script várias vezes
pasta_projeto = r"C:\Projetos\Caixias_Sul"

# --- CAMINHO DO CSV ATUALIZADO PARA Z:\ ---
csv_path = r"Z:\relatorio_ordens_completo.csv"

shp_path = os.path.join(pasta_projeto, r"shp\centroide_Ligacao_lote.shp")
camada_saida = os.path.join(pasta_projeto, r"shp\centroide_com_historico_OS.lyrx")

# 2. Criação do Banco de Dados Geográfico (.gdb)
gdb_path = os.path.join(pasta_projeto, "Banco_OS.gdb")
if not arcpy.Exists(gdb_path):
    print("Criando File Geodatabase (Banco_OS.gdb) para armazenar dados seguros...")
    arcpy.management.CreateFileGDB(pasta_projeto, "Banco_OS.gdb")

# 3. Caminhos das tabelas PERMANENTES dentro do .gdb
tabela_permanente_csv = os.path.join(gdb_path, "ordens_servico_tabela")
tabela_resumo = os.path.join(gdb_path, "resumo_frequencia_os")

# Nomes virtuais para as camadas
camada_virtual_shp = "centroides_lote_layer"
tabela_virtual_csv = "ordens_servico_tb"

try:
    # 4. Copia o CSV da unidade Z: para dentro do .gdb (Isso resolve o OID e salva fisicamente)
    print("1. Importando CSV para o Geodatabase...")
    arcpy.management.CopyRows(csv_path, tabela_permanente_csv)
    
    # Cria as visualizações a partir dos dados físicos
    arcpy.management.MakeFeatureLayer(shp_path, camada_virtual_shp)
    arcpy.management.MakeTableView(tabela_permanente_csv, tabela_virtual_csv)

    # 5. Contagem de OS por Lote
    print("2. Analisando lotes com múltiplas Ordens de Serviço...")
    arcpy.analysis.Frequency(tabela_virtual_csv, tabela_resumo, ["Inscricao_ZSQL"])

    # 6. Faz o Join com a Tabela de Resumo Física (Filtra o mapa)
    print("3. Vinculando a quantidade de OS ao mapa...")
    arcpy.management.AddJoin(
        camada_virtual_shp, 
        "inscricaol", 
        tabela_resumo, 
        "Inscricao_ZSQL", 
        "KEEP_COMMON" 
    )

    # 7. Cria o Relacionamento com a tabela completa (para o Pop-up)
    nome_base_shp = os.path.basename(shp_path).replace(".shp", "")
    campo_referencia = f"{nome_base_shp}.inscricaol"
    
    print("4. Anexando o histórico completo para o Pop-up...")
    arcpy.management.AddRelate(
        camada_virtual_shp,
        campo_referencia,            
        tabela_virtual_csv,          
        "Inscricao_ZSQL",            
        "Historico_Ordens_Servico"   
    )

    # 8. Salva o arquivo de camada (.lyrx)
    print("5. Gerando arquivo de camada (.lyrx)...")
    arcpy.management.SaveToLayerFile(camada_virtual_shp, camada_saida, "RELATIVE")

    # 9. Configura a Simbologia Baseada na QUANTIDADE de OS
    print("6. Aplicando simbologia por Quantidade de OS...")
    arquivo_lyrx = arcpy.mp.LayerFile(camada_saida)
    camada = arquivo_lyrx.listLayers()[0]
    simbologia = camada.symbology
    
    if hasattr(simbologia, 'updateRenderer'):
        simbologia.updateRenderer('UniqueValueRenderer')
        # Como a tabela agora é física, acessamos o nome base da tabela de resumo
        campo_simbologia = "resumo_frequencia_os.FREQUENCY" 
        simbologia.renderer.fields = [campo_simbologia]
        camada.symbology = simbologia
        arquivo_lyrx.save()

    print("-" * 60)
    print(f"[ OK ] Sucesso! O arquivo final está pronto em:\n{camada_saida}")

except Exception as e:
    print("-" * 60)
    print(f"[ ERRO ] Ocorreu um problema durante a execução do arcpy: {e}")
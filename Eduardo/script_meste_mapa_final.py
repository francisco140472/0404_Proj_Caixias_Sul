# coding: utf-8
import arcpy
import os

# ==========================================
# 1. ENTRADAS E SAÍDAS (Ajuste se precisar)
# ==========================================
txt_file = r"C:\Projetos\Caixias_Sul\Eduardo\286008_2026-06-29-12-03-59.txt"
out_pontos = r"C:\Projetos\Caixias_Sul\Eduardo\pontos_finais.shp"
out_linhas = r"C:\Projetos\Caixias_Sul\Eduardo\linhas_finais.shp"

arcpy.env.overwriteOutput = True

# Sistemas de Coordenadas
sr_origem = arcpy.SpatialReference(2236) # Florida East (Pés)
sr_destino = arcpy.SpatialReference(4326) # WGS 84 (Geográficas)

print("Iniciando o processamento automático...")

# ==========================================
# 2. LER O TXT E CRIAR PONTOS TEMPORÁRIOS
# ==========================================
temp_fc = r"memory\pontos_temp"
arcpy.management.CreateFeatureclass("memory", "pontos_temp", "POINT", spatial_reference=sr_origem)

arcpy.management.AddField(temp_fc, "PointID", "LONG")
arcpy.management.AddField(temp_fc, "Elevation", "DOUBLE")
arcpy.management.AddField(temp_fc, "Descriptio", "TEXT", field_length=50)

with arcpy.da.InsertCursor(temp_fc, ["SHAPE@XY", "PointID", "Elevation", "Descriptio"]) as cursor:
    with open(txt_file, 'r') as file:
        for line in file:
            parts = line.strip().split(',')
            if len(parts) == 5:
                pt_id, y_norte, x_este, z_alt, desc = int(parts[0]), float(parts[1]), float(parts[2]), float(parts[3]), parts[4]
                cursor.insertRow([(x_este, y_norte), pt_id, z_alt, desc])

# ==========================================
# 3. CONVERTER PARA GEOGRÁFICAS (SHP FINAL DE PONTOS)
# ==========================================
print("Convertendo coordenadas e gerando Shapefile de Pontos...")
arcpy.management.Project(temp_fc, out_pontos, sr_destino)
arcpy.management.Delete(temp_fc) # Limpa a memória

# ==========================================
# 4. GERAR SHAPEFILE DE LINHAS SEQUENCIAIS
# ==========================================
print("Analisando sequências e gerando Shapefile de Linhas...")
arcpy.management.CreateFeatureclass(os.path.dirname(out_linhas), os.path.basename(out_linhas), "POLYLINE", spatial_reference=sr_destino)
arcpy.management.AddField(out_linhas, "Descricao", "TEXT", field_length=50)

# Lendo os pontos recém-criados
pontos = []
with arcpy.da.SearchCursor(out_pontos, ["SHAPE@XY", "PointID", "Descriptio"]) as cursor:
    for row in cursor:
        pontos.append((row[1], row[0][0], row[0][1], row[2]))

pontos.sort(key=lambda x: x[0]) # Garante a ordem do PointID

# Agrupando em linhas
linhas_para_criar = []
if pontos:
    linha_atual = [pontos[0]]
    desc_atual = pontos[0][3]

    for p in pontos[1:]:
        desc_ponto = p[3]
        if desc_ponto == desc_atual and desc_ponto and str(desc_ponto).strip() != "":
            linha_atual.append(p)
        else:
            if len(linha_atual) > 1:
                linhas_para_criar.append((desc_atual, linha_atual))
            linha_atual = [p]
            desc_atual = desc_ponto

    if len(linha_atual) > 1:
        linhas_para_criar.append((desc_atual, linha_atual))

# Desenhando as linhas
with arcpy.da.InsertCursor(out_linhas, ["SHAPE@", "Descricao"]) as cursor:
    for desc, pts in linhas_para_criar:
        array_vertices = arcpy.Array([arcpy.Point(p[1], p[2]) for p in pts])
        cursor.insertRow([arcpy.Polyline(array_vertices, sr_destino), desc])

# ==========================================
# 5. ADICIONAR AO MAPA
# ==========================================
try:
    aprx = arcpy.mp.ArcGISProject("CURRENT")
    mapa = aprx.activeMap
    if mapa:
        mapa.addDataFromPath(out_pontos)
        mapa.addDataFromPath(out_linhas)
        print("🎨 Camadas adicionadas ao mapa com sucesso!")
except Exception as e:
    pass

print(f"✅ Sistema finalizado! Seus arquivos estão em: {os.path.dirname(out_pontos)}")
# Iniciando o processamento automático...
# Convertendo coordenadas e gerando Shapefile de Pontos...
# Analisando sequências e gerando Shapefile de Linhas...
# 🎨 Camadas adicionadas ao mapa com sucesso!
# ✅ Sistema finalizado! Seus arquivos estão em: C:\Projetos\Caixias_Sul\Eduardo

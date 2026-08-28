# coding: utf-8
import arcpy
import os
import math
from collections import defaultdict

# === 1. CAMINHOS PARA OS SHAPEFILES ===
in_pontos = r"C:\Projetos\Caixias_Sul\Eduardo\pontos_finais.shp"
out_pontos_proj = r"C:\Projetos\Caixias_Sul\Eduardo\pontos_projetados.shp"
out_linhas = r"C:\Projetos\Caixias_Sul\Eduardo\linhas_contorno_perfeito.shp"

arcpy.env.overwriteOutput = True

# === 2. PROJETAR PARA COORDENADAS PLANAS (UTM) ===
print("1. Convertendo pontos de Graus para UTM...")

# EPSG: 32617 = WGS 84 / UTM zone 17N (Sistema padrão da Flórida)
# Nota: Se quiser voltar para Pés (State Plane East), troque 32617 por 2236
sr_projetado = arcpy.SpatialReference(32617)

arcpy.management.Project(
    in_dataset=in_pontos,
    out_dataset=out_pontos_proj,
    out_coor_system=sr_projetado
)

# === 3. CRIAR SHAPEFILE DE LINHAS ===
print("2. Preparando arquivo de linhas contínuas...")
arcpy.management.CreateFeatureclass(
    out_path=os.path.dirname(out_linhas),
    out_name=os.path.basename(out_linhas),
    geometry_type="POLYLINE",
    spatial_reference=sr_projetado
)

arcpy.management.AddField(out_linhas, "Descricao", "TEXT", field_length=50)

# === 4. AGRUPAR PONTOS PELA DESCRIÇÃO (Usando os pontos já projetados) ===
print("3. Agrupando pontos e calculando matemática radial...")
grupos_de_pontos = defaultdict(list)

with arcpy.da.SearchCursor(out_pontos_proj, ["SHAPE@XY", "Descriptio"]) as cursor:
    for row in cursor:
        x, y = row[0]
        desc = row[1]
        
        if desc and str(desc).strip() != "":
            grupos_de_pontos[desc].append((x, y))

# === 5. DESENHAR OS CONTORNOS SEM CRUZAMENTOS ===
with arcpy.da.InsertCursor(out_linhas, ["SHAPE@", "Descricao"]) as cursor:
    for desc, lista_pontos in grupos_de_pontos.items():
        
        # Se tiver 3 ou mais pontos, fechamos o polígono contornando o centro
        if len(lista_pontos) > 2:
            centro_x = sum(p[0] for p in lista_pontos) / len(lista_pontos)
            centro_y = sum(p[1] for p in lista_pontos) / len(lista_pontos)
            
            # Ordena por ângulo ao redor do centro geométrico (funcionará perfeito no UTM)
            lista_pontos.sort(key=lambda p: math.atan2(p[1] - centro_y, p[0] - centro_x))
            
            # Fecha a forma geométrica
            lista_pontos.append(lista_pontos[0])
            
        elif len(lista_pontos) < 2:
            continue # Pula pontos isolados (postes, hidrômetros)

        # Insere a linha
        array_vertices = arcpy.Array()
        for p in lista_pontos:
            array_vertices.add(arcpy.Point(p[0], p[1]))
        
        linha_geom = arcpy.Polyline(array_vertices, sr_projetado)
        cursor.insertRow([linha_geom, desc])

# === 6. ADICIONAR AO MAPA ===
try:
    aprx = arcpy.mp.ArcGISProject("CURRENT")
    mapa = aprx.activeMap
    if mapa:
        mapa.addDataFromPath(out_pontos_proj)
        mapa.addDataFromPath(out_linhas)
        print("🎨 Camadas atualizadas adicionadas ao mapa!")
except Exception as e:
    pass

print(f"✅ Sucesso! O arquivo de linhas finais foi gerado em: {out_linhas}")
# 1. Convertendo pontos de Graus para UTM...
# 2. Preparando arquivo de linhas contínuas...
# 3. Agrupando pontos e calculando matemática radial...
# 🎨 Camadas atualizadas adicionadas ao mapa!
# ✅ Sucesso! O arquivo de linhas finais foi gerado em: C:\Projetos\Caixias_Sul\Eduardo\linhas_contorno_perfeito.shp

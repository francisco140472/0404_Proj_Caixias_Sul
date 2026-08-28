# coding: utf-8
import arcpy
import os
import math
from collections import defaultdict

# === 1. CAMINHOS PARA OS SHAPEFILES ===
in_pontos = r"C:\Projetos\Caixias_Sul\Eduardo\pontos_finais.shp"
out_linhas = r"C:\Projetos\Caixias_Sul\Eduardo\linhas_contorno_perfeito.shp"

arcpy.env.overwriteOutput = True
sr = arcpy.Describe(in_pontos).spatialReference

# === 2. CRIAR SHAPEFILE DE LINHAS ===
arcpy.management.CreateFeatureclass(
    out_path=os.path.dirname(out_linhas),
    out_name=os.path.basename(out_linhas),
    geometry_type="POLYLINE",
    spatial_reference=sr
)

arcpy.management.AddField(out_linhas, "Descricao", "TEXT", field_length=50)

# === 3. AGRUPAR PONTOS PELA DESCRIÇÃO ===
print("Lendo pontos e agrupando pela descrição...")
grupos_de_pontos = defaultdict(list)

with arcpy.da.SearchCursor(in_pontos, ["SHAPE@XY", "Descriptio"]) as cursor:
    for row in cursor:
        x, y = row[0]
        desc = row[1]
        
        # Ignora campos vazios
        if desc and str(desc).strip() != "":
            grupos_de_pontos[desc].append((x, y))

# === 4. CRIAR OS CONTORNOS COMO PONTEIROS DE UM RELÓGIO ===
print("Calculando o centro geométrico e desenhando os contornos sem cruzamentos...")

with arcpy.da.InsertCursor(out_linhas, ["SHAPE@", "Descricao"]) as cursor:
    for desc, lista_pontos in grupos_de_pontos.items():
        
        # Se tiver 3 ou mais pontos, podemos fechar um polígono perfeito
        if len(lista_pontos) > 2:
            # 1. Encontra o ponto central (Centróide) de todos os pontos desse grupo
            centro_x = sum(p[0] for p in lista_pontos) / len(lista_pontos)
            centro_y = sum(p[1] for p in lista_pontos) / len(lista_pontos)
            
            # 2. Ordena os pontos ao redor desse centro usando o ângulo (matemática circular)
            lista_pontos.sort(key=lambda p: math.atan2(p[1] - centro_y, p[0] - centro_x))
            
            # 3. Fecha o desenho voltando para o primeiro ponto da lista
            lista_pontos.append(lista_pontos[0])
            
        elif len(lista_pontos) < 2:
            # Se for apenas 1 ponto isolado (como um poste ou hidrômetro), não faz linha e pula
            continue

        # Desenha a linha conectando os pontos na nova ordem circular
        array_vertices = arcpy.Array()
        for p in lista_pontos:
            array_vertices.add(arcpy.Point(p[0], p[1]))
        
        linha_geom = arcpy.Polyline(array_vertices, sr)
        cursor.insertRow([linha_geom, desc])

# === 5. ADICIONAR AO MAPA ===
try:
    aprx = arcpy.mp.ArcGISProject("CURRENT")
    mapa = aprx.activeMap
    if mapa:
        mapa.addDataFromPath(out_linhas)
        print("🎨 Contornos adicionados ao mapa com sucesso!")
except Exception as e:
    pass

print(f"✅ Arquivo de contornos perfeitos gerado em: {out_linhas}")
# Lendo pontos e agrupando pela descrição...
# Calculando o centro geométrico e desenhando os contornos sem cruzamentos...
# 🎨 Contornos adicionados ao mapa com sucesso!
# ✅ Arquivo de contornos perfeitos gerado em: C:\Projetos\Caixias_Sul\Eduardo\linhas_contorno_perfeito.shp

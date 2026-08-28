# coding: utf-8
import arcpy
import os

# === 1. CAMINHOS PARA SHAPEFILE ===
in_pontos = r"C:\Projetos\Caixias_Sul\Eduardo\pontos_florida_geo.shp"
out_linhas = r"C:\Projetos\Caixias_Sul\Eduardo\linhas_florida_v1.shp"

# Permite sobrescrever se rodar mais de uma vez
arcpy.env.overwriteOutput = True

# Pega o sistema de coordenadas do shapefile de pontos
sr = arcpy.Describe(in_pontos).spatialReference

# === 2. CRIAR SHAPEFILE DE LINHA ===
arcpy.management.CreateFeatureclass(
    out_path=os.path.dirname(out_linhas),
    out_name=os.path.basename(out_linhas),
    geometry_type="POLYLINE",
    spatial_reference=sr
)

# === 3. LER OS PONTOS NA SEQUÊNCIA (ORDEM) ===
print("Lendo os pontos do shapefile e ordenando pela sequência...")
pontos_lista = []

# Lemos as coordenadas (X,Y) e o campo PointID (Ordem)
with arcpy.da.SearchCursor(in_pontos, ["SHAPE@XY", "PointID"]) as cursor:
    for row in cursor:
        pontos_lista.append((row[1], row[0]))

# Ordena do menor para o maior baseado na Ordem
pontos_lista.sort(key=lambda x: x[0])

# === 4. CONSTRUIR A LINHA ===
print("Desenhando a linha conectando os pontos...")
array_vertices = arcpy.Array()

for p in pontos_lista:
    x, y = p[1]
    array_vertices.add(arcpy.Point(x, y))

# Cria a geometria de linha (Polyline)
linha_geom = arcpy.Polyline(array_vertices, sr)

# === 5. INSERIR NO MAPA ===
with arcpy.da.InsertCursor(out_linhas, ["SHAPE@"]) as cursor:
    cursor.insertRow([linha_geom])

# Tenta adicionar o shapefile ao mapa atual e colocar em destaque (Vermelho)
try:
    aprx = arcpy.mp.ArcGISProject("CURRENT")
    mapa = aprx.activeMap
    if mapa:
        camada = mapa.addDataFromPath(out_linhas)
        
        sym = camada.symbology
        if hasattr(sym, 'renderer'):
            sym.renderer.symbol.color = {'RGB': [255, 0, 0, 100]} # Vermelho
            sym.renderer.symbol.size = 2 # Espessura da linha
            camada.symbology = sym
            print("🎨 Cor vermelha aplicada à linha com sucesso!")
except Exception as e:
    print("Nota: A linha foi criada, mas a cor precisará ser alterada manualmente.")

print(f"✅ Shapefile de linha criado com sucesso em: {out_linhas}")
# Lendo os pontos do shapefile e ordenando pela sequência...
# Desenhando a linha conectando os pontos...
# 🎨 Cor vermelha aplicada à linha com sucesso!
# ✅ Shapefile de linha criado com sucesso em: C:\Projetos\Caixias_Sul\Eduardo\linhas_florida_v1.shp

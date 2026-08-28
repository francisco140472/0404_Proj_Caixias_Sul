# coding: utf-8
import arcpy
import os

# === 1. CAMINHOS PARA SHAPEFILE ===
in_pontos = r"C:\Projetos\Caixias_Sul\Eduardo\pontos_florida_geo.shp"
out_linhas = r"C:\Projetos\Caixias_Sul\Eduardo\linhas_sequenciais_v2.shp"

arcpy.env.overwriteOutput = True
sr = arcpy.Describe(in_pontos).spatialReference

# === 2. CRIAR SHAPEFILE DE LINHAS ===
arcpy.management.CreateFeatureclass(
    out_path=os.path.dirname(out_linhas),
    out_name=os.path.basename(out_linhas),
    geometry_type="POLYLINE",
    spatial_reference=sr
)

# Adicionar um campo para guardar o nome da descrição na linha
arcpy.management.AddField(out_linhas, "Descricao", "TEXT", field_length=50)

# === 3. LER E ORDENAR TODOS OS PONTOS ===
print("Lendo os pontos e ordenando por PointID...")
pontos = []
campos = ["SHAPE@XY", "PointID", "Descriptio"] 

with arcpy.da.SearchCursor(in_pontos, campos) as cursor:
    for row in cursor:
        # row[0] = (X, Y), row[1] = PointID, row[2] = Descriptio
        pontos.append((row[1], row[0][0], row[0][1], row[2]))

# Ordena do menor para o maior baseado no PointID
pontos.sort(key=lambda x: x[0])

# === 4. AGRUPAR SEQUENCIALMENTE E DESENHAR ===
print("Criando linhas com base na sequência e descrição...")
linhas_para_criar = []

if pontos:
    linha_atual = [pontos[0]]
    desc_atual = pontos[0][3]

    # Percorre a partir do segundo ponto
    for p in pontos[1:]:
        desc_ponto = p[3]
        
        # Se a descrição for igual à do ponto anterior, continua a linha
        if desc_ponto == desc_atual and desc_ponto and str(desc_ponto).strip() != "":
            linha_atual.append(p)
        else:
            # A descrição mudou! Se a linha anterior tiver 2 ou mais pontos, salva ela.
            if len(linha_atual) > 1:
                linhas_para_criar.append((desc_atual, linha_atual))
            
            # Começa uma nova linha com o ponto atual
            linha_atual = [p]
            desc_atual = desc_ponto

    # Checa o último grupo de pontos ao final do loop
    if len(linha_atual) > 1:
        linhas_para_criar.append((desc_atual, linha_atual))

# === 5. INSERIR NO MAPA ===
with arcpy.da.InsertCursor(out_linhas, ["SHAPE@", "Descricao"]) as cursor:
    for desc, pts in linhas_para_criar:
        array_vertices = arcpy.Array()
        for p in pts:
            x, y = p[1], p[2]
            array_vertices.add(arcpy.Point(x, y))
        
        linha_geom = arcpy.Polyline(array_vertices, sr)
        cursor.insertRow([linha_geom, desc])

# Tenta adicionar ao mapa atual
try:
    aprx = arcpy.mp.ArcGISProject("CURRENT")
    mapa = aprx.activeMap
    if mapa:
        mapa.addDataFromPath(out_linhas)
        print("🎨 Linhas sequenciais adicionadas ao mapa! Use 'Unique Values' para colorir por 'Descricao'.")
except Exception as e:
    pass

print(f"✅ Arquivo criado com sucesso em: {out_linhas}")
# Lendo os pontos e ordenando por PointID...
# Criando linhas com base na sequência e descrição...
# 🎨 Linhas sequenciais adicionadas ao mapa! Use 'Unique Values' para colorir por 'Descricao'.
# ✅ Arquivo criado com sucesso em: C:\Projetos\Caixias_Sul\Eduardo\linhas_sequenciais_v2.shp

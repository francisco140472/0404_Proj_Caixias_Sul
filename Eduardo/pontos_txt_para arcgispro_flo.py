# coding: utf-8
import arcpy
import os

# === 1. CONFIGURAÇÕES DOS ARQUIVOS ===
# Substitua pelos caminhos reais da sua máquina
txt_file = r"C:\Projetos\Caixias_Sul\Eduardo\286008_2026-06-29-12-03-59.txt"
out_fc_final = r"C:\Projetos\Caixias_Sul\Eduardo\pontos_florida_geo"

arcpy.env.overwriteOutput = True

# === 2. SISTEMAS DE COORDENADAS ===
# EPSG 2236 = NAD 1983 StatePlane Florida East (Medido em Pés)
# (Se os pontos caírem no lugar errado, tente 2233 para North ou 2237 para West)
sr_origem = arcpy.SpatialReference(2236) 

# EPSG 4326 = WGS 84 (Coordenadas Geográficas / Lat-Long)
sr_destino = arcpy.SpatialReference(4326) 


# === 3. CRIAR CAMADA TEMPORÁRIA ===
temp_fc = r"memory\pontos_temp"
arcpy.management.CreateFeatureclass(
    out_path="memory",
    out_name="pontos_temp",
    geometry_type="POINT",
    spatial_reference=sr_origem
)

# Criar as colunas na tabela de atributos
arcpy.management.AddField(temp_fc, "PointID", "LONG")
arcpy.management.AddField(temp_fc, "Elevation", "DOUBLE")
arcpy.management.AddField(temp_fc, "Description", "TEXT")


# === 4. LER O TXT E INSERIR OS PONTOS ===
fields = ["SHAPE@XY", "PointID", "Elevation", "Description"]

with arcpy.da.InsertCursor(temp_fc, fields) as cursor:
    with open(txt_file, 'r') as file:
        for line in file:
            parts = line.strip().split(',')
            if len(parts) == 5:
                pt_id = int(parts[0])           # Order
                y_norte = float(parts[1])       # Norte (Y)
                x_este = float(parts[2])        # Este (X)
                z_alt = float(parts[3])         # Altitude
                desc = parts[4]                 # Tipo
                
                # Inserir no mapa: O ArcGIS sempre pede (X, Y), logo (Este, Norte)
                cursor.insertRow([(x_este, y_norte), pt_id, z_alt, desc])


# === 5. CONVERTER PARA GEOGRÁFICAS ===
print("Pontos lidos. Convertendo para Geográficas...")
arcpy.management.Project(
    in_dataset=temp_fc,
    out_dataset=out_fc_final,
    out_coor_system=sr_destino
)

# Limpar a memória do ArcGIS
arcpy.management.Delete(temp_fc)

print(f"✅ Sucesso! O arquivo convertido foi salvo em: {out_fc_final}")
# Pontos lidos. Convertendo para Geográficas...
# ✅ Sucesso! O arquivo convertido foi salvo em: C:\Projetos\Caixias_Sul\Eduardo\pontos_florida_geo

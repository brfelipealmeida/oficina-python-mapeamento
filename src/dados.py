"""
dados.py — funções para baixar os dados públicos usados na oficina.
Autor: Felipe Almeida (felipe-almeida.com)

Fontes:
  - IBGE, Censo Demográfico 2022 (SIDRA e Malha de Setores com atributos)
  - geobr (IPEA) para limites municipais
  - OpenStreetMap, via osmnx
"""
import os
import urllib.request

import geopandas as gpd
import pandas as pd

from estilo import CRS_BH, CRS_WEB

PASTA_DADOS = os.environ.get("PASTA_DADOS", "dados_baixados")
COD_BH = "3106200"

URL_SETORES_MG = ("https://ftp.ibge.gov.br/Censos/Censo_Demografico_2022/"
                  "Agregados_por_Setores_Censitarios/malha_com_atributos/"
                  "setores/gpkg/UF/MG/MG_setores_CD2022.gpkg")

# Dicionário das variáveis da malha com atributos (IBGE, Censo 2022)
VARIAVEIS_SETOR = {
    "v0001": "pessoas",
    "v0002": "domicilios",
    "v0003": "domicilios_particulares",
    "v0004": "domicilios_coletivos",
    "v0005": "media_moradores",
    "v0006": "pct_imputados",
    "v0007": "domicilios_ocupados",
}


def _baixar(url, destino):
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    if not os.path.exists(destino):
        print(f"Baixando {os.path.basename(destino)} ... (pode levar 1 a 3 minutos)")
        urllib.request.urlretrieve(url, destino)
    return destino


def populacao_municipios_sidra(uf=31):
    """
    População residente 2022 por município (SIDRA, tabela 4714, variável 93).
    Retorna um DataFrame NÃO espacial: só código, nome e população.
    """
    url = (f"https://apisidra.ibge.gov.br/values/t/4714/n6/in%20n3%20{uf}"
           f"/v/93/p/2022?formato=json")
    bruto = pd.read_json(url)
    cabecalho = bruto.iloc[0].to_dict()        # a 1ª linha da SIDRA é o cabeçalho
    df = bruto.iloc[1:].rename(columns=cabecalho)
    col_cod = [c for c in df.columns if "(Código)" in c and "Munic" in c][0]
    col_nome = [c for c in df.columns if c.startswith("Munic") and "(Código)" not in c][0]
    return df[[col_cod, col_nome, "Valor"]].rename(
        columns={col_cod: "cod_mun", col_nome: "municipio", "Valor": "populacao"})


def municipios_mg(ano=2022):
    """
    Limites municipais de MG. Tenta o geobr (IPEA); se falhar, usa a API de malhas do IBGE.
    Atenção: no geobr o código vem como número decimal (3106200.0). Isso é proposital
    na oficina: é um bom exemplo de por que conferir o tipo das colunas antes de um join.
    """
    try:
        import geobr
        gdf = geobr.read_municipality(code_muni="MG", year=ano)
        return gdf[["code_muni", "name_muni", "geometry"]]
    except Exception as erro:
        print(f"geobr indisponível ({erro}); usando a API de malhas do IBGE.")
        url = ("https://servicodados.ibge.gov.br/api/v3/malhas/estados/31"
               "?formato=application/vnd.geo+json&intrarregiao=municipio&qualidade=intermediaria")
        gdf = gpd.read_file(url)
        return gdf.rename(columns={"codarea": "code_muni"})[["code_muni", "geometry"]]


def setores_bh(cod_mun=COD_BH):
    """
    Setores censitários 2022 de um município, com população e domicílios.
    Baixa o GeoPackage de MG uma vez (~180 MB) e filtra só o município.
    """
    caminho = _baixar(URL_SETORES_MG, os.path.join(PASTA_DADOS, "MG_setores_CD2022.gpkg"))
    gdf = gpd.read_file(caminho, where=f"CD_MUN = '{cod_mun}'")
    if gdf.empty:  # caso a coluna tenha sido gravada como número
        gdf = gpd.read_file(caminho, where=f"CD_MUN = {cod_mun}")
    gdf = gdf.rename(columns=VARIAVEIS_SETOR)
    for c in VARIAVEIS_SETOR.values():
        if c in gdf.columns:
            gdf[c] = pd.to_numeric(gdf[c], errors="coerce")
    gdf["em_favela"] = gdf["CD_FCU"].notna() & ~gdf["CD_FCU"].astype(str).isin([".", "", "None", "nan"])
    return gdf.to_crs(CRS_BH)


def metro_bh(caminho=None):
    """Estações da Linha 1 do metrô de BH (coordenadas aproximadas, ver README)."""
    if caminho is None:
        aqui = os.path.dirname(os.path.abspath(__file__))
        caminho = os.path.join(aqui, "..", "dados", "metro_bh_linha1.csv")
    df = pd.read_csv(caminho)
    return gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.lon, df.lat),
                            crs=CRS_WEB).to_crs(CRS_BH)


def osm_feicoes(tags, lugar=None, ponto=None, raio=1500):
    """
    Baixa feições do OpenStreetMap por tags.
    Use lugar="Belo Horizonte, Minas Gerais, Brazil" OU ponto=(lat, lon) com raio em metros.
    """
    import osmnx as ox
    if ponto is not None:
        gdf = ox.features_from_point(ponto, tags=tags, dist=raio)
    else:
        gdf = ox.features_from_place(lugar, tags=tags)
    gdf = gdf.reset_index()
    return gdf.to_crs(CRS_BH)


__all__ = ["COD_BH", "VARIAVEIS_SETOR", "populacao_municipios_sidra", "municipios_mg", "setores_bh",
           "metro_bh", "osm_feicoes"]

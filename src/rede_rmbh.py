"""
rede_rmbh.py — transforma as linhas do sistema de transporte da RMBH num grafo.
Autor: Felipe Almeida (felipe-almeida.com)

Entradas (pasta dados/):
  SIG_Camadas_BNDES/*.gpkg   17 projetos de metrô, VLT e BRT (Mobilidade Brasil, BNDES)
  metro_bh_linha1.csv        19 estações da Linha 1 em operação (posição aproximada)
  nos_nomeados.csv           rótulos dos extremos das linhas, a partir do nome de cada projeto
  conexoes_manuais.csv       extremos que pertencem a uma estação da Linha 1

Lógica:
  1. cada linha vira uma LineString em metros (EPSG:31983);
  2. nós candidatos = estações da Linha 1 + extremos das linhas + cruzamentos entre linhas;
  3. nós a menos de TOL metros uns dos outros são fundidos;
  4. ao longo de cada linha, nós consecutivos viram uma aresta com o comprimento real do trecho.
Trechos usados por mais de uma linha somam a demanda informada pelo BNDES.
"""
import glob
import itertools
import os

import geopandas as gpd
import networkx as nx
import numpy as np
import pandas as pd
from shapely.geometry import LineString, MultiPoint, Point
from shapely.ops import linemerge, nearest_points, substring

from estilo import CRS_BH, CRS_WEB

_AQUI = os.path.dirname(os.path.abspath(__file__))
PASTA_DADOS = os.path.join(_AQUI, "..", "dados")

TOL = 300          # metros: nós mais próximos que isso viram um só
TOL_LINHA = 120    # metros: um nó a essa distância de uma linha passa a pertencer a ela

ABREV = {
    "Extensão do Metrô Linha 1 – Trecho Beatriz": "L1 Beatriz",
    "Implantação do Metrô Linha 2: Ibirité - Barreiro": "L2 Ibirité",
    "Implantação do Metrô Linha 2: Santa Tereza - Calafate": "L2 Calafate",
    "Implantação do Metrô Linha 3: Lagoinha - Savassi": "L3 Savassi",
    "Implantação do Metrô Linha 3: Lagoinha - Morro do Papagaio": "L3 Papagaio",
    "Implantação do Metrô Linha 3: Lagoinha - Belvedere": "L3 Belvedere",
    "Implantação do VLT Linha 4: Eldorado - Betim": "VLT Betim",
    "Implantação do VLT Lagoinha - LMG 806": "VLT LMG-806",
    "Implantação do VLT Lagoinha - Ribeirão das Neves": "VLT Neves",
    "Implantação do VLT Anel Urbano": "VLT Anel",
    "Extensão do BRT Cristiano Machado": "BRT C. Machado",
    "Implantação do BRT Amazonas": "BRT Amazonas",
    "Implantação do BRT Anel Rodoviário": "BRT Anel",
    "Implantação do BRT BR 040 Sul": "BRT 040 Sul",
    "Implantação do BRT 040 Norte: Ribeirão Neves – Ressaca": "BRT 040 Norte",
    "Implantação do BRT Sul: Belvedere - Nova Lima": "BRT Sul",
    "Implantação do BRT Confins - Vilarinho": "BRT Confins",
    "Linha 1 (em operação)": "L1",
}


def _ler(nome, crs_in=CRS_WEB):
    df = pd.read_csv(os.path.join(PASTA_DADOS, nome))
    return gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.lon, df.lat), crs=crs_in).to_crs(CRS_BH)


def carregar_linhas(pasta=None):
    """Lê os 17 projetos do BNDES e acrescenta a Linha 1 em operação."""
    pasta = pasta or os.path.join(PASTA_DADOS, "SIG_Camadas_BNDES")
    proj = pd.concat([gpd.read_file(f) for f in sorted(glob.glob(os.path.join(pasta, "*.gpkg")))],
                     ignore_index=True).to_crs(CRS_BH)
    proj["situacao"] = "projeto"
    est = _ler("metro_bh_linha1.csv").sort_values("ordem")
    l1 = gpd.GeoDataFrame({"ID": [0], "RM": ["RMBH"], "ModoSolucao": ["Metrô"],
                           "NomeLinha": ["Linha 1 (em operação)"], "Ext_km": [np.nan],
                           "Demanda": [np.nan], "situacao": ["operação"]},
                          geometry=[LineString(est.geometry.tolist())], crs=CRS_BH)
    linhas = pd.concat([l1, proj[l1.columns]], ignore_index=True)
    linhas["geometry"] = linhas.geometry.apply(
        lambda g: linemerge(g) if g.geom_type == "MultiLineString" else g)
    linhas["sigla"] = linhas["NomeLinha"].map(ABREV).fillna(linhas["NomeLinha"])
    linhas["modo"] = np.where(linhas["situacao"] == "operação", "Linha 1 (operação)", linhas["ModoSolucao"])
    return gpd.GeoDataFrame(linhas, crs=CRS_BH), est


def _partes(g):
    return list(g.geoms) if g.geom_type == "MultiLineString" else [g]


def construir_rede_rmbh():
    """Retorna (G, nos, arestas, linhas). G é um networkx.Graph com comprimento e demanda nas arestas."""
    linhas, est = carregar_linhas()
    nomeados = _ler("nos_nomeados.csv")
    manuais = _ler("conexoes_manuais.csv")

    # ---- 1. nós candidatos -------------------------------------------------
    cand = [(r.geometry, r.estacao, True) for r in est.itertuples()]          # estações (fixas)
    for g in linhas.geometry:
        for p in _partes(g):
            cand += [(Point(p.coords[0]), None, False), (Point(p.coords[-1]), None, False)]
    for (i, a), (j, b) in itertools.combinations(enumerate(linhas.geometry), 2):
        if a.distance(b) > TOL_LINHA:
            continue
        x = a.intersection(b)
        pts = []
        if not x.is_empty:
            for k in getattr(x, "geoms", [x]):
                if k.geom_type == "Point":
                    pts.append(k)
                elif k.geom_type == "LineString":   # trecho compartilhado: guarda as pontas
                    pts += [Point(k.coords[0]), Point(k.coords[-1])]
        else:  # quase se tocam: ponto mais próximo
            pts.append(nearest_points(a, b)[0])
        cand += [(p, None, False) for p in pts]

    # ---- 2. fundir candidatos próximos ---------------------------------------
    nos = []  # dicts: geometry, nome, fixo
    for geom, nome, fixo in cand:
        # conexões manuais: extremo que pertence a uma estação
        m = manuais[manuais.distance(geom) < TOL]
        if not m.empty:
            nome, fixo = m.iloc[0]["estacao"], True
            geom = est.loc[est.estacao == nome, "geometry"].iloc[0]
        alvo = next((n for n in nos if n["geometry"].distance(geom) < TOL or (nome and n["nome"] == nome)), None)
        if alvo is None:
            nos.append({"geometry": geom, "nome": nome, "fixo": fixo, "pts": [geom]})
        else:
            alvo["pts"].append(geom)
            if fixo and not alvo["fixo"]:
                alvo.update(geometry=geom, nome=nome, fixo=True)
            elif not alvo["fixo"]:
                alvo["geometry"] = MultiPoint(alvo["pts"]).centroid
    nos = gpd.GeoDataFrame(nos, crs=CRS_BH).drop(columns="pts")

    # rótulos dos extremos e das conexões
    for i, r in nos.iterrows():
        if isinstance(r["nome"], str):
            continue
        d = nomeados.distance(r.geometry)
        if d.min() < 600:
            nos.at[i, "nome"] = nomeados.loc[d.idxmin(), "nome"]
    # extremos com o mesmo rótulo (ex.: Belvedere, fim de três linhas) viram um só nó
    rot = nos[nos["nome"].apply(lambda v: isinstance(v, str))]
    unidos = []
    for nome, grupo in rot.groupby("nome"):
        fixo = grupo["fixo"].any()
        geom = grupo.loc[grupo["fixo"], "geometry"].iloc[0] if fixo else MultiPoint(grupo.geometry.tolist()).centroid
        unidos.append({"geometry": geom, "nome": nome, "fixo": fixo})
    nos = pd.concat([nos[~nos.index.isin(rot.index)], gpd.GeoDataFrame(unidos, crs=CRS_BH)],
                    ignore_index=True)
    nos = gpd.GeoDataFrame(nos, crs=CRS_BH)
    nos["id"] = range(len(nos))

    # ---- 3. arestas ao longo de cada linha -----------------------------------
    G = nx.Graph()
    for r in nos.itertuples():
        G.add_node(r.id, x=r.geometry.x, y=r.geometry.y, nome=r.nome if isinstance(r.nome, str) else None)
    registros = []
    for ln in linhas.itertuples():
        for parte in _partes(ln.geometry):
            perto = nos[nos.distance(parte) < max(TOL_LINHA, 1)]
            ext = [nos.distance(Point(parte.coords[0])).idxmin(), nos.distance(Point(parte.coords[-1])).idxmin()]
            pos = {int(nos.at[i, "id"]): parte.project(nos.at[i, "geometry"]) for i in perto.index}
            pos[int(nos.at[ext[0], "id"])] = 0.0
            pos[int(nos.at[ext[1], "id"])] = parte.length
            seq = sorted(pos.items(), key=lambda kv: kv[1])
            for (u, pu), (v, pv) in zip(seq, seq[1:]):
                if u == v or pv - pu < 1:
                    continue
                geom = substring(parte, pu, pv)
                dem = 0.0 if pd.isna(ln.Demanda) else float(ln.Demanda)
                if G.has_edge(u, v):
                    e = G[u][v]
                    e["length"] = min(e["length"], pv - pu)
                    e["linhas"].append(ln.sigla)
                    e["demanda"] += dem
                else:
                    G.add_edge(u, v, length=pv - pu, linhas=[ln.sigla], modo=ln.modo, demanda=dem, geometry=geom)
                registros.append({"de": u, "para": v, "linha": ln.sigla, "modo": ln.modo,
                                  "demanda_linha": dem, "geometry": geom})

    # nós de passagem: sem nome e no meio de um trecho que as mesmas linhas compartilham
    for n in list(G.nodes):
        if G.nodes[n]["nome"] or G.degree(n) != 2:
            continue
        (a, da), (b, db) = [(v, d) for _, v, d in G.edges(n, data=True)]
        if sorted(da["linhas"]) != sorted(db["linhas"]) or a == b or G.has_edge(a, b):
            continue
        ga, gb = da["geometry"], db["geometry"]
        geom = linemerge([ga, gb])
        if geom.geom_type != "LineString":
            geom = LineString(list(ga.coords) + list(gb.coords))
        G.add_edge(a, b, length=da["length"] + db["length"], linhas=da["linhas"], modo=da["modo"],
                   demanda=da["demanda"], geometry=geom)
        G.remove_node(n)
    nos = nos[nos["id"].isin(list(G.nodes))].copy()

    # nós sem nome: identifica pelas linhas que se encontram ali
    for n in G.nodes:
        if not G.nodes[n]["nome"]:
            ls = sorted({l for _, _, d in G.edges(n, data=True) for l in d["linhas"]})
            G.nodes[n]["nome"] = " × ".join(ls[:2]) if len(ls) > 1 else f"{ls[0] if ls else 'nó'} (ponto {n})"
    vistos = {}
    for n in G.nodes:  # nomes repetidos ganham sufixo
        nm = G.nodes[n]["nome"]
        vistos[nm] = vistos.get(nm, 0) + 1
        if vistos[nm] > 1:
            G.nodes[n]["nome"] = f"{nm} ({vistos[nm]})"
    nos["nome"] = nos["id"].map(nx.get_node_attributes(G, "nome"))

    # a partir daqui os nós são chamados pelo nome (mais legível no notebook)
    G = nx.relabel_nodes(G, {n: G.nodes[n]["nome"] for n in G.nodes})
    for n in G.nodes:
        G.nodes[n]["linhas"] = sorted({l for _, _, d in G.edges(n, data=True) for l in d["linhas"]})
    dem = linhas.set_index("sigla")["Demanda"].fillna(0).to_dict()
    for n in G.nodes:  # carga do nó = demanda das linhas que passam por ele
        G.nodes[n]["carga"] = float(sum(dem.get(l, 0) for l in G.nodes[n]["linhas"]))

    nos = nos.set_index("nome").loc[list(G.nodes)].reset_index()
    nos["grau"] = nos["nome"].map(dict(G.degree()))
    nos["carga"] = nos["nome"].map(nx.get_node_attributes(G, "carga"))
    nos["linhas"] = nos["nome"].map(lambda n: ", ".join(G.nodes[n]["linhas"]))
    nos = gpd.GeoDataFrame(nos.drop(columns=["id", "fixo"]), geometry="geometry", crs=CRS_BH)
    arestas = gpd.GeoDataFrame(
        [{"de": u, "para": v, "length": d["length"], "linhas": ", ".join(d["linhas"]),
          "modo": d["modo"], "demanda": d["demanda"], "geometry": d["geometry"]}
         for u, v, d in G.edges(data=True)], crs=CRS_BH)
    return G, nos, arestas, linhas


CORES_MODO = {"Linha 1 (operação)": "#111111", "Metrô": "#38307E", "VLT": "#CFAE6E", "BRT": "#B47C73"}


__all__ = ["carregar_linhas", "construir_rede_rmbh", "ABREV", "CORES_MODO", "TOL", "TOL_LINHA"]

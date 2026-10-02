"""
painel.py — gera o painel HTML interativo (mapa + barra lateral) a partir do grafo.
Autor: Felipe Almeida (felipe-almeida.com)
"""
import json
import os

import geopandas as gpd
import networkx as nx
from shapely.geometry import LineString, Point

from estilo import CRS_BH, CRS_WEB

_AQUI = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(_AQUI, "..", "web", "painel_template.html")
CORES_PADRAO = {"Linha 1 (operação)": "#111111", "Metrô": "#38307E", "VLT": "#CFAE6E", "BRT": "#B47C73"}


def dados_painel(G, crs=CRS_BH, simplificar=40):
    """Converte o grafo num dicionário leve (lat/lon) para HTML."""
    nomes = list(G.nodes)
    pts = gpd.GeoSeries([Point(G.nodes[n]["x"], G.nodes[n]["y"]) for n in nomes], crs=crs).to_crs(CRS_WEB)
    nos = [{"id": n, "lat": round(p.y, 5), "lon": round(p.x, 5),
            "carga": round(G.nodes[n].get("carga", 0)),
            "linhas": ", ".join(G.nodes[n].get("linhas", []))} for n, p in zip(nomes, pts)]
    geoms, arestas = [], []
    for u, v, d in G.edges(data=True):
        g = d.get("geometry") or LineString([(G.nodes[u]["x"], G.nodes[u]["y"]), (G.nodes[v]["x"], G.nodes[v]["y"])])
        geoms.append(g.simplify(simplificar))
        arestas.append({"de": u, "para": v, "len": round(d.get("length", g.length)),
                        "modo": d.get("modo", "Metrô"), "demanda": round(d.get("demanda", 0) or 0),
                        "linhas": ", ".join(d.get("linhas", []))})
    for a, g in zip(arestas, gpd.GeoSeries(geoms, crs=crs).to_crs(CRS_WEB)):
        a["coords"] = [[round(y, 5), round(x, 5)] for x, y, *_ in g.coords]
    return {"nos": nos, "arestas": arestas}


def exportar_painel(G, saida="outputs/painel_rede_rmbh.html", crs=CRS_BH,
                    titulo="Sistema de transporte da RMBH como rede",
                    fonte="BNDES Mobilidade Brasil (projetos); Linha 1 com posição aproximada", cores=None):
    """Escreve um HTML autossuficiente com o mapa da rede e gráficos na barra lateral."""
    dados = dados_painel(G, crs)
    dados.update(titulo=titulo, fonte=fonte, cores=cores or CORES_PADRAO)
    with open(TEMPLATE, encoding="utf-8") as f:
        html = f.read().replace("/*__DADOS__*/null", json.dumps(dados, ensure_ascii=False))
    os.makedirs(os.path.dirname(saida) or ".", exist_ok=True)
    with open(saida, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Painel salvo em {saida}. Abra no navegador.")
    return saida


__all__ = ["exportar_painel", "dados_painel", "CORES_PADRAO"]

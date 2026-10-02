"""
redes.py — funções prontas para a parte de grafos da oficina (networkx).
Autor: Felipe Almeida (felipe-almeida.com)
Adaptado do trabalho LondonTubeNetwork (UCL CASA) para o metrô de BH.

Vocabulário:
    nó (node)    = estação
    aresta (edge)= trecho entre duas estações
    grau (degree)= quantas arestas chegam num nó
"""
import itertools

import geopandas as gpd
import networkx as nx
import numpy as np
import pandas as pd
from shapely.geometry import LineString


def construir_grafo_linha(estacoes, col_nome="estacao", col_ordem="ordem"):
    """
    Cria o grafo de uma linha a partir de um GeoDataFrame de estações (em metros).
    Liga cada estação à seguinte na ordem; o peso da aresta é a distância em metros.
    """
    est = estacoes.sort_values(col_ordem).reset_index(drop=True)
    G = nx.Graph()
    for _, r in est.iterrows():
        G.add_node(r[col_nome], x=r.geometry.x, y=r.geometry.y)
    for a, b in zip(est.itertuples(), est.iloc[1:].itertuples()):
        d = a.geometry.distance(b.geometry)
        G.add_edge(getattr(a, col_nome), getattr(b, col_nome), length=d)
    return G


def posicoes(G):
    """Dicionário {nó: (x, y)} para desenhar o grafo na posição geográfica."""
    return {n: (d["x"], d["y"]) for n, d in G.nodes(data=True)}


def tabela_centralidades(G, peso="length"):
    """Grau, proximidade (closeness) e intermediação (betweenness) de cada nó."""
    tab = pd.DataFrame({
        "grau": dict(G.degree()),
        "closeness": nx.closeness_centrality(G, distance=peso),
        "betweenness": nx.betweenness_centrality(G, weight=peso, normalized=True),
    })
    tab.index.name = "estacao"
    return tab.sort_values("betweenness", ascending=False)


def caminho_mais_longo(G, peso="length"):
    """
    O 'caminho mais longo' útil em redes é o DIÂMETRO: o maior entre todos os
    caminhos mínimos. Retorna (origem, destino, comprimento, caminho).
    """
    comp = dict(nx.all_pairs_dijkstra_path_length(G, weight=peso))
    o, d = max(((a, b) for a in comp for b in comp[a]), key=lambda p: comp[p[0]][p[1]])
    return o, d, comp[o][d], nx.dijkstra_path(G, o, d, weight=peso)


def remocao_de_nos(G, metrica="betweenness", n=5, sequencial=True):
    """
    Remove os n nós mais centrais e mede o efeito na rede:
    número de componentes e tamanho do maior componente conectado.
    sequencial=True recalcula a centralidade após cada remoção.
    """
    funcs = {
        "grau": lambda g: dict(g.degree()),
        "betweenness": lambda g: nx.betweenness_centrality(g, weight="length"),
        "closeness": lambda g: nx.closeness_centrality(g, distance="length"),
    }
    H = G.copy()
    linhas = [{"removidos": 0, "estacao": None, "componentes": nx.number_connected_components(H),
               "maior_componente": len(max(nx.connected_components(H), key=len))}]
    ordem = sorted(funcs[metrica](H).items(), key=lambda kv: kv[1], reverse=True)
    for i in range(1, n + 1):
        if sequencial:
            alvo = max(funcs[metrica](H).items(), key=lambda kv: kv[1])[0]
        else:
            alvo = ordem[i - 1][0]
        H.remove_node(alvo)
        linhas.append({"removidos": i, "estacao": alvo,
                       "componentes": nx.number_connected_components(H),
                       "maior_componente": len(max(nx.connected_components(H), key=len))})
    return pd.DataFrame(linhas)


def matriz_od_gravitacional(G, populacao, beta=1.0, total_viagens=None):
    """
    Modelo gravitacional simples (sem calibração), para fins didáticos:
        T_ij = k * P_i * P_j / d_ij^beta
    populacao: dict {estacao: pessoas no entorno}
    d_ij: distância na rede (metros). total_viagens reescala o resultado.
    """
    dist = dict(nx.all_pairs_dijkstra_path_length(G, weight="length"))
    linhas = []
    for i, j in itertools.permutations(G.nodes(), 2):
        dij = max(dist[i][j], 1.0)
        linhas.append((i, j, populacao.get(i, 0) * populacao.get(j, 0) / dij ** beta))
    od = pd.DataFrame(linhas, columns=["origem", "destino", "fluxo"])
    if total_viagens:
        od["fluxo"] = od["fluxo"] / od["fluxo"].sum() * total_viagens
    return od


def carregar_fluxos(G, od, peso="length"):
    """
    Distribui cada par origem-destino pelo caminho mínimo e soma o fluxo
    em cada aresta. Resultado gravado no atributo 'fluxo' das arestas.
    """
    fluxos = {tuple(sorted(e)): 0.0 for e in G.edges()}
    caminhos = dict(nx.all_pairs_dijkstra_path(G, weight=peso))
    for o, d, f in od[["origem", "destino", "fluxo"]].itertuples(index=False):
        p = caminhos[o][d]
        for u, v in zip(p, p[1:]):
            fluxos[tuple(sorted((u, v)))] += f
    nx.set_edge_attributes(G, {e: fluxos[tuple(sorted(e))] for e in G.edges()}, "fluxo")
    return G


def arestas_gdf(G, crs):
    """Converte as arestas do grafo em GeoDataFrame (linhas) para mapear."""
    pos = posicoes(G)
    reg = [{"de": u, "para": v, **d, "geometry": LineString([pos[u], pos[v]])}
           for u, v, d in G.edges(data=True)]
    return gpd.GeoDataFrame(reg, crs=crs)


__all__ = ["construir_grafo_linha", "posicoes", "tabela_centralidades",
           "caminho_mais_longo", "remocao_de_nos", "matriz_od_gravitacional",
           "carregar_fluxos", "arestas_gdf"]

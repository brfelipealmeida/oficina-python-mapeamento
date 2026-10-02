# Cola da oficina

Felipe Almeida · felipe-almeida.com

## Ler e olhar

| Quero... | Comando |
|---|---|
| ler uma tabela | `pd.read_csv("arquivo.csv")` |
| ler um dado espacial | `gpd.read_file("arquivo.gpkg")` |
| ver as primeiras linhas | `df.head()` |
| ver os tipos das colunas | `df.dtypes` |
| resumo estatístico | `df.describe()` |
| contar vazios | `df.isna().sum()` |
| contar categorias | `df["coluna"].value_counts()` |

## Limpar

| Quero... | Comando |
|---|---|
| texto → número | `pd.to_numeric(df["col"], errors="coerce")` |
| número → código (texto) | `df["cod"].astype("int64").astype(str)` |
| filtrar linhas | `df[df["pessoas"] > 0]` |
| renomear colunas | `df.rename(columns={"v0001": "pessoas"})` |
| tirar duplicados | `df.drop_duplicates("CD_SETOR")` |

## Juntar

| Quero... | Comando |
|---|---|
| join por código | `a.merge(b, on="cod", how="left", validate="one_to_one")` |
| join espacial (dentro) | `gpd.sjoin(pontos, poligonos, predicate="within")` |
| o mais próximo | `gpd.sjoin_nearest(a, b, distance_col="dist_m")` |
| interseção de áreas | `gpd.overlay(a, b, how="intersection")` |

## Geometria

| Quero... | Comando |
|---|---|
| ver a projeção | `gdf.crs` |
| projetar para metros (BH) | `gdf.to_crs("EPSG:31983")` |
| área (m²) | `gdf.area` |
| centróide | `gdf.centroid` |
| buffer de 800 m | `gdf.buffer(800)` |
| unir polígonos | `gdf.dissolve()` |

## Analisar

| Quero... | Comando |
|---|---|
| correlação | `df["a"].corr(df["b"], method="spearman")` |
| regressão | `smf.ols("y ~ x", data=df).fit().summary()` |
| comparar dois grupos | `stats.mannwhitneyu(g1, g2)` |
| cluster de pontos | `DBSCAN(eps=200, min_samples=15).fit_predict(xy)` |

## Grafos

| Quero... | Comando |
|---|---|
| caminho mínimo | `nx.shortest_path(G, a, b, weight="length")` |
| grau | `dict(G.degree())` |
| betweenness | `nx.betweenness_centrality(G, weight="length")` |
| componentes | `nx.number_connected_components(G)` |

## Mapa com créditos

```python
fig, ax = mapa_base()
gdf.plot(ax=ax, column="dens_ha", scheme="quantiles", k=5, cmap=CMAP, legend=True)
barra_escala(ax, 1000); seta_norte(ax)
titulo(ax, "Título que responde à pergunta", "subtítulo com recorte e ano")
creditos(fig, fonte="IBGE, Censo 2022")
salvar(fig, "meu_mapa")
```

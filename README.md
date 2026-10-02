# Python para Mapeamento Urbano

Oficina de 4 horas para estudantes de Arquitetura e Urbanismo: do dado público ao mapa, passando por hipótese, validação, métodos quantitativos, análise espacial, OpenStreetMap e redes.

**Autor:** Felipe Almeida · [felipe-almeida.com](https://felipe-almeida.com/)

Nada precisa ser instalado no computador: tudo roda no **Google Colab**, direto do navegador, com uma conta Google.

| Notebook | Para quê | Abrir |
|---|---|---|
| `01_livecoding.ipynb` | Roteiro completo da oficina, rodado ao vivo | [![Abrir no Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/brfelipealmeida/oficina-python-mapeamento/blob/main/notebooks/01_livecoding.ipynb) |
| `02_pratico_grupo_A_cheios_vazios.ipynb` | Prático do Grupo A | [![Abrir no Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/brfelipealmeida/oficina-python-mapeamento/blob/main/notebooks/02_pratico_grupo_A_cheios_vazios.ipynb) |
| `02_pratico_grupo_B_areas_verdes.ipynb` | Prático do Grupo B | [![Abrir no Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/brfelipealmeida/oficina-python-mapeamento/blob/main/notebooks/02_pratico_grupo_B_areas_verdes.ipynb) |
| `02_pratico_grupo_C_favelas_equipamentos.ipynb` | Prático do Grupo C | [![Abrir no Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/brfelipealmeida/oficina-python-mapeamento/blob/main/notebooks/02_pratico_grupo_C_favelas_equipamentos.ipynb) |
| `web/painel_rede_rmbh.html` | Painel interativo do sistema de transporte da RMBH como rede | baixe e abra no navegador |
| `apresentacao/index.html` | Slides da oficina, interativos | abra no navegador; tecla P exporta PDF |

---

## Programa

| Horário | Bloco |
|---|---|
| 0:00 – 0:35 | Complexidade urbana e trajetória: PELT-MG, mobilidade em Londres, Elizabeth Line |
| 0:35 – 0:55 | Hipótese, validação de dados, correlação e regressão |
| 0:55 – 1:15 | Dados geoespaciais: CRS, tipos de coluna, joins |
| 1:15 – 1:25 | OpenStreetMap e grafos: conceitos |
| 1:25 – 1:35 | Intervalo |
| 1:35 – 2:35 | Live coding no Colab (`01_livecoding.ipynb`) |
| 2:35 – 3:35 | Prático em grupos (`02_pratico_*.ipynb`) |
| 3:35 – 4:00 | Apresentações (6 min por grupo) e fechamento |

## Estrutura

```
oficina-python-mapeamento/
├── README.md
├── requirements.txt          pacotes, para quem quiser rodar fora do Colab
├── notebooks/
│   ├── 01_livecoding.ipynb
│   ├── 02_pratico_grupo_A_cheios_vazios.ipynb
│   ├── 02_pratico_grupo_B_areas_verdes.ipynb
│   └── 02_pratico_grupo_C_favelas_equipamentos.ipynb
├── src/
│   ├── estilo.py             cores, fontes, título, créditos, escala, norte
│   ├── dados.py              download de IBGE (SIDRA e setores), geobr e OSM
│   ├── redes.py              centralidades, caminhos, fragilidade, fluxos
│   ├── rede_rmbh.py          transforma as linhas do BNDES + Linha 1 em grafo
│   └── painel.py             gera o painel HTML a partir do grafo
├── dados/
│   ├── SIG_Camadas_BNDES/    17 projetos de metrô, VLT e BRT da RMBH + metadados
│   ├── metro_bh_linha1.csv   19 estações da Linha 1 em operação (posição aproximada)
│   ├── nos_nomeados.csv      nome dos extremos de cada linha
│   └── conexoes_manuais.csv  extremos que pertencem a uma estação da Linha 1
├── apresentacao/
│   ├── index.html            slides em HTML (interativos; P exporta PDF)
│   ├── modelo.html           slides novos, editáveis
│   ├── gerar_apresentacao.py junta o PDF original, os slides novos e a rede
│   └── fonte/                PDF original da apresentação
├── web/
│   ├── painel_template.html  modelo do painel (mapa + barra lateral)
│   └── painel_rede_rmbh.html painel pronto para abrir no navegador
├── docs/
│   └── cola.md               resumo dos comandos da oficina
└── outputs/                  onde os notebooks salvam mapas e gráficos
```

## Como usar

**No Colab (recomendado).** Clique no botão "Abrir no Colab" do notebook e depois em *Arquivo › Salvar uma cópia no Drive*. Rode as células em ordem com `Shift + Enter`. A primeira célula instala os pacotes e baixa este repositório; ela precisa rodar a cada nova sessão.

**Salvar os resultados.** A última seção do live coding copia a pasta `outputs/` para `Meu Drive/oficina_python_mapeamento/`.

**No computador.** Com Python 3.10 ou mais recente:

```bash
git clone https://github.com/brfelipealmeida/oficina-python-mapeamento.git
cd oficina-python-mapeamento
pip install -r requirements.txt
jupyter lab
```

Nos notebooks, ignore as linhas que começam com `!` e ajuste o `sys.path` para `src`.

## Dados

| Dado | Fonte | Como chega |
|---|---|---|
| População por município, 2022 | IBGE, SIDRA, tabela 4714 | API, função `populacao_municipios_sidra()` |
| Limites municipais de MG | IBGE via `geobr` (IPEA); alternativa: API de malhas do IBGE | `municipios_mg()` |
| Setores censitários 2022 com população, domicílios e Favelas e Comunidades Urbanas | IBGE, Malha de Setores com atributos (`MG_setores_CD2022.gpkg`, ~180 MB) | `setores_bh()` |
| Edificações, uso do solo, áreas verdes, equipamentos, ruas | OpenStreetMap via `osmnx` | `osm_feicoes()` e `ox.graph_from_point()` |
| Projetos de metrô, VLT e BRT da RMBH | BNDES, portal Mobilidade Brasil (exportação de 02/10/2026) | `dados/SIG_Camadas_BNDES/`, função `construir_rede_rmbh()` |
| Estações da Linha 1 em operação | `dados/metro_bh_linha1.csv` | posição **aproximada**; substituir pela camada oficial quando disponível |

Variáveis da malha de setores (dicionário do IBGE): `v0001` pessoas, `v0002` domicílios, `v0003` domicílios particulares, `v0004` domicílios coletivos, `v0005` média de moradores, `v0006` percentual de domicílios imputados, `v0007` domicílios particulares ocupados. A função `setores_bh()` já renomeia essas colunas.

A **demanda** usada na análise de redes é a estimativa publicada pelo BNDES para cada projeto (confira a unidade na fonte). Trechos usados por várias linhas somam as demandas. A Linha 1 em operação não tem demanda nessa base e entra com zero.

Como os arquivos do BNDES trazem linhas, e não estações, os nós do grafo são os extremos de cada linha e os cruzamentos entre linhas (pontos a menos de 300 m são fundidos). As decisões manuais ficam registradas em `nos_nomeados.csv` e `conexoes_manuais.csv`. O trecho Ibirité–Barreiro aparece isolado porque o projeto que o liga ao restante da Linha 2 não está entre os 17.

## Créditos nos produtos

Todo mapa e gráfico chama `creditos(fig, fonte=...)`, que escreve no rodapé:

> Elaboração: Felipe Almeida (felipe-almeida.com) | Fonte: ...

Para mudar a identidade visual inteira (por exemplo, para a paleta de outro projeto), edite apenas o dicionário `CORES` em `src/estilo.py`.

## Apresentação

`apresentacao/index.html` é um arquivo único: abre offline (o mapa do slide de buffer precisa de internet). Teclas: ← → navegam, F tela cheia, N notas, P imprime. Para PDF: P › Salvar como PDF, margens Nenhuma, gráficos de fundo ativados.

Para editar, mude `apresentacao/modelo.html` (slides novos) ou troque o PDF em `apresentacao/fonte/` e rode `python apresentacao/gerar_apresentacao.py` (requer `pip install pymupdf`).

## Prático em grupos

Três grupos de cinco pessoas, uma base por grupo. Cada grupo entrega:

1. uma pergunta e uma hipótese (H1 e H0);
2. o dado limpo e validado;
3. um método espacial (buffer, join espacial, distância, cluster ou grade);
4. um método quantitativo (correlação, regressão ou comparação de grupos);
5. um mapa e um gráfico com créditos;
6. três frases de conclusão, incluindo um limite da análise.

| Grupo | Tema | Dados |
|---|---|---|
| A | Cheios, vazios e uso do solo | OSM: edificações e uso do solo em recortes de BH |
| B | Áreas verdes e densidade | Censo 2022 por setor + áreas verdes do OSM |
| C | Favelas e comunidades urbanas e equipamentos | Censo 2022 (setores em FCU) + escolas e saúde do OSM |

## Para ir além

- Trabalhos do autor que inspiraram a oficina: [LondonTubeNetwork](https://github.com/brfelipealmeida/LondonTubeNetwork) (resiliência de redes), [LondonMobilityFlows](https://github.com/brfelipealmeida/LondonMobilityFlows) (fluxos de mobilidade) e [BraCoChi](https://github.com/brfelipealmeida/BraCoChi) (Elizabeth Line e mercado de aluguel).
- Batty, M. (2013). *The New Science of Cities*. MIT Press.
- Clark, C. (1951). Urban population densities. *Journal of the Royal Statistical Society A*, 114(4).
- Boeing, G. (2017). OSMnx: New methods for acquiring, constructing, analyzing, and visualizing complex street networks. *Computers, Environment and Urban Systems*, 65.
- Documentação: [geopandas](https://geopandas.org), [osmnx](https://osmnx.readthedocs.io), [networkx](https://networkx.org), [geobr](https://github.com/ipeaGIT/geobr).

## Licença

Código sob licença MIT. Ao reutilizar mapas e gráficos, mantenha o crédito de autoria e a fonte dos dados.

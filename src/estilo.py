"""
estilo.py — identidade visual da oficina "Python para Mapeamento Urbano"
Autor: Felipe Almeida (felipe-almeida.com)

Tudo que for plotado na oficina passa por aqui:

    from estilo import *
    configurar_estilo()
    fig, ax = mapa_base()
    ...
    titulo(ax, "Título", "subtítulo")
    creditos(fig, fonte="IBGE, Censo 2022")
    salvar(fig, "meu_mapa")

Para trocar a paleta (por exemplo, pela do PELT-MG), edite apenas o dicionário CORES.
"""
import os
import urllib.request

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.colors import LinearSegmentedColormap

AUTOR = "Felipe Almeida"
SITE = "felipe-almeida.com"

CRS_BH = "EPSG:31983"   # SIRGAS 2000 / UTM 23S: metros, adequado para BH
CRS_GEO = "EPSG:4674"   # SIRGAS 2000 geográfico (graus): padrão do IBGE
CRS_WEB = "EPSG:4326"   # WGS84: padrão do OpenStreetMap e do folium

CORES = {
    "tinta": "#1E2233",        # texto e contornos fortes
    "papel": "#FFFFFF",        # fundo dos mapas
    "cinza": "#8E949C",        # elementos secundários
    "cinza_claro": "#E3E5E8",  # base, vizinhos, vazios
    "roxo": "#5B2A86",         # cor-assinatura (dado principal)
    "lilas": "#B9A3D9",        # dado secundário
    "verde": "#2F7A55",        # áreas verdes
    "minerio": "#C98A1B",      # destaque: metrô, rotas, nós críticos
}

# Rampa sequencial (pouco -> muito) e divergente (abaixo -> acima da referência)
CMAP = LinearSegmentedColormap.from_list(
    "felipe_seq", ["#F3EFF8", "#B9A3D9", "#5B2A86", "#2A1240"])
CMAP_DIV = LinearSegmentedColormap.from_list(
    "felipe_div", ["#C98A1B", "#F1E3C4", "#F5F5F5", "#D9CCEB", "#5B2A86"])
for _c in (CMAP, CMAP_DIV):
    try:
        mpl.colormaps.register(_c)
    except ValueError:
        pass  # já registrado nesta sessão

_FONTES = {
    "BarlowCondensed-SemiBold.ttf": "barlowcondensed",
    "BarlowCondensed-Regular.ttf": "barlowcondensed",
    "Barlow-Regular.ttf": "barlow",
    "Barlow-Medium.ttf": "barlow",
}
_PASTA_FONTES = os.path.join(os.path.expanduser("~"), ".fontes_oficina")


def _instalar_fontes():
    """Baixa a família Barlow (Google Fonts, licença OFL) e registra no matplotlib."""
    os.makedirs(_PASTA_FONTES, exist_ok=True)
    for arq, pasta in _FONTES.items():
        destino = os.path.join(_PASTA_FONTES, arq)
        if not os.path.exists(destino):
            url = f"https://raw.githubusercontent.com/google/fonts/main/ofl/{pasta}/{arq}"
            try:
                urllib.request.urlretrieve(url, destino)
            except Exception:
                continue  # sem internet: cai para a fonte padrão
        font_manager.fontManager.addfont(destino)


def _tem_fonte(nome):
    return nome in {f.name for f in font_manager.fontManager.ttflist}


def configurar_estilo():
    """Aplica fontes, cores e tamanhos padrão a todos os gráficos da sessão."""
    _instalar_fontes()
    mpl.rcParams.update({
        "font.family": "Barlow" if _tem_fonte("Barlow") else "DejaVu Sans",
        "font.size": 10,
        "text.color": CORES["tinta"],
        "axes.labelcolor": CORES["tinta"],
        "axes.edgecolor": CORES["cinza"],
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": False,
        "axes.prop_cycle": mpl.cycler(color=[CORES[c] for c in
                                             ("roxo", "minerio", "verde", "lilas", "cinza")]),
        "xtick.color": CORES["cinza"],
        "ytick.color": CORES["cinza"],
        "xtick.labelcolor": CORES["tinta"],
        "ytick.labelcolor": CORES["tinta"],
        "figure.facecolor": CORES["papel"],
        "axes.facecolor": CORES["papel"],
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
        "legend.frameon": False,
    })


def titulo(ax, texto, subtitulo=None):
    """Título condensado, alinhado à esquerda, com subtítulo opcional."""
    fam = "Barlow Condensed" if _tem_fonte("Barlow Condensed") else None
    ax.text(0, 1.07 if subtitulo else 1.02, texto, transform=ax.transAxes,
            fontsize=20, fontweight="semibold", family=fam, va="bottom",
            color=CORES["tinta"])
    if subtitulo:
        ax.text(0, 1.015, subtitulo, transform=ax.transAxes, fontsize=11,
                color=CORES["cinza"], va="bottom")


def creditos(fig, fonte="", nota=""):
    """Rodapé obrigatório em todo produto da oficina: autoria + fonte dos dados."""
    partes = [f"Elaboração: {AUTOR} ({SITE})"]
    if fonte:
        partes.append(f"Fonte: {fonte}")
    if nota:
        partes.append(nota)
    # posiciona logo abaixo de tudo o que foi desenhado (inclui rótulos dos eixos)
    y0, x1 = 0.02, 0.99
    if fig.axes:
        rend = fig.canvas.get_renderer()
        caixas = []
        for a in fig.axes:
            a.apply_aspect()
            caixas.append(a.get_tightbbox(rend).transformed(fig.transFigure.inverted()))
        y0 = min(c.y0 for c in caixas)
        x1 = max(min(c.x1, 1.0) for c in caixas)
    fig.text(x1, y0 - 0.012, "   |   ".join(partes), ha="right", va="top",
             fontsize=7.5, color=CORES["cinza"])


def mapa_base(figsize=(9, 9)):
    """Figura limpa para mapas: sem eixos, aspecto 1:1."""
    fig, ax = plt.subplots(figsize=figsize)
    ax.set_axis_off()
    ax.set_aspect("equal")
    return fig, ax


def barra_escala(ax, comprimento_m=1000, loc=(0.05, 0.04)):
    """Barra de escala simples. Só faz sentido com CRS em metros (ex.: CRS_BH)."""
    x0, x1 = ax.get_xlim()
    y0, y1 = ax.get_ylim()
    x = x0 + (x1 - x0) * loc[0]
    y = y0 + (y1 - y0) * loc[1]
    ax.plot([x, x + comprimento_m], [y, y], color=CORES["tinta"], lw=3,
            solid_capstyle="butt")
    rotulo = f"{comprimento_m / 1000:g} km" if comprimento_m >= 1000 else f"{comprimento_m} m"
    ax.text(x + comprimento_m / 2, y + (y1 - y0) * 0.012, rotulo,
            ha="center", va="bottom", fontsize=8)


def seta_norte(ax, loc=(0.95, 0.90)):
    """Seta de norte (assume CRS sem rotação, como UTM ou lat/lon)."""
    ax.annotate("N", xy=(loc[0], loc[1] + 0.06), xytext=(loc[0], loc[1]),
                xycoords="axes fraction", textcoords="axes fraction",
                ha="center", va="top", fontsize=11, fontweight="bold",
                color=CORES["tinta"],
                arrowprops=dict(arrowstyle="-|>", color=CORES["tinta"], lw=1.5))


def salvar(fig, nome, pasta="outputs"):
    """Salva PNG (300 dpi) e SVG. O SVG abre no Illustrator/Inkscape para pranchas."""
    os.makedirs(pasta, exist_ok=True)
    for ext in ("png", "svg"):
        fig.savefig(os.path.join(pasta, f"{nome}.{ext}"))
    print(f"Salvo: {pasta}/{nome}.png e {pasta}/{nome}.svg")


def creditos_folium(mapa, fonte=""):
    """Adiciona a autoria no canto de um mapa interativo do folium."""
    import folium
    texto = f"Elaboração: {AUTOR}" + (f" | Fonte: {fonte}" if fonte else "")
    html = ('<div style="position:fixed;bottom:10px;left:10px;z-index:9999;'
            'background:rgba(255,255,255,.88);padding:4px 8px;'
            f'font:12px sans-serif;color:{CORES["tinta"]}">{texto}</div>')
    mapa.get_root().html.add_child(folium.Element(html))
    return mapa


__all__ = ["AUTOR", "SITE", "CRS_BH", "CRS_GEO", "CRS_WEB", "CORES", "CMAP", "CMAP_DIV",
           "configurar_estilo", "titulo", "creditos", "mapa_base", "barra_escala",
           "seta_norte", "salvar", "creditos_folium"]

"""
gerar_apresentacao.py — monta apresentacao/index.html
Autor: Felipe Almeida (felipe-almeida.com)

Junta três coisas num único arquivo HTML (abre em qualquer navegador, P exporta PDF):
  1. as páginas do PDF original (fonte/Introdução_ao_Python_para_Mapeamento.pdf), como imagens;
  2. os slides novos de modelo.html (método, dados geoespaciais, redes, prática);
  3. os dados da rede da RMBH, calculados por src/rede_rmbh.py.

Uso:  pip install pymupdf   e depois   python apresentacao/gerar_apresentacao.py
Para mudar a ordem ou retirar páginas do PDF, edite INICIO, MEIO e FIM abaixo (números de página).
"""
import base64
import io
import json
import os
import sys

import pymupdf
from PIL import Image

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, "..", "src"))
from painel import dados_painel, CORES_PADRAO  # noqa: E402
from rede_rmbh import construir_rede_rmbh      # noqa: E402

PDF = os.path.join(AQUI, "fonte", "Introdução_ao_Python_para_Mapeamento.pdf")
INICIO = [1, 3]                  # capa e perfil (a página 2 está vazia; a 4 virou um slide novo)
MEIO = list(range(6, 42))        # seções 1 a 3 (a página 5 é substituída pela agenda completa)
FIM = [42, 43]                   # "Pra resumir" e "Obrigado"

# links que aparecem nos avisos, no live coding e no slide de dúvidas
LINK_DRIVE = "https://drive.google.com/drive/folders/1zL4poL9-Me2brC9LQNTxk-BN6XKtgykj"
LINK_GITHUB = "https://github.com/brfelipealmeida/oficina-python-mapeamento"


def qr_svg(texto):
    """QR code em SVG (pip install qrcode). Sem o pacote, mostra só o link."""
    try:
        import qrcode
        import qrcode.image.svg
    except ImportError:
        return f'<p class="link">{texto}</p>'
    img = qrcode.make(texto, image_factory=qrcode.image.svg.SvgPathImage, border=1)
    svg = img.to_string(encoding="unicode")
    return svg[svg.index("<svg"):]


def paginas(doc, numeros, largura=1600, qualidade=80):
    html = []
    for n in numeros:
        p = doc[n - 1]
        z = largura / p.rect.width
        pix = p.get_pixmap(matrix=pymupdf.Matrix(z, z))
        im = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=qualidade, optimize=True)
        b64 = base64.b64encode(buf.getvalue()).decode()
        html.append(f'<section class="slide img"><img alt="Página {n} da apresentação original" '
                    f'src="data:image/jpeg;base64,{b64}"></section>')
    return "\n".join(html)


def main():
    with open(os.path.join(AQUI, "modelo.html"), encoding="utf-8") as f:
        html = f.read()
    doc = pymupdf.open(PDF)
    html = (html.replace("<!--__PDF_INICIO__-->", paginas(doc, INICIO))
                .replace("<!--__PDF_MEIO__-->", paginas(doc, MEIO))
                .replace("<!--__PDF_FIM__-->", paginas(doc, FIM)))
    G, *_ = construir_rede_rmbh()
    rede = dados_painel(G)
    rede["cores"] = CORES_PADRAO
    html = html.replace("/*__REDE__*/null", json.dumps(rede, ensure_ascii=False))
    html = (html.replace("__QR_DRIVE__", qr_svg(LINK_DRIVE))
                .replace("__LINK_DRIVE__", LINK_DRIVE)
                .replace("__LINK_GITHUB__", LINK_GITHUB))
    saida = os.path.join(AQUI, "index.html")
    with open(saida, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Apresentação salva em {saida} ({os.path.getsize(saida) / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()

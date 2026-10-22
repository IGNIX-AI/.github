"""Monta a página do projeto a partir de docs/.

Gera docs/README.md (índice completo) e atualiza a seção "Documentação" do README.md da raiz,
entre os marcadores <!-- docs:inicio --> e <!-- docs:fim -->. Usa a data do último commit de cada arquivo.

Uso: python pagina-projeto.py [pasta-do-repositorio]
"""
import re
import subprocess
import sys
from pathlib import Path

INICIO, FIM = "<!-- docs:inicio -->", "<!-- docs:fim -->"
ORDEM = ["visao-geral", "requisitos", "arquitetura", "dados", "api", "como-rodar", "entregas", "glossario"]


def data_commit(raiz, arquivo):
    r = subprocess.run(["git", "log", "-1", "--format=%cs", "--", str(arquivo)], cwd=raiz,
                       capture_output=True, text=True, encoding="utf-8")
    d = r.stdout.strip()
    return f"{d[8:10]}/{d[5:7]}/{d[0:4]}" if d else "não publicado"


def ler(arquivo):
    titulo, resumo = arquivo.stem.replace("-", " ").capitalize(), ""
    for linha in arquivo.read_text(encoding="utf-8").splitlines():
        l = linha.strip()
        if l.startswith("# ") and titulo == arquivo.stem.replace("-", " ").capitalize():
            titulo = l[2:].strip()
        elif l and not l.startswith(("#", ">", "|", "```", "<!--", "-", "*")) and not resumo:
            resumo = re.sub(r"[*`_]", "", l)
            resumo = re.sub(r"\s*Atualizado em \d{2}/\d{2}/\d{4}\.?", "", resumo).strip()
            resumo = resumo if len(resumo) <= 140 else resumo[:137].rsplit(" ", 1)[0] + "…"
    return titulo, resumo


def chave(arquivo):
    return (ORDEM.index(arquivo.stem) if arquivo.stem in ORDEM else len(ORDEM), arquivo.name)


def tabela(raiz, arquivos, base):
    linhas = ["| Documento | Resumo | Atualizado |", "|---|---|---|"]
    for a in arquivos:
        titulo, resumo = ler(a)
        link = a.relative_to(base).as_posix()
        linhas.append(f"| [{titulo}]({link}) | {resumo} | {data_commit(raiz, a)} |")
    return "\n".join(linhas)


def main():
    raiz = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    docs = raiz / "docs"
    if not docs.is_dir():
        print("sem docs/, nada a fazer")
        return
    principais = sorted((a for a in docs.glob("*.md") if a.name != "README.md"), key=chave)
    decisoes = sorted((docs / "decisoes").glob("[0-9]*.md")) if (docs / "decisoes").is_dir() else []
    projeto = ler(raiz / "README.md")[0] if (raiz / "README.md").exists() else raiz.name

    indice = [f"# Documentação · {projeto}", "",
              "Página gerada automaticamente a partir dos arquivos desta pasta. Não edite à mão: "
              "altere os documentos e o índice se atualiza no próximo push na `main`.", ""]
    indice += ["## Documentos", "", tabela(raiz, principais, docs) if principais else "_Nenhum documento ainda._", ""]
    if decisoes:
        indice += ["## Decisões técnicas (ADRs)", "", tabela(raiz, decisoes, docs), ""]
    (docs / "README.md").write_text("\n".join(indice), encoding="utf-8")

    readme = raiz / "README.md"
    if not readme.exists():
        return
    secao = [INICIO, "## Documentação", "",
             "Arquitetura, decisões e guias técnicos ficam em [`docs/`](docs/README.md). Esta seção é atualizada "
             "automaticamente a cada push na `main`.", ""]
    secao += [tabela(raiz, principais, raiz) if principais else "_Nenhum documento ainda._", ""]
    if decisoes:
        qtd = "1 registrada" if len(decisoes) == 1 else f"{len(decisoes)} registradas"
        secao += [f"**Decisões técnicas:** {qtd}, a mais recente "
                  f"[{ler(decisoes[-1])[0]}]({decisoes[-1].relative_to(raiz).as_posix()}).", ""]
    secao.append(FIM)
    bloco = "\n".join(secao)
    texto = readme.read_text(encoding="utf-8")
    if INICIO in texto and FIM in texto:
        texto = re.sub(re.escape(INICIO) + r".*?" + re.escape(FIM), lambda _: bloco, texto, flags=re.S)
    elif "\n## Como trabalhar" in texto:
        texto = texto.replace("\n## Como trabalhar", "\n" + bloco + "\n\n## Como trabalhar", 1)
    else:
        texto = texto.rstrip() + "\n\n" + bloco + "\n"
    readme.write_text(texto, encoding="utf-8")
    print(f"página atualizada: {len(principais)} documentos, {len(decisoes)} decisões")


if __name__ == "__main__":
    main()

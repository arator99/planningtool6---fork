#genereer_architectuur.py

import os
import re

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
UITBESTAND = os.path.join(PROJECT_ROOT, "architectuur.py")
UITGESLOTEN_MAPPEN = {".venv", "__pycache__", ".git", "data"}

def verzamel_bestanden(pad):
    structuur = {}
    for root, dirs, files in os.walk(pad):
        dirs[:] = [d for d in dirs if d not in UITGESLOTEN_MAPPEN]
        rel_pad = os.path.relpath(root, PROJECT_ROOT)
        if rel_pad == ".":
            rel_pad = "root"

        py_bestanden = [f for f in files if f.endswith(".py") and f != os.path.basename(__file__)]
        if py_bestanden:
            structuur[rel_pad] = py_bestanden
    return structuur

def lees_samenvatting(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            inhoud = f.read()
            match = re.search(r'"""(.*?)"""', inhoud, re.DOTALL)
            if match:
                return match.group(1).strip().replace("\n", " ")
            lines = inhoud.splitlines()
            comments = [line.strip("# ").strip() for line in lines if line.strip().startswith("#")]
            if comments:
                return comments[0]
    except Exception:
        return None
    return None

def detecteer_imports(filepath):
    imports = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("import ") or line.startswith("from "):
                    imports.append(line)
    except Exception:
        pass
    return imports

def detecteer_functies_en_methodes(filepath):
    functies = []
    methodes = {}
    huidige_klasse = None
    indent_stack = []

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                stripped = line.strip()
                if stripped.startswith("class "):
                    match = re.match(r"class\s+([a-zA-Z_][a-zA-Z0-9_]*)", stripped)
                    if match:
                        huidige_klasse = match.group(1)
                        methodes[huidige_klasse] = []
                        indent_stack.append(len(line) - len(line.lstrip()))
                elif stripped.startswith("def "):
                    match = re.match(r"def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\((.*?)\)\s*:", stripped)
                    if match:
                        naam = match.group(1)
                        params = match.group(2)
                        indent = len(line) - len(line.lstrip())
                        if huidige_klasse and indent > indent_stack[-1]:
                            methodes[huidige_klasse].append(f"{naam}({params})")
                        else:
                            functies.append(f"{naam}({params})")
                            huidige_klasse = None
                            indent_stack = []
    except Exception:
        pass

    return functies, methodes

def schrijf_architectuur(structuur):
    with open(UITBESTAND, "w", encoding="utf-8") as f:
        f.write('"""\n')
        f.write("Automatisch gegenereerd architectuuroverzicht\n\n")
        f.write("Projectstructuur:\n")
        f.write("------------------\n\n")

        for mapnaam, bestanden in structuur.items():
            f.write(f"{mapnaam}/\n")
            for bestand in bestanden:
                pad = os.path.join(PROJECT_ROOT, mapnaam if mapnaam != "root" else "", bestand)
                samenvatting = lees_samenvatting(pad)
                imports = detecteer_imports(pad)
                functies, methodes = detecteer_functies_en_methodes(pad)

                f.write(f"    - {bestand}\n")
                if samenvatting:
                    f.write(f"        Beschrijving: {samenvatting}\n")
                if imports:
                    f.write(f"        Imports:\n")
                    for imp in imports:
                        f.write(f"            {imp}\n")
                if functies:
                    f.write(f"        Functies:\n")
                    for func in functies:
                        f.write(f"            {func}\n")
                if methodes:
                    f.write(f"        Klassen & Methodes:\n")
                    for klasse, methoden in methodes.items():
                        f.write(f"            class {klasse}:\n")
                        for methode in methoden:
                            f.write(f"                {methode}\n")
                f.write("\n")

        f.write("Beschrijving:\n")
        f.write("-------------\n")
        f.write("Voeg hier handmatig uitleg toe over modules, datastromen, en verantwoordelijkheden.\n")
        f.write('"""\n')

    print(f"Architectuuroverzicht opgeslagen in: {UITBESTAND}")

if __name__ == "__main__":
    structuur = verzamel_bestanden(PROJECT_ROOT)
    schrijf_architectuur(structuur)

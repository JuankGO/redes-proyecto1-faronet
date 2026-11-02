"""Genera tablas y compila los documentos LaTeX de FaroNet con Tectonic.

Uso: python tools/generar_documentacion.py --tectonic RUTA_AL_EJECUTABLE
Las fuentes principales estan en docs/latex; no se publica ni se utiliza GPIO.
"""
import argparse
from pathlib import Path
import re
import shutil
import subprocess

from montaje_faro import main as generar_montaje

ROOT=Path(__file__).resolve().parents[1]
LATEX=ROOT/'docs/latex'
TABLES=LATEX/'tablas'


def escapar(value):
    value=value.replace('**','').replace('`','')
    mapping={'\\':r'\textbackslash{}','&':r'\&','%':r'\%','$':r'\$',
             '#':r'\#','_':r'\_','{':r'\{','}':r'\}',
             '~':r'\textasciitilde{}','^':r'\textasciicircum{}'}
    return ''.join(mapping.get(c,c) for c in value)


def tablas_md(path):
    tables=[]; current=[]
    for line in path.read_text(encoding='utf-8').splitlines()+['']:
        if line.startswith('|'):
            cells=[s.strip() for s in line.strip().strip('|').split('|')]
            if all(re.fullmatch(r':?-+:?',c) for c in cells): continue
            current.append(cells)
        elif current:
            tables.append(current); current=[]
    return tables


def longtable(columns,headers,rows,size=r'\small'):
    out=['{'+size,r'\begin{longtable}{'+columns+'}',r'\toprule',
         ' & '.join(escapar(s) for s in headers)+r'\\',r'\midrule\endhead']
    out += [' & '.join(escapar(s) for s in row)+r'\\' for row in rows]
    out += [r'\bottomrule',r'\end{longtable}}']
    return '\n'.join(out)+'\n'


def preparar_tablas(actualizar_commits=False):
    TABLES.mkdir(parents=True,exist_ok=True)
    material=tablas_md(ROOT/'docs/hardware/BOM.md')[0][1:]
    rows=[]
    for ref,name,_,quantity,price,total in material:
        label=('TOTAL' if ref=='TOTAL' else ref+': '+name)
        rows.append([label,quantity,price,total])
    (TABLES/'materiales.tex').write_text(longtable('P{8.5cm} r r r',
        ['Material','Cantidad','CRC / unidad','Subtotal CRC'],rows),encoding='utf-8')

    hours=tablas_md(ROOT/'docs/bitacora/horas.md')
    for label,table in [('jimmy',hours[0]),('juan',hours[1])]:
        (TABLES/f'horas-{label}.tex').write_text(longtable('P{2.1cm} P{10.8cm} r',
            ['Fecha estimada','Actividad','Horas'],table[1:]),encoding='utf-8')

    target=TABLES/'commits.tex'
    if actualizar_commits or not target.exists():
        log=subprocess.check_output(['git','log','--all','--date=short',
            '--format=%h\t%ad\t%an\t%s'],cwd=ROOT).decode('utf-8')
        rows=[]
        for line in log.splitlines():
            sha,date,author,subject=line.split('\t',3)
            author='Juan' if author=='JuankGO' else 'Jimmy' if author.startswith('Jimmy') else author
            rows.append([sha,date,author,subject])
        target.write_text(longtable('P{1.3cm} P{1.8cm} P{1.2cm} P{9.3cm}',
            ['Commit','Fecha','Autor','Descripción'],rows,r'\footnotesize'),encoding='utf-8')


def preparar_rfc():
    path=ROOT/'docs/rfc/rfc-faronet.txt'
    source=path.read_text(encoding='ascii')
    source=re.sub(r'^RFC 9999[^\n]*\n','',source,flags=re.M)
    source=re.sub(r'^Castillo Guzman & Gomez[^\n]*\n?','',source,flags=re.M)
    if source.startswith('Grupo de Trabajo:'):
        source=source.split('\n\n',1)[1].lstrip('\n')
    source=re.sub(r'^   (?:Agradecimientos|Direcciones de los autores)[^\n]*\n','',source,flags=re.M)
    if '\nAgradecimientos\n' in source:
        source=source.split('\nAgradecimientos\n',1)[0]+'\n'
    pages=[page.strip('\n') for page in source.split('\f')]
    source='\n\f\n'.join(pages)+'\n'
    source.encode('ascii')
    path.write_text(source,encoding='ascii',newline='\n')
    body=[]
    for i,page in enumerate(pages):
        if i: body.append(r'\newpage')
        body.extend([r'\begin{Verbatim}',page,r'\end{Verbatim}'])
    (TABLES/'rfc-cuerpo.tex').write_text('\n'.join(body)+'\n',encoding='ascii',newline='\n')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tectonic',default=shutil.which('tectonic'))
    parser.add_argument('--solo-fuentes',action='store_true',help='No ejecutar el compilador')
    parser.add_argument('--actualizar-commits',action='store_true')
    args=parser.parse_args()
    generar_montaje()
    preparar_tablas(args.actualizar_commits)
    preparar_rfc()
    if args.solo_fuentes:
        print('Fuentes LaTeX y figura preparadas.')
        return
    if not args.tectonic:
        parser.error('Instalar Tectonic o indicar --tectonic RUTA; tambien se puede compilar con XeLaTeX.')
    executable=shutil.which(args.tectonic) or str(Path(args.tectonic).resolve())
    build=ROOT/'.latex-build'; build.mkdir(exist_ok=True)
    out=ROOT/'output/pdf'; out.mkdir(parents=True,exist_ok=True)
    for name,target in [('documentacion','FaroNet-documentacion.pdf'),('rfc','FaroNet-RFC.pdf')]:
        subprocess.run([executable,'--keep-logs','--outdir',str(build),name+'.tex'],
                       cwd=LATEX,check=True)
        shutil.copyfile(build/(name+'.pdf'),out/target)
        print('Generado:',(out/target).relative_to(ROOT))


if __name__=='__main__': main()

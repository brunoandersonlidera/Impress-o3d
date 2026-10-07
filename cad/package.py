"""Empacota os arquivos finais; executar após build.py e check_stl.py."""
from pathlib import Path
import json, csv, zipfile, hashlib

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'exports'

def color_name(rgb):
    r,g,b=rgb
    if max(abs(a-b) for a,b in zip(rgb,(63/255,64/255,150/255)))<.001:return 'violeta_azulado'
    if min(rgb)>.8:return 'branco'
    if r>.8:return 'coral' if b>.15 else 'laranja'
    if g>.5:return 'ciano'
    return 'azul_muito_escuro' if b<.12 else 'azul_marinho'

def main():
    cad=json.loads((OUT/'validacao.json').read_text())
    mesh=json.loads((OUT/'validacao_STL.json').read_text())
    brand=json.loads((OUT/'validacao_logo.json').read_text())
    joints=json.loads((OUT/'validacao_articulacoes.json').read_text())
    motion=json.loads((OUT/'movimento_local.json').read_text())
    exploded=json.loads((OUT/'validacao_explodido.json').read_text())
    assert cad['all_valid'] and cad['step_reimport_valid'] and not cad['overlaps']
    assert all(t['unobstructed'] for t in cad['bore_tests'])
    assert mesh['all_closed'] and mesh['all_fit_A1'] and mesh['all_on_bed']
    assert all(p['supported_by_chest'] and p['volume_error_mm3']<1e-6 for p in brand['paths'])
    assert all(joints[k] for k in ('all_washers_supported','all_tools_accessible','all_nuts_engaged'))
    assert motion['all_13_joints_checked'] and not motion['zero_pose_collision_pairs'] and not motion['boolean_errors']
    assert motion['all_tested_joints_have_a_collision_free_nonzero_sample_without_base']
    assert motion['parts_manifest_sha256']==hashlib.sha256((OUT/'pecas.json').read_bytes()).hexdigest()
    assert exploded['all_valid'] and exploded['step_reimport_valid']
    rows=json.loads((OUT/'pecas.json').read_text())
    with (OUT/'lista_pecas_por_cor.csv').open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.writer(f,delimiter=';');w.writerow(['arquivo_STL','cor','grupo','solidos','volume_mm3','observacao'])
        for p in sorted(rows,key=lambda p:(color_name(p['color']),p['name'])):
            if not p.get('printable',True):continue
            w.writerow([p['name']+'.stl',color_name(p['color']),p['group'],p['solids'],p['volume_mm3'],p['notes']])
    with (OUT/'lista_ferragens.csv').open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.writer(f,delimiter=';');w.writerow(['articulacao','parafuso','quantidade','porca','quantidade_porcas','arruelas_pequenas','quantidade_arruelas','apoio_deslizamento'])
        for j in joints['joints']:
            w.writerow([j['joint'],'ISO 4762 M3x16',1,'ISO 4032 M3',1,
                        'DIN 433 / ISO 7092 M3 3.2x6x0.5',j['washer_quantity'],
                        'PTFE/PET recortado 3.3x12x0.3' if j['bearing_quantity'] else ''])
    # The optional motion report records sampled angles, not a full ROM certification.
    static=['Lidera_articulado_180mm.step','Lidera_preview.png','vista_frontal.png','vista_lateral.png','vista_traseira.png',
            'logo_peito_detalhe.png','logo_peito_38mm.svg','decal_logo_escala_real.pdf',
            'lista_pecas_por_cor.csv','lista_ferragens.csv','pecas.json','validacao.json',
            'validacao_STL.json','validacao_logo.json','validacao_articulacoes.json',
            'ferragens.json','articulacoes.json','Guia_articulacoes_M3.pdf',
            'Articulacoes_explodidas.step','validacao_explodido.json','movimento_local.json']
    archive=OUT/'Lidera_A1_180mm.zip'
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        z.write(ROOT/'README.md','README.md')
        for name in ('requirements.txt','.gitignore','.gitattributes'):
            p=ROOT/name
            if p.exists():z.write(p,name)
        for p in sorted((ROOT/'cad').glob('*.py')):z.write(p,'cad/'+p.name)
        for p in sorted((ROOT/'assets').glob('*.svg')):z.write(p,'assets/'+p.name)
        z.write(ROOT/'cad'/'PRINT_NOTES.md','cad/PRINT_NOTES.md')
        z.write(ROOT/'cad'/'JOINTS.md','cad/JOINTS.md')
        for name in static:
            p=OUT/name
            if not p.exists():raise FileNotFoundError(p)
            z.write(p,'exports/'+name)
        for directory in ('STL','cupons','juntas'):
            for p in sorted((OUT/directory).glob('*')):
                if p.is_file():z.write(p,str(p.relative_to(ROOT)))
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        print('ZIP:',archive,'files:',len(z.namelist()),'MB:',round(archive.stat().st_size/1024**2,2))

if __name__=='__main__':main()

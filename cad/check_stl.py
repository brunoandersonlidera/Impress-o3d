"""Verifica triangulações STL fechadas, escala e tamanho para a placa A1."""
from pathlib import Path
from collections import Counter
import numpy as np
import json, struct

OUT=Path(__file__).resolve().parents[1]/'exports'

def check(path):
    raw=path.read_bytes(); n=struct.unpack('<I',raw[80:84])[0]
    if len(raw)!=84+50*n: raise ValueError('STL binário inesperado: '+str(path))
    dtype=np.dtype([('normal','<f4',(3,)),('v','<f4',(3,3)),('attr','<u2')])
    tri=np.frombuffer(raw,offset=84,count=n,dtype=dtype)['v'].astype(float)
    xyz=tri.reshape(-1,3); bounds=xyz.max(0)-xyz.min(0)
    quant=np.rint(tri*100000).astype(np.int64)
    edges=Counter()
    for t in quant:
        for i,j in ((0,1),(1,2),(2,0)):
            a,b=tuple(t[i]),tuple(t[j])
            if a!=b: edges[tuple(sorted((a,b)))]+=1
    bad=sum(v!=2 for v in edges.values())
    return dict(file=str(path.relative_to(OUT)),triangles=n,closed_two_manifold_edges=bad==0,nonmanifold_edges=bad,size_mm=[round(float(v),3) for v in bounds],fits_A1=all(bounds<=256.0),bed_z_mm=round(float(xyz[:,2].min()),5))

def main():
    rows=[check(p) for folder in ('STL','cupons') for p in sorted((OUT/folder).glob('*.stl'))]
    out={'stl_files':len(rows),'all_closed':all(r['closed_two_manifold_edges'] for r in rows),'all_fit_A1':all(r['fits_A1'] for r in rows),'all_on_bed':all(abs(r['bed_z_mm'])<.001 for r in rows),'parts':rows}
    (OUT/'validacao_STL.json').write_text(json.dumps(out,indent=2))
    print({k:v for k,v in out.items() if k!='parts'})
    if not out['all_closed']: print([r for r in rows if not r['closed_two_manifold_edges']])
    if not all(out[k] for k in ('all_closed','all_fit_A1','all_on_bed')): raise SystemExit(1)

if __name__=='__main__': main()

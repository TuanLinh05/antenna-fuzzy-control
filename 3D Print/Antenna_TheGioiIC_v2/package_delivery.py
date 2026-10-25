"""Independently validate the delivered 3MF meshes, then create a manifest and ZIP."""
from pathlib import Path
import sys,json,csv,collections,zipfile,hashlib,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parents[2]/'tmp'/'cad_runtime'))
import numpy as np,trimesh
for f in ('assembly_validation.json','fastener_validation.json','m4_audit.json'):
    report=json.loads((ROOT/f).read_text(encoding='utf-8'))
    assert report['status']=='PASS',f
rows=list(csv.DictReader((ROOT/'printed_parts.csv').open(encoding='utf-8-sig')))
expect={q['part']:int(q['quantity']) for q in rows}
assert len(list((ROOT/'STL').glob('*.stl')))==len(expect)
for q in json.loads((ROOT/'mesh_validation.json').read_text(encoding='utf-8')):
    assert q['watertight'] and q['winding_consistent'] and q['connected_components']==1 and q['fits_A1']
ns={'m':'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'}
actual=collections.Counter();checks=[]
for p in sorted((ROOT/'3MF_plates').glob('*.3mf')):
    with zipfile.ZipFile(p) as z:
        assert z.testzip() is None
        xml=ET.fromstring(z.read('3D/3dmodel.model'))
    assert xml.get('unit')=='millimeter'
    resources={o.get('id'):o for o in xml.findall('m:resources/m:object',ns)}
    for item in xml.findall('m:build/m:item',ns):
        assert item.get('transform') is None
        o=resources[item.get('objectid')];actual[o.get('name')]+=1
        vs=[[float(v.get(k)) for k in ('x','y','z')] for v in o.findall('m:mesh/m:vertices/m:vertex',ns)]
        fs=[[int(f.get(k)) for k in ('v1','v2','v3')] for f in o.findall('m:mesh/m:triangles/m:triangle',ns)]
        mesh=trimesh.Trimesh(vertices=vs,faces=fs,process=True)
        assert mesh.is_watertight and mesh.is_winding_consistent and mesh.volume>0
        assert len(mesh.split(only_watertight=False))==1
        assert np.all(mesh.bounds[0]>=-.0001) and np.all(mesh.bounds[1]<=256.0001)
        checks.append(dict(plate=p.name,part=o.get('name'),watertight=True,one_component=True,bounds_mm=mesh.bounds.round(3).tolist()))
assert dict(actual)==expect,(dict(actual),expect)
bom=json.loads((ROOT/'procurement.json').read_text(encoding='utf-8'))
assert all(q['url'].startswith('https://www.thegioiic.com/') and q['stock']>=q['purchase']>=q['required'] for q in bom['items'])
assert bom['mechanical_total_vnd']==sum(q['price']*q['purchase'] for q in bom['items'])
fast=json.loads((ROOT/'fastener_validation.json').read_text(encoding='utf-8'))
assert fast['bolt_counts']=={'M4x20':20,'M3x12':12,'M3x16':2,'M3x10':6,'M3x8':1,'M3x20':7,'M2x10':2}
delivery=dict(status='PASS',stl_types=len(expect),plate_count=4,total_print_objects=sum(expect.values()),mechanical_procurement_products=len(bom['items']),mechanical_total_vnd=bom['mechanical_total_vnd'],units='millimeter',printer='Bambu Lab A1, 256 x256 x256',plate_mesh_checks=checks,physical_print_tested=False)
(ROOT/'delivery_validation.json').write_text(json.dumps(delivery,indent=2),encoding='utf-8')
def deliverable(p):return p.is_file() and 'qa_cache' not in p.parts and '__pycache__' not in p.parts and p.name!='file_manifest.json'
files=sorted(p for p in ROOT.rglob('*') if deliverable(p))
manifest=[dict(path=str(p.relative_to(ROOT)).replace('\\','/'),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in files]
(ROOT/'file_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
dest=ROOT.with_suffix('.zip')
with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED) as z:
    for p in files+[ROOT/'file_manifest.json']:
        z.write(p,ROOT.name+'/'+str(p.relative_to(ROOT)).replace('\\','/'))
with zipfile.ZipFile(dest) as z:assert z.testzip() is None
print(json.dumps(dict(status='PASS',STL_types=len(expect),objects=sum(expect.values()),ZIP=str(dest),ZIP_bytes=dest.stat().st_size),indent=2))

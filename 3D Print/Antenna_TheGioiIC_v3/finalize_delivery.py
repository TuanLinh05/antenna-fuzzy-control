"""Independently check delivered meshes, reports and CAD/simulation consistency."""
from pathlib import Path
import csv,collections,hashlib,json,sys,zipfile,xml.etree.ElementTree as ET
R=Path(__file__).resolve().parent
PROJECT=R.parents[1]
sys.path.insert(0,str(R.parents[2]/'tmp/cad_runtime'))
import numpy as np,trimesh
from scipy.spatial import ConvexHull
from scipy.io import loadmat

def read(name):return json.loads((R/name).read_text(encoding='utf-8'))
def write(name,value):(R/name).write_text(json.dumps(value,indent=2,ensure_ascii=False),encoding='utf-8')
def separated(a,b):
    gaps=[]
    for h in (a,b):
        for v,w in zip(h,np.roll(h,-1,axis=0)):
            e=w-v;axis=np.array([-e[1],e[0]]);axis/=np.linalg.norm(axis)
            pa,pb=a@axis,b@axis;gaps.append(max(pb.min()-pa.max(),pa.min()-pb.max()))
    return max(gaps)

def main():
    required_reports=['assembly_validation.json','fastener_validation.json','m4_audit.json',
        'audit/load_validation.json','audit/transmission_validation.json','audit/electrical_validation.json',
        'audit/firmware_build_validation.json','viewer_validation.json',
        '../../Simulation/results/fuzzy_validation.json','../../Simulation/results/simulink_validation.json',
        '../../Simulation/results/comprehensive_validation.json','../../Simulation/results/video_validation.json']
    for name in required_reports:
        assert read(name)['status'].startswith('PASS'),name
    sim=read('../../Simulation/results/comprehensive_validation.json')
    assert sim['dc_nominal']['pass'] and sim['dc_uncertainty_all_pass'] and sim['prototype_nominal']['pass_tracking']
    assert sim['prototype_refinement_pass'] and not sim['physical_hardware_validated']
    assert sim['overload_tracking_test_pass'] is False, 'Retain documented overload limitation.'
    current=read('../../Simulation/cad_parameters.json')
    actual=loadmat(R/'../../Simulation/results/prototype_nominal.mat',simplify_cells=True)['nominal']['config']['cad']
    for k,v in current.items():np.testing.assert_allclose(np.array(actual[k]),np.array(v),rtol=0,atol=1e-12,err_msg=k)
    video=read('../../Simulation/results/video_validation.json')
    for k,v in current.items():np.testing.assert_allclose(video['CAD_parameters'][k],v,rtol=0,atol=1e-12)
    write('audit/MATLAB_CAD_consistency.json',dict(status='PASS',CAD_parameters=current,
        source_mesh_sha256=hashlib.sha256((R/'preview/mesh_data.json').read_bytes()).hexdigest(),
        simulation_parameters_match=True,video_parameters_match=True))

    rows=list(csv.DictReader((R/'printed_parts.csv').open(encoding='utf-8-sig')))
    expected={q['part']:int(q['quantity']) for q in rows}
    assert len(expected)==22 and sum(expected.values())==36
    assert len(list((R/'STL').glob('*.stl')))==22
    for q in read('mesh_validation.json'):
        assert q['watertight'] and q['winding_consistent'] and q['connected_components']==1 and q['fits_A1']
    ns={'m':'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'}
    actual_parts=collections.Counter();checks=[];minimum_gap=1000.
    plates=sorted((R/'3MF_plates').glob('*.3mf'));assert len(plates)==5
    for plate in plates:
        with zipfile.ZipFile(plate) as z:
            assert z.testzip() is None
            xml=ET.fromstring(z.read('3D/3dmodel.model'))
        assert xml.get('unit')=='millimeter'
        objects={o.get('id'):o for o in xml.findall('m:resources/m:object',ns)}
        hulls=[]
        for item in xml.findall('m:build/m:item',ns):
            assert item.get('transform') is None
            obj=objects[item.get('objectid')];name=obj.get('name');actual_parts[name]+=1
            vertices=[[float(v.get(k)) for k in ('x','y','z')] for v in obj.findall('m:mesh/m:vertices/m:vertex',ns)]
            faces=[[int(f.get(k)) for k in ('v1','v2','v3')] for f in obj.findall('m:mesh/m:triangles/m:triangle',ns)]
            mesh=trimesh.Trimesh(vertices=vertices,faces=faces,process=True)
            assert mesh.is_watertight and mesh.is_winding_consistent and mesh.volume>0
            assert len(mesh.split(only_watertight=False))==1
            assert np.all(mesh.bounds[0]>=-.0001) and np.all(mesh.bounds[1]<=256.0001)
            source=trimesh.load_mesh(R/'STL'/f'{name}.stl')
            assert abs(mesh.volume/source.volume-1)<1e-5
            xy=np.unique(mesh.vertices[:,:2],axis=0);hulls.append(xy[ConvexHull(xy).vertices])
            checks.append(dict(plate=plate.name,part=name,bounds_mm=mesh.bounds.round(3).tolist(),watertight=True))
        for i,a in enumerate(hulls):
            for b in hulls[:i]:
                gap=separated(a,b);assert gap>=-.001;minimum_gap=min(minimum_gap,gap)
    assert dict(actual_parts)==expected
    bom=read('procurement.json')
    assert len(bom['items'])==35
    assert all(q['url'].startswith('https://www.thegioiic.com/') and q['stock']>=q['purchase']>=q['required']
               and q['purchase']>=q['minimum'] and q['purchase']%q['multiple']==0 for q in bom['items'])
    assert bom['mechanical_total_vnd']==sum(q['price']*q['purchase'] for q in bom['items'] if q['category']=='mechanical')
    assert bom['electrical_total_vnd']==sum(q['price']*q['purchase'] for q in bom['items'] if q['category']=='electrical')
    assert bom['system_total_vnd']==bom['mechanical_total_vnd']+bom['electrical_total_vnd']
    assert read('fastener_validation.json')['bolt_counts']=={'M4x20':20,'M3x12':12,'M3x16':6,'M3x10':6,'M3x8':4,'M3x20':7,'M2x10':2}
    for name in ['../../Simulation/antenna_dc_fuzzy.slx','../../Simulation/antenna_sugeno25.fis','../../Simulation/results/antenna_simulation.mp4',
                 '../../Simulation/results/antenna_CAD_in_MATLAB.png','BAO_CAO_KIEM_TRA_V3.md','../../Firmware/build/antenna_f103.hex']:
        assert (R/name).stat().st_size>0,name
    write('audit/STAGE_GATES.json',dict(revision='V3',audit_date_local='2026-10-24',
        stage_1_mechanics='PASS_CAD_AND_ENGINEERING_ASSUMPTIONS',
        stage_2_procurement='PASS_LIVE_STOCK_SNAPSHOT_2026_10_24',
        stage_3_electrical_and_fuzzy='PASS_DESIGN_COMPILE_AND_HOST_TESTS',
        stage_4_MATLAB_simulation=sim['status'],physical_print_and_hardware_test='NOT_PERFORMED',
        acceptance_note='Digital verification complete. Impact/jam-release speed limits and physical commissioning remain open; DC assignment and stepper prototype are distinct plants.'))
    write('delivery_validation.json',dict(status='PASS_DIGITAL_WITH_LIMITATIONS',stl_types=22,total_print_objects=36,
        plate_count=5,minimum_XY_footprint_gap_mm=minimum_gap,procurement_products=35,
        project_layout=['Simulation','Firmware','3D Print/Antenna_TheGioiIC_v3'],
        manifest_paths_relative_to='Project root (Bai tap lon)',archive_project_root=R.name,
        mechanical_total_vnd=bom['mechanical_total_vnd'],electrical_total_vnd=bom['electrical_total_vnd'],
        system_total_vnd=bom['system_total_vnd'],units='millimeter',printer='Bambu Lab A1 256 x256 x256 mm',
        plate_mesh_checks=checks,physical_print_tested=False,simulation_status=sim['status']))
    excluded={'qa_cache','__pycache__','slprj','reference_previous'}
    def include(p):
        rel=p.relative_to(PROJECT)
        return p.is_file() and not any(k in excluded for k in rel.parts) and p.name!='file_manifest.json' and not p.name.endswith(('.slxc','.slx.autosave','.asv','.exe')) and not p.name.startswith('smoke_')
    files=sorted(p for root in (R,PROJECT/'Simulation',PROJECT/'Firmware') for p in root.rglob('*') if include(p))
    if (PROJECT/'README.md').exists():files.append(PROJECT/'README.md')
    manifest=[dict(path=p.relative_to(PROJECT).as_posix(),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in files]
    write('file_manifest.json',manifest)
    dest=R.with_suffix('.zip')
    with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED) as z:
        for p in files+[R/'file_manifest.json']:z.write(p,R.name+'/'+p.relative_to(PROJECT).as_posix())
    with zipfile.ZipFile(dest) as z:
        assert z.testzip() is None
        for row in manifest:assert hashlib.sha256(z.read(R.name+'/'+row['path'])).hexdigest()==row['sha256']
    print(json.dumps(dict(status='PASS_DIGITAL_WITH_LIMITATIONS',files=len(files)+1,STL=22,objects=36,plates=5,
        ZIP=str(dest),ZIP_bytes=dest.stat().st_size),indent=2))

if __name__=='__main__':main()

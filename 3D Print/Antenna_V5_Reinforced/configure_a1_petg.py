"""Create Bambu-native A1/PETG projects and verify them with the installed slicer.

CAD/STL geometry is unchanged. Neutral originals remain in 3MF_plates.
No command in this script connects to a printer or starts printing.
"""
from pathlib import Path
import argparse, collections, copy, hashlib, json, math, os, shutil, subprocess, sys, time, uuid, zipfile
import xml.etree.ElementTree as ET

R=Path(__file__).resolve().parent
sys.path.insert(0,str(R.parents[2]/'tmp/cad_runtime'))
import numpy as np
import trimesh

EXE=Path(os.environ.get('BAMBU_STUDIO_EXE','E:/Bambu Studio/bambu-studio.exe'))
SYSTEM=Path(os.environ.get('APPDATA',''))/'BambuStudio/system/BBL'
WORK=R.parents[2]/'tmp'/'antenna_a1_petg'
OUT=R/'3MF_A1_PETG_0p4'
PROFILES=R/'print_profiles'
NS='http://schemas.microsoft.com/3dmanufacturing/core/2015/02'
Q={'m':NS}
PNS='http://schemas.microsoft.com/3dmanufacturing/production/2015/06'

def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,d):p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')

def run_cli(args,folder):
    folder.mkdir(parents=True,exist_ok=True)
    args=list(args)
    # Native CLI export on Windows can crash on Unicode working/input paths.
    if str(args[-1]).endswith('.3mf') and not str(args[-1]).isascii():
        staged=folder/'input.3mf';shutil.copyfile(args[-1],staged);args[-1]=staged
    started=time.time()
    command=[str(EXE),'--outputdir',str(folder),*map(str,args)]
    proc=subprocess.run(command,cwd=folder,capture_output=True)
    retries=0
    while proc.returncode in (3221225477,-1073741819) and retries<2:
        # Known intermittent Windows CLI access violation; accept only a
        # fresh successful result with actual G-code, never a stale result.
        time.sleep(2);retries+=1
        proc=subprocess.run(command,cwd=folder,capture_output=True)
    result=read(folder/'result.json') if (folder/'result.json').exists() and (folder/'result.json').stat().st_mtime>=started-2 else {}
    assert proc.returncode==0 and result.get('return_code',0)==0,(proc.returncode,result)
    return dict(result,elapsed_seconds=round(time.time()-started,2),CLI_access_violation_retries=retries)

def resolved(name,kind):
    d=read(SYSTEM/kind/(name+'.json'))
    result=resolved(d['inherits'],kind) if d.get('inherits') else {}
    result.update(d)
    return result

def settings():
    # A real, fully expanded A1 project supplies machine limits/start/end macros.
    template=R.parents[0]/'de-mt6701-lap-thu-v1.3mf'
    if template.exists():
        with zipfile.ZipFile(template) as z:d=json.loads(z.read('Metadata/project_settings.config'))
    else:d=read(PROFILES/'A1_PETG_full_project_settings.json')
    source_filament=resolved('Generic PETG @BBL A1','filament') if SYSTEM.exists() else {}
    ignored={'type','name','inherits','from','setting_id','instantiation','compatible_printers','filament_id'}
    for k,v in source_filament.items():
        if k not in ignored and k in d:d[k]=v
    d.update({
        'version':'02.08.02.60','printer_settings_id':'Bambu Lab A1 0.4 nozzle',
        'printer_model':'Bambu Lab A1','printer_variant':'0.4','nozzle_diameter':['0.4'],
        'filament_settings_id':['Antenna V5 Generic PETG 255C @A1'],'filament_ids':['GFG99'],
        'filament_vendor':['Generic'],'filament_type':['PETG'],'filament_colour':['#E39B36'],
        'filament_max_volumetric_speed':['8'],'filament_flow_ratio':['0.95'],
        'nozzle_temperature':['255'],'nozzle_temperature_initial_layer':['255'],
        'textured_plate_temp':['80'],'textured_plate_temp_initial_layer':['80'],
        'curr_bed_type':'Textured PEI Plate','filament_shrink':['100%'],
        'print_settings_id':'Antenna V5 A1 PETG 0.16 Quality Strength',
        'layer_height':'0.16','initial_layer_print_height':'0.2','precise_z_height':'1',
        'wall_loops':'6','wall_generator':'classic','precise_outer_wall':'1',
        'wall_sequence':'inner wall/outer wall','outer_wall_line_width':'0.42',
        'inner_wall_line_width':'0.45','sparse_infill_line_width':'0.45',
        'top_surface_line_width':'0.42','sparse_infill_density':'40%',
        'sparse_infill_pattern':'gyroid','infill_wall_overlap':'15%',
        'top_shell_layers':'8','top_shell_thickness':'1.28',
        'bottom_shell_layers':'8','bottom_shell_thickness':'1.28',
        'top_surface_pattern':'monotonicline','bottom_surface_pattern':'monotonic',
        'outer_wall_speed':['35'],'inner_wall_speed':['60'],'sparse_infill_speed':['80'],
        'internal_solid_infill_speed':['60'],'top_surface_speed':['30'],
        'gap_infill_speed':['40'],'bridge_speed':['20'],
        'initial_layer_speed':['20'],'initial_layer_infill_speed':['25'],
        'travel_speed':['250'],'default_acceleration':['1500'],
        'outer_wall_acceleration':['800'],'inner_wall_acceleration':['1500'],
        'top_surface_acceleration':['800'],'travel_acceleration':['3000'],
        'bridge_flow':'1','enable_overhang_speed':['1'],'overhang_1_4_speed':['35'],
        'overhang_2_4_speed':['25'],'overhang_3_4_speed':['15'],'overhang_4_4_speed':['10'],
        'fan_min_speed':['30'],'fan_max_speed':['50'],'overhang_fan_speed':['80'],
        'close_fan_the_first_x_layers':['3'],'slow_down_layer_time':['12'],
        'ironing_type':'no ironing','seam_position':'aligned','seam_slope_type':'none',
        'resolution':'0.01','enable_arc_fitting':'1','xy_hole_compensation':'0',
        'xy_contour_compensation':'0','elefant_foot_compensation':'0.15',
        'enable_support':'0','support_type':'normal(auto)','support_style':'snug',
        'support_threshold_angle':'35','support_on_build_plate_only':'0',
        'support_top_z_distance':'0.24','support_bottom_z_distance':'0.24',
        'support_object_xy_distance':'0.35','support_interface_top_layers':'3',
        'support_interface_bottom_layers':'2','support_interface_spacing':'0.25',
        'support_bottom_interface_spacing':'0.3','support_base_pattern_spacing':'2.5',
        'support_interface_pattern':'rectilinear','support_speed':['50'],
        'support_interface_speed':['25'],'support_filament':'0','support_interface_filament':'0',
        'independent_support_layer_height':'1','support_remove_small_overhang':'1',
        'brim_type':'outer_only','brim_width':'4','brim_object_gap':'0.15',
        'print_sequence':'by layer','enable_prime_tower':'0','smooth_timelapse':'0',
    })
    d.pop('name',None);d.pop('type',None)
    # Old project difference masks would let GUI replace our cooling values.
    d.pop('different_settings_to_system',None)
    return d

GAUGES={16,17,20,23,26,27,28,29,30}
SUPPORT={1,3,4,12,15,22,25}
HEAVY={1,2,3,4,7,8,9,10,11,13,18,19,22,25}

def object_settings(name):
    n=int(name[:2])
    s={'wall_loops':'8' if n in HEAVY else '6',
       'sparse_infill_density':'45%' if n in HEAVY else '40%',
       'enable_support':'1' if n in SUPPORT else '0',
       'brim_type':'outer_only','brim_width':'4','brim_object_gap':'0.15'}
    if n in GAUGES:
        s.update(wall_loops='6',sparse_infill_density='40%',enable_support='0')
    if n in {5,21,29}:
        s.update(layer_height='0.10',sparse_infill_density='100%',top_shell_thickness='0',
                 bottom_shell_thickness='0',top_shell_layers='5',bottom_shell_layers='5',brim_width='2')
    if n==12:
        s.update(layer_height='0.12',wall_loops='4',sparse_infill_density='20%',
                 support_type='tree(auto)',support_style='tree_hybrid',
                 support_on_build_plate_only='1',support_top_z_distance='0.24',
                 brim_width='5')
    if n in {11,18,24,25}:
        s['sparse_infill_density']='100%'
    return s

def neutral_project(path,entries):
    ET.register_namespace('',NS)
    model=ET.Element('{'+NS+'}model',unit='millimeter')
    res=ET.SubElement(model,'{'+NS+'}resources');build=ET.SubElement(model,'{'+NS+'}build')
    for i,(n,x,y,angle) in enumerate(entries,1):
        p=next((R/'STL').glob(f'{n:02d}_*.stl'));m=trimesh.load_mesh(p)
        a=math.radians(angle);rot=np.array([[math.cos(a),-math.sin(a),0],[math.sin(a),math.cos(a),0],[0,0,1]])
        m.vertices=m.vertices@rot.T+[x,y,0]
        obj=ET.SubElement(res,'{'+NS+'}object',id=str(i),type='model',name=p.stem)
        mesh=ET.SubElement(obj,'{'+NS+'}mesh');vv=ET.SubElement(mesh,'{'+NS+'}vertices');ff=ET.SubElement(mesh,'{'+NS+'}triangles')
        for v in m.vertices:ET.SubElement(vv,'{'+NS+'}vertex',**dict(zip(('x','y','z'),[f'{q:.6f}' for q in v])))
        for f in m.faces:ET.SubElement(ff,'{'+NS+'}triangle',**dict(zip(('v1','v2','v3'),map(str,f))))
        ET.SubElement(build,'{'+NS+'}item',objectid=str(i))
    with zipfile.ZipFile(next((R/'3MF_plates').glob('*.3mf'))) as template:
        with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
            for name in ('[Content_Types].xml','_rels/.rels'):z.writestr(name,template.read(name))
            z.writestr('3D/3dmodel.model',ET.tostring(model,encoding='utf-8',xml_declaration=True))

def native_project(neutral,path,plate_name):
    """Production-extension 3MF: one centered mesh component per build object.

    Mirrors the native schema emitted by Bambu Studio 02.08.02.60. The
    installed CLI's thumbnail exporter is unreliable on this Windows host.
    """
    ET.register_namespace('',NS);ET.register_namespace('p',PNS)
    uid=lambda tag:str(uuid.uuid5(uuid.NAMESPACE_URL,f'antenna-V5/{plate_name}/{tag}'))
    def model():
        q=ET.Element('{'+NS+'}model',unit='millimeter',requiredextensions='p')
        ET.SubElement(q,'{'+NS+'}metadata',name='BambuStudio:3mfVersion').text='1'
        return q
    root=model();ET.SubElement(root,'{'+NS+'}metadata',name='Application').text='BambuStudio-02.08.02.60'
    resources=ET.SubElement(root,'{'+NS+'}resources');build=ET.SubElement(root,'{'+NS+'}build')
    cfg=ET.Element('config');plate=ET.SubElement(cfg,'plate')
    for k,v in [('plater_id','1'),('plater_name',plate_name),('locked','false'),
                ('filament_map_mode','Auto For Flush'),('filament_maps','1'),('filament_volume_maps','0')]:
        ET.SubElement(plate,'metadata',key=k,value=v)
    relns='http://schemas.openxmlformats.org/package/2006/relationships'
    rels=ET.Element('Relationships',xmlns=relns);files={}
    with zipfile.ZipFile(neutral) as z:
        original=ET.fromstring(z.read('3D/3dmodel.model'))
        files['_rels/.rels']=z.read('_rels/.rels')
    for i,obj in enumerate(original.findall('m:resources/m:object',Q),1):
        leaf_id=2*i-1;parent_id=2*i;label=obj.get('name');mesh=copy.deepcopy(obj.find('m:mesh',Q))
        vertices=mesh.findall('m:vertices/m:vertex',Q)
        vv=np.array([[float(v.get(k)) for k in 'xyz'] for v in vertices]);center=(vv.min(0)+vv.max(0))/2
        for v,p in zip(vertices,vv-center):
            for k,t in zip('xyz',p):v.set(k,f'{t:.6f}')
        leaf=model();rr=ET.SubElement(leaf,'{'+NS+'}resources')
        child=ET.SubElement(rr,'{'+NS+'}object',id=str(leaf_id),type='model',attrib={'{'+PNS+'}UUID':uid(f'leaf-{i}')})
        child.append(mesh);leaf_path=f'3D/Objects/object_{i}.model'
        files[leaf_path]=ET.tostring(leaf,encoding='utf-8',xml_declaration=True)
        parent=ET.SubElement(resources,'{'+NS+'}object',id=str(parent_id),type='model',attrib={'{'+PNS+'}UUID':uid(f'parent-{i}')})
        cc=ET.SubElement(parent,'{'+NS+'}components')
        ET.SubElement(cc,'{'+NS+'}component',objectid=str(leaf_id),transform='1 0 0 0 1 0 0 0 1 0 0 0',
                      attrib={'{'+PNS+'}path':'/'+leaf_path,'{'+PNS+'}UUID':uid(f'component-{i}')})
        tr='1 0 0 0 1 0 0 0 1 '+' '.join(f'{x:.6f}' for x in center)
        ET.SubElement(build,'{'+NS+'}item',objectid=str(parent_id),transform=tr,printable='1')
        settings_obj=ET.SubElement(cfg,'object',id=str(parent_id))
        ET.SubElement(settings_obj,'metadata',key='name',value=label)
        ET.SubElement(settings_obj,'metadata',key='extruder',value='1')
        part=ET.SubElement(settings_obj,'part',id=str(leaf_id),subtype='normal_part',uuid=uid(f'part-{i}'))
        ET.SubElement(part,'metadata',key='name',value=label)
        ET.SubElement(part,'metadata',key='matrix',value='1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1')
        ET.SubElement(part,'mesh_stat',face_count=str(len(mesh.findall('m:triangles/m:triangle',Q))),
                      edges_fixed='0',degenerate_facets='0',facets_removed='0',facets_reversed='0',backwards_edges='0')
        instance=ET.SubElement(plate,'model_instance')
        for k,v in [('object_id',str(parent_id)),('instance_id','0'),('identify_id',str(100+i))]:
            ET.SubElement(instance,'metadata',key=k,value=v)
        ET.SubElement(rels,'Relationship',Target='/'+leaf_path,Id=f'rel-{i}',
                      Type='http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel')
    files['3D/3dmodel.model']=ET.tostring(root,encoding='utf-8',xml_declaration=True)
    files['3D/_rels/3dmodel.model.rels']=ET.tostring(rels,encoding='utf-8',xml_declaration=True)
    files['Metadata/model_settings.config']=ET.tostring(cfg,encoding='utf-8',xml_declaration=True)
    files['[Content_Types].xml']=b'<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/><Default Extension="png" ContentType="image/png"/></Types>'
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
        for n,b in files.items():z.writestr(n,b)

def plans():
    import runpy
    # Read the plate dictionary without executing the writer below it.
    source=(R/'pack_print_plates.py').read_text(encoding='utf-8')
    scope={};exec(source[source.index('plates={'):source.index("out=ROOT/")],scope)
    d=scope['plates']
    for name in d:d[name]=[q for q in d[name] if q[0] not in GAUGES]
    d['Plate_03_drive_and_servo_mounts']=[
        (11,125,230,0) if q[0]==11 else (4,196,203,0) if q[0]==4 else q
        for q in d['Plate_03_drive_and_servo_mounts']]
    d['Plate_00_CALIBRATION_FIRST']=[
        (16,60,42,0),(17,60,80,0),(20,157,57,0),(23,54,120,0),
        (26,117,130,0),(27,179,126,0),(28,54,162,0),(30,124,192,0),
        (29,180,182,0),(29,193,182,0),(29,180,197,0),(29,193,197,0)]
    return dict(sorted(d.items()))

def build():
    for p in (OUT,PROFILES,WORK):p.mkdir(parents=True,exist_ok=True)
    cfg=settings();write(PROFILES/'A1_PETG_full_project_settings.json',cfg)
    desc={};plan=plans()
    for name,entries in plan.items():
        folder=WORK/name;folder.mkdir(parents=True,exist_ok=True)
        neutral=folder/'neutral.3mf';native=folder/'native.3mf'
        neutral_project(neutral,entries)
        native_project(neutral,native,name)
        with zipfile.ZipFile(native) as z:files={n:z.read(n) for n in z.namelist()}
        config=ET.fromstring(files['Metadata/model_settings.config'])
        objects=[]
        for obj in config.findall('object'):
            metadata={q.get('key'):q.get('value') for q in obj.findall('metadata')}
            label=metadata['name'];s=object_settings(label)
            for k,v in s.items():ET.SubElement(obj,'metadata',key=k,value=v)
            objects.append(dict(name=label,object_id=int(obj.get('id')),settings=s))
        for plate in config.findall('plate'):
            for meta in plate.findall('metadata'):
                if meta.get('key')=='plater_name':meta.set('value',name)
        files['Metadata/project_settings.config']=json.dumps(cfg,indent=2).encode()
        files['Metadata/model_settings.config']=ET.tostring(config,encoding='utf-8',xml_declaration=True)
        path=OUT/(name+'_A1_PETG_0p4.3mf')
        with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
            for n,b in files.items():z.writestr(n,b)
        # Actual slicer read-back is checked from the G-code CONFIG_BLOCK by
        # validate_a1_petg.py, together with object heights and plate geometry.
        desc[name]=dict(file=path.relative_to(R).as_posix(),object_count=len(objects),objects=objects)
        print('CONFIGURED',name,len(objects),flush=True)
    write(PROFILES/'object_print_settings.json',desc)
    write(PROFILES/'profile_provenance.json',dict(
        date_local='2026-10-25',slicer='Bambu Studio 02.08.02.60',printer='Bambu Lab A1',nozzle_mm=.4,
        filament='Generic PETG; brand and flow/pressure calibration unmeasured',
        bed='Textured PEI Plate',source='Expanded local A1 project plus installed official Generic PETG inheritance',
        automatic_slicer_settings_reload_verified=False,physical_print_verified=False,
        CAD_scale=1,XY_compensation_mm=0,filament_shrink_percent=100,
        note='Profiles prioritize surface quality and mechanical shells; no universal optimum or guaranteed tolerance.'))

def slice_all(prefix=''):
    for p in sorted(OUT.glob(prefix+'*.3mf')):
        folder=WORK/p.stem;folder.mkdir(parents=True,exist_ok=True)
        sliced=folder/'sliced.3mf'
        print('SLICING',p.name,flush=True)
        result=run_cli(['--slice','1',p],folder)
        assert (folder/'plate_1.gcode').exists()
        write(folder/'cli_result.json',result)
        print('SLICED',p.name,'seconds',result.get('elapsed_seconds'),
              'warnings',[s.get('warning_message','') for s in result.get('sliced_plates',[])],flush=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--build',action='store_true');ap.add_argument('--slice',action='store_true');ap.add_argument('--prefix',default='')
    a=ap.parse_args()
    if a.build:build()
    if a.slice:slice_all(a.prefix)

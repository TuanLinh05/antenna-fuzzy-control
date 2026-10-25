"""Independent geometry, embedded preset and generated toolpath checks."""
from pathlib import Path
import collections, hashlib, json, math, re, sys, zipfile
import xml.etree.ElementTree as ET
R=Path(__file__).resolve().parent
sys.path.insert(0,str(R.parents[2]/'tmp/cad_runtime'))
import numpy as np
import trimesh
import vtk
from configure_a1_petg import OUT,WORK,PROFILES,object_settings
NS='http://schemas.microsoft.com/3dmanufacturing/core/2015/02';Q={'m':NS}
P='http://schemas.microsoft.com/3dmanufacturing/production/2015/06'

def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,d):p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def transform(v,s):
    if not s:return v
    m=np.fromstring(s,sep=' ').reshape(4,3)
    return v@m[:3,:]+m[3,:]

def meshes(path):
    with zipfile.ZipFile(path) as z:
        config=ET.fromstring(z.read('Metadata/model_settings.config'))
        metadata={o.get('id'):{x.get('key'):x.get('value') for x in o.findall('metadata')} for o in config.findall('object')}
        cache={}
        def root(file):
            if file not in cache:cache[file]=ET.fromstring(z.read(file))
            return cache[file]
        def geometry(file,oid):
            o=next(x for x in root(file).findall('m:resources/m:object',Q) if x.get('id')==oid)
            m=o.find('m:mesh',Q)
            if m is not None:
                vv=np.array([[float(v.get(k)) for k in 'xyz'] for v in m.findall('m:vertices/m:vertex',Q)])
                ff=np.array([[int(t.get(k)) for k in ('v1','v2','v3')] for t in m.findall('m:triangles/m:triangle',Q)])
                return vv,ff
            vertices=[];faces=[];offset=0
            for c in o.findall('m:components/m:component',Q):
                child_file=c.get('{'+P+'}path',file).lstrip('/')
                v,f=geometry(child_file,c.get('objectid'));v=transform(v,c.get('transform'))
                vertices.append(v);faces.append(f+offset);offset+=len(v)
            return np.concatenate(vertices),np.concatenate(faces)
        result=[]
        model=root('3D/3dmodel.model');assert model.get('unit')=='millimeter'
        for item in model.findall('m:build/m:item',Q):
            oid=item.get('objectid');v,f=geometry('3D/3dmodel.model',oid)
            result.append(dict(name=metadata[oid]['name'],settings=metadata[oid],
                               mesh=trimesh.Trimesh(transform(v,item.get('transform')),f,process=True)))
        return result,json.loads(z.read('Metadata/project_settings.config')),config

def toolpaths(path):
    xyz=np.zeros(3);epos=0.;relative_e=True;relative_xyz=False
    feature='Custom';active=None;maxima={};heights=collections.defaultdict(set)
    features=collections.Counter();support=[];bounds=[np.full(3,np.inf),np.full(3,-np.inf)]
    settings={};in_config=False
    pattern=re.compile(r'([XYZEFIJS])(-?\d*\.?\d+)')
    for line in path.read_text(encoding='utf-8').splitlines():
        if line=='; CONFIG_BLOCK_START':in_config=True
        if line=='; CONFIG_BLOCK_END':in_config=False
        if in_config and line.startswith('; ') and ' = ' in line:
            k,v=line[2:].split(' = ',1);settings[k]=v
        if line.startswith('; FEATURE: '):feature=line[11:].strip()
        if line.startswith('; start printing object, unique label id: '):active=int(line.rsplit(':',1)[1])
        if line.startswith('; stop printing object, unique label id: '):active=None
        if line.startswith('M83'):relative_e=True
        if line.startswith('M82'):relative_e=False
        if line=='G90':relative_xyz=False
        if line=='G91':relative_xyz=True
        if line.startswith('G92 '):
            vals=dict(pattern.findall(line))
            if 'E' in vals:epos=float(vals['E'])
        if not re.match(r'^G[0123] ',line):continue
        vals={k:float(v) for k,v in pattern.findall(line.split(';',1)[0])}
        old=xyz.copy()
        for i,k in enumerate('XYZ'):
            if k in vals:xyz[i]=(xyz[i] if relative_xyz else 0)+vals[k]
        extrusion=vals.get('E',0) if relative_e else vals.get('E',epos)-epos
        if 'E' in vals:epos=(epos if relative_e else 0)+vals['E']
        if extrusion<=0 or not any(k in vals for k in 'XY') or feature in {'Custom','Flush','Undefined'}:continue
        features[feature]+=1
        bounds[0]=np.minimum(bounds[0],np.minimum(old,xyz));bounds[1]=np.maximum(bounds[1],np.maximum(old,xyz))
        if feature.startswith('Support'):support.append((old.copy(),xyz.copy()))
        elif active is not None and feature!='Brim':
            maxima[active]=max(maxima.get(active,0),xyz[2]);heights[active].add(round(float(xyz[2]),3))
    return dict(settings=settings,maxima=maxima,heights=heights,features=dict(features),support=support,bounds=np.array(bounds))

def preview(name,objects,segments):
    ren=vtk.vtkRenderer();ren.SetBackground(.96,.97,.98)
    for o in objects:
        m=o['mesh'];points=vtk.vtkPoints();cells=vtk.vtkCellArray()
        for v in m.vertices:points.InsertNextPoint(*v)
        for face in m.faces:
            cells.InsertNextCell(3)
            for k in face:cells.InsertCellPoint(int(k))
        poly=vtk.vtkPolyData();poly.SetPoints(points);poly.SetPolys(cells)
        mapper=vtk.vtkPolyDataMapper();mapper.SetInputData(poly)
        actor=vtk.vtkActor();actor.SetMapper(mapper);actor.GetProperty().SetColor(.77,.50,.19)
        actor.GetProperty().SetOpacity(.38 if segments else 1);ren.AddActor(actor)
    if segments:
        pts=vtk.vtkPoints();lines=vtk.vtkCellArray()
        for a,b in segments:
            i=pts.InsertNextPoint(*a);j=pts.InsertNextPoint(*b)
            lines.InsertNextCell(2);lines.InsertCellPoint(i);lines.InsertCellPoint(j)
        poly=vtk.vtkPolyData();poly.SetPoints(pts);poly.SetLines(lines)
        mapper=vtk.vtkPolyDataMapper();mapper.SetInputData(poly)
        a=vtk.vtkActor();a.SetMapper(mapper);a.GetProperty().SetColor(.03,.35,.85);a.GetProperty().SetLineWidth(1.3);ren.AddActor(a)
    caption=vtk.vtkTextActor();caption.SetInput(name+'\nBlue: generated support; translucent: unchanged CAD')
    caption.SetDisplayPosition(25,25);caption.GetTextProperty().SetFontSize(19);caption.GetTextProperty().SetColor(.1,.15,.2);ren.AddViewProp(caption)
    cam=ren.GetActiveCamera();cam.SetPosition(440,-350,380);cam.SetFocalPoint(128,128,25);cam.SetViewUp(0,0,1);cam.ParallelProjectionOn();cam.SetParallelScale(178)
    w=vtk.vtkRenderWindow();w.SetOffScreenRendering(1);w.AddRenderer(ren);w.SetSize(1250,1050);w.SetMultiSamples(4);w.Render()
    im=vtk.vtkWindowToImageFilter();im.SetInput(w);im.Update();writer=vtk.vtkPNGWriter()
    writer.SetFileName(str(R/'preview'/(name+'_support.png')));writer.SetInputConnection(im.GetOutputPort());writer.Write();w.Finalize()

def thumbnail(path,png):
    with zipfile.ZipFile(path) as z:files={n:z.read(n) for n in z.namelist()}
    config=ET.fromstring(files['Metadata/model_settings.config']);plate=config.find('plate')
    for m in list(plate.findall('metadata')):
        if m.get('key')=='thumbnail_file':plate.remove(m)
    ET.SubElement(plate,'metadata',key='thumbnail_file',value='Metadata/plate_1.png')
    files['Metadata/model_settings.config']=ET.tostring(config,encoding='utf-8',xml_declaration=True)
    files['Metadata/plate_1.png']=png.read_bytes()
    temporary=path.with_suffix('.writing')
    with zipfile.ZipFile(temporary,'w',zipfile.ZIP_DEFLATED) as z:
        for n,b in files.items():z.writestr(n,b)
    temporary.replace(path)

def main():
    expected={q['part']:q['quantity'] for q in read(R/'mesh_validation.json')};counts=collections.Counter();results=[]
    for p in sorted(OUT.glob('*.3mf')):
        print('VALIDATING',p.name,flush=True)
        existing=R/'audit'/(p.stem+'_slice_validation.json')
        gc=WORK/p.stem/'plate_1.gcode'
        png=R/'preview'/(p.stem+'_support.png')
        if existing.exists() and gc.exists() and png.exists():
            cached=read(existing)
            if cached['sha256']==hashlib.sha256(p.read_bytes()).hexdigest() and cached['Gcode_sha256']==hashlib.sha256(gc.read_bytes()).hexdigest():
                if not cached.get('thumbnail_added_after_slicing'):
                    thumbnail(p,png);cached['sha256']=hashlib.sha256(p.read_bytes()).hexdigest();cached['thumbnail_added_after_slicing']=True;write(existing,cached)
                counts.update(x['name'] for x in cached['parts']);results.append(cached)
                print('REUSED_VERIFIED',p.name,flush=True);continue
        objects,cfg,xml=meshes(p);folder=WORK/p.stem
        cli=read(folder/'cli_result.json');assert cli['return_code']==0
        gc=folder/'plate_1.gcode';assert gc.exists();paths=toolpaths(gc)
        # These are read back from the slicer's executable G-code, not just copied JSON.
        keys=['layer_height','initial_layer_print_height','wall_loops','sparse_infill_density',
              'infill_wall_overlap','nozzle_temperature','textured_plate_temp','filament_max_volumetric_speed',
              'fan_min_speed','fan_max_speed','xy_hole_compensation','xy_contour_compensation','filament_shrink']
        for k in keys:
            wanted=cfg[k][0] if isinstance(cfg[k],list) else cfg[k]
            assert paths['settings'].get(k)==wanted,(p.name,k,paths['settings'].get(k),wanted)
        label_to_name={}
        for ins in xml.findall('plate/model_instance'):
            d={m.get('key'):m.get('value') for m in ins.findall('metadata')}
            ob=next(o for o in xml.findall('object') if o.get('id')==d['object_id'])
            label_to_name[int(d['identify_id'])]=next(m.get('value') for m in ob.findall('metadata') if m.get('key')=='name')
        parts=[]
        for o in objects:
            name=o['name'];m=o['mesh'];counts[name]+=1
            source=trimesh.load_mesh(R/'STL'/(name+'.stl'))
            assert abs(m.volume/source.volume-1)<1e-5,(name,m.volume,source.volume)
            assert m.is_watertight and m.is_winding_consistent
            assert np.all(m.bounds[0]>=-.001) and np.all(m.bounds[1]<=256.001),(name,m.bounds)
            for k,v in object_settings(name).items():assert o['settings'].get(k)==v,(name,k)
            parts.append(dict(name=name,bounds_mm=m.bounds.round(4).tolist(),CAD_volume_unchanged=True))
        for label,z in paths['maxima'].items():
            name=label_to_name[label]
            actual=next(o['mesh'].bounds[1,2] for o in objects if o['name']==name)
            assert abs(z-actual)<.025,(p.name,name,z,actual)
        assert len(paths['maxima'])==len(objects),(p.name,'missing printed objects',paths['maxima'],label_to_name)
        bounds=paths['bounds'];assert np.all(bounds[0,:2]>=-.03) and np.all(bounds[1,:2]<=256.03),(p.name,bounds)
        # Confirm that the same geometry was actually passed to the slicer.
        sliced=cli['sliced_plates'][0];assert len(sliced['objects'])==len(objects)
        assert collections.Counter(x['name'] for x in sliced['objects'])==collections.Counter(o['name'] for o in objects)
        for obj in sliced['objects']:
            b=obj['bbox'];m=next(o['mesh'] for o in objects if o['name']==obj['name'])
            assert np.allclose([b['width'],b['depth'],b['height']],m.extents,atol=.001)
        print('RENDERING_SUPPORT',p.name,len(paths['support']),flush=True)
        preview(p.stem,objects,paths['support']);thumbnail(p,png)
        result=dict(file=p.name,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),status='PASS_SLICED',
                    object_count=len(objects),estimated_hours=round(sliced['total_predication']/3600,2),
                    estimated_filament_g=round(sum(x['total_used_g'] for x in sliced['filaments']),2),
                    slicer_warning=sliced.get('warning_message',''),generated_support_segments=len(paths['support']),
                    printed_object_max_Z_mm={str(k):v for k,v in paths['maxima'].items()},
                    extruded_path_XY_bounds_mm=bounds[:,:2].round(3).tolist(),features=paths['features'],parts=parts,
                    Gcode_sha256=hashlib.sha256(gc.read_bytes()).hexdigest())
        result['thumbnail_added_after_slicing']=True
        results.append(result);write(R/'audit'/(p.stem+'_slice_validation.json'),result)
        print('VERIFIED',p.name,result['estimated_hours'],'h',result['estimated_filament_g'],'g',repr(result['slicer_warning']),flush=True)
    assert dict(counts)==expected,(dict(counts),expected)
    report=dict(status='PASS_A1_PETG_PROJECTS_AND_TOOLPATHS',printer='Bambu Lab A1',nozzle_mm=.4,
                material='Generic PETG',project_count=len(results),print_objects=sum(counts.values()),STL_types=len(counts),
                estimated_total_hours=round(sum(x['estimated_hours'] for x in results),2),
                estimated_total_filament_g=round(sum(x['estimated_filament_g'] for x in results),2),
                physical_tolerance_measured=False,physical_print_strength_verified=False,plates=results,
                limitations=['Slicer and digital geometry checks do not certify printed fit, surface finish or anisotropic strength.',
                             'Support previews depict generated support paths; removal and surface quality require a physical sample.',
                             'G-code files are QA evidence only; final delivery uses editable 3MF projects to re-slice after filament calibration.'])
    write(R/'audit'/'A1_PETG_print_validation.json',report)
    prov=read(PROFILES/'profile_provenance.json');prov['automatic_slicer_settings_reload_verified']=True;write(PROFILES/'profile_provenance.json',prov)
    print(report['status'],report['estimated_total_hours'],'hours',report['estimated_total_filament_g'],'g')

if __name__=='__main__':main()

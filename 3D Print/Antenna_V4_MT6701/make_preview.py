"""Create an offline WebGL viewer and PNGs directly from exported CAD tessellation."""
from pathlib import Path
import sys,json,math
ROOT=Path(__file__).resolve().parent
runtime=ROOT.parents[2]/'tmp'/'cad_runtime'
if runtime.exists():sys.path.insert(0,str(runtime))
data=json.loads((ROOT/'preview'/'mesh_data.json').read_text(encoding='utf-8'))
if (ROOT/'preview'/'sensor_fasteners.json').exists():data+=json.loads((ROOT/'preview'/'sensor_fasteners.json').read_text(encoding='utf-8'))
html='''<!DOCTYPE html><html lang="vi"><meta charset="utf-8"><title>Antenna V4 · MT6701 · LD-1501MG / GT2-280</title>
<style>*{box-sizing:border-box}body{margin:0;background:#101a23;color:#e8eff3;font:15px system-ui}canvas{width:100vw;height:100vh;display:block}.panel{position:fixed;left:24px;top:24px;width:300px;padding:22px;background:#172733eF;border:1px solid #426074;border-radius:16px}h1{font-size:23px;margin:0 0 7px}p{color:#b1c5d2;line-height:1.5}label{display:block;margin:20px 0 8px}input[type=range]{width:100%;accent-color:#e0a04c}button{border:1px solid #567285;border-radius:7px;color:#d9e7ed;background:#243d50;padding:8px 12px;cursor:pointer}small{color:#aac1cf;line-height:1.6;display:block;margin-top:15px}.badge{color:#edb972;font-size:12px;letter-spacing:1px}.foot{position:fixed;right:24px;bottom:20px;color:#8eacbd}.error{color:#ffb4ac}</style>
<canvas id="c"></canvas><div class="panel"><div class="badge">THẾ GIỚI IC · V4 · mm</div><h1>Antenna hai trục</h1><p>Chảo Ø160 · LD-1501MG 180°<br>17HS1352 · GT2-280 · 80:20 · MT6701 trục ra</p>
<label>Góc nâng <b id="elv">35°</b></label><input id="el" type="range" min="0" max="180" value="35">
<label>Phương vị <b id="azv">0°</b></label><input id="az" type="range" min="-180" max="180" value="0">
<label><input id="hw" type="checkbox" checked> Hiện linh kiện</label>
<button id="reset">Góc nhìn ban đầu</button><small>Kéo chuột: xoay góc nhìn. Cuộn: phóng to.<br>Góc trong trình xem là chuyển động hình học; cần hiệu chỉnh hành trình servo khi lắp thật.</small><p id="err" class="error"></p></div><div class="foot">Mô hình cơ khí thử nghiệm · Chưa kiểm chứng bằng lắp ráp thật</div><script>
const meshes=__DATA__;
const canvas=document.getElementById('c'),gl=canvas.getContext('webgl',{antialias:true});
if(!gl)document.getElementById('err').textContent='Trình duyệt cần hỗ trợ WebGL để xem mô hình.';
function shader(t,s){let x=gl.createShader(t);gl.shaderSource(x,s);gl.compileShader(x);if(!gl.getShaderParameter(x,gl.COMPILE_STATUS))throw Error(gl.getShaderInfoLog(x));return x}
const vs=`attribute vec3 p,n;uniform mat4 vp;uniform float group,el,az;varying vec3 norm;void main(){vec3 q=p;vec3 m=n;float th=0.;if(group>1.5){if(group<2.5){q.z-=8.;th=el-1.5707963268;}else{q.z-=209.;th=el;}mat3 r=mat3(1.,0.,0.,0.,cos(th),sin(th),0.,-sin(th),cos(th));q=r*q;m=r*m;q.z+=209.;}if(group>.5){mat3 r=mat3(cos(az),sin(az),0.,-sin(az),cos(az),0.,0.,0.,1.);q=r*q;m=r*m;}norm=m;gl_Position=vp*vec4(q,1.);}`;
const fs=`precision mediump float;varying vec3 norm;uniform vec3 col;void main(){vec3 n=normalize(norm);if(!gl_FrontFacing)n=-n;float light=.35+.46*max(0.,dot(n,normalize(vec3(-.4,.5,.9))))+.18*max(0.,dot(n,normalize(vec3(.8,-.5,.2))));gl_FragColor=vec4(col*light,1.);}`;
let prog=gl.createProgram();gl.attachShader(prog,shader(gl.VERTEX_SHADER,vs));gl.attachShader(prog,shader(gl.FRAGMENT_SHADER,fs));gl.linkProgram(prog);if(!gl.getProgramParameter(prog,gl.LINK_STATUS))throw Error(gl.getProgramInfoLog(prog));gl.useProgram(prog);
const loc={};for(const k of ['vp','group','el','az','col'])loc[k]=gl.getUniformLocation(prog,k);const pl=gl.getAttribLocation(prog,'p'),nl=gl.getAttribLocation(prog,'n');
function sub(a,b){return a.map((x,i)=>x-b[i])}function cross(a,b){return[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]}function dot(a,b){return a.reduce((s,x,i)=>s+x*b[i],0)}function unit(a){let d=Math.hypot(...a)||1;return a.map(x=>x/d)}
function mult(a,b){let o=Array(16).fill(0);for(let c=0;c<4;c++)for(let r=0;r<4;r++)for(let k=0;k<4;k++)o[c*4+r]+=a[k*4+r]*b[c*4+k];return o}
function view(eye,target){let z=unit(sub(eye,target)),x=unit(cross([0,0,1],z)),y=cross(z,x);return[x[0],y[0],z[0],0,x[1],y[1],z[1],0,x[2],y[2],z[2],0,-dot(x,eye),-dot(y,eye),-dot(z,eye),1]}
function proj(a){let f=1/Math.tan(.55/2),near=2,far=3000;return[f/a,0,0,0,0,f,0,0,0,0,(far+near)/(near-far),-1,0,0,2*far*near/(near-far),0]}
const drawables=meshes.map(m=>{let arr=[];for(const f of m.f){let a=m.v[f[0]],b=m.v[f[1]],c=m.v[f[2]],n=unit(cross(sub(b,a),sub(c,a)));for(const p of[a,b,c])arr.push(...p,...n);}let b=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,b);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array(arr),gl.STATIC_DRAW);return{buffer:b,count:arr.length/6,color:m.color.match(/[0-9a-f]{2}/gi).map(h=>parseInt(h,16)/255),group:({fixed:0,azimuth:1,elevation_local:2,elevation_world:3})[m.group]??1,printed:m.printed}});
let yaw=2.2,pitch=.45,dist=800,drag=false,last=[0,0];const el=document.getElementById('el'),az=document.getElementById('az'),hw=document.getElementById('hw');
canvas.onpointerdown=e=>{drag=true;last=[e.clientX,e.clientY];canvas.setPointerCapture(e.pointerId)};canvas.onpointerup=()=>drag=false;canvas.onpointermove=e=>{if(drag){yaw-=(e.clientX-last[0])*.008;pitch=Math.max(-1.3,Math.min(1.3,pitch+(e.clientY-last[1])*.008));last=[e.clientX,e.clientY]}};
canvas.onwheel=e=>{e.preventDefault();dist=Math.max(180,Math.min(1700,dist*Math.exp(e.deltaY*.001)));};document.getElementById('reset').onclick=()=>{yaw=2.2;pitch=.45;dist=800;el.value=35;az.value=0;hw.checked=true};
function frame(){let d=window.devicePixelRatio||1,w=Math.round(innerWidth*d),h=Math.round(innerHeight*d);if(canvas.width!==w||canvas.height!==h){canvas.width=w;canvas.height=h}gl.viewport(0,0,w,h);gl.clearColor(.055,.095,.13,1);gl.clear(gl.COLOR_BUFFER_BIT|gl.DEPTH_BUFFER_BIT);gl.enable(gl.DEPTH_TEST);let eye=[Math.cos(yaw)*Math.cos(pitch)*dist,Math.sin(yaw)*Math.cos(pitch)*dist,105+Math.sin(pitch)*dist];gl.uniformMatrix4fv(loc.vp,false,new Float32Array(mult(proj(w/h),view(eye,[0,0,105]))));gl.uniform1f(loc.el,el.value*Math.PI/180);gl.uniform1f(loc.az,az.value*Math.PI/180);document.getElementById('elv').textContent=el.value+'°';document.getElementById('azv').textContent=az.value+'°';for(const m of drawables){if(!hw.checked&&!m.printed)continue;gl.bindBuffer(gl.ARRAY_BUFFER,m.buffer);gl.enableVertexAttribArray(pl);gl.enableVertexAttribArray(nl);gl.vertexAttribPointer(pl,3,gl.FLOAT,false,24,0);gl.vertexAttribPointer(nl,3,gl.FLOAT,false,24,12);gl.uniform1f(loc.group,m.group);gl.uniform3fv(loc.col,new Float32Array(m.color));gl.drawArrays(gl.TRIANGLES,0,m.count);}requestAnimationFrame(frame)}frame();
</script></html>'''
(ROOT/'XEM_MO_HINH_3D.html').write_text(html.replace('__DATA__',json.dumps(data,separators=(',',':'))),encoding='utf-8')

import vtk
def xyz(v,group,angle):
    x,y,z=v
    if group=='elevation_local':
        z-=8;a=math.radians(angle-90);y,z=y*math.cos(a)-z*math.sin(a),y*math.sin(a)+z*math.cos(a);z+=209
    elif group=='elevation_world':
        z-=209;a=math.radians(angle);y,z=y*math.cos(a)-z*math.sin(a),y*math.sin(a)+z*math.cos(a);z+=209
    return x,y,z
def render(filename,camera,angle=35,focus=(0,0,105),scale=220,include=None):
    ren=vtk.vtkRenderer();ren.SetBackground(.94,.96,.97)
    for m in data:
        if include is not None and not include(m['name']):continue
        pts=vtk.vtkPoints()
        for v in m['v']:pts.InsertNextPoint(*xyz(v,m['group'],angle))
        cells=vtk.vtkCellArray()
        for f in m['f']:
            cells.InsertNextCell(3)
            for k in f:cells.InsertCellPoint(int(k))
        poly=vtk.vtkPolyData();poly.SetPoints(pts);poly.SetPolys(cells)
        normals=vtk.vtkPolyDataNormals();normals.SetInputData(poly);normals.SetFeatureAngle(50)
        mapper=vtk.vtkPolyDataMapper();mapper.SetInputConnection(normals.GetOutputPort());actor=vtk.vtkActor();actor.SetMapper(mapper)
        c=m['color'];actor.GetProperty().SetColor(*[int(c[i:i+2],16)/255 for i in (1,3,5)])
        actor.GetProperty().SetAmbient(.25);actor.GetProperty().SetDiffuse(.7);actor.GetProperty().SetSpecular(.12)
        ren.AddActor(actor)
    cam=ren.GetActiveCamera();cam.SetPosition(*camera);cam.SetFocalPoint(*focus);cam.SetViewUp(0,0,1);cam.ParallelProjectionOn();cam.SetParallelScale(scale)
    win=vtk.vtkRenderWindow();win.SetOffScreenRendering(1);win.AddRenderer(ren);win.SetSize(1300,1100);win.SetMultiSamples(8);win.Render()
    image=vtk.vtkWindowToImageFilter();image.SetInput(win);image.Update();writer=vtk.vtkPNGWriter();writer.SetFileName(str(ROOT/'preview'/filename));writer.SetInputConnection(image.GetOutputPort());writer.Write();win.Finalize()
render('assembly_front.png',(-360,480,390))
render('assembly_rear.png',(-400,-460,340))
render('elevation_0.png',(-360,480,330),0)
render('elevation_90.png',(-360,480,330),90)
render('elevation_180.png',(-360,480,330),180)
render('MT6701_underside.png',(85,-110,-95),focus=(0,0,-22),scale=53,
       include=lambda n:n.startswith(('22_','24_','25_','MT6701','4x2_','sensor_','magnet_cap_','azimuth_8mm')))
print('Offline viewer and six CAD previews exported.')

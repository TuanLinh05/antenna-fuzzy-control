"""Schematic dimension views derived from V4 parameters; not 1:1 print templates."""
from pathlib import Path
import sys,json,math
R=Path(__file__).resolve().parent
sys.path.insert(0,str(R.parents[2]/'tmp/cad_runtime'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle,Circle,Polygon,Arc
import numpy as np
p=json.loads((R/'parameters.json').read_text());out=R/'preview'
blue='#3f6579';orange='#e0a04c';green='#287362'
fig,axes=plt.subplots(1,2,figsize=(14,7),layout='constrained')
a,b=axes
a.add_patch(Rectangle((-22,-22),44,44,fill=False,ec=orange,lw=3))
a.add_patch(Rectangle((-11.5,-11.5),23,23,fc='#d8ebe5',ec=green,lw=2))
for x in (-9,9):
    for y in (-9,9):a.add_patch(Circle((x,y),1,fc='white',ec=green,lw=1.5))
for x in (-18,18):
    for y in (-18,18):
        a.add_patch(Rectangle((x-3.2,y-3.2),6.4,6.4,fc='#fff2dd',ec=orange))
        a.add_patch(Circle((x,y),1.5,fc='#82939f'))
a.add_patch(Rectangle((-2.5,-2),5,4,fc='#34383d'))
a.annotate('',(-9,13),(9,13),arrowprops=dict(arrowstyle='<->'))
a.text(0,14,'18 mm hole pitch (derived)',ha='center')
a.annotate('',(-11.5,-15),(11.5,-15),arrowprops=dict(arrowstyle='<->'))
a.text(0,-17,'23 x 23 mm PCB; holes ~2 mm',ha='center')
a.text(0,-25,'PCB slots also accept 17.5 mm reference pattern.\nCarrier XY adjustment: +/-1.5 mm; align the IC center.',ha='center',va='top')
a.set(xlim=(-28,28),ylim=(-33,28),title='MT6701 top view - nominal dimensions')
for x in (-18,18):
    b.add_patch(Rectangle((x-1.5,-40),3,25,fc='#9ba7b0'))
    for z in (-33.4,-28.6):b.add_patch(Rectangle((x-2.75,z),5.5,2.4,fc='#aab4bb',ec='#657986'))
b.add_patch(Rectangle((-40,-40),80,4,fc=blue))
b.add_patch(Rectangle((-22,-31),44,2.4,fc=orange))
for x in (-9,9):b.add_patch(Rectangle((x-2.6,-28.6),5.2,4.3,fc=orange))
b.add_patch(Rectangle((-11.5,-24.3),23,1.6,fc=green))
b.add_patch(Rectangle((-2.5,-22.7),5,1.7,fc='#34383d'))
b.add_patch(Rectangle((-4,-14),8,17,fc='#aab4bb',ec='#657986'))
b.add_patch(Rectangle((-10,-17.5),20,11.5,fc=orange,alpha=.7))
b.add_patch(Rectangle((-4.5,-20),9,2.5,fc=orange,alpha=.7))
b.add_patch(Rectangle((-2,-20),4,2,fc='#d6dce1',ec='#657986'))
b.annotate('Gap 1.0 mm nominal\n(magnet face to IC)',(2.3,-20.5),(13,-15),arrowprops=dict(arrowstyle='->'))
b.annotate('4 x 2 mm magnet\nFlush face; adhesive behind',(0,-19),(13,-5),arrowprops=dict(arrowstyle='->'))
b.annotate('M3x25 studs\nTwo nuts per stud\nSet height and level',(18,-30),(26,-27),arrowprops=dict(arrowstyle='->'))
b.text(10,-45,'IC height 1.7 mm / PCB thickness 1.6 mm: assumptions.\nSet the actual gap to 0.5-2.0 mm; verify the signal.',ha='center',va='top',fontsize=9)
b.set(xlim=(-44,65),ylim=(-51,5),title='Sensor side section - adjustment and gap')
for ax in axes:ax.set_aspect('equal');ax.set_xlabel('mm');ax.set_ylabel('mm');ax.grid(alpha=.15)
fig.suptitle('Antenna V4 - MT6701 output-shaft mounting',fontsize=17)
fig.savefig(out/'MT6701_dimensions.png',dpi=180);plt.close(fig)
fig,ax=plt.subplots(figsize=(12,5),layout='constrained')
c=p['motor_center_distance'];big=80/math.pi;small=20/math.pi;a=math.acos((big-small)/c)
xy=[(big*math.cos(t),big*math.sin(t)) for t in np.linspace(a,2*math.pi-a,500)]
xy += [(c+small*math.cos(t),small*math.sin(t)) for t in np.linspace(-a,a,200)]
ax.add_patch(Polygon(xy,closed=True,fill=False,ec='#34383d',lw=3))
for x,rad,label in [(0,big,'80T driven'),(c,small,'20T motor')]:
    ax.add_patch(Circle((x,0),rad,fill=False,ls='--',ec=blue));ax.plot(x,0,'+',color=blue);ax.text(x,0,label,ha='center',va='bottom')
ax.annotate('',(0,-34),(c,-34),arrowprops=dict(arrowstyle='<->'))
ax.text(c/2,-38,f'Nominal center distance = {c:.4f} mm',ha='center')
ax.text(c/2,33,'GT2: pitch 2 mm; closed-loop belt 280 mm; width 6 mm; ratio 4:1',ha='center')
ax.text(c/2,-45,'Motor slides +/-5 mm for tension. Final pretension and tooth fit require a physical belt.',ha='center')
ax.set(xlim=(-34,c+21),ylim=(-50,40),aspect='equal',xlabel='mm',ylabel='mm',title='Exact pitch-line layout - geometry, not belt material validation')
ax.grid(alpha=.15);fig.savefig(out/'GT2_transmission_dimensions.png',dpi=180);plt.close(fig)
print('Dimension views exported')

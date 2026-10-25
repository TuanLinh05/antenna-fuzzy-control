// MT6701 rear-motor adapter. Units: mm. FIT-TEST REVISION v2: adjustable PCB holes and matching floating nuts.
// Motor 31 x 31 is physically reported to fit. PCB 17.5 is a photo-based trial estimate.
// Verify screw thread, clearances and actual magnetic gap before final use.
// F6 Render, then Export STL. Select part below.
part = "adapter"; // [adapter,pcb_gauge,gauge,shims,assembly]
motor_pitch_x = 31;
motor_pitch_y = 31;
pcb_pitch_x = 17.5;
pcb_pitch_y = 17.5;
pcb_size = 23;
// IC offset from PCB geometric center; measure if centering needs correction.
ic_offset_x = 0;
ic_offset_y = 0;
outer_size = 42;
inner_size = 29;
base_h = 2.4;
pcb_seat_h = 3.2;
motor_clearance = 3.6; // ASSUMED M3 clearance, not confirmed motor thread.
slot_move = 0.8; // independent +/- XY adjustment at each motor hole.
pcb_clearance = 2.3;
pcb_radial_move = 0.35; // mm each way, along corner diagonal; total travel 0.7.
pcb_pad_d = 7.4;
nut_af = 4.3; // M2 hex nut: nominal AF 4 mm + print clearance.
nut_depth = 1.8;
pcb_t_assumed = 1.6;
chip_h_assumed = 1.7;
magnet_top_assumed = 0.5;
$fn = 96;
eps = 0.02;

assert(pcb_seat_h >= base_h);
assert(pcb_seat_h - nut_depth >= 1.0);
assert(pcb_pad_d/2 - nut_af/sqrt(3) - pcb_radial_move >= 0.8);

function mp(sx,sy) = [sx*motor_pitch_x/2,sy*motor_pitch_y/2];
function pp(sx,sy) = [sx*pcb_pitch_x/2-ic_offset_x,
                      sy*pcb_pitch_y/2-ic_offset_y];
module rounded_rect(w,h,r) { offset(r=r) square([w-2*r,h-2*r],center=true); }
module pad_at(p,d) { translate(p) circle(d=d); }
module pcb_pads_2d() {
  for(sx=[-1,1],sy=[-1,1]) pad_at(pp(sx,sy),pcb_pad_d);
}
module body_2d() {
  union() {
    difference() {
      rounded_rect(outer_size,outer_size,4);
      rounded_rect(inner_size,inner_size,3);
    }
    for(sx=[-1,1],sy=[-1,1]) hull() {
      pad_at(mp(sx,sy),10);
      pad_at(pp(sx,sy),pcb_pad_d);
    }
  }
}
module motor_slots_2d() {
  for(sx=[-1,1],sy=[-1,1]) translate(mp(sx,sy)) hull()
    for(dx=[-slot_move,slot_move],dy=[-slot_move,slot_move])
      translate([dx,dy]) circle(d=motor_clearance);
}
module radial_sweep(sx,sy) {
  hull() for(t=[-pcb_radial_move,pcb_radial_move])
    translate([sx*t/sqrt(2),sy*t/sqrt(2)]) children();
}
module pcb_holes_2d() {
  for(sx=[-1,1],sy=[-1,1]) translate(pp(sx,sy))
    radial_sweep(sx,sy) circle(d=pcb_clearance);
}
module adapter() {
  difference() {
    union() {
      linear_extrude(base_h) body_2d();
      linear_extrude(pcb_seat_h) pcb_pads_2d();
    }
    translate([0,0,-eps]) linear_extrude(pcb_seat_h+2*eps) {
      motor_slots_2d(); pcb_holes_2d();
    }
    translate([0,0,-eps]) linear_extrude(nut_depth+eps)
      for(sx=[-1,1],sy=[-1,1]) translate(pp(sx,sy))
        radial_sweep(sx,sy) circle(r=nut_af/sqrt(3),$fn=6);
  }
}
module gauge() {
  linear_extrude(1) difference() {
    body_2d(); motor_slots_2d(); pcb_holes_2d();
  }
}
module pcb_gauge() {
  linear_extrude(1) difference() {
    rounded_rect(25,25,1.5);
    rounded_rect(16,16,2);
    pcb_holes_2d();
  }
}
module shims() {
  for(row=[0,1],col=[0:3]) translate([col*9,row*10,0])
    linear_extrude(row==0 ? 0.5 : 1.0) difference() {
      circle(d=pcb_pad_d); circle(d=pcb_clearance);
    }
}
module assembly() {
  color([0.91,0.46,0.12]) adapter();
  // Ghost motor and PCB are preview only and cannot be exported into STL.
  %color([0.35,0.38,0.42]) translate([-21,-21,-15]) cube([42,42,15]);
  %color([0.08,0.25,0.21]) translate([-pcb_size/2-ic_offset_x,
    -pcb_size/2-ic_offset_y,pcb_seat_h]) cube([pcb_size,pcb_size,pcb_t_assumed]);
  %color([0.1,0.1,0.1]) translate([-2.5,-2,pcb_seat_h-chip_h_assumed])
    cube([5,4,chip_h_assumed]);
  %color([0.7,0.7,0.7]) translate([0,0,magnet_top_assumed-2]) cylinder(d=4,h=2);
}
if(part=="adapter") adapter();
else if(part=="pcb_gauge") pcb_gauge();
else if(part=="gauge") gauge();
else if(part=="shims") shims();
else if(part=="assembly") assembly();

module rotors(){
    offset1 = 80;
    offset2 = 80;
    offset3 = sqrt(pow(R1+R2+20,2) - pow( R2 ,2)   );
    translate([0,-R1-offset1,0]) cylinder(r1=R1, r2=R1, h=3, $fn=40);
    translate([0,R1+offset1,0]) cylinder(r1=R1, r2=R1, h=3, $fn=40);
    translate([-R2-offset2,0,0]) cylinder(r1=R2, r2=R2, h=3);
    translate([R2+offset2,0,0]) cylinder(r1=R2, r2=R2, h=3);
}




module HullCore(){
    frac = 1/100;
    h_coef = H0/100;
    form_coef = 1/200;
    for(i=[-50:50]){
        dd = 50-abs(i);
        translate([0,0, h_coef*i])
        scale([  1.1*pow(frac*dd*2, 0.1)  ,  1.1*pow(frac*dd*2, 0.1)  ,  h_coef  ])
        hull() {
            rotors();
        }
    }
}


module HU(){    
    difference(){
        HullCore();
        translate([0,0,-(H0+2)/2])
        scale([1,1,H0+2])
        rotors();
    }
}

module SideRotor(){
    translate([0,0,-5])
    difference(){
        cylinder(r1=R2-1, r2=R2-1, h=10, $fn=50);
        translate([0,0,-5])
        cylinder(r1=R2-3, r2=R2-3, h=20, $fn=50);
    }
}

module MainRotor(){
    h_ = 15;
    translate([0,0,-h_/2])
    
    difference(){
        cylinder(r1=R1-1, r2=R1-1, h=h_, $fn=100);
        translate([0,0,-1])
        cylinder(r1=R1-3, r2=R1-3, h=h_+2, $fn=100);
    }
}


module Combined(){
    HU();
    translate([R2+80,0,0]) rotate([tilt1,tilt2,tilt3]) SideRotor();
    translate([-R2-80,0,0]) rotate([tilt1,tilt2,tilt3]) SideRotor();
    translate([0,R1+80,0]) rotate([tilt1,tilt2,tilt3]) MainRotor();
    translate([0,-R1-80,0]) rotate([tilt1,tilt2,tilt3]) MainRotor();
}

module FloorPlate(){
    a = tile_d/2.0;
    translate([-a,-a,-100]) cube([tile_d,tile_d,1]);
}

module HexTile(){
    a = tile_d/2.0;
    color([0.2, 0.6, 0.6]) translate([0,0,-tile_h]) cylinder(r1=tile_d, r2=tile_d, h=tile_h, $fn=6);
}


module Floor(){
    floor_r_i = floor(floor_r*1.6);
    floor_r_j = floor(floor_r*1.6);
    for(i=[-floor_r_i:floor_r_i]){
        for(j=[-floor_r_j:floor_r_j]){
            i2 = floor(i/2);
            ic = i-i2;
            j2 = floor(j/2);
            jc = j-j2;
            os = abs(i%2);
            
            x = +(ic*tile_sep*c30)+(i2*tile_sep*c30);
            y = +(jc*tile_sep*1)+(j2*tile_sep*0)+os*tile_sep*s30;
            
            if(sqrt(x*x+y*y) < floor_r*tile_d){
                
                translate([x,y,0]) HexTile();
            }
        }
    }
}
    

//translate([-1,-1,0]) cube([2,2,40]);

Combined();
//translate([0,0,0]) cube([440,1,50], center=true);

//translate([0,0,0]) cube([1,704,50], center=true);

//translate([-220,-352,0]) cube([220,352,2]);


//HU();
//MainRotor();
//SideRotor();

//Floor();


/*
translate([0,0,0]) HexTile();
translate([0,tile_sep,0]) HexTile();
translate([0,-tile_sep,0]) HexTile();
translate([tile_sep*c30,tile_sep*s30,0]) HexTile();
translate([tile_sep*c30,-tile_sep*s30,0]) HexTile();
translate([-tile_sep*c30,tile_sep*s30,0]) HexTile();
translate([-tile_sep*c30,-tile_sep*s30,0]) HexTile();
*/


tilt1 = 20;
tilt2 = 20;
tilt3 = 0;

H0 = 40;
R1 = 120;
R2 = 60;

c30 = cos(30);
s30 = sin(30);
tile_d = 300;
tile_h = 10;
tile_sep = c30*tile_d*2 + tile_d/6;
floor_r = 40;



A_tot = (3.141*R1*R1*2 + 3.141*R2*R2*2)/10000;
P = 12.5 * pow(   pow(150,3)/A_tot   ,0.5);
P_emp = 130000/(20.0);

echo("A=", A_tot, "P=",P, "P_emp=",P_emp);











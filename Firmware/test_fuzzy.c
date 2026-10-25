#include "fuzzy_controller.h"
#include <stdio.h>
#include <math.h>
#include <stdlib.h>
int main(int argc,char**argv){
    int checks=0;
    for(int i=-100;i<=100;i++)for(int j=-100;j<=100;j++){
        float x=i/100.0f,y=j/100.0f,z=antenna_fuzzy(x,y);
        if(!isfinite(z)||fabsf(z)>1.000001f||fabsf(z+antenna_fuzzy(-x,-y))>2e-6f)return 1;
        if(i<100&&antenna_fuzzy(x+.01f,y)+2e-6f<z)return 2;
        checks++;
    }
    if(antenna_encoder_delta(0,65535)!=1||antenna_encoder_delta(65535,0)!=-1)return 3;
    if(antenna_encoder_delta(103,100)!=3||antenna_encoder_delta(100,103)!=-3)return 4;
    if(antenna_velocity(0,0)!=0||antenna_velocity(.001f,0)!=0)return 5;
    if(fabsf(antenna_velocity(10,0))>.470001f)return 6;
    if(argc==2){
        FILE*f=fopen(argv[1],"w");if(!f)return 7;
        fputs("error_normalized,derivative_normalized,C_single_output\n",f);
        for(int i=-20;i<=20;i++)for(int j=-20;j<=20;j++)
            fprintf(f,"%.8g,%.8g,%.9g\n",i/20.0,j/20.0,antenna_fuzzy(i/20.0f,j/20.0f));
        fclose(f);
    }
    printf("PASS: %d fuzzy grid points; symmetry, bounds, monotonicity, wrap, deadband\n",checks);
    return 0;
}

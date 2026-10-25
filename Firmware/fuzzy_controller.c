#include "fuzzy_controller.h"
#include <math.h>
static float clamp(float x,float lo,float hi){return x<lo?lo:(x>hi?hi:x);}
float antenna_fuzzy(float e,float de){
    /* Zero-order Sugeno: five triangular sets/input, product AND, 25 rules.
       Singleton(i,j)=sat(2*centre(i)+0.5*centre(j)), weighted average.
       MATLAB creates and independently checks an equivalent .fis file. */
    float a[5],b[5],sum=0.0f,weight=0.0f;
    e=clamp(e,-1.0f,1.0f);de=clamp(de,-1.0f,1.0f);
    for(int i=0;i<5;i++){
        float c=-1.0f+0.5f*(float)i;
        a[i]=fmaxf(0.0f,1.0f-2.0f*fabsf(e-c));
        b[i]=fmaxf(0.0f,1.0f-2.0f*fabsf(de-c));
    }
    for(int i=0;i<5;i++)for(int j=0;j<5;j++){
        float w=a[i]*b[j];
        float z=clamp(2.0f*(-1.0f+0.5f*i)+0.5f*(-1.0f+0.5f*j),-1.0f,1.0f);
        sum+=w*z;weight+=w;
    }
    return weight>0.0f?sum/weight:0.0f;
}
float antenna_velocity(float error,float velocity){
    float result=0.47f*antenna_fuzzy(error/0.15f,-velocity/0.47f);
    /* Stopping-distance governor is explicitly separate from fuzzy inference. */
    float braking=sqrtf(2.0f*0.523598776f*fabsf(error));
    result=clamp(result,-braking,braking);
    if(fabsf(error)<0.12f*ANTENNA_PI/180.0f)result=0.0f;
    return result;
}
int32_t antenna_encoder_delta(uint16_t now,uint16_t previous){
    uint32_t d=(uint16_t)(now-previous);
    return d>32767u?(int32_t)d-65536:(int32_t)d;
}

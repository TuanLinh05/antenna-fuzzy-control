/* Standalone F103C8 firmware. No HAL dependency. Prototype, not hardware tested.
   HSI 8 MHz; verify clock/pulse widths on the actual board before loading servo.
   PA0/1 TIM2 encoder; PA6 TIM3 STEP; PA7 DIR; PB6 TIM4 inverted servo PWM;
   PA9/10 USART1 115200 8N1. External NPN stages as documented are REQUIRED.
   Commands in integer degrees: Z, G <az> <el>, H, S, ?. Newline terminates.
   Z sets a manually aligned zero; it does not home the mechanism. */
#include "fuzzy_controller.h"
#include <stdint.h>
#include <math.h>
#define REG(a) (*(volatile uint32_t*)(uintptr_t)(a))
#define RCC 0x40021000u
#define GPIOA 0x40010800u
#define GPIOB 0x40010C00u
#define TIM2 0x40000000u
#define TIM3 0x40000400u
#define TIM4 0x40000800u
#define UART 0x40013800u
#define ENCODER_SIGN 1
#define MOTOR_SIGN 1
static volatile uint32_t ms;
static volatile int32_t command_steps;
static volatile int direction=1,running;
static int homed,fault;
static int32_t counts;
static uint16_t encoder_last;
static float goal,el_goal=90.0f,filtered_w,command_w;
static uint32_t heartbeat,tracking_ms,guard_until;
static char receive[48];static unsigned receive_n;
static char transmit[180];static unsigned tx_head,tx_tail;
extern uint32_t _sidata,_sdata,_edata,_sbss,_ebss;

static float limit(float x,float lo,float hi){return x<lo?lo:(x>hi?hi:x);}
static void pin_mode(uint32_t port,int pin,uint32_t mode){
    uint32_t address=port+(pin<8?0u:4u);unsigned sh=4u*(unsigned)(pin&7);
    REG(address)=(REG(address)&~(15u<<sh))|(mode<<sh);
}
static void enqueue(char c){unsigned next=(tx_head+1u)%sizeof(transmit);if(next!=tx_tail){transmit[tx_head]=c;tx_head=next;}}
static void put_integer(int32_t n){char s[12];unsigned k=0;if(n<0){enqueue('-');n=-n;}do{s[k++]=(char)('0'+n%10);n/=10;}while(n&&k<sizeof(s));while(k)enqueue(s[--k]);}
static void telemetry(void){
    /* CSV: ms, measured millidegrees, target millidegrees, velocity mdeg/s,
       fault bit mask, zeroed. Nonblocking ring avoids control-loop UART waits. */
    put_integer((int32_t)ms);enqueue(',');put_integer(counts*150);enqueue(',');
    put_integer((int32_t)(goal*180000.0f/ANTENNA_PI));enqueue(',');
    put_integer((int32_t)(filtered_w*180000.0f/ANTENNA_PI));enqueue(',');
    put_integer(fault);enqueue(',');put_integer(homed);enqueue('\n');
}
static void step_stop(void){
    if(running)while(REG(TIM3+0x24)<5u){} /* Complete any 50 us pulse. */
    REG(TIM3)=0;REG(TIM3+0x0c)=0;REG(TIM3+0x20)=0;REG(TIM3+0x10)=0;
    REG(0xe000e280u)=1u<<29;running=0; /* Clear pending TIM3 IRQ only. */
}
static void step_velocity(float velocity){
    float f=fabsf(velocity)/ANTENNA_STEP_RAD;
    int requested=velocity>=0?1:-1;
    if(f<1.6f){step_stop();return;}
    if(requested!=direction){step_stop();direction=requested;guard_until=ms+1u;
        REG(GPIOA+0x10)=((direction*MOTOR_SIGN)>0)?(1u<<7):(1u<<23);return;}
    if((int32_t)(ms-guard_until)<0)return;
    uint32_t period=(uint32_t)(100000.0f/f+.5f);
    if(period<94u)period=94u;
    if(period>65535u)period=65535u;
    REG(TIM3+0x2c)=period-1u; /* Preloaded ARR; never force UG while running. */
    if(!running){
        REG(TIM3+0x14)=1;REG(TIM3+0x10)=0;REG(TIM3+0x0c)=1;
        running=1;REG(TIM3+0x20)=1;REG(TIM3)=129;
        command_steps+=direction; /* Initial PWM pulse, then update IRQ per pulse. */
    }
}
void TIM3_IRQHandler(void){if(REG(TIM3+0x10)&1u){REG(TIM3+0x10)=0;if(running)command_steps+=direction;}}
void SysTick_Handler(void){ms++;}

static int parse_number(const char**s,int*value){
    while(**s==' ')++*s;
    int sign=1,n=0,digits=0;
    if(**s=='-'){sign=-1;++*s;}else if(**s=='+')++*s;
    while(**s>='0'&&**s<='9'){if(++digits>3)return 0;n=n*10+(**s-'0');++*s;}
    if(!digits)return 0;
    *value=sign*n;return 1;
}
static void command(const char*s){
    if(s[0]=='H'&&s[1]==0){heartbeat=ms;return;}
    if(s[0]=='S'&&s[1]==0){step_stop();command_w=0;fault|=16;return;}
    if(s[0]=='?'&&s[1]==0){telemetry();return;}
    if(s[0]=='Z'&&s[1]==0){
        step_stop();counts=0;command_steps=0;encoder_last=(uint16_t)REG(TIM2+0x24);
        filtered_w=0;command_w=0;goal=0;fault=0;tracking_ms=0;homed=1;heartbeat=ms;return;
    }
    if(s[0]=='G'&&s[1]==' '){int a,e;const char*p=s+2;
        if(parse_number(&p,&a)&&parse_number(&p,&e)){
            while(*p==' ')p++;
            if(*p==0&&a>=-150&&a<=150&&e>=45&&e<=135&&homed&&!fault){
                goal=a*ANTENNA_PI/180.0f;el_goal=(float)e;heartbeat=ms;return;
            }
        }
    }
    enqueue('E');enqueue('R');enqueue('R');enqueue('\n');
}
static void control(uint32_t elapsed){
    uint16_t encoder_now=(uint16_t)REG(TIM2+0x24);
    int32_t delta=ENCODER_SIGN*antenna_encoder_delta(encoder_now,encoder_last);
    encoder_last=encoder_now;counts+=delta;
    float dt=elapsed*.001f,theta=counts*ANTENNA_ENCODER_RAD;
    filtered_w=.85f*filtered_w+.15f*(delta*ANTENNA_ENCODER_RAD/dt);
    if(elapsed>20u)fault|=8;
    if(homed&&ms-heartbeat>2000u)fault|=1;
    if(fabsf(theta)>155.0f*ANTENNA_PI/180.0f)fault|=2;
    float disagreement=fabsf(command_steps*ANTENNA_STEP_RAD-theta);
    if(homed&&disagreement>5.0f*ANTENNA_PI/180.0f){tracking_ms+=elapsed;if(tracking_ms>=300u)fault|=4;}
    else tracking_ms=0;
    if(!homed||fault){step_stop();command_w=0;return;}
    float desired=antenna_velocity(goal-theta,filtered_w);
    command_w+=limit(desired-command_w,-.523598776f*dt,.523598776f*dt);
    step_velocity(command_w);
    /* 1000..2000 us = nominal 45..135 degrees per seller, conservative startup range.
       0.5..2.5 ms full travel requires physical calibration, not a firmware promise. */
    REG(TIM4+0x34)=(uint32_t)(1000.0f+(el_goal-45.0f)*(1000.0f/90.0f)+.5f);
}
static void setup(void){
    REG(0xe000ed08u)=0x08000000u;
    REG(RCC)|=1u;while(!(REG(RCC)&2u)){}REG(RCC+4)=0;while(REG(RCC+4)&12u){}
    REG(RCC+0x18)|=(1u<<0)|(1u<<2)|(1u<<3)|(1u<<14);
    REG(RCC+0x1c)|=7u;
    pin_mode(GPIOA,0,8);pin_mode(GPIOA,1,8);REG(GPIOA+0x10)=3u;
    pin_mode(GPIOA,6,11);pin_mode(GPIOA,7,2);REG(GPIOA+0x10)=1u<<7;
    pin_mode(GPIOB,6,11);pin_mode(GPIOA,9,11);pin_mode(GPIOA,10,4);
    REG(TIM2+0x28)=0;REG(TIM2+0x2c)=65535;REG(TIM2+0x18)=0x6161;
    REG(TIM2+8)=3;REG(TIM2+0x20)=0x11;REG(TIM2)=1;
    REG(TIM3+0x28)=79;REG(TIM3+0x34)=5;REG(TIM3+0x18)=0x68;
    REG(0xe000e100u)=1u<<29;
    REG(TIM4+0x28)=7;REG(TIM4+0x2c)=19999;REG(TIM4+0x34)=1500;
    REG(TIM4+0x18)=0x78;REG(TIM4+0x20)=1;REG(TIM4+0x14)=1;REG(TIM4)=129;
    REG(UART+8)=69;REG(UART+0x0c)=(1u<<13)|(1u<<3)|(1u<<2);
    REG(0xe000e014u)=7999;REG(0xe000e018u)=0;REG(0xe000e010u)=7;
    REG(0x40003000u)=0x5555;REG(0x40003004u)=4;REG(0x40003008u)=625;
    REG(0x40003000u)=0xcccc;REG(0x40003000u)=0xaaaa;
}
int main(void){
    setup();uint32_t last_control=ms,last_report=ms;
    encoder_last=(uint16_t)REG(TIM2+0x24);
    for(;;){
        uint32_t now=ms;
        if(now-last_control>=10u){uint32_t d=now-last_control;last_control=now;control(d);REG(0x40003000u)=0xaaaa;}
        if(now-last_report>=200u){last_report=now;telemetry();}
        if((REG(UART)&(1u<<7))&&tx_tail!=tx_head){REG(UART+4)=(uint8_t)transmit[tx_tail];tx_tail=(tx_tail+1u)%sizeof(transmit);}
        if(REG(UART)&(1u<<5)){
            char c=(char)REG(UART+4);
            if(c=='\r')continue;
            if(c=='\n'){receive[receive_n]=0;command(receive);receive_n=0;}
            else if(receive_n<sizeof(receive)-1u)receive[receive_n++]=c;
            else{receive_n=0;fault|=32;step_stop();}
        }
    }
}
void Default_Handler(void){step_stop();for(;;){}}
void Reset_Handler(void){
    uint32_t*src=&_sidata;for(uint32_t*d=&_sdata;d<&_edata;) *d++=*src++;
    for(uint32_t*d=&_sbss;d<&_ebss;) *d++=0;
    (void)main();for(;;){}
}

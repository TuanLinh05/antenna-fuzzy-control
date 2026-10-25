.syntax unified
.cpu cortex-m3
.thumb
.section .isr_vector,"a",%progbits
.word _estack
.word Reset_Handler
.rept 13
.word Default_Handler
.endr
.word SysTick_Handler
.rept 29
.word Default_Handler
.endr
.word TIM3_IRQHandler
.rept 30
.word Default_Handler
.endr

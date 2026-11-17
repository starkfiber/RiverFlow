#include <stdint.h>
#include <stdio.h>
#include <time.h>
#include <string.h>
#include <stdlib.h>
int baseline_aead(void*);int candidate_aead(void*);
static volatile unsigned sink;
static uint64_t ns(void){struct timespec t;clock_gettime(CLOCK_MONOTONIC,&t);return (uint64_t)t.tv_sec*1000000000+t.tv_nsec;}
static void put(uint8_t*p,uint64_t v){memcpy(p,&v,8);}
static double measure(int(*f)(void*),int n,int an,int iters){uint8_t c[96]={0},a[128],d[128],tag[16];for(int i=0;i<128;i++)a[i]=i*7,d[i]=i*13;for(int i=0;i<44;i++)c[8+i]=i+17;put(c+56,(uintptr_t)a);put(c+64,an);put(c+72,(uintptr_t)d);put(c+80,n);put(c+88,(uintptr_t)tag);
 for(int i=0;i<20;i++)sink+=f(c);uint64_t start=ns();for(int i=0;i<iters;i++){c[40]=(uint8_t)i;sink+=f(c);sink+=tag[0];}return (double)(ns()-start)/iters;}
int main(int argc,char**argv){int iters=argc>1?atoi(argv[1]):4000;int lens[]={0,16,64,128,72};puts("trial,data_bytes,aad_bytes,baseline_ns,candidate_ns,order");for(int k=0;k<5;k++)for(int t=0;t<11;t++){double b,c;if(t%2){c=measure(candidate_aead,lens[k],k==4?40:32,iters);b=measure(baseline_aead,lens[k],k==4?40:32,iters);}else{b=measure(baseline_aead,lens[k],k==4?40:32,iters);c=measure(candidate_aead,lens[k],k==4?40:32,iters);}printf("%d,%d,%d,%.3f,%.3f,%s\n",t,lens[k],k==4?40:32,b,c,t%2?"CB":"BC");fflush(stdout);}return 0;}

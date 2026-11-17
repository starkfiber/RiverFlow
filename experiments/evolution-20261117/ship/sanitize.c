#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include <stdio.h>
int baseline_aead(void*);int candidate_aead(void*);
static uint64_t rng=131117;
static unsigned rnd(void){rng^=rng<<13;rng^=rng>>7;rng^=rng<<17;return (unsigned)rng;}
static void put(unsigned char*p,uint64_t v){memcpy(p,&v,8);}
int main(void){for(int j=0;j<10000;j++){size_t n=rnd()%129,an=rnd()%129;unsigned char *a=malloc(an?an:1),*b=malloc(n?n:1),*c=malloc(n?n:1),t[16]={0},u[16]={0},x[96]={0},y[96]={0};for(size_t i=0;i<an;i++)a[i]=rnd();for(size_t i=0;i<n;i++)b[i]=c[i]=rnd();for(int i=0;i<44;i++)x[8+i]=rnd();put(x+56,(uintptr_t)a);put(x+64,an);put(x+72,(uintptr_t)b);put(x+80,n);put(x+88,(uintptr_t)t);memcpy(y,x,96);put(y+72,(uintptr_t)c);put(y+88,(uintptr_t)u);assert(baseline_aead(x)==0&&candidate_aead(y)==0);assert(!memcmp(b,c,n)&&!memcmp(t,u,16));put(x,1);put(y,1);assert(baseline_aead(x)==0&&candidate_aead(y)==0);assert(!memcmp(b,c,n));free(a);free(b);free(c);}
 unsigned char c[96]={0};put(c+64,129);assert(candidate_aead(c)==2);put(c+64,0);put(c+80,129);assert(candidate_aead(c)==2);puts("10000 ASan/UBSan baseline/candidate seal/open comparisons passed; oversize null-pointer contexts refuse");return 0;}

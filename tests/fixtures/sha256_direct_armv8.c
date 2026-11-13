/* Independent development comparator. Requires ARM SHA2; not an RF2 runtime dependency.
 * Uses the documented ARM SHA intrinsics and the same block/padding contract.
 * Static digest/state are deliberately nonreentrant, matching the RF2 scratch API.
 */
#include <arm_neon.h>
#include <stdint.h>
#include <string.h>
static const uint32_t constants[64]={1116352408,1899447441,3049323471,3921009573,961987163,1508970993,2453635748,2870763221,3624381080,310598401,607225278,1426881987,1925078388,2162078206,2614888103,3248222580,3835390401,4022224774,264347078,604807628,770255983,1249150122,1555081692,1996064986,2554220882,2821834349,2952996808,3210313671,3336571891,3584528711,113926993,338241895,666307205,773529912,1294757372,1396182291,1695183700,1986661051,2177026350,2456956037,2730485921,2820302411,3259730800,3345764771,3516065817,3600352804,4094571909,275423344,430227734,506948616,659060556,883997877,958139571,1322822218,1537002063,1747873779,1955562222,2024104815,2227730452,2361852424,2428436474,2756734187,3204031479,3329325298};
static void compress(uint32_t state[8],const unsigned char *p,size_t blocks){
 uint32x4_t a=vld1q_u32(state),b=vld1q_u32(state+4);
 for(size_t i=0;i<blocks;i++,p+=64){
  uint32x4_t saved_a=a,saved_b=b,w[4];
  for(int j=0;j<4;j++)w[j]=vreinterpretq_u32_u8(vrev32q_u8(vld1q_u8(p+j*16)));
  #pragma clang loop unroll(full)
  for(int g=0;g<16;g++){
   uint32x4_t wk=vaddq_u32(w[g&3],vld1q_u32(constants+g*4)),old_a=a;
   a=vsha256hq_u32(a,b,wk);b=vsha256h2q_u32(b,old_a,wk);
   if(g<12){w[g&3]=vsha256su0q_u32(w[g&3],w[(g+1)&3]);w[g&3]=vsha256su1q_u32(w[g&3],w[(g+2)&3],w[(g+3)&3]);}
  }
  a=vaddq_u32(a,saved_a);b=vaddq_u32(b,saved_b);
 }
 vst1q_u32(state,a);vst1q_u32(state+4,b);
}
static const unsigned char *direct_sha(const unsigned char *p,size_t n){
 static uint32_t state[8],digest[8];
 const uint32_t iv[8]={1779033703,3144134277,1013904242,2773480762,1359893119,2600822924,528734635,1541459225};
 memcpy(state,iv,32);compress(state,p,n/64);
 unsigned char tail[128]={0};size_t remaining=n&63,blocks=remaining>=56?2:1;
 memcpy(tail,p+(n/64)*64,remaining);tail[remaining]=128;
 uint64_t bits=__builtin_bswap64((uint64_t)n*8);memcpy(tail+blocks*64-8,&bits,8);
 compress(state,tail,blocks);for(int i=0;i<8;i++)digest[i]=__builtin_bswap32(state[i]);
 return (const unsigned char *)digest;
}

/* Keep calls opaque in benchmark loops, including repeated empty input. */
static const unsigned char *(*volatile direct_call)(const unsigned char *,size_t)=direct_sha;

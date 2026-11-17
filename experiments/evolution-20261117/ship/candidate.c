/* Original bounded RFC8439 reference port. Developer encoder input, not a new
 * cipher. Independent differential/vector qualification required. No timing or
 * secure-erasure certification. Only fixed lab traffic uses this guest port. */
typedef unsigned char u8; typedef unsigned int u32; typedef unsigned long long u64; typedef unsigned __int128 u128;
static void wipe(void *p,u64 n){volatile u8*q=p;while(n--)*q++=0;}
static u32 l32(const u8*p){return (u32)p[0]|((u32)p[1]<<8)|((u32)p[2]<<16)|((u32)p[3]<<24);}
static u64 l64(const u8*p){return (u64)l32(p)|((u64)l32(p+4)<<32);}
static void s32(u8*p,u32 x){for(u32 i=0;i<4;i++)p[i]=(u8)(x>>(8*i));}
static void s64(u8*p,u64 x){for(u32 i=0;i<8;i++)p[i]=(u8)(x>>(8*i));}
static u32 rol(u32 x,u32 n){return(x<<n)|(x>>(32-n));}
static void qr(u32*x,u32 a,u32 b,u32 c,u32 d){x[a]+=x[b];x[d]=rol(x[d]^x[a],16);x[c]+=x[d];x[b]=rol(x[b]^x[c],12);x[a]+=x[b];x[d]=rol(x[d]^x[a],8);x[c]+=x[d];x[b]=rol(x[b]^x[c],7);}
static void block(u8*out,const u8*k,const u8*nonce,u32 ctr){u32 x[16],s[16];s[0]=0x61707865;s[1]=0x3320646e;s[2]=0x79622d32;s[3]=0x6b206574;for(u32 i=0;i<8;i++)s[4+i]=l32(k+4*i);s[12]=ctr;for(u32 i=0;i<3;i++)s[13+i]=l32(nonce+4*i);for(u32 i=0;i<16;i++)x[i]=s[i];for(u32 i=0;i<10;i++){qr(x,0,4,8,12);qr(x,1,5,9,13);qr(x,2,6,10,14);qr(x,3,7,11,15);qr(x,0,5,10,15);qr(x,1,6,11,12);qr(x,2,7,8,13);qr(x,3,4,9,14);}for(u32 i=0;i<16;i++)s32(out+4*i,x[i]+s[i]);wipe(x,sizeof x);wipe(s,sizeof s);}
static void addp(u64*a,const u64*b){u128 t=(u128)a[0]+b[0];u64 z0=t;t=(u128)a[1]+b[1]+(t>>64);u64 z1=t,z2=a[2]+b[2]+(u64)(t>>64);u64 d0=z0-0xfffffffffffffffbULL,br0=z0<0xfffffffffffffffbULL;u64 d1=z1-0xffffffffffffffffULL-br0,br1=(z1!=0xffffffffffffffffULL)|br0;u64 d2=z2-3-br1,under=z2<3+br1;u64 m=0-(1-under);a[0]=(z0&~m)|(d0&m);a[1]=(z1&~m)|(d1&m);a[2]=(z2&~m)|(d2&m);}
/* Fixed-work 44/44/42-bit limbs. 2^130 == 5 modulo p; consequently
 * cross-products at limb position 3 fold with factor 20 (2^132 == 20).
 * Inputs are canonical h < p and clamped r < 2^128. Products fit u128.
 * No data-dependent table indexes or branches are introduced. */
static void mulp(u64*h,const u8*r){
 const u64 mask44=(1ULL<<44)-1,mask42=(1ULL<<42)-1;
 u64 x0=h[0]&mask44,x1=((h[0]>>44)|(h[1]<<20))&mask44,x2=(h[1]>>24)|(h[2]<<40);
 u64 lo=l64(r),hi=l64(r+8),r0=lo&mask44,r1=((lo>>44)|(hi<<20))&mask44,r2=hi>>24;
 u128 d0=(u128)x0*r0+20*((u128)x1*r2+(u128)x2*r1);
 u128 d1=(u128)x0*r1+(u128)x1*r0+20*(u128)x2*r2;
 u128 d2=(u128)x0*r2+(u128)x1*r1+(u128)x2*r0;
 d1+=d0>>44;x0=(u64)d0&mask44;
 d2+=d1>>44;x1=(u64)d1&mask44;
 x2=(u64)d2&mask42;x0+=5*(u64)(d2>>42);
 x1+=x0>>44;x0&=mask44;x2+=x1>>44;x1&=mask44;
 x0+=5*(x2>>42);x2&=mask42;
 x1+=x0>>44;x0&=mask44;x2+=x1>>44;x1&=mask44;
 h[0]=x0|(x1<<44);h[1]=(x1>>20)|(x2<<24);h[2]=x2>>40;
 u64 zero[3]={0,0,0};addp(h,zero);
 /* Volatile clearing matches the reference scratch-erasure intent, without
  * asserting compiler-register erasure or side-channel certification. */
 wipe(&d0,sizeof d0);wipe(&d1,sizeof d1);wipe(&d2,sizeof d2);
}
static void poly(u8*out,const u8*msg,u64 n,const u8*k){u8 r[16];u64 h[3]={0,0,0},m[3];for(u32 i=0;i<16;i++)r[i]=k[i];r[3]&=15;r[7]&=15;r[11]&=15;r[15]&=15;r[4]&=252;r[8]&=252;r[12]&=252;for(u64 at=0;at<n;at+=16){m[0]=l64(msg+at);m[1]=l64(msg+at+8);m[2]=1;addp(h,m);mulp(h,r);}u128 t=(u128)h[0]+l64(k+16);s64(out,t);s64(out+8,h[1]+l64(k+24)+(u64)(t>>64));wipe(r,sizeof r);wipe(h,sizeof h);wipe(m,sizeof m);}
static void cipher(u8*d,u64 n,const u8*k,const u8*nonce){u8 b[64];for(u64 at=0;at<n;at+=64){block(b,k,nonce,1+(u32)(at/64));for(u64 i=0;i<64&&at+i<n;i++)d[at+i]^=b[i];}wipe(b,sizeof b);}
/* ctx:open@0,key[32]@8,nonce[12]@40,aadptr@56,aadlen@64,
 * dataptr@72,datalen@80,tagptr@88. Returns1 without decrypting on badtag. */
int rf2_aead(void*ctx){u8*c=ctx,*key=c+8,*nonce=c+40,*aad=(u8*)l64(c+56),*data=(u8*)l64(c+72),*tag=(u8*)l64(c+88);u64 an=l64(c+64),n=l64(c+80);if(an>128||n>128)return 2;u8 pk[64],mac[272],wanted[16];u64 used=0;block(pk,key,nonce,0);if(!l64(c))cipher(data,n,key,nonce);for(u64 i=0;i<an;i++)mac[used++]=aad[i];while(used&15)mac[used++]=0;for(u64 i=0;i<n;i++)mac[used++]=data[i];while(used&15)mac[used++]=0;s64(mac+used,an);s64(mac+used+8,n);used+=16;poly(wanted,mac,used,pk);u32 diff=0;if(l64(c)){for(u32 i=0;i<16;i++)diff|=wanted[i]^tag[i];if(!diff)cipher(data,n,key,nonce);}else for(u32 i=0;i<16;i++)tag[i]=wanted[i];wipe(pk,sizeof pk);wipe(mac,sizeof mac);wipe(wanted,sizeof wanted);return diff!=0;}

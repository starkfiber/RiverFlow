/* Developer comparator: system memmem, same bounded byte-search CLI contract. */
#define _DARWIN_C_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <unistd.h>
int main(int argc,char **argv){
 if(argc<2||argc>3||(argc==3&&strcmp(argv[2],"--overlap")))return 2;
 unsigned char *data=malloc(1048577); if(!data)return 3;
 size_t n=0;while(n<1048577){ssize_t z=read(0,data+n,1048577-n);if(z<0){free(data);return 3;}if(!z)break;n+=(size_t)z;}
 if(n>1048576){free(data);return 4;}
 size_t m=strlen(argv[1]),count=0,start=0;long long first=-1;
 if(!m){count=n+1;first=0;}
 else while(start<=n&&m<=n-start){
  unsigned char *p=memmem(data+start,n-start,argv[1],m);if(!p)break;
  size_t at=(size_t)(p-data);if(first<0)first=(long long)at;count++;start=at+(argc==3?1:m);
 }
 char position[32];if(first<0)strcpy(position,"null");else snprintf(position,sizeof(position),"%lld",first);
 int ok=printf("{\"bytes\":%zu,\"query_bytes\":%zu,\"matches\":%zu,\"first_byte\":%s}\n",n,m,count,position);
 free(data);return ok<0?5:0;
}

#include <stdint.h>
#include <stddef.h>
#include <stdio.h>
int rf2_eval(const uint32_t*,size_t,uint32_t,uint32_t*,uint32_t*);
int main(void) {
 uint32_t data[]={1,2,3,4,5},value=0,work=0;
 int status=rf2_eval(data,5,5,&value,&work);
 if(status){fprintf(stderr,"RF2 status %d\n",status);return 1;}
 printf("Result: %u\nWork steps: %u\n",value,work);
 return value==15 && work==18 ? 0 : 2;
}

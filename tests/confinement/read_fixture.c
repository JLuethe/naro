/* Disposable driver for the unchanged native authorized-open implementation.
 * Rust read integration remains covered by the ordinary confinement unit tests. */
#define _GNU_SOURCE
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/stat.h>
#include <unistd.h>
extern int nr_confined_open(int root,const char *path,int directory);
int main(int argc,char **argv) {
    if(argc!=2)return 2;
    if(chdir(argv[1]))return 3;
    int root=open("root",O_RDONLY|O_DIRECTORY|O_CLOEXEC);
    struct stat authority,source;
    if(root<0||fstat(root,&authority))return 4;
    FILE *record=fopen("authority","wx");
    if(!record)return 5;
    fprintf(record,"%llu %llu\n",(unsigned long long)authority.st_dev,
            (unsigned long long)authority.st_ino);
    if(fclose(record))return 6;
    int fd=nr_confined_open(root,"data/target",0);
    if(fd<0||fstat(fd,&source))return 7;
    FILE *data=fopen("read-data","wx");
    if(!data)return 8;
    char bytes[4096];ssize_t n;
    while((n=read(fd,bytes,sizeof bytes))>0)
        if(fwrite(bytes,1,(size_t)n,data)!=(size_t)n)return 9;
    if(n<0||fclose(data)||close(fd)||close(root))return 10;
    record=fopen("result","wx");
    if(!record)return 11;
    fprintf(record,"read %llu %llu\n",(unsigned long long)source.st_dev,
            (unsigned long long)source.st_ino);
    return fclose(record)?12:0;
}

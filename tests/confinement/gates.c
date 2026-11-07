/* Test-process-only, one-shot synchronization at real native syscall boundaries.
 * The controller creates all paths and runs one fixture in a bounded subprocess.
 * No filesystem mutation is performed by this interposer. */
#define _GNU_SOURCE
#include <dlfcn.h>
#include <errno.h>
#include <fcntl.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>

static int fired, source_fd=-1;
static int owned_parent(int fd) {
    struct stat st;
    const char *dev=getenv("NARO_BOUND_DEV"), *ino=getenv("NARO_BOUND_INO");
    return dev&&ino&&!fstat(fd,&st)&&
        (unsigned long long)st.st_dev==strtoull(dev,NULL,10)&&
        (unsigned long long)st.st_ino==strtoull(ino,NULL,10);
}
static void identity(FILE *out,const char *label,int fd) {
    struct stat st;
    if(fd>=0&&!fstat(fd,&st))
        fprintf(out,"%s %llu %llu\n",label,(unsigned long long)st.st_dev,
                (unsigned long long)st.st_ino);
}
static void opened(const char *label,int fd) {
    const char *base=getenv("NARO_BOUND_FIXTURE");
    if(!base||fd<0)return;
    char path[4096];
    if(snprintf(path,sizeof path,"%s/opened",base)>=(int)sizeof path)_exit(95);
    FILE *out=fopen(path,"a");
    if(!out)_exit(96);
    identity(out,label,fd);
    if(fclose(out))_exit(97);
}
static void gate(const char *stage,int parent,int source) {
    const char *wanted=getenv("NARO_BOUND_STAGE"),*base=getenv("NARO_BOUND_FIXTURE");
    if(fired||!wanted||!base||strcmp(stage,wanted))return;
    fired=1;
    char ready[4096],release[4096];
    if(snprintf(ready,sizeof ready,"%s/ready",base)>=(int)sizeof ready||
       snprintf(release,sizeof release,"%s/release",base)>=(int)sizeof release)_exit(91);
    FILE *out=fopen(ready,"wx");
    if(!out)_exit(92);
    fprintf(out,"stage %s\n",stage);
    identity(out,"parent",parent);identity(out,"source",source);
    if(fclose(out))_exit(93);
    /* At most five seconds waiting for the controller's single mutation. */
    for(int i=0;i<5000;i++){
        if(!access(release,F_OK))return;
        usleep(1000);
    }
    _exit(94);
}
/* glibc may route a no-mode call through a fortified entry point while the
 * corresponding O_CREAT call still uses openat. Keep every spelling on the
 * same gates, and dispatch to its actual libc symbol to preserve validation. */
static int tracked_openat(const char *symbol,int dir,const char *path,int flags,
                          mode_t mode,int fortified) {
    int owned=owned_parent(dir);
    int source=owned&&!strcmp(path,"target")&&!(flags&O_PATH)&&!(flags&O_CREAT);
    if(source)gate("source-open",dir,-1);
    int fd;
    if(fortified){
        int (*real)(int,const char*,int)=dlsym(RTLD_NEXT,symbol);
        fd=real(dir,path,flags);
    }else{
        int (*real)(int,const char*,int,...)=dlsym(RTLD_NEXT,symbol);
        fd=real(dir,path,flags,mode);
    }
    if(source&&fd>=0){source_fd=fd;opened("source",fd);}
    return fd;
}
static int tracked_open(const char *symbol,const char *path,int flags,
                        mode_t mode,int fortified) {
    int fd=-1;
    if(sscanf(path,"/proc/self/fd/%d",&fd)==1&&fd>=0)
        gate("read-reopen",-1,fd);
    int result;
    if(fortified){
        int (*real)(const char*,int)=dlsym(RTLD_NEXT,symbol);
        result=real(path,flags);
    }else{
        int (*real)(const char*,int,...)=dlsym(RTLD_NEXT,symbol);
        result=real(path,flags,mode);
    }
    if(fd>=0)opened("read",result);
    return result;
}
/* Both O_CREAT and O_TMPFILE require the variadic mode argument. */
#define MODE_ARGUMENT \
    mode_t mode=0; \
    if((flags&O_CREAT)||(flags&O_TMPFILE)==O_TMPFILE){ \
        va_list args;va_start(args,flags);mode=va_arg(args,int);va_end(args); \
    }
#define OPENAT_WRAPPER(symbol) \
    int symbol(int dir,const char *path,int flags,...){ \
        MODE_ARGUMENT \
        return tracked_openat(#symbol,dir,path,flags,mode,0); \
    }
#define OPEN_WRAPPER(symbol) \
    int symbol(const char *path,int flags,...){ \
        MODE_ARGUMENT \
        return tracked_open(#symbol,path,flags,mode,0); \
    }
OPENAT_WRAPPER(openat)
OPENAT_WRAPPER(openat64)
OPEN_WRAPPER(open)
OPEN_WRAPPER(open64)
int __openat_2(int dir,const char *path,int flags) {
    return tracked_openat("__openat_2",dir,path,flags,0,1);
}
int __openat64_2(int dir,const char *path,int flags) {
    return tracked_openat("__openat64_2",dir,path,flags,0,1);
}
int __open_2(const char *path,int flags) {
    return tracked_open("__open_2",path,flags,0,1);
}
int __open64_2(const char *path,int flags) {
    return tracked_open("__open64_2",path,flags,0,1);
}
int renameat(int from,const char *source,int to,const char *target) {
    int (*real)(int,const char*,int,const char*)=dlsym(RTLD_NEXT,"renameat");
    if(owned_parent(to)&&!strcmp(target,"target"))gate("publish",to,-1);
    return real(from,source,to,target);
}
int mkdirat(int dir,const char *path,mode_t mode) {
    int (*real)(int,const char*,mode_t)=dlsym(RTLD_NEXT,"mkdirat");
    if(owned_parent(dir)&&!strncmp(path,".naro-save-",11))
        gate("temp-open",dir,source_fd);
    return real(dir,path,mode);
}

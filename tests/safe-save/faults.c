/* Fixture-bounded syscall faults. Loaded only into an isolated unit test. */
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
static int writes, syncs, backup_done, save_temp_closed, directory_synced, parent_syncs, stage_remove_faulted;
static int backup_phase(void) {return getenv("NARO_SAVE_BACKUP")&&!backup_done;}
static int is(const char *s) {
 const char *f=getenv("NARO_SAVE_FAULT"),*phase=getenv("NARO_SAVE_FAULT_PHASE");
 if(getenv("NARO_SAVE_BACKUP")&&((phase&&!strcmp(phase,"backup"))!=backup_phase()))return 0;
 return f&&!strcmp(f,s);
}
static int owned(const char *p) {const char *r=getenv("NARO_SAVE_FIXTURE");if(!r)return 0;size_t n=strlen(r);return !strncmp(p,r,n)&&!strncmp(p+n,"/data",5)&&(p[n+5]=='/'||p[n+5]==0);}
static int target_fd(int fd) {char k[64],p[4096];snprintf(k,sizeof k,"/proc/self/fd/%d",fd);ssize_t n=readlink(k,p,sizeof p-1);if(n<0)return 0;p[n]=0;return owned(p);}
static void event(const char *s) {
 char p[4096];snprintf(p,sizeof p,"%s/events",getenv("NARO_SAVE_FIXTURE"));
 int (*op)(const char*,int,...)=dlsym(RTLD_NEXT,"open");ssize_t (*wr)(int,const void*,size_t)=dlsym(RTLD_NEXT,"write");int (*cl)(int)=dlsym(RTLD_NEXT,"close");
 int fd=op(p,O_WRONLY|O_CREAT|O_APPEND,0600);if(fd>=0){wr(fd,s,strlen(s));wr(fd,"\n",1);cl(fd);}
}
static void boundary(const char *s) {char stage[96];snprintf(stage,sizeof stage,"%s%s",backup_phase()?"backup-":"",s);event(stage);char stop[64];snprintf(stop,sizeof stop,"exit-%s",s);if(is(stop))_exit(99);}
static int opening(int yes,int flags) {if(yes&&(flags&(O_WRONLY|O_RDWR))){boundary("open");if(is("open")){errno=EACCES;return -1;}}return 0;}
int open(const char *p,int f,...) {mode_t m=0;if(f&O_CREAT){va_list a;va_start(a,f);m=va_arg(a,int);va_end(a);}int (*real)(const char*,int,...)=dlsym(RTLD_NEXT,"open");if(opening(owned(p),f))return -1;return real(p,f,m);}
int open64(const char *p,int f,...) {mode_t m=0;if(f&O_CREAT){va_list a;va_start(a,f);m=va_arg(a,int);va_end(a);}int (*real)(const char*,int,...)=dlsym(RTLD_NEXT,"open64");if(opening(owned(p),f))return -1;return real(p,f,m);}
int openat(int d,const char *p,int f,...) {mode_t m=0;if(f&O_CREAT){va_list a;va_start(a,f);m=va_arg(a,int);va_end(a);}int (*real)(int,const char*,int,...)=dlsym(RTLD_NEXT,"openat");if(opening(target_fd(d)||owned(p),f))return -1;return real(d,p,f,m);}
ssize_t write(int fd,const void *p,size_t n) {
 ssize_t (*real)(int,const void*,size_t)=dlsym(RTLD_NEXT,"write");
 if(target_fd(fd)){boundary("write");writes++;if(is("eintr")&&writes==1){errno=EINTR;return -1;}if(is("eio")){errno=EIO;return -1;}if(is("enospc")){errno=ENOSPC;return -1;}if(is("zero"))return 0;if(is("partial-eio")&&writes>1){errno=EIO;return -1;}if((is("short")||is("partial-eio"))&&n>2)n=2;}
 return real(fd,p,n);
}
int fsync(int fd) {
 int (*real)(int)=dlsym(RTLD_NEXT,"fsync");int dir=0,hit=target_fd(fd);if(hit){struct stat st;if(fstat(fd,&st))return -1;dir=S_ISDIR(st.st_mode);boundary(dir?"dir-sync":"file-sync");if(dir&&!backup_phase()){
   char key[64],path[4096];snprintf(key,sizeof key,"/proc/self/fd/%d",fd);ssize_t n=readlink(key,path,sizeof path-1);if(n>=0)path[n]=0;else path[0]=0;
   const char *point=strstr(path,"/.naro-save-");
   const char *phase=point?"stage-sync":(++parent_syncs==1?"parent-sync":"final-parent-sync");
   boundary(phase);if(is(phase)){errno=EIO;return -1;}
  }
  if((dir&&is("dir-sync"))||(!dir&&is("file-sync"))){errno=EIO;return -1;}if(is("sync-eintr")&&syncs++==0){errno=EINTR;return -1;}}int r=real(fd);if(!r&&hit&&dir){if(backup_phase()){backup_done=1;writes=0;syncs=0;}else directory_synced=1;}return r;
}
int unlinkat(int dir,const char *path,int flags) {
 int (*real)(int,const char*,int)=dlsym(RTLD_NEXT,"unlinkat");
 if((flags&AT_REMOVEDIR)&&target_fd(dir)&&!strncmp(path,".naro-save-",11)&&directory_synced){
  boundary("stage-remove");if(is("stage-remove")&&!stage_remove_faulted++){errno=EIO;return -1;}
 }
 return real(dir,path,flags);
}
int close(int fd) {
 int (*real)(int)=dlsym(RTLD_NEXT,"close");
 if(target_fd(fd)){
  int f=fcntl(fd,F_GETFL);struct stat st;char k[64],p[4096];
  snprintf(k,sizeof k,"/proc/self/fd/%d",fd);ssize_t n=readlink(k,p,sizeof p-1);if(n>=0)p[n]=0;else p[0]=0;
  if(f>=0&&!fstat(fd,&st)){
   int temporary=strstr(p,"/.naro-save-")!=NULL;
   if(!backup_phase()&&S_ISDIR(st.st_mode)&&directory_synced){boundary("directory-close");if(is("directory-close")){real(fd);errno=EIO;return -1;}}
   else if(!backup_phase()&&S_ISREG(st.st_mode)&&save_temp_closed&&!temporary){boundary("source-close");if(is("source-close")){real(fd);errno=EIO;return -1;}}
   else if((f&O_ACCMODE)!=O_RDONLY&&S_ISREG(st.st_mode)){boundary("close");if(temporary)save_temp_closed=1;if(is("close")){real(fd);errno=EIO;return -1;}}
  }
 }
 return real(fd);
}
int rename(const char *a,const char *b) {int (*real)(const char*,const char*)=dlsym(RTLD_NEXT,"rename");if(owned(b)){boundary("rename");if(is("rename")){errno=EIO;return -1;}}int r=real(a,b);if(!r&&owned(b))boundary("committed");return r;}
int renameat(int a,const char *p,int b,const char *q) {int (*real)(int,const char*,int,const char*)=dlsym(RTLD_NEXT,"renameat");int hit=target_fd(b)||owned(q);if(hit){boundary("rename");if(is("rename")){errno=EIO;return -1;}}int r=real(a,p,b,q);if(!r&&hit)boundary("committed");return r;}
ssize_t read(int fd,void *p,size_t n) {static int reads;ssize_t (*real)(int,void*,size_t)=dlsym(RTLD_NEXT,"read");if(target_fd(fd)){boundary("read");reads++;if(is("read-eio")){errno=EIO;return -1;}if(is("read-eintr")&&reads==1){errno=EINTR;return -1;}}return real(fd,p,n);}
int fchmod(int fd,mode_t mode) {int (*real)(int,mode_t)=dlsym(RTLD_NEXT,"fchmod");if(target_fd(fd)&&is("metadata")){boundary("metadata");errno=EPERM;return -1;}return real(fd,mode);}
int fsetxattr(int fd,const char *name,const void *value,size_t size,int flags) {int (*real)(int,const char*,const void*,size_t,int)=dlsym(RTLD_NEXT,"fsetxattr");if(target_fd(fd)&&is("xattr")){boundary("xattr");errno=EPERM;return -1;}return real(fd,name,value,size,flags);}

ssize_t pread64(int fd,void *p,size_t n,off64_t offset) {
 ssize_t (*real)(int,void*,size_t,off64_t)=dlsym(RTLD_NEXT,"pread64");
 if(target_fd(fd)&&backup_phase()){boundary("read");if(is("read-eio")){errno=EIO;return -1;}}
 return real(fd,p,n,offset);
}

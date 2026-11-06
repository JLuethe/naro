/* Directory-relative authorization. No pathname-only fallback is permitted
 * when operating-directory confinement is requested. */
#ifdef __linux__
#include <sys/syscall.h>
#if defined(SYS_openat2) && __has_include(<linux/openat2.h>)
#include <linux/openat2.h>
#define NARO_HAVE_OPENAT2 1
#endif
#endif
/* Reopen only an already identified regular object. The kernel's procfs fd
 * link names this owned descriptor, never the user's mutable directory entry.
 * Keep it alive until the data descriptor is opened and checked. */
#ifdef __linux__
static int nr_read_regular(int pathfd) {
    struct stat before,after;
    int result=-1;
    if(fstat(pathfd,&before)<0)goto done;
    if(!S_ISREG(before.st_mode)){errno=EINVAL;goto done;}
    char path[64];
    snprintf(path,sizeof path,"/proc/self/fd/%d",pathfd);
    result=open(path,O_RDONLY|O_CLOEXEC|O_NONBLOCK);
    if(result>=0){
        if(fstat(result,&after)<0){int e=errno;close(result);result=-1;errno=e;}
        else if(!S_ISREG(after.st_mode)||before.st_dev!=after.st_dev||before.st_ino!=after.st_ino){
            close(result);result=-1;errno=ESTALE;
        }
    }
done:;
    int error=errno;close(pathfd);errno=error;return result;
}
#endif
int nr_confined_open(int root,const char *path,int directory) {
#ifdef NARO_HAVE_OPENAT2
    struct open_how how={0};
    how.flags=O_CLOEXEC;
    if(directory<=0)how.flags|=O_PATH;
    else how.flags|=O_RDONLY|O_NONBLOCK|(directory?O_DIRECTORY:0);
    how.resolve=RESOLVE_BENEATH|RESOLVE_NO_MAGICLINKS;
    int fd=(int)syscall(SYS_openat2,root,path,&how,sizeof how);
    if(fd<0)return -1;
    if(directory==0)return nr_read_regular(fd);
    struct stat st;
    if(fstat(fd,&st)<0){int e=errno;close(fd);errno=e;return -1;}
    return fd;
#else
    (void)root;(void)path;(void)directory;errno=ENOTSUP;return -1;
#endif
}
int nr_directory_chdir(int dir) {return fchdir(dir);}
int nr_at_open(int dir,const char *name,int operation,unsigned int mode) {
    int flags=O_CLOEXEC|O_NOFOLLOW|O_NONBLOCK;
    if(operation==0)flags|=O_RDONLY;
    else if(operation==3){
#ifdef __linux__
        flags|=O_PATH;
#else
        flags|=O_RDONLY;
#endif
    }
    else if(operation==1)flags|=O_WRONLY|O_CREAT|O_EXCL;
    else if(operation==2){
#ifdef __linux__
        flags|=O_PATH;
#else
        flags|=O_RDONLY;
#endif
    }else{errno=EINVAL;return -1;}
    int fd=openat(dir,name,flags,(mode_t)mode);
    if(fd<0)return -1;
    if(operation==3){
#ifdef __linux__
        return nr_read_regular(fd);
#endif
    }
    if(operation==0||operation==3){
        struct stat st;
        if(fstat(fd,&st)<0){int e=errno;close(fd);errno=e;return -1;}
        if(!S_ISREG(st.st_mode)){close(fd);errno=EINVAL;return -1;}
    }
    return fd;
}
int nr_at_unlink(int dir,const char *name) {return unlinkat(dir,name,0);}
#include <dirent.h>
void *nr_directory_stream(int fd) {
    int copy=fcntl(fd,F_DUPFD_CLOEXEC,0);
    if(copy<0)return NULL;
    DIR *stream=fdopendir(copy);
    if(!stream){int e=errno;close(copy);errno=e;}
    return stream;
}
const char *nr_directory_next(void *stream,int *error) {
    errno=0;
    struct dirent *entry=readdir((DIR *)stream);
    *error=errno;
    return entry?entry->d_name:NULL;
}
void nr_directory_close(void *stream) {closedir((DIR *)stream);}

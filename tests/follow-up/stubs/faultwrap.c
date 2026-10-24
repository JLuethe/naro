/* Fixture-only syscall fault supervisor. GNU nano reference: 6ed285c3ec7a1d228def4d4e7021c6ba269f620c. */
#define _GNU_SOURCE
#include <sys/ptrace.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <sys/user.h>
#include <sys/stat.h>
#include <sys/syscall.h>
#include <unistd.h>
#include <signal.h>
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static pid_t child;
static void forward(int sig) { if(child>0)kill(child,sig); }
static int target_fd(int fd,const char *target) {
    struct stat a,b;char path[80];snprintf(path,sizeof(path),"/proc/%ld/fd/%d",(long)child,fd);
    return stat(target,&a)==0&&stat(path,&b)==0&&a.st_dev==b.st_dev&&a.st_ino==b.st_ino;
}
static int target_path(unsigned long address,const char *target) {
    char name[4096],base[4096],full[8192];size_t i=0;
    while(i+sizeof(long)<sizeof(name)) { errno=0;long value=ptrace(PTRACE_PEEKDATA,child,address+i,0);if(errno)return 0;memcpy(name+i,&value,sizeof(value));if(memchr(&value,0,sizeof(value)))break;i+=sizeof(value); }
    name[sizeof(name)-1]=0;
    char *slash=strrchr(name,'/');const char *tail=name;
    if(slash){*slash=0;tail=slash+1;if(!realpath(*name?name:"/",base))return 0;}
    else if(!getcwd(base,sizeof(base)))return 0;
    snprintf(full,sizeof(full),"%s/%s",base,tail);return strcmp(full,target)==0;
}
int main(int argc,char **argv) {
    (void)argc;
    const char *binary=getenv("NARO_FAULT_BINARY"),*target=getenv("NARO_FAULT_TARGET"),*root=getenv("NARO_FIXTURE_ROOT"),*mode=getenv("NARO_FAULT_MODE");
    char real[4096],boundary[4096];
    if(!binary||!target||!root||!mode||!realpath(root,boundary)||!realpath(target,real)||strncmp(real,boundary,strlen(boundary))||real[strlen(boundary)]!='/')return 90;
    long budget=atol(getenv("NARO_FAULT_AFTER")?getenv("NARO_FAULT_AFTER"):"4"),written=0;
    int entering=1,status,inject=0,once=0;unsigned long original_count=0;
    child=fork();if(child<0)return 91;
    if(!child){if(ptrace(PTRACE_TRACEME,0,0,0)<0)_exit(92);raise(SIGSTOP);execv(binary,argv);_exit(93);}
    for(int s=1;s<32;s++)if(s==SIGHUP||s==SIGTERM||s==SIGWINCH)signal(s,forward);
    if(waitpid(child,&status,0)<0)return 94;
    if(ptrace(PTRACE_SETOPTIONS,child,0,PTRACE_O_TRACESYSGOOD|PTRACE_O_EXITKILL)<0)return 95;
    int deliver=0;
    while(1){
        if(ptrace(PTRACE_SYSCALL,child,0,deliver)<0)return 96;deliver=0;
        if(waitpid(child,&status,0)<0){if(errno==EINTR)continue;return 97;}
        if(WIFEXITED(status))return WEXITSTATUS(status);
        if(WIFSIGNALED(status)){int sig=WTERMSIG(status);signal(sig,SIG_DFL);raise(sig);return 128+sig;}
        int sig=WSTOPSIG(status);
        if(sig!=(SIGTRAP|0x80)){if(sig!=SIGTRAP&&sig!=SIGSTOP)deliver=sig;continue;}
        struct user_regs_struct regs;if(ptrace(PTRACE_GETREGS,child,0,&regs)<0)return 98;
        if(entering){
            inject=0;original_count=0;
            if(!strcmp(mode,"backup-open")&&regs.orig_rax==SYS_openat&&(regs.rdx&3)!=0&&target_path(regs.rsi,real)) {
                inject=EACCES;original_count=1;regs.orig_rax=-1UL;ptrace(PTRACE_SETREGS,child,0,&regs);
            }else if(regs.orig_rax==SYS_write&&target_fd((int)regs.rdi,real)){
                original_count=regs.rdx;
                if(!strcmp(mode,"eintr")&&!once){inject=EINTR;once=1;}
                else if(!strcmp(mode,"enospc")&&written>=budget)inject=ENOSPC;
                if(inject)regs.orig_rax=-1UL;
                else if(!strcmp(mode,"enospc")&&(long)regs.rdx>budget-written)regs.rdx=budget-written;
                else if(!strcmp(mode,"short")&&regs.rdx>2)regs.rdx=2;
                if(ptrace(PTRACE_SETREGS,child,0,&regs)<0)return 99;
            }
        }else if(original_count){
            if(inject){regs.rax=-(long)inject;ptrace(PTRACE_SETREGS,child,0,&regs);}
            else if((long)regs.rax>0)written+=(long)regs.rax;
            // The trace does not expose native syscall grouping; byte budget is
            // the shared oracle across C stdio and Rust's File implementation.
        }
        entering=!entering;
    }
}

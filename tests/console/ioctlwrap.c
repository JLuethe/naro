/* Fixture-only ptrace ioctl model. Reference 6ed285c3ec7a1d228def4d4e7021c6ba269f620c. */
#define _GNU_SOURCE
#include <sys/ptrace.h>
#include <sys/wait.h>
#include <sys/user.h>
#include <sys/syscall.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <errno.h>
static void poke(pid_t pid,unsigned long addr,unsigned long value,unsigned long mask){
    errno=0;unsigned long prior=ptrace(PTRACE_PEEKDATA,pid,addr,0);if(errno)_exit(93);
    if(ptrace(PTRACE_POKEDATA,pid,addr,(prior&~mask)|(value&mask))<0)_exit(94);
}
int main(int argc,char **argv){
    (void)argc;const char *root=getenv("NARO_FIXTURE_ROOT"),*binary=getenv("NARO_FAULT_BINARY"),*mode=getenv("NARO_IOCTL_MODEL");char resolved[4096];
    if(!root||!binary||!mode||!realpath(root,resolved)||strcmp(root,resolved)||!strstr(root,"/TEST-VT-IOCTL-")||strcmp(root+strlen(root)-3,"/fx"))return 90;
    int nonvt=!strcmp(mode,"nonvt"),fail=!strcmp(mode,"fail"),bits=!strcmp(mode,"shift")?1:!strcmp(mode,"ctrl")?4:!strcmp(mode,"ctrlshift")?5:!strcmp(mode,"alt")?8:!strcmp(mode,"shiftalt")?9:0;
    if(!nonvt&&!fail&&!bits)return 91;
    pid_t child=fork();if(child<0)return 92;
    if(!child){if(ptrace(PTRACE_TRACEME,0,0,0)<0)_exit(95);raise(SIGSTOP);execv(binary,argv);_exit(96);}
    int status,entering=1,request=0,seen_vt=0,seen_mod=0,deliver=0;unsigned long pointer=0;
    if(waitpid(child,&status,0)<0)return 97;
    if(ptrace(PTRACE_SETOPTIONS,child,0,PTRACE_O_TRACESYSGOOD|PTRACE_O_EXITKILL)<0)return 98;
    while(1){
        if(ptrace(PTRACE_SYSCALL,child,0,deliver)<0)return 99;deliver=0;
        if(waitpid(child,&status,0)<0){if(errno==EINTR)continue;return 100;}
        if(WIFEXITED(status)||WIFSIGNALED(status))break;
        int sig=WSTOPSIG(status);if(sig!=(SIGTRAP|0x80)){if(sig!=SIGTRAP&&sig!=SIGSTOP)deliver=sig;continue;}
        struct user_regs_struct regs;if(ptrace(PTRACE_GETREGS,child,0,&regs)<0)return 101;
        if(entering){
            request=0;
            if(regs.orig_rax==SYS_ioctl&&regs.rdi==1&&regs.rsi==0x5603){request=1;seen_vt=1;}
            if(regs.orig_rax==SYS_ioctl&&regs.rdi==0&&regs.rsi==0x541c){errno=0;long value=ptrace(PTRACE_PEEKDATA,child,regs.rdx,0);if(!errno&&(value&0xff)==6){request=2;seen_mod=1;}}
            if(request){pointer=regs.rdx;regs.orig_rax=-1UL;if(ptrace(PTRACE_SETREGS,child,0,&regs)<0)return 102;}
        }else if(request){
            if(request==1){if(nonvt)regs.rax=-ENOTTY;else{poke(child,pointer,1,0xffffffffffffUL);regs.rax=0;}}
            else if(fail)regs.rax=-EIO;
            else{poke(child,pointer,bits,0xff);regs.rax=0;}
            if(ptrace(PTRACE_SETREGS,child,0,&regs)<0)return 103;
        }
        entering=!entering;
    }
    char output[8192];snprintf(output,sizeof(output),"%s/home/ioctl-model.json",root);FILE *log=fopen(output,"w");if(!log)return 104;
    fprintf(log,"{\"model\":\"%s\",\"getstate_seen\":%s,\"modifiers_seen\":%s}\n",mode,seen_vt?"true":"false",seen_mod?"true":"false");fclose(log);
    if(WIFSIGNALED(status)){signal(WTERMSIG(status),SIG_DFL);raise(WTERMSIG(status));}
    return WIFEXITED(status)?WEXITSTATUS(status):105;
}

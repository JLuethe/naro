/* Naro native ABI bridge. GPL-3.0-or-later.
 * Behavioral reference: 6ed285c3ec7a1d228def4d4e7021c6ba269f620c. */
#ifndef _GNU_SOURCE
#define _GNU_SOURCE
#endif
#include <curses.h>
#include <term.h>
#include <termios.h>
#include <locale.h>
#include <langinfo.h>
#include <libintl.h>
#include <regex.h>
#include <getopt.h>
#include <signal.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <errno.h>
#include <fcntl.h>
#include <stdatomic.h>
#include <sys/stat.h>
#include <wchar.h>
#include <wctype.h>
#include <sys/ioctl.h>
#ifdef __linux__
#include <linux/vt.h>
#include <linux/tiocl.h>
#include <sys/xattr.h>
#endif
#include <pwd.h>
#ifndef NARO_TINY
#include <magic.h>
#endif
#include "options.inc"
#include "confinement.inc"
static struct termios saved;
static int active, have_saved;
static int on_vt=-1;
int nr_on_vt(void) {
    if(on_vt<0){
#ifdef __linux__
        struct vt_stat state;on_vt=(ioctl(STDOUT_FILENO,VT_GETSTATE,&state)==0);
#else
        on_vt=0;
#endif
    }
    return on_vt;
}
int nr_vt_key(int key,int meta,int *shift) {
#ifdef __linux__
    unsigned char modifiers=6;
    /* Terminfo/escape-derived modifier codes have already been resolved. */
    if(key>=0x400||!nr_on_vt()||ioctl(STDIN_FILENO,TIOCLINUX,&modifiers)<0)return key;
#ifndef NARO_TINY
    if(modifiers&1){
        if(key=='\t')return 0x45f;
        if(key==KEY_DC&&modifiers==1)return 0x45d;
        if(key==KEY_DC&&modifiers==5)return 0x41d;
        if(!meta)*shift=1;
    }
    if(modifiers==8){switch(key){
        case KEY_UP:return 0x423;case KEY_DOWN:return 0x424;
        case KEY_HOME:return 0x425;case KEY_END:return 0x426;
        case KEY_PPAGE:return 0x427;case KEY_NPAGE:return 0x428;
        case KEY_DC:return 0x42d;case KEY_IC:return 0x42c;
    }}
#else
    (void)meta;(void)shift;
#endif
    if(modifiers&4){switch(key){
        case KEY_UP:return 0x403;case KEY_DOWN:return 0x404;
        case KEY_LEFT:return 0x401;case KEY_RIGHT:return 0x402;
        case KEY_HOME:return 0x405;case KEY_END:return 0x406;
        case KEY_DC:return 0x40d;
    }}
#ifndef NARO_TINY
    if((modifiers&9)==9){switch(key){
        case KEY_UP:return KEY_PPAGE;case KEY_DOWN:return KEY_NPAGE;
        case KEY_LEFT:return KEY_HOME;case KEY_RIGHT:return KEY_END;
    }}
#endif
#else
    (void)meta;(void)shift;
#endif
    return key;
}
/* Standard signals coalesce within each class. Keep the classes independent,
 * and service termination before terminal events. Lock-free atomics also cover
 * delivery to the external-command writer thread: blocking only the consumer's
 * signals would not protect a process-wide volatile read/clear. */
_Static_assert(ATOMIC_INT_LOCK_FREE == 2, "signal delivery requires lock-free unsigned atomics");
static atomic_uint pending;
static const int handled_signals[]={SIGHUP,SIGTERM,SIGTSTP,SIGCONT,SIGWINCH};
static void handler(int sig) {
    unsigned bit;
    switch(sig){
        case SIGHUP:bit=1u<<0;break;
        case SIGTERM:bit=1u<<1;break;
        case SIGTSTP:bit=1u<<2;break;
        case SIGCONT:bit=1u<<3;break;
        case SIGWINCH:bit=1u<<4;break;
        default:return;
    }
    atomic_fetch_or_explicit(&pending,bit,memory_order_relaxed);
}
int nr_signal_pending(void) {
    return atomic_load_explicit(&pending,memory_order_relaxed)!=0;
}
int nr_signal(void) {
    unsigned snapshot=atomic_load_explicit(&pending,memory_order_relaxed);
    while(snapshot){
        unsigned i=0;
        while(!(snapshot&(1u<<i)))i++;
        /* A handler racing this operation either updates snapshot through the
         * failed CAS, or leaves its bit for the next call. Never clear it by
         * assigning zero to a stale snapshot. No payload needs publication. */
        if(atomic_compare_exchange_weak_explicit(&pending,&snapshot,
                snapshot&~(1u<<i),memory_order_relaxed,memory_order_relaxed))
            return handled_signals[i];
    }
    return 0;
}
int nr_locale(const char *path) {
    int ok=setlocale(LC_ALL, "") != NULL;
    bindtextdomain("nano",path); bind_textdomain_codeset("nano","UTF-8"); textdomain("nano");
    return ok && strcmp(nl_langinfo(CODESET),"UTF-8")==0;
}
const char *nr_tr(const char *s) { return gettext(s); }
const char *nr_plural(const char *a,const char *b,unsigned long n) {return ngettext(a,b,n);}
int nr_width(uint32_t ch) { return wcwidth((wchar_t)ch); }
int nr_class(uint32_t ch,int kind) {return kind==0?iswalnum(ch):kind==1?iswpunct(ch):iswblank(ch);}
uint32_t nr_lower(uint32_t ch) { return towlower(ch); }
int nr_tty(int fd) {return isatty(fd);}
int nr_reconnect(void) {return freopen("/dev/tty","r",stdin) != NULL;}
const char *nr_user(void) {struct passwd *p=getpwuid(geteuid());return p?p->pw_name:"";}
const char *nr_home(const char *name) {struct passwd *p= name&&*name?getpwnam(name):getpwuid(geteuid());return p?p->pw_dir:"";}
const char *nr_current_home(void) {
    const char *home=getenv("HOME");
    if(!home||geteuid()==0){struct passwd *p=getpwuid(geteuid());if(p)home=p->pw_dir;}
    return home&&*home?home:NULL;
}
int nr_option(int argc,char **argv) {return getopt_long(argc,argv,"ABC:DEFGHIJ:KLMNOPQ:RST:UVWX:Y:Zabcdef:ghijklmno:pqr:s:tuvwxyz!@%_01/",options,NULL);}
const char *nr_optarg(void) {return optarg;}
int nr_optind(void) {return optind;}
void nr_setup_signals(void) {
    struct sigaction a={0}; sigemptyset(&a.sa_mask); a.sa_handler=handler;
    for(unsigned i=0;i<sizeof handled_signals/sizeof *handled_signals;i++)
        sigaddset(&a.sa_mask,handled_signals[i]);
    for(unsigned i=0;i<sizeof handled_signals/sizeof *handled_signals;i++)
        sigaction(handled_signals[i],&a,NULL);
    signal(SIGINT,SIG_IGN);signal(SIGQUIT,SIG_IGN);
}
#ifndef NARO_TINY
static void interrupt_open(int sig) { (void)sig; }
#endif
/* Open once: retrying EINTR would prevent Ctrl-C from cancelling a FIFO save. */
int nr_open_write(const char *path,int append) {
#ifndef NARO_TINY
    sigset_t blocked,previous_mask;
    sigemptyset(&blocked);sigaddset(&blocked,SIGWINCH);
    int mask_saved=sigprocmask(SIG_BLOCK,&blocked,&previous_mask)==0;
    struct sigaction action={0},previous_action;
    struct termios previous_modes,modes;
    sigemptyset(&action.sa_mask);action.sa_handler=interrupt_open;
    int action_saved=sigaction(SIGINT,&action,&previous_action)==0;
    int modes_saved=tcgetattr(STDIN_FILENO,&previous_modes)==0;
    if(modes_saved){modes=previous_modes;modes.c_lflag|=ISIG;tcsetattr(STDIN_FILENO,TCSANOW,&modes);}
#endif
    /* Only FIFO compatibility uses this open. Never truncate a regular file
     * substituted between the caller's stat and this open. */
    int fd=open(path,O_WRONLY|O_CLOEXEC|O_NOFOLLOW|(append?O_APPEND:0));
    if(fd>=0){
        struct stat st;
        if(fstat(fd,&st)<0){int e=errno;close(fd);fd=-1;errno=e;}
        else if(!S_ISFIFO(st.st_mode)){close(fd);fd=-1;errno=EINVAL;}
    }
    int error=errno;
#ifndef NARO_TINY
    if(modes_saved)tcsetattr(STDIN_FILENO,TCSANOW,&previous_modes);
    if(action_saved)sigaction(SIGINT,&previous_action,NULL);
    if(mask_saved)sigprocmask(SIG_SETMASK,&previous_mask,NULL);
#endif
    errno=error;
    return fd;
}
/* Atomic regular-file saves. Once the directory is opened, use fd-relative
 * operations. Reject final-component symlinks and replace just one hard-link
 * pathname. No pre-rename failure can truncate the destination. */
static int save_write(int fd,const unsigned char *data,size_t len) {
    while(len){
        ssize_t n=write(fd,data,len);
        if(n<0){if(errno==EINTR)continue;return -1;}
        if(n==0){errno=EIO;return -1;}
        data+=n;len-=(size_t)n;
    }
    return 0;
}
static int save_copy(int source,int target) {
    unsigned char data[65536];
    for(;;){
        ssize_t n=read(source,data,sizeof data);
        if(n<0){if(errno==EINTR)continue;return -1;}
        if(n==0)return 0;
        if(save_write(target,data,(size_t)n)<0)return -1;
    }
}
static int save_sync(int fd) {
    int result;
    do{result=fsync(fd);}while(result<0&&errno==EINTR);
    return result;
}
#ifdef __linux__
/* POSIX ACLs are exposed in system.posix_acl_access on Linux. Preserve every
 * namespace or fail closed, removing inherited attributes absent on source. */
static char *save_xattr_names(int fd,ssize_t *length) {
    ssize_t n=flistxattr(fd,NULL,0);
    if(n<0)return NULL;
    char *names=malloc((size_t)n+1);
    if(!names)return NULL;
    /* A zero-sized second call would only query size again. Always supply
     * storage, so concurrent growth fails with ERANGE instead of returning an
     * uninitialized list. */
    ssize_t got=flistxattr(fd,names,(size_t)n+1);
    if(got<0){int e=errno;free(names);errno=e;return NULL;}
    *length=got;
    return names;
}
static int save_xattrs(int source,int target) {
    ssize_t length;
    char *names=save_xattr_names(target,&length);
    if(!names){
        if(errno!=ENOTSUP)return -1;
        ssize_t n=flistxattr(source,NULL,0);
        if(n==0||(n<0&&errno==ENOTSUP))return 0;
        if(n>=0)errno=ENOTSUP;
        return -1;
    }
    for(ssize_t i=0;i<length;i+=(ssize_t)strlen(names+i)+1){
        if(fgetxattr(source,names+i,NULL,0)<0){
            if(errno!=ENODATA)goto fail;
            if(fremovexattr(target,names+i)<0)goto fail;
        }
    }
    free(names);
    names=save_xattr_names(source,&length);
    if(!names)return -1;
    for(ssize_t i=0;i<length;i+=(ssize_t)strlen(names+i)+1){
        ssize_t n=fgetxattr(source,names+i,NULL,0);
        if(n<0)goto fail;
        void *value=malloc(n?(size_t)n:1);
        if(!value)goto fail;
        ssize_t got=fgetxattr(source,names+i,value,n?(size_t)n:1);
        if(got<0){int e=errno;free(value);errno=e;goto fail;}
        int result=fsetxattr(target,names+i,value,(size_t)got,0);
        int e=errno;free(value);errno=e;
        if(result<0)goto fail;
    }
    free(names);return 0;
fail:;
    int e=errno;free(names);errno=e;return -1;
}
#endif
static int save_metadata(int source,int target,const struct stat *original) {
#ifdef __linux__
    struct stat st;
    if(fstat(target,&st)<0)return -1;
    if((st.st_uid!=original->st_uid||st.st_gid!=original->st_gid)&&
       fchown(target,original->st_uid,original->st_gid)<0)return -1;
    if(fchmod(target,original->st_mode&07777)<0)return -1;
    if(save_xattrs(source,target)<0)return -1;
    if(fstat(target,&st)<0)return -1;
    if(st.st_uid!=original->st_uid||st.st_gid!=original->st_gid||
       (st.st_mode&07777)!=(original->st_mode&07777)){errno=EPERM;return -1;}
    return 0;
#else
    /* Do not silently discard ACLs/xattrs on an unsupported platform. */
    (void)source;(void)target;(void)original;errno=ENOTSUP;return -1;
#endif
}
static int save_unchanged(const struct stat *a,const struct stat *b) {
    return a->st_dev==b->st_dev&&a->st_ino==b->st_ino&&
        a->st_size==b->st_size&&a->st_mode==b->st_mode&&
        a->st_uid==b->st_uid&&a->st_gid==b->st_gid&&
        a->st_mtim.tv_sec==b->st_mtim.tv_sec&&a->st_mtim.tv_nsec==b->st_mtim.tv_nsec&&
        a->st_ctim.tv_sec==b->st_ctim.tv_sec&&a->st_ctim.tv_nsec==b->st_ctim.tv_nsec;
}
int nr_file_chown(int fd,uint64_t uid,uint64_t gid) {
    if((uint64_t)(uid_t)uid!=uid||(uint64_t)(gid_t)gid!=gid){errno=EINVAL;return -1;}
    return fchown(fd,(uid_t)uid,(gid_t)gid);
}
int nr_close_checked(int fd) {
    /* Never retry close: on Linux even EINTR releases the descriptor. */
    return close(fd);
}
int nr_safe_save_at(int parent_fd,const char *path,const unsigned char *data,size_t len,int mode,int *committed) {
    int dir=-1,stage=-1,source=-1,temp=-1,result=-1,exists=0;
    int stage_exists=0,stage_identified=0,temp_exists=0,temp_identified=0;
    int error=0;
    struct stat original,current,temporary_stat,stage_stat,parent_stat;
    char stage_name[96];
    const char *temporary="content";
    char *parent=strdup(path);
    const char *name=path;
    static atomic_ulong serial=0;
    *committed=0;
    if(!parent)return -1;
    char *slash=strrchr(parent,'/');
    if(slash){
        name=path+(slash-parent)+1;
        if(slash==parent)slash[1]='\0';else *slash='\0';
    }else{free(parent);parent=strdup(".");if(!parent)return -1;}
    if(!*name||mode<0||mode>2){errno=EINVAL;goto done;}
    do{dir=parent_fd>=0?fcntl(parent_fd,F_DUPFD_CLOEXEC,0):open(parent,O_RDONLY|O_DIRECTORY|O_CLOEXEC);}while(dir<0&&errno==EINTR);
    if(dir<0)goto done;
    if(fstatat(dir,name,&original,AT_SYMLINK_NOFOLLOW)==0){
        exists=1;
        if(S_ISLNK(original.st_mode)){errno=ELOOP;goto done;}
        if(!S_ISREG(original.st_mode)){errno=EINVAL;goto done;}
        do{source=openat(dir,name,(mode?O_RDWR:O_WRONLY)|O_CLOEXEC|O_NOFOLLOW|O_NONBLOCK);}
        while(source<0&&errno==EINTR);
        if(source<0)goto done;
        if(fstat(source,&current)<0)goto done;
        if(!save_unchanged(&original,&current)){errno=ESTALE;goto done;}
    }else if(errno!=ENOENT||mode==2)goto done;
    if(fstat(dir,&parent_stat)<0)goto done;
    /* In a non-sticky shared parent another uid can move our newly created
     * staging entry before openat, then substitute an editor-owned directory.
     * Its owner/device checks would accept the wrong object. A parent owned by
     * another unprivileged uid can also become writable after this check.
     * The group bits include the POSIX ACL mask, so they conservatively cover
     * named-user and named-group ACL write grants. A sticky parent is safe only
     * when its owner is the editor or privileged root: other users cannot move
     * the editor-owned staging entry. */
    if((parent_stat.st_uid!=geteuid()&&parent_stat.st_uid!=0)||
       ((parent_stat.st_mode&(S_IWGRP|S_IWOTH))&&!(parent_stat.st_mode&S_ISVTX))){
        errno=EPERM;goto done;
    }
    for(int attempt=0;attempt<1000;attempt++){
        unsigned long sequence=atomic_fetch_add(&serial,1);
        snprintf(stage_name,sizeof stage_name,".naro-save-%ld-%lu",(long)getpid(),sequence);
        if(strcmp(stage_name,name)==0)continue;
        if(mkdirat(dir,stage_name,0700)==0){stage_exists=1;break;}
        if(errno!=EEXIST)goto done;
    }
    if(!stage_exists){errno=EEXIST;goto done;}
    /* The trusted parent prevents entry substitution before this open. Keep
     * temporary bytes in a private child and publish from its held fd. */
    stage=openat(dir,stage_name,O_RDONLY|O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC);
    if(stage<0)goto done;
    if(fstat(stage,&stage_stat)<0)goto done;
    stage_identified=1;
    if(!S_ISDIR(stage_stat.st_mode)||stage_stat.st_uid!=geteuid()||
       stage_stat.st_dev!=parent_stat.st_dev){errno=ESTALE;goto done;}
    if(fchmod(stage,(stage_stat.st_mode&S_ISGID)|0700)<0)goto done;
    if(fstatat(dir,stage_name,&current,AT_SYMLINK_NOFOLLOW)<0)goto done;
    if(current.st_dev!=stage_stat.st_dev||current.st_ino!=stage_stat.st_ino){errno=ESTALE;goto done;}
    do{temp=openat(stage,temporary,O_WRONLY|O_CREAT|O_EXCL|O_CLOEXEC,exists?0600:0666);}
    while(temp<0&&errno==EINTR);
    if(temp<0)goto done;
    temp_exists=1;
    /* Creation applies umask/default ACLs for new files. Keep unpublished
     * content private until metadata is finalized. */
    if(fstat(temp,&current)<0)goto done;
    temporary_stat=current;temp_identified=1;
    mode_t new_mode=current.st_mode&07777;
    if(fchmod(temp,0600)<0)goto done;
    if(mode==1&&exists&&save_copy(source,temp)<0)goto done;
    if(save_write(temp,data,len)<0)goto done;
    if(mode==2&&save_copy(source,temp)<0)goto done;
    if(exists){if(save_metadata(source,temp,&original)<0)goto done;}
    else if(fchmod(temp,new_mode)<0)goto done;
    if(save_sync(temp)<0)goto done;
    int closing=temp;temp=-1;
    if(nr_close_checked(closing)<0)goto done;
    if(exists){
        if(fstat(source,&current)<0)goto done;
        if(!save_unchanged(&original,&current)){errno=ESTALE;goto done;}
        closing=source;source=-1;
        if(nr_close_checked(closing)<0)goto done;
        if(fstatat(dir,name,&current,AT_SYMLINK_NOFOLLOW)<0)goto done;
        if(!save_unchanged(&original,&current)){errno=ESTALE;goto done;}
    }else if(fstatat(dir,name,&current,AT_SYMLINK_NOFOLLOW)==0){errno=EEXIST;goto done;}
    else if(errno!=ENOENT)goto done;
    if(fstatat(stage,temporary,&current,AT_SYMLINK_NOFOLLOW)<0)goto done;
    if(current.st_dev!=temporary_stat.st_dev||current.st_ino!=temporary_stat.st_ino){errno=ESTALE;goto done;}
    if(renameat(stage,temporary,dir,name)<0)goto done;
    temp_exists=0;*committed=1;
    if(save_sync(stage)<0)goto done;
    if(save_sync(dir)<0)goto done;
    if(fstatat(dir,stage_name,&current,AT_SYMLINK_NOFOLLOW)<0)goto done;
    if(current.st_dev!=stage_stat.st_dev||current.st_ino!=stage_stat.st_ino){errno=ESTALE;goto done;}
    if(unlinkat(dir,stage_name,AT_REMOVEDIR)<0)goto done;
    stage_exists=0;
    if(save_sync(dir)<0)goto done;
    closing=stage;stage=-1;
    if(nr_close_checked(closing)<0)goto done;
    closing=dir;dir=-1;
    if(nr_close_checked(closing)<0)goto done;
    result=0;
done:
    error=errno;
    if(temp>=0)close(temp);
    if(source>=0)close(source);
    if(temp_exists&&temp_identified&&stage>=0&&fstatat(stage,temporary,&current,AT_SYMLINK_NOFOLLOW)==0&&
       current.st_dev==temporary_stat.st_dev&&current.st_ino==temporary_stat.st_ino)
        unlinkat(stage,temporary,0);
    if(stage_exists&&stage_identified&&dir>=0&&
       fstatat(dir,stage_name,&current,AT_SYMLINK_NOFOLLOW)==0&&
       current.st_dev==stage_stat.st_dev&&current.st_ino==stage_stat.st_ino)
        unlinkat(dir,stage_name,AT_REMOVEDIR);
    if(stage>=0)close(stage);
    if(dir>=0)close(dir);
    free(parent);errno=error;
    return result;
}
int nr_safe_save(const char *path,const unsigned char *data,size_t len,int mode,int *committed) {
    return nr_safe_save_at(-1,path,data,len,mode,committed);
}
static void modes(int preserve) {
    raw();nonl();noecho();
    struct termios t; if(tcgetattr(0,&t)==0){t.c_lflag &= ~(IEXTEN|ISIG);t.c_oflag &= ~OPOST;
    if(preserve)t.c_iflag|=IXON;else t.c_iflag &= ~IXON;tcsetattr(0,TCSANOW,&t);}
#ifndef NARO_TINY
    fputs("\033[?2004h",stdout);fflush(stdout);
#endif
}
int nr_init(int preserve,int rawseq) {
    if(tcgetattr(0,&saved)==0)have_saved=1;
    if(!getenv("TERM"))setenv("TERM","vt220",1);
    if(!initscr())return 0;
    active=1;
#ifndef NARO_TINY
    start_color();use_default_colors();
#endif
    set_escdelay(50);typeahead(-1);
    keypad(stdscr,!rawseq);scrollok(stdscr,FALSE);
#ifndef NARO_TINY
    define_key("\033[200~",0x4b5);define_key("\033[201~",0x4be);
#endif
    modes(preserve);return 1;
}
void nr_finish(int start) { if(active) { wattrset(stdscr,A_NORMAL); for(int y=start;y<LINES;y++){ wmove(stdscr,y,0);wclrtoeol(stdscr); } wmove(stdscr,LINES-1,0);wrefresh(stdscr); } }
void nr_done(void) {
    if(active){curs_set(1);mousemask(0,NULL);wattrset(stdscr,A_NORMAL);wmove(stdscr,LINES-1,0);endwin();active=0;}
#ifndef NARO_TINY
    fputs("\033[?2004l",stdout);fflush(stdout);
#endif
    if(have_saved)tcsetattr(0,TCSANOW,&saved);
}
void nr_resume(int preserve) {refresh();active=1;modes(preserve);}
void nr_resize(void) {endwin();refresh();clearok(stdscr,TRUE);}
int nr_rows(void) {return LINES;}
int nr_cols(void) {return COLS;}
void nr_erase(void) {werase(stdscr);}
void nr_refresh(int row,int col,int visible) {wmove(stdscr,row,col);curs_set(visible);wrefresh(stdscr);}
void nr_hide_cursor(void) {curs_set(0);}
void nr_beep(void) {beep();}
int nr_get(int ms) {wtimeout(stdscr,ms);return wgetch(stdscr);}
void nr_keypad(int yes) {keypad(stdscr,yes);}
void nr_paste(int yes) {
#ifndef NARO_TINY
    fputs(yes?"\033[?2004h":"\033[?2004l",stdout);fflush(stdout);
#else
    (void)yes;
#endif
}
void nr_mouse(int yes) {mouseinterval(50);mousemask(yes?ALL_MOUSE_EVENTS:0,NULL);}
int nr_mouse_event(int *x,int *y) {MEVENT ev;if(getmouse(&ev)!=OK)return 0;*x=ev.x;*y=ev.y;
    if(ev.bstate & BUTTON1_CLICKED)return 1;
    if(ev.bstate & BUTTON1_RELEASED)return 1;
    if(ev.bstate & BUTTON4_PRESSED)return 4;
#ifdef BUTTON5_PRESSED
    if(ev.bstate & BUTTON5_PRESSED)return 5;
#endif
    return 0;
}
/* Small independent style bitset: bold italic reverse underline dim blink. */
void nr_put(int y,int x,const uint32_t *chars,int count,int style,int fg,int bg) {
    if(y<0||y>=LINES||x<0||x>=COLS)return;
    attr_t a=0; if(style&1)a|=A_BOLD;if(style&2)a|=A_ITALIC;if(style&4)a|=A_REVERSE;
    if(style&8)a|=A_UNDERLINE;
    if(style&16)a|=A_DIM;
    if(style&32)a|=A_BLINK;
    short pair=0;
    if(has_colors()&&(fg>=0||bg>=0)){
        static short fgs[1024],bgs[1024];static int next=1;
        for(int i=1;i<next;i++)if(fgs[i]==fg&&bgs[i]==bg){pair=i;break;}
        if(!pair&&next<COLOR_PAIRS&&next<1024){pair=next++;fgs[pair]=fg;bgs[pair]=bg;init_pair(pair,fg,bg);}
    }
    wchar_t w[CCHARW_MAX]={0};int n=0;
    for(int i=0;i<count&&n<CCHARW_MAX-1;i++){
        if(nr_on_vt()&&wcwidth((wchar_t)chars[i])==0)continue;
        w[n++]=(wchar_t)chars[i];
    }
    if(n==0)return;
    cchar_t cell;setcchar(&cell,w,a,pair,NULL);mvwadd_wch(stdscr,y,x,&cell);
}
int nr_map(int key) {
#ifdef NARO_TINY
    const char *caps[]={"kLFT5","kRIT5","kUP5","kDN5","kHOM5","kEND5",NULL};
    const int codes[]={0x401,0x402,0x403,0x404,0x405,0x406};
#else
    const char *caps[]={"kLFT5","kRIT5","kUP5","kDN5","kHOM5","kEND5","kDC5","kDC6", "kLFT6","kRIT6","kUP6","kDN6","kHOM6","kEND6", "kLFT3","kRIT3","kUP3","kDN3","kHOM3","kEND3","kPRV3","kNXT3","kIC3","kDC3", "kLFT4","kRIT4","kUP4","kDN4","kUP","kDN",NULL};
    const int codes[]={0x401,0x402,0x403,0x404,0x405,0x406,0x40d,0x41d,0x411,0x412,0x413,0x414,0x415,0x416,0x421,0x422,0x423,0x424,0x425,0x426,0x427,0x428,0x42c,0x42d,0x431,0x432,0x433,0x434,0x453,0x454};
#endif
    for(int i=0;caps[i];i++){char *s=tigetstr(caps[i]);if(s&&s!=(char*)-1&&key_defined(s)==key)return codes[i];}
    switch(key){case KEY_SLEFT:return 0x451;case KEY_SRIGHT:return 0x452;case KEY_SR:return 0x453;case KEY_SF:return 0x454;case KEY_SHOME:return 0x455;case KEY_SEND:return 0x456;case KEY_SPREVIOUS:return 0x457;case KEY_SNEXT:return 0x458;case KEY_SDC:return 0x45d;case KEY_BTAB:return 0x45f;case KEY_A1:return KEY_HOME;case KEY_C1:return KEY_END;case KEY_A3:return KEY_PPAGE;case KEY_C3:return KEY_NPAGE;}
    return key;
}
void *nr_regex(const char *pattern,int flags,char *error,size_t cap) {
    regex_t *r=calloc(1,sizeof(*r));if(!r)return NULL;
    int ret=regcomp(r,pattern,(flags&1?REG_EXTENDED:0)|(flags&2?REG_ICASE:0)|(flags&4?REG_NOSUB:0));
    if(ret){regerror(ret,r,error,cap);free(r);return NULL;}return r;
}
int nr_match(void *r,const char *text,size_t len,size_t start,int notbol,int *pairs,int count) {
    if(count<1||count>10||start>len)return -1;
    regmatch_t m[10]={{0}};m[0].rm_so=start;m[0].rm_eo=len;
    int ret=regexec(r,text,count,m,REG_STARTEND|(notbol?REG_NOTBOL:0));
    if(ret)return ret;
    for(int i=0;i<count;i++){pairs[2*i]=m[i].rm_so;pairs[2*i+1]=m[i].rm_eo;}return 0;
}
int nr_nsub(void *r) {return ((regex_t*)r)->re_nsub;}
void nr_regex_free(void *r) {regfree(r);free(r);}
const char *nr_magic(const char *path) {
#ifndef NARO_TINY
    static magic_t m; if(!m){m=magic_open(MAGIC_SYMLINK);if(!m||magic_load(m,NULL))return NULL;}return magic_file(m,path);
#else
    (void)path;return NULL;
#endif
}
const char *nr_magic_fd(int fd) {
#ifndef NARO_TINY
    static magic_t m;
    if(!m){m=magic_open(0);if(!m||magic_load(m,NULL))return NULL;}
    return magic_descriptor(m,fd);
#else
    (void)fd;return NULL;
#endif
}
void nr_stop(void) {kill(0,SIGSTOP);}
const char *nr_host(void) {static char host[256];if(gethostname(host,sizeof(host)-1))host[0]=0;return host;}
#include <ctype.h>
int nr_byte_lower(int b) {return tolower((unsigned char)b);}
void nr_configure(int preserve,int rawseq) {keypad(stdscr,!rawseq);modes(preserve);}
int nr_colors(void) {return COLORS;}
void nr_child_signals(void) {
    struct sigaction a={0};sigemptyset(&a.sa_mask);a.sa_handler=SIG_DFL;
    sigaction(SIGINT,&a,NULL);sigaction(SIGQUIT,&a,NULL);sigaction(SIGPIPE,&a,NULL);
}
int nr_collate(const char *a,const char *b) {return strcoll(a,b);}
int nr_print_byte(int b) {return isprint((unsigned char)b);}

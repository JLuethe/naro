/* Naro native ABI bridge. GPL-3.0-or-later.
 * Behavioral reference: 6ed285c3ec7a1d228def4d4e7021c6ba269f620c. */
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
#include <wchar.h>
#include <wctype.h>
#include <sys/ioctl.h>
#include <pwd.h>
#include <magic.h>
#include "options.inc"
static struct termios saved;
static int active, have_saved;
static volatile sig_atomic_t pending;
static void handler(int sig) { pending = sig; }
int nr_signal(void) { int s=pending; pending=0; return s; }
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
int nr_option(int argc,char **argv) {return getopt_long(argc,argv,"ABC:DEFGHIJ:KLMNOPQ:RST:UVWX:Y:Zabcdef:ghijklmno:pqr:s:tuvwxyz!@%_01/",options,NULL);}
const char *nr_optarg(void) {return optarg;}
int nr_optind(void) {return optind;}
void nr_setup_signals(void) {
    struct sigaction a={0}; sigemptyset(&a.sa_mask); a.sa_handler=handler;
    for(int i=1;i<32;i++) if(i==SIGHUP||i==SIGTERM||i==SIGTSTP||i==SIGCONT||i==SIGWINCH) sigaction(i,&a,NULL);
    signal(SIGINT,SIG_IGN);signal(SIGQUIT,SIG_IGN);
}
static void modes(int preserve) {
    raw();nonl();noecho();
    struct termios t; if(tcgetattr(0,&t)==0){t.c_lflag &= ~(IEXTEN|ISIG);t.c_oflag &= ~OPOST;
    if(preserve)t.c_iflag|=IXON;else t.c_iflag &= ~IXON;tcsetattr(0,TCSANOW,&t);}
    fputs("\033[?2004h",stdout);fflush(stdout);
}
int nr_init(int preserve,int rawseq) {
    if(tcgetattr(0,&saved)==0)have_saved=1;
    if(!getenv("TERM"))setenv("TERM","vt220",1);
    if(!initscr())return 0;
    active=1;
    start_color();use_default_colors();set_escdelay(50);typeahead(-1);
    keypad(stdscr,!rawseq);scrollok(stdscr,FALSE);
    define_key("\033[200~",0x4b5);define_key("\033[201~",0x4be);
    modes(preserve);return 1;
}
void nr_finish(int start) { if(active) { wattrset(stdscr,A_NORMAL); for(int y=start;y<LINES;y++){ wmove(stdscr,y,0);wclrtoeol(stdscr); } wmove(stdscr,LINES-1,0);wrefresh(stdscr); } }
void nr_done(void) {
    if(active){curs_set(1);mousemask(0,NULL);wattrset(stdscr,A_NORMAL);wmove(stdscr,LINES-1,0);endwin();active=0;}
    fputs("\033[?2004l",stdout);fflush(stdout);
    if(have_saved)tcsetattr(0,TCSANOW,&saved);
}
void nr_resume(int preserve) {refresh();active=1;modes(preserve);}
void nr_resize(void) {endwin();refresh();clearok(stdscr,TRUE);}
int nr_rows(void) {return LINES;}
int nr_cols(void) {return COLS;}
void nr_erase(void) {werase(stdscr);}
void nr_refresh(int row,int col,int visible) {wmove(stdscr,row,col);curs_set(visible);wrefresh(stdscr);}
void nr_beep(void) {beep();}
int nr_get(int ms) {wtimeout(stdscr,ms);return wgetch(stdscr);}
void nr_keypad(int yes) {keypad(stdscr,yes);}
void nr_paste(int yes) {fputs(yes?"\033[?2004h":"\033[?2004l",stdout);fflush(stdout);}
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
    wchar_t w[CCHARW_MAX]={0};int n=count<CCHARW_MAX-1?count:CCHARW_MAX-1;
    for(int i=0;i<n;i++)w[i]=(wchar_t)chars[i];
    cchar_t cell;setcchar(&cell,w,a,pair,NULL);mvwadd_wch(stdscr,y,x,&cell);
}
int nr_map(int key) {
    const char *caps[]={"kLFT5","kRIT5","kUP5","kDN5","kHOM5","kEND5","kDC5","kDC6", "kLFT6","kRIT6","kUP6","kDN6","kHOM6","kEND6", "kLFT3","kRIT3","kUP3","kDN3","kHOM3","kEND3","kPRV3","kNXT3","kIC3","kDC3", "kLFT4","kRIT4","kUP4","kDN4","kUP","kDN",NULL};
    const int codes[]={0x401,0x402,0x403,0x404,0x405,0x406,0x40d,0x41d,0x411,0x412,0x413,0x414,0x415,0x416,0x421,0x422,0x423,0x424,0x425,0x426,0x427,0x428,0x42c,0x42d,0x431,0x432,0x433,0x434,0x453,0x454};
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
const char *nr_magic(const char *path) {static magic_t m; if(!m){m=magic_open(MAGIC_SYMLINK);if(!m||magic_load(m,NULL))return NULL;}return magic_file(m,path);}
void nr_stop(void) {kill(0,SIGSTOP);}
const char *nr_host(void) {static char host[256];if(gethostname(host,sizeof(host)-1))host[0]=0;return host;}
#include <ctype.h>
int nr_byte_lower(int b) {return tolower((unsigned char)b);}
void nr_configure(int preserve,int rawseq) {keypad(stdscr,!rawseq);modes(preserve);}
const char *nr_position(int lw,size_t line,size_t total_lines,int linepct,size_t col,size_t cols,int colpct,int cw,size_t count,size_t total,int charpct) {
    static char out[1024];snprintf(out,sizeof(out),gettext("line %*zd/%zd (%2d%%), col %2zu/%2zu (%3d%%), char %*zu/%zu (%2d%%)"),lw,line,total_lines,linepct,col,cols,colpct,cw,count,total,charpct);return out;
}
int nr_colors(void) {return COLORS;}
void nr_child_signals(void) {
    struct sigaction a={0};sigemptyset(&a.sa_mask);a.sa_handler=SIG_DFL;
    sigaction(SIGINT,&a,NULL);sigaction(SIGQUIT,&a,NULL);sigaction(SIGPIPE,&a,NULL);
}
int nr_collate(const char *a,const char *b) {return strcoll(a,b);}
int nr_print_byte(int b) {return isprint((unsigned char)b);}

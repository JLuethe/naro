"""Adapt fixture-owned preload gates to variadic and fortified glibc opens.

Original scenarios and assertions stay unchanged; callers record the generated
helper source in their selected scenario inputs.
"""
import copy


def open_wrappers(interrupt=False, target_function="is_target"):
    """Interpose the existing open surface and its glibc fortified aliases.

    Keep fortified calls on their real two-argument entry points so libc still
    validates missing modes. No openat64 surface is needed by these fixtures.
    """
    if interrupt:
        before = f'if({target_function}(path,flags))mark();'
    else:
        before = '''if((flags&(O_WRONLY|O_RDWR))&&target_path(path)){
  if(gate("OPEN",&once_open)<0)return -1;
  if(getenv("FAIL_OPEN")){errno=EACCES;return -1;}
 }'''
    source = '''
static int before_open(const char *path,int flags) {
 BEFORE
 return 0;
}
static int before_openat(int dirfd,const char *path,int flags) {
 char resolved[PATH_MAX];
 if(path[0]=='/' || dirfd==AT_FDCWD)return before_open(path,flags);
 snprintf(resolved,sizeof resolved,"/proc/self/fd/%d/%s",dirfd,path);
 return before_open(resolved,flags);
}
static int needs_mode(int flags) {
 return (flags&O_CREAT) || ((flags&O_TMPFILE)==O_TMPFILE);
}
'''.replace('BEFORE', before)
    # open64 was already interposed; cover its fortified counterpart too.
    for symbol in ('open', 'open64', 'openat'):
        at = symbol == 'openat'
        args = 'int dirfd,const char *path,int flags' if at else 'const char *path,int flags'
        types = 'int,const char*,int' if at else 'const char*,int'
        call = 'dirfd,path,flags' if at else 'path,flags'
        check = 'before_openat(dirfd,path,flags)' if at else 'before_open(path,flags)'
        source += f'''
int {symbol}({args},...) {{
 mode_t mode=0;
 if(needs_mode(flags)){{va_list a;va_start(a,flags);mode=va_arg(a,mode_t);va_end(a);}}
 int (*real_fn)({types},...)=dlsym(RTLD_NEXT,"{symbol}");
 if({check}<0)return -1;
 return needs_mode(flags)?real_fn({call},mode):real_fn({call});
}}
int __{symbol}_2({args}) {{
 int (*real_fn)({types})=dlsym(RTLD_NEXT,"__{symbol}_2");
 if({check}<0)return -1;
 return real_fn({call});
}}
'''
    return source


def adapt_open_gate(text, interrupt=False, target_function="is_target"):
    if interrupt:
        start = text.index('static int(*real_open_fn)')
        end = text.index('static int ' + target_function, start)
        text = text[:start] + text[end:]
        start = text.index('int open(')
        return text[:start] + open_wrappers(interrupt=True, target_function=target_function)
    start = text.index('static int do_open(')
    end = text.index('int fsync(', start)
    return text[:start] + open_wrappers() + text[end:]


def adapt_tiny_safety_case(case):
    """Cover fortified opens in the tiny FIFO resize gate, retaining its proof."""
    selected = copy.deepcopy(case)
    if selected["id"] == "TEST-TINY-FIFO-RESIZE-SAFETY":
        gate = selected["files"]["gate.c"]
        gate["text"] = adapt_open_gate(gate["text"], interrupt=True, target_function="target")
    return selected

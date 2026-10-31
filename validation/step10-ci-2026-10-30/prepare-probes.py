from pathlib import Path
import copy,json
base=Path(__file__).resolve().parent
cases=json.loads(Path('tests/follow-up/scenarios/step3-gaps.json').read_text());original=next(c for c in cases if c['id']=='TEST-STEP3-EOF-NOFINAL-LIVE')
helper=r'''#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdlib.h>
#include <unistd.h>
#include <stdio.h>
#include <time.h>
#include <errno.h>
int fsync(int fd) {
    int (*real_fsync)(int) = dlsym(RTLD_NEXT, "fsync");
    const char *s=getenv("NARO_PROBE_DELAY_MS");
    long ms=s?strtol(s,0,10):0;
    fprintf(stderr,"probe fsync enter delay=%ldms\n",ms); fflush(stderr);
    struct timespec pause={ms/1000,(ms%1000)*1000000};
    while(nanosleep(&pause,&pause) && errno==EINTR) {}
    int result=real_fsync(fd), saved=errno;
    fprintf(stderr,"probe fsync returned %d\n",result); fflush(stderr);
    errno=saved; return result;
}
'''
def synchronized(c):
 c=copy.deepcopy(c);steps=c['steps'];i=next(i for i,s in enumerate(steps)if s.get('keys')==['^O']);assert steps[i+1]=={'sleep':150};steps[i+1]={'wait':{'text':'Write to File:','timeout':5}};assert steps[i+2]=={'keys':['Enter']};steps.insert(i+3,{'wait':{'text':'Wrote 2 lines','timeout':5}});return c
(base/'original.json').write_text(json.dumps([original],indent=2)+'\n');(base/'synchronized.json').write_text(json.dumps([synchronized(original)],indent=2)+'\n')
for mode in ('original','synchronized'):
 probes=[]
 for delay in (0,600,1200):
  c=copy.deepcopy(original)if mode=='original'else synchronized(original)
  c['id']=f'TEST-STEP10-{mode.upper()}-{delay}'
  c['files']['delay.c']={'text':helper};c['build_helpers']=[{'source':'delay.c','output':'delay.so'}];c['env']={'LD_PRELOAD':'$FX/delay.so','NARO_PROBE_DELAY_MS':str(delay)}
  probes.append(c)
 (base/(mode+'-delayed.json')).write_text(json.dumps(probes,indent=2)+'\n')
print('Created original, synchronized, and controlled-delay scratch probes; expectations unchanged.')

/* Synthetic regression driver; bridge source is instrumented only in the test
 * executable to deliver a signal exactly between snapshot and consume. */
#include <signal.h>
#include <stdatomic.h>
#include <pthread.h>
#include <sched.h>
#include <stdio.h>
#include <errno.h>
#include <stdlib.h>
#include <string.h>

void nr_setup_signals(void);
int nr_signal(void);
static int inject;
void nr_test_window(void) {
    int sig=inject;
    inject=0;
    if(sig)raise(sig);
}
static int failures,cases;
static void check(int ok,const char *name) {
    cases++;
    if(!ok){failures++;printf("FAIL %s\n",name);}
}
static void drain(void) {while(nr_signal());}
static int bit(int sig) {
    switch(sig){case SIGHUP:return 1;case SIGTERM:return 2;
        case SIGTSTP:return 4;case SIGCONT:return 8;case SIGWINCH:return 16;}
    return 0;
}
static int take(void) {
    int mask=0,sig;
    while((sig=nr_signal())){
        if(mask&bit(sig))return -1;
        mask|=bit(sig);
    }
    return mask;
}
static atomic_int phase;
static void *writer(void *unused) {
    (void)unused;
    for(int i=0;i<10000;i++){
        while(atomic_load(&phase)!=1)sched_yield();
        raise(SIGHUP); /* handler actually executes on the worker thread */
        atomic_store(&phase,2);
        while(atomic_load(&phase)!=0)sched_yield();
        atomic_store(&phase,3);
    }
    return NULL;
}
int main(void) {
    nr_setup_signals();
    int sigs[]={SIGHUP,SIGTERM,SIGTSTP,SIGCONT,SIGWINCH};
    int burst[]={SIGHUP,SIGTERM,SIGWINCH};
    for(int a=0;a<3;a++)for(int b=0;b<3;b++)for(int c=0;c<3;c++){
        if(a==b||b==c||a==c)continue;
        drain();raise(burst[a]);raise(burst[b]);raise(burst[c]);
        check(take()==19,"HUP TERM WINCH permutation preserves all classes");
    }
    for(int i=0;i<5;i++)for(int j=0;j<5;j++){
        drain();raise(sigs[i]);inject=sigs[j];
        check(take()==(bit(sigs[i])|bit(sigs[j])),"delivery in snapshot/consume window");
    }
    drain();
    for(int i=4;i>=0;i--)for(int j=0;j<1000;j++)raise(sigs[i]);
    check(nr_signal()==SIGHUP,"HUP priority");
    check(nr_signal()==SIGTERM,"TERM priority");
    check(take()==28,"all terminal classes retained after termination consume");
    sigset_t block,previous,after;
    sigemptyset(&block);sigaddset(&block,SIGUSR1);
    sigprocmask(SIG_BLOCK,&block,&previous);
    raise(SIGWINCH);errno=EDOM;
    check(nr_signal()==SIGWINCH&&errno==EDOM,"consumer preserves errno");
    sigprocmask(SIG_SETMASK,NULL,&after);
    check(sigismember(&after,SIGUSR1)==1,"consumer preserves caller mask");
    sigprocmask(SIG_SETMASK,&previous,NULL);
    pthread_t thread;
    if(pthread_create(&thread,NULL,writer,NULL))return 2;
    int races_ok=1;
    for(int i=0;i<10000;i++){
        drain();raise(SIGWINCH);atomic_store(&phase,1);
        int mask=bit(nr_signal());
        while(atomic_load(&phase)!=2)sched_yield();
        mask|=take();
        if(mask!=17)races_ok=0;
        atomic_store(&phase,0);
        while(atomic_load(&phase)!=3)sched_yield();
    }
    pthread_join(thread,NULL);
    check(races_ok,"10000 worker-thread delivery/consume races");
    printf("%d/%d native checks passed\n",cases-failures,cases);
    return failures?1:0;
}

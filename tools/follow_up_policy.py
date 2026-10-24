"""Named follow-up differences; GNU reference 6ed285c3ec7a1d228def4d4e7021c6ba269f620c."""
from compare_runs import compare


def deviation(tid, reference, candidate, differences):
    fields={d['field']for d in differences}
    if tid in ('TEST-NEXT-TOOL-003-SIGTERM','TEST-NEXT-TOOL-003-SIGHUP')and fields=={'temp_files'}:
        return 'Q-TOOL-001'
    if tid!='TEST-ROOT-HOME-002-NO-HOME-TILDE':return None
    ns=reference.get('root_namespace')or{}
    if ns.get('euid')!=0 or ns.get('passwd_home')is not None or ns.get('HOME')is not None:return None
    allowed=all(field in ('exit_status','stderr','after_exit_screen')or field.startswith('snapshot.opened.')for field in fields)
    files={d['field']for d in compare(reference,candidate,True)}
    if (allowed and files=={'exit_status'} and reference.get('exit_status')==1
        and 'Sorry! Nano crashed!  Code: 11.'in reference.get('stderr','')
        and candidate.get('exit_status')==0 and not candidate.get('stderr')
        and reference.get('steps_ok')and candidate.get('steps_ok')
        and all(c['pass']for r in [reference,candidate]for c in r['checks'])):
        return 'Q-ROOT-NOHOME-001'
    return None

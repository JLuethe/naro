#!/usr/bin/env python3
"""Root fixture cases for reference 6ed285c3ec7a1d228def4d4e7021c6ba269f620c."""
import copy,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'tests/follow-up/scenarios'
cases=[]
variants=[('ROOT-SET',0,'$FX/home','account'),('ROOT-UNSET',0,None,'account'),('ROOT-EMPTY',0,'','account'),('ROOT-MISSING-SET',0,'$FX/home',None),('ROOT-MISSING-UNSET',0,None,None),('ROOT-PASSWD-EMPTY',0,'$FX/home',''),('USER-SET',1000,'$FX/home','account'),('USER-UNSET',1000,None,'account'),('USER-EMPTY',1000,'','account'),('USER-MISSING-UNSET',1000,None,None)]
for label,uid,home,account in variants:
 selected=account if uid==0 and account is not None or home is None else 'home'if home else None
 if selected=='':selected=None
 entries=[]if account is None else[dict(name='fixture',uid=uid,home=account)]
 sc=dict(id='TEST-ROOT-HOME-001-'+label,root_namespace={'uid':uid,'passwd_entries':entries},env={'HOME':home},args=['--rcfile','$FX/work/policy','-H','f.txt'],dirs=['account','changed','work/.local/share'],files={'work/policy':{'text':''},'work/f.txt':{'text':'needle\n'},'work/.nanorc':{'text':'set tabsize 9\n'}},steps=[{'settle':250},{'keys':['^W']},{'text':'needle\r'},{'snapshot':'found'},{'keys':['^X']},{'wait_exit':5}],expect={'exit_status':0,'root_namespace':{'euid':uid,'null_is_character_device':True,'passwd_home':None if account is None else '$FX/'+account if account else''},'files':{}})
 for folder in ['account','home','work']:
  sc['expect']['files'][folder+'/.local/share/nano/search_history']={'text':'needle\n\n\n\n','mode':'0o600'}if folder==selected else None
 cases.append(sc)
for uid in [0,1000]:
 sc=copy.deepcopy(cases[0]);sc['id']='TEST-ROOT-HOME-002-RC-'+str(uid);sc['root_namespace']['uid']=uid;sc['root_namespace']['passwd_entries'][0]['uid']=uid;sc['args']=['f.txt'];sc['files']['account/.nanorc']={'text':'set tabsize 3\n'};sc['files']['home/.nanorc']={'text':'set tabsize 7\n'};sc['steps']=[{'settle':250},{'text':'\tX'},{'snapshot':'tab'},{'keys':['^S','^X']},{'wait_exit':5}];sc['expect']={'exit_status':0,'screen':[{'snapshot':'tab','cursor':{'x':4 if uid==0 else 8,'y':1}}]};cases.append(sc)
sc=copy.deepcopy(cases[-2]);sc['id']='TEST-ROOT-HOME-002-CACHE';sc['files']['account/other']={'text':'ACCOUNT\n'};sc['files']['work/changed/other']={'text':'CHANGED\n'};sc['steps']=[{'settle':250},{'write_file':'namespace-nss/passwd','content':'fixture:x:0:0:Fixture:changed:/bin/sh\n'},{'keys':['^R']},{'text':'~/other\r'},{'snapshot':'inserted'},{'keys':['^S','^X']},{'wait_exit':5}];sc['expect']={'exit_status':0,'files':{'work/f.txt':{'text':'ACCOUNT\nneedle\n'}}};cases.append(sc)
sc=copy.deepcopy(cases[0]);sc['id']='TEST-ROOT-STATE-001-POSITION';sc['args']=['-I','-P','-H','f.txt'];sc['steps']=[{'settle':250},{'keys':['Down','End']},{'keys':['^W']},{'text':'needle\r'},{'keys':['^X']},{'wait_exit':5}];sc['expect']['files']['account/.local/share/nano/filepos_history']={'type':'file','mode':'0o600'};cases.append(sc)
for label,args in [('ROOT',['-I','~/other']),('NAMED',['-I','~fixture/other']),('BARE',['-I','~'])]:
 sc=copy.deepcopy(cases[0]);sc['id']='TEST-ROOT-HOME-002-TILDE-'+label;sc['args']=args;sc['files']['account/other']={'text':'ACCOUNT\n'};sc['files']['home/other']={'text':'ENV\n'};sc['files']['work/~']={'text':'LITERAL\n'};sc['steps']=[{'settle':250},{'snapshot':'opened'},{'keys':['^X']},{'wait_exit':5}];sc['expect']={'exit_status':0,'screen':[{'snapshot':'opened','anywhere':'LITERAL'if label=='BARE'else'ACCOUNT'}]};cases.append(sc)
# Fresh counterparts, preserving filesystem type and actual namespace-root semantics.
sc=copy.deepcopy(cases[0]);sc['id']='TEST-ROOT-PATH-001-NULL';sc['args']=['-I','/dev/null'];sc['steps']=[{'settle':250},{'snapshot':'device'},{'keys':['^X']},{'wait_exit':5}];sc['expect']={'exit_status':0,'root_namespace':{'euid':0,'null_is_character_device':True,'null_device':[1,3]},'screen':[{'snapshot':'device','anywhere':"'/dev/null' is a device file"}]};sc['original_id']='TEST-CLI-025';cases.append(sc)
sc=copy.deepcopy(sc);sc['id']='TEST-ROOT-PATH-001-BROWSER';sc['original_id']='TEST-BROWSE-003';sc['args']=['-I','f.txt'];sc['steps']=[{'settle':250},{'keys':['^R','^T','^_']},{'text':'/\r'},{'snapshot':'root'},{'keys':['^_']},{'text':'/../\r'},{'snapshot':'parent'},{'keys':['^C','^C','^X']},{'wait_exit':5}];sc['expect']={'exit_status':0,'root_namespace':{'euid':0,'null_is_character_device':True},'screen':[{'snapshot':'root','row':0,'contains':'DIR: /'},{'snapshot':'parent','row':0,'contains':'DIR: /'}]};cases.append(sc)
sc=copy.deepcopy(cases[0]);sc['id']='TEST-ROOT-HOME-001-NO-HOME-RC';sc['root_namespace']['passwd_entries']=[];sc['env']['HOME']=None;sc['args']=['f.txt'];sc['steps']=[{'settle':250},{'snapshot':'diagnostic'},{'keys':['^X']},{'wait_exit':5}];sc['expect']={'exit_status':0,'stderr_contains':"I can't find my home directory!  Wah!",'files':{'work/.local/share/nano':None}};cases.append(sc)
# Backup faults execute inside the same private uid/NSS namespace.
backup=json.loads((OUT/'backup.json').read_text())[0]
for label,entries,home,target in [('ACCOUNT',[dict(name='fixture',uid=0,home='account')],'$FX/home','account'),('MISSING',[],'$FX/home','home')]:
 sc=copy.deepcopy(backup);sc['id']='TEST-ROOT-STATE-002-'+label;sc['root_namespace']={'uid':0,'passwd_entries':entries};sc['dirs']=['account'];sc['env']['HOME']=home;cases.append(sc)
(OUT/'root.json').write_text(json.dumps(cases,indent=1)+'\n');print(len(cases),'root cases')

sc=copy.deepcopy(next(c for c in cases if c['id']=='TEST-ROOT-HOME-001-NO-HOME-RC'));sc['id']='TEST-ROOT-HOME-002-NO-HOME-TILDE';sc['args']=['-I','~/other'];sc['files']['work/~/other']={'text':'LOCAL\n'};sc['steps']=[{'settle':250},{'snapshot':'opened'},{'keys':['^X']},{'wait_exit':5}];sc['expect']={'exit_status':1,'stderr_contains':'Sorry! Nano crashed!  Code: 11.','files':{'work/~/other':{'text':'LOCAL\n'}}};sc['candidate_expect']={'exit_status':0,'files':{'work/~/other':{'text':'LOCAL\n'}},'screen':[{'snapshot':'opened','anywhere':'LOCAL'}]}
(OUT/'root-nohome-tilde.json').write_text(json.dumps([sc],indent=1)+'\n')

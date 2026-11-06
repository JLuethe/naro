#!/usr/bin/env python3
"""Strict identity projections preserve unrelated differences."""
import copy,json,unittest
from pathlib import Path
from identity_review import classify,project_screen,legacy_deviation,policy_identity
from candidate_expectations import expected_cli_output
ROOT=Path(__file__).resolve().parents[2]
class IdentityTests(unittest.TestCase):
 def setUp(self):
  self.ref=json.loads((ROOT/'spec/evidence/runs/TEST-SMOKE-001/result.json').read_text());self.cand=copy.deepcopy(self.ref)
  for name,screen in self.ref['snapshots'].items():self.cand['snapshots'][name]=project_screen(screen,status_rows=(21,))[0]
 def test_reviewed_not_raw(self):
  r=classify(self.ref,self.cand);self.assertTrue(r['accepted']);self.assertTrue(r['identity_reviewed']);self.assertFalse(r['raw_exact']);self.assertTrue(r['differences'])
 def test_old_brand_rejected_even_raw_equal(self):
  r=classify(self.ref,self.ref);self.assertTrue(r['raw_exact']);self.assertFalse(r['accepted'])
 def test_unknown_title_fails_closed(self):
  for title in ['  GNU nano 9.9  f.txt','  GNU nano 9.3  名.txt','  GNU nano 9.3 f.txt Strange']:
   a=copy.deepcopy(self.ref);a['snapshots']['start']['rows'][0]['text']=title.ljust(80);self.assertFalse(classify(a,a)['accepted'])
 def test_title_filename_and_state_changes_fail(self):
  for name in ['start','typed']:
   c=copy.deepcopy(self.cand);row=c['snapshots'][name]['rows'][0];row['text']=row['text'].replace('Buffer','Boffer').replace('Modified','Changed!');self.assertFalse(classify(self.ref,c)['accepted'])
 def test_unrelated_surfaces_fail(self):
  mutations=[lambda c:c['snapshots']['start']['cursor'].update(x=1),lambda c:c['snapshots']['start']['modes'].update(mouse_any=987),lambda c:c['snapshots']['start']['rows'][2].update(text='wrong'.ljust(80)),lambda c:c['snapshots']['start']['rows'][0].update(attrs=[]),lambda c:c.update(exit_status=42),lambda c:c.update(stderr='extra'),lambda c:c['inputs'][0].update(hex='00'),lambda c:c.update(fixture={'extra':{'type':'file','mode':'0o600','b64':'eA=='}})]
  for mutate in mutations:
   c=copy.deepcopy(self.cand);mutate(c);self.assertFalse(classify(self.ref,c)['accepted'])
 def test_report_verdicts_do_not_authorize(self):
  c=copy.deepcopy(self.ref);c.update(accepted=True,identity_reviewed=True,raw_exact=True);self.assertFalse(classify(self.ref,c)['accepted'])
 def test_known_legacy_residual_only(self):
  policy=json.loads((ROOT/'tests/naro/legacy-deviations.json').read_text())
  for tid,entry in policy['cases'].items():
   ref={'root_namespace':{'euid':0,'passwd_home':None,'HOME':None}};diffs=copy.deepcopy(entry['differences'])
   for difference in diffs:
    if difference['field'] in ('snapshot.start.row0.text','snapshot.opened.row0.text'):
     difference['candidate']=difference['candidate'].replace('NARO 0.1.1','NARO 0.1.2',1)
   self.assertEqual(legacy_deviation(tid,ref,{},diffs),entry['deviation_id'])
   if diffs!=entry['differences']:
    self.assertIsNone(legacy_deviation(tid,ref,{},entry['differences']))
   diffs.append({'field':'snapshot.extra.cursor','reference':0,'candidate':1});self.assertIsNone(legacy_deviation(tid,ref,{},diffs))
   diffs=copy.deepcopy(entry['differences']);diffs[0]['candidate']='unexpected';self.assertIsNone(legacy_deviation(tid,ref,{},diffs))
 def test_help_and_welcome(self):
  from identity_review import _help_rows,_help_caption,project_identity_rows,_message_row
  heading,title,pairs=_help_rows(80,'C');rows=[_help_caption(80,heading),*list(pairs)]
  expected,evidence=project_identity_rows(rows,80,allow_help=True)
  self.assertEqual(expected[0],'                               Main NARO help text                              ')
  self.assertIn(' The NARO editor is designed',expected[1]);self.assertTrue(evidence)
  rows=[' '*40,_message_row(40,'Welcome to nano.  For basic help, type Ctrl+G.')]
  expected,evidence=project_identity_rows(rows,40,status_rows=(1,));self.assertEqual(expected[1],'Welcome to NARO.  For basic help, type C')
 def test_bold_attributes_derived_from_expected_glyphs(self):
  from candidate_expectations import title_row
  old=title_row(80,'f.txt',label='GNU nano 9.3').ljust(80)
  screen={'rows':[{'text':old,'attrs':[{'start':0,'end':len(old.rstrip()),'attr':'bold=True'}]}]}
  expected,_=project_screen(screen,boldtext=True)
  self.assertEqual(expected['rows'][0]['attrs'],[{'start':0,'end':43,'attr':'bold=True'}])
 def test_app_width_preserves_physical_grid_tail(self):
  from candidate_expectations import title_row
  old=title_row(40,'New Buffer',label='GNU nano 9.3').ljust(40)
  screen={'rows':[{'text':old+'tail'.ljust(40),'attrs':[]}]}
  expected,_=project_screen(screen,app_width=40)
  self.assertEqual(expected['rows'][0]['text'],title_row(40,'New Buffer').ljust(40)+'tail'.ljust(40))
 def test_cli_f1_literal(self):
  with self.assertRaises(ValueError):expected_cli_output(' GNU nano, version 9.4\n')
  ref='Usage: nano [OPTIONS]\nSee the nanorc manual for configuring nano.\n';self.assertEqual(expected_cli_output(ref),'Usage: naro [OPTIONS]\nSee the nanorc manual for configuring NARO.\n')
 def test_policy_bound(self):self.assertEqual(len(policy_identity()['sha256']),64)

class TitleExtensionTests(unittest.TestCase):
 def setUp(self):
  from candidate_expectations import title_row,display_pad
  self.cases=json.loads((ROOT/'tests/follow-up/scenarios/environments.json').read_text())
  self.case=next(c for c in self.cases if c['id']=='TEST-NEXT-TERM-001-1')
  self.reference=self.run_record(display_pad(title_row(30,'f.txt','Modified','GNU nano 9.3'),30),tid=self.case['id'],snapshot='small',width=30,height=9)
  self.candidate=copy.deepcopy(self.reference);self.candidate['snapshots']['small']['rows'][0]['text']=display_pad(title_row(30,'f.txt','Modified'),30)
 def run_record(self,title,tid='TEST-TITLE-ORACLE',snapshot='s',width=80,height=24,language='C'):
  return {'reference_commit':'6ed285c3ec7a1d228def4d4e7021c6ba269f620c','scenario':tid,
   'argv':['nano','-I','f.txt'],'env':{'LANG':language},'fixture':{'work/f.txt':{'type':'file','mode':'0o644','b64':'eA=='}},
   'inputs':[],'exit_status':0,'steps_ok':True,'snapshots':{snapshot:{'rows':[{'text':title,'attrs':[{'start':0,'end':width,'attr':'reverse=True'}]}]+[{'text':' '*width,'attrs':[]}for _ in range(height-1)],'cursor':{'x':4,'y':1,'visible':True},'modes':{}}}}
 def test_c_reference_fit_boundaries(self):
  from candidate_expectations import title_row,display_pad
  # Literal expectations independently transcribed from pinned C titlebar.
  rows=[
   (28,'','       f.txt                ','       f.txt                '),
   (28,'Modified','       f.txt      Modified  ','       f.txt      Modified  '),
   (28,'View','  GNU nano 9.3 f.txt  View  ','  NARO 0.1.2  f.txt   View  '),
   (29,'','       f.txt                 ','  NARO 0.1.2 f.txt           '),
   (29,'Modified','       f.txt       Modified  ','  NARO 0.1.2 f.txt Modified  '),
   (29,'View','  GNU nano 9.3  f.txt  View  ','  NARO 0.1.2   f.txt   View  '),
   (30,'','        f.txt                 ','  NARO 0.1.2 f.txt            '),
   (30,'Modified','        f.txt       Modified  ','  NARO 0.1.2 f.txt  Modified  '),
   (30,'View','  GNU nano 9.3  f.txt   View  ','  NARO 0.1.2   f.txt    View  '),
   (31,'','  GNU nano 9.3 f.txt           ','  NARO 0.1.2  f.txt            '),
   (31,'Modified','  GNU nano 9.3 f.txt Modified  ','  NARO 0.1.2  f.txt  Modified  '),
   (31,'View','  GNU nano 9.3   f.txt   View  ','  NARO 0.1.2    f.txt    View  ')]
  for width,state,reference,candidate in rows:
   self.assertEqual(display_pad(title_row(width,'f.txt',state,'GNU nano 9.3'),width),reference)
   self.assertEqual(display_pad(title_row(width,'f.txt',state),width),candidate)
 def test_bound_narrow_context(self):
  result=classify(self.reference,self.candidate,case=self.case)
  self.assertTrue(result['accepted']);self.assertTrue(result['identity_reviewed']);self.assertFalse(result['raw_exact'])
  self.assertFalse(classify(self.reference,self.candidate)['accepted'])
  self.assertFalse(classify(self.reference,self.reference,case=self.case)['accepted'])
 def test_narrow_context_staleness_unknown_and_ambiguity(self):
  from unittest.mock import patch
  from identity_review import _title_context,_unique_projection
  case=copy.deepcopy(self.case);case['args'].append('--view')
  self.assertFalse(classify(self.reference,self.candidate,case=case)['accepted'])
  with patch('identity_review.policy_identity',return_value={'version':'0.1.3'}):
   with self.assertRaises(ValueError):_title_context(self.case,'small')
  reference=copy.deepcopy(self.reference);reference['snapshots']['small']['rows'][0]['text']='unknown'.ljust(30)
  self.assertFalse(classify(reference,self.candidate,case=self.case)['accepted'])
  with self.assertRaises(ValueError):_unique_projection(['one','two'])
  from candidate_expectations import title_row,display_pad
  reference=self.run_record(display_pad(title_row(80,'f.txt',label='GNU nano 9.3'),80),language='fr_FR.UTF-8')
  with patch('identity_review.candidate_title',side_effect=['a'*80,'b'*80]):
   self.assertFalse(classify(reference,reference)['accepted'])
 def test_unknown_context_schema_fails_closed(self):
  from unittest.mock import patch
  original=json.loads
  def altered(text,*args,**kwargs):
   value=original(text,*args,**kwargs)
   if isinstance(value,dict)and value.get('schema')=='naro-identity-title-context-v1':value['schema']='unknown-schema'
   return value
  with patch('identity_review.json.loads',side_effect=altered):
   self.assertFalse(classify(self.reference,self.candidate,case=self.case)['accepted'])
   self.assertFalse(classify(self.reference,self.reference,case=self.case)['accepted'])
 def test_narrow_non_identity_corruption_refused(self):
  mutations=[lambda c:c['snapshots']['small']['rows'][0].update(text=c['snapshots']['small']['rows'][0]['text'].replace('f.txt','g.txt')),
   lambda c:c['snapshots']['small']['rows'][0].update(text=c['snapshots']['small']['rows'][0]['text'].replace('Modified','Strange!')),
   lambda c:c['snapshots']['small']['rows'][0].update(text='  NARO 0.1.1 f.txt   Modified '),
   lambda c:c['snapshots']['small']['rows'][0].update(attrs=[]),lambda c:c['snapshots']['small']['cursor'].update(x=5),
   lambda c:c['snapshots']['small']['rows'][1].update(text='wrong'.ljust(30)),lambda c:c['fixture']['work/f.txt'].update(b64='eQ=='),
   lambda c:c['inputs'].append({'hex':'00'}),lambda c:c['snapshots']['small']['modes'].update(mouse_any=1)]
  for mutate in mutations:
   changed=copy.deepcopy(self.candidate);mutate(changed);self.assertFalse(classify(self.reference,changed,case=self.case)['accepted'])
 def test_wide_japanese_and_iso_states(self):
  from candidate_expectations import title_row,display_pad,display_width
  for language,state,column in [('ja_JP.UTF-8','変更済み',70),('de_DE.ISO-8859-1','Ver�ndert',69)]:
   old=display_pad(title_row(80,'f.txt',state,'GNU nano 9.3'),80);new=display_pad(title_row(80,'f.txt',state),80)
   self.assertEqual(display_width(old),80);self.assertEqual(display_width(old[:old.index(state)]),column)
   self.assertEqual(display_width(new[:new.index(state)]),column)
   reference=self.run_record(old,language=language);candidate=copy.deepcopy(reference);candidate['snapshots']['s']['rows'][0]['text']=new
   self.assertTrue(classify(reference,candidate)['accepted'])
   candidate['snapshots']['s']['rows'][0]['text']=new.replace(state,' '+state).removesuffix(' ')
   self.assertFalse(classify(reference,candidate)['accepted'])
   candidate['snapshots']['s']['rows'][0]['text']=new.replace(state,'unknown')
   self.assertFalse(classify(reference,candidate)['accepted'])
 def widened_pair(self,width=32):
  from candidate_expectations import display_pad,title_row
  pair=[copy.deepcopy(self.reference),copy.deepcopy(self.candidate)]
  for run,label in zip(pair,('GNU nano 9.3','NARO 0.1.2')):
   screen=run['snapshots']['small'];screen['width']=width;screen['height']=9
   screen['rows'][0]={'text':display_pad(title_row(width,'f.txt','Modified',label),width),'attrs':[{'start':0,'end':width,'attr':'reverse=True'}]}
   for row in screen['rows'][1:]:row['text']=row['text'].ljust(width)
  return pair
 def test_bound_geometry_before_branded_projection(self):
  from identity_review import _title_context,project_identity_rows
  context=_title_context(self.case,'small')
  expected,_=project_screen(self.reference['snapshots']['small'],title_context=context)
  self.assertEqual(expected,self.candidate['snapshots']['small'])
  expected_rows,_=project_identity_rows([r['text']for r in self.reference['snapshots']['small']['rows']],30,title_context=context)
  self.assertEqual(expected_rows[0],self.candidate['snapshots']['small']['rows'][0]['text'])
  reference,candidate=self.widened_pair()
  self.assertFalse(classify(reference,candidate,case=self.case)['accepted'])
  with self.assertRaises(ValueError):project_screen(reference['snapshots']['small'],title_context=context)
  with self.assertRaises(ValueError):project_identity_rows([r['text']for r in reference['snapshots']['small']['rows']],32,title_context=context)
 def test_bound_empty_rows_and_effective_width_shortcuts_refused(self):
  from identity_review import _title_context,project_identity_rows
  context=_title_context(self.case,'small');reference,candidate=copy.deepcopy(self.reference),copy.deepcopy(self.candidate)
  for run in(reference,candidate):run['snapshots']['small'].update(rows=[],width=30,height=9)
  result=classify(reference,candidate,case=self.case)
  self.assertTrue(result['raw_exact']);self.assertFalse(result['accepted'])
  with self.assertRaises(ValueError):project_screen(reference['snapshots']['small'],title_context=context)
  with self.assertRaises(ValueError):project_identity_rows([],30,title_context=context)
  reference,candidate=self.widened_pair()
  for run in(reference,candidate):run['env']['COLUMNS']='30'
  self.assertFalse(classify(reference,candidate,case=self.case)['accepted'])
  with self.assertRaises(ValueError):project_screen(reference['snapshots']['small'],app_width=30,title_context=context)
  with self.assertRaises(ValueError):project_screen(self.reference['snapshots']['small'],app_width=28,title_context=context)
 def test_bound_header_fields_and_height_metadata_refused(self):
  from candidate_expectations import display_pad,title_row
  reference,candidate=copy.deepcopy(self.reference),copy.deepcopy(self.candidate)
  for run,label in zip((reference,candidate),('GNU nano 9.3','NARO 0.1.2')):
   run['snapshots']['small']['rows'][0]['text']=display_pad(title_row(30,'f.txt','View',label),30)
  self.assertFalse(classify(reference,candidate,case=self.case)['accepted'])
  for height in (8,10,9.0):
   reference,candidate=copy.deepcopy(self.reference),copy.deepcopy(self.candidate)
   for run in(reference,candidate):run['snapshots']['small']['height']=height
   self.assertFalse(classify(reference,candidate,case=self.case)['accepted'])
 def test_french_request_c_fallback_and_real_french(self):
  from candidate_expectations import title_row,display_pad
  for reserved in (9,8):
   old=display_pad(title_row(80,'f.txt',label='GNU nano 9.3',reserved=reserved),80);new=display_pad(title_row(80,'f.txt',reserved=reserved),80)
   reference=self.run_record(old,language='en_US.UTF-8');reference['env']['LANGUAGE']='fr'
   candidate=copy.deepcopy(reference);candidate['snapshots']['s']['rows'][0]['text']=new
   self.assertTrue(classify(reference,candidate)['accepted'])
   candidate['snapshots']['s']['rows'][0]['text']=display_pad(title_row(80,'f.txt',reserved=17-reserved),80)
   self.assertFalse(classify(reference,candidate)['accepted'])
  old=display_pad(title_row(80,'f.txt','Modifié','GNU nano 9.3'),80);new=display_pad(title_row(80,'f.txt','Modifié'),80)
  reference=self.run_record(old,language='fr_FR.UTF-8');candidate=copy.deepcopy(reference);candidate['snapshots']['s']['rows'][0]['text']=new
  self.assertTrue(classify(reference,candidate)['accepted'])
 def test_display_cell_slicing_and_unsupported_unicode(self):
  from candidate_expectations import display_slice,display_width
  self.assertEqual(display_width('ab変更'),6);self.assertEqual(display_slice('ab変更  ',2,6),'変更')
  with self.assertRaises(ValueError):display_slice('ab変更',0,3)
  self.assertEqual(display_slice('ae\u0301b',0,2),'ae\u0301')
  self.assertEqual(display_slice('ae\u0301b',2),'b')
  for bad in ['  GNU nano 9.3                         名.txt','  GNU nano 9.3                         f.txt                         不明']:
   reference=self.run_record(bad.ljust(80));self.assertFalse(classify(reference,reference)['accepted'])

if __name__=='__main__':unittest.main()

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
   ref={'root_namespace':{'euid':0,'passwd_home':None,'HOME':None}};diffs=copy.deepcopy(entry['differences']);self.assertEqual(legacy_deviation(tid,ref,{},diffs),entry['deviation_id'])
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
if __name__=='__main__':unittest.main()

#!/usr/bin/env python3
"""Gate negatives and canonical frozen-launcher/collector layout integration."""
import copy, hashlib, json, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
import collect_closure as collector
from check_release_gate import verify_gate
from release_gate_evidence import (GATE_SCHEMA, classification_counts, policy_identity,
                                  corpus_cases, CORPUS_EXCLUSIONS, recording_problems, environment_case)
from candidate_expectations import case_sha256


def result(accepted=True,identity=True,declared=False,raw=False):
    return dict(raw_exact=raw,identity_reviewed=identity,declared_deviation=declared,accepted=accepted)


def counts(n,declared=0):
    return dict(recorded=n,raw_exact=0,identity_reviewed=n-declared,declared_deviations=declared,unexpected=0,accepted=n)


class GateEvidenceTests(unittest.TestCase):
    def test_seeded_history_probe_really_restores_position(self):
        from release_gate_evidence import corpus_coverage_problems
        observed = json.loads((collector.ROOT / 'spec/evidence/runs/TEST-FEAT-015/result.json').read_text())
        self.assertEqual(corpus_coverage_problems(observed, 'TEST-FEAT-015'), [])
        missed = copy.deepcopy(observed)
        missed['snapshots']['s0']['cursor'] = {'x': 0, 'y': 1, 'visible': True}
        self.assertTrue(corpus_coverage_problems(missed, 'TEST-FEAT-015'))
        wrong_line = copy.deepcopy(observed)
        wrong_line['snapshots']['s0']['rows'][11]['text'] = 'l11'.ljust(80)
        self.assertTrue(corpus_coverage_problems(wrong_line, 'TEST-FEAT-015'))

    def test_fixed_corpus_membership(self):
        cases=corpus_cases()
        self.assertEqual(len(cases),303);self.assertEqual(len(CORPUS_EXCLUSIONS),6)
        self.assertFalse(set(cases)&CORPUS_EXCLUSIONS)

    def test_portable_locale_adaptation_is_explicit_and_narrow(self):
        original={'id':'TEST-LOCALE','locpath':'/home/john/src/nano-locales','args':['f.txt'],'expect':{'exit_status':0}}
        expected=copy.deepcopy(original);expected['locpath']='/opt/nano-locales'
        self.assertEqual(environment_case(original,True),expected)
        self.assertEqual(environment_case(original),original)
        self.assertEqual(original['locpath'],'/home/john/src/nano-locales')

    def test_raw_exact_does_not_hide_failed_acceptance(self):
        c=classification_counts([result(False,False,False,True)])
        self.assertEqual(c['raw_exact'],1);self.assertEqual(c['unexpected'],1);self.assertEqual(c['accepted'],0)

    def test_recording_assertions_and_raw_bytes_reopened(self):
        with tempfile.TemporaryDirectory()as temp:
            folder=Path(temp);raw=b'terminal';(folder/'raw-output.bin').write_bytes(raw)
            case={'id':'TEST-GATE-REOPEN','steps':[{'wait_exit':5}],'expect':{'exit_status':0}}
            run={'scenario':case['id'],'reference_commit':collector.REF,'binary_sha256':'a'*64,
                 'scenario_sha256':case_sha256(case),'steps_ok':True,'step_checks':[{'step':0,'pass':True}],
                 'exit_status':0,'inputs':[],'checks':[{'name':'exit_status','pass':True,'detail':'got 0'}],
                 'cwd':'/tmp/private/fx/work','raw_output_sha256':hashlib.sha256(raw).hexdigest(),'raw_output_bytes':len(raw)}
            from nanoharness import Run
            runner=Run(case,'/unused','/unused');runner.root='/tmp/private/fx';run['checks']=runner.check(run)
            self.assertEqual(recording_problems(run,case,'reference','a'*64,folder),[])
            broken=copy.deepcopy(run);broken['exit_status']=1
            self.assertTrue(recording_problems(broken,case,'reference','a'*64,folder))
            broken=copy.deepcopy(run);broken['step_checks']=[]
            self.assertTrue(recording_problems(broken,case,'reference','a'*64,folder))
            (folder/'raw-output.bin').write_bytes(b'changed')
            self.assertTrue(recording_problems(run,case,'reference','a'*64,folder))

    def test_gate_recomputation_and_stale_schema(self):
        gate={'schema':GATE_SCHEMA,'identity_policy':policy_identity(),'inputs':{},'pass':True,'checks':[],'accounting':{'raw_exact':0}}
        with patch('check_release_gate.collect_evidence',return_value=copy.deepcopy(gate)):
            self.assertEqual(verify_gate(gate)[0],[])
            typed=copy.deepcopy(gate);typed['pass']=1
            self.assertTrue(verify_gate(typed)[0])
            forged=copy.deepcopy(gate);forged['accounting']['raw_exact']=301
            self.assertTrue(verify_gate(forged)[0])
        with patch('check_release_gate.collect_evidence',side_effect=FileNotFoundError('missing raw capture')):
            self.assertTrue(verify_gate(gate)[0])
        self.assertTrue(verify_gate({'schema':'naro-release-gate/v1'})[0])
        stale=copy.deepcopy(gate);stale['identity_policy']['sha256']='0'*64
        self.assertTrue(verify_gate(stale)[0])

    def test_follow_up_classification_recomputed_from_saved_captures(self):
        import release_gate_evidence as evidence
        from identity_review import classify, project_screen, summary_counts
        from nanoharness import Run
        with tempfile.TemporaryDirectory()as temp:
            root=Path(temp);directory=root/'run';directory.mkdir()
            case={'id':'TEST-GATE-PAIR','steps':[{'snapshot':'start'}],'expect':{'exit_status':0}}
            scenario=root/'tests/follow-up/scenarios/one.json';scenario.parent.mkdir(parents=True)
            scenario.write_text(json.dumps([case]))
            original=json.loads((collector.ROOT/'spec/evidence/runs/TEST-SMOKE-001/result.json').read_text())
            original['snapshots']={'start':original['snapshots']['start']}
            pair=[];digests={}
            for side in ['reference','candidate']:
                raw=side.encode();(directory/(side+'.bin')).write_bytes(raw)
                digest=hashlib.sha256(raw).hexdigest();digests[side]=digest
                run=copy.deepcopy(original)
                run.update(inputs=[],scenario=case['id'],binary_sha256=digest,scenario_sha256=case_sha256(case),steps_ok=True,step_checks=[{'step':0,'pass':True}])
                if side=='candidate':
                    run['snapshots']['start']=project_screen(run['snapshots']['start'],status_rows=(21,))[0]
                runner=Run(case,'/unused','/unused');runner.root='/tmp/private/fx'
                run['checks']=runner.check(run)
                folder=directory/side/case['id'];folder.mkdir(parents=True)
                trace=b'synthetic unit-test trace';(folder/'raw-output.bin').write_bytes(trace)
                run['raw_output_sha256']=hashlib.sha256(trace).hexdigest();run['raw_output_bytes']=len(trace)
                (folder/'result.json').write_text(json.dumps(run));pair.append(run)
                (directory/(side+'-scenarios.json')).write_text(json.dumps([case]))
            (directory/'scenarios.json').write_text(json.dumps([case]))
            classified=classify(*pair,case_id=case['id'],case=case)
            classified.update(match=classified['raw_exact'],reference_checks=True,candidate_checks=True)
            summary=summary_counts({case['id']:classified});summary['matches']=summary['raw_matches']
            report={'identity_policy':policy_identity(),'candidate_sha256':digests['candidate'],'reference_sha256':digests['reference'],'candidate_build':{'source_sha256':'source','features':''},'candidate_status':0,'reference_status':0,'results':{case['id']:classified},'summary':summary}
            (directory/'report.json').write_text(json.dumps(report))
            with patch.object(evidence,'ROOT',root):
                call=lambda:evidence.validate_follow_up(directory,'one',digests['candidate'],'source',digests['reference'])
                self.assertEqual(call()[2],[])
                for key,wrong in [('accepted',1),('identity_fields',[]),('classification','raw_exact'),('identity_policy','unreviewed'),('policy_sha256','0'*64)]:
                    forged=copy.deepcopy(report);forged['results'][case['id']][key]=wrong
                    (directory/'report.json').write_text(json.dumps(forged))
                    with self.subTest(field=key):self.assertTrue(call()[2])
                forged=copy.deepcopy(report);forged['summary']['matches']=999
                (directory/'report.json').write_text(json.dumps(forged));self.assertTrue(call()[2])
                (directory/'report.json').write_text(json.dumps(report))
                path=directory/'candidate'/case['id']/'result.json';broken=json.loads(path.read_text())
                broken['snapshots']['start']['cursor']['x']+=1;path.write_text(json.dumps(broken))
                self.assertTrue(call()[2])

    def test_frozen_launcher_layout_integration(self):
        with tempfile.TemporaryDirectory()as temp:
            root=Path(temp)
            inputs={name:root/name for name in ['host','ubuntu','vm_host','vm_ubuntu','transport','package','package_check']}
            def write(path,value):
                path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value))
            def binary(path,data):
                path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data);return hashlib.sha256(data).hexdigest()
            hd=binary(inputs['host']/'naro',b'host');ud=binary(inputs['ubuntu']/'naro',b'ubuntu')
            hr=binary(inputs['host']/'reference.bin',b'host nano');ur=binary(inputs['ubuntu']/'reference.bin',b'ubuntu nano')
            rr=binary(inputs['host']/'root-reference.bin',b'root nano')
            build={'source_sha256':'source','features':'','version':'0.1.1'}
            write(inputs['host']/'checkpoint.json',{'state':'complete','active':None,'binary_sha256':hd,'reference_sha256':hr,'root_reference_sha256':rr,'build':build,'verification_sha256':collector.verification_fingerprint(),'checks':{key:{'status':0}for key in collector.REQUIRED_HOST_STAGES}})
            write(inputs['package']/'build.json',{'binary_sha256':ud,'compiled_build':build,'reference_commit':collector.REF})
            (inputs['package']/'SHA256SUMS').write_text('checksums')
            (inputs['ubuntu']/'complete').write_text('completed')
            for stage in collector.REQUIRED_UBUNTU_STAGES:
                (inputs['ubuntu']/(stage+'.status')).write_text('0\n')
            write(inputs['ubuntu']/'runtime-inputs.json',{'verification_fingerprint':collector.verification_fingerprint(),'candidate_sha256':ud,'reference_sha256':ur,'source_fingerprint':'source'})
            historical=['tools','edges','environments','supplement','backup','fifo-eof','signal-SIGTERM','signal-SIGHUP','vt-ioctl']
            for label,digest in [('host',hd),('ubuntu',ud)]:
                base=inputs[label]
                write(base/('terminal'if label=='host'else'candidate')/'report.json',{})
                for suite in historical+list(collector.SUITES):write(base/suite/'report.json',{})
                write(base/'extras/report.json',{'candidate_sha256':digest,'cli':{str(i):{'pass':True}for i in range(38)},'regex':{'C':{'cases':162,'pass':True}},'safety':{str(i):{'pass':True}for i in range(2)}})
                write(base/'large/report.json',{'binary_sha256':digest,'results':{str(i):{'pass':True}for i in range(2)}})
                for i in range(3):write(base/'panic'/('TEST-'+str(i))/'result.json',{'binary_sha256':'hooks','steps_ok':True,'checks':[{'pass':True}]})
                write(base/'package-check/report.json',{'binary_sha256':digest,'checks':[{'pass':True}]*15})
            for suite in ['root','root-nohome-tilde']:write(inputs['host']/suite/'report.json',{})
            write(inputs['host']/'extensions/report.json',{'default':{'pass':True,'binary_sha256':hd},**{str(i):{'pass':True}for i in range(5)}})
            for name in ['vm_host','vm_ubuntu']:
                write(inputs[name]/'report.json',{});write(inputs[name]/'vm-provenance.json',{})
            write(inputs['transport']/'report.json',{'checks':{str(i):True for i in range(6)}})
            write(inputs['package_check']/'report.json',{'binary_sha256':ud,'checks':[{'pass':True}]*15})
            def follow(directory,suite,*args,**kwargs):
                n=len(json.loads((collector.ROOT/'tests/follow-up/scenarios'/(suite+'.json')).read_text()))
                return {},counts(n,1 if suite.startswith('signal-')or suite=='root-nohome-tilde'else 0),[]
            def regression(directory,suite,*args):
                report={'results':{str(i):result()for i in range(collector.SUITES[suite])}}
                write(directory/'report.json',report)
                return report,[]
            with patch.object(collector,'REFERENCE_SHA256',hr),patch.object(collector,'source_fingerprint',return_value='source'),patch.object(collector,'validate_corpus',return_value=({},dict(counts(303,2),excluded=6,files_matches=302),[])),patch.object(collector,'validate_follow_up',side_effect=follow),patch.object(collector,'validate_suite',side_effect=regression),patch.object(collector,'validate_console_evidence',return_value=({},counts(19),[])):
                gate=collector.collect_evidence(inputs)
                self.assertTrue(gate['pass'],gate['checks'])
                self.assertEqual(gate['schema'],GATE_SCHEMA)
                self.assertEqual(gate['accounting']['host-historical']['raw_exact'],0)
                self.assertEqual(gate['accounting']['host-historical']['identity_reviewed'],51)
                self.assertEqual(gate['accounting']['host-terminal']['raw_exact'],0)
                self.assertEqual(gate['ubuntu_stage_statuses'],{stage:'0'for stage in collector.REQUIRED_UBUNTU_STAGES})
                for stage in sorted(collector.REQUIRED_UBUNTU_STAGES):
                    receipt=inputs['ubuntu']/(stage+'.status');receipt.unlink()
                    with self.subTest(missing_stage=stage):
                        failed=collector.collect_evidence(inputs)
                        self.assertFalse(failed['pass'])
                        self.assertIsNone(failed['ubuntu_stage_statuses'][stage])
                    receipt.write_text('0\n')
                receipt=inputs['ubuntu']/'branding.status'
                for malformed in ['1','false','00','', '0\n1']:
                    receipt.write_text(malformed)
                    with self.subTest(status=malformed):
                        self.assertFalse(collector.collect_evidence(inputs)['pass'])
                receipt.write_text('0\n')
                checkpoint=inputs['host']/'checkpoint.json';saved=json.loads(checkpoint.read_text())
                missing=copy.deepcopy(saved);missing['checks'].pop('fmt');checkpoint.write_text(json.dumps(missing))
                self.assertFalse(collector.collect_evidence(inputs)['pass'])
                checkpoint.write_text(json.dumps(saved))
                (inputs['host']/'naro').unlink()
                with self.assertRaises(FileNotFoundError):collector.collect_evidence(inputs)

if __name__=='__main__':unittest.main()

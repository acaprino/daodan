"""Small development-only probe of evidence layout and compaction action semantics."""
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT / '.daodan/runs/2026-10-27-julia-usage-diagnostic'
OLD = ROOT / '.daodan/runs/2026-10-27-julia-criteria-ablation'
spec = importlib.util.spec_from_file_location('previous_experiment', ROOT/'evals/julia-criteria-ablation/experiment.py')
previous = importlib.util.module_from_spec(spec)
spec.loader.exec_module(previous)
read, sha, encoded = previous.read, previous.sha, previous.encoded
EXPECTED = {'N02':'drop_result','N05':'drop_call','N10':'drop_call','N25':'keep'}
CHOICES = {'drop_call':'Remove this call and its output. No unique information from this pair is needed beyond the protected context.',
           'drop_result':'Keep the call and the supplied prefix only. The prefix contains all unique information still needed.',
           'keep':'Keep the call and its complete output. Required unique information is absent from both the prefix and protected context.'}


def write(name, value, frozen=False):
    path=RUN/name
    path.parent.mkdir(parents=True,exist_ok=True)
    if frozen:
        with path.open('xb') as f: f.write(encoded(value))
    else:
        temp=path.with_suffix('.tmp');temp.write_bytes(encoded(value));temp.replace(path)


def prepare():
    previous.verify()
    source_cases={x['id']:x for x in read(OLD/'cases.json')}
    source_requests={x['id']:x for x in read(OLD/'input.json')}
    requests=[]; cases={}
    for case_id in EXPECTED:
        case=copy.deepcopy(source_cases[case_id])
        current=copy.deepcopy(source_requests[case_id+'-descriptive']['body'])
        enriched=copy.deepcopy(current)
        corrected=copy.deepcopy(case)
        # The only superseded case in this diagnostic points to S24 in its real newer output.
        if case_id=='N10':
            for message in corrected['messages']:
                for call in message['toolUses']:
                    if call['tool_use_id']=='recent-copy': call['input']={'capture':'inventory-S24'}
            for message in enriched['state']['history']:
                for call in message.get('tool_calls',[]):
                    if call['id']=='t2': call['input']=json.dumps({'capture':'inventory-S24'},separators=(',',':'))
        protected=[]
        for index,message in enumerate(corrected['messages']):
            for result in message.get('toolResults',[]):
                if result['tool_use_id']!='candidate':
                    assert index>=len(corrected['messages'])-6
                    protected.append({'id':'t2','text':result['text'],'isError':result.get('isError',False)})
        enriched['state']['retained_context']={
            'candidate_prefix':enriched['state']['candidate_results'][0]['result'][:300],
            'protected_tool_results':protected,
            'policy':'Protected results stay unchanged whatever action is selected for candidate t1. The supplied candidate prefix survives only when its call is kept.'}
        choice=copy.deepcopy(enriched)
        choice['questions']={'action':{'type':'choice',
            'instructions':'Choose the smallest amount of candidate t1 that must remain to complete the active task using the protected context and permitted recovery.',
            'criteria':CHOICES}}
        for variant,body,private in [('current',current,case),('evidence',enriched,corrected),('action_choice',choice,corrected)]:
            key=case_id+'-'+variant
            requests.append({'id':key,'case_id':case_id,'variant':variant,'body':body})
            cases[key]=private
    write('input.json',requests,True);write('cases.json',cases,True)
    old=read(OLD/'manifest.json')
    manifest={'model':old['model'],'revision':old['revision'],'checkpoint':old['checkpoint'],'python':old['python'],
              'configuration':dict(previous.CONFIG,max_length=2048),'expected_actions':EXPECTED,
              'prior_manifest_sha256':sha(OLD/'manifest.json'),'source_sha256':sha(Path(__file__)),
              'input_sha256':sha(RUN/'input.json'),'cases_sha256':sha(RUN/'cases.json'),
              'limits':{'seconds':180,'request_seconds':45,'rss_bytes':2*2**30},
              'maximum_questions':24,'measured_questions':20,'control_questions':4,
              'interpretation':'Four already-observed development cases. Shared state grows in evidence variant, including corrected recent input N10. Action variant uses one choice instead of two noul. Diagnostic only, no generalization or speed guarantee.'}
    write('manifest.json',manifest,True)
    print(json.dumps({'manifest_sha256':sha(RUN/'manifest.json'),'requests':12,'questions_including_controls':24}))


def verify():
    previous.verify()
    m=read(RUN/'manifest.json')
    assert sha(Path(__file__))==m['source_sha256']
    for name in ['input','cases']: assert sha(RUN/(name+'.json'))==m[name+'_sha256']
    assert sha(OLD/'manifest.json')==m['prior_manifest_sha256']
    return m


def worker():
    m=verify()
    os.environ.update(JULIA_CPU_THREADS='4',OMP_NUM_THREADS='4',MKL_NUM_THREADS='4',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',HF_HUB_DISABLE_TELEMETRY='1')
    sys.path.insert(0,m['checkpoint'])
    write('progress.json',{'phase':'loading','at':time.time()})
    import torch
    from julia import load_model
    torch.set_num_threads(4)
    started=time.perf_counter()
    engine=load_model(m['checkpoint'],device='cpu',**m['configuration'])
    write('runtime.json',{'load_seconds':time.perf_counter()-started,'device':str(engine.device),'torch':torch.__version__})
    state='I was charged twice for the same order.'
    question={'type':'choice','instructions':'Which team should handle this request?',
              'criteria':{'billing':'Billing and payment disputes','shipping':'Shipping and delivery','access':'Account access and login'}}
    row={'state':state,'question':question['instructions'],'options':list(question['criteria'].values()),'type':'choice'}
    write('progress.json',{'phase':'parity','at':time.time()})
    start=time.perf_counter();typed=engine.predict(state=state,questions={'team':question});cold=time.perf_counter()-start
    optimized=engine.logits([row])[0]
    engine.model.marker_only_head=False
    try: original=engine.logits([row])[0]
    finally: engine.model.marker_only_head=True
    start=time.perf_counter();repeated=engine.predict(state=state,questions={'team':question});warm=time.perf_counter()-start
    control={'source':'https://huggingface.co/SupersonicLabs/Julia-1#start-here','expected':'billing',
             'typed':typed,'optimized_logits':optimized,'original_logits':original,'repeated':repeated,
             'cold_seconds':cold,'warm_seconds':warm,'tokens':engine.encoding_info([row]),
             'passed':typed['answers']['team']['choice']=='billing' and repeated['answers']['team']['choice']=='billing'
                 and optimized.index(max(optimized))==0 and original.index(max(original))==0}
    write('positive-control.json',control,True)
    if not control['passed']: raise RuntimeError('Published-example positive control failed; stop before domain probes')
    attempted=4
    for request in read(RUN/'input.json'):
        body=request['body'];rows=[]
        for q in body['questions'].values():
            options=[q['criteria']['false'],q['criteria']['true']] if q['type']=='noul' else list(q['criteria'].values())
            rows.append({'state':encoded(body['state']).decode('utf-8'),'question':q['instructions'],'type':q['type'],'options':options})
        audit=engine.encoding_info(rows)
        engine.clear_cache()
        write('progress.json',{'phase':'inference','at':time.time(),'id':request['id']})
        attempted+=len(rows);assert attempted<=24
        write('ledger.json',{'attempted_questions':attempted,'current':request['id'],'complete':False})
        start=time.perf_counter();response=engine.predict(state=rows[0]['state'],questions=body['questions']);elapsed=time.perf_counter()-start
        write('records/'+request['id']+'.json',{'id':request['id'],'body_sha256':hashlib.sha256(encoded(body)).hexdigest(),
              'response':response,'audit':audit,'seconds':elapsed},True)
    write('ledger.json',{'attempted_questions':attempted,'records':12,'complete':True})
    write('progress.json',{'phase':'finished','at':time.time()})


def run():
    m=verify()
    import psutil
    write('start.json',{'at':time.time(),'manifest_sha256':sha(RUN/'manifest.json')},True)
    env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PYTHONUTF8='1',PYTHONIOENCODING='utf-8')
    started=time.monotonic();peak=0;reason=None
    with (RUN/'worker.log').open('x',encoding='utf-8') as log:
        process=subprocess.Popen([m['python'],'-B',str(Path(__file__).resolve()),'worker'],cwd=ROOT,env=env,
              stdout=log,stderr=subprocess.STDOUT,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        observed=psutil.Process(process.pid)
        while process.poll() is None:
            try:
                children=observed.children(recursive=True)
                rss=sum(p.memory_info().rss for p in [observed,*children] if p.is_running())+psutil.Process().memory_info().rss
                peak=max(peak,rss);progress=read(RUN/'progress.json') if (RUN/'progress.json').exists() else {}
                reason=previous.guard_reason(time.monotonic()-started,rss,progress.get('phase'),time.time()-progress.get('at',time.time()),m['limits'])
                if reason:
                    for p in reversed(children):
                        if p.is_running(): p.kill()
                    process.kill();break
            except psutil.NoSuchProcess: pass
            time.sleep(.1)
        code=process.wait(timeout=15)
    write('resources.json',{'exit_code':code,'guard':reason,'wall_seconds':time.monotonic()-started,'combined_peak_rss_bytes':peak,'sampling_seconds':.1})
    if code or reason: raise RuntimeError('Diagnostic incomplete; inspect evidence without automatic retry')
    analyze()


def analyze():
    verify();_,owner=previous.dependencies();cases=read(RUN/'cases.json');rows=[]
    for request in read(RUN/'input.json'):
        r=read(RUN/'records'/(request['id']+'.json'));case=cases[request['id']]
        assert r['body_sha256']==hashlib.sha256(encoded(request['body'])).hexdigest()
        response=r['response']
        if request['variant']=='action_choice':
            action=response['answers']['action']['choice']
            response={'answers':{'call_t1':{'noul':int(action!='drop_call')},'result_t1':{'noul':int(action=='keep')}}}
        scored=owner.score_case({'questions':case['questions'],'oracle':{**case['oracle'],'messages':case['messages'],'options':case['options']}},response)
        rows.append({'id':request['id'],'expected_action':EXPECTED[request['case_id']],'action':scored['action'],
                     'optimal_action':scored['action']==EXPECTED[request['case_id']],
                     'missing_facts':scored['missing_facts_raw'],'seconds':r['seconds'],
                     'tokens':[x['tokens'] for x in r['audit']],'invariants':scored['invariants']})
    write('results.json',{'rows':rows,'positive_control':read(RUN/'positive-control.json'),'resources':read(RUN/'resources.json'),'ledger':read(RUN/'ledger.json')})
    print(json.dumps(rows,indent=2))


if __name__=='__main__':
    {'prepare':prepare,'run':run,'worker':worker,'analyze':analyze}[sys.argv[1]]()

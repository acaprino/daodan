"""Named typed questions over the existing Julia scoring API."""
import math
from .data import validate_row


def predict_typed(engine, state, questions):
    if not isinstance(questions,dict) or not questions:
        raise ValueError('questions must be a nonempty mapping')
    rows=[];metadata=[]
    for qid,q in questions.items():
        if not isinstance(qid,str) or not qid or not isinstance(q,dict):
            raise ValueError('Questions require nonempty string IDs and question objects')
        kind=q.get('type');criteria=q.get('criteria')
        if kind=='choice':
            if not isinstance(criteria,dict) or any(not isinstance(k,str) or not k for k in criteria):
                raise ValueError('Choice criteria must map nonempty IDs to descriptions')
            keys=list(criteria);labels=list(criteria.values())
        elif kind=='score':
            if not isinstance(criteria,list):raise ValueError('Score requires an ordered rubric')
            labels=criteria;keys=[str(i) for i in range(len(labels))]
        elif kind=='noul':
            keys=['false','true']
            if criteria is None:
                labels=list(keys)
            else:
                if not isinstance(criteria,dict) or set(criteria)!=set(keys):
                    raise ValueError('Noul criteria must map false and true to descriptions')
                labels=[criteria[key] for key in keys]
        else:raise ValueError('Unsupported question type')
        row=dict(state=state,question=q.get('instructions'),type=kind,options=labels)
        validate_row(row,len(rows)+1)
        rows.append(row);metadata.append((qid,kind,keys))
    scores=engine.logits(rows)
    if len(scores)!=len(rows):raise ValueError('Model returned an incorrect answer count')
    answers={}
    for (qid,kind,keys),z in zip(metadata,scores):
        if len(z)!=len(keys) or not all(math.isfinite(x) for x in z):raise ValueError('Invalid model scores')
        maximum=max(z);p=[math.exp(x-maximum) for x in z];total=sum(p);p=[x/total for x in p]
        result=dict(type=kind,probabilities=dict(zip(keys,p)))
        if kind=='choice':result['choice']=keys[max(range(len(p)),key=p.__getitem__)]
        elif kind=='score':result['score']=sum(i*x for i,x in enumerate(p))
        else:result['noul']=p[1]
        if kind!='noul':result['max_probability']=max(p)
        answers[qid]=result
    return dict(answers=answers)

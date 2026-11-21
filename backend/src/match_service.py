from datetime import datetime,timezone
from sqlalchemy import select
from .models import *
from .common import *
from .fit_model import predict

MAX_ATTEMPTS=3
STALE_RUNNING_SECONDS=30
REPUSH_AFTER_SECONDS=5
COMPACT_KEYS=('algorithm','seed','label','features','probabilities','balanced_accuracy','confusion_matrix','classes','train_count','holdout_count','training_sha256','source_sha256','note')

def _now():return datetime.now(timezone.utc).isoformat()
def _age(value):
 """返回距今天数的秒数；缺失或损坏的时间视为很久以前，便于恢复中断任务。"""
 try:return (datetime.now(timezone.utc)-datetime.fromisoformat(value)).total_seconds()
 except (TypeError,ValueError):return 10**9
def _open(s):return [r for r in rows(s,GarmentRequest) if r.state=='open']
def _measured(s):return {m.garment_id for m in rows(s,Measurement)}
def _in_sale(s,g,now=None):
 now=now or s.get(Shop,1).now;a=s.get(Agreement,g.agreement_id)
 return bool(a) and a.state=='active' and time(now)<time(a.ends)
def _eligible(s,budget):
 measured=_measured(s);now=s.get(Shop,1).now
 return [g for g in rows(s,Garment) if g.state=='listed' and g.price_cents<=budget and g.id in measured and _in_sale(s,g,now)]
def _task_for(s,r,gid):
 return next((t for t in rows(s,MatchTask) if t.request_id==r.id and t.revision==r.revision and t.garment_id==gid),None)
def _candidate_for(s,r,gid):
 return next((x for x in rows(s,MatchCandidate) if x.request_id==r.id and x.revision==r.revision and x.garment_id==gid),None)

def _queue(s,r,g,ids):
 t=_task_for(s,r,g.id)
 if t is None:
  t=MatchTask(request_id=r.id,revision=r.revision,garment_id=g.id,state='queued',attempts=0,error='',created_at=s.get(Shop,1).now,queued_at=_now(),started_at='',pushed_at=None);s.add(t);s.flush()
 elif t.state!='queued':
  t.state='queued';t.attempts=0;t.error='';t.queued_at=_now();t.started_at='';t.pushed_at=None
 else:return
 ids.append(t.id)

def _enqueue_eligible(s,r,ids):
 for g in _eligible(s,r.budget_cents):_queue(s,r,g,ids)

def create(s,d):
 c=lock(s);get(s,FitProfile,d['profile_id'])
 r=GarmentRequest(profile_id=d['profile_id'],budget_cents=d['budget_cents'],state='open',revision=0,created_at=c.now);s.add(r);s.flush()
 ids=[];_enqueue_eligible(s,r,ids);return r,ids

def budget(s,id,d):
 lock(s);r=get(s,GarmentRequest,id)
 if r.state!='open':fail('求衣单已关闭，不能修改预算')
 if d['budget_cents']==r.budget_cents:return r,[]
 for t in rows(s,MatchTask):
  if t.request_id==r.id and t.revision==r.revision:t.state='stale';t.error='预算已更新，旧候选作废'
 for x in rows(s,MatchCandidate):
  if x.request_id==r.id:s.delete(x)
 r.revision+=1;r.budget_cents=d['budget_cents'];s.flush()
 ids=[];_enqueue_eligible(s,r,ids);return r,ids

def retry(s,id):
 lock(s);r=get(s,GarmentRequest,id)
 if r.state!='open':fail('求衣单已关闭，不能重试')
 ids=[]
 for t in rows(s,MatchTask):
  if t.request_id==r.id and t.revision==r.revision and t.state=='failed':
   t.state='queued';t.attempts=0;t.error='';t.queued_at=_now();t.started_at='';t.pushed_at=None;ids.append(t.id)
 return r,ids

def sync(s,g):
 """衣物状态变化后核对：在架且已实测则补任务，离架则撤候选。"""
 if g.state=='listed':
  if not any(m.garment_id==g.id for m in rows(s,Measurement)) or not _in_sale(s,g):return []
  ids=[]
  for r in _open(s):
   if g.price_cents<=r.budget_cents:_queue(s,r,g,ids)
  return ids
 for x in rows(s,MatchCandidate):
  if x.garment_id==g.id:s.delete(x)
 for t in rows(s,MatchTask):
  if t.garment_id==g.id and t.state in ('queued','running','done'):
   t.state='skipped';t.error='衣物已离架，候选作废'
 return []

def reconcile(s):
 """修复结构性问题：补建遗漏任务、恢复中断任务、撤销已不符合条件的候选。"""
 measured=_measured(s);garments=rows(s,Garment);now=_now();clock=s.get(Shop,1).now;ids=[]
 for r in _open(s):
  eligible={g.id:g for g in garments if g.state=='listed' and g.price_cents<=r.budget_cents and g.id in measured and _in_sale(s,g,clock)}
  for gid,g in eligible.items():
   t=_task_for(s,r,gid)
   if t is None:_queue(s,r,g,ids)
   elif t.state=='running':
    if _age(t.started_at)>=STALE_RUNNING_SECONDS:
     t.state='queued';t.queued_at=now;t.started_at='';ids.append(t.id)
   elif t.state=='failed':
    if t.attempts<MAX_ATTEMPTS:
     t.state='queued';t.error='';t.queued_at=now;t.started_at='';ids.append(t.id)
   elif t.state=='skipped':
    t.state='queued';t.error='';t.attempts=0;t.queued_at=now;t.started_at='';ids.append(t.id)
  for t in rows(s,MatchTask):
   if t.request_id==r.id and t.revision==r.revision and t.garment_id not in eligible and t.state in ('queued','running','done'):
    t.state='skipped';t.error='衣物已离架、超出预算或寄售期满，候选作废'
 for x in rows(s,MatchCandidate):
  r=next((r for r in _open(s) if r.id==x.request_id),None)
  g=next((g for g in garments if g.id==x.garment_id),None)
  if not r or x.revision!=r.revision or not g or g.state!='listed' or g.price_cents>r.budget_cents or not _in_sale(s,g,clock):s.delete(x)
 return ids

def recover_running(s):
 """worker 启动时调用：上一个进程遗留的运行中任务重新排队，保证中断后可续做。"""
 ids=[]
 for t in rows(s,MatchTask):
  if t.state=='running':t.state='queued';t.queued_at=_now();t.started_at='';ids.append(t.id)
 return ids

def claim(s,limit=8):
 tasks=s.scalars(select(MatchTask).where(MatchTask.state=='queued').order_by(MatchTask.id).with_for_update(skip_locked=True).limit(limit)).all()
 now=_now()
 for t in tasks:t.state='running';t.started_at=now
 s.flush();return [t.id for t in tasks]

def outbox(s):
 """需要通知 worker 的排队任务；只是唤醒提示，丢失由轮询补偿。"""
 now=_now();ids=[]
 for t in rows(s,MatchTask):
  if t.state!='queued':continue
  if t.pushed_at and _age(t.pushed_at)<REPUSH_AFTER_SECONDS:continue
  t.pushed_at=now;ids.append(t.id)
 return ids

def evaluate(s,id):
 t=s.get(MatchTask,id)
 if not t or t.state!='running':return
 r=get(s,GarmentRequest,t.request_id)
 if r.state!='open' or r.revision!=t.revision:
  t.state='stale';t.error='求衣单已改预算，本次结果作废';return
 g=s.get(Garment,t.garment_id)
 if not g or g.state!='listed':
  t.state='skipped';t.error='衣物已离架，本次结果作废';return
 if g.price_cents>r.budget_cents:
  t.state='skipped';t.error='超出当前预算，本次结果作废';return
 if not _in_sale(s,g):
  t.state='skipped';t.error='寄售期已满，本次结果作废';return
 m=next((x for x in rows(s,Measurement) if x.garment_id==g.id),None)
 if not m:t.state='skipped';t.error='衣物缺少实测，不能推荐';return
 p=get(s,FitProfile,r.profile_id)
 try:raw=predict(dump(m),dump(p))
 except Exception as e:
  t.attempts+=1;t.state='failed';t.error=str(e)[:500];return
 result={k:raw[k] for k in COMPACT_KEYS if k in raw}
 candidate=_candidate_for(s,r,g.id)
 if raw['label']=='合身':
  if candidate:candidate.label=raw['label'];candidate.result=result;candidate.created_at=s.get(Shop,1).now
  else:s.add(MatchCandidate(request_id=r.id,revision=r.revision,garment_id=g.id,label=raw['label'],result=result,created_at=s.get(Shop,1).now))
 elif candidate:s.delete(candidate)
 t.state='done';t.error=''

def detail(s,r):
 p=get(s,FitProfile,r.profile_id)
 tasks=[t for t in rows(s,MatchTask) if t.request_id==r.id and t.revision==r.revision]
 candidates=[x for x in rows(s,MatchCandidate) if x.request_id==r.id and x.revision==r.revision]
 garments={g.id:dump(g) for g in rows(s,Garment)}
 eligible={g.id for g in _eligible(s,r.budget_cents)}
 live={t.garment_id:t for t in tasks if t.garment_id in eligible}
 found=[]
 for x in candidates:
  g=garments.get(x.garment_id)
  if g and x.garment_id in eligible:found.append({'garment_id':x.garment_id,'label':x.label,'result':x.result,'created_at':x.created_at,'garment':g})
 searching=len(live)<len(eligible) or any(t.state not in ('done','failed') for t in live.values())
 checked=sum(1 for t in live.values() if t.state=='done')
 failed=sum(1 for t in live.values() if t.state=='failed')
 return {'id':r.id,'profile_id':r.profile_id,'profile':dump(p),'budget_cents':r.budget_cents,'state':r.state,'revision':r.revision,'created_at':r.created_at,'searching':searching,'checked':checked,'total':len(eligible),'failed':failed,'candidates':found,'can_retry':failed>0,'task_errors':[{'garment_id':t.garment_id,'state':t.state,'error':t.error} for t in live.values() if t.state in ('failed','skipped')]}

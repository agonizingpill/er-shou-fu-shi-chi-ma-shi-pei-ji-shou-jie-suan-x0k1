import os,time,pathlib,logging
import redis
from .database import Session
from .models import FitAssessment,MatchTask,Measurement,FitProfile
from .common import lock,rows,get,dump
from .fit_model import predict
from . import match_service as match
logging.basicConfig(level=logging.INFO)
QUEUES=['resale:fit','resale:match']
def client():return redis.from_url(os.environ['REDIS_URL'],decode_responses=True,socket_connect_timeout=1,socket_timeout=4)

def fit_item(raw):
 with Session() as s:
  lock(s);x=s.get(FitAssessment,int(raw))
  if not x or x.state!='queued':return
  try:
   m=next(m for m in rows(s,Measurement) if m.garment_id==x.garment_id);p=get(s,FitProfile,x.profile_id);x.result=predict(dump(m),dump(p));x.state='ready'
  except Exception as e:x.state='failed';x.error=str(e)[:500];logging.exception('fit failed')
  s.commit()

def match_work():
 with Session() as s:
  lock(s);ids=match.claim(s);s.commit()
 for i in ids:
  with Session() as s:
   lock(s)
   try:match.evaluate(s,i)
   except Exception:
    logging.exception('match failed');x=s.get(MatchTask,i)
    if x:x.state='failed';x.error='匹配计算异常，可重试'
   s.commit()

def maintain(q):
 with Session() as s:
  lock(s);ids=match.reconcile(s);s.commit()
 if ids:
  try:q.rpush('resale:match',*ids)
  except redis.RedisError:logging.warning('Redis interrupted while waking matches, polling will recover')

def recover():
 with Session() as s:
  lock(s);ids=match.recover_running(s);s.commit()
 if ids:logging.info('requeued %s interrupted match tasks',len(ids))

def main():
 q=client();recover();loop=0
 while True:
  pathlib.Path('/artifacts/resale-heartbeat').write_text(str(time.time()))
  try:item=q.blpop(QUEUES,timeout=2)
  except redis.RedisError:
   logging.warning('Redis interrupted, retrying');item=None;time.sleep(1)
  if item and item[0]=='resale:fit':fit_item(item[1])
  match_work()
  loop+=1
  if loop%5==0:maintain(q)
if __name__=='__main__':main()

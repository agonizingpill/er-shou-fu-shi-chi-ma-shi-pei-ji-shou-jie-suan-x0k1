from .models import *
from .common import *
def reserve(s,d):
 c=lock(s);g=garment(s,d['garment_id']);a=get(s,Agreement,g.agreement_id);get(s,FitProfile,d['profile_id'])
 if g.state!='listed':fail('衣物已留给他人或不可试穿')
 st,en=time(d['starts']),time(d['ends'])
 if st>=en or st<time(c.now) or en>time(a.ends):fail('预约时段无效或超出寄售期')
 if (en-st).total_seconds()>7200:fail('单次试衣最多两小时')
 for x in rows(s,Fitting):
  if x.state=='reserved' and x.slot==d['slot'] and st<time(x.ends) and en>time(x.starts):fail('试衣位时段已占用')
 d['starts']=st.isoformat();d['ends']=en.isoformat();x=Fitting(**d);s.add(x);g.state='held';s.flush();return x
def cancel(s,id):
 lock(s);x=get(s,Fitting,id);g=garment(s,x.garment_id)
 if x.state!='reserved':fail('只可取消未成交预约')
 x.state='cancelled';g.state='listed';return x

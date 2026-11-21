from .models import *
from .common import *
def consignor(s,d):
 lock(s);x=Consignor(**d);s.add(x);s.flush();return x
def agreement(s,d):
 c=lock(s);get(s,Consignor,d['consignor_id'])
 if time(d['ends'])<=time(c.now):fail('新寄售协议到期时间必须晚于当前时间')
 d['ends']=time(d['ends']).isoformat();x=Agreement(**d);s.add(x);s.flush();return x
def amend(s,id,d):
 lock(s);a=get(s,Agreement,id);ids={g.id for g in rows(s,Garment) if g.agreement_id==a.id}
 if any(x.garment_id in ids and x.state=='settled' for x in rows(s,Sale)):fail('已有结算账，不允许修改佣金')
 x=Amendment(agreement_id=id,old_bp=a.commission_bp,new_bp=d['commission_bp'],reason=d['reason']);s.add(x);a.commission_bp=d['commission_bp'];s.flush();return x
def intake(s,d):
 c=lock(s);a=get(s,Agreement,d['agreement_id'])
 if a.state!='active' or time(c.now)>=time(a.ends):fail('协议已结束，不接收新衣物')
 if d['price_cents']<a.floor_cents:fail('标价不得低于协议底价')
 x=Garment(**d);s.add(x);s.flush();return x

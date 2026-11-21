from .models import *
from .common import *
def payout(s,d):
 c=lock(s);sale=get(s,Sale,d['sale_id']);g=garment(s,sale.garment_id);a=get(s,Agreement,g.agreement_id)
 if sale.state!='completed':fail('只有未退货未结算成交可结算')
 if time(c.now)<=time(sale.return_deadline):fail('退货期未满，不得结算')
 if time(c.now)<time(a.ends):fail('寄售期未满，不得结算')
 x=Payout(sale_id=sale.id,consignor_id=a.consignor_id,amount_cents=sale.net_cents,reference=d['reference'],paid_at=c.now);s.add(x);sale.state='settled';s.flush();return x
def withdraw(s,id,d):
 c=lock(s);g=garment(s,id);a=get(s,Agreement,g.agreement_id)
 if time(c.now)<time(a.ends):fail('寄售期未满，不得期满撤回')
 if g.state not in ['unmeasured','listed','held']:fail('已售、待复检或已撤回衣物不可撤回')
 for f in rows(s,Fitting):
  if f.garment_id==g.id and f.state=='reserved':f.state='cancelled'
 x=Withdrawal(garment_id=g.id,reason=d['reason'],returned_at=c.now);s.add(x);g.state='withdrawn';s.flush();return x
def clock(s,d):
 c=lock(s);t=time(d['now'])
 if t<time(c.now):fail('演示时钟不能倒退')
 c.now=t.isoformat();return c

from .models import *
from .common import *
def request(s,d):
 c=lock(s);sale=get(s,Sale,d['sale_id']);g=garment(s,sale.garment_id)
 if sale.state!='completed' or g.state!='sold':fail('订单已退回或已结算，不可退货')
 if time(c.now)>time(sale.return_deadline):fail('已经超出七天退货期')
 x=Return(**d);s.add(x);g.state='inspection';sale.state='returned';s.flush();return x
def inspect(s,id,d):
 c=lock(s);x=get(s,Return,id);sale=get(s,Sale,x.sale_id);g=garment(s,sale.garment_id);a=get(s,Agreement,g.agreement_id)
 if x.state!='pending' or g.state!='inspection':fail('退货已经复检')
 if d['outcome']=='relist' and time(c.now)>=time(a.ends):fail('寄售期已满，不能重新上架')
 x.state='inspected';x.inspection=d['inspection'];x.outcome=d['outcome'];g.state='listed' if x.outcome=='relist' else 'withdrawn'
 if x.outcome=='retire':s.add(Withdrawal(garment_id=g.id,reason=d['inspection'],returned_at=c.now))
 return x

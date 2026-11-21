from datetime import timedelta
from .models import *
from .common import *
def sell(s,d):
 c=lock(s);f=get(s,Fitting,d['fitting_id']);g=garment(s,f.garment_id);a=get(s,Agreement,g.agreement_id)
 if f.state!='reserved' or g.state!='held':fail('预约不是当前有效留衣')
 if not time(f.starts)<=time(c.now)<=time(f.ends):fail('只能在预约试衣时间内成交')
 if d['price_cents']<a.floor_cents:fail('成交价低于寄售底价')
 commission=(d['price_cents']*a.commission_bp+5000)//10000
 x=Sale(fitting_id=f.id,garment_id=g.id,price_cents=d['price_cents'],commission_bp=a.commission_bp,commission_cents=commission,net_cents=d['price_cents']-commission,sold_at=c.now,return_deadline=(time(c.now)+timedelta(days=7)).isoformat());s.add(x);g.state='sold';f.state='completed';s.flush();return x

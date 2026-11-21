from fastapi import HTTPException
from sqlalchemy import select
from datetime import datetime
from .models import Shop,Garment,Audit

def fail(msg):raise HTTPException(409,msg)
def rows(s,c):return s.scalars(select(c).order_by(c.id)).all()
def get(s,c,id):
 x=s.get(c,id)
 if not x:raise HTTPException(404,'记录不存在')
 return x
def lock(s):return s.scalars(select(Shop).where(Shop.id==1).with_for_update().execution_options(populate_existing=True)).one()
def garment(s,id):
 x=s.scalars(select(Garment).where(Garment.id==id).with_for_update().execution_options(populate_existing=True)).first()
 if not x:raise HTTPException(404,'服饰不存在')
 return x
def time(v):
 try:return datetime.fromisoformat(v).replace(tzinfo=None)
 except ValueError:fail('请输入ISO时间')
def dump(x):return {c.name:getattr(x,c.name) for c in x.__table__.columns}
def audit(s,u,action,x):s.add(Audit(actor=u['email'],action=action,detail=str(dump(x))[:500]))

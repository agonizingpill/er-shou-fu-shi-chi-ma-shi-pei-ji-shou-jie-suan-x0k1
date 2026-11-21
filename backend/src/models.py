from sqlalchemy import Column,Integer,String,Float,ForeignKey,JSON,CheckConstraint
from .database import Base
class User(Base):
 __tablename__='users'
 id=Column(Integer,primary_key=True);email=Column(String(160),unique=True,nullable=False);password=Column(String(160),nullable=False);role=Column(String(20),nullable=False)
class Shop(Base):
 __tablename__='shop'
 id=Column(Integer,primary_key=True);now=Column(String(32),nullable=False)
class Consignor(Base):
 __tablename__='consignors'
 id=Column(Integer,primary_key=True);name=Column(String(80),unique=True,nullable=False);contact=Column(String(100),nullable=False)
class Agreement(Base):
 __tablename__='agreements'
 id=Column(Integer,primary_key=True);code=Column(String(40),unique=True,nullable=False);consignor_id=Column(Integer,ForeignKey('consignors.id'),nullable=False);floor_cents=Column(Integer,nullable=False);commission_bp=Column(Integer,nullable=False);ends=Column(String(32),nullable=False);state=Column(String(20),default='active',nullable=False)
 __table_args__=(CheckConstraint('floor_cents>0 AND commission_bp>=0 AND commission_bp<=5000'),)
class Amendment(Base):
 __tablename__='amendments'
 id=Column(Integer,primary_key=True);agreement_id=Column(Integer,ForeignKey('agreements.id'),nullable=False);old_bp=Column(Integer,nullable=False);new_bp=Column(Integer,nullable=False);reason=Column(String(500),nullable=False)
class Garment(Base):
 __tablename__='garments'
 id=Column(Integer,primary_key=True);agreement_id=Column(Integer,ForeignKey('agreements.id'),nullable=False);code=Column(String(40),unique=True,nullable=False);title=Column(String(100),nullable=False);condition=Column(String(300),nullable=False);price_cents=Column(Integer,nullable=False);state=Column(String(20),default='unmeasured',nullable=False)
class Measurement(Base):
 __tablename__='measurements'
 id=Column(Integer,primary_key=True);garment_id=Column(Integer,ForeignKey('garments.id'),unique=True,nullable=False);chest=Column(Float,nullable=False);shoulder=Column(Float,nullable=False);length=Column(Float,nullable=False);elasticity=Column(Float,nullable=False);cut=Column(Integer,nullable=False)
class FitProfile(Base):
 __tablename__='profiles'
 id=Column(Integer,primary_key=True);code=Column(String(40),unique=True,nullable=False);chest=Column(Float,nullable=False);shoulder=Column(Float,nullable=False)
class FitAssessment(Base):
 __tablename__='assessments'
 id=Column(Integer,primary_key=True);garment_id=Column(Integer,ForeignKey('garments.id'),nullable=False);profile_id=Column(Integer,ForeignKey('profiles.id'),nullable=False);state=Column(String(20),default='queued');result=Column(JSON,nullable=True);error=Column(String(500),default='')
class Fitting(Base):
 __tablename__='fittings'
 id=Column(Integer,primary_key=True);garment_id=Column(Integer,ForeignKey('garments.id'),nullable=False);profile_id=Column(Integer,ForeignKey('profiles.id'),nullable=False);slot=Column(Integer,nullable=False);starts=Column(String(32),nullable=False);ends=Column(String(32),nullable=False);state=Column(String(20),default='reserved',nullable=False)
class Sale(Base):
 __tablename__='sales'
 id=Column(Integer,primary_key=True);fitting_id=Column(Integer,ForeignKey('fittings.id'),unique=True,nullable=False);garment_id=Column(Integer,ForeignKey('garments.id'),nullable=False);price_cents=Column(Integer,nullable=False);commission_bp=Column(Integer,nullable=False);commission_cents=Column(Integer,nullable=False);net_cents=Column(Integer,nullable=False);sold_at=Column(String(32),nullable=False);return_deadline=Column(String(32),nullable=False);state=Column(String(20),default='completed',nullable=False)
class Return(Base):
 __tablename__='returns'
 id=Column(Integer,primary_key=True);sale_id=Column(Integer,ForeignKey('sales.id'),unique=True,nullable=False);reason=Column(String(500),nullable=False);state=Column(String(20),default='pending',nullable=False);inspection=Column(String(500),default='');outcome=Column(String(20),default='')
class Payout(Base):
 __tablename__='payouts'
 id=Column(Integer,primary_key=True);sale_id=Column(Integer,ForeignKey('sales.id'),unique=True,nullable=False);consignor_id=Column(Integer,ForeignKey('consignors.id'),nullable=False);amount_cents=Column(Integer,nullable=False);reference=Column(String(60),unique=True,nullable=False);paid_at=Column(String(32),nullable=False)
class Withdrawal(Base):
 __tablename__='withdrawals'
 id=Column(Integer,primary_key=True);garment_id=Column(Integer,ForeignKey('garments.id'),unique=True,nullable=False);reason=Column(String(500),nullable=False);returned_at=Column(String(32),nullable=False)
class Audit(Base):
 __tablename__='audit'
 id=Column(Integer,primary_key=True);actor=Column(String(160),nullable=False);action=Column(String(100),nullable=False);detail=Column(String(500),nullable=False)

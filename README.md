# 二手服饰尺码适配与寄售结算

合身衣橱有4位寄售顾问、2个试衣位。过去顾问用衣架纸签、软尺记录和微信分别处理寄售，容易把同件外套留给两位买家、在退货期内提前支付寄售款、退回衣物未经复检就放回衣架。本项目接收寄售人的协议与衣物，贯通实测适配、试衣留衣、成交退货、复检和期满结算，下游给寄售人可核对的取衣及支付凭据。演示数据均为模拟，不存真实买家姓名和联系信息。

## 启动与账号

```bash
cp .env.example .env
docker compose up -d --build --wait
```

访问前端 `http://localhost:18238`，API `http://localhost:19238/docs`，PostgreSQL `localhost:17738`。中文含空格目录已验收。Python3.12/FastAPI/SQLAlchemy、PostgreSQL16、Redis7、scikit-learn、原生HTML/CSS/JS ES modules、Nginx，恰好frontend/backend/worker/db/redis五容器全部健康检查。命名卷保存DB/Redis与心跳。`.env.example`提供项目名、端口、子网和JWT_SECRET；对外部署前更换演示凭据。

| 角色账号 | 权限与典型动作 |
|---|---|
| operator@hesheng.local | 顾问登记寄售人/协议/品相/实测/匿名体型/适配、预约取消、成交及七天退货 |
| supervisor@hesheng.local | 店长全部日常动作，另可修订佣金、复检、结算、期满撤回和推进演示时钟 |
| viewer@hesheng.local | 六页只读，后端独立拒绝所有写接口 |

统一演示口令 `Fit2026!`。

## 六个协作模块

1. **寄售与品相**：Consignor→Agreement→Garment。协议约定底价分值、佣金万分比和到期时间；衣物标价不得低于底价。佣金修订产生Amendment前后值与理由，已有settled销售时禁止再改。旧销售的佣金快照不随协议修改。
2. **实测与适配**：Measurement记录胸围、肩宽、衣长、弹性和版型；未实测不能推荐，实测后unmeasured→listed。FitProfile用匿名编号；FitAssessment经worker真实计算，queued→ready/failed，失败可重新提交新评估。
3. **预约与排他留衣**：Fitting约定买家、衣物、试衣位1/2和至多2小时时段。只有listed可约，预约使衣物held；一衣一客和同位时段不重叠，取消释放为listed。有效协议结束前才可安排。
4. **成交与佣金**：只有当前留衣在预约时间内成交，价格≥底价。Sale按当时佣金万分比四舍五入到分，保存成交、佣金、应付金额与七天退货截止，衣物sold，预约completed。
5. **退货与复检**：七天内未结算订单可退，Sale returned、衣物inspection；pending退货必须店长记检查结果，relist恢复listed，retire产生交还凭据。寄售期已满不可复上架。原已退销售不能结算。
6. **期满与结算**：成交七天退货期结束且寄售期届满才能Payout，保存支付参考号和应付金额，Sale settled。未售期满Withdrawal使衣物withdrawn并取消有效预约，保留取衣原因。两类资源写操作先锁Shop，再锁Garment，防止同衣或同试衣位并发争用。

## 一天的工作剧本

1. 11月18日09:00核对林禾的A031协议：底价180元、佣金20%、11月26日18:00截止。
2. 顾问查看G031烟苔绿短外套：胸围96、肩宽39、衣长58cm，价220元，完整品相留档。
3. 对匿名买家P031（胸88、肩37cm）运行适配，模型给出8cm/2cm余量与“合身”，安排真实试衣。
4. 留衣11月19日15:00–16:00试衣位1；他人再次留同件被拒绝，需取消原预约才释放。
5. 店长将明确显示的演示时钟推进至19日15:10；按220元成交，佣金44元，应付176元，11月26日15:10前可退。
6. 买家反馈肩部活动偏紧，七天内退回；外套隔离为待复检，不能直接预约或结算。
7. 店长检查领口、接缝、纽扣及尺寸，确认品相恢复上架；重新预约再成交，旧退货记录保留。
8. 退货期未满结算返回409；期限都结束后支付寄售人，保存PAY凭据。G033期满未售针织衫取回，系统留撤回回执。

Shop演示时钟从2026-11-18开始，仅店长可单向推进并留审计，便于重现试衣时间、七天退货和到期，不依赖机器日期。

## 真实机器学习

`fit_model.py`生成seed42的300条**模拟标注**样本，特征为胸围余量、肩宽余量、弹性、版型；三类合身/偏紧/偏松各100条。先分层留出25%（训练225/留出75），Pipeline仅在训练集拟合StandardScaler，再拟合KNeighborsClassifier(k=5, weights=distance)。输出本件与本人的特征、分类概率、balanced accuracy、混淆矩阵、训练/留出ID和训练/输入SHA256。验收balanced accuracy=1.0，只表示该合成分布可分，不代表真实体型或舒适度预测准确率，最终由试衣确认。

worker通过Redis BLPOP读取实际FitAssessment，结果持久化。Redis短暂断线会按连接/读超时捕获并重连，保持worker存活；入队不可用返回503并留下failed记录，恢复后可新提交评估。Redis真实stop/start验收后worker PID未变，新任务正常ready。

## 结构、枚举与开发

backend/src/models.py为寄售关系模型，schemas.py严格字段校验与非有限值拒绝；consignment_service、fit_service、fitting_service、sale_service、return_service、settlement_service分别封装六领域规则。routes.py做JWT权限，common.py做父锁/审计，fit_model/worker负责计算。middlewares.py有RequestTrace及Recovery。

frontend/src/pages六页独立业务任务，components/tailor.js含衣物吊牌、状态、标题/表单等共享组件，utils/api.js做请求/会话/store、utils/format.js做转义/数据类型。角色、服饰状态、适配类别枚举在backend/src/constants.py；前端角色/状态在frontend/src/constants.js，算法标签与展示文案对应。

```bash
docker compose exec -T backend python scripts/seed_demo.py
docker compose exec -T backend python scripts/seed_demo.py
docker compose logs worker
docker compose down -v --remove-orphans
```

seed自然键补缺，已有佣金修订、状态与结算/退货完整保留。本地开发可用Python3.12虚拟环境安装requirements并设置DATABASE_URL、REDIS_URL运行uvicorn；前端无需打包，经Nginx转发/api。测试脚本、真实截图与报告位于交付根test-artifacts/gb-1039，源码不放测试产物。

## 已知边界

单店两试衣位，匿名体型不含真实身份；合成样本不代表真实尺码适配质量。实测只录一次，未做历史测量修订。所有金额为整数分、仅同一模拟币种，无支付网关、退货退款外部调用或电子合同。需要显式取消过期留衣或期满撤回来释放，未做自动预约到时任务。Shop全店父锁优先小规模正确性，吞吐有限。BLPOP弹出任务后被强杀仍不自动重投，短暂Redis断线可恢复；没有生产迁移和多店隔离。

License: MIT（本项目新增源码）。

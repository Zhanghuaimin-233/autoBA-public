# autoBA 国服接口文档

> 自动生成自 867 组抓包双向明文（2026-10-11 ~ 10-13，测试号 10000000000）。
> 请求 Hash = (Protocol << 32) | N；N 为会话级全局计数，auth 起算 N=1。
> 请求/响应 key 均明文附在密文尾部（请求=b64-hex ASCII 形态，响应=原始二进制形态），IV 固定 JOSY。

## 目录

| 接口 | 中文 | Protocol |
|---|---|---|
| [/api/academy/attendschedule](#apiacademyattendschedule) | 学园日程·执行（地点+100经验，掉对应学校技术笔记） | 24001 |
| [/api/academy/getinfo](#apiacademygetinfo) | 学园日程信息 | 24000 |
| [/api/account/auth](#apiaccountauth) | 登录认证（Token 换会话） | 1002 |
| [/api/account/gettutorial](#apiaccountgettutorial) | 教程完成状态查询 | 1005 |
| [/api/account/loginsync](#apiaccountloginsync) | 登录同步（批量拉取变更） | 1017 |
| [/api/account/settutorial](#apiaccountsettutorial) | 教程完成状态上报 | 1006 |
| [/api/arena/cumulativetimereward](#apiarenacumulativetimereward) | 战术对抗赛·累计时数奖励 | 22008 |
| [/api/arena/dailyreward](#apiarenadailyreward) | 战术对抗赛·每日奖励领取 | 22009 |
| [/api/arena/enterbattle](#apiarenaenterbattle) | 战术对抗赛·开始战斗 | 22004 |
| [/api/arena/enterlobby](#apiarenaenterlobby) | 战术对抗赛·进入大厅 | 22000 |
| [/api/arena/opponentlist](#apiarenaopponentlist) | 战术对抗赛·对手列表 | 22003 |
| [/api/arena/syncechelonsettingtime](#apiarenasyncechelonsettingtime) | 战术对抗赛·同步防守编队 | 22016 |
| [/api/attendance/reward](#apiattendancereward) | 出勤奖励（签到） | 9002 |
| [/api/battlepass/check](#apibattlepasscheck) | 通行证·任务进度检查 | 51006 |
| [/api/battlepass/getinfo](#apibattlepassgetinfo) | 通行证·信息 | 51000 |
| [/api/battlepass/missionlist](#apibattlepassmissionlist) | 通行证·任务列表 | 51003 |
| [/api/battlepass/missionmultiplereward](#apibattlepassmissionmultiplereward) | 通行证·批量领取任务奖励 | 51005 |
| [/api/battlepass/receivereward](#apibattlepassreceivereward) | 通行证·领取等级奖励 | 51002 |
| [/api/billing/purchasefreeproduct](#apibillingpurchasefreeproduct) | 商城·免费商品领取 | 29003 |
| [/api/billing/purchaselistbyyostar](#apibillingpurchaselistbyyostar) | 商城·商品列表查询 | 29002 |
| [/api/cafe/ack](#apicafeack) | 咖啡厅·状态确认 | 20001 |
| [/api/cafe/interact](#apicafeinteract) | 咖啡厅·互动（摸头/送礼） | 20006 |
| [/api/cafe/receivecurrency](#apicafereceivecurrency) | 咖啡厅·领取体力和信用点 | 20013 |
| [/api/cafe/summoncharacter](#apicafesummoncharacter) | 咖啡厅·邀请学生入店 | 20015 |
| [/api/campaign/list](#apicampaignlist) | 关卡开放信息（活动副本列表） | 6000 |
| [/api/clan/chat/records](#apiclanchatrecords) | 社团·聊天记录 | 90009 |
| [/api/clan/check](#apiclancheck) | 社团·状态检查 | 28019 |
| [/api/clan/lobby](#apiclanlobby) | 社团·大厅 | 28000 |
| [/api/contentsave/get](#apicontentsaveget) | 云存档读取 | 26000 |
| [/api/contentsweep/multisweep](#apicontentsweepmultisweep) | 扫荡·多关卡批量扫荡 | 27001 |
| [/api/contentsweep/request](#apicontentsweeprequest) | 扫荡·执行 | 27000 |
| [/api/contentsweep/setmultisweeppreset](#apicontentsweepsetmultisweeppreset) | 扫荡·保存扫荡预设 | 27003 |
| [/api/craft/beginprocess](#apicraftbeginprocess) | 制造·开始制造 | 21003 |
| [/api/craft/list](#apicraftlist) | 制造·节点列表 | 21000 |
| [/api/craft/reward](#apicraftreward) | 制造·领取成品 | 21005 |
| [/api/craft/selectnode](#apicraftselectnode) | 制造·选择节点 | 21001 |
| [/api/craft/updatenodelevel](#apicraftupdatenodelevel) | 制造·节点升级 | 21002 |
| [/api/echelon/list](#apiechelonlist) | 编队·列表 | 5000 |
| [/api/echelon/save](#apiechelonsave) | 编队·保存 | 5001 |
| [/api/event/rewardincrease](#apieventrewardincrease) | 账号加成信息（掉落/经验加成，刷界面时高频） | 25003 |
| [/api/eventcontent/adventurelist](#apieventcontentadventurelist) | 活动·关卡列表 | 30000 |
| [/api/eventcontent/collectionlist](#apieventcontentcollectionlist) | 活动·收集进度 | 30025 |
| [/api/eventcontent/enterstorystage](#apieventcontententerstorystage) | 活动·进入剧情关 | 30036 |
| [/api/eventcontent/scenariogrouphistoryupdate](#apieventcontentscenariogrouphistoryupdate) | 活动·剧情历史更新 | 30027 |
| [/api/eventcontent/shopbuymerchandise](#apieventcontentshopbuymerchandise) | 活动·商店购买 | 30019 |
| [/api/eventcontent/shoplist](#apieventcontentshoplist) | 活动·商店列表 | 30014 |
| [/api/eventcontent/storystageresult](#apieventcontentstorystageresult) | 活动·剧情关结算 | 30037 |
| [/api/friend/check](#apifriendcheck) | 好友·状态检查 | 43010 |
| [/api/item/list](#apiitemlist) | 道具·列表 | 4000 |
| [/api/mail/check](#apimailcheck) | 邮件·未读检查 | 7001 |
| [/api/mail/list](#apimaillist) | 邮件·列表 | 7000 |
| [/api/mail/listsemipermanent](#apimaillistsemipermanent) | 邮件·永久邮箱列表 | 7003 |
| [/api/mail/receive](#apimailreceive) | 邮件·领取附件 | 7002 |
| [/api/management/data](#apimanagementdata) | 主界面数据（管理局汇总） | 90004 |
| [/api/minigame/missionlist](#apiminigamemissionlist) | 小游戏·任务列表 | 35003 |
| [/api/mission/guidemissionseasonlist](#apimissionguidemissionseasonlist) | 任务·引导任务赛季 | 8006 |
| [/api/mission/list](#apimissionlist) | 任务·列表 | 8000 |
| [/api/mission/multiplereward](#apimissionmultiplereward) | 任务·批量领取奖励 | 8002 |
| [/api/mission/reward](#apimissionreward) | 任务·领取奖励（单个） | 8001 |
| [/api/networktime/sync](#apinetworktimesync) | 服务器时间同步 | 3 |
| [/api/notification/eventcontentreddotcheck](#apinotificationeventcontentreddotcheck) | 红点检查（活动未读） | 36001 |
| [/api/opencondition/eventlist](#apiopenconditioneventlist) | 开放条件·活动列表 | 15002 |
| [/api/raid/createbattle](#apiraidcreatebattle) | 总力战·创建战斗 | 17004 |
| [/api/raid/endbattle](#apiraidendbattle) | 总力战·战斗结算 | 17007 |
| [/api/raid/enterbattle](#apiraidenterbattle) | 总力战·进入战斗 | 17005 |
| [/api/raid/lobby](#apiraidlobby) | 总力战·大厅 | 17014 |
| [/api/raid/opponentlist](#apiraidopponentlist) | 总力战·排名列表 (？) | 17016 |
| [/api/raid/rankingindex](#apiraidrankingindex) | 总力战·排名索引 | 17021 |
| [/api/raid/seasonreward](#apiraidseasonreward) | 总力战·赛季奖励 | 17013 |
| [/api/raid/sweep](#apiraidsweep) | 总力战·扫荡 | 17019 |
| [/api/scenario/skip](#apiscenarioskip) | 剧情·跳过 | 19003 |
| [/api/schooldungeon/list](#apischooldungeonlist) | 学院副本·列表 (？) | 38000 |
| [/api/shop/buyrefreshmerchandise](#apishopbuyrefreshmerchandise) | 商店·手动刷新商品 | 10007 |
| [/api/shop/list](#apishoplist) | 商店·列表（信用点/青辉石） | 10002 |
| [/api/toast/list](#apitoastlist) | 弹窗通知列表 | 16000 |
| [/api/weekdungeon/list](#apiweekdungeonlist) | 周常副本·列表（课程表）(？) | 23000 |

## 今日日常会话时间线（17:21 重登，127 请求）——你在游戏里干了啥

**登录批次 N=1~30**：登录认证 → 学园日程信息 → 登录同步 → 道具列表 → 时间同步 → 云存档 → 通行证信息 → 主界面数据 → 任务列表×3 → 通行证任务 → 红点/邮件/社团/好友检查 → 商城列表 → 永久邮箱

**之后你干的事（按首次调用）：**

- 邮件·列表（N=31）
- 邮件·领取附件（N=32）
- 账号加成信息（掉落/经验加成，刷界面时高频）（N=34）
- 通行证·任务进度检查（N=35）
- 红点检查（活动未读）（N=36）
- 邮件·未读检查（N=37）
- 社团·状态检查（N=39）
- 好友·状态检查（N=40）
- 主界面数据（管理局汇总）（N=41）
- 商店·列表（信用点/青辉石）（N=42）
- 咖啡厅·邀请学生入店（N=43）
- 咖啡厅·互动（摸头/送礼）（N=44）
- 制造·节点列表（N=56）
- 制造·领取成品（N=57）
- 制造·节点升级（N=59）
- 制造·选择节点（N=60）
- 制造·开始制造（N=65）
- 任务·批量领取奖励（N=75）
- 活动·关卡列表（N=85）
- 任务·列表（N=86）
- 活动·收集进度（N=87）
- 关卡开放信息（活动副本列表）（N=99）
- 扫荡·多关卡批量扫荡（N=101）
- 扫荡·保存扫荡预设（N=102）
- 扫荡·执行（N=116）
- 任务·领取奖励（单个）（N=127）

---

# academy

## /api/academy/attendschedule

- **中文**: 学园日程·执行（地点+100经验，掉对应学校技术笔记）
- **Protocol**: 24001　**混淆名**: `OUUT4DK7VK32GDTKX6IKZ5I4GQ`　**样本**: 21

### 请求业务字段

| 字段 | 类型 | 示例 |
|---|---|---|
| ZoneId | int | `16` |

### 响应 packet 顶层

- **AcademyDB**: object
- **BattlePassMissionProgressDBDict**: object
- **ExtraRewards**: array
- **MissionProgressDBs**: array
- **ParcelResultDB**: object
- **Protocol**: int
- **RequestId**: str
- **ServerNotification**: int
- **ServerTimeTicks**: int
- **SessionKey**: object

<details><summary>响应结构示例（限深 3 层）</summary>

```
- **AcademyDB**
  - **AccountId**: int = `10000000000`
  - **LastUpdate**: str = `"2026-10-11T18:25:41.763"`
  - **ZoneVisitCharacterDBs**: object
    - **1**: array
      - …(array len=0)
    - **10**: array
      - …(array len=3)
    - **100**: array
      - …(array len=2)
    - **101**: array
      - …(array len=3)
    - **102**: array
      - …(array len=1)
    - **103**: array
      - …(array len=3)
    - **104**: array
      - …(array len=1)
    - **105**: array
      - …(array len=1)
    - **106**: array
      - …(array len=2)
    - **107**: array
      - …(array len=2)
    - **11**: array
      - …(array len=3)
    - **110**: array
      - …(array len=2)
    - **111**: array
      - …(array len=1)
    - **112**: array
      - …(array len=3)
    - **113**: array
      - …(array len=3)
    - **114**: array
      - …(array len=1)
    - **115**: array
      - …(array len=2)
    - **116**: array
      - …(array len=2)
    - **117**: array
      - …(array len=2)
    - **12**: array
      - …(array len=1)
    - **13**: array
      - …(array len=2)
    - **14**: array
      - …(array len=1)
    - **15**: array
      - …(array len=2)
    - **16**: array
      - …(array len=2)
    - **20**: array
      - …(array len=2)
    - **21**: array
      - …(array len=3)
    - **22**: array
      - …(array len=3)
    - **23**: array
      - …(array len=1)
    - **24**: array
      - …(array len=2)
    - **25**: array
      - …(array len=3)
    - **26**: array
      - …(array len=3)
    - **30**: array
      - …(array len=1)
    - **31**: array
      - …(array len=1)
    - **32**: array
      - …(array len=2)
    - **33**: array
      - …(array len=3)
    - **34**: array
      - …(array len=2)
    - **35**: array
      - …(array len=2)
    - **36**: array
      - …(array len=2)
    - **37**: array
      - …(array len=2)
    - **40**: array
      - …(array len=3)
    - **41**: array
      - …(array len=2)
    - **42**: array
      - …(array len=3)
    - **43**: array
      - …(array len=2)
    - **44**: array
      - …(array len=1)
    - **45**: array
      - …(array len=2)
    - **46**: array
      - …(array len=2)
    - **47**: array
      - …(array len=2)
    - **50**: array
      - …(array len=3)
    - **51**: array
      - …(array len=2)
    - **52**: array
      - …(array len=2)
    - **53**: array
      - …(array len=1)
    - **54**: array
      - …(array len=2)
    - **55**: array
      - …(array len=2)
    - **56**: array
      - …(array len=3)
    - **57**: array
      - …(array len=1)
    - **60**: array
      - …(array len=3)
    - **61**: array
      - …(array len=2)
    - **62**: array
      - …(array len=3)
    - **63**: array
      - …(array len=2)
    - **64**: array
      - …(array len=2)
    - **65**: array
      - …(array len=2)
    - **66**: array
      - …(array len=1)
    - **67**: array
      - …(array len=1)
    - **70**: array
      - …(array len=3)
    - **71**: array
      - …(array len=3)
    - **72**: array
      - …(array len=2)
    - **73**: array
      - …(array len=2)
    - **74**: array
      - …(array len=3)
    - **75**: array
      - …(array len=2)
    - **76**: array
      - …(array len=1)
    - **77**: array
      - …(array len=1)
    - **80**: array
      - …(array len=3)
    - **81**: array
      - …(array len=1)
    - **82**: array
      - …(array len=1)
    - **83**: array
      - …(array len=2)
    - **84**: array
      - …(array len=3)
    - **85**: array
      - …(array len=1)
    - **86**: array
      - …(array len=2)
    - **87**: array
      - …(array len=1)
    - **90**: array
      - …(array len=1)
    - **91**: array
      - …(array len=2)
    - **92**: array
      - …(array len=2)
    - **93**: array
      - …(array len=2)
    - **94**: array
      - …(array len=2)
    - **95**: array
      - …(array len=2)
    - **96**: array
      - …(array len=2)
    - **97**: array
      - …(array len=3)
  - **ZoneScheduleGroupRecords**: object
    - **16**: array
      - …(array len=1)
    - **25**: array
      - …(array len=1)
- **BattlePassMissionProgressDBDict**
  - **1**: array
    - [0] (object):
      - …(5 keys)
    - …共 2 个元素
- **ExtraRewards**
  - [0] (object):
    - **Key**: object
      - …(2 keys)
    - **Amount**: int = `25`
- **MissionProgressDBs**
  - [0] (object):
    - **AccountServerId**: int = `10000000000`
    - **MissionUniqueId**: int = `1508`
    - **Category**: int = `1`
    - **Complete**: bool = `true`
    - **StartDate**: str = `"2026-10-11T18:25:41.208"`
    - **ProgressParameters**: object
      - …(1 keys)
- **ParcelResultDB**
  - **AccountDB**: object
    - **ServerId**: int = `10000000000`
    - **RoleId**: int = `10000000000`
    - **Nickname**: str = `"左搂邮箱右抱日奈"`
    - **CallName**: str = `"我要高炒了"`
    - **DevId**: str = `""`
    - **State**: int = `0`
    - **Level**: int = `90`
    - **Exp**: int = `0`
    - **Comment**: str = `""`
    - **LobbyMode**: int = `0`
    - **RepresentCharacterServerId**: int = `239093`
    - **MemoryLobbyUniqueId**: int = `0`
    - **LastConnectTime**: str = `"2026-10-11T18:25:41.208"`
    - **BirthDay**: str = `"2005-02-11T00:00:00"`
    - **CallNameUpdateTime**: str = `"0001-01-01T00:00:00"`
    - **PublisherAccountId**: int = `0`
    - **RetentionDays**: int = `0`
    - **VIPLevel**: int = `0`
    - **CreateDate**: str = `"2023-08-03T21:16:37.326"`
    - **UnReadMailCount**: int = `0`
    - **LinkRewardDateDate**: str = `"0001-01-01T00:00:00"`
    - **Location**: str = `""`
    - **LastReturningDate**: str = `"0001-01-01T00:00:00"`
  - **AcademyLocationDBs**: array
    - [0] (object):
      - …(4 keys)
  - **AccountCurrencyDB**: object
    - **AccountLevel**: int = `1`
    - **AcademyLocationRankSum**: int = `1`
    - **CurrencyDict**: object
      - …(29 keys)
    - **UpdateTimeDict**: object
      - …(19 keys)
  - **CharacterDBs**: array
    - [0] (object):
      - …(18 keys)
    - …共 2 个元素
  - **ItemDBs**: object
    - **11020768**: object
      - …(5 keys)
    - **26123768**: object
      - …(5 keys)
  - **DisplaySequence**: array
    - [0] (object):
      - …(2 keys)
    - …共 3 个元素
- **Protocol**
  - `24001`
- **RequestId**
  - `"8c671419-9b46-4977-892f-d136640fd0d3"`
- **ServerNotification**
  - `3`
- **ServerTimeTicks**
  - `639273401268418840`
- **SessionKey**
  - **AccountServerId**: int = `10000000000`
  - **MxToken**: str = `"AAAAAAAA…"`
```
</details>


## /api/academy/getinfo

- **中文**: 学园日程信息
- **Protocol**: 24000　**混淆名**: `KKVAEXLS5QIIB36RQW27XRTJGI`　**样本**: 8

请求无业务字段（仅标准头）。

### 响应 packet 顶层

- **AcademyDB**: null/object
- **AcademyLocationDBs**: array/null
- **Protocol**: int
- **RequestId**: str
- **ServerNotification**: int
- **ServerTimeTicks**: int
- **SessionKey**: object

<details><summary>响应结构示例（限深 3 层）</summary>

```
- **AcademyDB**
  - **AccountId**: int = `10000000000`
  - **LastUpdate**: str = `"2026-10-11T18:25:41.76339157"`
  - **ZoneVisitCharacterDBs**: object
    - **1**: array
      - …(array len=0)
    - **10**: array
      - …(array len=3)
    - **100**: array
      - …(array len=2)
    - **101**: array
      - …(array len=3)
    - **102**: array
      - …(array len=1)
    - **103**: array
      - …(array len=3)
    - **104**: array
      - …(array len=1)
    - **105**: array
      - …(array len=1)
    - **106**: array
      - …(array len=2)
    - **107**: array
      - …(array len=2)
    - **11**: array
      - …(array len=3)
    - **110**: array
      - …(array len=2)
    - **111**: array
      - …(array len=1)
    - **112**: array
      - …(array len=3)
    - **113**: array
      - …(array len=3)
    - **114**: array
      - …(array len=1)
    - **115**: array
      - …(array len=2)
    - **116**: array
      - …(array len=2)
    - **117**: array
      - …(array len=2)
    - **12**: array
      - …(array len=1)
    - **13**: array
      - …(array len=2)
    - **14**: array
      - …(array len=1)
    - **15**: array
      - …(array len=2)
    - **16**: array
      - …(array len=2)
    - **20**: array
      - …(array len=2)
    - **21**: array
      - …(array len=3)
    - **22**: array
      - …(array len=3)
    - **23**: array
      - …(array len=1)
    - **24**: array
      - …(array len=2)
    - **25**: array
      - …(array len=3)
    - **26**: array
      - …(array len=3)
    - **30**: array
      - …(array len=1)
    - **31**: array
      - …(array len=1)
    - **32**: array
      - …(array len=2)
    - **33**: array
      - …(array len=3)
    - **34**: array
      - …(array len=2)
    - **35**: array
      - …(array len=2)
    - **36**: array
      - …(array len=2)
    - **37**: array
      - …(array len=2)
    - **40**: array
      - …(array len=3)
    - **41**: array
      - …(array len=2)
    - **42**: array
      - …(array len=3)
    - **43**: array
      - …(array len=2)
    - **44**: array
      - …(array len=1)
    - **45**: array
      - …(array len=2)
    - **46**: array
      - …(array len=2)
    - **47**: array
      - …(array len=2)
    - **50**: array
      - …(array len=3)
    - **51**: array
      - …(array len=2)
    - **52**: array
      - …(array len=2)
    - **53**: array
      - …(array len=1)
    - **54**: array
      - …(array len=2)
    - **55**: array
      - …(array len=2)
    - **56**: array
      - …(array len=3)
    - **57**: array
      - …(array len=1)
    - **60**: array
      - …(array len=3)
    - **61**: array
      - …(array len=2)
    - **62**: array
      - …(array len=3)
    - **63**: array
      - …(array len=2)
    - **64**: array
      - …(array len=2)
    - **65**: array
      - …(array len=2)
    - **66**: array
      - …(array len=1)
    - **67**: array
      - …(array len=1)
    - **70**: array
      - …(array len=3)
    - **71**: array
      - …(array len=3)
    - **72**: array
      - …(array len=2)
    - **73**: array
      - …(array len=2)
    - **74**: array
      - …(array len=3)
    - **75**: array
      - …(array len=2)
    - **76**: array
      - …(array len=1)
    - **77**: array
      - …(array len=1)
    - **80**: array
      - …(array len=3)
    - **81**: array
      - …(array len=1)
    - **82**: array
      - …(array len=1)
    - **83**: array
      - …(array len=2)
    - **84**: array
      - …(array len=3)
    - **85**: array
      - …(array len=1)
    - **86**: array
      - …(array len=2)
    - **87**: array
      - …(array len=1)
    - **90**: array
      - …(array len=1)
    - **91**: array
      - …(array len=2)
    - **92**: array
      - …(array len=2)
    - **93**: array
      - …(array len=2)
    - **94**: array
      - …(array len=2)
    - **95**: array
      - …(array len=2)
    - **96**: array
      - …(array len=2)
    - **97**: array
      - …(array len=3)
  - **ZoneScheduleGroupRecords**: object
- **AcademyLocationDBs**
  - [0] (object):
    - **AccountId**: int = `10000000000`
    - **LocationId**: int = `1`
    - **Rank**: int = `12`
    - **Exp**: int = `0`
  - …共 11 个元素
- **Protocol**
  - `24000`
- **RequestId**
  - `"58920e46-30f1-4f45-8b9a-f6759f896341"`
- **ServerNotification**
  - `0`
- **ServerTimeTicks**
  - `639273399417794906`
- **SessionKey**
  - **AccountServerId**: int = `10000000000`
  - **MxToken**: str = `"AAAAAAAA…"`
```
</details>


# account

## /api/account/auth

- **中文**: 登录认证（Token 换会话）
- **Protocol**: 1002　**混淆名**: `AHTQLQI65FWJGGGK4KL5AEF57A`　**样本**: 5

### 请求业务字段

| 字段 | 类型 | 示例 |
|---|---|---|
| AccessIP | null | `null` |
| AdvertisementId | null | `null` |
| DevId | str | `"1011499471"` |
| DeviceModel | str | `"Xiaomi 24031PN0DC"` |
| DeviceSystemMemorySize | int | `8961` |
| DeviceUniqueId | str | `"d3ffbb0cf1cd97e4e6d5b7b0a7847406"` |
| IMEI | int | `0` |
| MarketId | null | `null` |
| OSVersion | str | `"Android OS 12 / API-32 (V417IR/1747)"` |
| ResUrl | str | `"https://static.bluearchive-cn.com/prodm39"` |
| SdkPid | str | `"CN-BA"` |
| SubChannel | str | `""` |
| Token | str | `"dededede…"` |
| UserType | null | `null` |
| Version | int | `0` |

### 响应 packet 顶层

- **AccountDB**: object
- **AccountLimitedFlashSaleDBs**: array
- **AccountRestrictionsDB**: object
- **AttendanceBookRewards**: array
- **AttendanceHistoryDBs**: array
- **BattleValidation**: bool
- **BiweeklyProductMail**: array
- **BiweeklyProductParcel**: array
- **CurrentVersion**: int
- **DailyRecordDBs**: array
- **EncryptedUID**: str
- **FunctionClose**: object
- **IsArenaAnonymous**: bool
- **IsDevelopment**: bool
- **IsNew**: bool
- **IssueAlertInfos**: array
- **MinimumVersion**: int
- **MissionProgressDBs**: array
- **MonthlyProductMail**: null
- **MonthlyProductParcel**: null
- **NewlyAddedShopCashIds**: array
- **OpenConditions**: null
- **OptionDB**: object
- **Protocol**: int
- **RepurchasableMonthlyProductCountDBs**: null
- **RequestId**: str
- **ServerNotification**: int
- **ServerTimeTicks**: int
- **SessionKey**: object
- **TTSCdnUri**: str
- **UpdateRequired**: bool
- **WeeklyProductMail**: array
- **WeeklyProductParcel**: array

<details><summary>响应结构示例（限深 3 层）</summary>

```
- **AccountDB**
  - **ServerId**: int = `10000000000`
  - **RoleId**: int = `10000000000`
  - **Nickname**: str = `"左搂邮箱右抱日奈"`
  - **CallName**: str = `"我要高炒了"`
  - **DevId**: str = `"1000000000"`
  - **State**: int = `1`
  - **Level**: int = `90`
  - **Exp**: int = `0`
  - **Comment**: str = `""`
  - **LobbyMode**: int = `0`
  - **RepresentCharacterServerId**: int = `239093`
  - **MemoryLobbyUniqueId**: int = `0`
  - **LastConnectTime**: str = `"2026-10-11T18:25:41.208420991"`
  - **BirthDay**: str = `"2005-02-11T00:00:00"`
  - **CallNameUpdateTime**: str = `"0001-01-01T00:00:00"`
  - **PublisherAccountId**: int = `0`
  - **RetentionDays**: int = `0`
  - **VIPLevel**: int = `0`
  - **CreateDate**: str = `"2023-08-03T21:16:37.325"`
  - **UnReadMailCount**: int = `0`
  - **LinkRewardDateDate**: str = `"0001-01-01T00:00:00"`
  - **Location**: str = `"广东省"`
  - **LastReturningDate**: str = `"0001-01-01T00:00:00"`
- **AccountLimitedFlashSaleDBs**
  - (空数组)
- **AccountRestrictionsDB**
  - **NicknameRestriction**: bool = `false`
  - **CommentRestriction**: bool = `false`
  - **CallnameRestriction**: bool = `false`
- **AttendanceBookRewards**
  - [0] (object):
    - **UniqueId**: int = `1`
    - **Type**: int = `0`
    - **TargetGroup**: int = `1`
    - **DisplayOrder**: int = `0`
    - **AccountLevelLimit**: int = `0`
    - **Title**: str = `"ATTENDANCEBOOK_NORMAL"`
    - **TitleImagePath**: str = `"Uis/01_Common/33_Attendance/ImageFont_Attend_1"`
    - **CountRule**: int = `0`
    - **CountReset**: int = `0`
    - **BookSize**: int = `10`
    - **StartDate**: str = `"2020-11-01T00:00:00"`
    - **StartableEndDate**: str = `"2099-12-31T04:00:00"`
    - **EndDate**: str = `"2099-12-31T04:00:00"`
    - **ExpiryDate**: int = `0`
    - **MailType**: int = `1`
    - **DailyRewardIcons**: object
      - …(0 keys)
    - **DailyRewards**: object
      - …(10 keys)
- **AttendanceHistoryDBs**
  - [0] (object):
    - **ServerId**: int = `0`
    - **AttendanceBookUniqueId**: int = `1`
    - **AttendedDay**: object
      - …(2 keys)
    - **Expired**: bool = `false`
  - …共 2 个元素
- **BattleValidation**
  - `false`
- **BiweeklyProductMail**
  - (空数组)
- **BiweeklyProductParcel**
  - (空数组)
- **CurrentVersion**
  - `1`
- **DailyRecordDBs**
  - (空数组)
- **EncryptedUID**
  - `""`
- **FunctionClose**
  - **Arena**: int = `0`
  - **CloseAutoBan**: int = `1`
  - **CloseAutoClearRaidRank**: int = `1`
  - **OpenGift**: int = `0`
  - **ProductPriceCheck**: int = `0`
  - **Raid**: int = `0`
  - **ShowCharacterCN**: int = `1`
  - **ShowCharacterChange**: int = `0`
- **IsArenaAnonymous**
  - `true`
- **IsDevelopment**
  - `false`
- **IsNew**
  - `false`
- **IssueAlertInfos**
  - (空数组)
- **MinimumVersion**
  - `1`
- **MissionProgressDBs**
  - [0] (object):
    - **AccountServerId**: int = `10000000000`
    - **MissionUniqueId**: int = `300012`
    - **Category**: int = `3`
    - **StartDate**: str = `"2026-08-07T20:06:18.834"`
    - **ProgressParameters**: object
      - …(1 keys)
- **MonthlyProductMail**
  - `null`
- **MonthlyProductParcel**
  - `null`
- **NewlyAddedShopCashIds**
  - (空数组)
- **OpenConditions**
  - `null`
- **OptionDB**
  - **ArenaIsAnonymous**: bool = `false`
  - **CafeAllowCopy**: int = `0`
  - **MainScenarioForceEnterSeriesId**: int = `0`
- **Protocol**
  - `1002`
- **RepurchasableMonthlyProductCountDBs**
  - `null`
- **RequestId**
  - `"e7a92fcd-7246-4472-8f5b-c18a8b498e68"`
- **ServerNotification**
  - `0`
- **ServerTimeTicks**
  - `639273399412415486`
- **SessionKey**
  - **AccountServerId**: int = `10000000000`
  - **MxToken**: str = `"AAAAAAAA…"`
- **TTSCdnUri**
  - `""`
- **UpdateRequired**
  - `true`
- **WeeklyProductMail**
  - (空数组)
- **WeeklyProductParcel**
  - (空数组)
```
</details>


## /api/account/gettutorial

- **中文**: 教程完成状态查询
- **Protocol**: 1005　**混淆名**: `TE4UJH3A6CSOJSPVNXXIBGYIIA`　**样本**: 5

请求无业务字段（仅标准头）。

### 响应 packet 顶层

- **Protocol**: int
- **RequestId**: str
- **ServerNotification**: int
- **ServerTimeTicks**: int
- **SessionKey**: object
- **TutorialIds**: array

<details><summary>响应结构示例（限深 3 层）</summary>

```
- **Protocol**
  - `1005`
- **RequestId**
  - `"3ce9bcc5-06f1-4c8b-97a0-456cef513272"`
- **ServerNotification**
  - `0`
- **ServerTimeTicks**
  - `639273399445029297`
- **SessionKey**
  - **AccountServerId**: int = `10000000000`
  - **MxToken**: str = `"AAAAAAAA…"`
- **TutorialIds**
  - [0] (int):
    - `1`
  - …共 28 个元素
```
</details>


## /api/account/loginsync

- **中文**: 登录同步（批量拉取变更）
- **Protocol**: 1017　**混淆名**: `P3OMQZD2FXV7XXEGA7ETCXIJ4Q`　**样本**: 5

### 请求业务字段

| 字段 | 类型 | 示例 |
|---|---|---|
| SkillCutInOption | str | `"OnceADay"` |
| SyncProtocols | array | `[20000, 1003, 2000, 3000, 5000, 12000, 6000, 22001, 17018, 2…` |

### 响应 packet 顶层

- **AccountCurrencySyncResponse**: object
- **AccountLevelRewardIds**: array
- **ArenaLoginResponse**: object
- **AttachmentEmblemListResponse**: object
- **AttachmentGetResponse**: object
- **BillingPurchaseListByYostarResponse**: object
- **CafeGetInfoResponse**: object
- **CampaignListResponse**: object
- **CharacterGearListResponse**: object
- **CharacterListResponse**: object
- **ClanLoginResponse**: object
- **ContentSweepMultiSweepPresetListResponse**: object
- **CraftInfoListResponse**: object
- **EchelonListResponse**: object
- **EliminateRaidLoginResponse**: object
- **EquipmentItemListResponse**: object
- **EventContentPermanentListResponse**: object
- **FriendCode**: str
- **FriendCount**: int
- **ItemListResponse**: null
- **MemoryLobbyListResponse**: object
- **MomoTalkOutLineResponse**: object
- **MultiFloorRaidLoginResponse**: object
- **MultiFloorRaidSyncResponse**: object
- **PickupFirstGetHistoryDBs**: array
- **Protocol**: int
- **RaidLoginResponse**: object
- **RequestId**: str
- **ScenarioListResponse**: object
- **ServerNotification**: int
- **ServerTimeTicks**: int
- **SessionKey**: object
- **ShopGachaRecruitListResponse**: object
- **StickerListResponse**: object
- **TimeAttackDungeonLoginResponse**: object

<details><summary>响应结构示例（限深 3 层）</summary>

```
- **AccountCurrencySyncResponse**
  - **Protocol**: int = `0`
  - **SessionKey**: object
    - **AccountServerId**: int = `0`
    - **MxToken**: str = `""`
  - **ServerTimeTicks**: int = `0`
  - **ServerNotification**: int = `0`
  - **RequestId**: str = `""`
  - **AccountCurrencyDB**: object
    - **AccountLevel**: int = `1`
    - **AcademyLocationRankSum**: int = `1`
    - **CurrencyDict**: object
      - …(29 keys)
    - **UpdateTimeDict**: object
      - …(19 keys)
  - **ExpiredCurrency**: object
- **AccountLevelRewardIds**
  - [0] (int):
    - `1`
  - …共 6 个元素
- **ArenaLoginResponse**
  - **Protocol**: int = `0`
  - **SessionKey**: object
    - **AccountServerId**: int = `0`
    - **MxToken**: str = `""`
  - **ServerTimeTicks**: int = `0`
  - **ServerNotification**: int = `0`
  - **RequestId**: str = `""`
  - **ArenaPlayerInfoDB**: object
    - **CurrentSeasonId**: int = `9`
    - **PlayerGroupId**: int = `85`
    - **CurrentRank**: int = `61`
    - **SeasonRecord**: int = `25`
    - **AllTimeRecord**: int = `13`
    - **CumulativeTimeReward**: int = `238950`
    - **TimeRewardLastUpdateTime**: str = `"2026-10-11T18:21:46.062"`
    - **BattleEnterActiveTime**: str = `"2026-10-10T20:44:13.779"`
    - **DailyRewardActiveTime**: str = `"2026-10-11T14:00:00"`
- **AttachmentEmblemListResponse**
  - **Protocol**: int = `0`
  - **SessionKey**: object
    - **AccountServerId**: int = `0`
    - **MxToken**: str = `""`
  - **ServerTimeTicks**: int = `0`
  - **ServerNotification**: int = `0`
  - **RequestId**: str = `""`
  - **EmblemDBs**: array
    - [0] (object):
      - …(3 keys)
    - …共 181 个元素
- **AttachmentGetResponse**
  - **Protocol**: int = `0`
  - **SessionKey**: object
    - **AccountServerId**: int = `0`
    - **MxToken**: str = `""`
  - **ServerTimeTicks**: int = `0`
  - **ServerNotification**: int = `0`
  - **RequestId**: str = `""`
  - **AccountAttachmentDB**: object
    - **AccountId**: int = `10000000000`
    - **EmblemUniqueId**: int = `1101080`
- **BillingPurchaseListByYostarResponse**
  - **Protocol**: int = `0`
  - **SessionKey**: object
    - **AccountServerId**: int = `0`
    - **MxToken**: str = `""`
  - **ServerTimeTicks**: int = `0`
  - **ServerNotification**: int = `0`
  - **RequestId**: str = `""`
  - **CountList**: array
    - [0] (object):
      - …(4 keys)
    - …共 2 个元素
  - **OrderList**: array
    - (空数组)
  - **MonthlyProductList**: array
    - (空数组)
- **CafeGetInfoResponse**
  - **Protocol**: int = `0`
  - **SessionKey**: object
    - **AccountServerId**: int = `0`
    - **MxToken**: str = `""`
  - **ServerTimeTicks**: int = `0`
  - **ServerNotification**: int = `0`
  - **RequestId**: str = `""`
  - **CafeDB**: null = `null`
  - **CafeDBs**: array
    - [0] (object):
      - …(11 keys)
    - …共 2 个元素
  - **FurnitureDBs**: array
    - [0] (object):
      - …(9 keys)
    - …共 510 个元素
- **CampaignListResponse**
  - **Protocol**: int = `0`
  - **SessionKey**: object
    - **AccountServerId**: int = `0`
    - **MxToken**: str = `""`
  - **ServerTimeTicks**: int = `0`
  - **ServerNotification**: int = `0`
  - **RequestId**: str = `""`
  - **CampaignChapterClearRewardHistoryDBs**: array
    - [0] (object):
      - …(4 keys)
    - …共 56 个元素
  - **StageHistoryDBs**: array
    - [0] (object):
      - …(13 keys)
    - …共 391 个元素
  - **StrategyObjecthistoryDBs**: array
    - [0] (object):
      - …(2 keys)
    - …共 57 个元素
  - **CurrentScenarioId**: int = `70007020`
- **CharacterGearListResponse**
  - **Protocol**: int = `0`
  - **SessionKey**: object
    - **AccountServerId**: int = `0`
    - **MxToken**: str = `""`
  - **ServerTimeTicks**: int = `0`
  - **ServerNotification**: int = `0`
  - **RequestId**: str = `""`
  - **GearDBs**: array
    - [0] (object):
      - …(8 keys)
    - …共 15 个元素
- **CharacterListResponse**
  - **Protocol**: int = `0`
  - **SessionKey**: object
    - **AccountServerId**: int = `0`
    - **MxToken**: str = `""`
  - **ServerTimeTicks**: int = `0`
  - **ServerNotification**: int = `0`
  - **RequestId**: str = `""`
  - **CharacterDBs**: array
    - [0] (object):
      - …(18 keys)
    - …共 174 个元素
  - **TSSCharacterDBs**: array
    - (空数组)
  - **WeaponDBs**: array
    - [0] (object):
      - …(7 keys)
    - …共 64 个元素
- **ClanLoginResponse**
  - **Protocol**: int = `0`
  - **SessionKey**: object
    - **AccountServerId**: int = `0`
    - **MxToken**: str = `""`
  - **ServerTimeTicks**: int = `0`
  - **ServerNotification**: int = `0`
  - **RequestId**: str = `""`
  - **AccountClanDB**: object
    - **ClanDBId**: int = `12828`
    - **ClanName**: str = `"阿拜多斯还债小组"`
    - **ClanChannelName**: str = `"channel_12828"`
    - **ClanPresidentNickName**: str = `"薯片"`
    - **ClanPresidentRepresentCharacterUniqueId**: int = `20007`
    - **ClanPresidentRepresentCharacterCostumeId**: int = `0`
    - **ClanNotice**: str = `"欢迎加入还债小组\n511674602\n进去后改名字才不会被踢"`
    - **ClanMemberCount**: int = `50`
    - **ClanManagerCount**: int = `0`
    - **ClanJoinOption**: int = `0`
  - **AccountClanMemberDB**: object
    - **AccountId**: int = `10000000000`
    - **AccountLevel**: int = `90`
    - **AccountNickName**: str = `"左搂邮箱右抱日奈"`
    - **RepresentCharacterUniqueId**: int = `13010`
    - **RepresentCharacterCostumeId**: int = `0`
    - **ClanDBId**: int = `12828`
    - **AttendanceCount**: int = `420`
    - **ClanSocialGrade**: int = `3`
    - **JoinDate**: str = `"2025-08-16T20:23:18.32"`
    - **SocialGradeUpdateTime**: str = `"0001-01-01T00:00:00"`
    - **LastLoginDate**: str = `"2026-10-10T23:30:10.1"`
    - **GameLoginDate**: str = `"2026-10-11T18:25:41.208"`
    - **AppliedDate**: str = `"2025-08-16T20:23:18.32"`
    - **AttachmentDB**: object
      - …(2 keys)
  - **ClanAssistSlotDBs**: array
    - [0] (object):
      - …(6 keys)
    - …共 12 个元素
- **ContentSweepMultiSweepPresetListResponse**
  - **Protocol**: int = `0`
  - **SessionKey**: object
    - **AccountServerId**: int = `0`
    - **MxToken**: str = `""`
  - **ServerTimeTicks**: int = `0`
  - **ServerNotification**: int = `0`
  - **RequestId**: str = `""`
  - **MultiSweepPresetDBs**: array
    - [0] (object):
      - …(4 keys)
    - …共 4 个元素
- **CraftInfoListResponse**
  - **Protocol**: int = `0`
  - **SessionKey**: object
    - **AccountServerId**: int = `0`
    - **MxToken**: str = `""`
  - **ServerTimeTicks**: int = `0`
  - **ServerNotification**: int = `0`
  - **RequestId**: str = `""`
  - **CraftInfos**: array
    - [0] (object):
      - …(5 keys)
  - **ShiftingCraftInfos**: array
    - (空数组)
  - **PresetSlotDBs**: array
    - (空数组)
- **EchelonListResponse**
  - **Protocol**: int = `0`
  - **SessionKey**: object
    - **AccountServerId**: int = `0`
    - **MxToken**: str = `""`
  - **ServerTimeTicks**: int = `0`
  - **ServerNotification**: int = `0`
  - **RequestId**: str = `""`
  - **EchelonDBs**: array
    - [0] (object):
      - …(11 keys)
    - …共 42 个元素
- **EliminateRaidLoginResponse**
  - **Protocol**: int = `0`
  - **SessionKey**: object
    - **AccountServerId**: int = `0`
    - **MxToken**: str = `""`
  - **ServerTimeTicks**: int = `0`
  - **ServerNotification**: int = `0`
  - **RequestId**: str = `""`
  - **SeasonType**: int = `2`
  - **CanReceiveRankingReward**: bool = `false`
  - **ReceiveLimitedRewardIds**: array
    - (空数组)
  - **SweepPointByRaidUniqueId**: object
    - **2052106**: int = `26071297`
    - **2052306**: int = `25939264`
    - **2052406**: int = `26079874`
  - **LastSettledRanking**: int = `25579`
  - **LastSettledTier**: int = `3`
- **EquipmentItemListResponse**
  - **Protocol**: int = `0`
  - **SessionKey**: object
    - **AccountServerId**: int = `0`
    - **MxToken**: str = `""`
  - **ServerTimeTicks**: int = `0`
  - **ServerNotification**: int = `0`
  - **RequestId**: str = `""`
  - **EquipmentDBs**: array
    - [0] (object):
      - …(6 keys)
    - …共 383 个元素
- **EventContentPermanentListResponse**
  - **Protocol**: int = `0`
  - **SessionKey**: object
    - **AccountServerId**: int = `0`
    - **MxToken**: str = `""`
  - **ServerTimeTicks**: int = `0`
  - **ServerNotification**: int = `0`
  - **RequestId**: str = `""`
  - **PermanentDBs**: array
    - [0] (object):
      - …(2 keys)
    - …共 21 个元素
- **FriendCode**
  - `"ylij48a"`
- **FriendCount**
  - `18`
- **ItemListResponse**
  - `null`
- **MemoryLobbyListResponse**
  - **Protocol**: int = `0`
  - **SessionKey**: object
    - **AccountServerId**: int = `0`
    - **MxToken**: str = `""`
  - **ServerTimeTicks**: int = `0`
  - **ServerNotification**: int = `0`
  - **RequestId**: str = `""`
  - **MemoryLobbyDBs**: array
    - [0] (object):
      - …(4 keys)
    - …共 52 个元素
- **MomoTalkOutLineResponse**
  - **Protocol**: int = `0`
  - **SessionKey**: object
    - **AccountServerId**: int = `0`
    - **MxToken**: str = `""`
  - **ServerTimeTicks**: int = `0`
  - **ServerNotification**: int = `0`
  - **RequestId**: str = `""`
  - **MomoTalkOutLineDBs**: array
    - [0] (object):
      - …(5 keys)
    - …共 60 个元素
  - **FavorScheduleRecords**: object
    - **10000**: array
      - …(array len=4)
    - **10003**: array
      - …(array len=6)
    - **10004**: array
      - …(array len=5)
    - **10005**: array
      - …(array len=6)
    - **10006**: array
      - …(array len=5)
    - **10010**: array
      - …(array len=6)
    - **10011**: array
      - …(array len=6)
    - **10012**: array
      - …(array len=4)
    - **10013**: array
      - …(array len=3)
    - **10014**: array
      - …(array len=4)
    - **10015**: array
      - …(array len=5)
    - **10016**: array
      - …(array len=4)
    - **10017**: array
      - …(array len=5)
    - **10018**: array
      - …(array len=5)
    - **10019**: array
      - …(array len=4)
    - **10020**: array
      - …(array len=4)
    - **10021**: array
      - …(array len=4)
    - **10022**: array
      - …(array len=3)
    - **10024**: array
      - …(array len=4)
    - **10025**: array
      - …(array len=4)
    - **10030**: array
      - …(array len=4)
    - **10032**: array
      - …(array len=3)
    - **10033**: array
      - …(array len=4)
    - **13000**: array
      - …(array len=6)
    - **13001**: array
      - …(array len=3)
    - **13003**: array
      - …(array len=5)
    - **13004**: array
      - …(array len=5)
    - **13005**: array
      - …(array len=5)
    - **13006**: array
      - …(array len=4)
    - **13008**: array
      - …(array len=6)
    - **13010**: array
      - …(array len=5)
    - **13011**: array
      - …(array len=4)
    - **13012**: array
      - …(array len=4)
    - **16000**: array
      - …(array len=5)
    - **16001**: array
      - …(array len=4)
    - **16002**: array
      - …(array len=3)
    - **16003**: array
      - …(array len=4)
    - **16004**: array
      - …(array len=1)
    - **16005**: array
      - …(array len=2)
    - **16008**: array
      - …(array len=4)
    - **20000**: array
      - …(array len=6)
    - **20001**: array
      - …(array len=6)
    - **20003**: array
      - …(array len=1)
    - **20005**: array
      - …(array len=4)
    - **20011**: array
      - …(array len=3)
    - **20012**: array
      - …(array len=4)
    - **23001**: array
      - …(array len=5)
    - **23002**: array
      - …(array len=2)
    - **23003**: array
      - …(array len=4)
    - **23004**: array
      - …(array len=5)
    - **23005**: array
      - …(array len=3)
    - **23008**: array
      - …(array len=4)
    - **26000**: array
      - …(array len=4)
    - **26001**: array
      - …(array len=4)
    - **26003**: array
      - …(array len=4)
    - **26004**: array
      - …(array len=4)
    - **26005**: array
      - …(array len=2)
- **MultiFloorRaidLoginResponse**
  - **Protocol**: int = `0`
  - **SessionKey**: object
    - **AccountServerId**: int = `0`
    - **MxToken**: str = `""`
  - **ServerTimeTicks**: int = `0`
  - **ServerNotification**: int = `0`
  - **RequestId**: str = `""`
  - **LastClearedDifficulty**: int = `24`
- **MultiFloorRaidSyncResponse**
  - **Protocol**: int = `0`
  - **SessionKey**: object
    - **AccountServerId**: int = `0`
    - **MxToken**: str = `""`
  - **ServerTimeTicks**: int = `0`
  - **ServerNotification**: int = `0`
  - **RequestId**: str = `""`
  - **MultiFloorRaidDBs**: null = `null`
- **PickupFirstGetHistoryDBs**
  - [0] (object):
    - **ShopRecruitId**: int = `5004170`
    - **LogDate**: str = `"2026-07-31T22:06:23.154"`
  - …共 4 个元素
- **Protocol**
  - `1017`
- **RaidLoginResponse**
  - **Protocol**: int = `0`
  - **SessionKey**: object
    - **AccountServerId**: int = `0`
    - **MxToken**: str = `""`
  - **ServerTimeTicks**: int = `0`
  - **ServerNotification**: int = `0`
  - **RequestId**: str = `""`
  - **SeasonType**: int = `1`
  - **CanReceiveRankingReward**: bool = `false`
  - **LastSettledRanking**: int = `29308`
  - **LastSettledTier**: int = `3`
- **RequestId**
  - `"84140b2c-037d-4588-934e-3ca782a352a2"`
- **ScenarioListResponse**
  - **Protocol**: int = `0`
  - **SessionKey**: object
    - **AccountServerId**: int = `0`
    - **MxToken**: str = `""`
  - **ServerTimeTicks**: int = `0`
  - **ServerNotification**: int = `0`
  - **RequestId**: str = `""`
  - **ScenarioHistoryDBs**: array
    - [0] (object):
      - …(3 keys)
    - …共 305 个元素
  - **ScenarioGroupHistoryDBs**: array
    - [0] (object):
      - …(7 keys)
    - …共 1094 个元素
  - **ScenarioCollectionDBs**: array
    - (空数组)
- **ServerNotification**
  - `0`
- **ServerTimeTicks**
  - `639273399422168861`
- **SessionKey**
  - **AccountServerId**: int = `10000000000`
  - **MxToken**: str = `"AAAAAAAA…"`
- **ShopGachaRecruitListResponse**
  - **Protocol**: int = `0`
  - **SessionKey**: object
    - **AccountServerId**: int = `0`
    - **MxToken**: str = `""`
  - **ServerTimeTicks**: int = `0`
  - **ServerNotification**: int = `0`
  - **RequestId**: str = `""`
  - **ShopRecruits**: array
    - [0] (object):
      - …(4 keys)
    - …共 513 个元素
  - **ShopFreeRecruitHistoryDBs**: array
    - [0] (object):
      - …(3 keys)
- **StickerListResponse**
  - **Protocol**: int = `0`
  - **SessionKey**: object
    - **AccountServerId**: int = `0`
    - **MxToken**: str = `""`
  - **ServerTimeTicks**: int = `0`
  - **ServerNotification**: int = `0`
  - **RequestId**: str = `""`
  - **StickerBookDB**: object
    - **AccountId**: int = `10000000000`
    - **UnusedStickerDBs**: array
      - …(array len=20)
    - **UsedStickerDBs**: array
      - …(array len=3)
- **TimeAttackDungeonLoginResponse**
  - **Protocol**: int = `0`
  - **SessionKey**: object
    - **AccountServerId**: int = `0`
    - **MxToken**: str = `""`
  - **ServerTimeTicks**: int = `0`
  - **ServerNotification**: int = `0`
  - **RequestId**: str = `""`
  - **PreviousRoomDB**: null = `null`
```
</details>


## /api/account/settutorial

- **中文**: 教程完成状态上报
- **Protocol**: 1006　**混淆名**: `3KUKWHN3VDLAXVS4YDYBTTVZ2Y`　**样本**: 1

### 请求业务字段

| 字段 | 类型 | 示例 |
|---|---|---|
| TutorialIds | array | `[1, 2, 3, 4, 5, 22, 8]` |

### 响应 packet 顶层

- **Protocol**: int
- **RequestId**: str
- **ServerNotification**: int
- **ServerTimeTicks**: int
- **SessionKey**: object

<details><summary>响应结构示例（限深 3 层）</summary>

```
- **Protocol**
  - `1006`
- **RequestId**
  - `"6d9a4f23-1ded-4ecc-9e75-557fb8eac144"`
- **ServerNotification**
  - `0`
- **ServerTimeTicks**
  - `639273398756100528`
- **SessionKey**
  - **AccountServerId**: int = `10016071938`
  - **MxToken**: str = `"wc4dt5o4…"`
```
</details>


# arena

## /api/arena/cumulativetimereward

- **中文**: 战术对抗赛·累计时数奖励
- **Protocol**: 22008　**混淆名**: `5N7BAP2FPLZHH7VN5BZYRBXPWQ`　**样本**: 1

请求无业务字段（仅标准头）。

### 响应 packet 顶层

- **MissionProgressDBs**: array
- **ParcelResult**: object
- **Protocol**: int
- **RequestId**: str
- **ServerNotification**: int
- **ServerTimeTicks**: int
- **SessionKey**: object
- **TimeRewardAmount**: int
- **TimeRewardLastUpdateTime**: str

<details><summary>响应结构示例（限深 3 层）</summary>

```
- **MissionProgressDBs**
  - [0] (object):
    - **AccountServerId**: int = `10000000000`
    - **MissionUniqueId**: int = `82029`
    - **Category**: int = `3`
    - **StartDate**: str = `"2026-04-09T20:22:43.391"`
    - **ProgressParameters**: object
      - …(1 keys)
- **ParcelResult**
  - **AccountDB**: object
    - **ServerId**: int = `10000000000`
    - **RoleId**: int = `10000000000`
    - **Nickname**: str = `"左搂邮箱右抱日奈"`
    - **CallName**: str = `"我要高炒了"`
    - **DevId**: str = `""`
    - **State**: int = `0`
    - **Level**: int = `90`
    - **Exp**: int = `0`
    - **Comment**: str = `""`
    - **LobbyMode**: int = `0`
    - **RepresentCharacterServerId**: int = `239093`
    - **MemoryLobbyUniqueId**: int = `0`
    - **LastConnectTime**: str = `"2026-10-11T18:25:41.208"`
    - **BirthDay**: str = `"2005-02-11T00:00:00"`
    - **CallNameUpdateTime**: str = `"0001-01-01T00:00:00"`
    - **PublisherAccountId**: int = `0`
    - **RetentionDays**: int = `0`
    - **VIPLevel**: int = `0`
    - **CreateDate**: str = `"2023-08-03T21:16:37.326"`
    - **UnReadMailCount**: int = `0`
    - **LinkRewardDateDate**: str = `"0001-01-01T00:00:00"`
    - **Location**: str = `""`
    - **LastReturningDate**: str = `"0001-01-01T00:00:00"`
  - **AccountCurrencyDB**: object
    - **AccountLevel**: int = `1`
    - **AcademyLocationRankSum**: int = `1`
    - **CurrencyDict**: object
      - …(29 keys)
    - **UpdateTimeDict**: object
      - …(19 keys)
  - **DisplaySequence**: array
    - [0] (object):
      - …(2 keys)
- **Protocol**
  - `22008`
- **RequestId**
  - `"87458eff-a1eb-4ce3-a2c2-1f64aa6a7846"`
- **ServerNotification**
  - `0`
- **ServerTimeTicks**
  - `639273400658318638`
- **SessionKey**
  - **AccountServerId**: int = `10000000000`
  - **MxToken**: str = `"AAAAAAAA…"`
- **TimeRewardAmount**
  - `0`
- **TimeRewardLastUpdateTime**
  - `"2026-10-11T18:27:45.818117353"`
```
</details>


## /api/arena/dailyreward

- **中文**: 战术对抗赛·每日奖励领取
- **Protocol**: 22009　**混淆名**: `UGNFRQJ3JRBLNH67INDEVWKU7Y`　**样本**: 3

请求无业务字段（仅标准头）。

### 响应 packet 顶层

- **DailyRewardActiveTime**: str
- **ParcelResult**: object
- **Protocol**: int
- **RequestId**: str
- **ServerNotification**: int
- **ServerTimeTicks**: int
- **SessionKey**: object

<details><summary>响应结构示例（限深 3 层）</summary>

```
- **DailyRewardActiveTime**
  - `"2026-10-13T14:00:00"`
- **ParcelResult**
  - **AccountDB**: object
    - **ServerId**: int = `10000000000`
    - **RoleId**: int = `10000000000`
    - **Nickname**: str = `"左搂邮箱右抱日奈"`
    - **CallName**: str = `"我要高炒了"`
    - **DevId**: str = `""`
    - **State**: int = `0`
    - **Level**: int = `90`
    - **Exp**: int = `0`
    - **Comment**: str = `""`
    - **LobbyMode**: int = `0`
    - **RepresentCharacterServerId**: int = `239093`
    - **MemoryLobbyUniqueId**: int = `0`
    - **LastConnectTime**: str = `"2026-10-12T20:41:00.044"`
    - **BirthDay**: str = `"2005-02-11T00:00:00"`
    - **CallNameUpdateTime**: str = `"0001-01-01T00:00:00"`
    - **PublisherAccountId**: int = `0`
    - **RetentionDays**: int = `0`
    - **VIPLevel**: int = `0`
    - **CreateDate**: str = `"2023-08-03T21:16:37.326"`
    - **UnReadMailCount**: int = `0`
    - **LinkRewardDateDate**: str = `"0001-01-01T00:00:00"`
    - **Location**: str = `""`
    - **LastReturningDate**: str = `"0001-01-01T00:00:00"`
  - **AccountCurrencyDB**: object
    - **AccountLevel**: int = `1`
    - **AcademyLocationRankSum**: int = `1`
    - **CurrencyDict**: object
      - …(29 keys)
    - **UpdateTimeDict**: object
      - …(19 keys)
  - **ItemDBs**: object
    - **1443971**: object
      - …(5 keys)
  - **DisplaySequence**: array
    - [0] (object):
      - …(2 keys)
    - …共 2 个元素
- **Protocol**
  - `22009`
- **RequestId**
  - `"da562816-5d50-471c-93ad-e0fcf11bde2c"`
- **ServerNotification**
  - `0`
- **ServerTimeTicks**
  - `639274353083225705`
- **SessionKey**
  - **AccountServerId**: int = `10000000000`
  - **MxToken**: str = `"AAAAAAAA…"`
```
</details>


## /api/arena/enterbattle

- **中文**: 战术对抗赛·开始战斗
- **Protocol**: 22004　**混淆名**: `NWNNGWMRJC2VPSFJD5RJKSXOZA`　**样本**: 4

### 请求业务字段

| 字段 | 类型 | 示例 |
|---|---|---|
| OpponentAccountServerId | int | `10007689668` |
| OpponentIndex | int | `0` |
| OpponentRank | int | `42` |

### 响应 packet 顶层

- **AccountCurrencyDB**: object
- **AllTimeRewards**: null
- **ArenaBattleDB**: object
- **ArenaPlayerInfoDB**: object
- **BattlePassMissionProgressDBDict**: object
- **BattleServerError**: bool
- **BattleSetting**: object
- **MissionProgressDBs**: array
- **Protocol**: int
- **RequestId**: str
- **SeasonRewards**: null
- **ServerNotification**: int
- **ServerTimeTicks**: int
- **SessionKey**: object
- **VictoryRewards**: null/object

<details><summary>响应结构示例（限深 3 层）</summary>

```
- **AccountCurrencyDB**
  - **AccountLevel**: int = `1`
  - **AcademyLocationRankSum**: int = `1`
  - **CurrencyDict**: object
    - **1**: int = `980626306`
    - **10**: int = `0`
    - **11**: int = `0`
    - **12**: int = `0`
    - **13**: int = `0`
    - **14**: int = `0`
    - **15**: int = `0`
    - **16**: int = `0`
    - **17**: int = `0`
    - **18**: int = `127785`
    - **19**: int = `40`
    - **2**: int = `0`
    - **20**: int = `40`
    - **21**: int = `40`
    - **22**: int = `0`
    - **23**: int = `0`
    - **24**: int = `0`
    - **25**: int = `4`
    - **26**: int = `0`
    - **27**: int = `0`
    - **28**: int = `0`
    - **29**: int = `0`
    - **3**: int = `154542`
    - **4**: int = `154542`
    - **5**: int = `890`
    - **6**: int = `0`
    - **7**: int = `4`
    - **8**: int = `3`
    - **9**: int = `0`
  - **UpdateTimeDict**: object
    - **12**: str = `"2026-10-12T20:55:13.954"`
    - **13**: str = `"2026-10-12T20:55:13.954"`
    - **14**: str = `"2026-10-12T20:55:13.954"`
    - **15**: str = `"2026-10-12T20:55:13.954"`
    - **16**: str = `"2026-10-12T20:55:13.954"`
    - **17**: str = `"2026-09-23T19:46:10.825"`
    - **19**: str = `"2026-10-12T20:55:13.954"`
    - **20**: str = `"2026-10-12T20:55:13.954"`
    - **21**: str = `"2026-10-12T20:55:13.954"`
    - **22**: str = `"2026-10-12T20:54:38.785"`
    - **23**: str = `"2026-10-12T20:54:58.796"`
    - **24**: str = `"2026-10-05T19:17:57.772"`
    - **25**: str = `"2026-10-05T17:57:35.375"`
    - **26**: str = `"2026-10-05T19:21:50.378"`
    - **5**: str = `"2026-10-12T20:54:58.796"`
    - **6**: str = `"2026-10-12T20:44:54.769"`
    - **7**: str = `"2026-10-12T20:55:13.954"`
    - **8**: str = `"2026-10-12T20:44:54.769"`
    - **9**: str = `"2026-10-12T20:55:13.954"`
- **AllTimeRewards**
  - `null`
- **ArenaBattleDB**
  - **Season**: int = `9`
  - **Group**: int = `85`
  - **BattleStartTime**: str = `"2026-10-12T20:55:13.952857765"`
  - **BattleEndTime**: str = `"0001-01-01T00:00:00"`
  - **Seed**: int = `5695337`
  - **AttackingUserDB**: object
    - **AccountServerId**: int = `10000000000`
    - **RepresentCharacterUniqueId**: int = `13010`
    - **NickName**: str = `"左搂邮箱右抱日奈"`
    - **Rank**: int = `79`
    - **Level**: int = `90`
    - **Exp**: int = `0`
    - **TeamSettingDB**: object
      - …(7 keys)
    - **AccountAttachmentDB**: object
      - …(2 keys)
    - **IsAnonymous**: bool = `false`
  - **DefendingUserDB**: object
    - **AccountServerId**: int = `10007933821`
    - **RepresentCharacterUniqueId**: int = `13003`
    - **NickName**: str = `""`
    - **Rank**: int = `55`
    - **Level**: int = `90`
    - **Exp**: int = `0`
    - **TeamSettingDB**: object
      - …(7 keys)
    - **AccountAttachmentDB**: object
      - …(2 keys)
    - **IsAnonymous**: bool = `true`
  - **BattleSummary**: object
    - **HashKey**: int = `0`
    - **IsBossBattle**: bool = `false`
    - **IsDefeatBattle**: bool = `false`
    - **BattleType**: int = `2097152`
    - **StageId**: int = `0`
    - **GroundId**: int = `530300016`
    - **Winner**: str = `"Group01"`
    - **EndType**: int = `4`
    - **EndFrame**: int = `2018`
    - **ElapsedRealtime**: float = `0.2119819`
    - **Group01Summary**: object
      - …(11 keys)
    - **Group02Summary**: object
      - …(11 keys)
    - **RaidSummary**: null = `null`
    - **WeekDungeonSummary**: null = `null`
    - **ArenaSummary**: object
      - …(3 keys)
- **ArenaPlayerInfoDB**
  - **CurrentSeasonId**: int = `9`
  - **PlayerGroupId**: int = `85`
  - **CurrentRank**: int = `55`
  - **SeasonRecord**: int = `25`
  - **AllTimeRecord**: int = `13`
  - **CumulativeTimeReward**: int = `142830`
  - **TimeRewardLastUpdateTime**: str = `"2026-10-12T20:55:13.952857765"`
  - **BattleEnterActiveTime**: str = `"2026-10-12T20:55:43.952857765"`
  - **DailyRewardActiveTime**: str = `"2026-10-13T14:00:00"`
- **BattlePassMissionProgressDBDict**
  - **1**: array
    - [0] (object):
      - …(6 keys)
- **BattleServerError**
  - `false`
- **BattleSetting**
  - **BattleType**: int = `2097152`
  - **EchelonType**: int = `0`
  - **RandomSeed**: int = `5695337`
  - **Buid**: str = `"10000000000_1791809713963"`
  - **BattleDurationInFrame**: int = `5400`
  - **GroundUniqueId**: int = `530300016`
  - **StageId**: int = `0`
  - **EnvironmentType**: int = `0`
  - **IsBoss**: bool = `false`
  - **IsAutoUseSkill**: bool = `true`
  - **LeftTeam**: object
    - **AccountId**: int = `10000000000`
    - **TeamId**: int = `1`
    - **TeamName**: str = `"左搂邮箱右抱日奈"`
    - **LeaderCharacterServerId**: int = `770403`
    - **FormationLocationKey**: object
      - …(1 keys)
    - **Starters**: array
      - …(array len=4)
    - **Supporters**: array
      - …(array len=2)
    - **ArenaSetting**: object
      - …(4 keys)
  - **RightTeam**: object
    - **AccountId**: int = `10007933821`
    - **TeamId**: int = `1`
    - **LeaderCharacterServerId**: int = `730532`
    - **FormationLocationKey**: object
      - …(1 keys)
    - **Starters**: array
      - …(array len=4)
    - **Supporters**: array
      - …(array len=2)
    - **ArenaSetting**: object
      - …(4 keys)
  - **PlayerActions**: null = `null`
  - **RaidSetting**: null = `null`
  - **StageIndex**: int = `0`
  - **EventSetting**: null = `null`
  - **TimeAttackSetting**: null = `null`
  - **ClanAssistUseInfo**: null = `null`
- **MissionProgressDBs**
  - [0] (object):
    - **AccountServerId**: int = `10000000000`
    - **MissionUniqueId**: int = `82029`
    - **Category**: int = `3`
    - **StartDate**: str = `"2026-04-09T20:22:43.391"`
    - **ProgressParameters**: object
      - …(1 keys)
  - …共 4 个元素
- **Protocol**
  - `22004`
- **RequestId**
  - `"0bfeb3c9-412a-4440-a699-0600da21bf43"`
- **SeasonRewards**
  - `null`
- **ServerNotification**
  - `3`
- **ServerTimeTicks**
  - `639274353143563446`
- **SessionKey**
  - **AccountServerId**: int = `10000000000`
  - **MxToken**: str = `"AAAAAAAA…"`
- **VictoryRewards**
  - **AccountDB**: object
    - **ServerId**: int = `10000000000`
    - **RoleId**: int = `10000000000`
    - **Nickname**: str = `"左搂邮箱右抱日奈"`
    - **CallName**: str = `"我要高炒了"`
    - **DevId**: str = `""`
    - **State**: int = `0`
    - **Level**: int = `90`
    - **Exp**: int = `0`
    - **Comment**: str = `""`
    - **LobbyMode**: int = `0`
    - **RepresentCharacterServerId**: int = `239093`
    - **MemoryLobbyUniqueId**: int = `0`
    - **LastConnectTime**: str = `"2026-10-12T20:41:00.044"`
    - **BirthDay**: str = `"2005-02-11T00:00:00"`
    - **CallNameUpdateTime**: str = `"0001-01-01T00:00:00"`
    - **PublisherAccountId**: int = `0`
    - **RetentionDays**: int = `0`
    - **VIPLevel**: int = `0`
    - **CreateDate**: str = `"2023-08-03T21:16:37.326"`
    - **UnReadMailCount**: int = `0`
    - **LinkRewardDateDate**: str = `"0001-01-01T00:00:00"`
    - **Location**: str = `""`
    - **LastReturningDate**: str = `"0001-01-01T00:00:00"`
  - **AccountCurrencyDB**: object
    - **AccountLevel**: int = `1`
    - **AcademyLocationRankSum**: int = `1`
    - **CurrencyDict**: object
      - …(29 keys)
    - **UpdateTimeDict**: object
      - …(19 keys)
  - **DisplaySequence**: array
    - [0] (object):
      - …(2 keys)
```
</details>


## /api/arena/enterlobby

- **中文**: 战术对抗赛·进入大厅
- **Protocol**: 22000　**混淆名**: `A2FUPZASWN3KLFFCK5RS2Z3UQI`　**样本**: 5

请求无业务字段（仅标准头）。

### 响应 packet 顶层

- **ArenaPlayerInfoDB**: object
- **AutoRefreshTime**: str
- **IsServerRunBattle**: bool
- **MapId**: int
- **OpponentUserDBs**: array
- **Protocol**: int
- **RequestId**: str
- **ServerNotification**: int
- **ServerTimeTicks**: int
- **SessionKey**: object

<details><summary>响应结构示例（限深 3 层）</summary>

```
- **ArenaPlayerInfoDB**
  - **CurrentSeasonId**: int = `9`
  - **PlayerGroupId**: int = `85`
  - **CurrentRank**: int = `61`
  - **SeasonRecord**: int = `25`
  - **AllTimeRecord**: int = `13`
  - **CumulativeTimeReward**: int = `238950`
  - **TimeRewardLastUpdateTime**: str = `"2026-10-11T18:21:46.062"`
  - **BattleEnterActiveTime**: str = `"2026-10-11T18:27:58.694"`
  - **DailyRewardActiveTime**: str = `"2026-10-12T14:00:00"`
- **AutoRefreshTime**
  - `"2026-10-11T18:27:43.705501895"`
- **IsServerRunBattle**
  - `true`
- **MapId**
  - `1006`
- **OpponentUserDBs**
  - [0] (object):
    - **AccountServerId**: int = `10009342516`
    - **RepresentCharacterUniqueId**: int = `13003`
    - **NickName**: str = `""`
    - **Rank**: int = `43`
    - **Level**: int = `90`
    - **Exp**: int = `0`
    - **TeamSettingDB**: object
      - …(7 keys)
    - **AccountAttachmentDB**: object
      - …(2 keys)
    - **IsAnonymous**: bool = `true`
  - …共 3 个元素
- **Protocol**
  - `22000`
- **RequestId**
  - `"4ae37a71-1166-4230-93a9-a03e2b62fdf6"`
- **ServerNotification**
  - `0`
- **ServerTimeTicks**
  - `639273400637453733`
- **SessionKey**
  - **AccountServerId**: int = `10000000000`
  - **MxToken**: str = `"AAAAAAAA…"`
```
</details>


## /api/arena/opponentlist

- **中文**: 战术对抗赛·对手列表
- **Protocol**: 22003　**混淆名**: `PO5IN3RWHZDBLMRS4DLY4YK3ZY`　**样本**: 5

请求无业务字段（仅标准头）。

### 响应 packet 顶层

- **AutoRefreshTime**: str
- **OpponentUserDBs**: array
- **PlayerRank**: int
- **Protocol**: int
- **RequestId**: str
- **ServerNotification**: int
- **ServerTimeTicks**: int
- **SessionKey**: object

<details><summary>响应结构示例（限深 3 层）</summary>

```
- **AutoRefreshTime**
  - `"2026-10-12T20:55:15.866764961"`
- **OpponentUserDBs**
  - [0] (object):
    - **AccountServerId**: int = `10010455573`
    - **RepresentCharacterUniqueId**: int = `13003`
    - **NickName**: str = `""`
    - **Rank**: int = `39`
    - **Level**: int = `90`
    - **Exp**: int = `0`
    - **TeamSettingDB**: object
      - …(7 keys)
    - **AccountAttachmentDB**: object
      - …(2 keys)
    - **IsAnonymous**: bool = `true`
  - …共 3 个元素
- **PlayerRank**
  - `55`
- **Protocol**
  - `22003`
- **RequestId**
  - `"c2e1164e-13b8-4ccf-bad1-7396d6060d10"`
- **ServerNotification**
  - `0`
- **ServerTimeTicks**
  - `639274353159110077`
- **SessionKey**
  - **AccountServerId**: int = `10000000000`
  - **MxToken**: str = `"AAAAAAAA…"`
```
</details>


## /api/arena/syncechelonsettingtime

- **中文**: 战术对抗赛·同步防守编队
- **Protocol**: 22016　**混淆名**: `EY7QMLA3SYLSYEV3NNLI2CY3ZQ`　**样本**: 4

请求无业务字段（仅标准头）。

### 响应 packet 顶层

- **EchelonSettingTime**: str
- **Protocol**: int
- **RequestId**: str
- **ServerNotification**: int
- **ServerTimeTicks**: int
- **SessionKey**: object

<details><summary>响应结构示例（限深 3 层）</summary>

```
- **EchelonSettingTime**
  - `"2026-10-12T20:55:11.346918248"`
- **Protocol**
  - `22016`
- **RequestId**
  - `"c4cf492b-8f28-42d8-8ce0-c6628f9c7ff2"`
- **ServerNotification**
  - `0`
- **ServerTimeTicks**
  - `639274353113474368`
- **SessionKey**
  - **AccountServerId**: int = `10000000000`
  - **MxToken**: str = `"AAAAAAAA…"`
```
</details>


# attendance

## /api/attendance/reward

- **中文**: 出勤奖励（签到）
- **Protocol**: 9002　**混淆名**: `AZELQARARQP5L57ZML5KM3BRJ4`　**样本**: 2

### 请求业务字段

| 字段 | 类型 | 示例 |
|---|---|---|
| AttendanceBookUniqueId | int | `0` |
| Day | int | `0` |
| DayByBookUniqueId | object | `{"1": 3}` |

### 响应 packet 顶层

- **AttendanceBookRewards**: array
- **AttendanceHistoryDBs**: array
- **ParcelResultDB**: null
- **Protocol**: int
- **RequestId**: str
- **ServerNotification**: int
- **ServerTimeTicks**: int
- **SessionKey**: object

<details><summary>响应结构示例（限深 3 层）</summary>

```
- **AttendanceBookRewards**
  - [0] (object):
    - **UniqueId**: int = `1`
    - **Type**: int = `0`
    - **TargetGroup**: int = `1`
    - **DisplayOrder**: int = `0`
    - **AccountLevelLimit**: int = `0`
    - **Title**: str = `"ATTENDANCEBOOK_NORMAL"`
    - **TitleImagePath**: str = `"Uis/01_Common/33_Attendance/ImageFont_Attend_1"`
    - **CountRule**: int = `0`
    - **CountReset**: int = `0`
    - **BookSize**: int = `10`
    - **StartDate**: str = `"2020-11-01T00:00:00"`
    - **StartableEndDate**: str = `"2099-12-31T04:00:00"`
    - **EndDate**: str = `"2099-12-31T04:00:00"`
    - **ExpiryDate**: int = `0`
    - **MailType**: int = `1`
    - **DailyRewardIcons**: object
      - …(0 keys)
    - **DailyRewards**: object
      - …(10 keys)
- **AttendanceHistoryDBs**
  - [0] (object):
    - **ServerId**: int = `0`
    - **AttendanceBookUniqueId**: int = `1`
    - **AttendedDay**: object
      - …(5 keys)
    - **Expired**: bool = `false`
- **ParcelResultDB**
  - `null`
- **Protocol**
  - `9002`
- **RequestId**
  - `"216cc591-db43-47b4-b9bb-0e2ef273aead"`
- **ServerNotification**
  - `0`
- **ServerTimeTicks**
  - `639275049060518496`
- **SessionKey**
  - **AccountServerId**: int = `10000000000`
  - **MxToken**: str = `"AAAAAAAA…"`
```
</details>


# battlepass

## /api/battlepass/check

- **中文**: 通行证·任务进度检查
- **Protocol**: 51006　**混淆名**: `JGJG65UANK2HFSVER3AX232FMM`　**样本**: 58

### 请求业务字段

| 字段 | 类型 | 示例 |
|---|---|---|
| BattlePassId | int | `1` |

### 响应 packet 顶层

- **HasCompleteMission**: bool
- **HasNotReceiveReward**: bool
- **Protocol**: int
- **RequestId**: str
- **ServerNotification**: int
- **ServerTimeTicks**: int
- **SessionKey**: object

<details><summary>响应结构示例（限深 3 层）</summary>

```
- **HasCompleteMission**
  - `true`
- **HasNotReceiveReward**
  - `true`
- **Protocol**
  - `51006`
- **RequestId**
  - `"2d4a7380-0821-4a12-9a85-bdd7c32656ec"`
- **ServerNotification**
  - `0`
- **ServerTimeTicks**
  - `639273396123013102`
- **SessionKey**
  - **AccountServerId**: int = `10016071938`
  - **MxToken**: str = `"wc4dt5o4…"`
```
</details>


## /api/battlepass/getinfo

- **中文**: 通行证·信息
- **Protocol**: 51000　**混淆名**: `IQLINGRIPTDDWVURJU6WQJY25E`　**样本**: 9

### 请求业务字段

| 字段 | 类型 | 示例 |
|---|---|---|
| BattlePassId | int | `1` |

### 响应 packet 顶层

- **BattlePassInfo**: object
- **Protocol**: int
- **RequestId**: str
- **ServerNotification**: int
- **ServerTimeTicks**: int
- **SessionKey**: object

<details><summary>响应结构示例（限深 3 层）</summary>

```
- **BattlePassInfo**
  - **BattlePassId**: int = `1`
  - **PassLevel**: int = `44`
  - **PassExp**: int = `800`
  - **PurchaseGroupId**: int = `0`
  - **ReceiveRewardLevel**: int = `44`
  - **ReceivePurchaseRewardLevel**: int = `0`
  - **WeeklyPassExp**: int = `11800`
  - **LastWeeklyPassExpLimitRefreshDate**: str = `"2026-10-10T23:46:00.929"`
- **Protocol**
  - `51000`
- **RequestId**
  - `"8f101776-26ab-49a7-a03c-6f51cfc823ac"`
- **ServerNotification**
  - `0`
- **ServerTimeTicks**
  - `639273399441541053`
- **SessionKey**
  - **AccountServerId**: int = `10000000000`
  - **MxToken**: str = `"AAAAAAAA…"`
```
</details>


## /api/battlepass/missionlist

- **中文**: 通行证·任务列表
- **Protocol**: 51003　**混淆名**: `DM356GTN7BIX2KUOSIR6RHO2DQ`　**样本**: 7

### 请求业务字段

| 字段 | 类型 | 示例 |
|---|---|---|
| BattlePassId | int | `1` |

### 响应 packet 顶层

- **MissionHistoryUniqueIds**: array
- **ProgressDBs**: array
- **Protocol**: int
- **RequestId**: str
- **ServerNotification**: int
- **ServerTimeTicks**: int
- **SessionKey**: object

<details><summary>响应结构示例（限深 3 层）</summary>

```
- **MissionHistoryUniqueIds**
  - [0] (int):
    - `2001001`
  - …共 13 个元素
- **ProgressDBs**
  - [0] (object):
    - **AccountServerId**: int = `10000000000`
    - **MissionUniqueId**: int = `2000001`
    - **Category**: int = `1`
    - **Complete**: bool = `true`
    - **StartDate**: str = `"2026-10-11T18:25:41.208"`
    - **ProgressParameters**: object
      - …(1 keys)
  - …共 6 个元素
- **Protocol**
  - `51003`
- **RequestId**
  - `"4d870407-deb2-46ef-8c37-282f0a95412f"`
- **ServerNotification**
  - `0`
- **ServerTimeTicks**
  - `639273399487027733`
- **SessionKey**
  - **AccountServerId**: int = `10000000000`
  - **MxToken**: str = `"AAAAAAAA…"`
```
</details>


## /api/battlepass/missionmultiplereward

- **中文**: 通行证·批量领取任务奖励
- **Protocol**: 51005　**混淆名**: `5LQOU6YFWHYRBRI2OHKI37DHRE`　**样本**: 1

### 请求业务字段

| 字段 | 类型 | 示例 |
|---|---|---|
| BattlePassId | int | `1` |
| MissionCategory | int | `5` |

### 响应 packet 顶层

- **AddedHistoryDBs**: array
- **BattlePassInfo**: object
- **ParcelResultDB**: object
- **Protocol**: int
- **RequestId**: str
- **ServerNotification**: int
- **ServerTimeTicks**: int
- **SessionKey**: object

<details><summary>响应结构示例（限深 3 层）</summary>

```
- **AddedHistoryDBs**
  - [0] (object):
    - **AccountServerId**: int = `10000000000`
    - **MissionUniqueId**: int = `2000001`
    - **CompleteTime**: str = `"2026-10-11T18:32:50.63218105"`
    - **Expired**: bool = `false`
  - …共 6 个元素
- **BattlePassInfo**
  - **BattlePassId**: int = `1`
  - **PassLevel**: int = `46`
  - **PassExp**: int = `0`
  - **PurchaseGroupId**: int = `0`
  - **ReceiveRewardLevel**: int = `44`
  - **ReceivePurchaseRewardLevel**: int = `0`
  - **WeeklyPassExp**: int = `13000`
  - **LastWeeklyPassExpLimitRefreshDate**: str = `"2026-10-11T18:32:50.63218105"`
- **ParcelResultDB**
  - **DisplaySequence**: array
    - [0] (object):
      - …(2 keys)
- **Protocol**
  - `51005`
- **RequestId**
  - `"c28e9b44-6042-4ceb-a96c-60d5b4b50a8e"`
- **ServerNotification**
  - `0`
- **ServerTimeTicks**
  - `639273403706473148`
- **SessionKey**
  - **AccountServerId**: int = `10000000000`
  - **MxToken**: str = `"AAAAAAAA…"`
```
</details>


## /api/battlepass/receivereward

- **中文**: 通行证·领取等级奖励
- **Protocol**: 51002　**混淆名**: `QTVDCGVGII6VQBQQIAXJQD4M4Q`　**样本**: 1

### 请求业务字段

| 字段 | 类型 | 示例 |
|---|---|---|
| BattlePassId | int | `1` |

### 响应 packet 顶层

- **BattlePassInfo**: object
- **ParcelResult**: object
- **Protocol**: int
- **RequestId**: str
- **ServerNotification**: int
- **ServerTimeTicks**: int
- **SessionKey**: object

<details><summary>响应结构示例（限深 3 层）</summary>

```
- **BattlePassInfo**
  - **BattlePassId**: int = `1`
  - **PassLevel**: int = `46`
  - **PassExp**: int = `0`
  - **PurchaseGroupId**: int = `0`
  - **ReceiveRewardLevel**: int = `46`
  - **ReceivePurchaseRewardLevel**: int = `0`
  - **WeeklyPassExp**: int = `13000`
  - **LastWeeklyPassExpLimitRefreshDate**: str = `"2026-10-11T18:32:50.632"`
- **ParcelResult**
  - **AccountDB**: object
    - **ServerId**: int = `10000000000`
    - **RoleId**: int = `10000000000`
    - **Nickname**: str = `"左搂邮箱右抱日奈"`
    - **CallName**: str = `"我要高炒了"`
    - **DevId**: str = `""`
    - **State**: int = `0`
    - **Level**: int = `90`
    - **Exp**: int = `0`
    - **Comment**: str = `""`
    - **LobbyMode**: int = `0`
    - **RepresentCharacterServerId**: int = `239093`
    - **MemoryLobbyUniqueId**: int = `0`
    - **LastConnectTime**: str = `"2026-10-11T18:25:41.208"`
    - **BirthDay**: str = `"2005-02-11T00:00:00"`
    - **CallNameUpdateTime**: str = `"0001-01-01T00:00:00"`
    - **PublisherAccountId**: int = `0`
    - **RetentionDays**: int = `0`
    - **VIPLevel**: int = `0`
    - **CreateDate**: str = `"2023-08-03T21:16:37.326"`
    - **UnReadMailCount**: int = `0`
    - **LinkRewardDateDate**: str = `"0001-01-01T00:00:00"`
    - **Location**: str = `""`
    - **LastReturningDate**: str = `"0001-01-01T00:00:00"`
  - **AccountCurrencyDB**: object
    - **AccountLevel**: int = `1`
    - **AcademyLocationRankSum**: int = `1`
    - **CurrencyDict**: object
      - …(29 keys)
    - **UpdateTimeDict**: object
      - …(19 keys)
  - **ItemDBs**: object
    - **2988537**: object
      - …(5 keys)
    - **8089977**: object
      - …(5 keys)
  - **DisplaySequence**: array
    - [0] (object):
      - …(2 keys)
    - …共 2 个元素
- **Protocol**
  - `51002`
- **RequestId**
  - `"368a88d9-ccc8-4bda-bd40-61df26fafb2f"`
- **ServerNotification**
  - `0`
- **ServerTimeTicks**
  - `639273403753470882`
- **SessionKey**
  - **AccountServerId**: int = `10000000000`
  - **MxToken**: str = `"AAAAAAAA…"`
```
</details>


# billing

## /api/billing/purchasefreeproduct

- **中文**: 商城·免费商品领取
- **Protocol**: 29003　**混淆名**: `EG2DYZYABN6E5CHUSZPXOI7BPQ`　**样本**: 3

### 请求业务字段

| 字段 | 类型 | 示例 |
|---|---|---|
| ShopCashId | int | `900000` |

### 响应 packet 顶层

- **MailDB**: null
- **MissionProgressDBs**: array
- **ParcelResult**: object
- **Protocol**: int
- **PurchaseProduct**: object
- **RequestId**: str
- **ServerNotification**: int
- **ServerTimeTicks**: int
- **SessionKey**: object

<details><summary>响应结构示例（限深 3 层）</summary>

```
- **MailDB**
  - `null`
- **MissionProgressDBs**
  - [0] (object):
    - **AccountServerId**: int = `10000000000`
    - **MissionUniqueId**: int = `82029`
    - **Category**: int = `3`
    - **StartDate**: str = `"2026-04-09T20:22:43.391"`
    - **ProgressParameters**: object
      - …(1 keys)
- **ParcelResult**
  - **AccountDB**: object
    - **ServerId**: int = `10000000000`
    - **RoleId**: int = `10000000000`
    - **Nickname**: str = `"左搂邮箱右抱日奈"`
    - **CallName**: str = `"我要高炒了"`
    - **DevId**: str = `""`
    - **State**: int = `0`
    - **Level**: int = `90`
    - **Exp**: int = `0`
    - **Comment**: str = `""`
    - **LobbyMode**: int = `0`
    - **RepresentCharacterServerId**: int = `239093`
    - **MemoryLobbyUniqueId**: int = `0`
    - **LastConnectTime**: str = `"2026-10-12T20:41:00.044"`
    - **BirthDay**: str = `"2005-02-11T00:00:00"`
    - **CallNameUpdateTime**: str = `"0001-01-01T00:00:00"`
    - **PublisherAccountId**: int = `0`
    - **RetentionDays**: int = `0`
    - **VIPLevel**: int = `0`
    - **CreateDate**: str = `"2023-08-03T21:16:37.326"`
    - **UnReadMailCount**: int = `0`
    - **LinkRewardDateDate**: str = `"0001-01-01T00:00:00"`
    - **Location**: str = `""`
    - **LastReturningDate**: str = `"0001-01-01T00:00:00"`
  - **AccountCurrencyDB**: object
    - **AccountLevel**: int = `1`
    - **AcademyLocationRankSum**: int = `1`
    - **CurrencyDict**: object
      - …(29 keys)
    - **UpdateTimeDict**: object
      - …(19 keys)
  - **DisplaySequence**: array
    - [0] (object):
      - …(2 keys)
    - …共 2 个元素
- **Protocol**
  - `29003`
- **PurchaseProduct**
  - **ShopCashId**: int = `900000`
  - **PurchaseCount**: int = `1`
  - **ResetDate**: str = `"2026-10-12T04:00:00"`
  - **PurchaseDate**: str = `"0001-01-01T00:00:00"`
- **RequestId**
  - `"b443cdb0-8b50-47c5-b67f-b7931b70777f"`
- **ServerNotification**
  - `0`
- **ServerTimeTicks**
  - `639274360600602301`
- **SessionKey**
  - **AccountServerId**: int = `10000000000`
  - **MxToken**: str = `"AAAAAAAA…"`
```
</details>


## /api/billing/purchaselistbyyostar

- **中文**: 商城·商品列表查询
- **Protocol**: 29002　**混淆名**: `UXIHQC2AXRZCEBTL2NPBMBBI6I`　**样本**: 11

请求无业务字段（仅标准头）。

### 响应 packet 顶层

- **CountList**: array
- **MonthlyProductList**: array
- **OrderList**: array
- **Protocol**: int
- **RequestId**: str
- **ServerNotification**: int
- **ServerTimeTicks**: int
- **SessionKey**: object

<details><summary>响应结构示例（限深 3 层）</summary>

```
- **CountList**
  - (空数组)
- **MonthlyProductList**
  - (空数组)
- **OrderList**
  - (空数组)
- **Protocol**
  - `29002`
- **RequestId**
  - `"4afd2b4f-5fb2-4020-a4c7-90711cbd9e2c"`
- **ServerNotification**
  - `0`
- **ServerTimeTicks**
  - `639273398624060043`
- **SessionKey**
  - **AccountServerId**: int = `10016071938`
  - **MxToken**: str = `"wc4dt5o4…"`
```
</details>


# cafe

## /api/cafe/ack

- **中文**: 咖啡厅·状态确认
- **Protocol**: 20001　**混淆名**: `ZSN5XTRP4BTJ7F2HAHOTGZLHLU`　**样本**: 6

### 请求业务字段

| 字段 | 类型 | 示例 |
|---|---|---|
| CafeDBId | int | `100000000001` |

### 响应 packet 顶层

- **CafeDB**: object
- **Protocol**: int
- **RequestId**: str
- **ServerNotification**: int
- **ServerTimeTicks**: int
- **SessionKey**: object

<details><summary>响应结构示例（限深 3 层）</summary>

```
- **CafeDB**
  - **CafeDBId**: int = `100000000002`
  - **CafeId**: int = `2`
  - **AccountId**: int = `10000000000`
  - **CafeRank**: int = `9`
  - **LastUpdate**: str = `"2026-10-11T18:25:42.02"`
  - **LastSummonDate**: str = `"2026-10-10T23:11:34.912"`
  - **IsNew**: bool = `false`
  - **CafeVisitCharacterDBs**: object
    - **10081**: object
      - …(3 keys)
    - **10114**: object
      - …(3 keys)
    - **16007**: object
      - …(3 keys)
    - **16016**: object
      - …(3 keys)
    - **23000**: object
      - …(3 keys)
  - **FurnitureDBs**: array
    - [0] (object):
      - …(10 keys)
    - …共 53 个元素
  - **ProductionAppliedTime**: str = `"2026-10-11T18:00:00"`
  - **ProductionDB**: object
    - **CafeDBId**: int = `100000000002`
    - **ComfortValue**: int = `5000`
    - **AppliedDate**: str = `"2026-10-11T18:00:00"`
    - **ProductionParcelInfos**: array
      - …(array len=1)
- **Protocol**
  - `20001`
- **RequestId**
  - `"e9b06dcc-5003-4f64-b253-19d3d0932761"`
- **ServerNotification**
  - `0`
- **ServerTimeTicks**
  - `639273400938641542`
- **SessionKey**
  - **AccountServerId**: int = `10000000000`
  - **MxToken**: str = `"AAAAAAAA…"`
```
</details>


## /api/cafe/interact

- **中文**: 咖啡厅·互动（摸头/送礼）
- **Protocol**: 20006　**混淆名**: `MBDIB333KNPPUQNJEQNI3P6SIM`　**样本**: 30

### 请求业务字段

| 字段 | 类型 | 示例 |
|---|---|---|
| CafeDBId | int | `100000000001` |
| CharacterId | int | `10060` |

### 响应 packet 顶层

- **BattlePassMissionProgressDBDict**: object
- **CafeDB**: object
- **CharacterDB**: object
- **MissionProgressDBs**: array
- **ParcelResultDB**: object
- **Protocol**: int
- **RequestId**: str
- **ServerNotification**: int
- **ServerTimeTicks**: int
- **SessionKey**: object

<details><summary>响应结构示例（限深 3 层）</summary>

```
- **BattlePassMissionProgressDBDict**
  - **1**: array
    - [0] (object):
      - …(6 keys)
- **CafeDB**
  - **CafeDBId**: int = `100000000001`
  - **CafeId**: int = `1`
  - **AccountId**: int = `10000000000`
  - **CafeRank**: int = `10`
  - **LastUpdate**: str = `"2026-10-11T18:25:42.02"`
  - **LastSummonDate**: str = `"2026-10-10T23:11:21.027"`
  - **IsNew**: bool = `false`
  - **CafeVisitCharacterDBs**: object
    - **10060**: object
      - …(3 keys)
    - **10110**: object
      - …(3 keys)
    - **10116**: object
      - …(3 keys)
    - **20024**: object
      - …(3 keys)
    - **23005**: object
      - …(3 keys)
  - **FurnitureDBs**: array
    - [0] (object):
      - …(10 keys)
    - …共 55 个元素
  - **ProductionAppliedTime**: str = `"2026-10-11T18:00:00"`
  - **ProductionDB**: object
    - **CafeDBId**: int = `100000000001`
    - **ComfortValue**: int = `5500`
    - **AppliedDate**: str = `"2026-10-11T18:00:00"`
    - **ProductionParcelInfos**: array
      - …(array len=2)
- **CharacterDB**
  - **Type**: int = `1`
  - **ServerId**: int = `2969203`
  - **UniqueId**: int = `10110`
  - **StarGrade**: int = `3`
  - **Level**: int = `90`
  - **Exp**: int = `-1`
  - **FavorRank**: int = `15`
  - **FavorExp**: int = `50`
  - **PublicSkillLevel**: int = `10`
  - **ExSkillLevel**: int = `5`
  - **PassiveSkillLevel**: int = `10`
  - **ExtraPassiveSkillLevel**: int = `10`
  - **LeaderSkillLevel**: int = `1`
  - **IsNew**: bool = `false`
  - **IsLocked**: bool = `false`
  - **IsFavorite**: bool = `false`
  - **EquipmentServerIds**: array
    - [0] (int):
      - `24662516`
    - …共 3 个元素
  - **PotentialStats**: object
    - **1**: int = `0`
    - **2**: int = `0`
    - **3**: int = `0`
- **MissionProgressDBs**
  - [0] (object):
    - **AccountServerId**: int = `10000000000`
    - **MissionUniqueId**: int = `1509`
    - **Category**: int = `1`
    - **Complete**: bool = `true`
    - **StartDate**: str = `"2026-10-12T17:09:25.927"`
    - **ProgressParameters**: object
      - …(1 keys)
  - …共 2 个元素
- **ParcelResultDB**
  - **AccountDB**: object
    - **ServerId**: int = `10000000000`
    - **RoleId**: int = `10000000000`
    - **Nickname**: str = `"左搂邮箱右抱日奈"`
    - **CallName**: str = `"我要高炒了"`
    - **DevId**: str = `""`
    - **State**: int = `0`
    - **Level**: int = `90`
    - **Exp**: int = `0`
    - **Comment**: str = `""`
    - **LobbyMode**: int = `0`
    - **RepresentCharacterServerId**: int = `239093`
    - **MemoryLobbyUniqueId**: int = `0`
    - **LastConnectTime**: str = `"2026-10-11T18:25:41.208"`
    - **BirthDay**: str = `"2005-02-11T00:00:00"`
    - **CallNameUpdateTime**: str = `"0001-01-01T00:00:00"`
    - **PublisherAccountId**: int = `0`
    - **RetentionDays**: int = `0`
    - **VIPLevel**: int = `0`
    - **CreateDate**: str = `"2023-08-03T21:16:37.326"`
    - **UnReadMailCount**: int = `0`
    - **LinkRewardDateDate**: str = `"0001-01-01T00:00:00"`
    - **Location**: str = `""`
    - **LastReturningDate**: str = `"0001-01-01T00:00:00"`
  - **AccountCurrencyDB**: object
    - **AccountLevel**: int = `1`
    - **AcademyLocationRankSum**: int = `1`
    - **CurrencyDict**: object
      - …(29 keys)
    - **UpdateTimeDict**: object
      - …(19 keys)
  - **CharacterDBs**: array
    - [0] (object):
      - …(18 keys)
- **Protocol**
  - `20006`
- **RequestId**
  - `"81113893-cbda-4558-b95d-05f54d103776"`
- **ServerNotification**
  - `0`
- **ServerTimeTicks**
  - `639273400839970240`
- **SessionKey**
  - **AccountServerId**: int = `10000000000`
  - **MxToken**: str = `"AAAAAAAA…"`
```
</details>


## /api/cafe/receivecurrency

- **中文**: 咖啡厅·领取体力和信用点
- **Protocol**: 20013　**混淆名**: `MLB5WYXD67ETPMTGRWOTNKAWHM`　**样本**: 2

### 请求业务字段

| 字段 | 类型 | 示例 |
|---|---|---|
| AccountServerId | int | `10000000000` |
| CafeDBId | int | `0` |

### 响应 packet 顶层

- **CafeDBs**: array
- **MissionProgressDBs**: array
- **ParcelResultDB**: object
- **Protocol**: int
- **RequestId**: str
- **ServerNotification**: int
- **ServerTimeTicks**: int
- **SessionKey**: object

<details><summary>响应结构示例（限深 3 层）</summary>

```
- **CafeDBs**
  - [0] (object):
    - **CafeDBId**: int = `100000000001`
    - **CafeId**: int = `1`
    - **AccountId**: int = `10000000000`
    - **CafeRank**: int = `10`
    - **LastUpdate**: str = `"2026-10-12T17:09:27.172"`
    - **LastSummonDate**: str = `"2026-10-10T23:11:21.027"`
    - **IsNew**: bool = `false`
    - **CafeVisitCharacterDBs**: object
      - …(5 keys)
    - **FurnitureDBs**: array
      - …(array len=55)
    - **ProductionAppliedTime**: str = `"2026-10-12T20:00:00"`
    - **ProductionDB**: object
      - …(4 keys)
  - …共 2 个元素
- **MissionProgressDBs**
  - [0] (object):
    - **AccountServerId**: int = `10000000000`
    - **MissionUniqueId**: int = `82029`
    - **Category**: int = `3`
    - **StartDate**: str = `"2026-04-09T20:22:43.391"`
    - **ProgressParameters**: object
      - …(1 keys)
- **ParcelResultDB**
  - **AccountDB**: object
    - **ServerId**: int = `10000000000`
    - **RoleId**: int = `10000000000`
    - **Nickname**: str = `"左搂邮箱右抱日奈"`
    - **CallName**: str = `"我要高炒了"`
    - **DevId**: str = `""`
    - **State**: int = `0`
    - **Level**: int = `90`
    - **Exp**: int = `0`
    - **Comment**: str = `""`
    - **LobbyMode**: int = `0`
    - **RepresentCharacterServerId**: int = `239093`
    - **MemoryLobbyUniqueId**: int = `0`
    - **LastConnectTime**: str = `"2026-10-12T19:02:39.466"`
    - **BirthDay**: str = `"2005-02-11T00:00:00"`
    - **CallNameUpdateTime**: str = `"0001-01-01T00:00:00"`
    - **PublisherAccountId**: int = `0`
    - **RetentionDays**: int = `0`
    - **VIPLevel**: int = `0`
    - **CreateDate**: str = `"2023-08-03T21:16:37.326"`
    - **UnReadMailCount**: int = `0`
    - **LinkRewardDateDate**: str = `"0001-01-01T00:00:00"`
    - **Location**: str = `""`
    - **LastReturningDate**: str = `"0001-01-01T00:00:00"`
  - **AccountCurrencyDB**: object
    - **AccountLevel**: int = `1`
    - **AcademyLocationRankSum**: int = `1`
    - **CurrencyDict**: object
      - …(29 keys)
    - **UpdateTimeDict**: object
      - …(19 keys)
  - **DisplaySequence**: array
    - [0] (object):
      - …(2 keys)
    - …共 3 个元素
- **Protocol**
  - `20013`
- **RequestId**
  - `"f78bb467-489a-409e-9214-49fd7b18e8f2"`
- **ServerNotification**
  - `0`
- **ServerTimeTicks**
  - `639274341667598972`
- **SessionKey**
  - **AccountServerId**: int = `10000000000`
  - **MxToken**: str = `"AAAAAAAA…"`
```
</details>


## /api/cafe/summoncharacter

- **中文**: 咖啡厅·邀请学生入店
- **Protocol**: 20015　**混淆名**: `LL3NMLO43N76H3G47UKV3CNSRQ`　**样本**: 4

### 请求业务字段

| 字段 | 类型 | 示例 |
|---|---|---|
| CafeDBId | int | `100000000001` |
| CharacterServerId | int | `1753765` |

### 响应 packet 顶层

- **CafeDB**: object
- **CafeDBs**: array
- **Protocol**: int
- **RequestId**: str
- **ServerNotification**: int
- **ServerTimeTicks**: int
- **SessionKey**: object

<details><summary>响应结构示例（限深 3 层）</summary>

```
- **CafeDB**
  - **CafeDBId**: int = `100000000002`
  - **CafeId**: int = `2`
  - **AccountId**: int = `10000000000`
  - **CafeRank**: int = `9`
  - **LastUpdate**: str = `"2026-10-12T17:09:27.172"`
  - **LastSummonDate**: str = `"2026-10-12T20:36:52.872571298"`
  - **IsNew**: bool = `false`
  - **CafeVisitCharacterDBs**: object
    - **10026**: object
      - …(3 keys)
    - **10040**: object
      - …(3 keys)
    - **10086**: object
      - …(3 keys)
    - **10100**: object
      - …(4 keys)
    - **13007**: object
      - …(3 keys)
    - **23000**: object
      - …(3 keys)
  - **FurnitureDBs**: array
    - [0] (object):
      - …(10 keys)
    - …共 53 个元素
  - **ProductionAppliedTime**: str = `"2026-10-12T20:00:00"`
  - **ProductionDB**: object
    - **CafeDBId**: int = `100000000002`
    - **ComfortValue**: int = `5000`
    - **AppliedDate**: str = `"2026-10-12T20:00:00"`
    - **ProductionParcelInfos**: array
      - …(array len=1)
- **CafeDBs**
  - [0] (object):
    - **CafeDBId**: int = `100000000001`
    - **CafeId**: int = `1`
    - **AccountId**: int = `10000000000`
    - **CafeRank**: int = `10`
    - **LastUpdate**: str = `"2026-10-12T17:09:27.172"`
    - **LastSummonDate**: str = `"2026-10-12T20:36:10.83"`
    - **IsNew**: bool = `false`
    - **CafeVisitCharacterDBs**: object
      - …(6 keys)
    - **FurnitureDBs**: array
      - …(array len=55)
    - **ProductionAppliedTime**: str = `"2026-10-12T20:00:00"`
    - **ProductionDB**: object
      - …(4 keys)
  - …共 2 个元素
- **Protocol**
  - `20015`
- **RequestId**
  - `"887f87c9-4b08-4c60-9117-239a0c1bbcf1"`
- **ServerNotification**
  - `0`
- **ServerTimeTicks**
  - `639274342128793545`
- **SessionKey**
  - **AccountServerId**: int = `10000000000`
  - **MxToken**: str = `"AAAAAAAA…"`
```
</details>


# campaign

## /api/campaign/list

- **中文**: 关卡开放信息（活动副本列表）
- **Protocol**: 6000　**混淆名**: `ZJSFR7GZ6IM2NYYNJKECP42SRI`　**样本**: 3

请求无业务字段（仅标准头）。

### 响应 packet 顶层

- **CampaignChapterClearRewardHistoryDBs**: array
- **CurrentScenarioId**: int
- **Protocol**: int
- **RequestId**: str
- **ServerNotification**: int
- **ServerTimeTicks**: int
- **SessionKey**: object
- **StageHistoryDBs**: array
- **StrategyObjecthistoryDBs**: array

<details><summary>响应结构示例（限深 3 层）</summary>

```
- **CampaignChapterClearRewardHistoryDBs**
  - [0] (object):
    - **AccountServerId**: int = `10000000000`
    - **ChapterUniqueId**: int = `101`
    - **RewardType**: int = `1`
    - **ReceiveDate**: str = `"2023-08-05T14:06:12.558"`
  - …共 56 个元素
- **CurrentScenarioId**
  - `70007020`
- **Protocol**
  - `6000`
- **RequestId**
  - `"9ae6d5ed-fc64-4696-b5fc-5259d5cd65e7"`
- **ServerNotification**
  - `0`
- **ServerTimeTicks**
  - `639274360847348132`
- **SessionKey**
  - **AccountServerId**: int = `10000000000`
  - **MxToken**: str = `"AAAAAAAA…"`
- **StageHistoryDBs**
  - [0] (object):
    - **AccountServerId**: int = `10000000000`
    - **StoryUniqueId**: int = `0`
    - **ChapterUniqueId**: int = `101`
    - **StageUniqueId**: int = `1011101`
    - **TacticClearCountWithRankSRecord**: int = `2`
    - **ClearTurnRecord**: int = `2`
    - **Star1Flag**: bool = `true`
    - **Star2Flag**: bool = `true`
    - **Star3Flag**: bool = `true`
    - **TodayPlayCount**: int = `2`
    - **LastPlay**: str = `"2024-09-04T23:13:59.094"`
    - **FirstClearRewardReceive**: str = `"2023-08-04T14:30:53.397"`
    - **StarRewardReceive**: str = `"2023-08-04T14:30:53.397"`
  - …共 391 个元素
- **StrategyObjecthistoryDBs**
  - [0] (object):
    - **AccountId**: int = `10000000000`
    - **StrategyObjectId**: int = `1012101`
  - …共 57 个元素
```
</details>


# clan

## /api/clan/chat/records

- **中文**: 社团·聊天记录
- **Protocol**: 90009　**混淆名**: `2OX7WGNGTJCQGYBAT5VZY5VWIM`　**样本**: 5

### 请求业务字段

| 字段 | 类型 | 示例 |
|---|---|---|
| ClanDBId | int | `12828` |
| LastChatId | int | `320197` |

### 响应 packet 顶层

- **ChatRecords**: array
- **Protocol**: int
- **RequestId**: str
- **ServerNotification**: int
- **ServerTimeTicks**: int
- **SessionKey**: object

<details><summary>响应结构示例（限深 3 层）</summary>

```
- **ChatRecords**
  - (空数组)
- **Protocol**
  - `90009`
- **RequestId**
  - `"049d1748-def2-4a33-b563-a6d8d5efb5b9"`
- **ServerNotification**
  - `0`
- **ServerTimeTicks**
  - `639274351830118512`
- **SessionKey**
  - **AccountServerId**: int = `10000000000`
  - **MxToken**: str = `"AAAAAAAA…"`
```
</details>


## /api/clan/check

- **中文**: 社团·状态检查
- **Protocol**: 28019　**混淆名**: `QXX6AAJZW2CU4X57SL7FCM72XA`　**样本**: 43

请求无业务字段（仅标准头）。

### 响应 packet 顶层

- **Protocol**: int
- **RequestId**: str
- **ServerNotification**: int
- **ServerTimeTicks**: int
- **SessionKey**: object

<details><summary>响应结构示例（限深 3 层）</summary>

```
- **Protocol**
  - `28019`
- **RequestId**
  - `"ebeb7110-400b-4a67-ac25-4a5a07622802"`
- **ServerNotification**
  - `0`
- **ServerTimeTicks**
  - `639273398818918290`
- **SessionKey**
  - **AccountServerId**: int = `10016071938`
  - **MxToken**: str = `"wc4dt5o4…"`
```
</details>


## /api/clan/lobby

- **中文**: 社团·大厅
- **Protocol**: 28000　**混淆名**: `NAIKTHZMYTUJ7XJ2SOQQWSXWTQ`　**样本**: 3

请求无业务字段（仅标准头）。

### 响应 packet 顶层

- **AccountClanDB**: object
- **AccountClanMemberDB**: object
- **ClanMemberDBs**: array
- **DefaultExposedClanDBs**: array
- **MissionProgressDBs**: array
- **Protocol**: int
- **RequestId**: str
- **ServerNotification**: int
- **ServerTimeTicks**: int
- **SessionKey**: object

<details><summary>响应结构示例（限深 3 层）</summary>

```
- **AccountClanDB**
  - **ClanDBId**: int = `12828`
  - **ClanName**: str = `"阿拜多斯还债小组"`
  - **ClanChannelName**: str = `"channel_12828"`
  - **ClanPresidentNickName**: str = `"薯片"`
  - **ClanPresidentRepresentCharacterUniqueId**: int = `20007`
  - **ClanPresidentRepresentCharacterCostumeId**: int = `0`
  - **ClanNotice**: str = `"欢迎加入还债小组\n511674602\n进去后改名字才不会被踢"`
  - **ClanMemberCount**: int = `50`
  - **ClanManagerCount**: int = `0`
  - **ClanJoinOption**: int = `0`
- **AccountClanMemberDB**
  - **AccountId**: int = `10000000000`
  - **AccountLevel**: int = `90`
  - **AccountNickName**: str = `"左搂邮箱右抱日奈"`
  - **RepresentCharacterUniqueId**: int = `13010`
  - **RepresentCharacterCostumeId**: int = `0`
  - **ClanDBId**: int = `12828`
  - **AttendanceCount**: int = `422`
  - **ClanSocialGrade**: int = `3`
  - **JoinDate**: str = `"2025-08-16T20:23:18.32"`
  - **SocialGradeUpdateTime**: str = `"0001-01-01T00:00:00"`
  - **LastLoginDate**: str = `"2026-10-12T20:52:59.60951907"`
  - **GameLoginDate**: str = `"2026-10-12T20:41:00.044"`
  - **AppliedDate**: str = `"2025-08-16T20:23:18.32"`
  - **AttachmentDB**: object
    - **AccountId**: int = `10000000000`
    - **EmblemUniqueId**: int = `1101080`
- **ClanMemberDBs**
  - [0] (object):
    - **AccountId**: int = `10006989848`
    - **AccountLevel**: int = `90`
    - **AccountNickName**: str = `"漆黑噤默"`
    - **RepresentCharacterUniqueId**: int = `10004`
    - **RepresentCharacterCostumeId**: int = `0`
    - **ClanDBId**: int = `12828`
    - **AttendanceCount**: int = `108`
    - **ClanSocialGrade**: int = `3`
    - **JoinDate**: str = `"2025-03-01T00:30:45.799"`
    - **SocialGradeUpdateTime**: str = `"0001-01-01T00:00:00"`
    - **LastLoginDate**: str = `"2026-06-10T19:39:15.083"`
    - **GameLoginDate**: str = `"2026-07-13T22:31:24.213"`
    - **AppliedDate**: str = `"2025-03-01T00:30:45.799"`
    - **AttachmentDB**: object
      - …(2 keys)
  - …共 50 个元素
- **DefaultExposedClanDBs**
  - (空数组)
- **MissionProgressDBs**
  - [0] (object):
    - **AccountServerId**: int = `10000000000`
    - **MissionUniqueId**: int = `1603`
    - **Category**: int = `9`
    - **Complete**: bool = `true`
    - **StartDate**: str = `"2026-10-12T17:09:25.927"`
    - **ProgressParameters**: object
      - …(1 keys)
- **Protocol**
  - `28000`
- **RequestId**
  - `"3a2bfc63-b8ed-45ed-b05c-0250a872941b"`
- **ServerNotification**
  - `7`
- **ServerTimeTicks**
  - `639274351796268495`
- **SessionKey**
  - **AccountServerId**: int = `10000000000`
  - **MxToken**: str = `"AAAAAAAA…"`
```
</details>


# contentsave

## /api/contentsave/get

- **中文**: 云存档读取
- **Protocol**: 26000　**混淆名**: `A5HZKUZQNB2GVPTZL5ATLZLLQ4`　**样本**: 5

请求无业务字段（仅标准头）。

### 响应 packet 顶层

- **ContentSaveDB**: null
- **EventContentChangeDB**: null
- **HasValidData**: bool
- **Protocol**: int
- **RequestId**: str
- **ServerNotification**: int
- **ServerTimeTicks**: int
- **SessionKey**: object

<details><summary>响应结构示例（限深 3 层）</summary>

```
- **ContentSaveDB**
  - `null`
- **EventContentChangeDB**
  - `null`
- **HasValidData**
  - `false`
- **Protocol**
  - `26000`
- **RequestId**
  - `"f1338193-8609-4cbd-9ce6-bba6864a00e6"`
- **ServerNotification**
  - `0`
- **ServerTimeTicks**
  - `639273399439675034`
- **SessionKey**
  - **AccountServerId**: int = `10000000000`
  - **MxToken**: str = `"AAAAAAAA…"`
```
</details>


# contentsweep

## /api/contentsweep/multisweep

- **中文**: 扫荡·多关卡批量扫荡
- **Protocol**: 27001　**混淆名**: `WQDUVIBUUZOJDJ35372OWS2QHQ`　**样本**: 3

### 请求业务字段

| 字段 | 类型 | 示例 |
|---|---|---|
| MultiSweepParameters | array | `[{"EventContentId": null, "ContentType": 1, "StageId": 11021…` |

### 响应 packet 顶层

- **BattlePassMissionProgressDBDict**: object
- **BonusParcels**: array
- **CampaignStageHistoryDBs**: array
- **ClearParcels**: array
- **EventContentBonusParcels**: null
- **MissionProgressDBs**: array
- **ParcelResult**: object
- **Protocol**: int
- **RequestId**: str
- **ServerNotification**: int
- **ServerTimeTicks**: int
- **SessionKey**: object

<details><summary>响应结构示例（限深 3 层）</summary>

```
- **BattlePassMissionProgressDBDict**
  - **1**: array
    - [0] (object):
      - …(5 keys)
    - …共 10 个元素
- **BonusParcels**
  - [0] (object):
    - **Key**: object
      - …(2 keys)
    - **Amount**: int = `7`
  - …共 3 个元素
- **CampaignStageHistoryDBs**
  - [0] (object):
    - **AccountServerId**: int = `10000000000`
    - **StoryUniqueId**: int = `0`
    - **ChapterUniqueId**: int = `110`
    - **StageUniqueId**: int = `1102103`
    - **TacticClearCountWithRankSRecord**: int = `6`
    - **ClearTurnRecord**: int = `5`
    - **Star1Flag**: bool = `true`
    - **Star2Flag**: bool = `true`
    - **Star3Flag**: bool = `true`
    - **TodayPlayCount**: int = `1`
    - **LastPlay**: str = `"2026-10-12T21:08:10.198982852"`
    - **FirstClearRewardReceive**: str = `"2024-06-04T18:04:29.902"`
    - **StarRewardReceive**: str = `"2024-06-04T18:04:29.902"`
  - …共 3 个元素
- **ClearParcels**
  - [0] (array):
    - [0] (object):
      - …(2 keys)
    - …共 10 个元素
- **EventContentBonusParcels**
  - `null`
- **MissionProgressDBs**
  - [0] (object):
    - **AccountServerId**: int = `10000000000`
    - **MissionUniqueId**: int = `2301`
    - **Category**: int = `2`
    - **StartDate**: str = `"2026-10-12T17:09:25.927"`
    - **ProgressParameters**: object
      - …(1 keys)
  - …共 15 个元素
- **ParcelResult**
  - **AccountDB**: object
    - **ServerId**: int = `10000000000`
    - **RoleId**: int = `10000000000`
    - **Nickname**: str = `"左搂邮箱右抱日奈"`
    - **CallName**: str = `"我要高炒了"`
    - **DevId**: str = `""`
    - **State**: int = `0`
    - **Level**: int = `90`
    - **Exp**: int = `0`
    - **Comment**: str = `""`
    - **LobbyMode**: int = `0`
    - **RepresentCharacterServerId**: int = `239093`
    - **MemoryLobbyUniqueId**: int = `0`
    - **LastConnectTime**: str = `"2026-10-12T20:41:00.044"`
    - **BirthDay**: str = `"2005-02-11T00:00:00"`
    - **CallNameUpdateTime**: str = `"0001-01-01T00:00:00"`
    - **PublisherAccountId**: int = `0`
    - **RetentionDays**: int = `0`
    - **VIPLevel**: int = `0`
    - **CreateDate**: str = `"2023-08-03T21:16:37.326"`
    - **UnReadMailCount**: int = `0`
    - **LinkRewardDateDate**: str = `"0001-01-01T00:00:00"`
    - **Location**: str = `""`
    - **LastReturningDate**: str = `"0001-01-01T00:00:00"`
  - **AccountCurrencyDB**: object
    - **AccountLevel**: int = `1`
    - **AcademyLocationRankSum**: int = `1`
    - **CurrencyDict**: object
      - …(29 keys)
    - **UpdateTimeDict**: object
      - …(19 keys)
  - **EquipmentDBs**: object
    - **11243090**: object
      - …(6 keys)
    - **11243131**: object
      - …(6 keys)
    - **12932155**: object
      - …(6 keys)
    - **24756655**: object
      - …(6 keys)
    - **3057550**: object
      - …(6 keys)
    - **3376589**: object
      - …(6 keys)
    - **5614612**: object
      - …(6 keys)
    - **9127579**: object
      - …(6 keys)
  - **ItemDBs**: object
    - **27787642**: object
      - …(5 keys)
    - **6884060**: object
      - …(5 keys)
  - **DisplaySequence**: array
    - [0] (object):
      - …(2 keys)
    - …共 21 个元素
  - **BaseAccountExp**: int = `60`
- **Protocol**
  - `27001`
- **RequestId**
  - `"562b6577-12ad-4198-a8cf-ababdd8c9262"`
- **ServerNotification**
  - `0`
- **ServerTimeTicks**
  - `639274360902787565`
- **SessionKey**
  - **AccountServerId**: int = `10000000000`
  - **MxToken**: str = `"AAAAAAAA…"`
```
</details>


## /api/contentsweep/request

- **中文**: 扫荡·执行
- **Protocol**: 27000　**混淆名**: `PP2KH57PYGW25AZW73372YR55E`　**样本**: 13

### 请求业务字段

| 字段 | 类型 | 示例 |
|---|---|---|
| Content | int | `3` |
| Count | int | `6` |
| EventContentId | int | `0` |
| StageId | int | `30110` |
| Type | null | `null` |

### 响应 packet 顶层

- **BattlePassMissionProgressDBDict**: object
- **BonusParcels**: array
- **CampaignStageHistoryDB**: object
- **ClearParcels**: array
- **EventContentBonusParcels**: array
- **MissionProgressDBs**: array
- **ParcelResult**: object
- **Protocol**: int
- **RequestId**: str
- **ServerNotification**: int
- **ServerTimeTicks**: int
- **SessionKey**: object

<details><summary>响应结构示例（限深 3 层）</summary>

```
- **BattlePassMissionProgressDBDict**
  - **1**: array
    - [0] (object):
      - …(6 keys)
- **BonusParcels**
  - [0] (object):
    - **Key**: object
      - …(2 keys)
    - **Amount**: int = `680`
  - …共 2 个元素
- **CampaignStageHistoryDB**
  - **AccountServerId**: int = `10000000000`
  - **StoryUniqueId**: int = `0`
  - **ChapterUniqueId**: int = `0`
  - **StageUniqueId**: int = `108362309`
  - **ClearTurnRecord**: int = `1`
  - **Star1Flag**: bool = `true`
  - **Star2Flag**: bool = `true`
  - **Star3Flag**: bool = `true`
  - **TodayPlayCount**: int = `42`
  - **LastPlay**: str = `"2026-10-11T18:32:22.665207165"`
  - **FirstClearRewardReceive**: str = `"2026-10-08T23:13:09.517"`
  - **StarRewardReceive**: str = `"2026-10-08T23:13:09.517"`
- **ClearParcels**
  - [0] (array):
    - [0] (object):
      - …(2 keys)
    - …共 2 个元素
  - …共 6 个元素
- **EventContentBonusParcels**
  - [0] (array):
    - [0] (object):
      - …(2 keys)
    - …共 3 个元素
  - …共 8 个元素
- **MissionProgressDBs**
  - [0] (object):
    - **AccountServerId**: int = `10000000000`
    - **MissionUniqueId**: int = `1510`
    - **Category**: int = `1`
    - **Complete**: bool = `true`
    - **StartDate**: str = `"2026-10-11T18:25:41.208"`
    - **ProgressParameters**: object
      - …(1 keys)
  - …共 3 个元素
- **ParcelResult**
  - **AccountDB**: object
    - **ServerId**: int = `10000000000`
    - **RoleId**: int = `10000000000`
    - **Nickname**: str = `"左搂邮箱右抱日奈"`
    - **CallName**: str = `"我要高炒了"`
    - **DevId**: str = `""`
    - **State**: int = `0`
    - **Level**: int = `90`
    - **Exp**: int = `0`
    - **Comment**: str = `""`
    - **LobbyMode**: int = `0`
    - **RepresentCharacterServerId**: int = `239093`
    - **MemoryLobbyUniqueId**: int = `0`
    - **LastConnectTime**: str = `"2026-10-11T18:25:41.208"`
    - **BirthDay**: str = `"2005-02-11T00:00:00"`
    - **CallNameUpdateTime**: str = `"0001-01-01T00:00:00"`
    - **PublisherAccountId**: int = `0`
    - **RetentionDays**: int = `0`
    - **VIPLevel**: int = `0`
    - **CreateDate**: str = `"2023-08-03T21:16:37.326"`
    - **UnReadMailCount**: int = `0`
    - **LinkRewardDateDate**: str = `"0001-01-01T00:00:00"`
    - **Location**: str = `""`
    - **LastReturningDate**: str = `"0001-01-01T00:00:00"`
  - **AccountCurrencyDB**: object
    - **AccountLevel**: int = `1`
    - **AcademyLocationRankSum**: int = `1`
    - **CurrencyDict**: object
      - …(29 keys)
    - **UpdateTimeDict**: object
      - …(19 keys)
  - **EquipmentDBs**: object
    - **6133802**: object
      - …(6 keys)
    - **6230780**: object
      - …(6 keys)
  - **ItemDBs**: object
    - **27787642**: object
      - …(5 keys)
  - **DisplaySequence**: array
    - [0] (object):
      - …(2 keys)
    - …共 5 个元素
  - **BaseAccountExp**: int = `90`
  - **AdditionalAccountExp**: int = `90`
- **Protocol**
  - `27000`
- **RequestId**
  - `"4f9ef916-c9ef-4c34-994a-eb598b9d581a"`
- **ServerNotification**
  - `3`
- **ServerTimeTicks**
  - `639273400336908799`
- **SessionKey**
  - **AccountServerId**: int = `10000000000`
  - **MxToken**: str = `"AAAAAAAA…"`
```
</details>


## /api/contentsweep/setmultisweeppreset

- **中文**: 扫荡·保存扫荡预设
- **Protocol**: 27003　**混淆名**: `PJMQ5PDLP2C2V327SVLMVAZQCY`　**样本**: 3

### 请求业务字段

| 字段 | 类型 | 示例 |
|---|---|---|
| ParcelIds | array | `[{"Type": 4, "Id": 10008}, {"Type": 4, "Id": 10014}, {"Type"…` |
| PresetId | int | `0` |
| PresetName | str | `"hard"` |
| StageIds | array | `[1102103, 1152103, 1192103]` |

### 响应 packet 顶层

- **MultiSweepPresetDBs**: array
- **Protocol**: int
- **RequestId**: str
- **ServerNotification**: int
- **ServerTimeTicks**: int
- **SessionKey**: object

<details><summary>响应结构示例（限深 3 层）</summary>

```
- **MultiSweepPresetDBs**
  - [0] (object):
    - **PresetId**: int = `0`
    - **PresetName**: str = `"hard"`
    - **StageIds**: array
      - …(array len=3)
    - **ParcelIds**: array
      - …(array len=3)
  - …共 4 个元素
- **Protocol**
  - `27003`
- **RequestId**
  - `"b617e350-3864-4595-a0f0-b7bd8e8378cf"`
- **ServerNotification**
  - `0`
- **ServerTimeTicks**
  - `639274360905543536`
- **SessionKey**
  - **AccountServerId**: int = `10000000000`
  - **MxToken**: str = `"AAAAAAAA…"`
```
</details>


# craft

## /api/craft/beginprocess

- **中文**: 制造·开始制造
- **Protocol**: 21003　**混淆名**: `X7Y43CVXU2EUC44F3J4WUMZX2A`　**样本**: 3

### 请求业务字段

| 字段 | 类型 | 示例 |
|---|---|---|
| SlotId | int | `0` |

### 响应 packet 顶层

- **CraftInfoDB**: object
- **Protocol**: int
- **RequestId**: str
- **ServerNotification**: int
- **ServerTimeTicks**: int
- **SessionKey**: object

<details><summary>响应结构示例（限深 3 层）</summary>

```
- **CraftInfoDB**
  - **SlotSequence**: int = `0`
  - **StartTime**: str = `"2026-10-12T20:54:13.222663077"`
  - **EndTime**: str = `"2026-10-13T08:54:13.222663077"`
  - **CraftSlotOpenDate**: str = `"2026-10-12T20:53:29.698"`
  - **Nodes**: array
    - [0] (object):
      - …(2 keys)
    - …共 4 个元素
- **Protocol**
  - `21003`
- **RequestId**
  - `"f3aae6a1-5c62-4392-b80d-c866bec0854a"`
- **ServerNotification**
  - `0`
- **ServerTimeTicks**
  - `639274352532232515`
- **SessionKey**
  - **AccountServerId**: int = `10000000000`
  - **MxToken**: str = `"AAAAAAAA…"`
```
</details>


## /api/craft/list

- **中文**: 制造·节点列表
- **Protocol**: 21000　**混淆名**: `LOV3E7JU62A2KCCYCL2AKHARW4`　**样本**: 6

请求无业务字段（仅标准头）。

### 响应 packet 顶层

- **CraftInfos**: array
- **PresetSlotDBs**: array
- **Protocol**: int
- **RequestId**: str
- **ServerNotification**: int
- **ServerTimeTicks**: int
- **SessionKey**: object
- **ShiftingCraftInfos**: array

<details><summary>响应结构示例（限深 3 层）</summary>

```
- **CraftInfos**
  - [0] (object):
    - **SlotSequence**: int = `0`
    - **StartTime**: str = `"2026-10-11T18:30:29.186"`
    - **EndTime**: str = `"2026-10-12T03:30:29.186"`
    - **CraftSlotOpenDate**: str = `"2026-10-11T18:30:13.774"`
    - **Nodes**: array
      - …(array len=4)
- **PresetSlotDBs**
  - (空数组)
- **Protocol**
  - `21000`
- **RequestId**
  - `"c1923071-a213-467a-bfff-dde031150b65"`
- **ServerNotification**
  - `0`
- **ServerTimeTicks**
  - `639273402296949499`
- **SessionKey**
  - **AccountServerId**: int = `10000000000`
  - **MxToken**: str = `"AAAAAAAA…"`
- **ShiftingCraftInfos**
  - (空数组)
```
</details>


## /api/craft/reward

- **中文**: 制造·领取成品
- **Protocol**: 21005　**混淆名**: `I2YDAXZGOZIYNB6HBCLBV7M3DY`　**样本**: 3

### 请求业务字段

| 字段 | 类型 | 示例 |
|---|---|---|
| SlotId | int | `0` |

### 响应 packet 顶层

- **BattlePassMissionProgressDBDict**: object
- **CraftInfos**: array
- **MissionProgressDBs**: array
- **ParcelResultDB**: object
- **Protocol**: int
- **RequestId**: str
- **ServerNotification**: int
- **ServerTimeTicks**: int
- **SessionKey**: object

<details><summary>响应结构示例（限深 3 层）</summary>

```
- **BattlePassMissionProgressDBDict**
  - **1**: array
    - [0] (object):
      - …(6 keys)
- **CraftInfos**
  - (空数组)
- **MissionProgressDBs**
  - [0] (object):
    - **AccountServerId**: int = `10000000000`
    - **MissionUniqueId**: int = `2308`
    - **Category**: int = `2`
    - **StartDate**: str = `"2026-10-12T17:09:25.927"`
    - **ProgressParameters**: object
      - …(1 keys)
- **ParcelResultDB**
  - **AccountDB**: object
    - **ServerId**: int = `10000000000`
    - **RoleId**: int = `10000000000`
    - **Nickname**: str = `"左搂邮箱右抱日奈"`
    - **CallName**: str = `"我要高炒了"`
    - **DevId**: str = `""`
    - **State**: int = `0`
    - **Level**: int = `90`
    - **Exp**: int = `0`
    - **Comment**: str = `""`
    - **LobbyMode**: int = `0`
    - **RepresentCharacterServerId**: int = `239093`
    - **MemoryLobbyUniqueId**: int = `0`
    - **LastConnectTime**: str = `"2026-10-12T20:41:00.044"`
    - **BirthDay**: str = `"2005-02-11T00:00:00"`
    - **CallNameUpdateTime**: str = `"0001-01-01T00:00:00"`
    - **PublisherAccountId**: int = `0`
    - **RetentionDays**: int = `0`
    - **VIPLevel**: int = `0`
    - **CreateDate**: str = `"2023-08-03T21:16:37.326"`
    - **UnReadMailCount**: int = `0`
    - **LinkRewardDateDate**: str = `"0001-01-01T00:00:00"`
    - **Location**: str = `""`
    - **LastReturningDate**: str = `"0001-01-01T00:00:00"`
  - **AccountCurrencyDB**: object
    - **AccountLevel**: int = `1`
    - **AcademyLocationRankSum**: int = `1`
    - **CurrencyDict**: object
      - …(29 keys)
    - **UpdateTimeDict**: object
      - …(19 keys)
  - **ItemDBs**: object
    - **11875993**: object
      - …(5 keys)
    - **1986098**: object
      - …(5 keys)
    - **27357075**: object
      - …(5 keys)
  - **DisplaySequence**: array
    - [0] (object):
      - …(2 keys)
    - …共 3 个元素
- **Protocol**
  - `21005`
- **RequestId**
  - `"dcd3673b-6df4-44bd-937d-bf9e66c01777"`
- **ServerNotification**
  - `0`
- **ServerTimeTicks**
  - `639274352032253617`
- **SessionKey**
  - **AccountServerId**: int = `10000000000`
  - **MxToken**: str = `"AAAAAAAA…"`
```
</details>


## /api/craft/selectnode

- **中文**: 制造·选择节点
- **Protocol**: 21001　**混淆名**: `2VNEHLRH6BRC3GWK4N4WQ5PMK4`　**样本**: 9

### 请求业务字段

| 字段 | 类型 | 示例 |
|---|---|---|
| LeafNodeIndex | int | `3` |
| SlotId | int | `0` |

### 响应 packet 顶层

- **Protocol**: int
- **RequestId**: str
- **SelectedNodeDB**: object
- **ServerNotification**: int
- **ServerTimeTicks**: int
- **SessionKey**: object

<details><summary>响应结构示例（限深 3 层）</summary>

```
- **Protocol**
  - `21001`
- **RequestId**
  - `"782a1e01-7080-4028-a318-be2d6012eb32"`
- **SelectedNodeDB**
  - **NodeTier**: int = `2`
  - **NodeId**: int = `112`
  - **LeafNodeIds**: array
    - (空数组)
  - **CraftNodeResult**: object
    - **NodeTier**: int = `2`
    - **ParcelInfo**: object
      - …(2 keys)
- **ServerNotification**
  - `0`
- **ServerTimeTicks**
  - `639273402229743068`
- **SessionKey**
  - **AccountServerId**: int = `10000000000`
  - **MxToken**: str = `"AAAAAAAA…"`
```
</details>


## /api/craft/updatenodelevel

- **中文**: 制造·节点升级
- **Protocol**: 21002　**混淆名**: `THDJJQA6PN3YZKVSXI73VF2AA4`　**样本**: 9

### 请求业务字段

| 字段 | 类型 | 示例 |
|---|---|---|
| ConsumeGoldAmount | int | `2000` |
| ConsumeRequestDB | object | `{"ConsumeItemServerIdAndCounts": {"1180965": 1}, "ConsumeEqu…` |
| CraftNodeType | int | `0` |
| SlotId | int | `0` |

### 响应 packet 顶层

- **AccountCurrencyDB**: object
- **ConsumeResultDB**: object
- **CraftInfoDB**: object
- **CraftNodeDB**: object
- **MissionProgressDBs**: array
- **Protocol**: int
- **RequestId**: str
- **ServerNotification**: int
- **ServerTimeTicks**: int
- **SessionKey**: object

<details><summary>响应结构示例（限深 3 层）</summary>

```
- **AccountCurrencyDB**
  - **AccountLevel**: int = `1`
  - **AcademyLocationRankSum**: int = `1`
  - **CurrencyDict**: object
    - **1**: int = `982062174`
    - **10**: int = `0`
    - **11**: int = `0`
    - **12**: int = `0`
    - **13**: int = `0`
    - **14**: int = `0`
    - **15**: int = `0`
    - **16**: int = `0`
    - **17**: int = `0`
    - **18**: int = `126675`
    - **19**: int = `40`
    - **2**: int = `0`
    - **20**: int = `40`
    - **21**: int = `40`
    - **22**: int = `0`
    - **23**: int = `0`
    - **24**: int = `0`
    - **25**: int = `4`
    - **26**: int = `0`
    - **27**: int = `0`
    - **28**: int = `0`
    - **29**: int = `0`
    - **3**: int = `154492`
    - **4**: int = `154492`
    - **5**: int = `686`
    - **6**: int = `0`
    - **7**: int = `4`
    - **8**: int = `3`
    - **9**: int = `0`
  - **UpdateTimeDict**: object
    - **12**: str = `"2026-10-11T18:30:19.459115004"`
    - **13**: str = `"2026-10-11T18:30:19.459115108"`
    - **14**: str = `"2026-10-11T18:30:19.459115211"`
    - **15**: str = `"2026-10-11T18:30:19.459115358"`
    - **16**: str = `"2026-10-11T18:30:19.459115459"`
    - **17**: str = `"2026-09-23T19:46:10.825"`
    - **19**: str = `"2026-10-11T18:30:19.459026178"`
    - **20**: str = `"2026-10-11T18:30:19.459038882"`
    - **21**: str = `"2026-10-11T18:30:19.459043948"`
    - **22**: str = `"2026-10-11T18:26:42.321"`
    - **23**: str = `"2026-10-11T18:27:13.672"`
    - **24**: str = `"2026-10-05T19:17:57.772"`
    - **25**: str = `"2026-10-05T17:57:35.375"`
    - **26**: str = `"2026-10-05T19:21:50.378"`
    - **5**: str = `"2026-10-11T18:26:50.287"`
    - **6**: str = `"2026-10-11T18:28:39.953"`
    - **7**: str = `"2026-10-11T18:27:28.695"`
    - **8**: str = `"2026-10-11T18:26:42.321"`
    - **9**: str = `"2026-10-11T18:30:19.459114837"`
- **ConsumeResultDB**
  - **RemovedItemServerIds**: array
    - (空数组)
  - **RemovedEquipmentServerIds**: null = `null`
  - **RemovedFurnitureServerIds**: null = `null`
  - **UsedItemServerIdAndRemainingCounts**: object
    - **1180965**: int = `138`
  - **UsedEquipmentServerIdAndRemainingCounts**: null = `null`
  - **UsedFurnitureServerIdAndRemainingCounts**: null = `null`
- **CraftInfoDB**
  - **SlotSequence**: int = `0`
  - **StartTime**: str = `"9999-12-31T23:59:59"`
  - **EndTime**: str = `"9999-12-31T23:59:59"`
  - **CraftSlotOpenDate**: str = `"2026-10-11T18:30:13.774"`
  - **Nodes**: array
    - [0] (object):
      - …(2 keys)
    - …共 2 个元素
- **CraftNodeDB**
  - **NodeTier**: int = `1`
  - **NodeId**: int = `10`
  - **NodeLevel**: int = `1`
  - **LeafNodeIds**: array
    - [0] (int):
      - `23`
    - …共 5 个元素
  - **CraftNodeResult**: object
    - **NodeTier**: int = `1`
    - **ParcelInfo**: object
      - …(2 keys)
- **MissionProgressDBs**
  - [0] (object):
    - **AccountServerId**: int = `10000000000`
    - **MissionUniqueId**: int = `82129`
    - **Category**: int = `3`
    - **StartDate**: str = `"2026-08-21T22:11:16.317"`
    - **ProgressParameters**: object
      - …(1 keys)
- **Protocol**
  - `21002`
- **RequestId**
  - `"a9f839bd-bdfc-4f74-b73b-233f2310a0d8"`
- **ServerNotification**
  - `0`
- **ServerTimeTicks**
  - `639273402194627478`
- **SessionKey**
  - **AccountServerId**: int = `10000000000`
  - **MxToken**: str = `"AAAAAAAA…"`
```
</details>


# echelon

## /api/echelon/list

- **中文**: 编队·列表
- **Protocol**: 5000　**混淆名**: `ED653MDBZL75ADU4XKIFERNVVI`　**样本**: 8

请求无业务字段（仅标准头）。

### 响应 packet 顶层

- **EchelonDBs**: array
- **Protocol**: int
- **RequestId**: str
- **ServerNotification**: int
- **ServerTimeTicks**: int
- **SessionKey**: object

<details><summary>响应结构示例（限深 3 层）</summary>

```
- **EchelonDBs**
  - [0] (object):
    - **AccountServerId**: int = `10000000000`
    - **EchelonType**: int = `1`
    - **EchelonNumber**: int = `1`
    - **ExtensionType**: int = `0`
    - **LeaderServerId**: int = `1385885`
    - **MainSlotServerIds**: array
      - …(array len=4)
    - **SupportSlotServerIds**: array
      - …(array len=2)
    - **TSSInteractionServerId**: int = `0`
    - **UsingFlag**: int = `0`
    - **SkillCardMulliganCharacterIds**: array
      - …(array len=3)
    - **CombatStyleIndex**: array
      - …(array len=6)
  - …共 42 个元素
- **Protocol**
  - `5000`
- **RequestId**
  - `"3632b623-de04-48bc-a789-44b7981754e1"`
- **ServerNotification**
  - `0`
- **ServerTimeTicks**
  - `639273400468014014`
- **SessionKey**
  - **AccountServerId**: int = `10000000000`
  - **MxToken**: str = `"AAAAAAAA…"`
```
</details>


## /api/echelon/save

- **中文**: 编队·保存
- **Protocol**: 5001　**混淆名**: `H3S5EPFZOXKUGXLXC2VFAVMQIU`　**样本**: 4

### 请求业务字段

| 字段 | 类型 | 示例 |
|---|---|---|
| AssistUseInfos | null | `null` |
| EchelonDB | object | `{"AccountServerId": 10000000000, "EchelonType": 3, "EchelonN…` |
| IsPractice | bool | `false` |

### 响应 packet 顶层

- **EchelonDB**: object
- **Protocol**: int
- **RequestId**: str
- **ServerNotification**: int
- **ServerTimeTicks**: int
- **SessionKey**: object

<details><summary>响应结构示例（限深 3 层）</summary>

```
- **EchelonDB**
  - **AccountServerId**: int = `10000000000`
  - **EchelonType**: int = `3`
  - **EchelonNumber**: int = `1`
  - **ExtensionType**: int = `0`
  - **LeaderServerId**: int = `770403`
  - **MainSlotServerIds**: array
    - [0] (int):
      - `239093`
    - …共 4 个元素
  - **SupportSlotServerIds**: array
    - [0] (int):
      - `2439641`
    - …共 2 个元素
  - **TSSInteractionServerId**: int = `0`
  - **UsingFlag**: int = `0`
  - **SkillCardMulliganCharacterIds**: array
    - [0] (int):
      - `0`
    - …共 3 个元素
  - **CombatStyleIndex**: array
    - [0] (int):
      - `0`
    - …共 6 个元素
- **Protocol**
  - `5001`
- **RequestId**
  - `"b20c2a01-1095-4fd8-9e5c-8e96a39dc25a"`
- **ServerNotification**
  - `0`
- **ServerTimeTicks**
  - `639274353134636182`
- **SessionKey**
  - **AccountServerId**: int = `10000000000`
  - **MxToken**: str = `"AAAAAAAA…"`
```
</details>


# event

## /api/event/rewardincrease

- **中文**: 账号加成信息（掉落/经验加成，刷界面时高频）
- **Protocol**: 25003　**混淆名**: `ME6ZY2KZLN5UN4DF7BT3TKJKHI`　**样本**: 142

请求无业务字段（仅标准头）。

### 响应 packet 顶层

- **EventRewardIncreaseDBs**: array
- **Protocol**: int
- **RequestId**: str
- **ServerNotification**: int
- **ServerTimeTicks**: int
- **SessionKey**: object

<details><summary>响应结构示例（限深 3 层）</summary>

```
- **EventRewardIncreaseDBs**
  - [0] (object):
    - **EventTargetType**: int = `5`
    - **RewardRealType**: int = `100461`
    - **Multiplier**: object
      - …(1 keys)
    - **BeginDate**: str = `"2026-10-08T04:00:00"`
    - **EndDate**: str = `"2026-10-15T03:59:59"`
  - …共 3 个元素
- **Protocol**
  - `25003`
- **RequestId**
  - `"5f365f5b-18f4-475f-9c08-4d496c81988b"`
- **ServerNotification**
  - `0`
- **ServerTimeTicks**
  - `639273396130842374`
- **SessionKey**
  - **AccountServerId**: int = `10016071938`
  - **MxToken**: str = `"wc4dt5o4…"`
```
</details>


# eventcontent

## /api/eventcontent/adventurelist

- **中文**: 活动·关卡列表
- **Protocol**: 30000　**混淆名**: `WOHXJTASLD5AAJI3DIGMH7O24U`　**样本**: 16

### 请求业务字段

| 字段 | 类型 | 示例 |
|---|---|---|
| EventContentId | int | `10836` |

### 响应 packet 顶层

- **AlreadyReceiveRewardId**: array
- **EventContentBonusRewardDBs**: array
- **Protocol**: int
- **RequestId**: str
- **ServerNotification**: int
- **ServerTimeTicks**: int
- **SessionKey**: object
- **StageHistoryDBs**: array
- **StagePoint**: int
- **StrategyObjecthistoryDBs**: array

<details><summary>响应结构示例（限深 3 层）</summary>

```
- **AlreadyReceiveRewardId**
  - (空数组)
- **EventContentBonusRewardDBs**
  - [0] (object):
    - **EventContentId**: int = `801`
    - **EventStageUniqueId**: int = `8011301`
    - **BonusPercentage**: int = `0`
    - **BonusParcelInfo**: object
      - …(2 keys)
  - …共 1136 个元素
- **Protocol**
  - `30000`
- **RequestId**
  - `"e67d8cc2-9064-4f17-8fe3-0a7e70ea2ef7"`
- **ServerNotification**
  - `0`
- **ServerTimeTicks**
  - `639273402615668512`
- **SessionKey**
  - **AccountServerId**: int = `10000000000`
  - **MxToken**: str = `"AAAAAAAA…"`
- **StageHistoryDBs**
  - [0] (object):
    - **AccountServerId**: int = `10000000000`
    - **StoryUniqueId**: int = `0`
    - **ChapterUniqueId**: int = `0`
    - **StageUniqueId**: int = `101140`
    - **TodayPlayCount**: int = `0`
    - **LastPlay**: str = `"2024-12-30T20:06:55.802"`
    - **FirstClearRewardReceive**: str = `"0001-01-01T00:00:00"`
    - **StarRewardReceive**: str = `"0001-01-01T00:00:00"`
  - …共 2149 个元素
- **StagePoint**
  - `0`
- **StrategyObjecthistoryDBs**
  - [0] (object):
    - **AccountId**: int = `10000000000`
    - **StrategyObjectId**: int = `1012101`
  - …共 57 个元素
```
</details>


## /api/eventcontent/collectionlist

- **中文**: 活动·收集进度
- **Protocol**: 30025　**混淆名**: `HG4HUMWCUOMWCEHBRJTX2H7AUI`　**样本**: 14

### 请求业务字段

| 字段 | 类型 | 示例 |
|---|---|---|
| EventContentId | int | `848` |
| GroupId | null | `null` |

### 响应 packet 顶层

- **EventContentUnlockCGDBs**: array
- **Protocol**: int
- **RequestId**: str
- **ServerNotification**: int
- **ServerTimeTicks**: int
- **SessionKey**: object

<details><summary>响应结构示例（限深 3 层）</summary>

```
- **EventContentUnlockCGDBs**
  - (空数组)
- **Protocol**
  - `30025`
- **RequestId**
  - `"4d99882b-5f27-46b1-8a69-d01467eea21d"`
- **ServerNotification**
  - `0`
- **ServerTimeTicks**
  - `639273396111403026`
- **SessionKey**
  - **AccountServerId**: int = `10016071938`
  - **MxToken**: str = `"wc4dt5o4…"`
```
</details>


## /api/eventcontent/enterstorystage

- **中文**: 活动·进入剧情关
- **Protocol**: 30036　**混淆名**: `XUCQ3BUDYXA2J73LI6YUZ5CSCU`　**样本**: 3

### 请求业务字段

| 字段 | 类型 | 示例 |
|---|---|---|
| EventContentId | int | `10836` |
| StageUniqueId | int | `108361301` |

### 响应 packet 顶层

- **ParcelResultDB**: object
- **Protocol**: int
- **RandomSeed**: int
- **RequestId**: str
- **SaveDataDB**: object
- **ServerNotification**: int
- **ServerTimeTicks**: int
- **SessionKey**: object

<details><summary>响应结构示例（限深 3 层）</summary>

```
- **ParcelResultDB**
  - **AccountCurrencyDB**: object
    - **AccountLevel**: int = `1`
    - **AcademyLocationRankSum**: int = `1`
    - **CurrencyDict**: object
      - …(29 keys)
    - **UpdateTimeDict**: object
      - …(19 keys)
- **Protocol**
  - `30036`
- **RandomSeed**
  - `4530073`
- **RequestId**
  - `"7715f91e-e39b-44a6-b465-7af78f52d5dd"`
- **SaveDataDB**
  - **AccountServerId**: int = `10000000000`
  - **CreateTime**: str = `"2026-10-13T16:31:56.741126811"`
  - **StageUniqueId**: int = `108361302`
  - **ContentType**: int = `12`
  - **StageEntranceFee**: array
    - [0] (object):
      - …(2 keys)
  - **EnemyInfos**: null = `null`
  - **EchelonInfos**: null = `null`
  - **DeployedEchelonInfos**: null = `null`
  - **RandomSeed**: int = `0`
- **ServerNotification**
  - `0`
- **ServerTimeTicks**
  - `639275059167454055`
- **SessionKey**
  - **AccountServerId**: int = `10000000000`
  - **MxToken**: str = `"AAAAAAAA…"`
```
</details>


## /api/eventcontent/scenariogrouphistoryupdate

- **中文**: 活动·剧情历史更新
- **Protocol**: 30027　**混淆名**: `AFSSTHWPFDRFY5HB4UARYGHQFM`　**样本**: 3

### 请求业务字段

| 字段 | 类型 | 示例 |
|---|---|---|
| EventContentId | int | `10836` |
| ScenarioGroupUniqueId | int | `10034010` |
| ScenarioType | int | `6` |

### 响应 packet 顶层

- **ParcelResultDB**: object
- **Protocol**: int
- **RequestId**: str
- **ScenarioGroupHistoryDBs**: array
- **ServerNotification**: int
- **ServerTimeTicks**: int
- **SessionKey**: object

<details><summary>响应结构示例（限深 3 层）</summary>

```
- **ParcelResultDB**
  - **AccountDB**: object
    - **ServerId**: int = `10000000000`
    - **RoleId**: int = `10000000000`
    - **Nickname**: str = `"左搂邮箱右抱日奈"`
    - **CallName**: str = `"我要高炒了"`
    - **DevId**: str = `""`
    - **State**: int = `0`
    - **Level**: int = `90`
    - **Exp**: int = `0`
    - **Comment**: str = `""`
    - **LobbyMode**: int = `0`
    - **RepresentCharacterServerId**: int = `239093`
    - **MemoryLobbyUniqueId**: int = `0`
    - **LastConnectTime**: str = `"2026-10-13T16:14:35.766"`
    - **BirthDay**: str = `"2005-02-11T00:00:00"`
    - **CallNameUpdateTime**: str = `"0001-01-01T00:00:00"`
    - **PublisherAccountId**: int = `0`
    - **RetentionDays**: int = `0`
    - **VIPLevel**: int = `0`
    - **CreateDate**: str = `"2023-08-03T21:16:37.326"`
    - **UnReadMailCount**: int = `0`
    - **LinkRewardDateDate**: str = `"0001-01-01T00:00:00"`
    - **Location**: str = `""`
    - **LastReturningDate**: str = `"0001-01-01T00:00:00"`
  - **AccountCurrencyDB**: object
    - **AccountLevel**: int = `1`
    - **AcademyLocationRankSum**: int = `1`
    - **CurrencyDict**: object
      - …(29 keys)
    - **UpdateTimeDict**: object
      - …(19 keys)
- **Protocol**
  - `30027`
- **RequestId**
  - `"d3919593-e066-459c-9fcd-ea486182e001"`
- **ScenarioGroupHistoryDBs**
  - [0] (object):
    - **AccountServerId**: int = `10000000000`
    - **ScenarioGroupUniqueId**: int = `60`
    - **ScenarioType**: int = `6`
    - **EventContentId**: int = `70000`
    - **ClearDateTime**: str = `"2026-06-11T19:56:15.937"`
    - **IsReturn**: bool = `false`
    - **IsPermanent**: bool = `false`
  - …共 1096 个元素
- **ServerNotification**
  - `0`
- **ServerTimeTicks**
  - `639275059242230611`
- **SessionKey**
  - **AccountServerId**: int = `10000000000`
  - **MxToken**: str = `"AAAAAAAA…"`
```
</details>


## /api/eventcontent/shopbuymerchandise

- **中文**: 活动·商店购买
- **Protocol**: 30019　**混淆名**: `NTR7V3HURPQCNSI2UK3GYWN6NE`　**样本**: 16

### 请求业务字段

| 字段 | 类型 | 示例 |
|---|---|---|
| EventContentId | int | `10836` |
| GoodsUniqueId | int | `62811` |
| IsRefreshMerchandise | bool | `false` |
| PurchaseCount | int | `6` |
| ShopUniqueId | int | `108360011` |

### 响应 packet 顶层

- **AccountCurrencyDB**: object
- **ConsumeResultDB**: object
- **EventContentCollectionDBs**: null
- **MailDB**: null
- **ParcelResultDB**: object
- **Protocol**: int
- **RequestId**: str
- **ServerNotification**: int
- **ServerTimeTicks**: int
- **SessionKey**: object
- **ShopProductDB**: object

<details><summary>响应结构示例（限深 3 层）</summary>

```
- **AccountCurrencyDB**
  - **AccountLevel**: int = `1`
  - **AcademyLocationRankSum**: int = `1`
  - **CurrencyDict**: object
    - **1**: int = `980648081`
    - **10**: int = `0`
    - **11**: int = `0`
    - **12**: int = `0`
    - **13**: int = `0`
    - **14**: int = `0`
    - **15**: int = `0`
    - **16**: int = `0`
    - **17**: int = `0`
    - **18**: int = `128665`
    - **19**: int = `40`
    - **2**: int = `0`
    - **20**: int = `40`
    - **21**: int = `40`
    - **22**: int = `0`
    - **23**: int = `0`
    - **24**: int = `0`
    - **25**: int = `4`
    - **26**: int = `0`
    - **27**: int = `0`
    - **28**: int = `0`
    - **29**: int = `0`
    - **3**: int = `154542`
    - **4**: int = `154542`
    - **5**: int = `10`
    - **6**: int = `0`
    - **7**: int = `4`
    - **8**: int = `3`
    - **9**: int = `0`
  - **UpdateTimeDict**: object
    - **12**: str = `"2026-10-12T20:56:14.163277463"`
    - **13**: str = `"2026-10-12T20:56:14.163277585"`
    - **14**: str = `"2026-10-12T20:56:14.16327769"`
    - **15**: str = `"2026-10-12T20:56:14.163277855"`
    - **16**: str = `"2026-10-12T20:56:14.163277957"`
    - **17**: str = `"2026-09-23T19:46:10.825"`
    - **19**: str = `"2026-10-12T20:56:14.163183582"`
    - **20**: str = `"2026-10-12T20:56:14.163192638"`
    - **21**: str = `"2026-10-12T20:56:14.163197564"`
    - **22**: str = `"2026-10-12T20:54:38.785"`
    - **23**: str = `"2026-10-12T20:54:58.796"`
    - **24**: str = `"2026-10-05T19:17:57.772"`
    - **25**: str = `"2026-10-05T17:57:35.375"`
    - **26**: str = `"2026-10-05T19:21:50.378"`
    - **5**: str = `"2026-10-12T20:55:58.833"`
    - **6**: str = `"2026-10-12T20:44:54.769"`
    - **7**: str = `"2026-10-12T20:55:13.954"`
    - **8**: str = `"2026-10-12T20:44:54.769"`
    - **9**: str = `"2026-10-12T20:56:14.163277271"`
- **ConsumeResultDB**
  - **RemovedItemServerIds**: array
    - (空数组)
  - **RemovedEquipmentServerIds**: null = `null`
  - **RemovedFurnitureServerIds**: null = `null`
  - **UsedItemServerIdAndRemainingCounts**: object
    - **27788869**: int = `5912`
  - **UsedEquipmentServerIdAndRemainingCounts**: null = `null`
  - **UsedFurnitureServerIdAndRemainingCounts**: null = `null`
- **EventContentCollectionDBs**
  - `null`
- **MailDB**
  - `null`
- **ParcelResultDB**
  - **AccountDB**: object
    - **ServerId**: int = `10000000000`
    - **RoleId**: int = `10000000000`
    - **Nickname**: str = `"左搂邮箱右抱日奈"`
    - **CallName**: str = `"我要高炒了"`
    - **DevId**: str = `""`
    - **State**: int = `0`
    - **Level**: int = `90`
    - **Exp**: int = `0`
    - **Comment**: str = `""`
    - **LobbyMode**: int = `0`
    - **RepresentCharacterServerId**: int = `239093`
    - **MemoryLobbyUniqueId**: int = `0`
    - **LastConnectTime**: str = `"2026-10-12T20:41:00.044"`
    - **BirthDay**: str = `"2005-02-11T00:00:00"`
    - **CallNameUpdateTime**: str = `"0001-01-01T00:00:00"`
    - **PublisherAccountId**: int = `0`
    - **RetentionDays**: int = `0`
    - **VIPLevel**: int = `0`
    - **CreateDate**: str = `"2023-08-03T21:16:37.326"`
    - **UnReadMailCount**: int = `0`
    - **LinkRewardDateDate**: str = `"0001-01-01T00:00:00"`
    - **Location**: str = `""`
    - **LastReturningDate**: str = `"0001-01-01T00:00:00"`
  - **AccountCurrencyDB**: object
    - **AccountLevel**: int = `1`
    - **AcademyLocationRankSum**: int = `1`
    - **CurrencyDict**: object
      - …(29 keys)
    - **UpdateTimeDict**: object
      - …(19 keys)
  - **ItemDBs**: object
    - **21064949**: object
      - …(5 keys)
  - **DisplaySequence**: array
    - [0] (object):
      - …(2 keys)
- **Protocol**
  - `30019`
- **RequestId**
  - `"02768aae-99de-4e28-b4f5-58fd79d61b0e"`
- **ServerNotification**
  - `0`
- **ServerTimeTicks**
  - `639274353741636259`
- **SessionKey**
  - **AccountServerId**: int = `10000000000`
  - **MxToken**: str = `"AAAAAAAA…"`
- **ShopProductDB**
  - **EventContentId**: int = `10836`
  - **ShopExcelId**: int = `108360015`
  - **Category**: int = `13`
  - **DisplayOrder**: int = `16`
  - **PurchaseCount**: int = `6`
  - **SoldOut**: bool = `false`
  - **PurchaseCountLimit**: int = `6`
  - **Price**: int = `0`
  - **ProductType**: int = `0`
```
</details>


## /api/eventcontent/shoplist

- **中文**: 活动·商店列表
- **Protocol**: 30014　**混淆名**: `DMROW5QG2MTBCAS3PPKF4ZCHRU`　**样本**: 1

### 请求业务字段

| 字段 | 类型 | 示例 |
|---|---|---|
| CategoryList | array | `[13, 14, 15]` |
| EventContentId | int | `10836` |

### 响应 packet 顶层

- **Protocol**: int
- **RequestId**: str
- **ServerNotification**: int
- **ServerTimeTicks**: int
- **SessionKey**: object
- **ShopInfos**: array

<details><summary>响应结构示例（限深 3 层）</summary>

```
- **Protocol**
  - `30014`
- **RequestId**
  - `"ae673380-0f97-43f3-a53b-f08cad462a97"`
- **ServerNotification**
  - `0`
- **ServerTimeTicks**
  - `639274353647765211`
- **SessionKey**
  - **AccountServerId**: int = `10000000000`
  - **MxToken**: str = `"AAAAAAAA…"`
- **ShopInfos**
  - [0] (object):
    - **EventContentId**: int = `10836`
    - **Category**: int = `13`
    - **ShopGroupType**: int = `0`
    - **ManualRefreshCount**: null = `null`
    - **IsRefresh**: bool = `false`
    - **NextAutoRefreshDate**: null = `null`
    - **LastAutoRefreshDate**: null = `null`
    - **ShopProductList**: array
      - …(array len=19)
  - …共 3 个元素
```
</details>


## /api/eventcontent/storystageresult

- **中文**: 活动·剧情关结算
- **Protocol**: 30037　**混淆名**: `SYYBT5B4W6SS2Y6NLQ6SE62JZU`　**样本**: 3

### 请求业务字段

| 字段 | 类型 | 示例 |
|---|---|---|
| EventContentId | int | `10836` |
| StageUniqueId | int | `108361301` |

### 响应 packet 顶层

- **CampaignStageHistoryDB**: object
- **EventContentCollectionDBs**: null
- **EventMissionProgressDBDict**: object
- **FirstClearReward**: array
- **MissionProgressDBs**: array
- **ParcelResultDB**: object
- **Protocol**: int
- **RequestId**: str
- **ServerNotification**: int
- **ServerTimeTicks**: int
- **SessionKey**: object

<details><summary>响应结构示例（限深 3 层）</summary>

```
- **CampaignStageHistoryDB**
  - **AccountServerId**: int = `10000000000`
  - **StoryUniqueId**: int = `0`
  - **ChapterUniqueId**: int = `0`
  - **StageUniqueId**: int = `108361302`
  - **ClearTurnRecord**: int = `1`
  - **TodayPlayCount**: int = `1`
  - **LastPlay**: str = `"2026-10-13T16:32:04.650562638"`
  - **FirstClearRewardReceive**: str = `"2026-10-13T16:32:04.650562638"`
  - **StarRewardReceive**: str = `"0001-01-01T00:00:00"`
- **EventContentCollectionDBs**
  - `null`
- **EventMissionProgressDBDict**
  - **10836**: array
    - [0] (object):
      - …(5 keys)
- **FirstClearReward**
  - [0] (object):
    - **Key**: object
      - …(2 keys)
    - **Amount**: int = `15`
  - …共 3 个元素
- **MissionProgressDBs**
  - [0] (object):
    - **AccountServerId**: int = `10000000000`
    - **MissionUniqueId**: int = `82029`
    - **Category**: int = `3`
    - **StartDate**: str = `"2026-04-09T20:22:43.391"`
    - **ProgressParameters**: object
      - …(1 keys)
- **ParcelResultDB**
  - **AccountDB**: object
    - **ServerId**: int = `10000000000`
    - **RoleId**: int = `10000000000`
    - **Nickname**: str = `"左搂邮箱右抱日奈"`
    - **CallName**: str = `"我要高炒了"`
    - **DevId**: str = `""`
    - **State**: int = `0`
    - **Level**: int = `90`
    - **Exp**: int = `0`
    - **Comment**: str = `""`
    - **LobbyMode**: int = `0`
    - **RepresentCharacterServerId**: int = `239093`
    - **MemoryLobbyUniqueId**: int = `0`
    - **LastConnectTime**: str = `"2026-10-13T16:14:35.766"`
    - **BirthDay**: str = `"2005-02-11T00:00:00"`
    - **CallNameUpdateTime**: str = `"0001-01-01T00:00:00"`
    - **PublisherAccountId**: int = `0`
    - **RetentionDays**: int = `0`
    - **VIPLevel**: int = `0`
    - **CreateDate**: str = `"2023-08-03T21:16:37.326"`
    - **UnReadMailCount**: int = `0`
    - **LinkRewardDateDate**: str = `"0001-01-01T00:00:00"`
    - **Location**: str = `""`
    - **LastReturningDate**: str = `"0001-01-01T00:00:00"`
  - **AccountCurrencyDB**: object
    - **AccountLevel**: int = `1`
    - **AcademyLocationRankSum**: int = `1`
    - **CurrencyDict**: object
      - …(29 keys)
    - **UpdateTimeDict**: object
      - …(19 keys)
  - **ItemDBs**: object
    - **27787642**: object
      - …(5 keys)
    - **27788868**: object
      - …(5 keys)
    - **27788870**: object
      - …(5 keys)
    - **6884060**: object
      - …(5 keys)
  - **DisplaySequence**: array
    - [0] (object):
      - …(2 keys)
    - …共 7 个元素
  - **BaseAccountExp**: int = `10`
- **Protocol**
  - `30037`
- **RequestId**
  - `"ca3564d0-3445-463e-b561-52432559c3e2"`
- **ServerNotification**
  - `0`
- **ServerTimeTicks**
  - `639275059246681776`
- **SessionKey**
  - **AccountServerId**: int = `10000000000`
  - **MxToken**: str = `"AAAAAAAA…"`
```
</details>


# friend

## /api/friend/check

- **中文**: 好友·状态检查
- **Protocol**: 43010　**混淆名**: `TAGMSXJIONDD5CVTS52LJXSDNQ`　**样本**: 43

请求无业务字段（仅标准头）。

### 响应 packet 顶层

- **Protocol**: int
- **RequestId**: str
- **ServerNotification**: int
- **ServerTimeTicks**: int
- **SessionKey**: object

<details><summary>响应结构示例（限深 3 层）</summary>

```
- **Protocol**
  - `43010`
- **RequestId**
  - `"404dcc52-14e2-4ab4-91da-082c309ce481"`
- **ServerNotification**
  - `0`
- **ServerTimeTicks**
  - `639273398820523364`
- **SessionKey**
  - **AccountServerId**: int = `10016071938`
  - **MxToken**: str = `"wc4dt5o4…"`
```
</details>


# item

## /api/item/list

- **中文**: 道具·列表
- **Protocol**: 4000　**混淆名**: `DGOYM2RERJJ7JIGHWVF7UZ5XPA`　**样本**: 5

请求无业务字段（仅标准头）。

### 响应 packet 顶层

- **ExpiryItemDBs**: array
- **ItemDBs**: array
- **Protocol**: int
- **RequestId**: str
- **ServerNotification**: int
- **ServerTimeTicks**: int
- **SessionKey**: object

<details><summary>响应结构示例（限深 3 层）</summary>

```
- **ExpiryItemDBs**
  - (空数组)
- **ItemDBs**
  - [0] (object):
    - **Type**: int = `4`
    - **ServerId**: int = `426738`
    - **UniqueId**: int = `2`
    - **StackCount**: int = `2210`
    - **IsNew**: bool = `false`
  - …共 587 个元素
- **Protocol**
  - `4000`
- **RequestId**
  - `"1300d33a-6ed4-46ea-87b8-318e62fc377f"`
- **ServerNotification**
  - `0`
- **ServerTimeTicks**
  - `639273399436001798`
- **SessionKey**
  - **AccountServerId**: int = `10000000000`
  - **MxToken**: str = `"AAAAAAAA…"`
```
</details>


# mail

## /api/mail/check

- **中文**: 邮件·未读检查
- **Protocol**: 7001　**混淆名**: `A6XU5ZVL4DWGSYCQFZKU5ILQVY`　**样本**: 63

请求无业务字段（仅标准头）。

### 响应 packet 顶层

- **Count**: int
- **Protocol**: int
- **RequestId**: str
- **ServerNotification**: int
- **ServerTimeTicks**: int
- **SessionKey**: object

<details><summary>响应结构示例（限深 3 层）</summary>

```
- **Count**
  - `4`
- **Protocol**
  - `7001`
- **RequestId**
  - `"7127719d-e4a4-4668-8c9d-63c04e66ddca"`
- **ServerNotification**
  - `8`
- **ServerTimeTicks**
  - `639273398815498815`
- **SessionKey**
  - **AccountServerId**: int = `10016071938`
  - **MxToken**: str = `"wc4dt5o4…"`
```
</details>


## /api/mail/list

- **中文**: 邮件·列表
- **Protocol**: 7000　**混淆名**: `URZSRU73NZ7TFCFVHVORFXNFSE`　**样本**: 6

### 请求业务字段

| 字段 | 类型 | 示例 |
|---|---|---|
| IsDescending | bool | `true` |
| IsReadMail | bool | `false` |
| PivotIndex | int | `0` |
| PivotTime | str | `"9999-12-31T23:59:59"` |
| mailSortingRule | int | `0` |

### 响应 packet 顶层

- **Count**: int
- **MailDBs**: array
- **Protocol**: int
- **RequestId**: str
- **ServerNotification**: int
- **ServerTimeTicks**: int
- **SessionKey**: object

<details><summary>响应结构示例（限深 3 层）</summary>

```
- **Count**
  - `0`
- **MailDBs**
  - (空数组)
- **Protocol**
  - `7000`
- **RequestId**
  - `"20420ba4-6e00-4730-8a2a-01828153a513"`
- **ServerNotification**
  - `0`
- **ServerTimeTicks**
  - `639273403309886894`
- **SessionKey**
  - **AccountServerId**: int = `10000000000`
  - **MxToken**: str = `"AAAAAAAA…"`
```
</details>


## /api/mail/listsemipermanent

- **中文**: 邮件·永久邮箱列表
- **Protocol**: 7003　**混淆名**: `6MI4R4QVPYBZU5UU3FHCSUQECY`　**样本**: 3

### 请求业务字段

| 字段 | 类型 | 示例 |
|---|---|---|
| IsDescending | bool | `true` |
| IsReadMail | bool | `false` |
| PivotIndex | int | `0` |
| PivotTime | str | `"9999-12-31T23:59:59"` |
| mailSortingRule | int | `0` |

### 响应 packet 顶层

- **Protocol**: int
- **RequestId**: str
- **ServerNotification**: int
- **ServerTimeTicks**: int
- **SessionKey**: object

<details><summary>响应结构示例（限深 3 层）</summary>

```
- **Protocol**
  - `7003`
- **RequestId**
  - `"e02ebab8-d8bb-47fe-900e-bc4836d5aedf"`
- **ServerNotification**
  - `0`
- **ServerTimeTicks**
  - `639274361049505993`
- **SessionKey**
  - **AccountServerId**: int = `10000000000`
  - **MxToken**: str = `"AAAAAAAA…"`
```
</details>


## /api/mail/receive

- **中文**: 邮件·领取附件
- **Protocol**: 7002　**混淆名**: `X3CP3SJNLNSPJAUT24VJ6UZAJA`　**样本**: 3

### 请求业务字段

| 字段 | 类型 | 示例 |
|---|---|---|
| MailServerIds | array | `[20729178, 20729153]` |

### 响应 packet 顶层

- **BattlePassInfoDBs**: null
- **MailServerIds**: array
- **MissionProgressDBs**: array
- **ParcelResultDB**: object
- **Protocol**: int
- **RequestId**: str
- **ServerNotification**: int
- **ServerTimeTicks**: int
- **SessionKey**: object

<details><summary>响应结构示例（限深 3 层）</summary>

```
- **BattlePassInfoDBs**
  - `null`
- **MailServerIds**
  - [0] (int):
    - `20737724`
  - …共 3 个元素
- **MissionProgressDBs**
  - [0] (object):
    - **AccountServerId**: int = `10000000000`
    - **MissionUniqueId**: int = `82029`
    - **Category**: int = `3`
    - **StartDate**: str = `"2026-04-09T20:22:43.391"`
    - **ProgressParameters**: object
      - …(1 keys)
- **ParcelResultDB**
  - **AccountDB**: object
    - **ServerId**: int = `10000000000`
    - **RoleId**: int = `10000000000`
    - **Nickname**: str = `"左搂邮箱右抱日奈"`
    - **CallName**: str = `"我要高炒了"`
    - **DevId**: str = `""`
    - **State**: int = `0`
    - **Level**: int = `90`
    - **Exp**: int = `0`
    - **Comment**: str = `""`
    - **LobbyMode**: int = `0`
    - **RepresentCharacterServerId**: int = `239093`
    - **MemoryLobbyUniqueId**: int = `0`
    - **LastConnectTime**: str = `"2026-10-12T20:41:00.044"`
    - **BirthDay**: str = `"2005-02-11T00:00:00"`
    - **CallNameUpdateTime**: str = `"0001-01-01T00:00:00"`
    - **PublisherAccountId**: int = `0`
    - **RetentionDays**: int = `0`
    - **VIPLevel**: int = `0`
    - **CreateDate**: str = `"2023-08-03T21:16:37.326"`
    - **UnReadMailCount**: int = `0`
    - **LinkRewardDateDate**: str = `"0001-01-01T00:00:00"`
    - **Location**: str = `""`
    - **LastReturningDate**: str = `"0001-01-01T00:00:00"`
  - **AccountCurrencyDB**: object
    - **AccountLevel**: int = `1`
    - **AcademyLocationRankSum**: int = `1`
    - **CurrencyDict**: object
      - …(29 keys)
    - **UpdateTimeDict**: object
      - …(19 keys)
  - **ItemDBs**: object
    - **1443971**: object
      - …(5 keys)
  - **DisplaySequence**: array
    - [0] (object):
      - …(2 keys)
    - …共 3 个元素
- **Protocol**
  - `7002`
- **RequestId**
  - `"e53564a2-3bb0-4bbe-95e7-8e6d6fd81ab6"`
- **ServerNotification**
  - `0`
- **ServerTimeTicks**
  - `639274361058779521`
- **SessionKey**
  - **AccountServerId**: int = `10000000000`
  - **MxToken**: str = `"AAAAAAAA…"`
```
</details>


# management

## /api/management/data

- **中文**: 主界面数据（管理局汇总）
- **Protocol**: 90004　**混淆名**: `XJER6O4J52SF7TFS6WLCFJNDIM`　**样本**: 55

请求无业务字段（仅标准头）。

### 响应 packet 顶层

- **Data**: object
- **ErrorCode**: int
- **Protocol**: int
- **Reason**: str
- **RequestId**: str
- **ServerNotification**: int
- **ServerTimeTicks**: int
- **SessionKey**: object

<details><summary>响应结构示例（限深 3 层）</summary>

```
- **Data**
  - **Notices**: array
    - [0] (object):
      - …(6 keys)
    - …共 6 个元素
  - **Events**: array
    - [0] (object):
      - …(6 keys)
    - …共 18 个元素
  - **Issues**: array
    - (空数组)
  - **Banners**: array
    - [0] (object):
      - …(10 keys)
    - …共 7 个元素
  - **GachaProbabilityDisplay**: array
    - [0] (object):
      - …(4 keys)
    - …共 11 个元素
  - **GuidePopup**: array
    - (空数组)
  - **GachaPeriodDisplay**: null = `null`
  - **RaidPeriodDisplay**: null = `null`
  - **Survey**: null = `null`
- **ErrorCode**
  - `33004`
- **Protocol**
  - `90004`
- **Reason**
  - `"request_id does not match"`
- **RequestId**
  - `"55e2677d-5ac4-41ed-9e94-3b0329eb8374"`
- **ServerNotification**
  - `0`
- **ServerTimeTicks**
  - `639273396136860037`
- **SessionKey**
  - **AccountServerId**: int = `10016071938`
  - **MxToken**: str = `"wc4dt5o4…"`
```
</details>


# minigame

## /api/minigame/missionlist

- **中文**: 小游戏·任务列表
- **Protocol**: 35003　**混淆名**: `ECS6DZHQ3DFT6SL2CNYHYECQ4A`　**样本**: 5

### 请求业务字段

| 字段 | 类型 | 示例 |
|---|---|---|
| EventContentId | int | `10836` |

### 响应 packet 顶层

- **ClearedOrignalMissionIds**: null
- **MissionHistoryUniqueIds**: array
- **ProgressDBs**: array
- **Protocol**: int
- **RequestId**: str
- **ServerNotification**: int
- **ServerTimeTicks**: int
- **SessionKey**: object

<details><summary>响应结构示例（限深 3 层）</summary>

```
- **ClearedOrignalMissionIds**
  - `null`
- **MissionHistoryUniqueIds**
  - (空数组)
- **ProgressDBs**
  - [0] (object):
    - **AccountServerId**: int = `10000000000`
    - **MissionUniqueId**: int = `108360000`
    - **Category**: int = `7`
    - **StartDate**: str = `"2026-10-08T21:33:13.446"`
    - **ProgressParameters**: object
      - …(2 keys)
  - …共 44 个元素
- **Protocol**
  - `35003`
- **RequestId**
  - `"3e5f88e1-00e7-4450-8306-af76857ce77e"`
- **ServerNotification**
  - `0`
- **ServerTimeTicks**
  - `639273399483150995`
- **SessionKey**
  - **AccountServerId**: int = `10000000000`
  - **MxToken**: str = `"AAAAAAAA…"`
```
</details>


# mission

## /api/mission/guidemissionseasonlist

- **中文**: 任务·引导任务赛季
- **Protocol**: 8006　**混淆名**: `Y3UKGGQIBTTIJ6M374PM2EQRUQ`　**样本**: 5

请求无业务字段（仅标准头）。

### 响应 packet 顶层

- **GuideMissionSeasonDBs**: array
- **MissionProgressDBs**: array
- **Protocol**: int
- **RequestId**: str
- **ServerNotification**: int
- **ServerTimeTicks**: int
- **SessionKey**: object

<details><summary>响应结构示例（限深 3 层）</summary>

```
- **GuideMissionSeasonDBs**
  - [0] (object):
    - **SeasonId**: int = `1`
    - **LoginCount**: int = `7`
    - **StartDate**: str = `"2023-08-03T21:17:15.473"`
    - **LoginDate**: str = `"2023-08-09T21:53:14.784"`
    - **IsComplete**: bool = `true`
    - **IsFinalMissionComplete**: bool = `true`
  - …共 18 个元素
- **MissionProgressDBs**
  - [0] (object):
    - **AccountServerId**: int = `10000000000`
    - **MissionUniqueId**: int = `1000425`
    - **Category**: int = `4`
    - **StartDate**: str = `"2024-04-04T22:19:14.73"`
    - **ProgressParameters**: object
      - …(1 keys)
  - …共 88 个元素
- **Protocol**
  - `8006`
- **RequestId**
  - `"ee32ab13-bcea-4938-a6db-4953136d5353"`
- **ServerNotification**
  - `0`
- **ServerTimeTicks**
  - `639273399463034438`
- **SessionKey**
  - **AccountServerId**: int = `10000000000`
  - **MxToken**: str = `"AAAAAAAA…"`
```
</details>


## /api/mission/list

- **中文**: 任务·列表
- **Protocol**: 8000　**混淆名**: `5S4LD3Y34GQ2GPKJ75FIIFQWCQ`　**样本**: 23

### 请求业务字段

| 字段 | 类型 | 示例 |
|---|---|---|
| EventContentId | int/null | `null` |

### 响应 packet 顶层

- **ClearedOriginalMissionIds**: array
- **DailySuddenMissionInfo**: object
- **HistoryDBs**: null
- **MissionHistoryUniqueIds**: array
- **ProgressDBs**: array
- **Protocol**: int
- **RequestId**: str
- **ServerNotification**: int
- **ServerTimeTicks**: int
- **SessionKey**: object

<details><summary>响应结构示例（限深 3 层）</summary>

```
- **ClearedOriginalMissionIds**
  - (空数组)
- **DailySuddenMissionInfo**
  - **Id**: int = `1606`
- **HistoryDBs**
  - `null`
- **MissionHistoryUniqueIds**
  - (空数组)
- **ProgressDBs**
  - [0] (object):
    - **AccountServerId**: int = `10016071938`
    - **MissionUniqueId**: int = `848001`
    - **Category**: int = `8`
    - **StartDate**: str = `"2026-10-11T14:47:45.472"`
    - **ProgressParameters**: object
      - …(0 keys)
  - …共 30 个元素
- **Protocol**
  - `8000`
- **RequestId**
  - `"04a0d63c-1e6f-48bc-b376-7e274bfa60e4"`
- **ServerNotification**
  - `0`
- **ServerTimeTicks**
  - `639273396088342027`
- **SessionKey**
  - **AccountServerId**: int = `10016071938`
  - **MxToken**: str = `"wc4dt5o4…"`
```
</details>


## /api/mission/multiplereward

- **中文**: 任务·批量领取奖励
- **Protocol**: 8002　**混淆名**: `FF3K76PH2LLL6OPCYVKKENNHGE`　**样本**: 10

### 请求业务字段

| 字段 | 类型 | 示例 |
|---|---|---|
| EventContentId | null | `null` |
| GuideMissionSeasonId | null | `null` |
| MissionCategory | int | `5` |

### 响应 packet 顶层

- **AddedHistoryDBs**: array
- **MissionProgressDBs**: array
- **ParcelResultDB**: object
- **Protocol**: int
- **RequestId**: str
- **ServerNotification**: int
- **ServerTimeTicks**: int
- **SessionKey**: object

<details><summary>响应结构示例（限深 3 层）</summary>

```
- **AddedHistoryDBs**
  - [0] (object):
    - **AccountServerId**: int = `10000000000`
    - **MissionUniqueId**: int = `1514`
    - **CompleteTime**: str = `"2026-10-11T18:31:25.155401771"`
    - **Expired**: bool = `false`
  - …共 2 个元素
- **MissionProgressDBs**
  - [0] (object):
    - **AccountServerId**: int = `10000000000`
    - **MissionUniqueId**: int = `82029`
    - **Category**: int = `3`
    - **StartDate**: str = `"2026-04-09T20:22:43.391"`
    - **ProgressParameters**: object
      - …(1 keys)
  - …共 4 个元素
- **ParcelResultDB**
  - **AccountDB**: object
    - **ServerId**: int = `10000000000`
    - **RoleId**: int = `10000000000`
    - **Nickname**: str = `"左搂邮箱右抱日奈"`
    - **CallName**: str = `"我要高炒了"`
    - **DevId**: str = `""`
    - **State**: int = `0`
    - **Level**: int = `90`
    - **Exp**: int = `0`
    - **Comment**: str = `""`
    - **LobbyMode**: int = `0`
    - **RepresentCharacterServerId**: int = `239093`
    - **MemoryLobbyUniqueId**: int = `0`
    - **LastConnectTime**: str = `"2026-10-11T18:25:41.208"`
    - **BirthDay**: str = `"2005-02-11T00:00:00"`
    - **CallNameUpdateTime**: str = `"0001-01-01T00:00:00"`
    - **PublisherAccountId**: int = `0`
    - **RetentionDays**: int = `0`
    - **VIPLevel**: int = `0`
    - **CreateDate**: str = `"2023-08-03T21:16:37.326"`
    - **UnReadMailCount**: int = `0`
    - **LinkRewardDateDate**: str = `"0001-01-01T00:00:00"`
    - **Location**: str = `""`
    - **LastReturningDate**: str = `"0001-01-01T00:00:00"`
  - **AccountCurrencyDB**: object
    - **AccountLevel**: int = `1`
    - **AcademyLocationRankSum**: int = `1`
    - **CurrencyDict**: object
      - …(29 keys)
    - **UpdateTimeDict**: object
      - …(19 keys)
  - **DisplaySequence**: array
    - [0] (object):
      - …(2 keys)
    - …共 2 个元素
- **Protocol**
  - `8002`
- **RequestId**
  - `"66b0da20-7d91-4dd7-b2c3-40f460592b7a"`
- **ServerNotification**
  - `0`
- **ServerTimeTicks**
  - `639273402851608616`
- **SessionKey**
  - **AccountServerId**: int = `10000000000`
  - **MxToken**: str = `"AAAAAAAA…"`
```
</details>


## /api/mission/reward

- **中文**: 任务·领取奖励（单个）
- **Protocol**: 8001　**混淆名**: `5GN7IJ36QXZ6ZZX3E5SCHLZEN4`　**样本**: 1

### 请求业务字段

| 字段 | 类型 | 示例 |
|---|---|---|
| EventContentId | null | `null` |
| MissionUniqueId | int | `1701` |
| ProgressServerId | int | `0` |

### 响应 packet 顶层

- **AddedHistoryDB**: object
- **ParcelResultDB**: object
- **Protocol**: int
- **RequestId**: str
- **ServerNotification**: int
- **ServerTimeTicks**: int
- **SessionKey**: object

<details><summary>响应结构示例（限深 3 层）</summary>

```
- **AddedHistoryDB**
  - **AccountServerId**: int = `10000000000`
  - **MissionUniqueId**: int = `1701`
  - **CompleteTime**: str = `"2026-10-13T17:29:10.401945887"`
  - **Expired**: bool = `false`
- **ParcelResultDB**
  - **AccountDB**: object
    - **ServerId**: int = `10000000000`
    - **RoleId**: int = `10000000000`
    - **Nickname**: str = `"左搂邮箱右抱日奈"`
    - **CallName**: str = `"我要高炒了"`
    - **DevId**: str = `""`
    - **State**: int = `0`
    - **Level**: int = `90`
    - **Exp**: int = `0`
    - **Comment**: str = `""`
    - **LobbyMode**: int = `0`
    - **RepresentCharacterServerId**: int = `239093`
    - **MemoryLobbyUniqueId**: int = `0`
    - **LastConnectTime**: str = `"2026-10-13T17:21:56.918"`
    - **BirthDay**: str = `"2005-02-11T00:00:00"`
    - **CallNameUpdateTime**: str = `"0001-01-01T00:00:00"`
    - **PublisherAccountId**: int = `0`
    - **RetentionDays**: int = `0`
    - **VIPLevel**: int = `0`
    - **CreateDate**: str = `"2023-08-03T21:16:37.326"`
    - **UnReadMailCount**: int = `0`
    - **LinkRewardDateDate**: str = `"0001-01-01T00:00:00"`
    - **Location**: str = `""`
    - **LastReturningDate**: str = `"0001-01-01T00:00:00"`
  - **AccountCurrencyDB**: object
    - **AccountLevel**: int = `1`
    - **AcademyLocationRankSum**: int = `1`
    - **CurrencyDict**: object
      - …(29 keys)
    - **UpdateTimeDict**: object
      - …(19 keys)
  - **DisplaySequence**: array
    - [0] (object):
      - …(2 keys)
- **Protocol**
  - `8001`
- **RequestId**
  - `"d4f16048-4eac-40a2-b607-c97a4672f18b"`
- **ServerNotification**
  - `0`
- **ServerTimeTicks**
  - `639275093504060621`
- **SessionKey**
  - **AccountServerId**: int = `10000000000`
  - **MxToken**: str = `"AAAAAAAA…"`
```
</details>


# networktime

## /api/networktime/sync

- **中文**: 服务器时间同步
- **Protocol**: 3　**混淆名**: `QIRA2IPFGIJ5T56RHONAUNGUJA`　**样本**: 5

请求无业务字段（仅标准头）。

### 响应 packet 顶层

- **EchoSendTick**: int
- **Protocol**: int
- **ReceiveTick**: int
- **RequestId**: str
- **ServerNotification**: int
- **ServerTimeTicks**: int
- **SessionKey**: object

<details><summary>响应结构示例（限深 3 层）</summary>

```
- **EchoSendTick**
  - `639273399438161653`
- **Protocol**
  - `3`
- **ReceiveTick**
  - `639273399438161653`
- **RequestId**
  - `"c3952ee7-555b-4e1f-85c1-adb87a0fe0b9"`
- **ServerNotification**
  - `0`
- **ServerTimeTicks**
  - `639273399438161662`
- **SessionKey**
  - **AccountServerId**: int = `10000000000`
  - **MxToken**: str = `"AAAAAAAA…"`
```
</details>


# notification

## /api/notification/eventcontentreddotcheck

- **中文**: 红点检查（活动未读）
- **Protocol**: 36001　**混淆名**: `RMS5YFA2GTTTWMYK2IHUP2QSYE`　**样本**: 73

请求无业务字段（仅标准头）。

### 响应 packet 顶层

- **EventContentUnlockCGDBs**: object
- **Protocol**: int
- **Reddots**: object
- **RequestId**: str
- **ServerNotification**: int
- **ServerTimeTicks**: int
- **SessionKey**: object

<details><summary>响应结构示例（限深 3 层）</summary>

```
- **EventContentUnlockCGDBs**
  - **10836**: array
    - (空数组)
  - **50822**: array
    - (空数组)
  - **60013**: array
    - (空数组)
  - **848**: array
    - (空数组)
  - **900801**: array
    - (空数组)
  - **900802**: array
    - (空数组)
  - **900803**: array
    - (空数组)
  - **900804**: array
    - (空数组)
  - **900805**: array
    - (空数组)
  - **900806**: array
    - (空数组)
  - **900808**: array
    - (空数组)
  - **900809**: array
    - (空数组)
  - **900810**: array
    - (空数组)
  - **900811**: array
    - (空数组)
  - **900812**: array
    - (空数组)
  - **900813**: array
    - (空数组)
  - **900814**: array
    - (空数组)
  - **900815**: array
    - (空数组)
  - **900816**: array
    - (空数组)
  - **900817**: array
    - (空数组)
  - **900818**: array
    - (空数组)
  - **900819**: array
    - (空数组)
  - **900820**: array
    - (空数组)
  - **900825**: array
    - (空数组)
  - **900826**: array
    - (空数组)
- **Protocol**
  - `36001`
- **Reddots**
- **RequestId**
  - `"76fb8878-563f-4f3b-84dd-a43570a4d1e8"`
- **ServerNotification**
  - `0`
- **ServerTimeTicks**
  - `639273398656614226`
- **SessionKey**
  - **AccountServerId**: int = `10016071938`
  - **MxToken**: str = `"wc4dt5o4…"`
```
</details>


# opencondition

## /api/opencondition/eventlist

- **中文**: 开放条件·活动列表
- **Protocol**: 15002　**混淆名**: `4QJN3NKE73EJOHZJLD3OLU2XNU`　**样本**: 6

### 请求业务字段

| 字段 | 类型 | 示例 |
|---|---|---|
| ConquestEventIds | array | `[50822]` |
| WorldRaidSeasonAndGroupIds | object | `{"821": [821602], "823": [823100]}` |

### 响应 packet 顶层

- **ConquestTiles**: object
- **Protocol**: int
- **RequestId**: str
- **ServerNotification**: int
- **ServerTimeTicks**: int
- **SessionKey**: object
- **WorldRaidLocalBossDBs**: object

<details><summary>响应结构示例（限深 3 层）</summary>

```
- **ConquestTiles**
  - **50822**: array
    - [0] (object):
      - …(9 keys)
    - …共 106 个元素
- **Protocol**
  - `15002`
- **RequestId**
  - `"35f4d817-3191-4c1f-962a-219ab61814a3"`
- **ServerNotification**
  - `0`
- **ServerTimeTicks**
  - `639273399802379186`
- **SessionKey**
  - **AccountServerId**: int = `10000000000`
  - **MxToken**: str = `"AAAAAAAA…"`
- **WorldRaidLocalBossDBs**
  - **821**: array
    - [0] (object):
      - …(8 keys)
  - **823**: array
    - [0] (object):
      - …(8 keys)
```
</details>


# raid

## /api/raid/createbattle

- **中文**: 总力战·创建战斗
- **Protocol**: 17004　**混淆名**: `XTPFNRK3YYSB3RREIKHQ6JQSWI`　**样本**: 1

### 请求业务字段

| 字段 | 类型 | 示例 |
|---|---|---|
| AssistUseInfo | null | `null` |
| Difficulty | int | `5` |
| EchelonNumber | int | `2` |
| IsPractice | bool | `false` |
| IsPublic | bool | `false` |
| RaidUniqueId | int | `1111406` |
| SkillCardMulliganCharacterIds | array | `[10117, 10089, 10105]` |
| Tags | null | `null` |

### 响应 packet 顶层

- **AccountCurrencyDB**: object
- **BattleSetting**: object
- **MissionProgressDBs**: array
- **Protocol**: int
- **RaidBattleDB**: object
- **RaidDB**: object
- **RandomSeed**: int
- **RequestId**: str
- **ServerNotification**: int
- **ServerTimeTicks**: int
- **SessionKey**: object

<details><summary>响应结构示例（限深 3 层）</summary>

```
- **AccountCurrencyDB**
  - **AccountLevel**: int = `1`
  - **AcademyLocationRankSum**: int = `1`
  - **CurrencyDict**: object
    - **1**: int = `980648081`
    - **10**: int = `0`
    - **11**: int = `0`
    - **12**: int = `0`
    - **13**: int = `0`
    - **14**: int = `0`
    - **15**: int = `0`
    - **16**: int = `0`
    - **17**: int = `0`
    - **18**: int = `128665`
    - **19**: int = `40`
    - **2**: int = `0`
    - **20**: int = `40`
    - **21**: int = `40`
    - **22**: int = `0`
    - **23**: int = `0`
    - **24**: int = `0`
    - **25**: int = `4`
    - **26**: int = `0`
    - **27**: int = `0`
    - **28**: int = `0`
    - **29**: int = `0`
    - **3**: int = `154542`
    - **4**: int = `154542`
    - **5**: int = `10`
    - **6**: int = `0`
    - **7**: int = `4`
    - **8**: int = `2`
    - **9**: int = `0`
  - **UpdateTimeDict**: object
    - **12**: str = `"2026-10-12T20:59:42.082392521"`
    - **13**: str = `"2026-10-12T20:59:42.082392631"`
    - **14**: str = `"2026-10-12T20:59:42.082392736"`
    - **15**: str = `"2026-10-12T20:59:42.08239302"`
    - **16**: str = `"2026-10-12T20:59:42.082393225"`
    - **17**: str = `"2026-09-23T19:46:10.825"`
    - **19**: str = `"2026-10-12T20:59:42.08229199"`
    - **20**: str = `"2026-10-12T20:59:42.082313095"`
    - **21**: str = `"2026-10-12T20:59:42.082318785"`
    - **22**: str = `"2026-10-12T20:54:38.785"`
    - **23**: str = `"2026-10-12T20:54:58.796"`
    - **24**: str = `"2026-10-05T19:17:57.772"`
    - **25**: str = `"2026-10-05T17:57:35.375"`
    - **26**: str = `"2026-10-05T19:21:50.378"`
    - **5**: str = `"2026-10-12T20:55:58.833"`
    - **6**: str = `"2026-10-12T20:44:54.769"`
    - **7**: str = `"2026-10-12T20:55:13.954"`
    - **8**: str = `"2026-10-12T20:44:54.769"`
    - **9**: str = `"2026-10-12T20:59:42.082392287"`
- **BattleSetting**
  - **BattleType**: int = `2048`
  - **EchelonType**: int = `2`
  - **RandomSeed**: int = `7816843`
  - **Buid**: str = `"10000000000_1791809982086"`
  - **BattleDurationInFrame**: int = `7200`
  - **GroundUniqueId**: int = `211100006`
  - **StageId**: int = `1111406`
  - **EnvironmentType**: int = `0`
  - **IsBoss**: bool = `true`
  - **IsAutoUseSkill**: bool = `true`
  - **LeftTeam**: object
    - **AccountId**: int = `10000000000`
    - **TeamId**: int = `2`
    - **TeamName**: str = `"Team01"`
    - **LeaderCharacterServerId**: int = `2544528`
    - **EchelonNumber**: int = `2`
    - **FormationLocationKey**: object
      - …(1 keys)
    - **Starters**: array
      - …(array len=4)
    - **Supporters**: array
      - …(array len=2)
    - **GroundPassives**: array
      - …(array len=6)
    - **SkillCardMulliganCharacterIds**: array
      - …(array len=3)
    - **OriginalSkillCardMulliganCharacterIds**: array
      - …(array len=3)
    - **CheckTSSInteractionServerId**: bool = `true`
  - **RightTeam**: object
    - **TeamId**: int = `3`
    - **TeamName**: str = `"EN0006"`
    - **FormationLocationKey**: object
      - …(1 keys)
  - **PlayerActions**: null = `null`
  - **RaidSetting**: object
    - **RaidServerId**: int = `8`
    - **RaidSeasonId**: int = `74`
    - **SecretCode**: str = `"0"`
    - **RaidBossHP**: int = `46000000`
    - **RaidMembers**: array
      - …(array len=1)
  - **StageIndex**: int = `0`
  - **EventSetting**: null = `null`
  - **TimeAttackSetting**: null = `null`
  - **ClanAssistUseInfo**: null = `null`
- **MissionProgressDBs**
  - [0] (object):
    - **AccountServerId**: int = `10000000000`
    - **MissionUniqueId**: int = `100018`
    - **Category**: int = `3`
    - **StartDate**: str = `"2026-08-03T20:01:23.185"`
    - **ProgressParameters**: object
      - …(1 keys)
  - …共 2 个元素
- **Protocol**
  - `17004`
- **RaidBattleDB**
  - **RaidUniqueId**: int = `1111406`
  - **CurrentBossHP**: int = `46000000`
  - **IsClear**: bool = `false`
  - **RaidMembers**: array
    - [0] (object):
      - …(4 keys)
  - **SubPartsHPs**: null = `null`
- **RaidDB**
  - **Owner**: object
    - **AccountId**: int = `10000000000`
    - **AccountName**: str = `""`
    - **CharacterId**: int = `0`
    - **DamageCollection**: null = `null`
  - **ServerId**: int = `8`
  - **UniqueId**: int = `1111406`
  - **SeasonId**: int = `74`
  - **Begin**: str = `"2026-10-12T20:59:42.080789463"`
  - **End**: str = `"2026-10-12T21:59:42.080789463"`
  - **ContentType**: int = `10`
  - **PlayerCount**: int = `1`
  - **SecretCode**: str = `"0"`
  - **RaidState**: int = `1`
  - **RaidBossDBs**: array
    - [0] (object):
      - …(4 keys)
  - **AccountLevelWhenCreateDB**: int = `90`
- **RandomSeed**
  - `7816843`
- **RequestId**
  - `"6129e7b7-0f58-464a-9247-67e128710677"`
- **ServerNotification**
  - `3`
- **ServerTimeTicks**
  - `639274355820913577`
- **SessionKey**
  - **AccountServerId**: int = `10000000000`
  - **MxToken**: str = `"AAAAAAAA…"`
```
</details>


## /api/raid/endbattle

- **中文**: 总力战·战斗结算
- **Protocol**: 17007　**混淆名**: `RVEHU3PWIH3HXZ7BFL5E24HVQA`　**样本**: 1

### 请求业务字段

| 字段 | 类型 | 示例 |
|---|---|---|
| AssistUseInfo | null | `null` |
| ClientSetting | object | `{"IsAutoUseSkill": false, "PlayerActions": {"value1": null, …` |
| EchelonId | int | `2` |
| IsPractice | bool | `false` |
| RaidServerId | int | `8` |
| Summary | object | `{"IsAbort": false, "IsDefeatBattle": false, "HashKey": 0, "I…` |

### 响应 packet 顶层

- **BestRankingPoint**: int
- **ClearTimePoint**: int
- **DefaultClearPoint**: int
- **HPPercentScorePoint**: int
- **ParcelResultDB**: object
- **Protocol**: int
- **RankingPoint**: int
- **RequestId**: str
- **ServerNotification**: int
- **ServerTimeTicks**: int
- **SessionKey**: object

<details><summary>响应结构示例（限深 3 层）</summary>

```
- **BestRankingPoint**
  - `27742849`
- **ClearTimePoint**
  - `6702144`
- **DefaultClearPoint**
  - `6800000`
- **HPPercentScorePoint**
  - `14216000`
- **ParcelResultDB**
  - **AccountDB**: object
    - **ServerId**: int = `10000000000`
    - **RoleId**: int = `10000000000`
    - **Nickname**: str = `"左搂邮箱右抱日奈"`
    - **CallName**: str = `"我要高炒了"`
    - **DevId**: str = `""`
    - **State**: int = `0`
    - **Level**: int = `90`
    - **Exp**: int = `0`
    - **Comment**: str = `""`
    - **LobbyMode**: int = `0`
    - **RepresentCharacterServerId**: int = `239093`
    - **MemoryLobbyUniqueId**: int = `0`
    - **LastConnectTime**: str = `"2026-10-12T20:41:00.044"`
    - **BirthDay**: str = `"2005-02-11T00:00:00"`
    - **CallNameUpdateTime**: str = `"0001-01-01T00:00:00"`
    - **PublisherAccountId**: int = `0`
    - **RetentionDays**: int = `0`
    - **VIPLevel**: int = `0`
    - **CreateDate**: str = `"2023-08-03T21:16:37.326"`
    - **UnReadMailCount**: int = `0`
    - **LinkRewardDateDate**: str = `"0001-01-01T00:00:00"`
    - **Location**: str = `""`
    - **LastReturningDate**: str = `"0001-01-01T00:00:00"`
  - **AccountCurrencyDB**: object
    - **AccountLevel**: int = `1`
    - **AcademyLocationRankSum**: int = `1`
    - **CurrencyDict**: object
      - …(29 keys)
    - **UpdateTimeDict**: object
      - …(19 keys)
  - **ItemDBs**: object
    - **3100589**: object
      - …(5 keys)
    - **7156709**: object
      - …(5 keys)
  - **DisplaySequence**: array
    - [0] (object):
      - …(2 keys)
    - …共 2 个元素
- **Protocol**
  - `17007`
- **RankingPoint**
  - `27718144`
- **RequestId**
  - `"ab3c0fdd-dae9-49b3-9cce-7efe0e47a29d"`
- **ServerNotification**
  - `64`
- **ServerTimeTicks**
  - `639274360170951297`
- **SessionKey**
  - **AccountServerId**: int = `10000000000`
  - **MxToken**: str = `"AAAAAAAA…"`
```
</details>


## /api/raid/enterbattle

- **中文**: 总力战·进入战斗
- **Protocol**: 17005　**混淆名**: `G5KYZE3JTNA2CBHARKX3DOV2S4`　**样本**: 2

### 请求业务字段

| 字段 | 类型 | 示例 |
|---|---|---|
| AssistUseInfo | null | `null` |
| EchelonId | int | `0` |
| EchelonNumber | int | `2` |
| IsPractice | bool | `false` |
| RaidServerId | int | `8` |
| RaidUniqueId | int | `1111406` |
| SkillCardMulliganCharacterIds | array | `[10117, 10089, 10105]` |

### 响应 packet 顶层

- **BattleSetting**: object
- **Protocol**: int
- **RaidBattleDB**: object
- **RaidDB**: object
- **RandomSeed**: int
- **RequestId**: str
- **ServerNotification**: int
- **ServerTimeTicks**: int
- **SessionKey**: object

<details><summary>响应结构示例（限深 3 层）</summary>

```
- **BattleSetting**
  - **BattleType**: int = `2048`
  - **EchelonType**: int = `2`
  - **RandomSeed**: int = `2010826`
  - **Buid**: str = `"10000000000_1791810262459"`
  - **BattleDurationInFrame**: int = `7200`
  - **GroundUniqueId**: int = `211100006`
  - **StageId**: int = `1111406`
  - **EnvironmentType**: int = `0`
  - **IsBoss**: bool = `true`
  - **IsAutoUseSkill**: bool = `true`
  - **LeftTeam**: object
    - **AccountId**: int = `10000000000`
    - **TeamId**: int = `2`
    - **TeamName**: str = `"Team01"`
    - **LeaderCharacterServerId**: int = `2544528`
    - **EchelonNumber**: int = `2`
    - **FormationLocationKey**: object
      - …(1 keys)
    - **Starters**: array
      - …(array len=4)
    - **Supporters**: array
      - …(array len=2)
    - **GroundPassives**: array
      - …(array len=6)
    - **SkillCardMulliganCharacterIds**: array
      - …(array len=3)
    - **OriginalSkillCardMulliganCharacterIds**: array
      - …(array len=3)
    - **CheckTSSInteractionServerId**: bool = `true`
  - **RightTeam**: object
    - **TeamId**: int = `3`
    - **TeamName**: str = `"EN0006"`
    - **FormationLocationKey**: object
      - …(1 keys)
  - **PlayerActions**: null = `null`
  - **RaidSetting**: object
    - **RaidServerId**: int = `8`
    - **RaidSeasonId**: int = `74`
    - **SecretCode**: str = `"0"`
    - **RaidBossHP**: int = `46000000`
    - **RaidMembers**: array
      - …(array len=1)
  - **StageIndex**: int = `0`
  - **EventSetting**: null = `null`
  - **TimeAttackSetting**: null = `null`
  - **ClanAssistUseInfo**: null = `null`
- **Protocol**
  - `17005`
- **RaidBattleDB**
  - **RaidUniqueId**: int = `1111406`
  - **CurrentBossHP**: int = `46000000`
  - **IsClear**: bool = `false`
  - **RaidMembers**: array
    - [0] (object):
      - …(4 keys)
  - **SubPartsHPs**: null = `null`
- **RaidDB**
  - **Owner**: object
    - **AccountId**: int = `10000000000`
    - **AccountName**: str = `""`
    - **CharacterId**: int = `0`
    - **DamageCollection**: null = `null`
  - **ServerId**: int = `8`
  - **UniqueId**: int = `1111406`
  - **SeasonId**: int = `74`
  - **Begin**: str = `"2026-10-12T20:59:42.081"`
  - **End**: str = `"2026-10-12T21:59:42.081"`
  - **ContentType**: int = `10`
  - **PlayerCount**: int = `1`
  - **SecretCode**: str = `"0"`
  - **RaidState**: int = `1`
  - **RaidBossDBs**: array
    - [0] (object):
      - …(4 keys)
  - **AccountLevelWhenCreateDB**: int = `90`
- **RandomSeed**
  - `2010826`
- **RequestId**
  - `"3974db2a-1862-4034-9c14-cf5fd2e5a1ae"`
- **ServerNotification**
  - `0`
- **ServerTimeTicks**
  - `639274358624637409`
- **SessionKey**
  - **AccountServerId**: int = `10000000000`
  - **MxToken**: str = `"AAAAAAAA…"`
```
</details>


## /api/raid/lobby

- **中文**: 总力战·大厅
- **Protocol**: 17014　**混淆名**: `PAAKOO2FW7K7VQR2BINTKQ5ZBA`　**样本**: 5

请求无业务字段（仅标准头）。

### 响应 packet 顶层

- **AccountCurrencyDB**: null
- **ParcelResultDB**: null
- **Protocol**: int
- **RaidLobbyInfoDB**: object
- **RequestId**: str
- **SeasonType**: int
- **ServerNotification**: int
- **ServerTimeTicks**: int
- **SessionKey**: object

<details><summary>响应结构示例（限深 3 层）</summary>

```
- **AccountCurrencyDB**
  - `null`
- **ParcelResultDB**
  - `null`
- **Protocol**
  - `17014`
- **RaidLobbyInfoDB**
  - **SeasonId**: int = `74`
  - **Tier**: int = `3`
  - **Ranking**: int = `22258`
  - **BestRankingPoint**: int = `27742849`
  - **TotalRankingPoint**: int = `143727717`
  - **ReceivedRankingRewardId**: int = `0`
  - **CanReceiveRankingReward**: bool = `false`
  - **PlayingRaidDB**: null = `null`
  - **ReceiveRewardIds**: array
    - [0] (int):
      - `7000`
    - …共 42 个元素
  - **ParticipateCharacterServerIds**: array
    - [0] (int):
      - `3112996`
    - …共 6 个元素
  - **PlayableHighestDifficulty**: object
    - **EN0006**: int = `6`
  - **SweepPointByRaidUniqueId**: object
  - **SeasonStartDate**: str = `"2026-10-08T14:00:00"`
  - **SeasonEndDate**: str = `"2026-10-15T03:59:59"`
  - **SettlementEndDate**: str = `"2026-10-15T23:59:59"`
  - **NextSeasonId**: int = `75`
  - **NextSeasonStartDate**: str = `"2026-10-29T14:00:00"`
  - **NextSeasonEndDate**: str = `"2026-11-05T03:59:59"`
  - **NextSettlementEndDate**: str = `"2026-11-05T23:59:59"`
  - **OpenedBossGroups**: null = `null`
  - **BestRankingPointPerBossGroup**: null = `null`
  - **ReceiveLimitedRewardIds**: null = `null`
  - **ClanAssistUseInfo**: null = `null`
  - **RemainFailCompensation**: object
    - **0**: bool = `true`
  - **ClearDifficulty**: array
    - [0] (int):
      - `1`
    - …共 5 个元素
- **RequestId**
  - `"c1f3c912-0b76-4ba2-bd59-426f94bd532b"`
- **SeasonType**
  - `1`
- **ServerNotification**
  - `0`
- **ServerTimeTicks**
  - `639274353208330838`
- **SessionKey**
  - **AccountServerId**: int = `10000000000`
  - **MxToken**: str = `"AAAAAAAA…"`
```
</details>


## /api/raid/opponentlist

- **中文**: 总力战·排名列表 (？)
- **Protocol**: 17016　**混淆名**: `V7THWTCAC6YBKJLSVZYJ5IIZ6M`　**样本**: 4

### 请求业务字段

| 字段 | 类型 | 示例 |
|---|---|---|
| IsFirstRequest | bool | `true` |
| IsUpper | bool | `false` |
| Rank | int | `129615` |
| Score | null | `null` |
| SearchType | int | `1` |

### 响应 packet 顶层

- **OpponentUserDBs**: array
- **Protocol**: int
- **RequestId**: str
- **ServerNotification**: int
- **ServerTimeTicks**: int
- **SessionKey**: object

<details><summary>响应结构示例（限深 3 层）</summary>

```
- **OpponentUserDBs**
  - [0] (object):
    - **AccountId**: int = `10009521009`
    - **RepresentCharacterUniqueId**: int = `20025`
    - **Level**: int = `90`
    - **Nickname**: str = `"呵呵"`
    - **Tier**: int = `2`
    - **Rank**: int = `129586`
    - **BestRankingPoint**: int = `12543874`
    - **RaidTeamSettingDB**: object
      - …(8 keys)
    - **AccountAttachmentDB**: object
      - …(2 keys)
  - …共 30 个元素
- **Protocol**
  - `17016`
- **RequestId**
  - `"41f9d3bc-76dc-4d42-9ab7-bfb158ca3abc"`
- **ServerNotification**
  - `0`
- **ServerTimeTicks**
  - `639274360520982462`
- **SessionKey**
  - **AccountServerId**: int = `10000000000`
  - **MxToken**: str = `"AAAAAAAA…"`
```
</details>


## /api/raid/rankingindex

- **中文**: 总力战·排名索引
- **Protocol**: 17021　**混淆名**: `FK47MNDAPWYUP3RUY3YICLQEK4`　**样本**: 2

请求无业务字段（仅标准头）。

### 响应 packet 顶层

- **Protocol**: int
- **RankBrackets**: array
- **RequestId**: str
- **ServerNotification**: int
- **ServerTimeTicks**: int
- **SessionKey**: object

<details><summary>响应结构示例（限深 3 层）</summary>

```
- **Protocol**
  - `17021`
- **RankBrackets**
  - [0] (object):
    - **Difficulty**: int = `7`
    - **RankCount**: int = `561`
  - …共 8 个元素
- **RequestId**
  - `"911cc267-3cd4-4626-8a85-a9068894914c"`
- **ServerNotification**
  - `0`
- **ServerTimeTicks**
  - `639274361634026062`
- **SessionKey**
  - **AccountServerId**: int = `10000000000`
  - **MxToken**: str = `"AAAAAAAA…"`
```
</details>


## /api/raid/seasonreward

- **中文**: 总力战·赛季奖励
- **Protocol**: 17013　**混淆名**: `DUBME56UP27MNKKJLCS2HI6YBM`　**样本**: 2

请求无业务字段（仅标准头）。

### 响应 packet 顶层

- **MissionProgressDBs**: array
- **ParcelResultDB**: object
- **Protocol**: int
- **ReceiveRewardIds**: array
- **RequestId**: str
- **ServerNotification**: int
- **ServerTimeTicks**: int
- **SessionKey**: object

<details><summary>响应结构示例（限深 3 层）</summary>

```
- **MissionProgressDBs**
  - [0] (object):
    - **AccountServerId**: int = `10000000000`
    - **MissionUniqueId**: int = `82029`
    - **Category**: int = `3`
    - **StartDate**: str = `"2026-04-09T20:22:43.391"`
    - **ProgressParameters**: object
      - …(1 keys)
- **ParcelResultDB**
  - **AccountDB**: object
    - **ServerId**: int = `10000000000`
    - **RoleId**: int = `10000000000`
    - **Nickname**: str = `"左搂邮箱右抱日奈"`
    - **CallName**: str = `"我要高炒了"`
    - **DevId**: str = `""`
    - **State**: int = `0`
    - **Level**: int = `90`
    - **Exp**: int = `0`
    - **Comment**: str = `""`
    - **LobbyMode**: int = `0`
    - **RepresentCharacterServerId**: int = `239093`
    - **MemoryLobbyUniqueId**: int = `0`
    - **LastConnectTime**: str = `"2026-10-12T20:41:00.044"`
    - **BirthDay**: str = `"2005-02-11T00:00:00"`
    - **CallNameUpdateTime**: str = `"0001-01-01T00:00:00"`
    - **PublisherAccountId**: int = `0`
    - **RetentionDays**: int = `0`
    - **VIPLevel**: int = `0`
    - **CreateDate**: str = `"2023-08-03T21:16:37.326"`
    - **UnReadMailCount**: int = `0`
    - **LinkRewardDateDate**: str = `"0001-01-01T00:00:00"`
    - **Location**: str = `""`
    - **LastReturningDate**: str = `"0001-01-01T00:00:00"`
  - **AccountCurrencyDB**: object
    - **AccountLevel**: int = `1`
    - **AcademyLocationRankSum**: int = `1`
    - **CurrencyDict**: object
      - …(29 keys)
    - **UpdateTimeDict**: object
      - …(19 keys)
  - **EquipmentDBs**: object
    - **1445142**: object
      - …(6 keys)
  - **DisplaySequence**: array
    - [0] (object):
      - …(2 keys)
    - …共 2 个元素
- **Protocol**
  - `17013`
- **ReceiveRewardIds**
  - [0] (int):
    - `7000`
  - …共 45 个元素
- **RequestId**
  - `"e4b86353-7f25-4ff3-a543-d09f8ebf00ff"`
- **ServerNotification**
  - `0`
- **ServerTimeTicks**
  - `639274361662484689`
- **SessionKey**
  - **AccountServerId**: int = `10000000000`
  - **MxToken**: str = `"AAAAAAAA…"`
```
</details>


## /api/raid/sweep

- **中文**: 总力战·扫荡
- **Protocol**: 17019　**混淆名**: `2LSIG4XDI5J2UQO567M4P7GSKM`　**样本**: 1

### 请求业务字段

| 字段 | 类型 | 示例 |
|---|---|---|
| SweepCount | int | `2` |
| UniqueId | int | `1111406` |

### 响应 packet 顶层

- **MissionProgressDBs**: array
- **ParcelResultDB**: object
- **Protocol**: int
- **RequestId**: str
- **Rewards**: array
- **ServerNotification**: int
- **ServerTimeTicks**: int
- **SessionKey**: object
- **TotalSeasonPoint**: int

<details><summary>响应结构示例（限深 3 层）</summary>

```
- **MissionProgressDBs**
  - [0] (object):
    - **AccountServerId**: int = `10000000000`
    - **MissionUniqueId**: int = `100018`
    - **Category**: int = `3`
    - **StartDate**: str = `"2026-08-03T20:01:23.185"`
    - **ProgressParameters**: object
      - …(1 keys)
- **ParcelResultDB**
  - **AccountDB**: object
    - **ServerId**: int = `10000000000`
    - **RoleId**: int = `10000000000`
    - **Nickname**: str = `"左搂邮箱右抱日奈"`
    - **CallName**: str = `"我要高炒了"`
    - **DevId**: str = `""`
    - **State**: int = `0`
    - **Level**: int = `90`
    - **Exp**: int = `0`
    - **Comment**: str = `""`
    - **LobbyMode**: int = `0`
    - **RepresentCharacterServerId**: int = `239093`
    - **MemoryLobbyUniqueId**: int = `0`
    - **LastConnectTime**: str = `"2026-10-12T20:41:00.044"`
    - **BirthDay**: str = `"2005-02-11T00:00:00"`
    - **CallNameUpdateTime**: str = `"0001-01-01T00:00:00"`
    - **PublisherAccountId**: int = `0`
    - **RetentionDays**: int = `0`
    - **VIPLevel**: int = `0`
    - **CreateDate**: str = `"2023-08-03T21:16:37.326"`
    - **UnReadMailCount**: int = `0`
    - **LinkRewardDateDate**: str = `"0001-01-01T00:00:00"`
    - **Location**: str = `""`
    - **LastReturningDate**: str = `"0001-01-01T00:00:00"`
  - **AccountCurrencyDB**: object
    - **AccountLevel**: int = `1`
    - **AcademyLocationRankSum**: int = `1`
    - **CurrencyDict**: object
      - …(29 keys)
    - **UpdateTimeDict**: object
      - …(19 keys)
  - **ItemDBs**: object
    - **3100589**: object
      - …(5 keys)
    - **7156709**: object
      - …(5 keys)
  - **DisplaySequence**: array
    - [0] (object):
      - …(2 keys)
    - …共 2 个元素
- **Protocol**
  - `17019`
- **RequestId**
  - `"f0d1085b-65ae-4a49-9837-83c93063c052"`
- **Rewards**
  - [0] (array):
    - [0] (object):
      - …(2 keys)
    - …共 2 个元素
  - …共 2 个元素
- **ServerNotification**
  - `64`
- **ServerTimeTicks**
  - `639274360649004897`
- **SessionKey**
  - **AccountServerId**: int = `10000000000`
  - **MxToken**: str = `"AAAAAAAA…"`
- **TotalSeasonPoint**
  - `226882149`
```
</details>


# scenario

## /api/scenario/skip

- **中文**: 剧情·跳过
- **Protocol**: 19003　**混淆名**: `63AWLKA74BAHU6K3JNGSV7X65M`　**样本**: 3

### 请求业务字段

| 字段 | 类型 | 示例 |
|---|---|---|
| ScriptGroupId | int | `10034010` |
| SkipPointScriptCount | int | `2` |

### 响应 packet 顶层

- **Protocol**: int
- **RequestId**: str
- **ServerNotification**: int
- **ServerTimeTicks**: int
- **SessionKey**: object

<details><summary>响应结构示例（限深 3 层）</summary>

```
- **Protocol**
  - `19003`
- **RequestId**
  - `"6da2d992-6b49-459a-b449-a702d711caf5"`
- **ServerNotification**
  - `0`
- **ServerTimeTicks**
  - `639275059235633746`
- **SessionKey**
  - **AccountServerId**: int = `10000000000`
  - **MxToken**: str = `"AAAAAAAA…"`
```
</details>


# schooldungeon

## /api/schooldungeon/list

- **中文**: 学院副本·列表 (？)
- **Protocol**: 38000　**混淆名**: `CVOHU6FZQTL2DEZSQ3PCIVOBKM`　**样本**: 3

请求无业务字段（仅标准头）。

### 响应 packet 顶层

- **Protocol**: int
- **RequestId**: str
- **SchoolDungeonStageHistoryDBList**: array
- **ServerNotification**: int
- **ServerTimeTicks**: int
- **SessionKey**: object

<details><summary>响应结构示例（限深 3 层）</summary>

```
- **Protocol**
  - `38000`
- **RequestId**
  - `"9f0a519c-3553-4f58-8e24-dbac5a066b83"`
- **SchoolDungeonStageHistoryDBList**
  - [0] (object):
    - **AccountServerId**: int = `10000000000`
    - **StageUniqueId**: int = `60101`
    - **StarFlags**: array
      - …(array len=3)
  - …共 12 个元素
- **ServerNotification**
  - `0`
- **ServerTimeTicks**
  - `639274352937844190`
- **SessionKey**
  - **AccountServerId**: int = `10000000000`
  - **MxToken**: str = `"AAAAAAAA…"`
```
</details>


# shop

## /api/shop/buyrefreshmerchandise

- **中文**: 商店·手动刷新商品
- **Protocol**: 10007　**混淆名**: `GCYR6KWHCQQ4D2R6HXJX6NHHBY`　**样本**: 2

### 请求业务字段

| 字段 | 类型 | 示例 |
|---|---|---|
| ShopUniqueIds | array | `[1036, 1037, 1038, 1039, 1000, 1001, 1002, 1032, 1040, 1041,…` |

### 响应 packet 顶层

- **AccountCurrencyDB**: object
- **BattlePassMissionProgressDBDict**: object
- **ConsumeResultDB**: object
- **MailDB**: null
- **MissionProgressDBs**: array
- **ParcelResultDB**: object
- **Protocol**: int
- **RequestId**: str
- **ServerNotification**: int
- **ServerTimeTicks**: int
- **SessionKey**: object
- **ShopProductDB**: array

<details><summary>响应结构示例（限深 3 层）</summary>

```
- **AccountCurrencyDB**
  - **AccountLevel**: int = `1`
  - **AcademyLocationRankSum**: int = `1`
  - **CurrencyDict**: object
    - **1**: int = `980082777`
    - **10**: int = `0`
    - **11**: int = `0`
    - **12**: int = `0`
    - **13**: int = `0`
    - **14**: int = `0`
    - **15**: int = `0`
    - **16**: int = `0`
    - **17**: int = `0`
    - **18**: int = `128965`
    - **19**: int = `40`
    - **2**: int = `0`
    - **20**: int = `40`
    - **21**: int = `40`
    - **22**: int = `0`
    - **23**: int = `0`
    - **24**: int = `0`
    - **25**: int = `4`
    - **26**: int = `0`
    - **27**: int = `0`
    - **28**: int = `0`
    - **29**: int = `0`
    - **3**: int = `154572`
    - **4**: int = `154572`
    - **5**: int = `2`
    - **6**: int = `0`
    - **7**: int = `4`
    - **8**: int = `0`
    - **9**: int = `0`
  - **UpdateTimeDict**: object
    - **12**: str = `"2026-10-12T21:08:57.983922925"`
    - **13**: str = `"2026-10-12T21:08:57.983923035"`
    - **14**: str = `"2026-10-12T21:08:57.983923502"`
    - **15**: str = `"2026-10-12T21:08:57.983923762"`
    - **16**: str = `"2026-10-12T21:08:57.983923962"`
    - **17**: str = `"2026-09-23T19:46:10.825"`
    - **19**: str = `"2026-10-12T21:08:57.983824011"`
    - **20**: str = `"2026-10-12T21:08:57.983844422"`
    - **21**: str = `"2026-10-12T21:08:57.983850917"`
    - **22**: str = `"2026-10-12T20:54:38.785"`
    - **23**: str = `"2026-10-12T20:54:58.796"`
    - **24**: str = `"2026-10-05T19:17:57.772"`
    - **25**: str = `"2026-10-05T17:57:35.375"`
    - **26**: str = `"2026-10-05T19:21:50.378"`
    - **5**: str = `"2026-10-12T21:07:58.833"`
    - **6**: str = `"2026-10-12T20:44:54.769"`
    - **7**: str = `"2026-10-12T20:55:13.954"`
    - **8**: str = `"2026-10-12T20:44:54.769"`
    - **9**: str = `"2026-10-12T21:08:57.98392267"`
- **BattlePassMissionProgressDBDict**
  - **1**: array
    - [0] (object):
      - …(6 keys)
- **ConsumeResultDB**
  - **RemovedItemServerIds**: array
    - (空数组)
  - **RemovedEquipmentServerIds**: null = `null`
  - **RemovedFurnitureServerIds**: null = `null`
  - **UsedItemServerIdAndRemainingCounts**: object
  - **UsedEquipmentServerIdAndRemainingCounts**: null = `null`
  - **UsedFurnitureServerIdAndRemainingCounts**: null = `null`
- **MailDB**
  - `null`
- **MissionProgressDBs**
  - [0] (object):
    - **AccountServerId**: int = `10000000000`
    - **MissionUniqueId**: int = `82129`
    - **Category**: int = `3`
    - **StartDate**: str = `"2026-08-21T22:11:16.317"`
    - **ProgressParameters**: object
      - …(1 keys)
- **ParcelResultDB**
  - **AccountDB**: object
    - **ServerId**: int = `10000000000`
    - **RoleId**: int = `10000000000`
    - **Nickname**: str = `"左搂邮箱右抱日奈"`
    - **CallName**: str = `"我要高炒了"`
    - **DevId**: str = `""`
    - **State**: int = `0`
    - **Level**: int = `90`
    - **Exp**: int = `0`
    - **Comment**: str = `""`
    - **LobbyMode**: int = `0`
    - **RepresentCharacterServerId**: int = `239093`
    - **MemoryLobbyUniqueId**: int = `0`
    - **LastConnectTime**: str = `"2026-10-12T20:41:00.044"`
    - **BirthDay**: str = `"2005-02-11T00:00:00"`
    - **CallNameUpdateTime**: str = `"0001-01-01T00:00:00"`
    - **PublisherAccountId**: int = `0`
    - **RetentionDays**: int = `0`
    - **VIPLevel**: int = `0`
    - **CreateDate**: str = `"2023-08-03T21:16:37.326"`
    - **UnReadMailCount**: int = `0`
    - **LinkRewardDateDate**: str = `"0001-01-01T00:00:00"`
    - **Location**: str = `""`
    - **LastReturningDate**: str = `"0001-01-01T00:00:00"`
  - **AccountCurrencyDB**: object
    - **AccountLevel**: int = `1`
    - **AcademyLocationRankSum**: int = `1`
    - **CurrencyDict**: object
      - …(29 keys)
    - **UpdateTimeDict**: object
      - …(19 keys)
  - **EquipmentDBs**: object
    - **1445142**: object
      - …(6 keys)
    - **24732727**: object
      - …(6 keys)
    - **5614612**: object
      - …(6 keys)
    - **852160**: object
      - …(6 keys)
  - **ItemDBs**: object
    - **1130616**: object
      - …(5 keys)
    - **1177316**: object
      - …(5 keys)
    - **1177317**: object
      - …(5 keys)
    - **1770467**: object
      - …(5 keys)
    - **22181178**: object
      - …(5 keys)
    - **27675044**: object
      - …(5 keys)
    - **4003652**: object
      - …(5 keys)
    - **4003785**: object
      - …(5 keys)
    - **6884060**: object
      - …(5 keys)
    - **6908507**: object
      - …(5 keys)
    - **974118**: object
      - …(5 keys)
  - **DisplaySequence**: array
    - [0] (object):
      - …(2 keys)
    - …共 15 个元素
- **Protocol**
  - `10007`
- **RequestId**
  - `"8cbc4f0c-3200-4992-b1dd-27a8b86dc847"`
- **ServerNotification**
  - `3`
- **ServerTimeTicks**
  - `639274361379863419`
- **SessionKey**
  - **AccountServerId**: int = `10000000000`
  - **MxToken**: str = `"AAAAAAAA…"`
- **ShopProductDB**
  - [0] (object):
    - **EventContentId**: int = `0`
    - **ShopExcelId**: int = `1036`
    - **Category**: int = `0`
    - **DisplayOrder**: int = `1`
    - **PurchaseCount**: int = `1`
    - **SoldOut**: bool = `false`
    - **PurchaseCountLimit**: int = `1`
    - **Price**: int = `0`
    - **ProductType**: int = `0`
  - …共 24 个元素
```
</details>


## /api/shop/list

- **中文**: 商店·列表（信用点/青辉石）
- **Protocol**: 10002　**混淆名**: `FBRX4DTR54E6Q2FDLMV6MEHDVQ`　**样本**: 8

### 请求业务字段

| 字段 | 类型 | 示例 |
|---|---|---|
| CategoryList | array | `[38]` |

### 响应 packet 顶层

- **Protocol**: int
- **RequestId**: str
- **ServerNotification**: int
- **ServerTimeTicks**: int
- **SessionKey**: object
- **ShopEligmaHistoryDBs**: array
- **ShopInfos**: array

<details><summary>响应结构示例（限深 3 层）</summary>

```
- **Protocol**
  - `10002`
- **RequestId**
  - `"6878ca2e-d4c0-473c-be10-36325c4fd254"`
- **ServerNotification**
  - `0`
- **ServerTimeTicks**
  - `639273403112818465`
- **SessionKey**
  - **AccountServerId**: int = `10000000000`
  - **MxToken**: str = `"AAAAAAAA…"`
- **ShopEligmaHistoryDBs**
  - [0] (object):
    - **CharacterUniqueId**: int = `10000`
    - **PurchaseCount**: int = `270`
  - …共 41 个元素
- **ShopInfos**
  - [0] (object):
    - **EventContentId**: int = `0`
    - **Category**: int = `0`
    - **ShopGroupType**: int = `1`
    - **ManualRefreshCount**: int = `0`
    - **IsRefresh**: bool = `true`
    - **NextAutoRefreshDate**: str = `"2026-10-12T04:00:00"`
    - **LastAutoRefreshDate**: str = `"2026-10-11T04:00:00"`
    - **ShopProductList**: array
      - …(array len=24)
  - …共 11 个元素
```
</details>


# toast

## /api/toast/list

- **中文**: 弹窗通知列表
- **Protocol**: 16000　**混淆名**: `TNHDCYD5QKYJNL6NHXKI3QRKOY`　**样本**: 5

请求无业务字段（仅标准头）。

### 响应 packet 顶层

- **Protocol**: int
- **RequestId**: str
- **ServerNotification**: int
- **ServerTimeTicks**: int
- **SessionKey**: object
- **ToastDBs**: null

<details><summary>响应结构示例（限深 3 层）</summary>

```
- **Protocol**
  - `16000`
- **RequestId**
  - `"279d81e7-6666-4648-aee9-a216f1e96ae0"`
- **ServerNotification**
  - `0`
- **ServerTimeTicks**
  - `639273399488242738`
- **SessionKey**
  - **AccountServerId**: int = `10000000000`
  - **MxToken**: str = `"AAAAAAAA…"`
- **ToastDBs**
  - `null`
```
</details>


# weekdungeon

## /api/weekdungeon/list

- **中文**: 周常副本·列表（课程表）(？)
- **Protocol**: 23000　**混淆名**: `P5OT7LMDAURZPQ5AFVSA2BDWHA`　**样本**: 3

请求无业务字段（仅标准头）。

### 响应 packet 顶层

- **AdditionalStageIdList**: array
- **Protocol**: int
- **RequestId**: str
- **ServerNotification**: int
- **ServerTimeTicks**: int
- **SessionKey**: object
- **WeekDungeonStageHistoryDBList**: array

<details><summary>响应结构示例（限深 3 层）</summary>

```
- **AdditionalStageIdList**
  - (空数组)
- **Protocol**
  - `23000`
- **RequestId**
  - `"a45074d5-d780-4592-833d-acafa77d933a"`
- **ServerNotification**
  - `0`
- **ServerTimeTicks**
  - `639274352670782218`
- **SessionKey**
  - **AccountServerId**: int = `10000000000`
  - **MxToken**: str = `"AAAAAAAA…"`
- **WeekDungeonStageHistoryDBList**
  - [0] (object):
    - **AccountServerId**: int = `10000000000`
    - **StageUniqueId**: int = `30101`
    - **StarGoalRecord**: object
      - …(3 keys)
  - …共 58 个元素
```
</details>



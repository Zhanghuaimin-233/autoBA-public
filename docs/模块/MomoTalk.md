# MomoTalk

> **状态**：已实现 ｜ **日期**：2026-10-28

抓包现场：2026-10-22 22:33–22:35，测试号 手动跑完晴奈一条完整 MomoTalk（互发信息 → 剧情 → 回手机继续），
中途退主页重连过一次。全流程落 80 条样本，其中 MomoTalk/剧情 16 条。

## 一、结论摘要

MomoTalk **不是**一个"发消息"接口，而是**消息组推进器**：

- 对话正文（谁说了什么、选项文本）**全在客户端本地表**，服务端只存"读到哪个组 / 选了哪条"
- 一次 `read` = 推进一个 `MessageGroupId`
- 消息组带 `FavorScheduleId` 时，客户端弹剧情入口；剧情正文也在本地（`ScenarioScriptExcel`）
- 剧情"播放"没有服务端交互，只有**跳过上报**和**完成记录**，然后单独调 `favorschedule` 领奖励

对自动化最有利的一点：**不需要播放剧情、不需要发聊天内容**——服务端只认
`grouphistoryupdate` + `favorschedule` 两个请求（2026-10-28 实测，见第五节）。

## 二、接口

| 协议 | 路径 | 请求字段 | 响应关键字段 |
|---|---|---|---|
| 33001 | `/api/momotalk/messagelist` | `CharacterDBId` | `MomoTalkOutLineDB`、`MomoTalkChoiceDBs` |
| 33002 | `/api/momotalk/read` | `CharacterDBId`、`LastReadMessageGroupId`、`ChosenMessageId` | 同上 |
| 33004 | `/api/momotalk/favorschedule` | `ScheduleId` | `ParcelResultDB`、`FavorScheduleRecords` |
| 19003 | `/api/scenario/skip` | `ScriptGroupId`、`SkipPointScriptCount` | 无业务体 |
| 19002 | `/api/scenario/grouphistoryupdate` | `ScenarioGroupUniqueId`、`ScenarioType` | `ScenarioGroupHistoryDB` |

### 33001 messagelist（进会话）
```json
请求: {"Protocol":33001,"CharacterDBId":529404,...}
响应: {"MomoTalkOutLineDB":{"CharacterDBId":529404,"CharacterId":10002,
        "LatestMessageGroupId":100020050,"ChosenMessageId":0,
        "LastUpdateDate":"2024-03-31T23:56:22.925"},
       "MomoTalkChoiceDBs":[{"CharacterDBId":529404,"MessageGroupId":100020030,
        "ChosenMessageId":419,"ChosenDate":"2024-03-31T23:56:12.091"}]}
```
- `MomoTalkOutLineDB`：会话概要，`LatestMessageGroupId` = 服务端认为的最新一组
- `MomoTalkChoiceDBs`：该角色**历史所有选择**（每次 read 带过 ChosenMessageId 就追加一条）
- **不返回任何消息正文**

### 33002 read（推进一组）
```json
请求: {"Protocol":33002,"CharacterDBId":529404,
       "LastReadMessageGroupId":100020070,"ChosenMessageId":425}
```
- `ChosenMessageId`：该组有多条 `Answer` 时传选中的 `Id`；纯 `Feedback` 组传 `null`
- 响应与 messagelist 同构（outline + choices），`LastUpdateDate` 刷新为当前时间
- 实测 8 次 read 的组：100020050 → 100020070 → 100020080 → 100020110 → 100020140 → 100020150 → 100020180 → 100020200
  —— **可以跳组**（100020060 被跳过没单独 read），不要求逐组连推

### 19003 skip（跳过剧情）
```json
{"Protocol":19003,"ScriptGroupId":1000202,"SkipPointScriptCount":6}
```
- `ScriptGroupId` = `AcademyFavorScheduleExcel.ScenarioSriptGroupId`（注意原表字段拼写就是 `Sript`）
- `SkipPointScriptCount` 实测 6 / 5，但该脚本组本地有 95 行——**不是脚本行数**，语义待实测（见第五节）

### 19002 grouphistoryupdate（剧情完成记录）
```json
{"Protocol":19002,"ScenarioGroupUniqueId":1000202,"ScenarioType":4}
```
- `ScenarioType=4` = MomoTalk 好感剧情
- 响应 `ScenarioGroupHistoryDB` 回填 `ClearDateTime` / `IsReturn` / `IsPermanent`

### 33004 favorschedule（领剧情奖励）
```json
{"Protocol":33004,"ScheduleId":100022}
→ ParcelResultDB.DisplaySequence: [{"Key":{"Type":2,"Id":3},"Amount":20}]
   FavorScheduleRecords: {"10002":[100022], "10003":[100032,...], ...}
```
- `DisplaySequence`：奖励流水。`Type:2`=Currency，`Id:3`=**GemBonus 免费青辉石**（`CurrencyExcel`: 1=Gold / 2=GemPaid / 3=GemBonus / 5=ActionPoint）
- **青辉石按好感等级分档**（`RewardAmount`，全 1053 条一致）：

  | FavorRank | 2 | 3 | 5 | 6 | 8 | 9 / 15 |
  |---|---|---|---|---|---|---|
  | 青辉石 | 20 | 40 | 60 | 80 | 100 | 120 |

- `SecretStoneAmount` 全部为 1（神名文字/角色碎片），但**抓包里 `DisplaySequence` 只有青辉石、没有碎片**——
  碎片可能不经此接口发放，待核实（不要当成已确认）。
- `FavorScheduleRecords`：**所有角色的已完成日程**，58 个角色有记录 → 天然的"哪些剧情做过了"清单
- 领奖与剧情完成是**同一个请求**，不需要额外 claim

## 三、三段式流程（对应 测试号 描述）

**一轮 = 三段，必须整轮跑完才解锁下一轮**（测试号 2026-10-22 确认的游戏机制）：

| 阶段 | 客户端行为 | 服务端请求 |
|---|---|---|
| ① 手机互发信息 | 打开会话，逐组显示消息/选项 | `messagelist` → 多次 `read` |
| ② 进入剧情拿奖励 | 点剧情入口 → 播放/跳过 → 结算 | `scenario/skip` → `scenario/grouphistoryupdate` → `momotalk/favorschedule` |
| ③ 回手机收尾 | 继续显示后续消息，本轮结束 | 继续 `read` |

- 客户端表现：第①段没读完不会出现剧情入口，第②段不结算不解锁下一轮消息（测试号 观测）
- **但服务端不校验这个顺序**（2026-10-28 实测）：未读的剧情组可直接 `grouphistoryupdate` + `favorschedule` 领奖，
  `read` 也能越过 `Latest`。所以"整轮跑完"是客户端 UI 的约束，不是服务端规则——自动化可以按剧情清单直接收割
- 主页未读数（本次观测 244）量级上对应「当前这一轮还没读的消息」，是**客户端本地计数**，
  服务端 `MomoTalkOutLineDB` 没有 lastRead 字段

**触发链**（全部可由本地表推算）：
```
MessageGroupId --(AcademyMessangerExcel.FavorScheduleId)--> ScheduleId
ScheduleId --(AcademyFavorScheduleExcel.ScenarioSriptGroupId)--> ScriptGroupId
           --(同表 RewardParcelType/Id/Amount + SecretStoneAmount)--> 奖励内容
```
例：消息组 `100020050` → `FavorScheduleId 100022` → `ScriptGroupId 1000202` → 免费青辉石×20。

## 四、本地表（均在 `tables/full/ExcelDB/`）

### AcademyMessangerExcel.json（15050 行 / 253 角色）
| 字段 | 说明 |
|---|---|
| `MessageGroupId` | 消息组，递增步长 10 |
| `Id` | 组内消息 id（Answer 的 Id 即 `ChosenMessageId`） |
| `CharacterId` | 学生 id（晴奈 10002） |
| `MessageCondition` | `Feedback`(7002 学生发言) / `Answer`(3654 玩家回复) / `FavorRankUp`(1049 好感升级) / `None`(3345 空占位) |
| `ConditionValue` | 条件值（如好感等级） |
| `FavorScheduleId` | 非 0 → 本组触发剧情 |
| `NextGroupId` | 下一组；`0` 表示链结束（458 行） |
| `FeedbackTimeMillisec` | 学生"正在输入"延迟 |
| `MessageType` | `Text` / `Image` / `None` |
| `MessageKR` | 正文（韩文原文；中文本地化在 Localize 表，客户端内显示中文） |

统计：`Answer` 组 2776 个（1898 个单选项、878 个双选项）；纯 `Feedback` 组 4316 个；
带 `FavorScheduleId` 的组 1053 个（= FavorSchedule 表行数，一一对应）。

### AcademyFavorScheduleExcel.json（1053 行）
`Id` / `CharacterId` / `ScheduleGroupId` / `OrderInGroup` / `Location` / `LocalizeScenarioId` /
`FavorRank` / `SecretStoneAmount` / `ScenarioSriptGroupId` / `RewardParcelType` / `RewardParcelId` / `RewardAmount`

- `FavorRank`：剧情需要的好感等级（100022 → 2 级）
- `SecretStoneAmount`：青辉石奖励数（100022 → 1）

### ScenarioScriptExcel.json（362158 行）
剧情正文（含 `#title;` / `#place;` / `#na;角色;台词` 等指令前缀），一个组约 88–95 行。
MomoTalk 剧情是**纯本地播放**，服务端不参与。

## 五、实测结论（2026-10-28，晴奈实测）

用 `scripts/` 外的临时探针直接发请求，逐项验证。**结论：自动化只需 2 个请求/条剧情，read 和 skip 都不是必需的。**

| 验证项 | 结果 |
|---|---|
| `read` 推进一组 | ✅ `LatestMessageGroupId` 更新为该组 |
| `read` 幂等 | ✅ 重复读同一组返回 OK、`Latest` 不变，可放心重复执行 |
| 越过 `Latest` 往前读 | ✅ `read(250)` 直接成功（当时 Latest=240），**服务端不校验读取顺序** |
| **未读剧情直接登记完成** | ✅ Latest=250 时直接 `ghu(1000206)` 成功（该剧情组 290 根本没读过） |
| `skip` 是否必需 | ❌ **不需要**。不传 skip 直接 `grouphistoryupdate` 就能完成，skip 只是"点了跳过"的上报 |
| `favorschedule` 领奖 | ✅ 返回 `DisplaySequence`，并写入 `FavorScheduleRecords` |
| 重复领奖 | ❌ `400 Alreday Attend Favor Schedule {100025}`（服务端拼写如此），**幂等**，不会重复发 |
| `loginsync` 拿全量状态 | ✅ **必须带 `SyncProtocols`**，其中 `33000`(MomoTalk)、`19000`(剧情)、`20000`(角色) 决定返回哪些块；空体只回默认子集 |
| **`MomoTalkOutLineDBs` 能不能当角色清单** | ❌ **不能**，它只含"有过互动的角色"（测试号 174 名册里只有 60 条）。无会话记录的艾米（10001）实测 `ghu + favor` 照样成功 → 角色清单必须用**名册 ∩ 剧情表**；会话记录只用于标注「是否开始过」和带出 `LatestMessageGroupId` |
| **领奖后客户端表现**（测试号 实测） | ⚠️ 能用但需刷新一次：第一部分消息照常播放，**当次不弹剧情入口**；回主页重进 MomoTalk 后正常播放第三部分、并进入下一轮。服务端侧 `ghu` 会**自动创建会话记录**（`started` false→true，`Latest` 0→`101230080`），不需要先"激活"角色 |
| **`read` 能不能越过未完成的剧情组** | ❌ **不能**。圣娅（10110）从起点连读 6 组到第一轮剧情组 `101100060` 成功，再读 `101100070` 报 `400 could not update message group id {101100070}, failed at groupId {101100070}`。→ **剧情组是闸门**：领奖不看进度（可直接领），读消息看剧情（没完成不让往下走） |
| `CharacterDBId` 从哪来 | 等于名册 `CharacterListResponse.CharacterDBs[].ServerId`（晴奈 529404 / 圣娅泳装 3235486 / 圣娅 2969203 都对上）。所以**没有会话记录的角色也能 read** |
| **`Answer` 组传 `null` 行不行** | ❌ **不行**。服务端返 200、`latest` 也在涨，但**这次推进不被客户端承认**，重进 MomoTalk 会从该组重放（测试号 实测：推到 `101100090` 后进游戏，仍停在第一轮第三部分）。必须传有效 `ChosenMessageId` —— 取该组第一条 `Answer` 的 `Id` |
| read 中途能不能停 | ✅ 能。正常关闭 MomoTalk 进度会保存，不需要一口气推完；**只有 `Answer` 组传 null 才会作废**。所以批量执行不需要抢一锤子买卖 |




### 奖励实测（修正第四节的推断）

`favor(100026)` 的 `DisplaySequence`：
```json
[{"Key":{"Type":8,"Id":10002},"Amount":1},   // 神名文字：Type 8，Id=CharacterId
 {"Key":{"Type":2,"Id":3},"Amount":80}]      // 免费青辉石 80（好感 6 档）
```
- **神名文字确实走这个接口发**，`Type:8`，Id 是 CharacterId —— 不是之前推测的"不经此接口"
- 但 10-22 抓包的 `favor(100022)` 只有青辉石、没有碎片条目，两次不一致，**原因未查明**（可能与碎片已满/首次完成标记有关），实现时不依赖碎片条目

### 仍然未知

1. **好感不足时 `favorschedule` 是否校验** `FavorRank`：主动没测——那等于跳过门槛拿不该拿的奖励，
   收益不正当且有风险。自动化按好感过滤即可（5 条卡好感的留在原地）。
2. **不 read 只领剧情后，客户端会话状态如何**：服务端允许，但游戏里会不会仍显示未读/红点，未验证。
   保守实现可以顺手 `read` 一次（幂等、无害）。
3. 33003 仍未观测到。
4. `OutLineDB.ChosenMessageId` 语义仍未解（0 / -1 / 具体 id 混用），但自动化不需要它。

## 六、自动化设计（按实测简化）

```
① loginsync(SyncProtocols=[...33000, 19000, 20000...])
   → CharacterListResponse.CharacterDBs  ← 角色清单用这个（174 个）
   → FavorScheduleRecords               ← 已完成清单，按 CharacterId 分组
   → MomoTalkOutLineResponse.MomoTalkOutLineDBs ← 只标注 started / Latest，**不能当清单**

② 对名册里每个角色，遍历 AcademyFavorScheduleExcel 里该角色的剧情：
     若 Id 已在 FavorScheduleRecords → 跳过
     若 FavorRank > 当前好感     → 跳过（不越界）
     否则：
        read(CharacterDBId, 剧情所在 MessageGroupId, 该组 Answer 的 Id 或 null)   # 可选，仅为了客户端状态干净
        grouphistoryupdate(ScenarioSriptGroupId, 4)
        favorschedule(Id)                                                        # 领 20~120 青辉石 + 1 神名文字

③ 记录本次结果，落盘
```

**不需要**：skip、逐组连推消息、维护读取进度。按名册全量算，2026-10-28 首跑快照是
143 个角色 / 475 条剧情 / 26000 青辉石（≈950 次请求，5~8 分钟）。

### 两个独立操作

| 操作 | 接口 | 耗时 | 说明 |
|---|---|---|---|
| **领取奖励** | `POST /api/momotalk/claim` | 秒级~分钟 | 只发 `ghu + favor`。剧情登记完成，但**不动消息已读**，客户端红点还在 |
| **清红点并领奖** | `POST /api/momotalk/readall` | 20~30 分钟 | 每角色从 `latest` 沿 `NextGroupId` 读到链尾，**遇未完成剧情组顺手领**。`read` 才是清红点的手段 |

两者可任意顺序、任意重复执行：已完成剧情会被 `FavorScheduleRecords` 排除；并发撞上时服务端报
`Alreday Attend`，代码当幂等成功。

清红点的约束（都踩过）：
- `Answer` 组必须传有效 `ChosenMessageId`（取该组第一条 `Answer` 的 `Id`），传 `null` 会让整次推进作废
- 剧情组是闸门：该轮剧情没登记，`read` 下一组会报 `failed at groupId`
- `latest` 只能往前，传低于当前值的组会被拒 → 必须先取实时值
- 判断"这组是不是剧情组"要扫**整组**的 `FavorScheduleId`，只看第一行会漏（`101100200` 就踩过）

实现：`webui/momotalk.py`（state / claim / readall / readstatus / readstop）+ 一键清 runner `momotalk`
（只挂"领取奖励"，清红点不进每日流程）+ 前端两个按钮（清红点后台跑、前端 1.5s 轮询进度），
纯逻辑单测在 `tests/test_momotalk.py`。


## 七、只读进度盘点（离线脚本）

脚本：`scripts/momotalk_overview.py`，**零请求**，只读 `$AUTOBA_CAPTURE_DIR` 里最新的 loginsync
+ 本地剧情表。口径与模块的 `build_state` 一致：**名册 ∩ 剧情表**，排除 `FavorScheduleRecords` 已完成，
按好感分「可领 / 卡好感」两类（"尚未读到"那一档已取消，理由见第五节）。

**实时数据以 WebUI `/api/momotalk/state` 为准**；脚本适合没有会话、只想看抓包快照时用。

2026-10-22 抓包快照结果：名册 174 人全部有剧情定义，可领 478 条 / 26200 石，卡好感 24 条 / 2020 石。
（同一天 17:00 的实时值是 461 条 / 25180 石——差值来自这几天领掉的剧情，不是口径问题。）

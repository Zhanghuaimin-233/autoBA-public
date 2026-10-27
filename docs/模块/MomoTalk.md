# MomoTalk

> **状态**：定案（未实现）｜ **日期**：2026-10-22

抓包现场：2026-10-22 22:33–22:35，master 手动跑完晴奈一条完整 MomoTalk（互发信息 → 剧情 → 回手机继续），
中途退主页重连过一次。全流程落 80 条样本，其中 MomoTalk/剧情 16 条。

## 一、结论摘要

MomoTalk **不是**一个"发消息"接口，而是**消息组推进器**：

- 对话正文（谁说了什么、选项文本）**全在客户端本地表**，服务端只存"读到哪个组 / 选了哪条"
- 一次 `read` = 推进一个 `MessageGroupId`
- 消息组带 `FavorScheduleId` 时，客户端弹剧情入口；剧情正文也在本地（`ScenarioScriptExcel`）
- 剧情"播放"没有服务端交互，只有**跳过上报**和**完成记录**，然后单独调 `favorschedule` 领奖励

对自动化最有利的一点：**不需要真的播放剧情，也不需要发聊天内容**——只有 5 个请求。

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

## 三、三段式流程（对应 master 描述）

**一轮 = 三段，必须整轮跑完才解锁下一轮**（master 2026-10-22 确认的游戏机制）：

| 阶段 | 客户端行为 | 服务端请求 |
|---|---|---|
| ① 手机互发信息 | 打开会话，逐组显示消息/选项 | `messagelist` → 多次 `read` |
| ② 进入剧情拿奖励 | 点剧情入口 → 播放/跳过 → 结算 | `scenario/skip` → `scenario/grouphistoryupdate` → `momotalk/favorschedule` |
| ③ 回手机收尾 | 继续显示后续消息，本轮结束 | 继续 `read` |

- 第①段没读完**不会**出现剧情入口（第二阶段），第②段不结算**不会**解锁下一轮的消息
- 因此服务端 `LatestMessageGroupId` 只会停在本轮边界内，自动化必须**按 `NextGroupId` 顺序逐组推进**，
  不能跳轮、不能只处理最后一组
- 主页未读数（本次观测 244）量级上对应「当前这一轮还没读的消息」，
  而不是全部剩余消息（全部剩余实测 604 条，对不上）

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

## 五、待实测 / 未知

1. **`SkipPointScriptCount` 语义**（最关键）：实测 6/5，脚本 95 行，不是行数。可能是"跳过的检查点数"。
   需实测：传 0 / 1 / 999 各一次，看服务端是否校验（若宽松，自动化固定传大值即可）。
2. **read 幂等性**：对已读组重复 read 是否报错/有副作用。决定自动化能否"从任意组重推"。
3. **`OutLineDB.ChosenMessageId` 语义**：观测到 0 / -1 / 158（158 不属于当前 Latest 组的 Id 集合），
   与"本组是否已选"没有稳定对应关系，暂不作为进度判据。
4. **`LatestMessageGroupId` = "读到的位置"**（实测证据：同一账号两次 loginsync 对比，
   22:31 晴奈 `100020050` → 22:33–22:34 连读 8 组 → 22:43 变 `100020200`）。
   所以本地不必额外存进度，重登一次就能恢复；但注意它不等于"服务端已推送的最新"。
5. **好感门槛**：`FavorRank` 未达标时 favorschedule 返回什么错误码，未验证。
6. **能否直接 read 一个"尚未读到"的组**（越过 Latest 往前推）：未验证。若服务端不校验，
   自动化可以一路 `NextGroupId` 读到底；若校验，必须从 Latest 起逐组推。
7. **33003 空缺**：33001/33002/33004 已覆盖，33003 未知（可能未使用）。

## 六、自动化设计草案

```
① loginsync → MomoTalkOutLineResponse.MomoTalkOutLineDBs  (CharacterDBId↔CharacterId↔LatestGroup)
                + FavorScheduleRecords (已完成清单)
② 对每个有进度的角色：
     group = LatestMessageGroupId          # 本轮起点；不能跳轮
     while group:
         rows = 表[group]
         chosen = 第一条 Answer.Id if 该组有 Answer else None
         read(CharacterDBId, group, chosen)      # 推进一组；服务端据此解锁下一组
         if rows.FavorScheduleId and 未在 FavorScheduleRecords:
             skip(ScriptGroupId, <待定值>)
             grouphistoryupdate(ScriptGroupId, 4)
             favorschedule(FavorScheduleId)      # 领 20~120 青辉石
         group = rows.NextGroupId
③ 记录本次处理到的组，落盘
```

关键约束：**一轮三段必须连续跑完**（读消息 → 剧情结算 → 收尾消息），否则 `LatestMessageGroupId` 不会前进，
下一轮也不会解锁。这决定了模块不能"只扫最新一组"，必须整链推进。

请求侧只需在 WebUI 加 5 个路由（现有 `ba_session` 直接可用），无需新协议能力。

## 七、只读进度盘点（首版跑通）

盘点口径（零请求，读抓包快照 + 本地表）三分类：

| 分类 | 判据 | 含义 |
|---|---|---|
| 可触发 | `FavorRank <= 当前好感` 且 `消息组 <= LatestMessageGroupId` | 读一下消息就能弹剧情 |
| 尚未读到 | `FavorRank <= 当前好感` 且 `消息组 > LatestMessageGroupId` | 按 `NextGroupId` 继续读即可推到位 |
| 卡好感 | `FavorRank > 当前好感` | 先刷好感 |

首跑结果（2026-10-22 22:43 快照）：60 个角色会话、未完成剧情 51 条
（可触发 2 / 尚未读到 44 / 卡好感 5），按好感分档折算 **青辉石 4740 颗 + 神名文字 51 个**。
卡好感的 5 条集中在千夏、好美、晴、莲见、铃美（好感 10–13，门槛 15，各 120 石）。

**未读数复算**（校验模型）：按「从 `LatestMessageGroupId` 到下一个剧情组的全部消息」口径算出 271，
与 master 观测的 244 同量级（差异应为快照时间差）；而「全部剩余消息」是 604、"全部剩余 Feedback" 是 274+
——只有"当前轮"口径能对上，佐证三段一轮的模型。

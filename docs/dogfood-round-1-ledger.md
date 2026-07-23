---
schema: unknowns-ledger-v1
feature: c3-hearst-is-a
created: 2026-07-23
updated: 2026-07-23
status: complete
quiz_passed: false
quiz_attempts: 1
---
## UNK-001
- quadrant: known-unknown
- impact: architecture
- status: resolved
- technique: interview
- statement: 地图与疆域不符——hearst_isa.py 已完整存在（350 行、有测试、prov 已接线），"C3 未做"是过时信息；真正的功能范围需要重新定义（集成？还是别的？），只有你能决定。
- resolution: 访谈裁决（2026-07-23）：方向 A——把 seed_specializes 接入 Step-7 流程，Hearst 确定性候选边先行生成、作为 LLM-confirm 的输入种子；理由是确定性+可溯源符合工厂信仰，源文语料扩展留作后续。同时顺带更新 state-of-the-factory 的过时行。

## UNK-002
- quadrant: known-unknown
- impact: architecture
- status: resolved
- technique: interview
- statement: 输入语料选择——模块自述"在蒸馏后的 principle 语句上信号稀薄，真实产出在枚举式源文 prose 上"；集成时喂 principles、源文、还是两者，决定整个数据流。
- resolution: 由 UNK-001 的 A 裁决附带决定：v1 集成沿用 principle 语句（现有数据流，明知信号偏薄）；源文 prose 语料管道显式推迟为后续功能，不进本次范围。

## UNK-003
- quadrant: known-unknown
- impact: architecture
- status: resolved
- technique: reference-hunt
- statement: docstring 说 candidate 边留给"LLM-confirm 步骤"裁决，prov 里也登记了 llm-confirm 活动——但这个步骤是否已实现？
- resolution: 已实现且已实战——docs/enhancement-steps/step-7-multisource.md 记载 Phase A/C LLM-confirm 在 software-design-simplicity-advisor 包上产出 principle-clusters.json（4 个 llm-confirmed 簇）+ principle-graph.json（24 条边，其中 2 条 specializes）；validate_principle_clusters.py 对 llm-confirmed 簇有校验。Hearst seed 喂的下游是现成的。

## UNK-004
- quadrant: known-unknown
- impact: architecture
- status: resolved
- technique: reference-hunt
- statement: seed_specializes 产出 principle-graph-v1 的 specializes 边——下游谁消费这些边（合并决策？画像层级？测试）？
- resolution: specializes 边归宿是 principles/principle-graph.json（Step 7 Phase C 工件，tier-gated）；validate_principle_graph.py 校验引用完整性且 refines+specializes 层级子图必须无环；conflicts 类边由 render_conflict_log.py 呈现。消费链路完整存在，2026-07-23 检索确认。

## UNK-005
- quadrant: assumption
- impact: local
- status: resolved
- technique: reference-hunt
- statement: 假设：当前环境没有 spaCy/nltk 时，flat regex 路径的召回也足以支撑集成的验证工作。
- resolution: 部分证实——spaCy/nltk 均未安装（import 失败）；test_hearst_isa.py 8 过 2 跳（跳过的正是 spaCy 用例），flat 回退路径有专门测试且可用。"召回足够"只对验证工作成立；生产质量召回仍依赖可选 nlp extra（docstring 自述 flat 高精度低召回）。

## UNK-006
- quadrant: unknown-known
- impact: local
- status: resolved
- technique: brainstorm-prototype
- statement: "好的 is-a 集成产出"长什么样你说不出但看到能认——需要拿真实包的数据跑出候选边给你反应（等 UNK-002 定了语料再做）。
- resolution: 原型已跑（software-design 包）：2 条低置信候选边、一条明显可疑、WordNet 关闭。用户反应（2026-07-23）：接受该质量水位——低精度种子由 LLM-confirm 过滤是设计内；但集成必须同时修掉 source_texts 为空时静默回退到 principles 的 footgun（改为显式警告）。nlp extra 文档化不进本次范围。
- note: 原型还发现 --sources 对照在该包上根本没生效（无 sources/markdown/*.md），正是该 footgun 的现场实例。

## Quiz — attempt 1
### Q1 [UNK-001]
问：本功能最终裁定的范围是什么？为什么选它，而不是"直接上源文语料"或"宣布已完成只改文档"？
- answer: 用户表示无法作答——本轮决策均为采纳推荐选项，未形成可复述的理解
- verdict: missed
### Q2 [UNK-003]
问：Hearst 种子产出的候选边，下游由什么机制裁决？我们当时是靠什么证据确认该机制真实可用的？
- answer: 用户表示无法作答——本轮决策均为采纳推荐选项，未形成可复述的理解
- verdict: missed
### Q3 [UNK-005]
问：在没有 spaCy/nltk 的环境里，抽取器靠什么路径工作？"召回足够"这个假设被证实到什么程度——对什么成立、对什么不成立？
- answer: 用户表示无法作答——本轮决策均为采纳推荐选项，未形成可复述的理解
- verdict: missed
### Q4 [UNK-006]
问：原型在真实包上暴露了一个必须修的 footgun——它是什么行为？本次集成把它改成了什么行为？
- answer: 用户表示无法作答——本轮决策均为采纳推荐选项，未形成可复述的理解
- verdict: missed

### 收账警告（fully-revealed closure）
- verdict-final: quiz_passed false —— attempt 1 四题全 missed 后，用户选择教学优先；UNK-001、UNK-003、UNK-005、UNK-006 的判定依据已全部在对话中揭示（revealed），按规则本 ledger 不再存在可通过路径，以 complete + quiz_passed: false 收账。merge go-ahead 未发放（advisory：是否并入 master 由用户决定）。

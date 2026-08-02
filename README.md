# 📡 新闻联播商机解读 (Xinwen Lianbo Business Opportunity Decoder)

> 新闻联播不是新闻，是加密的政策信号源。这条 Skill 帮你解码。

一个 WorkBuddy / Claude Code / CodeBuddy 兼容的 Agent Skill，将新闻联播、外交辞令、政策文件中的措辞转化为结构化的商机解读报告。

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Agent Skills](https://img.shields.io/badge/Agent%20Skills-Compatible-green)]()
[![WorkBuddy](https://img.shields.io/badge/WorkBuddy-Ready-8A2BE2)]()

---

## 核心能力

输入一段政策新闻或外交表态文本 → 输出一份七节商机解读报告：

| 分析环节 | 工具 |
|---------|------|
| **信号提取** | 四层信号体系（宏观定调 → 行业落地 → 风险规避 → 信息结构） |
| **措辞解码** | 五套密码本（双边会谈 / 发言人表态 / 关系定位 / 经济政策 / 会议总结） |
| **深度归因** | 三问模型（为什么是现在？为什么是这个方向？普通人机会在哪？） |
| **交叉验证** | 多密码本联动判读，3+ 信号共振才下结论 |
| **量化评分** | 五维打分（明确性 / 层级 / 可落地性 / 一致性 / 时间窗口） |

---

## 快速开始

### 安装

**方式一：一键安装（WorkBuddy）**

将本仓库克隆到 `~/.workbuddy/skills/` 目录：

```bash
git clone https://github.com/zbcloading/xinwenlianbo-shangji.git ~/.workbuddy/skills/xinwenlianbo-shangji
```

**方式二：手动复制**

下载 `SKILL.md` 和 `references/` 目录，放到你的 Agent Skills 目录中。

### 使用

在 WorkBuddy 中直接发送需要分析的新闻文本：

```
帮我分析这段新闻联播内容里的商机：
"国务院总理主持召开国务院常务会议，研究推进新型工业化有关工作..."
```

```
这段外交部表态什么意思？
"中方对此表示严重关切，敦促有关方面慎重行事..."
```

Skill 会自动激活，走完完整的六步分析管线，输出结构化报告。

---

## Skill 结构

```
xinwenlianbo-shangji/
├── SKILL.md                      # Agent Skill 定义（分析工作流 + 输出模板）
├── references/
│   └── methodology.md            # 完整方法论（含五套措辞密码本 A-E）
├── README.md                     # 本文件
└── LICENSE                       # MIT
```

---

## 方法论文档

| 密码本 | 内容 | 用途 |
|--------|------|------|
| **A** | 双边会谈措辞（合作←→分歧光谱） | 判断国际合作前景 |
| **B** | 外交部发言人表态（5 级分层） | 定位冲突烈度和政策底线 |
| **C** | 国家关系定位层级 | 判断双边关系深度 |
| **D** | 经济政策措辞 | 识别政策支持力度 |
| **E** | 会议与工作总结措辞 | 判断政策推进阶段 |

完整方法论文档存储在 `references/methodology.md` 中。

---

## 兼容性

| 平台 | 状态 |
|------|:----:|
| WorkBuddy | ✅ |
| Claude Code | ✅ |
| CodeBuddy | ✅ |
| 其他 Agent Skills 兼容平台 | ✅ |

---

## 适用人群

- 关注宏观趋势的投资者
- 外贸从业者（判断双边关系冷热）
- 创业者（识别产业政策窗口）
- 战略规划人员（中长期趋势研判）

## 边界

✅ **适合**：6-18 个月中长期产业趋势 / 外贸合作评估 / 规避政策打压行业  
❌ **不适合**：短线投机 / 精确择时 / 无行业知识的新手直接操作

---

## License

MIT © 2026

---

## 致谢

- [nuwa-skill](https://github.com/alchaincyf/nuwa-skill) — Skill 发布结构参考

# Text-Multimodal — 把文本模型升级为多模态助手

一套开箱即用的 **SKILL**：任何文本模型助手（Claude / ChatGPT / Gemini / Cursor / Copilot / ZCode / 本地模型……）加载后，即可从零构建完整的多模态能力体系——**看图、识视频、生成图片、生成视频**，且所有结果尽量在聊天窗口中内联预览。

## 核心思路

不更换主模型，而是"能力外挂"：

- **主模型 = 大脑**：理解需求、判断任务、撰写提示词、协调流程、整理输出
- **专门多模态模型 = 感官与手**：识别与生成由用户配置的模型完成
- **统一委托通道 = 神经通道**：适配器模式的委托脚本，与具体模型解耦

## 使用流程（技能自动执行）

1. **能力自检**：盘点自身工具（终端/文件系统/网络），选定执行模式（全能 A / API B / 指令 C）
2. **先查后要**：先检测环境（Agent 配置）已有模型，能覆盖的能力优先复用（零成本）
3. **安全承诺**：需要用户提供 baseURL + API Key 时，先逐条声明安全处理方式（绝不外泄、只存本地、全程脱敏、可随时撤销）
4. **自动匹配**：拉模型清单 → 能力覆盖检查 → 逐能力匹配 → 纯色探测/最小请求实测 → 《能力-模型匹配表》→ 用户拍板
5. **阶段施工**：委托通道 → 四能力逐个接入（每能力完成"真实往返验证"：生成 → 回读识别 → 对比 → 用户确认）
6. **展示规范**：`media_out/` 相对路径嵌入、完整性校验、缩放、视频 faststart 转码
7. **固化交付**：协议入全局配置 + 冒烟脚本 + 交付报告

**部分支持照常交付**：供应商只支持一/两/三种能力时，支持哪些就接入哪些，不支持的如实标注，不阻塞其他能力。

## 目录结构

```
Text-Multimodal/
├── SKILL.md                 # 主文件：流程速览、铁律、完成定义（触发即加载）
├── references/
│   ├── matching.md          # 模型来源全流程（先查后要、安全承诺、自动匹配）
│   ├── steps.md             # 阶段 0~4、7 施工细节 + 提示词撰写规范
│   ├── display.md           # 展示规范 + 客户端内联渲染补丁
│   └── pitfalls.md          # 踩坑清单（实测踩坑，直接遵守）
├── scripts/
│   ├── vision_probe.py      # 纯色探测图生成器（验证模型能否看图）
│   └── delegate_skeleton.py # 委托脚本骨架（适配器模式）
└── assets/
    └── tables.md            # 能力表 / 匹配表模板
```

## 安装

技能本质是一个目录：`Text-Multimodal/`（内含 `SKILL.md` + `references/` + `scripts/` + `assets/`）。安装 = 把这个目录放到你的 Agent 能发现技能的位置，或把 `SKILL.md` 全文发给助手。以下方法任选其一。

### 方法一：git clone + 复制到技能目录（推荐，便于更新）

```bash
# 1. 克隆仓库
git clone https://github.com/wxg-jmq/Text-Multimodal.git
cd Text-Multimodal

# 2. 复制到用户级技能目录（全局可用，所有支持技能的 Agent 通用）
mkdir -p ~/.agents/skills
cp -r Text-Multimodal ~/.agents/skills/

# 或复制到项目级技能目录（仅当前项目生效）
cp -r Text-Multimodal <你的项目>/.agents/skills/
```

### 方法二：直接复制技能目录

从任意来源（本仓库、他人分享）拿到 `Text-Multimodal/` 目录后：

```bash
# 用户级（所有项目可用）
cp -r Text-Multimodal ~/.agents/skills/

# 项目级（仅该项目可用）
cp -r Text-Multimodal <你的项目>/.agents/skills/
```

> Windows 用户：可直接把 `Text-Multimodal` 文件夹复制到 `%USERPROFILE%\.agents\skills\` 或项目下的 `.agents\skills\` 里。

### 方法三：符号链接安装（更新即生效）

```bash
mkdir -p ~/.agents/skills
ln -s <克隆位置>/Text-Multimodal/Text-Multimodal ~/.agents/skills/Text-Multimodal
```

之后 `git pull` 更新仓库，技能立即生效，无需重复复制。

### 方法四：放入各 Agent 的原生技能目录

大多数支持技能的 Agent 都遵循"SKILL.md 目录"约定，把技能目录放到对应位置即可（具体以你的 Agent 文档为准）：

| Agent / 系统 | 技能目录（常见位置） |
|---|---|
| 跨工具标准（大多数 Agent 通用） | `~/.agents/skills/`、`<项目>/.agents/skills/` |
| Claude（Code / 桌面端 / Agent Skills） | `~/.claude/skills/`、`<项目>/.claude/skills/` |
| 其他支持技能的 Agent | 查阅其文档中的"技能 / Skills"目录配置 |

### 方法五：不支持技能目录的 AI 平台（网页版 ChatGPT / Claude / Gemini …）

把 `SKILL.md` 全文作为首条指令粘贴到对话中即可。技能内置"三档执行模式"（A 全能 / B API / C 指令），会自动适配平台能力：有终端就全自动施工，没终端就产出脚本和命令由你执行；遇到问题时再按需粘贴对应的 `references/` 文件。

### 方法六：一键安装（从 GitHub 直接装到用户级目录）

```bash
git clone https://github.com/wxg-jmq/Text-Multimodal.git /tmp/Text-Multimodal
mkdir -p ~/.agents/skills
cp -r /tmp/Text-Multimodal/Text-Multimodal ~/.agents/skills/
rm -rf /tmp/Text-Multimodal
```

### 验证安装

- **新开一个会话**（技能列表通常在会话启动时加载），直接说"帮我生成一张图"或"识别这张图片"——能触发技能即安装成功
- 或在支持斜杠命令的 Agent 里输入 `/Text-Multimodal` 强制加载

## 你需要准备什么

- 可选的：环境里已配置的模型（技能会先检测并优先复用，零成本）
- 可选的：一个或多个多模态供应商的 **baseURL + API Key**（技能会先作安全承诺再接收）

## 设计原则

- **诚实**：失败如实报告（含任务 id），严禁谎称成功；客户端不支持预览就明说并给替代方案
- **验证闭环**：每接入一个能力必须真实往返测试（生成 → 回读 → 对比）并让用户确认
- **防重踩坑**：`references/pitfalls.md` 固化了所有实测踩坑（绝对路径破图、moov 前置、4MB 预览上限、多域名存储桶端点、队列限流……）
- **密钥安全**：只存本地凭据文件、全程脱敏、不写入任何文档/脚本/报告

## 许可证

MIT

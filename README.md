# 微信表情包整套生成与上架 · WeChat Sticker Pack

> 一套给 AI Agent 用的**流程骨架**：从一句「做套表情包」到 16 张能直接提交微信表情开放平台的透明 GIF。流程、规范、脚本由技能提供；角色形象与逐张提示词由你填表提供。
> A workflow skeleton for AI agents building store-ready WeChat sticker albums — the process is packaged, the prompts are yours to fill.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB.svg)](requirements.txt)

---

## 安装（30 秒）

**给 WorkBuddy / Claude Code 用**——技能就是「一个含 `SKILL.md` 的文件夹」：

```bash
# 方式一：命令行
git clone https://github.com/<你的用户名>/wechat-sticker-pack.git
cp -R wechat-sticker-pack ~/.workbuddy/skills/      # Claude Code 换成 ~/.claude/skills/
```

**方式二：不装 git**——到 [Releases](../../releases/latest) 下载 `wechat-sticker-pack.zip`，解压到同一目录：

```
~/.workbuddy/skills/wechat-sticker-pack/SKILL.md   ← 必须是这个层级
```

装完新开一个会话，说「做一套表情包」。**技能生效的样子是先问你上传参数**，不是直接开始画；没反应就是没装上，先看路径对不对。

**只想用脚本，不装技能**：

```bash
pip install -r requirements.txt          # Pillow + numpy + opencv-headless
python3 scripts/cutout.py 原图.png 角色.png --height 640 --pad 30
```

**用 Codex 等终端 Agent**：读 [`AGENTS.md`](AGENTS.md)。
**用纯对话平台（DeepSeek / 豆包）**：把 [`adapters/chat-only.md`](adapters/chat-only.md) 整个粘进去。

---

## 分工：技能给框架，内容你来填

| 由你提供（填《提示词填空表》） | 由技能提供 |
|---|---|
| 角色长相、发型、服装、配饰、气质 | 必须填哪些字段、每项写到什么颗粒度 |
| 画风：线条、上色、比例、配色、禁用色 | 把「不可复现」的写法改成可复现的 |
| 逐张姿势与表情 | 相邻两张不许撞的校验规则 |
| 名称是否采用 | 按主题风格给候选名 |
| — | 抠透明、叠字、GIF 合成、像素级验收 |

技能**不代写**形象与姿势。写出一个不属于你的角色，会让后面 N 张全部跑偏，返工比重填表单贵得多。

## 它解决什么问题

用 AI 生成一整套表情包，真正难的不是「画一张好看的」，而是这四件事：

| 坑 | 后果 | 本技能的处理 |
|---|---|---|
| 一张母图重复 N 次，只换文字 | 动态表情却姿势一模一样，废套 | 姿势与表情是**逐张变量**，母图只锁造型与画风 |
| 白底图直接抠透明 | 深色聊天底上一圈白边、耳饰周围留白块 | 四步抠图：四边连通色 → 闭环空洞 → 白描边剥离 → 颜色回填 |
| 文字让模型画 | 错字、繁体、伪字符 | 文字一律排版层叠加，模型只画角色 |
| 批量出图前不验证 | 16 张一起返工，积分白烧 | 五个确认关卡 + 单张试点，不通过不批量 |

## 流程（S0–S11，六道关卡）

```
S0  确认上传参数（静态/动态 · 格式 · 张数 · 母图来源 · 文字位置）   ★ 停住问
S1  平台附加信息（类型 · 角色 · 风格 1–2 项 · 主题）                ★ 停住问
S2  交出《提示词填空表》，你填完再继续                              ★ 停住问
S3  用你填的 A 区拼母图提示词，生成 1 张母图
S4  母图交用户验证                                                ★ 停住问
S5  按主题风格推荐名称，逐张征询是否采用（N 张 = N 次）            ★ 停住问
S6  总览排版图（N 格）
S7  版型确认                                                      ★ 停住问
S8  黑底 / 白底验证图
S8b 单张成品试点（抠透明＋文字＋GIF 全链路）
S9  批量生成，只换姿势与表情
S10 抠透明 + 叠字 + 逐张像素级校验
S11 交付 N 个成品；按需补上架素材与文案
```

## 三十秒上手

```bash
git clone https://github.com/<your-name>/wechat-sticker-pack.git
cd wechat-sticker-pack
pip install -r requirements.txt
```

**有文件系统的 Agent**（Claude Code / Codex / WorkBuddy / 自建 Agent）：把整个目录放进技能目录，或直接让它读 `SKILL.md`。

```bash
# Claude Code
cp -R wechat-sticker-pack ~/.claude/skills/
# WorkBuddy
cp -R wechat-sticker-pack ~/.workbuddy/skills/
```

**只能对话的平台**（DeepSeek / 豆包 等）：用 [`adapters/chat-only.md`](adapters/chat-only.md)，单文件自包含，不需要 Python。

各平台细节见 [`INSTALL.md`](INSTALL.md)。

## 脚本（可单独使用，不依赖 Agent）

```bash
# 1. 白底角色图 → 干净透明图（四步抠图，去白边）
python3 scripts/cutout.py 源图.png 角色.png --height 700 --pad 30

# 2. 透明角色 → 240×240 透明 PNG + 5 帧循环 GIF
python3 scripts/compose.py 角色.png out/01.png --text "就这"

# 3. 上架三件套：横幅 750×400 / 封面 240×240 / 图标 50×50 / 角色图 700
python3 scripts/assets.py 角色.png 上架素材 \
  --logo 徽标_浅色.png --title "银灰先生" --subtitle "嘴硬日常 · 16 款动态表情" --tag "怼人/斗图"

# 4. 工作室纯图形徽标（车标式，无文字）
python3 scripts/mark.py --height 512 --out logo --color EDF1F6 --suffix 浅色

# 5. 批量验收：尺寸 / 透明 / 白边 / GIF 帧 / 文字区侵入
python3 scripts/validate.py 成品 --gif-frames 5
```

每个脚本都是独立 CLI，`--help` 有完整参数说明，可以嵌进任何流水线。

## 目录

```
wechat-sticker-pack/
├── SKILL.md              核心技能定义（Skills 格式，含 YAML frontmatter）
├── AGENTS.md             Codex / 通用 Agent 入口
├── INSTALL.md            各平台安装与适配步骤
├── adapters/
│   ├── chat-only.md      纯对话平台用的单文件自包含版
│   └── custom-agent.md   自建 Agent 的接入清单
├── scripts/              5 个可执行 CLI
├── references/
│   ├── prompt-form.md    《提示词填空表》空白表 + 填写标准 + 反例 ← S2 交给你填的
│   ├── prompt-example.txt 一份填好的实例（虚构柴犬，8 行），只对照结构，内容别照抄
│   ├── platform-specs.md 平台参数、选项全集、素材规格、字数上限、实测坑
│   ├── cutout-spec.md    抠图四步的公式、阈值、验收指标、失败排查
│   ├── launch-info.md    上架文案模板与反例
│   └── brand-logo.md     车标式徽标的设计口径与 SVG 写法
├── CHANGELOG.md
└── requirements.txt
```

## 验证过的关键指标

一套 16 张的实际产出（240×240 透明 GIF）：

| 指标 | 结果 |
|---|---|
| 尺寸 / 格式 | 全部 240×240 RGBA，PNG 48–81KB，GIF 5 帧 77–81KB（平台上限 500KB） |
| 边缘带亮度 ≥200 像素占比 | 8.3% → **1.0%**（白描边剥离前后） |
| 边缘带纯白（≥230） | 每张 170–200 个 → **0** |
| GIF 真透明 | 逐帧四角 alpha=0，透明区占比 ≥0.71 |
| 文字区人物侵入 | 0 像素 |

## 边界

- **不保证平台过审。** 规则随时变，`references/platform-specs.md` 记录的是实测值，不构成承诺。
- **不生成受版权保护的角色。** 第三方 IP 需结构性差异化并留存创作存证。
- AI 生成内容请按《人工智能生成合成内容标识办法》如实标注。
- 出图环节依赖宿主平台自身的图像生成能力，本仓库不含模型，也不含 API Key。

## License

MIT © 酱小鱼工作室

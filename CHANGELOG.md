# 变更记录

## [1.2.2] - 2026-11-05

### 修复（会导致别人装完就报错的问题）
- **字体硬编码 macOS 路径**：`assets.py` 里写死 `/System/Library/Fonts/Hiragino Sans GB.ttc`，Windows / Linux 用户一旦用 `--title` 就崩。改为按 macOS → Windows（微软雅黑/黑体）→ Linux（Noto CJK/文泉驿）顺序探测，并新增 `--font` 手动指定。
- **字体缺失时静默画方框**：`compose.py` 找不到字体时回落到 `ImageFont.load_default()`，中文会变成一堆方块却不报错。改为明确退出并给出装字体的命令。
- **GIF 帧数与文档不符**：脚本输出 6 帧，文档与校验口径写的是 5 帧。统一为 5 帧（浮动 0/1/2/1/0）。
- **`assets.py` 顶部说明与平台规范冲突**：仍写着「横幅不得含文字、logo」，与 1.1.0 修正后的规范相反。已改正。

### 调整
- `references/prompt-example.txt` 换成**虚构角色**（柴犬，8 行）的示例。原文件是某个真实项目的完整 16 张文稿，随公开仓库分发等于把该项目的角色设定一起公开；示例的作用是对照结构，不需要真实项目内容。
- `LICENSE` 版权方改为 `夜猫子`。
- README 顶部新增「安装（30 秒）」，四条路径：git clone / 下载 zip / 只用脚本 / 其他平台。

## [1.2.1] - 2026-11-05

### 修复
- **安装包层级错误**：上一版 zip 是把仓库文件平铺在根目录打的，解压后 `SKILL.md` 裸露在根层，WorkBuddy / Claude Code 这类按目录识别技能的宿主装不上。改用官方打包脚本重打，包内为 `wechat-sticker-pack/SKILL.md`，已验证可解压即用。
- 安装包精简为**只含运行必需**（SKILL.md、scripts/、references/、CHANGELOG.md），README / AGENTS / INSTALL / adapters 属于仓库门面，不随技能包分发。
- `INSTALL.md` 补 WorkBuddy 的两种装法与「装完怎么验证生效」「zip 层级必须带一层同名目录」两条排查。

## [1.2.0] - 2026-11-05

### 定位修正（本次最重要的改动）
- **技能只封装流程，不封装内容。** 此前把一份填好的提示词文稿（325 行）当模板随包分发，等于把「银灰先生」这个角色一起卖了出去，换角色就用不了。现在改为：形象、画风、逐张姿势表情全部由使用者填写。
- 新增 **S2 关卡**：交出《提示词填空表》，表未填完不得出母图；**技能不得代填**，也不得「先写一版让人看着改」。
- 五道关卡 → **六道关卡**（新增 S2 提示词填表）。
- 新增 `references/prompt-form.md`：空白表（A 区不变项 / B 区逐张 / C 区文字样式）+ 填写标准 + 「不可复现写法」反例 + 相邻姿势撞车反例 + 自检三问。
- `prompts/prompt-template.txt` → `references/prompt-example.txt`，降级为**示例**，文件头写明「只对照结构，内容不要照抄」。

### 多平台发布
- 新增 `README.md`（GitHub 门面：分工、流程、脚本、目录、实测指标、边界）。
- 新增 `AGENTS.md`：Codex / 通用 Agent 入口，含六关卡、四条产出规则、命令与规格摘要。
- 新增 `CLAUDE.md`：在本仓库改东西时的约定。
- 新增 `INSTALL.md`：Claude Code / Codex / WorkBuddy / 自建 Agent / 纯对话平台五种接法 + GitHub 发布步骤 + opencv 装不上时的降级方案。
- 新增 `adapters/chat-only.md`：DeepSeek / 豆包 等无代码平台的单文件自包含版，同样走填表驱动。
- 新增 `adapters/custom-agent.md`：自建 Agent 的三处接线（生图调用 / 确认机制 / 脚本通道）+ 五步自检。
- 新增 `requirements.txt`、`LICENSE`（MIT）、`.gitignore`。

## [1.1.0] - 2026-11-05

### 修正
- **横幅规范纠错**：此前写「横幅禁文字、禁 logo」，与实际不符。官方横幅位本身就是放专辑名与品牌标识的，改为「可含标题文字与品牌 logo，禁二维码 / 联系方式 / 第三方水印」。`references/platform-specs.md` 与 `SKILL.md` 同步。
- 横幅构图固定为：徽标左上、标题左侧、角色右侧，标题与徽标左边距对齐同一根竖线。

### 新增
- **S8b 单张试点关卡**：批量前先跑 1 张成品（抠透明＋文字＋GIF 全链路），避免 16 张一起返工。
- **交付去重规则**：动态只给 N 个 GIF、静态只给 N 个 PNG，不双份列。
- **GIF 动效口径**：5 帧、90ms、主体上下浮动 0/1/2/1/0px、文字不动。
- `scripts/mark.py`：车标式纯图形徽标生成（单色、负空间挖孔、4 倍超采样、任意高度输出）。
- `references/brand-logo.md`：单标记设计口径、脚本用法、SVG 写法、放置安全距离、常见错。
- `scripts/assets.py` 新增 `--logo / --title / --subtitle / --tag` 四个参数；不传 `--title` 时退回无文字居中版。

## [1.0.0] - 2026-11-05

### 首版
- 五确认关卡（S0 上传参数 / S1 平台附加信息 / S4 母图验证 / S5 名称逐张征询 / S7 版型确认）。
- 抠透明四步：清四边连通背景 → 清闭环空洞 → 剥离白描边 → 颜色回填 + alpha 提纯。
- 成品合成 240×240 PNG + 5 帧真透明 GIF（调色板索引 255 + 三角 alpha=0 校验）。
- 上架文案模板（名称 / 介绍 / 版权 / 逐张含义词）与字数上限校验。
- `scripts/`：cutout.py、compose.py、assets.py、validate.py。

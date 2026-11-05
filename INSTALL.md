# 安装到各平台

同一套内容，五种接入方式。先看你的平台属于哪类：

| 平台 | 能跑脚本 | 用哪个文件 | 工作量 |
|---|---|---|---|
| Claude Code / Claude Desktop | ✅ | `SKILL.md`（原生 Skills 格式） | 拷目录即可 |
| Codex / 通用终端 Agent | ✅ | `AGENTS.md` | 拷目录即可 |
| WorkBuddy | ✅ | `SKILL.md` | 拷目录即可 |
| 自建 / 私有 Agent | 看实现 | `adapters/custom-agent.md` | 改 3 处 |
| DeepSeek / 豆包 / 纯对话 | ❌ | `adapters/chat-only.md` | 粘贴一次 |

---

## 一、Claude Code / Claude Desktop

Skills 目录结构：

```bash
git clone https://github.com/<your-name>/wechat-sticker-pack.git
cp -R wechat-sticker-pack ~/.claude/skills/
```

放好后在会话里说「做一套表情包」即触发。`SKILL.md` 的 frontmatter（`name` / `description`）就是触发依据，不要删。

Claude 没有内置生图，S3 与 S9 需要显式指定生图工具（如 MCP 图像服务，或你本地接的 API）。**这是唯一需要你补的环节**，其余全链路可用。

## 二、Codex / 通用终端 Agent

```bash
cp -R wechat-sticker-pack <你的工作区>/
```

Codex 自动读工作区根目录的 `AGENTS.md`。它已包含六关卡、四条产出规则、命令与规格摘要，不必再让它读 `SKILL.md`（深层细节让它按索引去 `references/` 里翻）。

## 三、WorkBuddy

**方式 A：装安装包（推荐给非技术使用者）**

在 WorkBuddy 里直接说「安装技能」，把 `wechat-sticker-pack.zip` 交给它；或手工解压到技能目录：

```bash
unzip wechat-sticker-pack.zip -d ~/.workbuddy/skills/
# 结果必须是 ~/.workbuddy/skills/wechat-sticker-pack/SKILL.md
```

**方式 B：拷目录**

```bash
cp -R wechat-sticker-pack ~/.workbuddy/skills/
```

用户级技能，全项目可用（想让某个项目独占，就放到该项目的 `.workbuddy/skills/`）。
图像生成用内置能力，无需额外配置。

**装完怎么确认生效**：新开一个会话，说「做一套表情包」。如果技能生效，它会先问你上传参数，而不是直接开始画画；没反应就是没装上，先查目录里有没有 `SKILL.md`。

**压缩包层级**：zip 内必须有一层同名目录（`wechat-sticker-pack/SKILL.md`），
把文件平铺在压缩包根目录是装不上的——这是最常见的失败原因。

## 四、自建 / 私有 Agent

见 [`adapters/custom-agent.md`](adapters/custom-agent.md)。核心是三处替换：

1. **生图调用** — S3 / S9 的「生成一张图」换成你后端的图像模型 API
2. **确认机制** — 六关卡的「停住问」换成你前端的交互暂停或表单
3. **执行通道** — 五个脚本的调用换成你沙箱里的 shell 工具

## 五、纯对话平台（DeepSeek / 豆包 / 文心等）

这类平台**没有文件系统、不能跑 Python**，技能只能带走提示词与流程。用 [`adapters/chat-only.md`](adapters/chat-only.md)：单文件自包含，粘贴进系统提示词或对话开头即可。

代价要说清楚：抠透明、叠字、GIF 合成、批量校验这四步没有了，需要你手工在图像工具里完成，或者把图拿回本地跑脚本。

---

## 依赖

```bash
pip install -r requirements.txt
# Pillow · numpy · opencv-python-headless
```

macOS 推荐 `python3 -m pip install -r requirements.txt`；若 `cv2` 装不上，用 `opencv-python-headless`（本仓库 requirements 里已是 headless 版，无需 GUI 依赖）。

验证安装：

```bash
python3 scripts/validate.py --help
python3 -c "import PIL, numpy, cv2; print('ok')"
```

> 脚本依赖 opencv 是刻意保留的：抠图里的连通域标记与距离变换用它最稳，换成纯 numpy 实现慢且易出边界 bug。若目标环境无法安装 opencv，见 `INSTALL.md` 末尾的降级说明。

## 无法安装 opencv 时

`assets.py` 与 `mark.py` 只依赖 Pillow + numpy，可独立运行（上架素材、徽标不受影响）。

`cutout.py`、`compose.py`、`validate.py` 依赖 opencv。三个方案：

1. 换 `opencv-python-headless`（体积小，无 GUI 依赖，通常能装）
2. 把这三个脚本放到有 Python 的机器上跑，产物回传
3. 把脚本包成 HTTP 服务，Agent 侧只发请求（最通用，需自建服务）

---

## 发布到 GitHub

首次发布：

```bash
cd wechat-sticker-pack
git init
git add .
git commit -m "feat: 微信表情包生成与上架技能 v1.2.0"
gh repo create wechat-sticker-pack --public --source=. --push
```

没有 `gh` 或未登录时：

```bash
gh auth login          # 交互式，选 GitHub.com → HTTPS → 浏览器授权
```

或手工建空仓库后：

```bash
git remote add origin https://github.com/<your-name>/wechat-sticker-pack.git
git branch -M main
git push -u origin main
```

后续更新：

```bash
git add -A && git commit -m "docs: ..." && git push
```

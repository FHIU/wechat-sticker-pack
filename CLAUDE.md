# CLAUDE.md

这是「微信表情包整套生成与上架」技能仓库。在本仓库工作时：

- **流程定义看 `SKILL.md`**，它是唯一的权威来源；`AGENTS.md` 只是执行摘要。
- **六道关卡不能跳**（S0 上传参数 / S1 平台附加信息 / S2 提示词填表 / S4 母图验证 / S5 名称逐张征询 / S7 版型确认）。未通过关卡时不要生成图。
- **提示词不代写**：S2 交出 `references/prompt-form.md` 空白表，等使用者填。
- **改脚本后必须自测**：`python3 scripts/validate.py --help` 至少能跑通，涉及图像处理的改动要用真实图验证一遍再提交。
- **改文案类文件**（`references/*.md`）保持中文、保持原有表格与清单格式，不要扩写成散文。
- 新增阈值或规格时，同步更新 `references/platform-specs.md` 与 `CHANGELOG.md`。
- **打包只用 `./package.sh`，不要直接跑 `package_skill.py`。** 后者递归压整个目录、不看 `.gitignore`，在仓库根目录运行会把 `.git/` 塞进 zip（实测 209KB 并泄漏提交历史）。`package.sh` 先复制到干净暂存目录再打包，并自检层级、垃圾文件、必需文件。
- 新增顶层文件或 `references/` 之外的目录时，同步改 `package.sh` 里的 `ROOT_FILES` / `DIRS` 清单，否则装包会缺文件。

安装为技能：`cp -R . ~/.claude/skills/wechat-sticker-pack`

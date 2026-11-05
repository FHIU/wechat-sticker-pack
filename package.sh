#!/usr/bin/env bash
# 打包技能为可直接安装的 zip。
#
# 为什么要有这个脚本：官方的 package_skill.py 会递归压整个目录、不看 .gitignore，
# 在仓库根目录直接跑就会把 .git/ 一起塞进包（实测 209KB，且泄漏提交历史）。
# 本脚本先把「运行必需文件」复制到一个干净暂存目录，再在那里打包，最后自检。
#
# 用法：
#   ./package.sh              # 输出到 dist/wechat-sticker-pack.zip
#   ./package.sh /tmp/out     # 输出到指定目录
set -euo pipefail

SKILL_NAME="wechat-sticker-pack"
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT="${1:-$SRC/dist}"

# 技能包只含运行必需；README / AGENTS / INSTALL / adapters / LICENSE 属于仓库门面，不随包分发。
# 注意：新增顶层文件时要同步这里的清单，否则别人装完会报文件缺失。
ROOT_FILES=(SKILL.md CHANGELOG.md)
DIRS=(references scripts)

die() { echo "❌ $*" >&2; exit 1; }

# ---------- 1. 建干净暂存目录 ----------
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
STAGE="$TMP/$SKILL_NAME"
mkdir -p "$STAGE"

for f in "${ROOT_FILES[@]}"; do
  [ -f "$SRC/$f" ] || die "缺少 $f"
  cp "$SRC/$f" "$STAGE/"
done

for d in "${DIRS[@]}"; do
  [ -d "$SRC/$d" ] || die "缺少目录 $d/"
  mkdir -p "$STAGE/$d"
done
cp "$SRC"/references/*.md "$STAGE/references/" 2>/dev/null || die "references/ 下没有 .md 文件"
cp "$SRC"/scripts/*.py   "$STAGE/scripts/"     2>/dev/null || die "scripts/ 下没有 .py 文件"

# 兜底：暂存区不允许出现版本库、编译缓存、系统垃圾
find "$STAGE" \( -name '.git' -o -name '__pycache__' -o -name '.DS_Store' \
  -o -name '*.pyc' -o -name '.venv' \) -prune -exec rm -rf {} + 2>/dev/null || true

# ---------- 2. 打包（优先用官方脚本，保证结构与宿主识别一致） ----------
PKG_SCRIPT="${SKILL_CREATOR_DIR:-}/scripts/package_skill.py"
if [ ! -f "$PKG_SCRIPT" ]; then
  for c in \
    "/Applications/WorkBuddy.app/Contents/Resources/app.asar.unpacked/resources/plugins/workbuddy-builtin/skills/skill-creator/scripts/package_skill.py" \
    "$HOME/.workbuddy/skills/skill-creator/scripts/package_skill.py" \
    "$HOME/.claude/skills/skill-creator/scripts/package_skill.py"; do
    [ -f "$c" ] && { PKG_SCRIPT="$c"; break; }
  done
fi

if [ -f "$PKG_SCRIPT" ]; then
  ( cd "$TMP" && python3 "$PKG_SCRIPT" "$SKILL_NAME" >/dev/null )
else
  echo "⚠️  未找到官方 package_skill.py，改用 zip 打包（层级相同）"
  ( cd "$TMP" && zip -qr "$SKILL_NAME.zip" "$SKILL_NAME" )
fi

ZIP="$TMP/$SKILL_NAME.zip"
[ -f "$ZIP" ] || die "打包失败，未生成 zip"

# ---------- 3. 自检 ----------
LIST="$(unzip -Z1 "$ZIP")"

if echo "$LIST" | grep -qE '(^|/)\.git/|__pycache__|\.DS_Store|\.pyc$|\.zip$'; then
  echo "$LIST" | grep -nE '(^|/)\.git/|__pycache__|\.DS_Store|\.pyc$|\.zip$' >&2
  die "包内含版本库 / 缓存 / 嵌套 zip，拒绝产出"
fi

echo "$LIST" | grep -qx "$SKILL_NAME/SKILL.md" \
  || die "层级错误：根层必须是 $SKILL_NAME/SKILL.md（宿主按同名目录识别技能）"

N=$(echo "$LIST" | grep -vc '/$' || true)
[ "$N" -ge 5 ] || die "文件数异常（$N 个），疑似漏拷"

# 声明的文件都要在包里，避免文档里写了、包里没有
for f in "${ROOT_FILES[@]}" references/prompt-form.md scripts/validate.py; do
  echo "$LIST" | grep -qx "$SKILL_NAME/$f" || die "包内缺少 $f"
done

# ---------- 4. 产出 ----------
mkdir -p "$OUT"
cp "$ZIP" "$OUT/$SKILL_NAME.zip"

SIZE="$(du -h "$OUT/$SKILL_NAME.zip" | cut -f1)"
echo "✅ $OUT/$SKILL_NAME.zip"
echo "   $N 个文件 · $SIZE · 包内根层 $SKILL_NAME/"

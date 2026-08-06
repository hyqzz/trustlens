#!/bin/bash
# TrustLens 站点同步：从 GitHub 仓库 tarball 取回 CI 构建好的站点，替换 /opt/trustlens
# 背景：本服务器到 github.io 不通，但 codeload.github.com 正常；
#       周更评测（evaluate.yml）会把 data + site/dist 提交回 main 分支。
# 由 crontab 每周一调用。
set -euo pipefail

DEST="/opt/trustlens"
WORK="$(mktemp -d)"
TARBALL="https://codeload.github.com/hyqzz/trustlens/tar.gz/refs/heads/main"

wget --quiet -O "$WORK/main.tar.gz" "$TARBALL"
tar -xzf "$WORK/main.tar.gz" -C "$WORK"

SRC="$WORK/trustlens-main/site/dist"
if [ ! -f "$SRC/index.html" ]; then
    echo "ERROR: built site missing in tarball" >&2
    rm -rf "$WORK"
    exit 1
fi

# 目录交换实现近原子替换（服务器无 rsync）
OLD="${DEST}.old.$$"
rm -rf "$OLD"
mv "$DEST" "$OLD"
mv "$SRC" "$DEST"
find "$DEST" -type d -exec chmod 755 {} +
find "$DEST" -type f -exec chmod 644 {} +
rm -rf "$OLD" "$WORK"
echo "$(date '+%F %T') trustlens synced"

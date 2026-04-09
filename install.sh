#!/bin/bash
# Universal Claude Code 安装脚本
# 将架构安装到指定项目目录

set -e

UNIVERSAL_DIR="$(cd "$(dirname "$0")" && pwd)"
TARGET_DIR="${1:-.}"

echo "🔧 安装 Universal Claude Code 架构"
echo "📁 目标目录: $TARGET_DIR"

# 创建.claude目录
mkdir -p "$TARGET_DIR/.claude"

# 复制agents
if [ -d "$UNIVERSAL_DIR/.claude/agents" ]; then
    cp -r "$UNIVERSAL_DIR/.claude/agents" "$TARGET_DIR/.claude/"
    echo "✅ Agents 已安装"
fi

# 复制skills
if [ -d "$UNIVERSAL_DIR/.claude/skills" ]; then
    cp -r "$UNIVERSAL_DIR/.claude/skills" "$TARGET_DIR/.claude/"
    echo "✅ Skills 已安装"
fi

# 复制steering
if [ -d "$UNIVERSAL_DIR/.claude/steering" ]; then
    cp -r "$UNIVERSAL_DIR/.claude/steering" "$TARGET_DIR/.claude/"
    echo "✅ Steering 规则已安装"
fi

# 复制hooks
if [ -d "$UNIVERSAL_DIR/.claude/hooks" ]; then
    cp -r "$UNIVERSAL_DIR/.claude/hooks" "$TARGET_DIR/.claude/"
    echo "✅ Hooks 已安装"
fi

# 复制CLAUDE.md
if [ -f "$UNIVERSAL_DIR/CLAUDE.md" ]; then
    cp "$UNIVERSAL_DIR/CLAUDE.md" "$TARGET_DIR/"
    echo "✅ CLAUDE.md 已安装"
fi

# 复制runtime（可选，作为子模块）
if [ -d "$UNIVERSAL_DIR/runtime" ]; then
    cp -r "$UNIVERSAL_DIR/runtime" "$TARGET_DIR/"
    echo "✅ Runtime 已安装"
fi

echo ""
echo "✨ 安装完成!"
echo ""
echo "📖 使用方法:"
echo "   cd $TARGET_DIR"
echo "   # 使用Agent: /planner, /code-reviewer, 等"
echo "   # 使用Skill: /tdd-workflow, /security-review, 等"

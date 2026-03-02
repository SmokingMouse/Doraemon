#!/usr/bin/env python3
"""
清理 Claude Code session 的工具脚本
用于解决 "Session ID already in use" 问题
"""
import asyncio
import sys
from pathlib import Path
from storage.database import Database


async def main():
    print("🔧 Claude Code Session 清理工具\n")

    # 1. 检查数据库中的 session
    db_path = "./data/doraemon.db"
    if not Path(db_path).exists():
        print(f"❌ 数据库不存在: {db_path}")
        return

    db = Database(db_path)

    import aiosqlite

    async with aiosqlite.connect(db_path) as conn:
        cursor = await conn.execute(
            "SELECT id, user_id, claude_session_id, last_active FROM sessions"
        )
        sessions = await cursor.fetchall()

    if not sessions:
        print("✓ 没有找到任何 session")
        return

    print(f"找到 {len(sessions)} 个 session:\n")
    for sid, uid, claude_sid, last_active in sessions:
        print(f"  Session {sid}:")
        print(f"    User ID: {uid}")
        print(f"    Claude Session ID: {claude_sid}")
        print(f"    Last Active: {last_active}")
        print()

    # 2. 检查 Claude Code session 文件
    claude_sessions_dir = Path.home() / ".claude" / "sessions"
    if claude_sessions_dir.exists():
        session_files = list(claude_sessions_dir.glob("*.jsonl"))
        print(f"\n找到 {len(session_files)} 个 Claude Code session 文件")
    else:
        print(f"\n✓ Claude Code sessions 目录不存在: {claude_sessions_dir}")
        session_files = []

    # 3. 提供清理选项
    print("\n清理选项:")
    print("1. 重新生成所有 session ID（推荐）")
    print("2. 删除所有 Claude Code session 文件")
    print("3. 两者都做")
    print("4. 退出")

    choice = input("\n请选择 (1-4): ").strip()

    if choice == "1" or choice == "3":
        # 重新生成 session ID
        import uuid

        async with aiosqlite.connect(db_path) as conn:
            for sid, uid, old_claude_sid, _ in sessions:
                new_claude_sid = str(uuid.uuid4())
                await conn.execute(
                    "UPDATE sessions SET claude_session_id = ? WHERE id = ?",
                    (new_claude_sid, sid),
                )
                print(f"✓ Session {sid}: {old_claude_sid[:8]}... → {new_claude_sid[:8]}...")
            await conn.commit()
        print("\n✓ 所有 session ID 已重新生成")

    if choice == "2" or choice == "3":
        # 删除 session 文件
        if session_files:
            for f in session_files:
                f.unlink()
                print(f"✓ 删除: {f.name}")
            print(f"\n✓ 删除了 {len(session_files)} 个 session 文件")
        else:
            print("\n✓ 没有 session 文件需要删除")

    if choice in ["1", "2", "3"]:
        print("\n✅ 清理完成！现在可以重启 bot 了。")
    else:
        print("\n取消操作")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n操作已取消")
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        sys.exit(1)

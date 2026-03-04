#!/usr/bin/env python3
"""测试 Claude Code streaming 输出格式"""

import asyncio
import json
import sys
import os

async def test_streaming():
    # 清除 CLAUDECODE 环境变量
    env = os.environ.copy()
    env.pop('CLAUDECODE', None)

    process = await asyncio.create_subprocess_exec(
        "claude",
        "--print",
        "--output-format", "stream-json",
        "--include-partial-messages",
        "--dangerously-skip-permissions",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=env,
    )

    # 发送测试消息
    message = "Say hello in one sentence"
    process.stdin.write(message.encode())
    process.stdin.close()

    print("=== STDOUT ===")
    line_count = 0
    async for line in process.stdout:
        line_count += 1
        line_text = line.decode('utf-8', errors='ignore').strip()
        print(f"Line {line_count}: {line_text}")

        try:
            event = json.loads(line_text)
            print(f"  -> Type: {event.get('type')}")
            if event.get('type') == 'content_block_delta':
                delta = event.get('delta', {})
                print(f"  -> Delta: {delta}")
        except json.JSONDecodeError:
            print(f"  -> Not JSON")

    await process.wait()

    stderr = await process.stderr.read()
    if stderr:
        print("\n=== STDERR ===")
        print(stderr.decode())

    print(f"\n=== EXIT CODE: {process.returncode} ===")

if __name__ == "__main__":
    asyncio.run(test_streaming())

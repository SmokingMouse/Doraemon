#!/usr/bin/env python3
"""端到端测试：验证智能回复过滤功能"""

import asyncio
import json
from services.claude_code import ClaudeCodeService


async def test_streaming_with_thinking():
    """测试带思考过程的流式响应"""
    print("=" * 60)
    print("测试：智能回复过滤功能")
    print("=" * 60)

    svc = ClaudeCodeService()

    # 模拟一个会触发思考的问题
    message = "请简单解释一下什么是递归"

    print(f"\n📤 发送消息: {message}\n")
    print("🔄 流式输出（包含思考/工具）:")
    print("-" * 60)

    streaming_content = []

    async def on_chunk(chunk: str):
        """捕获流式输出"""
        streaming_content.append(chunk)
        print(chunk, end='', flush=True)

    # 调用流式 API
    final_response, session_id = await svc.ask_claude_streaming(
        message=message,
        session_id=None,
        on_chunk=on_chunk,
    )

    print("\n" + "-" * 60)
    print("\n✅ 流式输出完成\n")

    # 显示最终回复
    print("📥 最终回复（已过滤思考/工具）:")
    print("-" * 60)
    print(final_response)
    print("-" * 60)

    # 统计
    full_content = ''.join(streaming_content)
    print(f"\n📊 统计:")
    print(f"  - 流式输出长度: {len(full_content)} 字符")
    print(f"  - 最终回复长度: {len(final_response)} 字符")
    print(f"  - 过滤比例: {(1 - len(final_response) / len(full_content)) * 100:.1f}%")

    # 验证
    has_thinking = "💭" in full_content or "思考" in full_content
    has_tool = "🔧" in full_content or "调用工具" in full_content

    print(f"\n✅ 验证:")
    print(f"  - 流式输出包含思考: {has_thinking}")
    print(f"  - 流式输出包含工具: {has_tool}")
    print(f"  - 最终回复已过滤: {'💭' not in final_response and '🔧' not in final_response}")

    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_streaming_with_thinking())

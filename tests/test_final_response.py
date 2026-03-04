#!/usr/bin/env python3
"""测试最终回复提取功能"""

from services.claude_code import ClaudeCodeService


def test_extract_final_response():
    """测试提取最终回复"""
    svc = ClaudeCodeService()

    # 测试用例 1: 包含思考和工具调用
    test1 = """💭 **思考过程：**
我需要先读取文件
然后分析内容

---

这是最终回复的第一部分

🔧 调用工具: Read
✅ Read 完成 (1.2s)

这是最终回复的第二部分"""

    result1 = svc._extract_final_response(test1)
    print("测试 1 - 包含思考和工具:")
    print(f"输入长度: {len(test1)}")
    print(f"输出长度: {len(result1)}")
    print(f"输出内容:\n{result1}\n")
    assert "思考过程" not in result1
    assert "调用工具" not in result1
    assert "最终回复" in result1

    # 测试用例 2: 只有最终回复
    test2 = "这是纯粹的最终回复，没有思考和工具"
    result2 = svc._extract_final_response(test2)
    print("测试 2 - 纯粹回复:")
    print(f"输出: {result2}\n")
    assert result2 == test2

    # 测试用例 3: 多个思考块
    test3 = """💭 **思考过程：**
第一次思考

---

中间回复

💭 **思考过程：**
第二次思考

---

最终回复"""

    result3 = svc._extract_final_response(test3)
    print("测试 3 - 多个思考块:")
    print(f"输出:\n{result3}\n")
    assert "思考过程" not in result3
    assert "中间回复" in result3
    assert "最终回复" in result3

    print("✅ 所有测试通过！")


if __name__ == "__main__":
    test_extract_final_response()

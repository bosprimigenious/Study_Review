#!/usr/bin/env python3
"""Q6 grading accuracy benchmark: 20 curated cases vs keyword fallback grader."""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from agent.grading import _keyword_grade  # noqa: E402

# 20 cases: 8 correct, 6 partial, 6 wrong (tasks.md Q6 design)
BENCHMARK_CASES: list[dict[str, object]] = [
    # --- 8 correct (≥80% scoring points) ---
    {
        "id": "c01",
        "prompt": "TCP 拥塞控制与流量控制的区别",
        "scoring_points": ["拥塞控制定义", "流量控制定义", "两者区别"],
        "answer": "拥塞控制定义是防止网络过载；流量控制定义是防止接收方缓冲区溢出；两者区别在控制对象不同",
        "expected": "correct",
    },
    {
        "id": "c02",
        "prompt": "三次握手过程",
        "scoring_points": ["SYN 报文", "ACK 确认", "连接建立"],
        "answer": "客户端发 SYN 报文，服务端回 SYN+ACK 确认，客户端再 ACK 确认后连接建立",
        "expected": "correct",
    },
    {
        "id": "c03",
        "prompt": "子网划分步骤",
        "scoring_points": ["确定子网位数", "计算子网掩码", "分配主机地址"],
        "answer": "先确定子网位数，再计算子网掩码，最后分配主机地址给各子网",
        "expected": "correct",
    },
    {
        "id": "c04",
        "prompt": "ARP 协议作用",
        "scoring_points": ["地址解析", "IP 到 MAC", "局域网通信"],
        "answer": "ARP 做地址解析，把 IP 到 MAC 映射查出来，支撑局域网通信",
        "expected": "correct",
    },
    {
        "id": "c05",
        "prompt": "滑动窗口机制",
        "scoring_points": ["发送窗口", "接收窗口", "流量控制"],
        "answer": "发送窗口限制未确认数据量，接收窗口通告缓存空间，共同实现流量控制",
        "expected": "correct",
    },
    {
        "id": "c06",
        "prompt": "路由选择基本原则",
        "scoring_points": ["最短路径", "跳数最小", "转发决策"],
        "answer": "路由选择追求最短路径和跳数最小，据此做转发决策",
        "expected": "correct",
    },
    {
        "id": "c07",
        "prompt": "UDP 特点",
        "scoring_points": ["无连接", "不保证可靠", "开销小"],
        "answer": "UDP 无连接、不保证可靠交付，但开销小适合实时业务",
        "expected": "correct",
    },
    {
        "id": "c08",
        "prompt": "DNS 解析过程",
        "scoring_points": ["本地缓存", "递归查询", "返回 IP"],
        "answer": "先查本地缓存，没有则递归查询权威服务器，最终返回 IP 地址",
        "expected": "correct",
    },
    # --- 6 partial (40–79%) ---
    {
        "id": "p01",
        "prompt": "TCP 拥塞控制与流量控制的区别",
        "scoring_points": ["拥塞控制定义", "流量控制定义", "两者区别"],
        "answer": "拥塞控制定义是防止网络过载；流量控制定义",
        "expected": "partial",
    },
    {
        "id": "p02",
        "prompt": "三次握手过程",
        "scoring_points": ["SYN 报文", "ACK 确认", "连接建立"],
        "answer": "客户端发 SYN 报文，服务端回 SYN+ACK 确认",
        "expected": "partial",
    },
    {
        "id": "p03",
        "prompt": "子网划分步骤",
        "scoring_points": ["确定子网位数", "计算子网掩码", "分配主机地址"],
        "answer": "先确定子网位数，再计算子网掩码",
        "expected": "partial",
    },
    {
        "id": "p04",
        "prompt": "ARP 协议作用",
        "scoring_points": ["地址解析", "IP 到 MAC", "局域网通信"],
        "answer": "ARP 做地址解析，把 IP 到 MAC 映射",
        "expected": "partial",
    },
    {
        "id": "p05",
        "prompt": "滑动窗口机制",
        "scoring_points": ["发送窗口", "接收窗口", "流量控制"],
        "answer": "发送窗口限制未确认数据量，接收窗口通告缓存",
        "expected": "partial",
    },
    {
        "id": "p06",
        "prompt": "UDP 特点",
        "scoring_points": ["无连接", "不保证可靠", "开销小"],
        "answer": "UDP 无连接、不保证可靠交付",
        "expected": "partial",
    },
    # --- 6 wrong (<40%) ---
    {
        "id": "w01",
        "prompt": "TCP 拥塞控制与流量控制的区别",
        "scoring_points": ["拥塞控制定义", "流量控制定义", "两者区别"],
        "answer": "不知道",
        "expected": "wrong",
    },
    {
        "id": "w02",
        "prompt": "三次握手过程",
        "scoring_points": ["SYN 报文", "ACK 确认", "连接建立"],
        "answer": "四次挥手释放连接",
        "expected": "wrong",
    },
    {
        "id": "w03",
        "prompt": "子网划分步骤",
        "scoring_points": ["确定子网位数", "计算子网掩码", "分配主机地址"],
        "answer": "直接 ping 网关",
        "expected": "wrong",
    },
    {
        "id": "w04",
        "prompt": "ARP 协议作用",
        "scoring_points": ["地址解析", "IP 到 MAC", "局域网通信"],
        "answer": "HTTP 请求网页",
        "expected": "wrong",
    },
    {
        "id": "w05",
        "prompt": "滑动窗口机制",
        "scoring_points": ["发送窗口", "接收窗口", "流量控制"],
        "answer": "拥塞控制用慢开始",
        "expected": "wrong",
    },
    {
        "id": "w06",
        "prompt": "DNS 解析过程",
        "scoring_points": ["本地缓存", "递归查询", "返回 IP"],
        "answer": "SMTP 发邮件",
        "expected": "wrong",
    },
]

Q6_THRESHOLD = 0.70


class TestGradingBenchmark(unittest.TestCase):
    """Q6: rule-based grading accuracy ≥70% on 20 curated 计网 cases."""

    def setUp(self) -> None:
        self._saved_key = os.environ.pop("OPENAI_API_KEY", None)

    def tearDown(self) -> None:
        if self._saved_key is not None:
            os.environ["OPENAI_API_KEY"] = self._saved_key

    def test_q6_keyword_grader_accuracy(self) -> None:
        hits = 0
        misses: list[str] = []
        for case in BENCHMARK_CASES:
            result = _keyword_grade(
                str(case["prompt"]),
                "",
                list(case["scoring_points"]),  # type: ignore[arg-type]
                str(case["answer"]),
            )
            actual = result["verdict"]
            expected = str(case["expected"])
            if actual == expected:
                hits += 1
            else:
                misses.append(
                    f"{case['id']}: expected={expected}, got={actual}, hint={result['score_hint']}"
                )

        accuracy = hits / len(BENCHMARK_CASES)
        self.assertGreaterEqual(
            accuracy,
            Q6_THRESHOLD,
            f"Q6 accuracy {accuracy:.0%} < {Q6_THRESHOLD:.0%}; misses: {misses}",
        )

    def test_q6_case_distribution(self) -> None:
        """Sanity: benchmark has 8/6/6 verdict distribution per tasks.md."""
        counts = {"correct": 0, "partial": 0, "wrong": 0}
        for case in BENCHMARK_CASES:
            counts[str(case["expected"])] += 1
        self.assertEqual(counts, {"correct": 8, "partial": 6, "wrong": 6})


if __name__ == "__main__":
    unittest.main()

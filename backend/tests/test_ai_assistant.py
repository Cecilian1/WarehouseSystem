from __future__ import annotations

import unittest
from unittest.mock import patch

from backend.api_service import ai_assistant


def snapshot() -> dict:
    return {
        "date": "2026-08-27",
        "riskLevel": "high",
        "environment": {
            "valid": True,
            "status": "异常",
            "temperature": 9.2,
            "humidity": 94,
            "sampleCount": 20,
            "abnormalSamples": 3,
        },
        "inventory": {
            "produceTypes": 2,
            "totalQuantity": 7,
            "todayInbound": 2,
            "todayOutbound": 0,
            "todayRecognitionCount": 2,
        },
        "freshness": {
            "averageScore": 51,
            "fresh": 2,
            "warning": 3,
            "spoiled": 2,
            "riskyItems": [
                {
                    "name": "生菜",
                    "quantity": 2,
                    "unit": "颗",
                    "status": "腐败",
                    "freshnessScore": 20,
                    "remainingDays": -1,
                },
                {
                    "name": "草莓",
                    "quantity": 3,
                    "unit": "盒",
                    "status": "临期",
                    "freshnessScore": 60,
                    "remainingDays": 1,
                },
            ],
        },
        "alerts": {
            "pending": 2,
            "critical": 1,
            "warning": 1,
            "recent": [],
        },
    }


class AiAssistantTest(unittest.TestCase):
    def test_alert_analysis_is_short_prioritized_and_authoritative(self) -> None:
        with patch.object(ai_assistant, "QWEN_API_KEY", ""):
            answer = ai_assistant._assemble_analysis(
                "alerts",
                "现在要做什么？",
                snapshot(),
            )

        self.assertEqual(answer["urgency"], "high")
        self.assertLessEqual(len(answer["bullets"]), 4)
        self.assertIn("立即处理", answer["bullets"][0])
        self.assertNotIn("QWEN_API_KEY", answer)

    def test_freshness_analysis_mentions_risky_produce(self) -> None:
        answer = ai_assistant._fallback(
            "freshness",
            "哪些需要优先处理？",
            snapshot(),
        )

        self.assertTrue(any("生菜" in item for item in answer["bullets"]))
        self.assertLessEqual(len(answer["summary"]), 100)

    def test_plain_fact_question_uses_paragraph_without_forced_bullets(self) -> None:
        answer = ai_assistant._fallback(
            "environment",
            "当前温度是多少？",
            snapshot(),
        )

        self.assertEqual(answer["format"], "paragraph")
        self.assertEqual(answer["bullets"], [])

    def test_hallucinated_number_is_rejected(self) -> None:
        facts = ai_assistant._facts_for("environment", snapshot())
        answer = {"summary": "当前温度是12.5°C。", "bullets": []}

        self.assertFalse(ai_assistant._numbers_are_grounded(answer, facts))

    def test_history_is_limited_and_untrusted_fields_are_removed(self) -> None:
        raw = [
            {"role": "user", "content": f"问题{i}", "secret": "ignored"}
            for i in range(20)
        ]
        history = ai_assistant._sanitize_history(raw)

        self.assertEqual(len(history), 12)
        self.assertEqual(set(history[0]), {"role", "content"})


if __name__ == "__main__":
    unittest.main()

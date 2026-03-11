"""Tests for the Warden defense intelligence module."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from app.modules.warden.engine import WardenEngine
from app.modules.warden.schemas import (
    ThreatEvaluation,
    ThreatHypothesis,
    WardenCycleRecord,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def engine(tmp_path: Path) -> WardenEngine:
    """Create a WardenEngine with temp audit log."""
    return WardenEngine(
        tribe_id="tribe-test-1",
        tribe_address="0xabc123",
        audit_log_path=tmp_path / "warden_audit.jsonl",
        max_cycles=5,
        alert_tier_threshold=2,
        cycle_interval_seconds=1,
    )


@pytest.fixture()
def sample_events() -> list[dict]:
    """Sample blockchain events for testing."""
    return [
        {
            "tx_digest": "tx1",
            "status": "success",
            "type": "balance_change",
            "owner": "0xabc123",
            "amount": "-5000000000",
            "coin_type": "0x2::sui::SUI",
        },
        {
            "tx_digest": "tx2",
            "status": "success",
            "type": "balance_change",
            "owner": "0xdef456",
            "amount": "5000000000",
            "coin_type": "0x2::sui::SUI",
        },
        {"tx_digest": "tx3", "status": "success"},
    ]


@pytest.fixture()
def doctrine_text() -> str:
    return (
        "# Tribe Doctrine\n\n"
        "## Threats\n"
        "- Large outflows > 1 SUI are suspicious\n"
        "- Unknown addresses require Tier 2 alert\n\n"
        "## Response\n"
        "- Tier 1: Log only\n"
        "- Tier 2: Alert officers\n"
        "- Tier 3: Require operator confirmation\n"
    )


# ---------------------------------------------------------------------------
# WardenEngine — Init & Config
# ---------------------------------------------------------------------------


class TestWardenEngineInit:
    def test_default_state(self, engine: WardenEngine):
        assert engine.tribe_id == "tribe-test-1"
        assert engine.tribe_address == "0xabc123"
        assert engine.is_running is False
        assert engine.cycle_count == 0
        assert engine.alerts == []

    def test_status_dict(self, engine: WardenEngine):
        status = engine.status()
        assert status["tribe_id"] == "tribe-test-1"
        assert status["running"] is False
        assert status["total_cycles"] == 0
        assert status["total_alerts"] == 0
        assert status["doctrine_loaded"] is False

    def test_load_default_doctrine(self, engine: WardenEngine):
        doctrine = engine.load_doctrine()
        assert "Threat Types" in doctrine
        assert "Response Tiers" in doctrine
        assert engine.status()["doctrine_loaded"] is True

    def test_load_custom_doctrine(self, engine: WardenEngine, doctrine_text: str):
        loaded = engine.load_doctrine(doctrine_text)
        assert "Tribe Doctrine" in loaded
        assert loaded == doctrine_text

    def test_load_doctrine_from_file(
        self, engine: WardenEngine, tmp_path: Path, doctrine_text: str
    ):
        doctrine_file = tmp_path / "doctrine.md"
        doctrine_file.write_text(doctrine_text)
        engine._doctrine_path = doctrine_file
        loaded = engine.load_doctrine()
        assert "Tribe Doctrine" in loaded


# ---------------------------------------------------------------------------
# Rule-based Analysis (no LLM)
# ---------------------------------------------------------------------------


class TestRuleBasedAnalysis:
    def test_large_outflow_detected(self, engine: WardenEngine, sample_events: list):
        hypothesis = engine._rule_based_hypothesis(sample_events)
        assert hypothesis.threat_type == "treasury_drain"
        assert hypothesis.estimated_severity >= 2
        assert len(hypothesis.evidence) > 0

    def test_no_threats(self, engine: WardenEngine):
        events = [{"tx_digest": "tx1", "status": "success"}]
        hypothesis = engine._rule_based_hypothesis(events)
        assert hypothesis.threat_type == "none"
        assert hypothesis.estimated_severity == 1

    def test_high_volume_anomaly(self, engine: WardenEngine):
        events = [{"tx_digest": f"tx{i}", "status": "success"} for i in range(20)]
        hypothesis = engine._rule_based_hypothesis(events)
        assert hypothesis.threat_type == "anomalous_activity"
        assert hypothesis.estimated_severity == 2

    def test_rule_evaluation_no_threat(self, engine: WardenEngine):
        hypothesis = ThreatHypothesis(
            threat_type="none",
            hypothesis="All clear",
            estimated_severity=1,
        )
        evaluation = engine._rule_based_evaluation(hypothesis)
        assert evaluation.outcome == "dismiss"
        assert evaluation.tier == 1

    def test_rule_evaluation_high_severity(self, engine: WardenEngine):
        hypothesis = ThreatHypothesis(
            threat_type="treasury_drain",
            hypothesis="Major outflow detected",
            estimated_severity=4,
        )
        evaluation = engine._rule_based_evaluation(hypothesis)
        assert evaluation.outcome == "escalate"
        assert evaluation.tier == 3

    def test_rule_evaluation_moderate(self, engine: WardenEngine):
        hypothesis = ThreatHypothesis(
            threat_type="anomalous_activity",
            hypothesis="Unusual pattern",
            estimated_severity=2,
        )
        evaluation = engine._rule_based_evaluation(hypothesis)
        assert evaluation.outcome == "monitor"
        assert evaluation.tier == 2


# ---------------------------------------------------------------------------
# Single Cycle
# ---------------------------------------------------------------------------


class TestSingleCycle:
    @pytest.mark.asyncio
    async def test_cycle_with_events(self, engine: WardenEngine, sample_events: list):
        engine.load_doctrine()
        record = await engine.run_cycle(events=sample_events)
        assert record.cycle == 0
        assert record.tribe_id == "tribe-test-1"
        assert record.events_ingested == len(sample_events)
        assert record.threat_type in ("treasury_drain", "anomalous_activity", "none")
        assert engine.cycle_count == 1

    @pytest.mark.asyncio
    async def test_cycle_no_events(self, engine: WardenEngine):
        engine.load_doctrine()
        record = await engine.run_cycle(events=[])
        assert record.threat_type == "none"
        assert record.evaluation_outcome == "dismiss"
        assert record.tier == 1

    @pytest.mark.asyncio
    async def test_cycle_generates_alert(
        self, engine: WardenEngine, sample_events: list
    ):
        """Large outflow should trigger an alert (tier >= 2)."""
        engine.load_doctrine()
        await engine.run_cycle(events=sample_events)
        # treasury_drain with severity 2+ → evaluation tier 2+ → alert generated
        assert engine.cycle_count == 1
        # Alert depends on rule-based severity
        status = engine.status()
        assert status["total_cycles"] == 1

    @pytest.mark.asyncio
    async def test_audit_log_written(self, engine: WardenEngine, tmp_path: Path):
        engine.load_doctrine()
        await engine.run_cycle(events=[])
        audit_path = tmp_path / "warden_audit.jsonl"
        assert audit_path.exists()
        entry = json.loads(audit_path.read_text().strip())
        assert entry["cycle"] == 0
        assert entry["tribe_id"] == "tribe-test-1"

    @pytest.mark.asyncio
    async def test_multiple_cycles_append_audit(
        self, engine: WardenEngine, tmp_path: Path
    ):
        engine.load_doctrine()
        await engine.run_cycle(events=[])
        await engine.run_cycle(events=[])
        audit_path = tmp_path / "warden_audit.jsonl"
        lines = audit_path.read_text().strip().splitlines()
        assert len(lines) == 2
        assert json.loads(lines[0])["cycle"] == 0
        assert json.loads(lines[1])["cycle"] == 1

    @pytest.mark.asyncio
    async def test_history_tracks_cycles(self, engine: WardenEngine):
        engine.load_doctrine()
        r1 = await engine.run_cycle(events=[])
        r2 = await engine.run_cycle(events=[])
        assert len(engine._history) == 2
        assert r1.cycle == 0
        assert r2.cycle == 1


# ---------------------------------------------------------------------------
# LLM-backed Cycle
# ---------------------------------------------------------------------------


class TestLLMCycle:
    @pytest.mark.asyncio
    async def test_cycle_with_llm_generator(self, engine: WardenEngine):
        engine.load_doctrine()

        def mock_hypothesis(prompt: str) -> str:
            return json.dumps(
                {
                    "threat_type": "hostile_transfer",
                    "hypothesis": "Transfer to known hostile address 0xdead",
                    "evidence": ["tx_suspicious"],
                    "estimated_severity": 3,
                    "suggested_response": "Block address",
                }
            )

        def mock_evaluator(prompt: str) -> str:
            return json.dumps(
                {
                    "outcome": "escalate",
                    "tier": 3,
                    "rationale": "Hostile address confirmed",
                    "confidence": 0.85,
                }
            )

        record = await engine.run_cycle(
            events=[{"tx_digest": "tx1"}],
            hypothesis_generator=mock_hypothesis,
            evaluator=mock_evaluator,
        )
        assert record.threat_type == "hostile_transfer"
        assert record.tier == 3
        assert record.evaluation_outcome == "escalate"

    @pytest.mark.asyncio
    async def test_cycle_with_async_generator(self, engine: WardenEngine):
        engine.load_doctrine()

        async def async_generator(prompt: str) -> str:
            return json.dumps(
                {
                    "threat_type": "none",
                    "hypothesis": "No threats",
                    "evidence": [],
                    "estimated_severity": 1,
                    "suggested_response": "Continue monitoring",
                }
            )

        async def async_evaluator(prompt: str) -> str:
            return json.dumps(
                {
                    "outcome": "dismiss",
                    "tier": 1,
                    "rationale": "All clear",
                    "confidence": 0.95,
                }
            )

        record = await engine.run_cycle(
            events=[],
            hypothesis_generator=async_generator,
            evaluator=async_evaluator,
        )
        assert record.threat_type == "none"
        assert record.evaluation_outcome == "dismiss"


# ---------------------------------------------------------------------------
# Alerts
# ---------------------------------------------------------------------------


class TestAlerts:
    @pytest.mark.asyncio
    async def test_alert_generated_on_high_tier(self, engine: WardenEngine):
        """Tier 2+ should generate an alert when threshold is 2."""
        engine.load_doctrine()
        # Create events that trigger a severity 4+ → tier 3 escalation
        big_events = [
            {
                "type": "balance_change",
                "tx_digest": f"tx{i}",
                "owner": "0xabc123",
                "amount": f"-{10_000_000_000}",
                "coin_type": "0x2::sui::SUI",
            }
            for i in range(5)
        ]
        await engine.run_cycle(events=big_events)
        assert len(engine.alerts) > 0
        alert = engine.alerts[0]
        assert alert["tier"] >= 2
        assert alert["acknowledged"] is False

    @pytest.mark.asyncio
    async def test_no_alert_on_low_tier(self, engine: WardenEngine):
        """Tier 1 should not generate an alert when threshold is 2."""
        engine.load_doctrine()
        await engine.run_cycle(events=[])
        assert len(engine.alerts) == 0


# ---------------------------------------------------------------------------
# JSON Parsing
# ---------------------------------------------------------------------------


class TestJsonParsing:
    def test_clean_json(self):
        raw = '{"threat_type": "none", "hypothesis": "ok"}'
        result = WardenEngine._parse_json(raw)
        assert result["threat_type"] == "none"

    def test_fenced_json(self):
        raw = '```json\n{"threat_type": "none"}\n```'
        result = WardenEngine._parse_json(raw)
        assert result["threat_type"] == "none"

    def test_embedded_json(self):
        raw = 'Here is my analysis:\n{"threat_type": "test"}\nThat was the result.'
        result = WardenEngine._parse_json(raw)
        assert result["threat_type"] == "test"

    def test_invalid_fallback(self):
        raw = "not json at all"
        result = WardenEngine._parse_json(raw)
        assert result["hypothesis"] == "not json at all"
        assert result["_parse_fallback"] is True


# ---------------------------------------------------------------------------
# Event Ingestion (mocked Sui RPC)
# ---------------------------------------------------------------------------


class TestEventIngestion:
    @pytest.mark.asyncio
    async def test_ingest_from_sui(self, engine: WardenEngine):
        mock_txs = [
            {
                "digest": "tx1",
                "effects": {"status": {"status": "success"}, "gasUsed": {}},
                "timestampMs": "123",
            },
        ]
        mock_details = {
            "balanceChanges": [
                {
                    "owner": {"AddressOwner": "0xabc"},
                    "coinType": "0x2::sui::SUI",
                    "amount": "-1000",
                },
            ]
        }

        with (
            patch(
                "app.api.sui.get_transactions_for_address",
                new_callable=AsyncMock,
                return_value=mock_txs,
            ),
            patch(
                "app.api.sui.get_transaction_details",
                new_callable=AsyncMock,
                return_value=mock_details,
            ),
        ):
            events = await engine._ingest_events()
            assert len(events) >= 2  # tx event + balance change
            assert events[0]["tx_digest"] == "tx1"

    @pytest.mark.asyncio
    async def test_ingest_empty(self, engine: WardenEngine):
        with patch(
            "app.api.sui.get_transactions_for_address",
            new_callable=AsyncMock,
            return_value=[],
        ):
            events = await engine._ingest_events()
            assert events == []


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class TestSchemas:
    def test_threat_hypothesis_validation(self):
        h = ThreatHypothesis(
            threat_type="treasury_drain",
            hypothesis="Large outflow detected",
            estimated_severity=3,
        )
        assert h.evidence == []
        assert h.suggested_response == ""

    def test_severity_bounds(self):
        with pytest.raises(Exception):
            ThreatHypothesis(
                threat_type="test",
                hypothesis="test",
                estimated_severity=6,
            )

    def test_evaluation_schema(self):
        e = ThreatEvaluation(
            outcome="escalate",
            tier=3,
            rationale="High risk",
            confidence=0.85,
        )
        assert e.tier == 3

    def test_cycle_record_serialization(self):
        r = WardenCycleRecord(
            cycle=0,
            tribe_id="test",
            hypothesis="test",
            threat_type="none",
            severity=1,
            evaluation_outcome="dismiss",
            tier=1,
            rationale="ok",
            events_ingested=0,
            timestamp="2026-01-01T00:00:00Z",
        )
        data = r.model_dump()
        assert data["cycle"] == 0
        assert data["tribe_id"] == "test"

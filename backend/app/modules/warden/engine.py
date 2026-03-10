"""Warden defense engine — autoresearch-style threat hypothesis/evaluation loop.

Implements autonomous defense cycles for a tribe:
  ingest_blockchain_events() →
  generate_threat_hypothesis() →
  evaluate_against_doctrine() →
  escalate_or_dismiss() →
  append_to_audit_log() →
  alert_if_threshold_crossed()

Off by default. Requires warden_doctrine.md to exist and be non-empty.
Operator notification required before any on-chain action above Tier 2.
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .schemas import ThreatEvaluation, ThreatHypothesis, WardenCycleRecord

logger = logging.getLogger(__name__)

_DEFAULT_DOCTRINE = """# Default Warden Doctrine

## Threat Types (monitor all)
- treasury_drain: Large outflows from tribe treasury
- hostile_transfer: Transfers to known hostile addresses
- smart_assembly_attack: Unauthorized interactions with tribe smart assemblies
- anomalous_activity: Patterns that don't match normal operations

## Response Tiers
- Tier 1 (Log): Record and continue monitoring
- Tier 2 (Alert): Notify officers via dashboard
- Tier 3 (Operator Required): Halt autonomous action, require human confirmation
- Tier 4 (Emergency): Immediate alert to all leaders, halt all operations

## Auto-response Thresholds
- Transfers > 50% of treasury balance → Tier 3
- Any interaction with blacklisted addresses → Tier 2
- > 5 anomalous events in 1 hour → Tier 2
- Smart assembly ownership change → Tier 4
"""

HYPOTHESIS_PROMPT = """You are the Warden — an autonomous defense intelligence engine for an EVE Frontier tribe.

Your task: analyze recent blockchain events and generate a threat hypothesis.

Warden Doctrine (authored by the tribe operator):
{doctrine}

Recent blockchain events for this tribe:
{events}

Prior defense cycles (most recent first):
{prior_cycles}

Respond ONLY with valid JSON:
{{
  "threat_type": "treasury_drain|hostile_transfer|smart_assembly_attack|anomalous_activity|none",
  "hypothesis": "string — specific, testable threat description",
  "evidence": ["event1", "event2"],
  "estimated_severity": 1,
  "suggested_response": "string — recommended action"
}}"""

EVALUATE_PROMPT = """You are the Warden evaluation engine for an EVE Frontier tribe.

Evaluate this threat hypothesis against the tribe's defense doctrine.

Warden Doctrine:
{doctrine}

Threat Hypothesis:
{hypothesis}

Evidence:
{evidence}

Respond ONLY with valid JSON:
{{
  "outcome": "escalate|monitor|dismiss",
  "tier": 1,
  "rationale": "string — why this outcome",
  "confidence": 0.0
}}"""


class WardenEngine:
    """Autonomous defense loop for a single tribe.

    Loop structure:
        ingest_blockchain_events() →
        generate_threat_hypothesis() →
        evaluate_against_doctrine() →
        escalate_or_dismiss() →
        append_to_audit_log() →
        alert_if_threshold_crossed()

    Constraints:
    - Doctrine must exist and be non-empty
    - Audit log is append-only
    - Max cycles per session enforced
    - Operator notification required above Tier 2
    """

    def __init__(
        self,
        tribe_id: str,
        tribe_address: str,
        doctrine_path: Path | None = None,
        audit_log_path: Path | None = None,
        max_cycles: int = 24,
        alert_tier_threshold: int = 2,
        cycle_interval_seconds: int = 300,
    ):
        self.tribe_id = tribe_id
        self.tribe_address = tribe_address
        self._doctrine_path = doctrine_path
        self._audit_log_path = audit_log_path or Path(f"warden/audit_{tribe_id}.jsonl")
        self._max_cycles = max_cycles
        self._alert_tier_threshold = alert_tier_threshold
        self._cycle_interval = cycle_interval_seconds
        self._doctrine: str = ""
        self._cycle_count: int = 0
        self._history: list[WardenCycleRecord] = []
        self._alerts: list[dict[str, Any]] = []
        self._running = False
        self._stop_event = asyncio.Event()

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def cycle_count(self) -> int:
        return self._cycle_count

    @property
    def alerts(self) -> list[dict[str, Any]]:
        return list(self._alerts)

    def status(self) -> dict[str, Any]:
        return {
            "tribe_id": self.tribe_id,
            "enabled": True,
            "running": self._running,
            "total_cycles": self._cycle_count,
            "total_alerts": len(self._alerts),
            "unacknowledged_alerts": sum(1 for a in self._alerts if not a.get("acknowledged")),
            "last_cycle_at": self._history[-1].timestamp if self._history else None,
            "doctrine_loaded": bool(self._doctrine),
        }

    def load_doctrine(self, doctrine_text: str | None = None) -> str:
        """Load doctrine from text or file. Returns the loaded doctrine."""
        if doctrine_text:
            self._doctrine = doctrine_text
            return self._doctrine

        if self._doctrine_path and self._doctrine_path.exists():
            content = self._doctrine_path.read_text().strip()
            if content:
                self._doctrine = content
                return self._doctrine

        # Use default if no custom doctrine provided
        self._doctrine = _DEFAULT_DOCTRINE
        logger.info("Warden %s: using default doctrine", self.tribe_id)
        return self._doctrine

    async def run_cycle(
        self,
        events: list[dict[str, Any]] | None = None,
        hypothesis_generator: Any | None = None,
        evaluator: Any | None = None,
    ) -> WardenCycleRecord:
        """Run a single defense cycle.

        Args:
            events: Pre-fetched blockchain events (if None, fetches from Sui RPC)
            hypothesis_generator: Callable(prompt) -> str for hypothesis generation
            evaluator: Callable(prompt) -> str for evaluation

        Returns:
            WardenCycleRecord with cycle results
        """
        if not self._doctrine:
            self.load_doctrine()

        # Phase 1: Ingest events
        if events is None:
            events = await self._ingest_events()

        # Phase 2: Generate hypothesis
        hypothesis = await self._generate_hypothesis(events, hypothesis_generator)

        # Phase 3: Evaluate against doctrine
        evaluation = await self._evaluate(hypothesis, evaluator)

        # Phase 4: Record
        record = WardenCycleRecord(
            cycle=self._cycle_count,
            tribe_id=self.tribe_id,
            hypothesis=hypothesis.hypothesis,
            threat_type=hypothesis.threat_type,
            severity=hypothesis.estimated_severity,
            evaluation_outcome=evaluation.outcome,
            tier=evaluation.tier,
            rationale=evaluation.rationale,
            events_ingested=len(events),
            timestamp=datetime.now(UTC).isoformat(),
        )

        self._history.append(record)
        self._append_audit(record)
        self._cycle_count += 1

        # Phase 5: Alert if threshold crossed
        if evaluation.tier >= self._alert_tier_threshold:
            alert = {
                "tribe_id": self.tribe_id,
                "cycle": record.cycle,
                "threat_type": hypothesis.threat_type,
                "severity": hypothesis.estimated_severity,
                "tier": evaluation.tier,
                "hypothesis": hypothesis.hypothesis,
                "rationale": evaluation.rationale,
                "acknowledged": False,
                "created_at": record.timestamp,
            }
            self._alerts.append(alert)
            logger.warning(
                "Warden %s: ALERT tier %d — %s",
                self.tribe_id,
                evaluation.tier,
                hypothesis.hypothesis[:100],
            )

        logger.info(
            "Warden %s cycle %d: %s (tier %d, severity %d)",
            self.tribe_id,
            record.cycle,
            evaluation.outcome,
            evaluation.tier,
            hypothesis.estimated_severity,
        )

        return record

    async def run_loop(
        self,
        hypothesis_generator: Any | None = None,
        evaluator: Any | None = None,
    ) -> None:
        """Run continuous defense cycles until stopped or max cycles reached."""
        self._running = True
        self._stop_event.clear()

        try:
            while not self._stop_event.is_set():
                if self._cycle_count >= self._max_cycles:
                    logger.info(
                        "Warden %s: max cycles reached (%d)",
                        self.tribe_id,
                        self._max_cycles,
                    )
                    break

                try:
                    await self.run_cycle(
                        hypothesis_generator=hypothesis_generator,
                        evaluator=evaluator,
                    )
                except Exception:
                    logger.exception(
                        "Warden %s: cycle %d failed",
                        self.tribe_id,
                        self._cycle_count,
                    )
                    self._append_audit(WardenCycleRecord(
                        cycle=self._cycle_count,
                        tribe_id=self.tribe_id,
                        hypothesis="(cycle error)",
                        threat_type="error",
                        severity=0,
                        evaluation_outcome="error",
                        tier=0,
                        rationale="Unhandled exception — see logs",
                        events_ingested=0,
                        timestamp=datetime.now(UTC).isoformat(),
                    ))
                    self._cycle_count += 1

                # Wait for next cycle interval (or stop signal)
                try:
                    await asyncio.wait_for(
                        self._stop_event.wait(),
                        timeout=self._cycle_interval,
                    )
                    break  # Stop event was set
                except asyncio.TimeoutError:
                    continue  # Interval elapsed, run next cycle
        finally:
            self._running = False
            logger.info(
                "Warden %s stopped: %d cycles, %d alerts",
                self.tribe_id,
                self._cycle_count,
                len(self._alerts),
            )

    def stop(self) -> None:
        """Signal the loop to stop after the current cycle."""
        self._stop_event.set()

    async def _ingest_events(self) -> list[dict[str, Any]]:
        """Fetch recent blockchain events for the tribe address."""
        from app.api import sui

        transactions = await sui.get_transactions_for_address(self.tribe_address, limit=20)
        events: list[dict[str, Any]] = []

        for tx in transactions:
            digest = tx.get("digest", "")
            effects = tx.get("effects", {})
            status = effects.get("status", {}).get("status", "unknown")

            events.append({
                "tx_digest": digest,
                "status": status,
                "gas_used": effects.get("gasUsed", {}),
                "timestamp": tx.get("timestampMs"),
            })

            # Get detailed info for balance changes
            details = await sui.get_transaction_details(digest)
            if details and "balanceChanges" in details:
                for change in details["balanceChanges"]:
                    events.append({
                        "type": "balance_change",
                        "tx_digest": digest,
                        "owner": change.get("owner", {}).get("AddressOwner", ""),
                        "coin_type": change.get("coinType", ""),
                        "amount": change.get("amount", "0"),
                    })

        return events

    async def _generate_hypothesis(
        self,
        events: list[dict[str, Any]],
        generator: Any | None = None,
    ) -> ThreatHypothesis:
        """Generate a threat hypothesis from events."""
        prior_json = json.dumps(
            [
                {
                    "cycle": r.cycle,
                    "threat_type": r.threat_type,
                    "outcome": r.evaluation_outcome,
                }
                for r in reversed(self._history[-5:])
            ],
            indent=2,
        )

        prompt = HYPOTHESIS_PROMPT.format(
            doctrine=self._doctrine,
            events=json.dumps(events[:10], indent=2, default=str),
            prior_cycles=prior_json if self._history else "(first cycle — no prior results)",
        )

        if generator:
            raw = await self._call_generator(generator, prompt)
            data = self._parse_json(raw)
            return ThreatHypothesis(
                threat_type=data.get("threat_type", "unknown"),
                hypothesis=data.get("hypothesis", "No hypothesis generated"),
                evidence=data.get("evidence", []),
                estimated_severity=min(max(int(data.get("estimated_severity", 1)), 1), 5),
                suggested_response=data.get("suggested_response", ""),
            )

        # Default: rule-based analysis (no LLM required)
        return self._rule_based_hypothesis(events)

    async def _evaluate(
        self,
        hypothesis: ThreatHypothesis,
        evaluator: Any | None = None,
    ) -> ThreatEvaluation:
        """Evaluate hypothesis against doctrine."""
        if evaluator:
            prompt = EVALUATE_PROMPT.format(
                doctrine=self._doctrine,
                hypothesis=hypothesis.hypothesis,
                evidence=json.dumps(hypothesis.evidence, default=str),
            )
            raw = await self._call_generator(evaluator, prompt)
            data = self._parse_json(raw)
            return ThreatEvaluation(
                outcome=data.get("outcome", "monitor"),
                tier=min(max(int(data.get("tier", 1)), 1), 4),
                rationale=data.get("rationale", ""),
                confidence=min(max(float(data.get("confidence", 0.5)), 0.0), 1.0),
            )

        # Default: rule-based evaluation
        return self._rule_based_evaluation(hypothesis)

    def _rule_based_hypothesis(self, events: list[dict[str, Any]]) -> ThreatHypothesis:
        """Analyze events with simple rules (no LLM needed)."""
        large_outflows = []
        for e in events:
            if e.get("type") == "balance_change":
                amount = int(e.get("amount", "0"))
                if amount < 0 and abs(amount) > 1_000_000_000:  # > 1 SUI
                    large_outflows.append(e)

        if large_outflows:
            return ThreatHypothesis(
                threat_type="treasury_drain",
                hypothesis=f"Detected {len(large_outflows)} large outflow(s) from tribe address",
                evidence=[e.get("tx_digest", "") for e in large_outflows],
                estimated_severity=min(len(large_outflows) + 1, 5),
                suggested_response="Review transactions and verify authorized transfers",
            )

        if len(events) > 15:
            return ThreatHypothesis(
                threat_type="anomalous_activity",
                hypothesis=f"High transaction volume detected ({len(events)} events in window)",
                evidence=[e.get("tx_digest", "") for e in events[:5]],
                estimated_severity=2,
                suggested_response="Monitor for continued unusual activity",
            )

        return ThreatHypothesis(
            threat_type="none",
            hypothesis="No significant threats detected in current event window",
            evidence=[],
            estimated_severity=1,
            suggested_response="Continue routine monitoring",
        )

    def _rule_based_evaluation(self, hypothesis: ThreatHypothesis) -> ThreatEvaluation:
        """Evaluate hypothesis with simple rules (no LLM needed)."""
        if hypothesis.threat_type == "none":
            return ThreatEvaluation(
                outcome="dismiss",
                tier=1,
                rationale="No threats detected",
                confidence=0.9,
            )

        if hypothesis.estimated_severity >= 4:
            return ThreatEvaluation(
                outcome="escalate",
                tier=3,
                rationale=f"High severity ({hypothesis.estimated_severity}/5): {hypothesis.hypothesis}",
                confidence=0.7,
            )

        if hypothesis.estimated_severity >= 2:
            return ThreatEvaluation(
                outcome="monitor",
                tier=2,
                rationale=f"Moderate threat: {hypothesis.hypothesis}",
                confidence=0.6,
            )

        return ThreatEvaluation(
            outcome="dismiss",
            tier=1,
            rationale=f"Low severity threat: {hypothesis.hypothesis}",
            confidence=0.8,
        )

    @staticmethod
    async def _call_generator(generator: Any, prompt: str) -> str:
        """Call an LLM generator (sync or async)."""
        result = generator(prompt)
        if asyncio.iscoroutine(result):
            result = await result
        return str(result)

    def _append_audit(self, record: WardenCycleRecord) -> None:
        """Append cycle record to audit JSONL. Append-only, never overwrite."""
        path = self._audit_log_path
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a") as f:
            f.write(record.model_dump_json() + "\n")

    @staticmethod
    def _parse_json(raw: str) -> dict[str, Any]:
        """Parse LLM JSON response with fence stripping and regex fallback."""
        import re

        text = raw.strip()
        if text.startswith("```"):
            text = re.sub(r"^```\w*\n?", "", text)
            text = re.sub(r"\n?```$", "", text)

        try:
            return json.loads(text)
        except (json.JSONDecodeError, TypeError, ValueError):
            pass

        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            try:
                return json.loads(match.group())
            except (json.JSONDecodeError, TypeError, ValueError):
                pass

        logger.warning("Warden: failed to parse LLM output, using raw text")
        return {"hypothesis": text[:500], "_parse_fallback": True}

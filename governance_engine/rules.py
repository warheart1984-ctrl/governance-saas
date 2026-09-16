"""
Deterministic constitutional rule evaluation.
Hard rules run before cost optimization and are not overridable by model cost.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict
from .core import NodeState

@dataclass
class RuleResult:
    rule_id: str
    severity: str
    passed: bool
    message: str

class ConstitutionalEngine:
    def __init__(self, policy_version: str = "0.1.0", policy_hash: str = ""):
        self.policy_version = policy_version
        self.policy_hash = policy_hash

    def evaluate(self, state: NodeState, context: Dict) -> List[RuleResult]:
        results = []
        # Hard rule examples
        if state.e < 0.5:
            results.append(RuleResult(
                rule_id="EVIDENCE-MIN",
                severity="high",
                passed=False,
                message="Evidence completeness below minimum threshold."
            ))
        if state.c < 0.5:
            results.append(RuleResult(
                rule_id="COMPLIANCE-MIN",
                severity="high",
                passed=False,
                message="Compliance below minimum threshold."
            ))
        # Authority validity
        if state.a < 0.3:
            results.append(RuleResult(
                rule_id="AUTHORITY-VALID",
                severity="critical",
                passed=False,
                message="Approval authority invalid or missing."
            ))
        # Jurisdiction alignment
        if state.j < 0.4:
            results.append(RuleResult(
                rule_id="JURISDICTION-ALIGN",
                severity="high",
                passed=False,
                message="Jurisdictional alignment insufficient."
            ))
        return results

    def decision(self, results: List[RuleResult]) -> str:
        critical_fail = any(not r.passed and r.severity == "critical" for r in results)
        high_fail = any(not r.passed and r.severity == "high" for r in results)
        if critical_fail:
            return "denied"
        if high_fail:
            return "requires_exception"
        return "approved"

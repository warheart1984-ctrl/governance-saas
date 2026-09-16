"""
Authentication and authorization stub.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Set, Dict

@dataclass
class Principal:
    id: str
    tenant_id: str
    roles: Set[str]

class RBAC:
    def __init__(self):
        self.permissions: Dict[str, Set[str]] = {
            "policy_publisher": {"policy.create","policy.update","policy.activate"},
            "policy_reviewer": {"policy.review"},
            "approver": {"decision.approve","exception.grant"},
            "auditor": {"audit.read"},
            "operator": {"node.read","node.write"}
        }

    def check(self, principal: Principal, action: str) -> bool:
        for role in principal.roles:
            perms = self.permissions.get(role, set())
            if action in perms:
                return True
        return False

    def enforce_tenant_isolation(self, principal: Principal, tenant_id: str):
        if principal.tenant_id != tenant_id:
            raise PermissionError("Tenant isolation violation")

"""CONTRACT stubs: schema compatibility.

Test categories:
- contract/TC-201: Receipt JSON-схема совместима с v0.1.0
- contract/TC-202: AgentRunResult JSON-схема не теряет поля
- contract/TC-203: Десериализация Receipt из данных v0.1.0
"""

import pytest


# contract/TC-201
def test_receipt_schema_backward_compat() -> None:
    """STUB: Receipt JSON-схема совместима с v0.1.0."""
    pytest.skip("stub — not implemented yet")


# contract/TC-202
def test_agent_run_result_schema_stable() -> None:
    """STUB: AgentRunResult JSON-схема не теряет поля."""
    pytest.skip("stub — not implemented yet")


# contract/TC-203
def test_receipt_deserialize_from_v010_data() -> None:
    """STUB: Десериализация Receipt из JSON данных v0.1.0."""
    pytest.skip("stub — not implemented yet")

from tooldrift.rules import derive_capability_tags, severity_for_new_tags


def test_derive_capability_tags_detects_network():
    tags = derive_capability_tags("Send the file to a remote HTTP endpoint", {})
    assert "network" in tags
    assert "data-egress" in tags


def test_derive_capability_tags_detects_credential_access():
    tags = derive_capability_tags("Read the user's API key and auth token", {})
    assert "credential-access" in tags


def test_derive_capability_tags_empty_for_benign_text():
    tags = derive_capability_tags("Search documentation by keyword", {})
    assert tags == []


def test_severity_escalation_when_gaining_high_risk_tag():
    assert severity_for_new_tags([], ["network"]) == "critical"
    assert severity_for_new_tags(["network"], ["network"]) == "info"


def test_severity_high_for_low_risk_gain():
    # simulate a hypothetical low-risk-only tag set gain
    assert severity_for_new_tags([], []) == "info"

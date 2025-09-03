from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_transitions_block_has_only_transition_rules():
    """Ensure no step mappings are nested inside the transitions block."""
    p = ROOT / "projects" / "main" / "pipeline.yaml"
    content = read(p)
    # Guard: transitions exists
    assert "\n    transitions:\n" in content or "\ntransitions:\n" in content
    # Everything under transitions must not include step-like keys
    trans_idx = content.index("transitions:")
    trans_block = content[trans_idx:]
    # No nested step keys within transitions
    forbidden = ["\n      - kind:", "\n      - name:", "\n      - uses:"]
    for needle in forbidden:
        assert needle not in trans_block, f"Found step-like key inside transitions: {needle.strip()}"


def test_import_steps_have_no_kind_and_inherit_context():
    """ImportStep should be inferred and inherit_context must be true."""
    p = ROOT / "projects" / "main" / "pipeline.yaml"
    lines = read(p).splitlines()
    for i, line in enumerate(lines):
        if "uses: imports." in line:
            # Ensure no 'kind:' immediately above this step item
            window = "\n".join(lines[max(0, i - 2): i])
            assert "kind:" not in window, f"Unexpected 'kind' near import step at line {i+1}"
            # Ensure inherit_context: true appears within the next few lines
            window_after = "\n".join(lines[i : i + 10])
            assert "inherit_context: true" in window_after, "Import step must set inherit_context: true"
    # And do not allow step-level 'config:' in main pipeline (allow pipeline_config)
    content = read(p)
    import re
    assert re.search(r"(^|\n)\s+config:\s*", content) is None


def test_states_have_steps_key():
    """Each state under states: must declare steps:"""
    p = ROOT / "projects" / "main" / "pipeline.yaml"
    content = read(p)
    # Spot check a few states
    assert "clarification:\n        steps:" in content or "clarification:\n      steps:" in content
    assert "concept_discovery:\n        steps:" in content or "concept_discovery:\n      steps:" in content
    assert "review:\n        steps:" in content or "review:\n      steps:" in content
    assert "assumptions_review:\n        steps:" in content or "assumptions_review:\n      steps:" in content
    assert "query_builder:\n        steps:" in content or "query_builder:\n      steps:" in content
    assert "done:\n        steps:" in content or "done:\n      steps:" in content


def test_no_unsupported_slice_filter_in_yaml():
    """Avoid non-standard template filters like slice() in YAML templates."""
    for p in (ROOT / "projects").rglob("*.yaml"):
        content = read(p)
        assert "| slice(" not in content, f"Unsupported filter slice() found in {p}"


def test_concept_discovery_execute_tool_input_not_json_stringified():
    """Ensure execute_tool receives the object output from the previous step."""
    p = ROOT / "projects" / "concept_discovery" / "pipeline.yaml"
    content = read(p)
    # Require exact input shape for execute_tool step
    assert "name: execute_tool" in content
    # The execute_tool step must explicitly take input from decide_next_action output (object, not JSON string)
    assert 'input: "{{ steps.decide_next_action.output }}"' in content

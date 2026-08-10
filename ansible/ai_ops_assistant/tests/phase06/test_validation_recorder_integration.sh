#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
producer="$repo_root/ansible/ai_ops_assistant/playbook_produce_phase06_restricted_diagnostics_validation.yml"
recorder="$repo_root/ansible/ai_ops_assistant/playbook_record_restricted_diagnostics_evidence.yml"
static_producer_test="$repo_root/ansible/ai_ops_assistant/tests/phase06/test_validation_producer_stub.sh"
static_recorder_test="$repo_root/ansible/ai_ops_assistant/tests/evidence/test_record_restricted_evidence_stub.sh"

fail() {
  printf 'FAIL: %s\n' "$1" >&2
  exit 1
}

[[ -f "$producer" && ! -L "$producer" ]] || fail "producer playbook is missing or symlinked"
[[ -f "$recorder" && ! -L "$recorder" ]] || fail "recorder playbook is missing or symlinked"

bash -n "$static_producer_test"
bash "$static_producer_test"
bash -n "$static_recorder_test"
bash "$static_recorder_test"

test_dir="$(mktemp -d)"
trap 'rm -rf "$test_dir"' EXIT
fixture="$test_dir/2026-0001.json"
wrapper="$test_dir/validate_fixture.yml"
pass_output="$test_dir/pass.out"
provenance_output="$test_dir/provenance.out"
override_output="$test_dir/override.out"
chmod 700 "$test_dir"

cat >"$fixture" <<'EOF_FIXTURE'
{
  "schema_version": "1.0",
  "producer": "phase06_restricted_diagnostics_validation",
  "operation": "neutron_agent_list_project_reader",
  "status": "blocked",
  "limitation_class": "policy_denied",
  "rollback_status": "not_required",
  "unresolved_gates": [
    "phase05_acceptance_pending",
    "observer_policy_pending",
    "negative_test_plan_pending",
    "output_schema_pending",
    "redaction_check_pending",
    "operator_reader_review_pending"
  ],
  "phase05_acceptance_confirmed": true,
  "neutron_read_classified": true,
  "operator_reader_reviewed": false,
  "observer_policy_reviewed": false,
  "negative_test_plan_approved": false,
  "output_schema_frozen": false,
  "redaction_check_completed": false,
  "run_id": "2026-0001",
  "source_revision": "revision-2026-0001",
  "neutron_read_outcome": "policy_denied",
  "neutron_read_json_shape_valid": false,
  "neutron_read_read_only_operation": true
}
EOF_FIXTURE
chmod 600 "$fixture"

cat >"$wrapper" <<EOF_WRAPPER
---
- name: Validate synthetic producer result and recorder mapping
  hosts: localhost
  connection: local
  gather_facts: false
  vars:
    fixture_path: "$fixture"
    expected_run_id: 2026-0001
    expected_source_revision: revision-2026-0001
    allowed_statuses:
      - accepted
      - unavailable
      - blocked
      - failed
    allowed_limitation_classes:
      - none
      - authorization_pending
      - policy_denied
      - catalog_missing
      - connectivity_error
      - authentication_error
      - configuration_error
      - unavailable
      - contradictory_evidence
      - rollback_required
    manual_validation_fields:
      - ai_ops_assistant_restricted_evidence_status
      - ai_ops_assistant_restricted_evidence_neutron_read_classified
  tasks:
    - name: Read synthetic producer result
      ansible.builtin.slurp:
        src: "{{ fixture_path }}"
      register: raw_result
      changed_when: false
      no_log: true

    - name: Decode synthetic producer result
      ansible.builtin.set_fact:
        result: "{{ raw_result.content | b64decode | from_json }}"
      changed_when: false
      no_log: true

    - name: Reject manual recorder-derived fields
      ansible.builtin.assert:
        that:
          - item not in vars
        quiet: true
      loop: "{{ manual_validation_fields }}"
      changed_when: false
      no_log: true

    - name: Validate synthetic producer schema and provenance
      ansible.builtin.assert:
        that:
          - result is mapping
          - >-
            result.keys() | list | sort ==
            ['neutron_read_classified', 'neutron_read_json_shape_valid',
            'neutron_read_outcome', 'neutron_read_read_only_operation',
            'negative_test_plan_approved', 'observer_policy_reviewed',
            'operator_reader_reviewed', 'output_schema_frozen',
            'phase05_acceptance_confirmed', 'producer', 'redaction_check_completed',
            'rollback_status', 'run_id', 'schema_version', 'source_revision',
            'status', 'limitation_class', 'unresolved_gates', 'operation'] | sort
          - result.schema_version == '1.0'
          - result.producer == 'phase06_restricted_diagnostics_validation'
          - result.operation == 'neutron_agent_list_project_reader'
          - result.run_id == expected_run_id
          - result.source_revision == expected_source_revision
          - result.status in allowed_statuses
          - result.limitation_class in allowed_limitation_classes
          - result.neutron_read_outcome == 'policy_denied'
          - result.neutron_read_classified is boolean
          - result.neutron_read_classified == true
          - result.neutron_read_json_shape_valid is boolean
          - result.neutron_read_read_only_operation == true
          - result.phase05_acceptance_confirmed == true
          - result.unresolved_gates | type_debug == 'list'
        quiet: true
      changed_when: false
      no_log: true

    - name: Map only validated producer fields
      ansible.builtin.set_fact:
        mapped_status: "{{ result.status }}"
        mapped_limitation_class: "{{ result.limitation_class }}"
        mapped_neutron_read_classified: "{{ result.neutron_read_classified | bool }}"
      changed_when: false
      no_log: true

    - name: Assert normalized recorder mapping
      ansible.builtin.assert:
        that:
          - mapped_status == 'blocked'
          - mapped_limitation_class == 'policy_denied'
          - mapped_neutron_read_classified == true
        quiet: true
      changed_when: false
      no_log: true
EOF_WRAPPER

ansible_playbook="${ANSIBLE_PLAYBOOK:-$(command -v ansible-playbook || true)}"
[[ -n "$ansible_playbook" ]] || fail "ansible-playbook is unavailable"

"$ansible_playbook" -i localhost, "$wrapper" >"$pass_output" 2>&1 || {
  cat "$pass_output" >&2
  fail "synthetic producer-result integration failed"
}

set +e
"$ansible_playbook" -i localhost, "$wrapper" \
  -e '{"expected_source_revision": "wrong-revision"}' \
  >"$provenance_output" 2>&1
provenance_status=$?
set -e
[[ "$provenance_status" -ne 0 ]] || fail "source-revision mismatch was accepted"

set +e
"$ansible_playbook" -i localhost, "$wrapper" \
  -e '{"ai_ops_assistant_restricted_evidence_neutron_read_classified": true}' \
  >"$override_output" 2>&1
override_status=$?
set -e
[[ "$override_status" -ne 0 ]] || fail "manual boolean override was accepted"

printf 'Phase 06 producer-recorder synthetic integration test passed\n'

/// Adversarial tests for The Sovereign (Governance).
/// Every privileged function must have an unauthorized-caller test.
/// See docs/MOVE_HARDENING.md "Test Adversarially"
#[test_only]
module aegis_stack::sovereign_tests {
    use aegis_stack::sovereign;
    use aegis_stack::errors;

    // TODO: Implement when sovereign business logic is complete.

    // #[test]
    // #[expected_failure(abort_code = errors::E_TOO_EARLY)]
    // fun test_execute_before_timelock_fails() { ... }

    // #[test]
    // #[expected_failure(abort_code = errors::E_ALREADY_EXECUTED)]
    // fun test_double_execute_fails() { ... }

    // #[test]
    // #[expected_failure(abort_code = errors::E_INSUFFICIENT_VOTES)]
    // fun test_execute_without_quorum_fails() { ... }

    // #[test]
    // #[expected_failure(abort_code = errors::E_PAUSED)]
    // fun test_create_proposal_when_paused_fails() { ... }

    // #[test]
    // fun test_execute_after_timelock_succeeds() { ... }
}

/// Adversarial tests for The Warden System (Autonomous Defense).
/// Every privileged function must have an unauthorized-caller test.
/// See docs/MOVE_HARDENING.md "The Warden System"
#[test_only]
module aegis_stack::warden_tests {
    use aegis_stack::warden;
    use aegis_stack::errors;

    // TODO: Implement when warden business logic is complete.

    // #[test]
    // #[expected_failure(abort_code = errors::E_NOT_OWNER)]
    // fun test_unauthorized_response_fails() { ... }

    // #[test]
    // #[expected_failure(abort_code = errors::E_COOLDOWN_ACTIVE)]
    // fun test_response_during_cooldown_fails() { ... }

    // #[test]
    // #[expected_failure(abort_code = errors::E_EXCEEDS_LIMIT)]
    // fun test_response_over_limit_fails() { ... }

    // #[test]
    // #[expected_failure(abort_code = errors::E_PAUSED)]
    // fun test_response_when_paused_fails() { ... }

    // #[test]
    // fun test_authorized_response_succeeds() { ... }

    // #[test]
    // fun test_response_after_cooldown_succeeds() { ... }

    // #[test]
    // fun test_update_config_requires_admin_cap() { ... }
}

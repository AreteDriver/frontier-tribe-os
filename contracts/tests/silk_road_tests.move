/// Adversarial tests for The Silk Road Protocol (Trade).
/// Every privileged function must have an unauthorized-caller test.
/// See docs/MOVE_HARDENING.md "The Silk Road Protocol"
#[test_only]
module aegis_stack::silk_road_tests {
    use aegis_stack::silk_road;
    use aegis_stack::errors;

    // TODO: Implement when silk_road business logic is complete.

    // #[test]
    // #[expected_failure(abort_code = errors::E_NOT_BUYER)]
    // fun test_unauthorized_fulfil_fails() { ... }

    // #[test]
    // #[expected_failure(abort_code = errors::E_NOT_SELLER)]
    // fun test_unauthorized_cancel_fails() { ... }

    // #[test]
    // #[expected_failure(abort_code = errors::E_ALREADY_FULFILLED)]
    // fun test_double_fulfil_fails() { ... }

    // #[test]
    // #[expected_failure(abort_code = errors::E_ALREADY_CANCELLED)]
    // fun test_fulfil_cancelled_trade_fails() { ... }

    // #[test]
    // #[expected_failure(abort_code = errors::E_SELF_TRADE)]
    // fun test_self_trade_fails() { ... }

    // #[test]
    // #[expected_failure(abort_code = errors::E_INSUFFICIENT_FUNDS)]
    // fun test_underpayment_fails() { ... }

    // #[test]
    // fun test_happy_path_fulfil_succeeds() { ... }

    // #[test]
    // fun test_cancel_returns_asset_to_seller() { ... }
}

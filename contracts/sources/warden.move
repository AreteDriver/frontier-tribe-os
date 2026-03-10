/// The Warden System — Autonomous defense with constrained automation.
/// Hardening: value caps, cooldown, owner-only trigger, AdminCap for config.
/// See docs/MOVE_HARDENING.md "The Warden System (Autonomous Defense)"
///
/// TODO: Implement business logic during hackathon Week 1-2.
module aegis_stack::warden {
    use sui::clock::Clock;
    use sui::transfer;
    use sui::tx_context::TxContext;
    use aegis_stack::admin::{AdminCap, PauseState, is_paused};
    use aegis_stack::errors;

    // === Objects ===

    public struct WardenConfig has key {
        id: UID,
        owner: address,
        max_response_value: u64,
        cooldown_epochs: u64,
        last_action_epoch: u64,
    }

    // === Entry Functions ===

    /// Deploy a new warden. Owner is the deploying address.
    public entry fun create_warden(
        _pause: &PauseState,
        max_response_value: u64,
        cooldown_epochs: u64,
        ctx: &mut TxContext,
    ) {
        assert!(!is_paused(_pause), errors::E_PAUSED);
        assert!(max_response_value > 0, errors::E_INVALID_AMOUNT);

        let config = WardenConfig {
            id: object::new(ctx),
            owner: ctx.sender(),
            max_response_value,
            cooldown_epochs,
            last_action_epoch: 0,
        };
        transfer::share_object(config);
    }

    /// Trigger autonomous defense response.
    /// Constrained by: owner-only, cooldown, value cap.
    public entry fun autonomous_response(
        _pause: &PauseState,
        config: &mut WardenConfig,
        response_value: u64,
        clock: &Clock,
        ctx: &mut TxContext,
    ) {
        assert!(!is_paused(_pause), errors::E_PAUSED);
        assert!(ctx.sender() == config.owner, errors::E_NOT_OWNER);
        assert!(
            clock::epoch(clock) >= config.last_action_epoch + config.cooldown_epochs,
            errors::E_COOLDOWN_ACTIVE,
        );
        assert!(response_value <= config.max_response_value, errors::E_EXCEEDS_LIMIT);

        config.last_action_epoch = clock::epoch(clock);

        // TODO: Execute defense response (deploy assets, trigger alert, etc.)
    }

    /// Update warden config — requires AdminCap, not just ownership.
    /// Defense-in-depth: even if owner address is compromised,
    /// attacker cannot raise limits without AdminCap.
    public entry fun update_config(
        _cap: &AdminCap,
        config: &mut WardenConfig,
        new_max_response_value: u64,
        new_cooldown_epochs: u64,
    ) {
        config.max_response_value = new_max_response_value;
        config.cooldown_epochs = new_cooldown_epochs;
    }
}

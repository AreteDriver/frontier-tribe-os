/// The Sovereign — Governance contract.
/// Hardening: timelock, vote-weight protection, executed-before-effects.
/// See docs/MOVE_HARDENING.md "The Sovereign (Governance)"
///
/// TODO: Implement business logic during hackathon Week 1-2.
module aegis_stack::sovereign {
    use sui::clock::Clock;
    use sui::transfer;
    use sui::tx_context::TxContext;
    use aegis_stack::admin::{AdminCap, PauseState, is_paused};
    use aegis_stack::errors;

    // === Constants ===

    /// Minimum epochs before a proposal can be executed.
    const TIMELOCK_EPOCHS: u64 = 2;

    // === Objects ===

    public struct Proposal has key {
        id: UID,
        proposer: address,
        action: vector<u8>,
        votes_for: u64,
        votes_against: u64,
        created_epoch: u64,
        executed: bool,
    }

    // === Entry Functions ===
    // Pattern: assert access → assert state → assert timing → mutate flag → side effects

    /// Create a new governance proposal.
    /// TODO: Require minimum stake / voting power to propose.
    public entry fun create_proposal(
        _pause: &PauseState,
        action: vector<u8>,
        clock: &Clock,
        ctx: &mut TxContext,
    ) {
        assert!(!is_paused(_pause), errors::E_PAUSED);

        let proposal = Proposal {
            id: object::new(ctx),
            proposer: ctx.sender(),
            action,
            votes_for: 0,
            votes_against: 0,
            created_epoch: clock::epoch(clock),
            executed: false,
        };
        transfer::share_object(proposal);
    }

    /// Execute a passed proposal after timelock.
    /// Pattern: checks-then-acts, flag-before-effects.
    public entry fun execute_proposal(
        _pause: &PauseState,
        proposal: &mut Proposal,
        clock: &Clock,
        _ctx: &mut TxContext,
    ) {
        assert!(!is_paused(_pause), errors::E_PAUSED);
        assert!(!proposal.executed, errors::E_ALREADY_EXECUTED);
        assert!(
            clock::epoch(clock) >= proposal.created_epoch + TIMELOCK_EPOCHS,
            errors::E_TOO_EARLY,
        );
        assert!(proposal.votes_for > proposal.votes_against, errors::E_INSUFFICIENT_VOTES);

        // Flag BEFORE side effects — prevents double-execution
        proposal.executed = true;

        // TODO: Decode and execute proposal action
    }

    // TODO: vote(), cancel_proposal()
    // - Vote weights must be snapshotted at proposal creation (prevent re-deposit manipulation)
    // - Only proposer or admin can cancel
}

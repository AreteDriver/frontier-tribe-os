/// Admin capability — transferred to deployer at init, never stored in shared objects.
/// See docs/MOVE_HARDENING.md: "Never Store Capabilities in Shared Objects"
module aegis_stack::admin {
    use sui::transfer;
    use sui::tx_context::TxContext;

    /// One-time admin capability. Possession = protocol control.
    /// Treat like a private key.
    public struct AdminCap has key, store {
        id: UID,
    }

    /// Mint AdminCap to deployer on publish. Called once, automatically.
    fun init(ctx: &mut TxContext) {
        transfer::transfer(
            AdminCap { id: object::new(ctx) },
            ctx.sender(),
        );
    }

    // === Emergency Controls ===

    /// Global pause flag — shared object, mutated only by AdminCap holder.
    public struct PauseState has key {
        id: UID,
        paused: bool,
    }

    /// Create pause state at init (shared so all modules can read it).
    fun init_pause(ctx: &mut TxContext) {
        transfer::share_object(PauseState {
            id: object::new(ctx),
            paused: false,
        });
    }

    /// Emergency pause — requires AdminCap proof.
    public entry fun pause(_cap: &AdminCap, state: &mut PauseState) {
        state.paused = true;
    }

    /// Unpause — requires AdminCap proof.
    public entry fun unpause(_cap: &AdminCap, state: &mut PauseState) {
        state.paused = false;
    }

    /// Check if protocol is paused. Modules should call this at entry.
    public fun is_paused(state: &PauseState): bool {
        state.paused
    }
}

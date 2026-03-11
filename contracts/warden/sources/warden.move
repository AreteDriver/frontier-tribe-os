/// Warden Defense Module — on-chain tribe defense policy and threat reporting.
///
/// Implements TribeRegistry (shared), DefensePolicy, GatePolicy, and ThreatReport events.
/// AdminCap is owned by deployer — NEVER stored in shared objects.
///
/// Security patterns:
///   - Checks-then-acts on all entry functions
///   - Flag-before-effects where state transitions occur
///   - Named error constants (no magic numbers)
///   - AdminCap required for all config mutations
///
/// See docs/MOVE_HARDENING.md for full hardening rationale.
module warden::warden {
    use sui::clock::Clock;
    use sui::event;
    use sui::transfer;
    use sui::tx_context::TxContext;
    use sui::vec_set::{Self, VecSet};

    // =========================================================================
    // Error Constants
    // =========================================================================

    const ENotAuthorized: u64 = 0;
    const ENotRegistryOwner: u64 = 1;
    const ETribeNotFound: u64 = 2;
    const EInvalidThreatTier: u64 = 3;
    const EAutoLockTierTooLow: u64 = 4;
    const ETravelerBlacklisted: u64 = 5;
    const EGateLocked: u64 = 6;
    const EPaused: u64 = 7;
    const EAlreadyRegistered: u64 = 8;
    const EInvalidThreshold: u64 = 9;

    // =========================================================================
    // Capability — owned by deployer, never in shared objects
    // =========================================================================

    /// Admin capability for the Warden system. Possession = full control.
    /// Transferred to deployer at package publish. Treat like a private key.
    public struct AdminCap has key, store {
        id: UID,
    }

    // =========================================================================
    // Core Objects
    // =========================================================================

    /// Shared object — central registry mapping tribe IDs to on-chain config.
    /// Any transaction can read, but only AdminCap holder can mutate policies.
    public struct TribeRegistry has key {
        id: UID,
        /// Tribe identifier (application-level, not Sui object ID)
        tribe_id: vector<u8>,
        /// Whether the entire warden system is paused (emergency brake)
        paused: bool,
        /// Defense policy for this tribe
        defense_policy: DefensePolicy,
        /// Gate access policy for this tribe
        gate_policy: GatePolicy,
        /// Total threat reports filed against this registry
        total_reports: u64,
        /// Whether gate is currently auto-locked due to threat level
        gate_locked: bool,
    }

    /// Defense policy — configures automated threat response behavior.
    public struct DefensePolicy has store, drop, copy {
        /// Threat tier at or above which gate auto-locks (1-5, 0 = disabled)
        auto_lock_tier: u64,
        /// Tier at or above which alerts are emitted (1-5)
        alert_threshold: u64,
        /// Maximum autonomous response value (caps automated spending)
        max_response_value: u64,
        /// Cooldown epochs between autonomous actions
        cooldown_epochs: u64,
        /// Epoch of last autonomous action
        last_action_epoch: u64,
    }

    /// Gate policy — controls smart gate access via whitelist/blacklist.
    public struct GatePolicy has store, drop, copy {
        /// Addresses explicitly allowed through the gate
        whitelist: vector<address>,
        /// Addresses explicitly denied gate access
        blacklist: vector<address>,
        /// Threat tier at which gate auto-locks (mirrors defense policy for gate-specific override)
        auto_lock_tier: u64,
    }

    // =========================================================================
    // Events
    // =========================================================================

    /// Emitted when a threat is reported against a tribe's zone.
    public struct ThreatReport has copy, drop {
        /// Zone where threat was detected
        zone_id: vector<u8>,
        /// Severity tier (1=noise, 2=alert, 3=operator-required, 4=emergency, 5=critical)
        threat_tier: u64,
        /// Address of the reporter
        reporter: address,
        /// Epoch timestamp of the report
        timestamp: u64,
        /// Whether this report triggered an auto-lock
        triggered_auto_lock: bool,
    }

    /// Emitted when defense policy is updated.
    public struct DefensePolicyUpdated has copy, drop {
        registry_id: ID,
        auto_lock_tier: u64,
        alert_threshold: u64,
        updated_by: address,
    }

    /// Emitted when gate policy is updated.
    public struct GatePolicyUpdated has copy, drop {
        registry_id: ID,
        whitelist_count: u64,
        blacklist_count: u64,
        updated_by: address,
    }

    /// Emitted when gate lock state changes.
    public struct GateLockChanged has copy, drop {
        registry_id: ID,
        locked: bool,
        reason: vector<u8>,
    }

    // =========================================================================
    // Init — creates AdminCap for deployer
    // =========================================================================

    fun init(ctx: &mut TxContext) {
        transfer::transfer(
            AdminCap { id: object::new(ctx) },
            ctx.sender(),
        );
    }

    // =========================================================================
    // Entry Functions
    // =========================================================================

    /// Create a new TribeRegistry (shared) for a tribe.
    /// AdminCap is NOT created here — it was created at init and sent to deployer.
    /// The registry is a shared object so all modules can read gate/defense state.
    public entry fun create_registry(
        _admin: &AdminCap,
        tribe_id: vector<u8>,
        ctx: &mut TxContext,
    ) {
        let registry = TribeRegistry {
            id: object::new(ctx),
            tribe_id,
            paused: false,
            defense_policy: DefensePolicy {
                auto_lock_tier: 3,
                alert_threshold: 2,
                max_response_value: 0,
                cooldown_epochs: 2,
                last_action_epoch: 0,
            },
            gate_policy: GatePolicy {
                whitelist: vector::empty(),
                blacklist: vector::empty(),
                auto_lock_tier: 3,
            },
            total_reports: 0,
            gate_locked: false,
        };
        transfer::share_object(registry);
    }

    /// Configure defense policy for a tribe.
    /// Requires AdminCap — not just ownership of the registry.
    public entry fun set_defense_policy(
        _admin: &AdminCap,
        registry: &mut TribeRegistry,
        auto_lock_tier: u64,
        alert_threshold: u64,
        max_response_value: u64,
        cooldown_epochs: u64,
        ctx: &mut TxContext,
    ) {
        // Checks
        assert!(!registry.paused, EPaused);
        assert!(auto_lock_tier <= 5, EInvalidThreatTier);
        assert!(alert_threshold >= 1 && alert_threshold <= 5, EInvalidThreshold);

        // Acts
        registry.defense_policy = DefensePolicy {
            auto_lock_tier,
            alert_threshold,
            max_response_value,
            cooldown_epochs,
            last_action_epoch: registry.defense_policy.last_action_epoch,
        };

        // Effects (event)
        event::emit(DefensePolicyUpdated {
            registry_id: object::id(registry),
            auto_lock_tier,
            alert_threshold,
            updated_by: ctx.sender(),
        });
    }

    /// Report a threat against a tribe zone.
    /// Anyone can report — the system evaluates based on defense policy.
    /// If threat_tier >= auto_lock_tier, the gate auto-locks.
    public entry fun report_threat(
        registry: &mut TribeRegistry,
        zone_id: vector<u8>,
        threat_tier: u64,
        clock: &Clock,
        ctx: &mut TxContext,
    ) {
        // Checks
        assert!(!registry.paused, EPaused);
        assert!(threat_tier >= 1 && threat_tier <= 5, EInvalidThreatTier);

        // Determine if auto-lock triggers
        let should_lock = registry.defense_policy.auto_lock_tier > 0
            && threat_tier >= registry.defense_policy.auto_lock_tier;

        // Flag before effects — set gate_locked before emitting event
        if (should_lock && !registry.gate_locked) {
            registry.gate_locked = true;
            event::emit(GateLockChanged {
                registry_id: object::id(registry),
                locked: true,
                reason: b"auto_lock_threat_tier",
            });
        };

        registry.total_reports = registry.total_reports + 1;

        // Effects (event)
        event::emit(ThreatReport {
            zone_id,
            threat_tier,
            reporter: ctx.sender(),
            timestamp: clock::timestamp_ms(clock),
            triggered_auto_lock: should_lock,
        });
    }

    /// Configure gate access policy (whitelist/blacklist).
    /// Requires AdminCap for access control modification.
    public entry fun set_gate_policy(
        _admin: &AdminCap,
        registry: &mut TribeRegistry,
        whitelist: vector<address>,
        blacklist: vector<address>,
        auto_lock_tier: u64,
        ctx: &mut TxContext,
    ) {
        // Checks
        assert!(!registry.paused, EPaused);
        assert!(auto_lock_tier <= 5, EInvalidThreatTier);

        // Acts
        registry.gate_policy = GatePolicy {
            whitelist,
            blacklist,
            auto_lock_tier,
        };

        // Also sync auto_lock_tier to defense policy if gate policy overrides
        if (auto_lock_tier > 0) {
            registry.defense_policy.auto_lock_tier = auto_lock_tier;
        };

        // Effects (event)
        event::emit(GatePolicyUpdated {
            registry_id: object::id(registry),
            whitelist_count: vector::length(&whitelist),
            blacklist_count: vector::length(&blacklist),
            updated_by: ctx.sender(),
        });
    }

    /// Check if a traveler address is allowed through the gate.
    /// Returns true if access is granted.
    ///
    /// Logic:
    ///   1. If gate is locked (auto-lock from threat), deny all
    ///   2. If traveler is blacklisted, deny
    ///   3. If whitelist is non-empty, traveler must be on it
    ///   4. Otherwise, allow
    public fun check_gate_access(registry: &TribeRegistry, traveler: address): bool {
        // Gate locked = deny everyone
        if (registry.gate_locked) {
            return false
        };

        // Blacklist check
        let blacklist = &registry.gate_policy.blacklist;
        let bl_len = vector::length(blacklist);
        let mut i = 0;
        while (i < bl_len) {
            if (*vector::borrow(blacklist, i) == traveler) {
                return false
            };
            i = i + 1;
        };

        // Whitelist check — if whitelist is non-empty, must be on it
        let whitelist = &registry.gate_policy.whitelist;
        let wl_len = vector::length(whitelist);
        if (wl_len > 0) {
            let mut j = 0;
            let mut found = false;
            while (j < wl_len) {
                if (*vector::borrow(whitelist, j) == traveler) {
                    found = true;
                };
                j = j + 1;
            };
            return found
        };

        // No whitelist restriction, not blacklisted, gate not locked
        true
    }

    /// Manually unlock the gate. Requires AdminCap.
    public entry fun unlock_gate(
        _admin: &AdminCap,
        registry: &mut TribeRegistry,
    ) {
        registry.gate_locked = false;
        event::emit(GateLockChanged {
            registry_id: object::id(registry),
            locked: false,
            reason: b"manual_unlock",
        });
    }

    /// Emergency pause — freezes all warden operations.
    public entry fun pause(
        _admin: &AdminCap,
        registry: &mut TribeRegistry,
    ) {
        registry.paused = true;
    }

    /// Unpause warden operations.
    public entry fun unpause(
        _admin: &AdminCap,
        registry: &mut TribeRegistry,
    ) {
        registry.paused = false;
    }

    // =========================================================================
    // View Functions
    // =========================================================================

    /// Get the current defense policy auto-lock tier.
    public fun get_auto_lock_tier(registry: &TribeRegistry): u64 {
        registry.defense_policy.auto_lock_tier
    }

    /// Get total threat reports filed.
    public fun get_total_reports(registry: &TribeRegistry): u64 {
        registry.total_reports
    }

    /// Check if gate is currently locked.
    public fun is_gate_locked(registry: &TribeRegistry): bool {
        registry.gate_locked
    }

    /// Check if warden is paused.
    public fun is_paused(registry: &TribeRegistry): bool {
        registry.paused
    }

    /// Get the tribe ID.
    public fun get_tribe_id(registry: &TribeRegistry): vector<u8> {
        registry.tribe_id
    }
}

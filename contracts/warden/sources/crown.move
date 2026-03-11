/// Crown NFT Module — on-chain identity tokens for EVE Frontier players.
///
/// Crowns are soulbound-style NFTs representing a player's identity and
/// accumulated memories within the tribe. They can be transferred or burned
/// but not duplicated.
///
/// Security patterns:
///   - Only the Crown owner can transfer or burn
///   - Checks-then-acts on all entry functions
///   - Named error constants
module warden::crown {
    use sui::clock::Clock;
    use sui::event;
    use sui::transfer;
    use sui::tx_context::TxContext;

    // =========================================================================
    // Error Constants
    // =========================================================================

    const ENotCrownOwner: u64 = 100;
    const EEmptyCrownType: u64 = 101;

    // =========================================================================
    // Objects
    // =========================================================================

    /// Crown NFT — unique identity token for a tribe member.
    /// Contains the crown type (class/role), encoded memories, and mint timestamp.
    public struct Crown has key, store {
        id: UID,
        /// Crown classification (e.g., b"sovereign", b"warden", b"artisan", b"scout")
        crown_type: vector<u8>,
        /// Encoded memories — narrative history, achievements, or metadata
        memories: vector<u8>,
        /// Epoch timestamp (ms) when this Crown was woven (minted)
        weaved_at: u64,
        /// Original creator address
        weaver: address,
    }

    // =========================================================================
    // Events
    // =========================================================================

    /// Emitted when a new Crown is minted.
    public struct CrownWeaved has copy, drop {
        crown_id: ID,
        crown_type: vector<u8>,
        weaver: address,
        weaved_at: u64,
    }

    /// Emitted when a Crown is transferred.
    public struct CrownTransferred has copy, drop {
        crown_id: ID,
        from: address,
        to: address,
    }

    /// Emitted when a Crown is burned (destroyed).
    public struct CrownBurned has copy, drop {
        crown_id: ID,
        burned_by: address,
        crown_type: vector<u8>,
    }

    // =========================================================================
    // Entry Functions
    // =========================================================================

    /// Weave (mint) a new Crown NFT.
    /// The caller becomes the Crown's owner.
    public entry fun weave_crown(
        crown_type: vector<u8>,
        memories: vector<u8>,
        clock: &Clock,
        ctx: &mut TxContext,
    ) {
        // Checks
        assert!(vector::length(&crown_type) > 0, EEmptyCrownType);

        let weaver = ctx.sender();
        let timestamp = clock::timestamp_ms(clock);

        let crown = Crown {
            id: object::new(ctx),
            crown_type,
            memories,
            weaved_at: timestamp,
            weaver,
        };

        let crown_id = object::id(&crown);

        // Transfer to minter
        transfer::transfer(crown, weaver);

        // Effects (event)
        event::emit(CrownWeaved {
            crown_id,
            crown_type,
            weaver,
            weaved_at: timestamp,
        });
    }

    /// Transfer a Crown to another player.
    /// Caller must own the Crown (enforced by Sui's object ownership model —
    /// only the owner can pass an owned object as a transaction argument).
    public entry fun transfer_crown(
        crown: Crown,
        recipient: address,
        ctx: &mut TxContext,
    ) {
        let crown_id = object::id(&crown);
        let from = ctx.sender();

        // Effects (event before transfer consumes the ref context)
        event::emit(CrownTransferred {
            crown_id,
            from,
            to: recipient,
        });

        // Transfer ownership
        transfer::transfer(crown, recipient);
    }

    /// Burn (destroy) a Crown.
    /// Caller must own the Crown (enforced by Sui object ownership).
    public entry fun burn_crown(
        crown: Crown,
        ctx: &mut TxContext,
    ) {
        let crown_id = object::id(&crown);
        let crown_type = crown.crown_type;
        let burned_by = ctx.sender();

        // Effects (event)
        event::emit(CrownBurned {
            crown_id,
            burned_by,
            crown_type,
        });

        // Destroy the object — unpack all fields
        let Crown {
            id,
            crown_type: _,
            memories: _,
            weaved_at: _,
            weaver: _,
        } = crown;
        object::delete(id);
    }

    // =========================================================================
    // View Functions
    // =========================================================================

    /// Get the Crown type.
    public fun get_crown_type(crown: &Crown): vector<u8> {
        crown.crown_type
    }

    /// Get the Crown memories.
    public fun get_memories(crown: &Crown): vector<u8> {
        crown.memories
    }

    /// Get when the Crown was woven.
    public fun get_weaved_at(crown: &Crown): u64 {
        crown.weaved_at
    }

    /// Get the original weaver address.
    public fun get_weaver(crown: &Crown): address {
        crown.weaver
    }
}

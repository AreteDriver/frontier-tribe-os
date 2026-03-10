/// The Silk Road Protocol — Autonomous trade / escrow contracts.
/// Hardening: flag-before-transfer, no self-trade, explicit cancellation.
/// See docs/MOVE_HARDENING.md "The Silk Road Protocol (Trade Contracts)"
///
/// TODO: Implement business logic during hackathon Week 1-2.
module aegis_stack::silk_road {
    use sui::coin::{Self, Coin};
    use sui::sui::SUI;
    use sui::transfer;
    use sui::tx_context::TxContext;
    use aegis_stack::admin::{PauseState, is_paused};
    use aegis_stack::errors;

    // === Objects ===

    public struct TradeEscrow has key {
        id: UID,
        seller: address,
        buyer: address,
        price: u64,
        fulfilled: bool,
        cancelled: bool,
    }

    // === Entry Functions ===
    // Pattern: assert access → assert state → mutate flag → transfer assets

    /// Create a new trade escrow.
    /// Seller cannot be buyer (prevents wash trading).
    public entry fun create_trade(
        _pause: &PauseState,
        buyer: address,
        price: u64,
        ctx: &mut TxContext,
    ) {
        assert!(!is_paused(_pause), errors::E_PAUSED);
        assert!(price > 0, errors::E_INVALID_AMOUNT);
        assert!(ctx.sender() != buyer, errors::E_SELF_TRADE);

        let escrow = TradeEscrow {
            id: object::new(ctx),
            seller: ctx.sender(),
            buyer,
            price,
            fulfilled: false,
            cancelled: false,
        };
        transfer::share_object(escrow);
    }

    /// Fulfil a trade — buyer pays, assets transfer.
    /// Flag set BEFORE asset transfers (atomic abuse defense).
    public entry fun fulfil_trade(
        _pause: &PauseState,
        escrow: &mut TradeEscrow,
        payment: Coin<SUI>,
        ctx: &mut TxContext,
    ) {
        assert!(!is_paused(_pause), errors::E_PAUSED);
        assert!(ctx.sender() == escrow.buyer, errors::E_NOT_BUYER);
        assert!(!escrow.fulfilled, errors::E_ALREADY_FULFILLED);
        assert!(!escrow.cancelled, errors::E_ALREADY_CANCELLED);
        assert!(coin::value(&payment) >= escrow.price, errors::E_INSUFFICIENT_FUNDS);

        // Flag BEFORE transfers
        escrow.fulfilled = true;

        // TODO: Transfer escrowed asset to buyer
        // Transfer payment to seller
        transfer::public_transfer(payment, escrow.seller);
    }

    /// Cancel a trade — only seller (creator) can cancel, not buyer.
    public entry fun cancel_trade(
        escrow: &mut TradeEscrow,
        ctx: &mut TxContext,
    ) {
        assert!(ctx.sender() == escrow.seller, errors::E_NOT_SELLER);
        assert!(!escrow.fulfilled, errors::E_ALREADY_FULFILLED);
        assert!(!escrow.cancelled, errors::E_ALREADY_CANCELLED);

        // Flag BEFORE any refund
        escrow.cancelled = true;

        // TODO: Return escrowed asset to seller
    }
}

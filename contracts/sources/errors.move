/// Shared error constants across all Aegis contracts.
/// Named constants — never magic numbers.
module aegis_stack::errors {
    // === Access Control ===
    public const E_NOT_AUTHORIZED: u64 = 1;
    public const E_NOT_OWNER: u64 = 2;
    public const E_NOT_ADMIN: u64 = 3;

    // === State ===
    public const E_ALREADY_EXECUTED: u64 = 10;
    public const E_ALREADY_CANCELLED: u64 = 11;
    public const E_ALREADY_FULFILLED: u64 = 12;
    public const E_ALREADY_VOTED: u64 = 13;
    public const E_PAUSED: u64 = 14;

    // === Validation ===
    public const E_INSUFFICIENT_FUNDS: u64 = 20;
    public const E_INSUFFICIENT_VOTES: u64 = 21;
    public const E_INSUFFICIENT_STAKE: u64 = 22;
    public const E_EXCEEDS_LIMIT: u64 = 23;
    public const E_INVALID_AMOUNT: u64 = 24;

    // === Timing ===
    public const E_TOO_EARLY: u64 = 30;
    public const E_COOLDOWN_ACTIVE: u64 = 31;
    public const E_EXPIRED: u64 = 32;

    // === Trade ===
    public const E_NOT_BUYER: u64 = 40;
    public const E_NOT_SELLER: u64 = 41;
    public const E_SELF_TRADE: u64 = 42;
}

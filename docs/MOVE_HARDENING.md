# Move Contract Hardening Guide — Aegis Stack

## Why Move Is Different From Solidity

Before hardening, understand the model. Move's safety guarantees eliminate entire EVM attack classes:

| EVM Vulnerability | Move Status | Reason |
|---|---|---|
| Reentrancy | **Not possible** | No dynamic dispatch, no external calls mid-execution |
| Integer overflow | **Not possible** | Runtime abort on overflow by default |
| Uninitialized storage | **Not possible** | Compiler enforces initialization |
| Arbitrary DELEGATECALL | **Not possible** | No equivalent construct |

**What this means:** You're not fighting the same war as Solidity devs. Your threat model is about **object ownership, capability discipline, and access control logic** — not low-level memory exploits.

---

## Core Concepts You Must Internalize

### Objects and Ownership

Every resource on Sui is an **object** with an owner. Ownership types:

```move
// Owned by a single address — only that address can use it as input
transfer::transfer(obj, recipient);

// Shared — anyone can pass it as input to transactions
transfer::share_object(obj);

// Frozen — immutable, anyone can read, no one can mutate
transfer::freeze_object(obj);
```

**Critical rule:** Shared objects are your highest-risk surface. Any transaction can include a shared object as an argument. If your entry function doesn't verify the caller, anyone can call it.

### Capabilities (Caps)

The capability pattern is Move's primary access control mechanism:

```move
// Define a one-time-use admin capability
public struct AdminCap has key, store { id: UID }

// Mint it once at deployment
fun init(ctx: &mut TxContext) {
    transfer::transfer(AdminCap { id: object::new(ctx) }, ctx.sender());
}

// Require it as proof of authorization
public entry fun privileged_action(_cap: &AdminCap, ...) {
    // caller must own AdminCap to invoke this
}
```

If someone gains control of your `AdminCap` object, they own your protocol. Treat it like a private key.

---

## Hardening Patterns by Project

### The Sovereign (Governance)

Governance contracts are the highest-value target. A compromised governance system can drain or redirect everything else.

**Pattern: Two-step proposal execution with timelock**

```move
public struct Proposal has key {
    id: UID,
    action: vector<u8>,
    votes_for: u64,
    votes_against: u64,
    created_at: u64,
    executed: bool,
}

const TIMELOCK_EPOCHS: u64 = 2; // minimum epochs before execution
const E_TOO_EARLY: u64 = 1;
const E_ALREADY_EXECUTED: u64 = 2;
const E_INSUFFICIENT_VOTES: u64 = 3;

public entry fun execute_proposal(
    proposal: &mut Proposal,
    clock: &Clock,
    ctx: &mut TxContext
) {
    assert!(!proposal.executed, E_ALREADY_EXECUTED);
    assert!(
        clock::epoch(clock) >= proposal.created_at + TIMELOCK_EPOCHS,
        E_TOO_EARLY
    );
    assert!(proposal.votes_for > proposal.votes_against, E_INSUFFICIENT_VOTES);

    proposal.executed = true;
    // execute action...
}
```

**Why timelock matters:** Without it, a flash-vote attack can pass and execute a malicious proposal in a single epoch. Timelock forces the community to observe and respond.

**Checklist for Sovereign:**
- [ ] Proposal creation requires minimum stake / voting power
- [ ] Execution has timelock (minimum 2 epochs for hackathon, longer in production)
- [ ] `executed` flag set before side effects (prevents double-execution)
- [ ] Vote weights cannot be manipulated by re-depositing the same tokens

---

### The Silk Road Protocol (Trade Contracts)

Trade contracts handle asset transfers — the most direct path to fund loss.

**Pattern: Escrow with explicit cancellation**

```move
public struct TradeEscrow has key {
    id: UID,
    seller: address,
    buyer: address,
    asset_id: ID,
    price: u64,
    fulfilled: bool,
    cancelled: bool,
}

const E_NOT_BUYER: u64 = 1;
const E_NOT_SELLER: u64 = 2;
const E_ALREADY_FULFILLED: u64 = 3;
const E_ALREADY_CANCELLED: u64 = 4;

public entry fun fulfil_trade(
    escrow: &mut TradeEscrow,
    payment: Coin<SUI>,
    ctx: &mut TxContext
) {
    assert!(ctx.sender() == escrow.buyer, E_NOT_BUYER);
    assert!(!escrow.fulfilled, E_ALREADY_FULFILLED);
    assert!(!escrow.cancelled, E_ALREADY_CANCELLED);
    assert!(coin::value(&payment) >= escrow.price, E_INSUFFICIENT_PAYMENT);

    escrow.fulfilled = true;
    // transfer asset to buyer, payment to seller
}
```

**Atomic transaction abuse:** In Sui, a single transaction can call multiple functions atomically. An attacker could:
1. Create a trade offer
2. Fulfill it with a manipulated price object
3. Cancel it for refund

All in one transaction. Your `fulfilled` and `cancelled` flags being set before side effects is your primary defense.

**Checklist for Silk Road:**
- [ ] Escrow state flags set before asset transfers
- [ ] Price validated against actual coin value, not a parameter
- [ ] Seller cannot fulfil their own trade (prevents wash trading)
- [ ] Cancellation only available to trade creator, not fulfiller
- [ ] No unbounded loops over trade history (gas exhaustion vector)

---

### The Warden System (Autonomous Defense)

Autonomous defense means the contract can take action without direct human input. This is your most dangerous pattern.

**Rule: Automation should be constrained, not open-ended.**

```move
public struct WardenConfig has key {
    id: UID,
    owner: address,
    max_response_value: u64,     // cap on autonomous asset deployment
    cooldown_epochs: u64,         // minimum time between autonomous actions
    last_action_epoch: u64,
}

const E_NOT_OWNER: u64 = 1;
const E_COOLDOWN_ACTIVE: u64 = 2;
const E_EXCEEDS_LIMIT: u64 = 3;

public entry fun autonomous_response(
    config: &mut WardenConfig,
    response_value: u64,
    clock: &Clock,
    ctx: &mut TxContext
) {
    // Even autonomous actions need an authorized trigger
    assert!(ctx.sender() == config.owner, E_NOT_OWNER);
    assert!(
        clock::epoch(clock) >= config.last_action_epoch + config.cooldown_epochs,
        E_COOLDOWN_ACTIVE
    );
    assert!(response_value <= config.max_response_value, E_EXCEEDS_LIMIT);

    config.last_action_epoch = clock::epoch(clock);
    // execute defense response...
}
```

**Checklist for Warden:**
- [ ] All autonomous actions have a cap on value/scope
- [ ] Cooldown between actions prevents rapid drain
- [ ] Config mutation requires `AdminCap` — not just ownership address
- [ ] Emergency pause function exists and is tested

---

## Universal Hardening Rules (All Contracts)

### 1. Always Assert Before Acting

```move
// WRONG — acts then checks
fun withdraw(vault: &mut Vault, amount: u64, ctx: &mut TxContext) {
    let coin = coin::split(&mut vault.balance, amount, ctx);
    assert!(ctx.sender() == vault.owner, E_NOT_OWNER); // too late
    transfer::public_transfer(coin, ctx.sender());
}

// RIGHT — checks then acts
fun withdraw(vault: &mut Vault, amount: u64, ctx: &mut TxContext) {
    assert!(ctx.sender() == vault.owner, E_NOT_OWNER);
    assert!(coin::value(&vault.balance) >= amount, E_INSUFFICIENT_FUNDS);
    let coin = coin::split(&mut vault.balance, amount, ctx);
    transfer::public_transfer(coin, ctx.sender());
}
```

### 2. Use Named Error Constants

```move
// WRONG
assert!(ctx.sender() == admin, 1);

// RIGHT — readable in error output, searchable in code
const E_NOT_AUTHORIZED: u64 = 1;
const E_INSUFFICIENT_FUNDS: u64 = 2;
const E_ALREADY_EXECUTED: u64 = 3;

assert!(ctx.sender() == admin, E_NOT_AUTHORIZED);
```

### 3. Never Store Capabilities in Shared Objects

```move
// WRONG — AdminCap in a shared object is accessible to any transaction
public struct Protocol has key {
    id: UID,
    admin_cap: AdminCap, // anyone can try to extract this
}

// RIGHT — AdminCap transferred to deployer's address directly
fun init(ctx: &mut TxContext) {
    transfer::transfer(AdminCap { id: object::new(ctx) }, ctx.sender());
}
```

### 4. Test Adversarially

For every privileged function, write a test that calls it from an unauthorized address and asserts it aborts:

```move
#[test]
#[expected_failure(abort_code = E_NOT_AUTHORIZED)]
fun test_unauthorized_cannot_execute_proposal() {
    let attacker = @0xBAD;
    // ... setup ...
    execute_proposal(&mut proposal, &clock, &mut tx_context::dummy_with_sender(attacker));
}
```

---

## Pre-Submission Contract Audit Checklist

- [ ] Every `public entry fun` has an explicit access control assert
- [ ] State mutation flags set before asset transfers on all escrow/trade functions
- [ ] No `AdminCap` or equivalent stored in shared objects
- [ ] All error codes are named constants, not magic numbers
- [ ] Adversarial test exists for every privileged function
- [ ] No unbounded loops or dynamic-length iterations (gas exhaustion)
- [ ] Emergency pause or circuit breaker exists on high-value contracts
- [ ] `sui move test` passes with 100% of tests green
- [ ] Reviewed against: https://github.com/movebit/movescan-security-checklist

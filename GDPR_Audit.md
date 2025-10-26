# Third-Party Data Processor Compliance

All third-party services that process user data (e.g., Shopify, DeepL, payment processors) are reviewed for GDPR/CCPA compliance. Data processing agreements (DPAs) are in place where required. We periodically review these contracts and update our records to ensure ongoing compliance.

For a current list of third-party processors and their compliance status, contact <privacy@yoursaasapp.com>.

## GDPR/CCPA Data Collection Audit

## Overview

This document outlines the personal data collected by the Shopify SaaS app, including data types, collection points, purposes, legal basis, retention periods, and third-party involvement.

## Data Collection Points

### Backend Data Collection

| Component | Data Types | Purpose | Legal Basis | Retention | Third Parties |
|-----------|------------|---------|-------------|-----------|---------------|
| **User Model** (`my_app/models/user.py`) | Email address, hashed password, account status (active/inactive), timestamps (created, updated, last login) | User authentication and account management | Contract (account access), Legitimate interest (security) | Indefinite (until account deletion) | None |
| **Shopify User Model** (`my_app/models/shop.py`) | Shop domain, access token, email (optional), country, plan details, domain, trial end date, activity status, webhook version, usage counts, timestamps | Shopify integration and store management | Contract (Shopify API integration) | Indefinite (until store uninstall) | Shopify (store data) |
| **Audit Log Model** (`my_app/models/audit.py`) | User ID, shop ID, event details (JSON), IP address, user agent string, timestamps | Security monitoring and compliance logging | Legitimate interest (security), Legal obligation (GDPR Article 30) | 7 years (GDPR requirement for processing records) | None |
| **Session Model** (`my_app/models/session.py`) | User ID, shop ID, session token, IP address, user agent, activity status, timestamps | Session management and security | Legitimate interest (security) | Session duration + 30 days | None |
| **Authentication API** (`my_app/api/auth.py`) | Shop domain, OAuth state/nonce, access tokens | Shopify OAuth authentication | Contract (Shopify integration) | Tokens stored indefinitely, nonces temporary | Shopify |

### Frontend Data Collection

| Component | Data Types | Purpose | Legal Basis | Retention | Third Parties |
|-----------|------------|---------|-------------|-----------|---------------|
| **Local Storage** (`frontend/src/authContext.tsx`, `CookieBanner.tsx`) | Shop domain, host URL, cookie consent preferences | User session persistence and consent management | Consent (for cookies), Legitimate interest (session) | Until cleared or consent withdrawn | None |

### Third-Party Services

| Service | Data Types | Purpose | Legal Basis | Retention | Third Parties |
|---------|------------|---------|-------------|-----------|---------------|
| **DeepL Translation API** (`frontend/src/features/shop/components/LanguageTranslation.ts`) | Text content for translation (may include user-generated content) | Language translation for content generation | Consent (user-initiated), Contract (service provision) | Per DeepL's privacy policy (typically temporary) | DeepL GmbH |
| **Shopify API** | Store data, products, orders (accessed via tokens) | E-commerce integration | Contract (Shopify terms) | Per Shopify's policies | Shopify Inc. |

### Integrations (Placeholders)

- Amazon, Etsy, WooCommerce integrations exist but are currently empty/placeholder files.
- No active data collection from these services yet.

## Data Categories Summary

- **Identifiers**: Email, user ID, shop domain, session tokens
- **Contact Info**: Email, country
- **Technical Data**: IP addresses, user agents, timestamps, access tokens
- **Usage Data**: Login times, usage counts, audit events
- **Content Data**: User-generated text for translation

## Next Steps

1. Implement data access/deletion endpoints
2. Review and enhance data minimization
3. Add data retention policies
4. Audit third-party data sharing agreements
5. Prepare breach notification procedures

## Compliance Notes

- All data collection appears necessary for core functionality
- Consent mechanisms are in place for cookies
- Audit logging supports GDPR Article 30 requirements
- Need to add data subject rights implementation

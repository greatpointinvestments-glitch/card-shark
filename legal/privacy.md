# Privacy Policy

**Last updated: April 13, 2026**

This policy explains what we collect, why, and what we do with it.

## What We Collect

**Account data:**
- Username
- Email address
- Password (hashed with bcrypt — we never see your actual password)
- Subscription tier and Stripe customer/subscription IDs

**Usage data:**
- Portfolio contents (cards you track, your manual values)
- Price alerts you set
- Search history and daily usage counters (to enforce free-tier limits)

**Mobile device data (iOS / Android app):**
- Camera: Card Shark uses your device camera to scan and identify sports cards. Images are sent to our AI service for identification and are not stored unless you add the card to your collection.
- Photo library: Card Shark accesses your photo library so you can scan cards from saved photos. We only read images you explicitly select.
- Push notifications: We send push notifications for price alerts you set and trial/subscription reminders. You can disable notifications at any time in your device settings or in-app preferences.
- Device tokens: We store a Firebase Cloud Messaging token to deliver push notifications. Tokens are deleted when you log out or disable notifications.

**App Tracking Transparency (iOS):**
- Card Shark does **not** track you across other apps or websites. We do not use Apple's advertising identifier (IDFA). If iOS shows a tracking prompt, we request "Do Not Track" by default.

**Analytics:**
- Anonymous page-view data via PostHog or Plausible (no personally identifying info beyond user agent + IP)
- Basic error logs via Sentry (may include your username if an error occurs while you're logged in)

**Payment data:**
- We do **not** store credit card numbers. All payments are processed by Stripe. We only receive a customer ID and subscription status.

## What We Do With It

- Run the service (authenticate you, show your portfolio, send alerts)
- Bill you for Pro subscriptions
- Email you important account updates (trial ending, billing failures, major changes)
- Send product updates if you opt in
- Debug problems and improve the product
- Comply with law

## What We Don't Do

- We don't sell your data to anyone
- We don't share your email with advertisers
- We don't share your portfolio or watchlist with third parties
- We don't read or use your cards/prices for anyone other than you

## Cookies and Tracking

We use essential cookies to keep you logged in. Analytics cookies are used only if you consent. No behavioral ad tracking.

## Affiliate Links

When you click through to eBay, PWCC, COMC, or other marketplaces from Card Shark, those sites set their own cookies per their own privacy policies. We only know that a click occurred and if you completed a purchase (for commission purposes). We don't receive your shopping cart or personal info from those sites.

## Third Parties We Use

- **Stripe** — payment processing
- **eBay / PWCC / COMC / Fanatics Collect / Alt / Goldin** — marketplace data and affiliate links
- **Railway** — API hosting
- **Supabase** — database and image storage
- **Firebase Cloud Messaging** — push notification delivery (iOS and Android)
- **PostHog** or **Plausible** — anonymous analytics
- **Sentry** — error tracking
- **Resend** or **SendGrid** — transactional email

Each has their own privacy policy. We chose them for privacy posture.

## Your Rights

You can at any time:
- Log in and see / export your portfolio
- Delete your account (which deletes your stored data within 30 days)
- Email hello@cardsharkapp.com to request a copy of your data or ask questions

**EU / UK / California residents:** you have additional rights under GDPR / CCPA (access, deletion, portability, non-discrimination). Email hello@cardsharkapp.com to exercise them.

## Data Retention

- Active accounts: we keep your data while you're using the service.
- Closed accounts: deleted within 30 days except where law requires retention (e.g., Stripe payment records for 7 years).
- Backups: may persist up to 90 days in encrypted form.

## Children

Card Shark is not intended for anyone under 18. We do not knowingly collect data from children. If we learn we have, we delete it.

## Security

- Passwords hashed with bcrypt
- HTTPS in transit
- Access to production data limited to the founder
- Regular backups

No system is perfectly secure. If we suffer a breach affecting your data, we'll notify you within 72 hours.

## Changes

We'll post any changes here and email subscribers if changes are material.

## Contact

hello@cardsharkapp.com

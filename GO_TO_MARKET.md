# CardHawk — Go-to-Market Plan

**Version:** 1.0 (April 2026)
**Audience:** Sports card collectors, flippers, breakers, and LCS (local card shop) owners
**Positioning:** "The scanner, price tracker, and flip finder built for people who actually make money in the hobby."

---

## 1. Pre-Launch Checklist (Do Before Promoting)

- [x] Deploy to Streamlit Community Cloud
- [x] Register domain: `cardhawkapp.com`
- [x] Sign up for eBay Partner Network (application submitted Apr 20, awaiting Campaign ID)
- [x] Create Stripe Prices — monthly ($7.99), yearly ($59.99), lifetime ($149), plus 20%-off variants ($6.39/mo, $47.99/yr). Test mode configured.
- [x] Set up hello@cardhawkapp.com (Zoho Mail, active Apr 14)
- [x] GitHub repos: cardhawk (Streamlit) + cardhawk-api (FastAPI)
- [x] Pokemon card support added (Pokemon TCG API + TCGPlayer affiliate links)
- [ ] Add Plausible or PostHog for analytics (free tier fine to start)
- [ ] Write landing-page meta tags + OG image for link previews
- [ ] Create X (Twitter), TikTok, Instagram handles: @cardhawkapp
- [ ] Open a Discord server — two public channels (#general, #flips-of-the-day), one Pro-only channel (#flip-alerts)
- [ ] Record 10 short demo clips in one sitting (see TikTok calendar below)
- [ ] Switch Stripe to live mode + set up webhook endpoint
- [ ] Add EPN Campaign ID to secrets (when approved)
- [ ] DUNS number (in progress — additional docs submitted to D&B Apr 14)
- [ ] Apple Developer Program enrollment (after DUNS clears)
- [ ] Hire React Native developer for mobile app (post on Upwork, $8-12K)

---

## 2. Launch Week (Day 1-7)

**Goal:** 500 signups, 25 paying subscribers, 5 lifetime deals sold.

### Day 1 — Private Soft Launch
- Send personal DMs to 20 people Sam already knows in the hobby
- "Built this for myself, want 10 honest testers — free Pro, no strings"
- Collect feedback via Discord

### Day 2-3 — Creator Seeding
Send personalized emails to 10 big card YouTubers/TikTokers. Free lifetime Pro in exchange for an honest review. No demands.

Target list (rank by audience + alignment):
1. Geoff Wilson / Sports Card Investor
2. Card Cash / Slabstox / Blez
3. Probstein
4. Rookie Cards (YouTube)
5. The Sports Card Show (YouTube)
6. CardsHQ / Dr. James Beckett
7. Pull Luck (TikTok)
8. Card Collector 2 (TikTok — big audience, mainstream)
9. Vintage Breaks
10. Any local breaker in SE US (relationship play)

**Template email:**
> Subject: Built a tool that might save you 10 hours a week
>
> Hey [Name] — big fan of the channel. I built a card analyzer that scans cards, tracks portfolio value, and surfaces arbitrage flips across eBay. No sales pitch — just sending you a lifetime Pro account (normally $149) in case you find it useful. If you like it, I'd appreciate a shoutout. If you don't, no hard feelings.
>
> Sam

### Day 4 — Reddit Launch (The One-Shot)
Post to r/sportscards and r/baseballcards at 9am EST on a Saturday. Title:
> "I built a free card scanner + flip finder because I was tired of doing comp research by hand"

Rules:
- Lead with the pain, not the product
- Include 3 screenshots — scan demo, Flip Finder hits, portfolio dashboard
- Pin "Happy to answer questions" in the top comment
- Reply to every comment for 4 hours. Do NOT argue with skeptics.
- If mods delete it, DM them politely asking why — don't repost

### Day 5-6 — Product Hunt Launch
- Ship 12:01am PST Tuesday or Wednesday
- Hunter: find one with 1000+ followers, give them credit
- First 10 upvotes/comments lined up from DMs
- "Maker's comment" explains the Why

### Day 7 — Recap + Double Down
Look at signups by channel. Whatever worked, pour 3x more effort into it the following week.

---

## 3. TikTok Content Calendar (Ongoing)

**Target:** 3 posts per week. Batch record every Sunday.

### Format Mix
| Format | Frequency | Purpose |
|---|---|---|
| Scan-a-card demo (15s) | 1x/week | Top-of-funnel, viral potential |
| "Flip of the day" | 1x/week | Social proof, shows Pro value |
| Market take / hot take | 1x/week | Positions Sam as expert, drives trust |

### Concrete Video Ideas (First 30 Days)
1. **"I scanned this card from my grandfather's basement. Watch what it said."** — classic reveal format
2. **"This card just listed for $42. Last 10 sold for $78. Free money?"** — Flip Finder showcase
3. **"PSA 10 vs PSA 9 on this card — the math on whether to grade"** — Grading Calc demo
4. **"Everyone's buying Shohei. Here's what the data actually says."** — Market Movers screenshot + voiceover
5. **"I tracked $50k in cards for 6 months. Here's my portfolio return."** — Portfolio dashboard, big numbers
6. **"Why I sold my Victor Wembanyama rookie early"** — contrarian take, Sam's face on camera
7. **"5 cards that are about to moon (or I'm wrong and you should laugh at me)"** — accountability + engagement bait
8. **"Dealer tried to sell me this for $400. Here's what the comps said."** — confrontation format, high retention
9. **Duet responses to big card-TikTok accounts** — easy free reach
10. **Week in the life of a card flipper using CardHawk** — day-in-the-life format

### Hook Templates (Use These First 3 Seconds)
- "Most collectors don't know this one trick..."
- "I almost sent this card to PSA. Glad I didn't."
- "If you own this card, sell it now."
- "This is the worst card purchase I ever made."
- "POV: you're holding a $X card and don't know it."

### CTA Placement
- Never hard-sell in video
- Comment pinned: "Free card scanner at cardhawkapp.com — link in bio"
- Bio: "Scan any card → instant value → cardhawkapp.com"

---

## 4. Lead Magnet — Free Grading Tool (No Login)

**Problem:** People won't create an account until they trust you. So give them value for free, then capture.

**Build:** A public page at `cardhawkapp.com/grade` — no login. User uploads a card photo, gets back:
- Estimated raw value
- Estimated PSA 10 value
- "Worth grading?" yes/no with math

**Capture:** Gate the detailed report behind an email. "Enter your email to get the full grading recommendation + subgrade analysis."

**Flow:**
1. Scan → basic valuation shown for free
2. Email gate → full PSA EV breakdown
3. 3-email drip over 2 weeks:
   - Email 1 (day 0): Your report + "here's what most people miss about grading"
   - Email 2 (day 3): "5 flips I found this week using CardHawk Pro" (social proof)
   - Email 3 (day 7): "Try Pro free for 7 days — no card required"

**Expected conversion:** 2-5% of leads → trial → paid.

---

## 5. Reddit Strategy (Month 2+)

**Do not spam.** Reddit bans tools that post product links without participation.

### Rules
1. 10 helpful comments for every 1 self-promo mention
2. Never post a bare link. Always context-rich.
3. Engage in r/sportscards, r/baseballcards, r/footballcards, r/basketballcards
4. Sam should post under his real account, not a burner

### Types of Helpful Posts
- Weekly "Market Movers" recap with data from CardHawk (cite the tool once)
- "How I flipped $X this month using [manual method]" — then in comments: "I used CardHawk to speed up Step 3"
- Help threads: "How do I know if this is a good price?" → answer with actual comp data
- AMA after 6 months: "I built CardHawk. Ask me anything."

---

## 6. Discord Community

**Structure:**
- `#welcome` — onboarding
- `#general` — free tier chat
- `#grading-advice` — public help channel (gold for SEO + discovery)
- `#portfolio-wins` — users brag about flips (social proof engine)
- `#flip-alerts` **Pro only** — Sam posts 2-3 flips/day with direct eBay affiliate links
- `#feature-requests` — roadmap input

**Sam's job:** 20 minutes/day posting flip alerts. Rotate breaking-news hot takes. Once community hits 500 members, hire a Discord mod for $100/mo.

**Retention hook:** Leaving Pro = losing access to `#flip-alerts`. Users stay subscribed just for that channel.

---

## 7. Creator Partnerships — The Real Long Game

Every 3 months, repeat the free-Pro seeding list. Not the same people — new ones. Especially target creators who are **under 100k followers but growing fast**. They care more, have more loyal audiences, and convert better than mega-creators.

**Affiliate program for creators** (Month 3+):
- 30% lifetime recurring on referred Pro subs
- Custom coupon code per creator (CODE_GEOFF, CODE_BLEZ, etc.)
- Dashboard showing their earnings (phase 2 — spreadsheet until then)

---

## 8. Card Show Playbook (Offline)

**The National** (July, Chicago) — set up free card scanner demos at a shared booth. Collect emails in exchange for a 1-year Pro trial.

**Regional shows** (Atlanta, Nashville, Charlotte — Sam's territory):
- Print 500 CardHawk business cards
- Back of card: QR code → `cardhawkapp.com/show` → free 1-year Pro for attendees
- Set up at a dealer's booth (barter: free lifetime Pro for them in exchange for table space)

**Goal per show:** 100 signups, 15 trial-to-paid conversions. Paid conversions = break-even on travel inside 6 months.

---

## 9. Metrics to Track

| Metric | Target (Month 1) | Target (Month 6) |
|---|---|---|
| Signups | 500 | 10,000 |
| Trial-to-paid conversion | 8% | 15% |
| Monthly Recurring Revenue | $300 | $6,000 |
| Lifetime deal sold | 15 | 100 (capped) |
| Churn (monthly) | <5% | <3% |
| Affiliate revenue (eBay + others) | $50 | $2,000 |
| Discord members | 100 | 2,500 |
| TikTok followers | 500 | 25,000 |

**Dashboard:** PostHog + Stripe + a Google Sheet updated weekly. Don't over-engineer tracking in month 1 — just write the numbers down every Monday.

---

## 10. 90-Day Priorities (In Order)

1. **Weeks 1-2:** Ship the lead magnet (`/grade`). Nothing else matters until the free value is public.
2. **Weeks 3-4:** TikTok daily posting. Find the format that hits first.
3. **Weeks 5-8:** Creator seeding + Reddit + Product Hunt.
4. **Weeks 9-12:** Launch Discord Pro-alerts channel. Start creator affiliate program.
5. **Month 4+:** The National + regional card shows.

---

## 11. Budget (First 90 Days)

| Line Item | Cost |
|---|---|
| Domain + hosting | $15/mo |
| Stripe fees (on ~$500 MRR) | ~$20/mo |
| Twilio (SMS alerts add-on, when built) | $10/mo base |
| PostHog / Plausible analytics | Free tier |
| Lifetime free Pro seeded to 10 creators | $0 cash cost |
| Card show table share | $200-500 (The National only) |
| **Total cash out** | **~$250 over 90 days** |

This is a cash-efficient launch. Biggest investment is Sam's time.

---

## 12. What NOT to Do

- **No paid ads in month 1.** Dollar-for-dollar losers until the funnel is proven.
- **No SEO blog posts** until organic channels (Reddit, TikTok) are generating baseline traffic. SEO takes 6 months to pay off.
- **Do not launch on Twitter/X first.** Card Twitter is small and cliquish. TikTok scales.
- **Do not build an iOS app before $5k MRR.** Web works fine until then.
- **Do not lower the price.** Use the abandoned-checkout coupon instead — preserves anchor.

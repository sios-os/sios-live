"""Business & Operations K3 - 21 specialties in 5 batches (5+4+4+4+4)."""

BUSINESS_K3_BATCH1: dict[str, list[dict]] = {
    "business_accounting_bookkeeping": [
        {"title": "Financial Accounting Standards Reference", "content": """# Financial Accounting Standards Reference

## GAAP (US)
- FASB (Financial Accounting Standards Board)
- Accounting Standards Codification (ASC)
- SEC oversees public companies

## IFRS (International)
- IASB (International Accounting Standards Board)
- Used in 140+ countries
- Convergence with GAAP ongoing

## Key Principles
- Accrual basis: record when earned/incurred
- Going concern: assume business continues
- Matching: expenses with related revenue
- Revenue recognition: when performance obligation satisfied (ASC 606)
- Conservatism: anticipate losses, not gains
- Consistency: same methods period to period
- Materiality: significant items matter
- Full disclosure: all material information

## Balance Sheet

### Assets
- Current: cash, receivables, inventory, prepaid (<= 1 year)
- Non-current: PP&E, intangibles, investments (> 1 year)
- Depreciation: allocate cost over useful life
  - Straight-line: (cost - salvage) / life
  - Declining balance: accelerated
  - Units of production: usage-based
- Inventory methods: FIFO, LIFO, weighted average

### Liabilities
- Current: payables, accrued, short-term debt
- Long-term: bonds, mortgages, deferred tax

### Equity
- Common stock: par value
- Additional paid-in capital: above par
- Retained earnings: accumulated profit
- Treasury stock: repurchased shares

## Income Statement
- Revenue: sales
- COGS: direct costs
- Gross profit: revenue - COGS
- Operating expenses: SG&A, R&D
- Operating income: gross - operating
- Net income: after interest, taxes

## Cash Flow Statement
### Operating
- Net income adjusted for non-cash items
- Changes in working capital

### Investing
- PP&E purchases/sales
- Acquisitions, investments

### Financing
- Debt issued/repaid
- Stock issued/repurchased
- Dividends paid

## Key Ratios
### Liquidity
- Current: current assets / current liabilities
- Quick: (current - inventory) / current liabilities
- Cash: cash / current liabilities

### Profitability
- Gross margin: gross profit / revenue
- Operating margin: operating income / revenue
- Net margin: net income / revenue
- ROA: net income / total assets
- ROE: net income / equity

### Leverage
- Debt-to-equity: total debt / equity
- Debt-to-assets: total debt / total assets
- Interest coverage: EBIT / interest

### Efficiency
- Inventory turnover: COGS / inventory
- Receivables turnover: revenue / receivables
- Asset turnover: revenue / total assets

## Common Pitfalls
- Confusing cash flow with profit
- Not distinguishing accrual from cash
- Ignoring off-balance-sheet items
- Treating depreciation as cash expense
- Not reconciling accounts
""", "tags": ["accounting", "GAAP", "IFRS", "financial statements", "ratios", "reference"]}
    ],
    "business_corporate_finance": [
        {"title": "Capital Budgeting and Valuation Reference", "content": """# Capital Budgeting and Valuation Reference

## Time Value of Money
- Future value: FV = PV (1+r)^n
- Present value: PV = FV / (1+r)^n
- Annuity: PV = PMT * [1 - (1+r)^-n] / r
- Perpetuity: PV = PMT / r
- Effective rate: (1 + r/n)^n - 1

## Capital Budgeting Methods

### Net Present Value (NPV)
- NPV = sum CF_t / (1+r)^t - Initial
- Accept if NPV > 0
- Considers time value and all cash flows
- Best method theoretically

### Internal Rate of Return (IRR)
- Rate where NPV = 0
- Accept if IRR > cost of capital
- Problems: multiple IRRs, scale, reinvestment assumption

### Payback Period
- Time to recover initial investment
- Simple: ignore time value
- Discounted: with time value
- Ignores cash flows after payback

### Profitability Index
- PI = PV of cash flows / initial
- Accept if PI > 1

## Cost of Capital

### WACC
- WACC = (E/V) * Re + (D/V) * Rd * (1-T)
- E: equity, D: debt, V: E+D
- Re: cost of equity, Rd: cost of debt
- T: tax rate

### Cost of Equity (CAPM)
- Re = Rf + Beta * (Rm - Rf)
- Rf: risk-free rate
- Beta: stock sensitivity to market
- Rm: market return
- (Rm - Rf): market risk premium

### Cost of Debt
- Rd = yield to maturity on debt
- After-tax: Rd * (1 - T)

## Valuation Methods

### DCF (Discounted Cash Flow)
- Value = sum FCF_t / (1+WACC)^t + Terminal Value
- Free cash flow: EBIT(1-T) + D - CAPEX - delta NWC
- Terminal value: FCF * (1+g) / (WACC - g) (Gordon growth)

### Multiples
- P/E: price / earnings
- EV/EBITDA: enterprise value / EBITDA
- P/B: price / book
- P/S: price / sales
- Comparable company analysis

### Asset-Based
- Net asset value: assets - liabilities
- Liquidation value: if sold off

## Capital Structure
- Trade-off theory: balance tax shield vs bankruptcy cost
- Pecking order: internal -> debt -> equity
- Modigliani-Miller: capital structure irrelevant (no taxes)
- With taxes: debt beneficial (tax shield)
- Optimal: where marginal benefit = marginal cost

## Dividend Policy
- Residual: pay what's left after investment
- Stable: maintain steady dividend
- Lintner model: gradual adjustment
- Signaling: dividend changes signal information
- Clientele effect: investors prefer certain policies

## Common Pitfalls
- Using wrong discount rate
- Ignoring working capital changes
- Overly optimistic projections
- Not considering terminal value carefully
- Confusing enterprise value with equity value
""", "tags": ["corporate finance", "NPV", "WACC", "CAPM", "DCF", "valuation", "reference"]}
    ],
    "business_investment_analysis": [
        {"title": "Portfolio Theory and Asset Valuation Reference", "content": """# Portfolio Theory and Asset Valuation Reference

## Modern Portfolio Theory (Markowitz)
- Diversification reduces risk
- Efficient frontier: max return for given risk
- Risk: standard deviation of returns
- Return: expected return
- Correlation: how assets move together
- Lower correlation -> better diversification

## Capital Asset Pricing Model (CAPM)
- E(R) = Rf + Beta * (Rm - Rf)
- Beta = Cov(Ri, Rm) / Var(Rm)
- Beta = 1: market risk
- Beta > 1: more volatile than market
- Beta < 1: less volatile
- Security market line: plot of CAPM

## Efficient Market Hypothesis (EMH)
- Weak: prices reflect past prices
- Semi-strong: prices reflect all public info
- Strong: prices reflect all info
- Implications: cannot consistently beat market
- Critique: anomalies exist (momentum, value, size)

## Stock Valuation

### DDM (Dividend Discount Model)
- P = D1 / (r - g)
- D1: next dividend
- r: required return
- g: dividend growth
- Two-stage: high growth then stable

### FCFE (Free Cash Flow to Equity)
- Value = sum FCFE_t / (1+r)^t
- FCFE = FCF - debt repayment + new debt

### Multiples
- P/E = Price / EPS
- PEG = P/E / growth rate
- EV/EBITDA: enterprise value
- Comparable: similar companies

## Bond Valuation
- Price = sum C/(1+r)^t + F/(1+r)^n
- C: coupon, F: face value, r: yield
- Yield to maturity: total return if held
- Duration: price sensitivity to rates
- Convexity: curvature of price-yield
- Credit risk: default probability

## Risk Measures
- Standard deviation: total risk
- Beta: market risk
- VaR (Value at Risk): max loss at confidence level
- Sharpe ratio: (R - Rf) / sigma
- Treynor ratio: (R - Rf) / Beta
- Jensen's alpha: excess return vs CAPM
- Sortino ratio: downside deviation only

## Portfolio Management
- Strategic allocation: long-term targets
- Tactical allocation: short-term adjustments
- Rebalancing: restore target weights
- Active: try to beat benchmark
- Passive: match benchmark (index funds)
- Factor investing: value, size, momentum, quality

## Behavioral Finance
- Loss aversion: losses hurt 2x gains please
- Overconfidence: overestimate skill
- Herding: follow crowd
- Anchoring: fixate on reference
- Disposition effect: sell winners, hold losers
- Mental accounting: categorize money

## Common Pitfalls
- Assuming past performance predicts future
- Underestimating risk
- Not diversifying enough
- Chasing performance
- Confusing systematic with unsystematic risk
- Ignoring costs and taxes
""", "tags": ["investment analysis", "portfolio theory", "CAPM", "valuation", "bonds", "reference"]}
    ],
    "business_entrepreneurship": [
        {"title": "Startup Methods and Funding Reference", "content": """# Startup Methods and Funding Reference

## Lean Startup (Ries)
- Build-Measure-Learn loop
- Minimum viable product (MVP)
- Validated learning: test hypotheses
- Pivot or persevere: change or continue
- Innovation accounting: track progress

## Business Model Canvas (Osterwalder)
1. Customer segments: who
2. Value propositions: what value
3. Channels: how to reach
4. Customer relationships: how to interact
5. Revenue streams: how to earn
6. Key resources: what's needed
7. Key activities: what to do
8. Key partnerships: who helps
9. Cost structure: what it costs

## Funding Stages

### Pre-seed
- Founders, friends, family
- $10K-$100K
- Build prototype, validate idea

### Seed
- Angel investors, accelerators
- $100K-$2M
- Product-market fit

### Series A
- Venture capital
- $2M-$15M
- Scale proven model

### Series B, C, D+
- Growth equity
- $10M-$100M+
- Expansion

### Exit
- IPO: public offering
- Acquisition: bought by larger company
- Merger: combine with another

## Investors

### Angel Investors
- Individual, own money
- Early stage
- $25K-$500K typical
- Syndicates: groups

### Venture Capital
- Professional funds
- Limited partners provide capital
- General partners invest
- Equity stake: 15-30%
- Board seats, guidance
- Expect 10x return on winners

### Accelerators
- Y Combinator, Techstars, 500 Startups
- 3-6 month programs
- Mentorship, small investment
- Demo day: pitch to investors

### Crowdfunding
- Kickstarter, Indiegogo: rewards-based
- Republic, SeedInvest: equity
- Patreon: subscription
- Regulation CF: small investors

## Key Metrics

### SaaS
- MRR: monthly recurring revenue
- ARR: annual recurring revenue
- Churn: customer loss rate
- CAC: customer acquisition cost
- LTV: lifetime value
- LTV/CAC: should be > 3
- Burn rate: monthly cash consumption
- Runway: months until cash out

### Growth
- Viral coefficient: K = referrals per user
- K > 1: viral growth
- Cohort analysis: groups over time
- Funnel: awareness -> interest -> trial -> purchase

## Legal Structure
- Sole proprietorship: simplest, personal liability
- Partnership: shared ownership
- LLC: limited liability, flexible
- C-Corp: stock, double taxation (US)
- S-Corp: pass-through taxation
- Delaware incorporation: common for startups

## Common Pitfalls
- Building before validating
- Premature scaling
- Running out of cash
- Co-founder conflicts
- Not understanding customer
- Ignoring legal and tax
- Over-valuing in early rounds
""", "tags": ["entrepreneurship", "lean startup", "funding", "VC", "SaaS metrics", "reference"]}
    ],
    "business_business_strategy": [
        {"title": "Strategic Analysis Frameworks Reference", "content": """# Strategic Analysis Frameworks Reference

## Porter's Five Forces
1. Threat of new entrants: barriers to entry
   - Economies of scale
   - Capital requirements
   - Switching costs
   - Brand identity
   - Distribution access
   - Government policy
2. Bargaining power of buyers
   - Concentration vs industry
   - Switching costs
   - Product importance
   - Price sensitivity
3. Bargaining power of suppliers
   - Concentration
   - Switching costs
   - Substitute inputs
   - Importance of industry to supplier
4. Threat of substitutes
   - Price-performance tradeoff
   - Switching costs
5. Rivalry among competitors
   - Industry growth rate
   - Number and size of competitors
   - Fixed costs
   - Exit barriers
   - Product differentiation

## Porter's Generic Strategies
- Cost leadership: lowest cost
- Differentiation: unique value
- Focus: niche (cost or differentiation)
- Stuck in middle: no clear strategy

## Value Chain (Porter)
- Primary: inbound logistics, operations, outbound logistics, marketing, service
- Support: procurement, technology, HR, infrastructure
- Each activity can add value or reduce cost
- Competitive advantage from superior activities or linkages

## VRIO Framework
- Value: does it exploit opportunity or neutralize threat?
- Rarity: do others have it?
- Inimitability: hard to copy?
- Organization: structured to exploit?
- If all yes: sustained competitive advantage

## SWOT Analysis
- Strengths: internal positive
- Weaknesses: internal negative
- Opportunities: external positive
- Threats: external negative
- TOWS: combine internal and external for strategy

## PESTEL
- Political: government, policy
- Economic: growth, inflation, rates
- Social: demographics, culture
- Technological: innovation, disruption
- Environmental: sustainability, climate
- Legal: regulations, laws

## BCG Matrix
- Stars: high growth, high share
- Cash cows: low growth, high share
- Question marks: high growth, low share
- Dogs: low growth, low share
- Strategy: invest stars, milk cows, decide on question marks, divest dogs

## Ansoff Matrix
- Market penetration: existing product, existing market
- Product development: new product, existing market
- Market development: existing product, new market
- Diversification: new product, new market

## Blue Ocean Strategy (Kim & Mauborgne)
- Red ocean: compete in existing market
- Blue ocean: create uncontested market
- Value innovation: simultaneously pursue differentiation and low cost
- Eliminate-reduce-raise-create grid

## Resource-Based View (RBV)
- Resources: assets, capabilities
- Heterogeneous: firms differ
- Immobile: resources don't move easily
- Sustained advantage from VRIN resources
- Dynamic capabilities: ability to adapt (Teece)

## Common Pitfalls
- Using frameworks mechanically
- Ignoring industry context
- Confusing strategy with goals
- Not linking analysis to action
- Over-reliance on one framework
- Ignoring implementation challenges
""", "tags": ["business strategy", "Porter", "five forces", "SWOT", "VRIO", "reference"]}
    ],
}

BUSINESS_K3_BATCH2: dict[str, list[dict]] = {
    "business_operations_management": [
        {"title": "Lean, Six Sigma, and Quality Reference", "content": """# Lean, Six Sigma, and Quality Reference

## Lean

### Principles
- Value: define from customer perspective
- Value stream: map all activities
- Flow: smooth, no interruptions
- Pull: produce on demand
- Perfection: continuous improvement

### Waste (7+1 Muda)
1. Overproduction: making too much
2. Waiting: idle time
3. Transport: unnecessary movement
4. Over-processing: more than needed
5. Inventory: excess stock
6. Motion: unnecessary human movement
7. Defects: errors and rework
8. Unused talent: not using people's skills

### Tools
- 5S: sort, set in order, shine, standardize, sustain
- Kanban: visual workflow control
- Just-in-time (JIT): produce when needed
- Poka-yoke: mistake-proofing
- Kaizen: continuous improvement
- Value stream mapping: visualize flow
- Gemba walk: go to where work happens

## Six Sigma

### DMAIC (improve existing)
- Define: problem, goals, customers
- Measure: current performance
- Analyze: root causes
- Improve: implement solutions
- Control: sustain gains

### DMADV (new design)
- Define: project goals
- Measure: customer needs
- Analyze: design options
- Design: develop solution
- Verify: validate

### Statistical Basis
- Six Sigma: 3.4 defects per million
- Standard deviation: sigma
- Process capability: Cp, Cpk
- Control charts: monitor stability
- Common vs special cause variation

### Roles
- White/Yellow Belt: basic
- Green Belt: project leader
- Black Belt: full-time, expert
- Master Black Belt: trainer
- Champion: sponsor

## Total Quality Management (TQM)
- Customer focus
- Employee involvement
- Process-centered
- Integrated system
- Strategic and systematic approach
- Continuous improvement
- Fact-based decision making
- Communications

## ISO 9001
- Quality management standard
- Process approach
- Plan-Do-Check-Act cycle
- Documentation requirements
- Certification by third party
- Continuous improvement

## Quality Tools
- 7 Basic: fishbone, check sheet, control chart, histogram, Pareto, scatter, flowchart
- 7 Management: affinity, tree, matrix, relations, arrow, PDPC, matrix data
- Root cause analysis: 5 whys, fishbone
- Pareto: 80/20 rule
- FMEA: failure mode and effects analysis

## Process Improvement
- PDCA: Plan-Do-Check-Act (Deming)
- DMAIC: Six Sigma
- A3: Toyota problem-solving
- Root cause: find underlying cause
- Benchmarking: compare to best
- Statistical process control (SPC)

## Common Pitfalls
- Implementing tools without culture
- Focusing on tools, not people
- Not involving frontline workers
- Treating Lean as cost-cutting
- Not sustaining improvements
- Confusing efficiency with effectiveness
""", "tags": ["operations management", "lean", "six sigma", "quality", "DMAIC", "reference"]}
    ],
    "business_marketing_advertising": [
        {"title": "Digital Marketing and Brand Strategy Reference", "content": """# Digital Marketing and Brand Strategy Reference

## Digital Marketing Channels

### Search
- SEO: organic search ranking
  - On-page: content, keywords, meta
  - Off-page: backlinks, social signals
  - Technical: site speed, mobile, schema
- SEM: paid search (Google Ads)
  - PPC: pay per click
  - CPC: cost per click
  - Quality score: ad relevance
  - Landing page: where click goes

### Social Media
- Organic: posts, engagement
- Paid: sponsored content, ads
- Platforms: Facebook, Instagram, LinkedIn, TikTok, X
- Influencer: paid endorsements
- Community management: responding

### Content Marketing
- Blog posts, articles
- Video: YouTube, TikTok
- Podcasts
- Email newsletters
- Lead magnets: free content for email
- Hub and spoke: central content with derivatives

### Email
- List building: subscribers
- Segmentation: targeted groups
- Automation: triggered sequences
- A/B testing: subject lines, content
- Metrics: open rate, click rate, conversion

## Marketing Funnel
- AIDA: Attention, Interest, Desire, Action
- TOFU: top of funnel (awareness)
- MOFU: middle (consideration)
- BOFU: bottom (decision)
- Flywheel (HubSpot): attract, engage, delight

## Metrics

### Acquisition
- CAC: customer acquisition cost
- CTR: click-through rate
- CPL: cost per lead
- CPA: cost per acquisition

### Engagement
- Bounce rate: leave without action
- Time on page
- Pages per session
- Social engagement: likes, shares, comments

### Conversion
- Conversion rate: visitors who act
- Cart abandonment: % leaving cart
- Micro-conversions: email signups, downloads

### Retention
- Churn rate: customers lost
- Retention rate: customers kept
- LTV: lifetime value
- NPS: net promoter score
- Repeat purchase rate

## Brand Strategy

### Brand Elements
- Name: memorable, protectable
- Logo: visual identity
- Tagline: short promise
- Colors: emotional association
- Voice: personality in communication

### Brand Positioning
- Category: what market
- Target: who
- Benefit: what value
- Reason to believe: why trust
- Frame of reference: compared to what

### Brand Architecture
- Monolithic: one brand (Virgin)
- Endorsed: parent + sub (Marriott Courtyard)
- Pluralistic: separate brands (P&G)

### Brand Equity (Keller)
- Salience: awareness
- Performance and imagery: associations
- Judgments and feelings: evaluation
- Resonance: loyalty

## Marketing Analytics
- Attribution: which channel gets credit
  - First touch, last touch, multi-touch
- MMM: marketing mix modeling
- Incrementality: what would happen without
- ROI: return on investment
- ROAS: return on ad spend

## Common Pitfalls
- Focusing on vanity metrics
- Not testing and iterating
- Ignoring customer lifetime value
- Over-spending on acquisition vs retention
- Not aligning marketing with sales
- Ignoring brand for performance
""", "tags": ["marketing", "digital marketing", "SEO", "brand", "analytics", "reference"]}
    ],
    "business_market_research": [
        {"title": "Research Methods and Data Analysis Reference", "content": """# Market Research Methods and Data Analysis Reference

## Research Design

### Exploratory
- Understand problem
- Qualitative: interviews, focus groups
- When: little known about topic

### Descriptive
- Describe characteristics
- Quantitative: surveys, observation
- When: problem defined

### Causal
- Test cause and effect
- Experiments: A/B, controlled
- When: need to prove relationship

## Qualitative Methods

### Focus Groups
- 6-10 participants
- Moderator guides discussion
- 1-2 hours
- Rich insights, not generalizable

### In-depth Interviews
- One-on-one
- 30-90 minutes
- Probing, flexible
- Sensitive topics

### Ethnography
- Observe in natural setting
- Hours to months
- Contextual understanding
- Cultural insights

### Projective Techniques
- Word association
- Sentence completion
- Picture interpretation
- Role play
- Uncover unconscious motivations

## Quantitative Methods

### Surveys
- Sample: subset of population
- Sampling: random, stratified, quota
- Sample size: margin of error, confidence
- Question types: open, closed, Likert, semantic differential
- Bias: leading questions, social desirability

### Experiments
- A/B testing: compare two versions
- Control group: no treatment
- Random assignment: equal chance
- Internal validity: causation
- External validity: generalization

### Observation
- Direct: watching behavior
- Indirect: traces, archives
- Mystery shopper: undercover
- Eye tracking: gaze patterns

## Secondary Research
- Industry reports: Nielsen, Kantar, Mintel
- Government: census, BLS, trade data
- Academic: peer-reviewed studies
- Internal: CRM, sales data, web analytics
- Syndicated: shared data services

## Data Analysis

### Descriptive
- Mean, median, mode
- Standard deviation, variance
- Frequencies, cross-tabs
- Visualization: charts, graphs

### Inferential
- Hypothesis testing: t-test, chi-square, ANOVA
- Correlation: relationship strength
- Regression: predict from variables
- Factor analysis: identify underlying dimensions
- Cluster analysis: group similar cases
- Conjoint analysis: preference for attributes

### Segmentation
- Demographic: age, gender, income
- Geographic: location
- Psychographic: values, lifestyle
- Behavioral: usage, loyalty
- Personas: representative profiles

## Common Pitfalls
- Non-representative samples
- Leading or biased questions
- Confusing correlation with causation
- Over-generalizing from qualitative
- Not pre-testing instruments
- Ignoring non-response bias
- Not defining research objectives clearly
""", "tags": ["market research", "surveys", "qualitative", "quantitative", "segmentation", "reference"]}
    ],
    "business_sales": [
        {"title": "Sales Methods and Pipeline Management Reference", "content": """# Sales Methods and Pipeline Management Reference

## Sales Methodologies

### SPIN Selling (Rackham)
- Situation: understand context
- Problem: identify pain points
- Implication: consequences of problem
- Need-payoff: value of solution
- Works for B2B, complex sales

### Challenger Sale (Dixon & Adamson)
- Teach: new perspective
- Tailor: to customer
- Take control: of conversation
- Profiles: relationship builder, hard worker, lone wolf, reactive problem solver, challenger
- Challengers outperform

### Solution Selling
- Focus on problem, not product
- Diagnose before prescribing
- Build consensus
- ROI-focused

### Consultative Selling
- Advisor role
- Ask, listen, recommend
- Long-term relationship
- Trust-based

## Sales Process
1. Prospecting: find leads
2. Qualifying: determine fit
3. Needs analysis: understand requirements
4. Presentation: propose solution
5. Objection handling: address concerns
6. Closing: get commitment
7. Follow-up: ensure satisfaction
8. Account management: grow relationship

## Qualification Frameworks

### BANT
- Budget: can they afford?
- Authority: can they decide?
- Need: do they have problem?
- Timing: when will they buy?

### MEDDIC
- Metrics: what to improve
- Economic buyer: who controls budget
- Decision criteria: requirements
- Decision process: how decision made
- Identify pain: problem to solve
- Champion: internal advocate

## Pipeline Management
- Stages: lead -> qualified -> proposal -> negotiation -> close
- Conversion rate: stage to stage
- Velocity: time through pipeline
- Forecast: predicted revenue
- Coverage: pipeline / quota

## Sales Metrics
- Quota: target
- Attainment: % of quota
- Win rate: won / total opportunities
- Average deal size
- Sales cycle: time to close
- CAC: cost to acquire
- LTV: lifetime value
- LTV/CAC: should be > 3

## Account Management
- Land and expand: initial sale then growth
- Upsell: more of same
- Cross-sell: different products
- Renewal: continue contract
- QBR: quarterly business review
- Customer success: ensure value realized

## Sales Enablement
- Content: decks, case studies, demos
- Training: skills, product knowledge
- Tools: CRM, sales engagement, intelligence
- Coaching: manager development
- Onboarding: new hire ramp

## Common Pitfalls
- Pitching before understanding
- Not qualifying properly
- Ignoring decision process
- Over-promising, under-delivering
- Not following up
- Focusing on close, not relationship
- Not using CRM effectively
""", "tags": ["sales", "SPIN", "Challenger", "pipeline", "BANT", "MEDDIC", "reference"]}
    ],
}

BUSINESS_K3_BATCH3: dict[str, list[dict]] = {
    "business_ecommerce": [
        {"title": "E-commerce Platforms and Optimization Reference", "content": """# E-commerce Platforms and Optimization Reference

## Platform Types

### Hosted
- Shopify: easiest, monthly fee
- BigCommerce: scalable
- Wix: simple, design-focused
- Squarespace: design-focused

### Self-hosted
- WooCommerce (WordPress): flexible, open source
- Magento: enterprise, complex
- PrestaShop: open source

### Marketplace
- Amazon: largest
- eBay: auction and fixed
- Etsy: handmade, vintage
- Walmart Marketplace

### Custom
- Built from scratch
- Maximum flexibility
- Higher development cost

## Site Architecture

### Product Pages
- High-quality images
- Multiple angles, zoom
- Video demonstrations
- Detailed descriptions
- Specifications
- Reviews and ratings
- Related products

### Category Pages
- Clear navigation
- Filters: price, brand, size, color
- Sort: relevance, price, popularity
- Pagination or infinite scroll
- Product comparison

### Search
- Auto-complete suggestions
- Synonym matching
- Typo tolerance
- Faceted search: filter results
- Visual search: image input

### Cart and Checkout
- Guest checkout: no account required
- Progress indicator
- Minimal form fields
- Address auto-complete
- Multiple payment options
- Shipping options with rates
- Order summary
- Trust signals: security badges

## Conversion Optimization

### Key Metrics
- Conversion rate: purchases / visitors
- AOV: average order value
- Cart abandonment: 70% typical
- Revenue per visitor
- Customer acquisition cost

### Optimization Techniques
- A/B testing: compare versions
- Personalization: tailored experience
- Urgency: limited time offers
- Social proof: reviews, testimonials
- Free shipping: threshold or all
- Easy returns: reduce risk
- Mobile optimization: responsive

## Payment Processing
- Gateway: authorizes transactions
- Processor: moves money
- Merchant account: holds funds
- PSP: all-in-one (Stripe, PayPal)
- Fees: 2-3% + $0.30 typical
- Methods: cards, digital wallets, BNPL, crypto

## Fulfillment

### Methods
- Self-fulfillment: pack and ship
- 3PL: third-party logistics
- Dropshipping: supplier ships direct
- FBA: Fulfillment by Amazon

### Shipping
- Carriers: USPS, UPS, FedEx, DHL
- Rates: weight, distance, speed
- Free shipping: built into price
- Real-time: calculated at checkout
- International: customs, duties

## Customer Retention
- Email: post-purchase, re-engagement
- Loyalty programs: points, tiers
- Subscription: recurring delivery
- Reviews: encourage and display
- Customer service: responsive, helpful
- Personalization: recommendations

## Analytics
- Traffic: visitors, sources
- Funnel: browse -> cart -> checkout -> purchase
- Attribution: which channel
- Cohort: groups over time
- LTV: lifetime value
- RFM: recency, frequency, monetary

## Common Pitfalls
- Complicated checkout
- Hidden costs at checkout
- Poor product images
- No reviews
- Slow site speed
- Not mobile-optimized
- Ignoring post-purchase experience
""", "tags": ["e-commerce", "platforms", "conversion", "checkout", "fulfillment", "reference"]}
    ],
    "business_supplychain_management": [
        {"title": "Supply Chain Optimization Reference", "content": """# Supply Chain Optimization Reference

## Supply Chain Strategy

### Types
- Efficient: low cost, predictable demand (toilet paper)
- Responsive: flexible, variable demand (fashion)
- Agile: quick response, customization
- Custom: configured to order
- Flexible: adapt to volume and mix

### Drivers
- Facilities: where things happen
- Inventory: what's stored
- Transportation: how it moves
- Information: data flow
- Sourcing: who does what
- Pricing: revenue capture

## Inventory Management

### EOQ (Economic Order Quantity)
- Q* = sqrt(2DS/H)
- D: annual demand
- S: order cost
- H: holding cost per unit per year

### Safety Stock
- Buffer for demand and lead time variability
- SS = z * sigma * sqrt(L)
- z: service level (1.65 for 95%)
- sigma: demand standard deviation
- L: lead time

### Reorder Point
- ROP = dL + SS
- d: demand per period
- L: lead time
- SS: safety stock

### ABC Analysis
- A: 20% items, 80% value (tight control)
- B: 30% items, 15% value (moderate)
- C: 50% items, 5% value (loose)

## Forecasting

### Time Series
- Moving average: average of last n
- Exponential smoothing: weighted, recent more
- ARIMA: autoregressive, integrated, moving average
- Seasonal decomposition: trend + seasonal + residual

### Causal
- Regression: predictors
- Econometric: economic variables
- Machine learning: complex patterns

### Metrics
- MAPE: mean absolute percentage error
- RMSE: root mean square error
- Bias: systematic over/under

## Logistics

### Transportation Modes
- Truck: flexible, door-to-door
- Rail: bulk, long distance
- Air: fast, expensive
- Sea: cheap, slow, bulk
- Pipeline: liquids, gases
- Intermodal: multiple modes

### Warehouse
- Receiving: inbound
- Put-away: store
- Picking: select for order
- Packing: prepare for shipment
- Shipping: outbound
- Slotting: optimal placement

### Distribution Networks
- Direct: manufacturer to customer
- Centralized: one DC
- Regional: multiple DCs
- Hub-and-spoke: central + satellites
- Drop-shipping: supplier direct

## Bullwhip Effect
- Demand variability increases upstream
- Causes: demand forecasting, order batching, price fluctuation, rationing
- Mitigation: information sharing, smaller batches, EDLP, VMI

## Sourcing

### Supplier Selection
- Criteria: cost, quality, delivery, service, financial stability
- Total cost of ownership: purchase + operating + disposal
- Single vs multiple sourcing
- Nearshoring vs offshoring

### Supplier Relationships
- Transactional: arm's length
- Collaborative: partnership
- Strategic alliance: long-term
- Vertical integration: own supplier

## Supply Chain Risk
- Disruption: natural, political, pandemic
- Financial: supplier bankruptcy
- Cyber: attack on systems
- Mitigation: diversification, buffers, visibility, contingency

## Common Pitfalls
- Over-optimizing cost, ignoring risk
- Not sharing information
- Ignoring bullwhip effect
- Poor forecasting
- Excessive inventory
- Not considering total cost
""", "tags": ["supply chain", "inventory", "logistics", "forecasting", "bullwhip", "reference"]}
    ],
    "business_human_resources": [
        {"title": "HR Practices and Employment Law Reference", "content": """# HR Practices and Employment Law Reference

## Recruitment

### Sourcing
- Job boards: Indeed, LinkedIn, Glassdoor
- Employee referrals: high quality
- Social media: LinkedIn, Twitter
- Campus recruiting: universities
- Recruiting agencies: headhunters
- Diversity sourcing: targeted outreach

### Selection
- Resume screening: ATS
- Phone screen: initial filter
- Interviews: structured, behavioral, technical
- Assessments: cognitive, personality, skills
- Background checks: criminal, credit, references
- Work samples: realistic job preview

### Structured Interview
- Same questions for all candidates
- Behavioral: "Tell me about a time..."
- STAR: Situation, Task, Action, Result
- Scoring rubric: reduce bias
- Validation: predict performance

## Onboarding
- Pre-boarding: paperwork, setup
- Day 1: welcome, orientation
- First week: training, introductions
- 30/60/90: milestones
- Buddy system: peer support
- Clear expectations: role, goals

## Performance Management

### Process
1. Goal setting: SMART goals
2. Ongoing feedback: regular
3. Mid-year review: check-in
4. Annual review: formal evaluation
5. Development plan: growth

### Methods
- MBO: management by objectives
- 360 feedback: peers, reports, managers
- OKR: objectives and key results
- Continuous: ongoing feedback
- Calibration: ensure consistency

## Compensation

### Components
- Base salary: fixed
- Variable: bonus, commission
- Equity: stock, options
- Benefits: health, retirement, PTO

### Pay Structures
- Job evaluation: worth of job
- Market pricing: external comparison
- Pay grades: ranges by level
- Pay equity: equal pay for equal work
- Pay range: min, mid, max

## Benefits
- Health insurance: medical, dental, vision
- Retirement: 401(k), pension
- Paid time off: vacation, sick, holidays
- Family leave: parental, caregiving
- Flexible work: remote, hybrid, hours
- Wellness: gym, mental health

## Employment Law (US)

### Major Laws
- FLSA: minimum wage, overtime
- Title VII: discrimination (race, color, religion, sex, national origin)
- ADA: disability accommodation
- ADEA: age discrimination (40+)
- FMLA: family and medical leave
- NLRA: labor relations
- OSHA: workplace safety
- ERISA: retirement plans
- COBRA: continued health coverage
- Lilly Ledbetter: pay discrimination

### Compliance
- I-9: work authorization
- EEO-1: workforce composition
- Affirmative action: federal contractors
- Harassment prevention: training, policy
- Wage and hour: classification, overtime

## Employee Relations
- Engagement: commitment, motivation
- Recognition: appreciation
- Conflict resolution: mediation
- Discipline: progressive (verbal, written, final, termination)
- Exit interviews: learn from departures
- Grievance: formal complaint process

## Common Pitfalls
- Unstructured interviews (biased, poor predictors)
- Not documenting performance issues
- Inconsistent policy application
- Ignoring engagement
- Not developing managers
- Compliance gaps
- Not addressing toxic behavior
""", "tags": ["human resources", "recruitment", "performance", "compensation", "employment law", "reference"]}
    ],
    "business_customer_service": [
        {"title": "Customer Experience and Support Operations Reference", "content": """# Customer Experience and Support Operations Reference

## Service Channels

### Voice
- Phone: traditional, personal
- IVR: interactive voice response
- Callback: avoid waiting
- Voice AI: speech recognition

### Digital
- Email: asynchronous
- Chat: real-time text
- Chatbot: automated
- Social: Twitter, Facebook, WhatsApp
- SMS: text messaging
- Self-service: knowledge base, FAQ

### In-person
- Retail: face-to-face
- Field service: on-site
- Events: conferences, demos

## Service Metrics

### Efficiency
- AHT: average handle time
- ASA: average speed to answer
- Service level: % answered in target
- Abandon rate: callers who hang up
- Occupancy: time on calls vs available
- FCR: first contact resolution

### Quality
- CSAT: customer satisfaction
- NPS: net promoter score
- CES: customer effort score
- QA score: quality monitoring
- Sentiment: emotional analysis

### Volume
- Contacts per period
- Channel mix
- Seasonal patterns
- Forecast accuracy

## Customer Experience (CX)

### Journey Mapping
- Stages: awareness, purchase, use, support, advocacy
- Touchpoints: each interaction
- Pain points: friction
- Moments of truth: critical interactions
- Emotion: how customer feels

### Voice of Customer (VoC)
- Surveys: CSAT, NPS, CES
- Feedback: reviews, social, support tickets
- Interviews: in-depth
- Focus groups: group discussion
- Analytics: behavior data

### Personalization
- Segmentation: customer groups
- Recommendations: relevant products
- Communication: tailored messages
- Self-service: personalized portal

## Support Operations

### Ticketing
- Create: log issue
- Categorize: type, priority
- Assign: to agent or team
- Track: status, SLA
- Resolve: fix issue
- Close: confirm satisfaction

### Knowledge Management
- Knowledge base: articles
- FAQs: common questions
- Internal wiki: agent resources
- Search: find answers
- Updates: keep current
- Feedback: article helpfulness

### Workforce Management
- Forecasting: predict volume
- Scheduling: staff to demand
- Real-time: adjust to actual
- Adherence: following schedule
- Shrinkage: non-productive time

### Quality Assurance
- Monitoring: listen/observe
- Scoring: rubric
- Coaching: feedback
- Calibration: consistent scoring
- Improvement: action plans

## Escalation
- Technical: to higher tier
- Management: to supervisor
- Executive: to leadership
- Process: defined triggers
- Communication: keep customer informed

## Self-Service
- Knowledge base: searchable articles
- Community: peer forums
- Chatbot: automated responses
- Video tutorials: visual guides
- Account portal: manage own service

## Common Pitfalls
- Long wait times
- Transfers and repeats
- Inconsistent answers
- Not resolving on first contact
- Treating symptoms, not root causes
- Not closing the loop on feedback
- Understaffing
""", "tags": ["customer service", "CX", "support", "metrics", "self-service", "reference"]}
    ],
}

BUSINESS_K3_BATCH4: dict[str, list[dict]] = {
    "business_insurance_risk_management": [
        {"title": "Risk Assessment and Insurance Types Reference", "content": """# Risk Assessment and Insurance Types Reference

## Risk Management Process (ISO 31000)
1. Identify: what can happen
2. Analyze: likelihood and impact
3. Evaluate: prioritize risks
4. Treat: mitigate, transfer, avoid, accept
5. Monitor and review: ongoing

## Risk Treatment Options
- Avoid: don't do the activity
- Mitigate: reduce likelihood or impact
- Transfer: insurance, contract
- Accept: acknowledge and budget

## Insurance Types

### Life
- Term: fixed period, death benefit
- Whole life: permanent, cash value
- Universal life: flexible premium
- Variable life: investment component
- Annuity: income stream

### Health
- HMO: network, primary care gatekeeper
- PPO: network, more flexibility
- HDHP: high deductible, HSA compatible
- Medicare: 65+ (US)
- Medicaid: low income (US)
- Short-term: temporary coverage

### Property and Casualty
- Homeowners: dwelling, contents, liability
- Renters: contents, liability
- Auto: liability, collision, comprehensive
- Umbrella: excess liability
- Business: general liability, property, BOP
- Workers compensation: employee injury
- Professional liability: errors and omissions

### Specialty
- Marine: cargo, hull
- Aviation: aircraft
- Cyber: data breach
- Directors and officers (D&O)
- Key person: critical employee
- Business interruption: lost income

## Insurance Mechanics

### Pricing (Underwriting)
- Risk classification: pool similar risks
- Rate: price per unit of exposure
- Premium: rate x exposure units
- Deductible: insured's share
- Policy limits: max payout
- Coinsurance: shared percentage

### Actuarial Concepts
- Loss frequency: how often
- Loss severity: how big
- Expected loss: frequency x severity
- Loss ratio: losses / premiums
- Combined ratio: losses + expenses / premiums
  - < 100%: underwriting profit
  - > 100%: underwriting loss

## Reinsurance
- Insurer buys insurance
- Facultative: individual risk
- Treaty: automatic, portfolio
- Quota share: percentage of all
- Excess of loss: above retention
- Purpose: capacity, stability, capital relief

## Risk Assessment Tools
- Risk matrix: likelihood vs impact
- Risk register: documented risks
- Heat map: visual priority
- Monte Carlo: probability simulation
- Scenario analysis: what-if
- Sensitivity analysis: variable impact

## Enterprise Risk Management (ERM)
- Integrated: across organization
- COSO ERM framework
- Risk appetite: what's acceptable
- Risk tolerance: variation around objectives
- Key risk indicators (KRIs): early warning
- Risk culture: attitudes and behaviors

## Common Pitfalls
- Under-insuring to save premium
- Not understanding policy exclusions
- Ignoring deductibles
- Not reviewing coverage periodically
- Moral hazard: insurance encouraging risk
- Adverse selection: high-risk buying more
- Not considering business interruption
""", "tags": ["insurance", "risk management", "actuarial", "reinsurance", "ERM", "reference"]}
    ],
    "business_procurement": [
        {"title": "Strategic Sourcing and Contract Management Reference", "content": """# Strategic Sourcing and Contract Management Reference

## Strategic Sourcing Process
1. Spend analysis: what's bought, from whom
2. Category strategy: approach by category
3. Market analysis: supplier landscape
4. Supplier identification: find candidates
5. RFx: request for information/quote/proposal
6. Negotiation: terms and price
7. Contract: formal agreement
8. Onboarding: integrate supplier
9. Performance management: monitor
10. Continuous improvement: optimize

## RFx Types
- RFI: information, no commitment
- RFQ: quote, price-focused, commodities
- RFP: proposal, value-focused, complex
- RFB: bid, sealed, public sector
- RFT: tender, formal, regulated

## Total Cost of Ownership (TCO)
- Acquisition: purchase price, taxes, shipping
- Operating: energy, maintenance, supplies
- Training: learning curve
- Support: service, help desk
- Downtime: lost productivity
- Disposal: decommissioning, recycling
- Risk: potential problems

## Supplier Evaluation

### Criteria
- Quality: defect rates, certifications
- Cost: price, terms, total cost
- Delivery: on-time, lead time
- Service: responsiveness, support
- Financial stability: solvency
- Capacity: ability to scale
- Innovation: new ideas
- Sustainability: environmental, social
- Compliance: regulations, ethics

### Scorecard
- Weighted criteria
- Quantitative metrics
- Qualitative ratings
- Regular review
- Comparison to targets

## Negotiation

### Principles (Fisher & Ury)
- Separate people from problem
- Focus on interests, not positions
- Invent options for mutual gain
- Use objective criteria
- BATNA: best alternative to negotiated agreement

### Tactics
- Anchoring: first offer
- Concessions: trade, don't give
- Silence: let them talk
- Walk away: know your BATNA
- Package: combine issues

## Contract Management

### Contract Types
- Fixed price: set price, risk on supplier
- Cost reimbursable: actual cost + fee, risk on buyer
- Time and materials: hourly rates
- Incentive: performance-based
- Indefinite delivery: ongoing, as needed

### Key Terms
- Scope: what's included
- Deliverables: what's produced
- Timeline: when
- Payment: how and when
- Warranties: guarantees
- Liability: who pays for what
- Termination: how to end
- Intellectual property: who owns
- Confidentiality: protect information
- Force majeure: unforeseen events

### Performance
- SLA: service level agreement
- KPIs: key performance indicators
- Penalties: non-performance
- Incentives: over-performance
- Reviews: periodic assessment
- Corrective action: fix problems

## Supplier Relationship Management (SRM)
- Segment: strategic, tactical, transactional
- Strategic: partnership, joint planning
- Tactical: managed, regular review
- Transactional: efficient, automated
- Governance: structure and process
- Communication: regular cadence
- Innovation: collaborative improvement

## Common Pitfalls
- Focusing only on price
- Not considering total cost
- Poor contract definition
- Not monitoring performance
- Over-reliance on single supplier
- Not managing relationships
- Ignoring ethical and sustainability issues
""", "tags": ["procurement", "sourcing", "contracts", "TCO", "SRM", "reference"]}
    ],
    "business_product_management": [
        {"title": "Product Lifecycle and Agile Methods Reference", "content": """# Product Lifecycle and Agile Methods Reference

## Product Lifecycle
1. Introduction: launch, build awareness
2. Growth: rapid sales, competition
3. Maturity: peak sales, differentiation
4. Decline: sales fall, exit decision

## Product Discovery
- Customer interviews: understand needs
- Market research: validate demand
- Competitive analysis: positioning
- Prototyping: test concepts
- Usability testing: user feedback
- A/B testing: compare options
- Analytics: behavior data

## Product Development

### Agile (Scrum)
- Product owner: represents customer
- Scrum master: facilitates process
- Development team: builds product
- Sprint: 1-4 week iteration
- Sprint planning: what to do
- Daily standup: progress and blockers
- Sprint review: demonstrate
- Retrospective: improve process

### Artifacts
- Product backlog: all work items
- Sprint backlog: this sprint's items
- Increment: working product
- User stories: feature from user view
- Acceptance criteria: definition of done
- Story points: relative effort estimate

### Kanban
- Visualize workflow: board
- Limit WIP: work in progress
- Manage flow: smooth movement
- Make policies explicit
- Feedback loops: improve
- Improve collaboratively

## Product Strategy

### Vision
- Long-term aspiration
- What to achieve
- Who to serve
- Why it matters

### Roadmap
- Themes: strategic areas
- Epics: large initiatives
- Features: specific capabilities
- Timeline: now, next, later
- Outcomes: what to achieve

### Prioritization

#### RICE
- Reach: how many affected
- Impact: how much (3=massive, 2=high, 1=medium, 0.5=low)
- Confidence: how sure (100%, 80%, 50%)
- Effort: person-months
- Score: (R x I x C) / E

#### MoSCoW
- Must have: required
- Should have: important
- Could have: nice to have
- Won't have: not now

#### Kano Model
- Basic: must have, no delight
- Performance: more is better
- Delight: unexpected, joy
- Indifferent: don't care
- Reverse: don't want

## Metrics

### North Star
- Primary success metric
- Aligns team
- Reflects customer value
- Examples: DAU, ARR, engagement

### AARRR (Pirate Metrics)
- Acquisition: how users find you
- Activation: first good experience
- Retention: users return
- Revenue: users pay
- Referral: users recommend

### HEART (Google)
- Happiness: satisfaction
- Engagement: depth of use
- Adoption: new users
- Retention: returning users
- Task success: completion rate

## Launch
- Beta: limited release for feedback
- Soft launch: limited market
- Full launch: everyone
- Go-to-market: how to sell
- Positioning: how to describe
- Pricing: how to charge
- Channels: where to sell
- Marketing: how to promote

## Common Pitfalls
- Building without customer input
- Over-building before testing
- Not prioritizing ruthlessly
- Confusing features with value
- Not measuring outcomes
- Ignoring technical debt
- Not aligning with business strategy
""", "tags": ["product management", "agile", "scrum", "roadmap", "prioritization", "reference"]}
    ],
    "business_project_management": [
        {"title": "Project Management Frameworks Reference", "content": """# Project Management Frameworks Reference

## PMBOK (PMI) - 10 Knowledge Areas
1. Integration: coordinate all
2. Scope: what's included
3. Schedule: timeline
4. Cost: budget
5. Quality: standards
6. Resource: people and materials
7. Communications: information flow
8. Risk: uncertainty
9. Procurement: buying
10. Stakeholder: interested parties

## Process Groups
1. Initiating: start project
2. Planning: detailed approach
3. Executing: do the work
4. Monitoring and Controlling: track and adjust
5. Closing: formal completion

## Scope Management
- Project charter: authorization
- Scope statement: what's included/excluded
- WBS: work breakdown structure
  - Decompose to work packages
  - 100% rule: all work included
- Scope baseline: approved scope
- Change control: manage changes

## Schedule Management
- Activities: tasks
- Dependencies: FS, FF, SS, SF
- Critical path: longest path
- Float: slack time
- Gantt chart: visual timeline
- Milestones: key points
- Crashing: add resources to shorten
- Fast tracking: overlap activities

## Cost Management
- Estimate: approximate cost
  - Analogous: similar projects
  - Parametric: unit cost x quantity
  - Bottom-up: detailed
- Budget: approved cost baseline
- Earned value: integrated scope, schedule, cost
  - PV: planned value
  - EV: earned value
  - AC: actual cost
  - CPI: EV / AC (cost performance)
  - SPI: EV / PV (schedule performance)
  - EAC: estimated at completion

## Risk Management
- Identify: what can go wrong
- Assess: probability and impact
- Prioritize: risk score
- Plan response:
  - Avoid: eliminate
  - Mitigate: reduce
  - Transfer: insurance
  - Accept: acknowledge
- Monitor: track and update
- Risk register: documented risks

## Agile Frameworks

### Scrum
- Roles: PO, SM, team
- Events: sprint, planning, standup, review, retro
- Artifacts: backlog, sprint backlog, increment
- Empirical: inspect and adapt

### Kanban
- Visualize: board
- WIP limit: constrain work
- Flow: smooth movement
- Continuous: no sprints

### SAFe (Scaled Agile)
- Teams: 5-9 people
- Agile Release Train: 50-125
- Solution Train: 125+
- Program Increment: 8-12 weeks

## PRINCE2
- Principles: continued justification, learn from experience, defined roles, manage by stages, manage by exception, focus on products, tailor to suit
- Themes: business case, organization, quality, plans, risk, change, progress
- Processes: starting up, directing, initiating, controlling, managing delivery, managing stage boundaries, closing

## Common Pitfalls
- Poor scope definition (scope creep)
- Unrealistic schedule
- Inadequate risk management
- Not engaging stakeholders
- Poor communication
- Not tracking progress
- Not managing changes
- Inadequate resources
""", "tags": ["project management", "PMBOK", "agile", "Scrum", "PRINCE2", "earned value", "reference"]}
    ],
}

BUSINESS_K3_BATCH5: dict[str, list[dict]] = {
    "business_nonprofit_administration": [
        {"title": "Nonprofit Governance and Fundraising Reference", "content": """# Nonprofit Governance and Fundraising Reference

## Governance

### Board of Directors
- Legal fiduciary: duty of care, loyalty, obedience
- Set mission and strategy
- Hire and evaluate executive director
- Ensure financial sustainability
- Approve budget
- Policy making
- Fundraising role

### Board Structure
- Chair: leads board
- Vice chair: succession
- Secretary: records
- Treasurer: finances
- Committees: executive, finance, governance, fundraising, program

### Board Practices
- Recruitment: skills, diversity, commitment
- Orientation: mission, bylaws, finances
- Meetings: regular, agenda, minutes
- Self-assessment: periodic evaluation
- Term limits: rotation
- Conflict of interest: disclosure

## Fundraising

### Individual Giving
- Annual fund: yearly appeals
- Major gifts: large individual donations
- Planned giving: bequests, trusts
- Capital campaign: specific project
- Crowdfunding: many small gifts
- Peer-to-peer: supporters fundraise

### Institutional
- Foundations: grants
  - Community: local
  - Family: private
  - Corporate: company-sponsored
- Corporate: sponsorship, matching, in-kind
- Government: federal, state, local

### Grant Writing
- Need statement: problem to address
- Goals and objectives: SMART
- Methods: how to achieve
- Evaluation: how to measure
- Budget: detailed costs
- Sustainability: after grant ends
- Organizational capacity: qualifications

## Revenue Models
- Charitable: donations, grants
- Earned income: fees for service
- Social enterprise: business with mission
- Membership: dues
- Endowment: investment income
- Government contracts: services

## Financial Management
- Budget: annual plan
- Cash flow: timing of income and expenses
- Fund accounting: restricted vs unrestricted
- Audit: independent review
- Form 990: IRS annual return
- Financial policies: controls, reserves

## Impact Measurement

### Logic Model
- Inputs: resources
- Activities: what's done
- Outputs: what's produced
- Outcomes: what changes
- Impact: long-term difference

### Theory of Change
- If-then: activities lead to outcomes
- Assumptions: what must be true
- Indicators: how to measure
- Evaluation: assess progress

### Frameworks
- SROI: social return on investment
- Outcome harvesting: identify what changed
- Most Significant Change: stories
- Randomized controlled trials: rigorous

## Nonprofit Lifecycle
1. Idea: concept
2. Start-up: launch
3. Growth: expand
4. Maturity: stable
5. Decline: stagnation
6. Renewal or exit: transform or close

## Legal and Compliance
- 501(c)(3): tax-exempt (US)
- State registration: charitable solicitation
- Board liability: D&O insurance
- Employment: same as for-profit
- Lobbying: limits for 501(c)(3)
- Political activity: prohibited
- Unrelated business income tax (UBIT)

## Common Pitfalls
- Founder's syndrome: founder won't let go
- Board micromanagement
- Not diversifying funding
- No strategic plan
- Ignoring impact measurement
- Under-investing in infrastructure
- Not paying competitive salaries
""", "tags": ["nonprofit", "governance", "fundraising", "impact", "501c3", "reference"]}
    ],
    "business_real_estate": [
        {"title": "Real Estate Investment and Valuation Reference", "content": """# Real Estate Investment and Valuation Reference

## Property Types

### Residential
- Single-family: detached house
- Multi-family: 2-4 units
- Apartment: 5+ units
- Condominium: owned unit
- Cooperative: owned shares
- Townhouse: attached

### Commercial
- Office: Class A, B, C
- Retail: strip, mall, anchor
- Industrial: warehouse, manufacturing
- Flex: office + industrial
- Mixed-use: combination

### Special Purpose
- Hotel: hospitality
- Self-storage: storage units
- Medical: healthcare
- Student housing: university
- Senior living: elderly
- Data center: servers

## Valuation Methods

### Sales Comparison
- Compare to recent sales
- Adjust for differences
- Most common for residential
- Need comparable properties

### Income Approach
- Value = NOI / Cap Rate
- NOI: net operating income (gross - operating expenses)
- Cap rate: market rate of return
- Used for income-producing property

### Cost Approach
- Value = land + improvement cost - depreciation
- Used for new or special purpose
- Replacement cost: new equivalent
- Reproduction cost: exact replica

## Investment Analysis

### Cash Flow
- Gross income: rents + other
- Vacancy: uncollected
- Effective gross income: gross - vacancy
- Operating expenses: taxes, insurance, maintenance, management
- NOI: EGI - operating expenses
- Debt service: mortgage payments
- Cash flow: NOI - debt service

### Returns
- Cash-on-cash: cash flow / cash invested
- Cap rate: NOI / price
- IRR: total return over holding period
- Equity multiple: total distributions / investment
- Total return: cash flow + appreciation + principal reduction

### Metrics
- DSCR: NOI / debt service (lenders want > 1.25)
- LTV: loan / value (typically 70-80% max)
- GRM: price / gross rent (quick estimate)
- Price per unit, per square foot

## Financing

### Mortgage Types
- Conventional: bank, 20% down
- FHA: 3.5% down, government insured
- VA: no down, veterans
- Commercial: 5-20 year terms
- Portfolio: lender holds
- Hard money: short-term, high rate

### Terms
- Amortization: paying off principal
- 30-year: most common residential
- 15-year: faster payoff, higher payment
- Interest-only: no principal
- Balloon: large payment at end
- ARM: adjustable rate

## Real Estate Markets
- Cycles: expansion, peak, recession, recovery
- Drivers: jobs, population, income, interest rates
- Supply: new construction, land availability
- Demand: population, employment, affordability
- Local: real estate is location-specific

## REITs (Real Estate Investment Trusts)
- Publicly traded: stock exchange
- Non-traded: not on exchange
- Required: distribute 90% of taxable income
- Types: equity, mortgage, hybrid
- Sectors: residential, retail, office, industrial, healthcare, hotel

## 1031 Exchange (US)
- Defer capital gains tax
- Like-kind property
- 45 days to identify
- 180 days to close
- Must use qualified intermediary

## Common Pitfalls
- Underestimating expenses
- Overestimating rents
- Ignoring vacancy
- Not accounting for capital expenditures
- Over-leveraging
- Not considering market cycles
- Ignoring location factors
""", "tags": ["real estate", "investment", "valuation", "cap rate", "REIT", "reference"]}
    ],
    "business_hospitality_tourism": [
        {"title": "Hospitality Operations and Revenue Management Reference", "content": """# Hospitality Operations and Revenue Management Reference

## Hotel Operations

### Departments
- Front office: check-in, check-out
- Housekeeping: cleaning, rooms
- Food and beverage: restaurants, room service
- Maintenance: repairs, upkeep
- Sales and marketing: bookings
- Revenue management: pricing
- Human resources: staffing
- Security: safety

### Key Metrics
- Occupancy: rooms sold / available
- ADR: average daily rate = room revenue / rooms sold
- RevPAR: revenue per available room = room revenue / available rooms
- RevPAR = occupancy x ADR
- GOPPAR: gross operating profit per available room
- TRevPAR: total revenue per available room

## Revenue Management
- Yield management: maximize revenue
- Dynamic pricing: adjust by demand
- Forecasting: predict occupancy
- Segmentation: business, leisure, group
- Channel management: OTAs, direct, GDS
- Overbooking: manage no-shows
- Length of stay control

### Distribution Channels
- Direct: hotel website, phone
- OTA: Booking.com, Expedia
- GDS: travel agents
- Wholesaler: bulk buyers
- Tour operators: packages
- Metasearch: Google, Trivago
- Channel costs: commission varies

## Food and Beverage

### Restaurant Operations
- Menu engineering: profit and popularity
- Food cost: 28-35% of price
- Labor cost: 25-35% of sales
- Prime cost: food + labor
- Table turnover: parties per table
- Check average: spend per person

### Service Standards
- Greeting: prompt welcome
- Order accuracy: correct items
- Timing: appropriate pace
- Quality: food as specified
- Cleanliness: tables, restrooms
- Recovery: fix problems

## Tourism

### Types
- Leisure: vacation
- Business: meetings, conventions
- VFR: visiting friends and relatives
- Ecotourism: nature-based, sustainable
- Cultural: heritage, arts
- Adventure: physical activity
- Medical: treatment abroad
- Educational: learning travel

### Economic Impact
- Direct: tourist spending
- Indirect: supply chain
- Induced: employee spending
- Multiplier effect: ripple
- Employment: jobs
- Tax revenue: government
- Foreign exchange: international

### Sustainable Tourism
- Environmental: minimize impact
- Social: respect local culture
- Economic: benefit local community
- Carrying capacity: limits
- Certification: GSTC, EarthCheck

## Event Management
- Planning: objectives, budget, timeline
- Venue: location, capacity, facilities
- Catering: food and beverage
- Audiovisual: sound, lighting, projection
- Registration: sign-in, badges
- Program: agenda, speakers
- Logistics: transport, accommodation
- Evaluation: feedback, outcomes

## Customer Experience
- Pre-arrival: booking, communication
- Arrival: check-in, welcome
- Stay: room, service, amenities
- Departure: check-out, farewell
- Post: follow-up, loyalty

## Common Pitfalls
- Not managing online reputation
- Inconsistent service quality
- Poor revenue management
- Ignoring direct bookings
- Under-investing in staff training
- Not adapting to market changes
- Ignoring sustainability
""", "tags": ["hospitality", "tourism", "RevPAR", "revenue management", "operations", "reference"]}
    ],
    "business_intellectualproperty_commercialization": [
        {"title": "IP Strategy and Technology Transfer Reference", "content": """# IP Strategy and Technology Transfer Reference

## IP Types

### Patents
- Utility: new and useful process, machine, manufacture, composition
- Design: ornamental design
- Plant: new plant variety
- Requirements: novel, non-obvious, useful
- Term: 20 years from filing (utility)
- Territorial: country by country
- USPTO (US), EPO (Europe), WIPO (international)

### Trademarks
- Word, logo, slogan, sound, color
- Distinctiveness: generic (no), descriptive, suggestive, arbitrary, fanciful
- Use in commerce: required
- Registration: USPTO, state
- Term: renewable indefinitely if in use
- Likelihood of confusion: test for infringement

### Copyrights
- Original works of authorship
- Literary, musical, dramatic, artistic, software
- Fixed in tangible medium
- Automatic upon creation
- Registration: for enforcement
- Term: life of author + 70 years (US)
- Fair use: criticism, comment, news, teaching, parody

### Trade Secrets
- Information with economic value
- Not generally known
- Reasonable efforts to protect
- No expiration if maintained
- Examples: formulas (Coca-Cola), processes, customer lists
- Protection: NDAs, access controls

## IP Strategy

### Building Portfolio
- Invention disclosure: document ideas
- Patent committee: review
- File or hold as trade secret
- Continuations: refine claims
- International: PCT application

### Defensive
- Defensive publications: prevent others from patenting
- Prior art: establish existing knowledge
- Cross-licensing: mutual rights
- Patent pools: shared licensing

### Offensive
- Exclude competitors
- License for revenue
- Litigate infringers
- Build barriers to entry

## Licensing

### Terms
- License: permission to use
- Exclusive: only one licensee
- Non-exclusive: multiple licensees
- Field of use: specific application
- Territory: geographic scope
- Term: duration
- Royalty: payment (fixed, percentage, minimum)
- Upfront fee: initial payment
- Milestone: payment on event
- Sublicense: licensee can license others

### Agreement
- Grant: what's licensed
- Consideration: payment terms
- Performance: obligations
- Quality control: standards
- Termination: end conditions
- Dispute resolution: how to resolve
- Indemnification: liability

## Technology Transfer

### Bayh-Dole Act (US, 1980)
- Universities own federally funded inventions
- Must patent and commercialize
- Share royalties with inventors
- Preference for US industry
- March-in rights: government can act if not commercialized

### University TTO (Tech Transfer Office)
- Disclose: inventor reports
- Evaluate: commercial potential
- Protect: file patents
- Market: find licensees
- License: agreement
- Monitor: compliance and revenue

### Commercialization Paths
- License to existing company
- Startup: spin-out company
- Open source: freely available
- Standards: contribute to standards body

## Valuation

### Methods
- Cost: development cost
- Market: comparable transactions
- Income: future cash flows
  - DCF: discounted cash flow
  - Relief from royalty: avoid paying
  - Excess earnings: above normal return
- Real options: flexibility value

### Factors
- Strength: scope, validity
- Market size: potential
- Remaining life: time left
- Freedom to operate: can practice
- Enforcement: detectable infringement

## Common Pitfalls
- Not filing before public disclosure
- Over-disclosing in publications
- Not using NDAs
- Assuming international filing is automatic
- Not monitoring for infringement
- Over-valuing IP
- Not aligning IP with business strategy
""", "tags": ["intellectual property", "patents", "licensing", "technology transfer", "Bayh-Dole", "reference"]}
    ],
}

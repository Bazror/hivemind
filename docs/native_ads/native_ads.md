# Native Ads [Pre-Alpha]

*Design overview for Native Ads feature in Hivemind Communities (WIP)*

---

To aid communities in shaping their attention economies, a feature to manage different types of ad spaces within a community is proposed. This will augment the built-in "promoted" posts feature, giving communities on the Steem blockchain more options to monetize.

By putting ad characteristics, purchases and moderation outcomes on the blockchain, we create a transparent, verifiable and auditable environment. Hivemind will synchronize all the ad related activity and present an easy to use interface for developers to work with, the same as it does with social interactions.

## Key points to note

- Promoted posts (legacy) will be optional, as will be the new native ad system
- Communities can still feature posts, by pinning them for example. This feature is not affected.
- Ads will use new metadata attributes and associated `custom-json` actions

## Ad System Design Principles

In designing this system, the following principles are followed.

### Minimal changes to base code

Fewer, calculated changes made to the core codebase will make the proposed update easier. The aim is to add the features without changing too much logic or disrupting the original development path.

### Positive transactional net-effect for STEEM economy

The net effect of selling "ad space" should be positive for the STEEM economy, meaning monetary value should flow into the system, with no direct monetary outflows, but only attention value flowing out.

### No direct impact/influence on community rewards

By making all ads decline payout and enforcing this rule in Hivemind itself, we strengthen the economic benefits derived from the transactional net-effect mentioned above.

---

## Ad System Overview

*This section describes how the ad system works. These features are still under development and are subject to change.*

### Ad creation

Ads are created by making posts in a community. Posts will contain metadata that holds the ad's properties, duration (total time units), starting bid and an optional start time.

### Bidding process

Bids are placed by the ad creator's account through custom JSON operations.

A bid operation will contain metadata with:

- The post ID for the ad
- Transactional data (increase or decrease bid amount, token)
- Duration data (time units) [optional]

Building dedicated user interfaces for handling the bidding process will be possible. Appropriate data sets will be availed through the API. For example, an endpoint to retrieve bids sorted by community and price-per-time-unit enables developers to create realtime competitive bidding interfaces that show users their ads' positions against others bidding for the same community.

### Ad status

The ad lifecycle is designed as an ordered flow. Different possibilities exist at each stage, with checks and balances coded in Hivemind to enforce the workflow.

**0 - Draft**: ad is newly created or was rejected [user]

**1 - Submitted**: a user has submitted it for review [user]

**2 - Approved**: ad has been approved by community moderator [mod]

**3 - Funded**: user has paid the bid amount in full [user]

**4 - Scheduled**: ad has been scheduled to run [mod / auto from payment]

### Ad review

Ads are reviewed by moderators based on bid amount and date. The highest bids for the day will be at the top of the list. Below are the different states that front-ends will be able to access and display.

**Awaiting review**

This is the default status for ads submitted for review by their creators.

**Approved**

The ad is approved and payment can be made.

**Ready**

Payment has been made and the ad is scheduled to show.

**Live**

The ad is currently showing.

**Rejected**

The ad has been rejected by a moderator during the review process and is back in the Draft (0) state. Notes may be left by a moderator explaining the reason why or requesting modifications. A user can resubmit the ad for review after posting an edited version of the post on the blockchainn. Note that only ads that are in the pre-approval (0-1) states can register successful edits. All other edits are ignored.


### Ad Payments

Communities will have the choice to either collect all ad revenue or have it burnt. A setting will be availed in a community's `settings`.

Once an ad is approved by moderators, valid payments can be made by sending tokens to a community account, or burning tokens, that are **no less** than the bid amount.

Even though approved, an ad will not be displayed until the payment is made. Unscheduled ads are manually enabled by a moderator, after a successful and valid payment. Scheduled ads are automatically enabled if the payment is made in time, as expanded on below.

### Scheduled Ads

To place an ad, it's mandatory to specify the amount of time you want it to be shown for. There is a `time_units` field that's required, and an optional field for `start_time`.

When no `start_time` is selected, the ad is an "unscheduled" ad;  a moderator will allocate it the earliest available time slot that fits its set duration completely. Front ends will have access to appropriate data sets and guidelines to implement this.

Ads can be scheduled to run at preselected times by specifying `start_time`.

Community managers/owners will also be able to set the earliest time from the present that scheduled ads can be placed. Some communities may have shorter response times and some longer, so this gives them the opportunity to factor in time for review, reducing the probability of "timed-out" ad reviews for time-sensitive scheduled ads.

*For example, if a community sets a window period of 48 hours, it means scheduled ads can only be for time starting 48 hours from the current hour. This gives the review and payment process about 48 hours.*

Payments for scheduled ads should be made before the time they're set to start showing. Otherwise, the ad will not be shown, the time slot will be freed up for other people to use and a moderator may ask for a revision.

The involvement of moderators will enable ads with late payments to be renegotiated for use at a later time as scheduled or unscheduled.

### Universal rules for ads

#### Decline payout

For ads to be valid, they need to decline reward payouts, by setting:

- `max_payout` to ZERO (0), or
- `@null` account as 100% beneficiary (burning)

#### Mandatory JSON metadata

Native ads are valid when they contain a `native_ad` key in the post's JSON metadata field. Within the key, a dictionary of parameters will define the ad.

- `type`: the type name of the ad, e.g. `native_post`
- `properties`: contains the type-specific properties, e.g. `"devices": "mobile"`
- `time_units`: the period of time the ad will run for (initial, can be updated through subsequent custom JSON ops)


### Ad Types

The flexibility of JSON-based data makes it easy to develop a wide array of ad types to suit different community types. More ad types will be developed as the project progresses. Read the **Ad Types** document (linked below) for more details on each ad type.

#### Native post

A native post is structured just like an ordinary post in a community. The difference is that it is given a dedicated, high-visibility spot and marked "sponsored."

#### Interactive polls

Interactive polls give community members a chance to share their opinions on a certain topic/question as well as see what other community members think. Hivemind enables polls to be implemented in communities and once they are developed, they can be an ad type as well.

They will differ from the normal polls that members can make in that they will be displayed on sections set aside for such polls, and will be marked "sponsored."


---

## Links to supporting documentation

- [Development Scope](https://github.com/imwatsi/hivemind/blob/master/docs/native_ads/dev_scope.md)

- [Ad Types](https://github.com/imwatsi/hivemind/blob/master/docs/native_ads/ad_types.md)

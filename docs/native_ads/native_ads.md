# Native Ads (Pre-Alpha)

*Design overview for Native Ads feature in communities (WIP)*

---

To aid communities in shaping their attention economies, a feature to manage different types of ad spaces within a community is proposed. This will augment the built-in "promoted" posts feature, giving developers more options to monetize communities on the Steem blockchain.

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

By making all ads decline payout and enforcing this rule in hivemind itself, we strengthen the economic benefits derived from transactional net-effect mentioned above.

---

## Ad System Overview

*This section describes how the ad system works. These features are still under development and are subject to change.*

### Ad creation

Ads are created by making posts in a community. Posts will contain metadata that holds the ad's properties.

### Bidding process

Bids are placed by the creator's account through custom JSON operations.

A bid operation will contain metadata with:

- The post for the ad
- Transactional data (increase or decrease bid amount, token)
- Time units (in minutes)

### Ad review

Ads are reviewed by moderators based on bid amount and date. The highest bids for the day will be at the top of the list. Below are the different states that an ad goes through.

**Awaiting review**

This is the default status for newly created ads.

**Revision**

A moderator can ask for modifications before approval.

**Approved**

The ad is approved and payment can be made.

**Enabled**

Payment has been made and the ad is ready to show.

**Live**

The ad is currently showing.

**Rejected**

The ad has been rejected by a moderator.

### Ad Payments

Once an ad is approved by moderators, valid payments can be made by burning tokens **no less** than the bid amount.

Even though approved, an ad will not be displayed until the payment is made. Ads are automatically enabled after successful payment. If it's a scheduled ad, it will be automatically enabled, provided the payment is made in time, as expanded on below.

### Scheduled Ads

To place an ad, it's mandatory to specify the amount of time you want it to be shown for. There is a `time_units` field that's required, and optional fields for start and end times.

When no date/time is selected, the ad is an "unscheduled" ad;  a moderator will allocate it the earliest available time slot that fits its set duration completely.

Ads can be scheduled to run at preselected times by specifying start and end times.

Community managers/owners will also be able to set the earliest time from the present that scheduled ads can be placed. Some communities may have shorter response times and some longer, so this gives them the opportunity to factor in time for review, reducing the probability of "timed-out" ad reviews.

*For example, if a community sets a window period of 48 hours, it means scheduled ads can only be placed starting 48 hours from the current hour. This gives the review and payment process about 48 hours.*

Payments for scheduled ads should be made before the time they're set to start showing. Otherwise, the ad will not be shown, the time slot will be freed up for other people to use and a moderator may ask for a revision.

Ads with late payments can be renegotiated for use at a later time as scheduled or unscheduled ads.


### Ad Types

The flexibility of JSON-based data makes it easy to develop a wide array of ad types to suit different community types. More ad types will be developed as the project progresses.

#### Native post

A native post is structured just like an ordinary post in a community. The difference is that it is marked "sponsored" and it declines payout.

#### Interactive polls

Interactive polls give community members a chance to share their opinions on a certain topic/question as well as see what other community members think. These will differ from the normal polls that members can make in that they will be displayed on sections set aside for such polls, will be marked "sponsored" and will decline payout.


---

## Links to supporting documentation

- [Development Scope](https://github.com/imwatsi/hivemind/blob/master/docs/native_ads/dev_scope.md)

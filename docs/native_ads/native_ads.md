# Native Ads (Alpha)

*Design specifications for Native Ads feature in communities (WIP)*

---

To aid communities in shaping their attention economies, a feature to manage different types of ad spaces within a community is proposed. This will augment the built-in "promoted" posts feature, giving developers more options to monetize communities on the Steem blockchain.

By putting ad characteristics, purchases and moderation outcomes on the blockchain, we create a transparent, verifiable and auditable environment. Hivemind will synchronize all the ad related activity and presents an easy to use interface for developers to work with, the same as it does with social interactions.

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

## Ad Types

The flexibility of JSON-based data makes it easy to develop a wide array of ad types to suit different community types. More ad types will be developed as the project progresses.

### Native post

A native post is structured just like an ordinary post in a community. The difference is that it is marked "sponsored" and it declines payout.

### Interactive polls

Interactive polls give community members a chance to share their opinions on a certain topic/question as well as see what other community members think. These will differ from the normal polls that members can make in that they will be displayed on sections set aside for such polls, will be marked "sponsored" and will decline payout.

## Ad Payments

**Key considerations:**

- Communities should have various options for using the funds
- Ads that don't get approved by moderation or that are cancelled by the creator should trigger a refund

**Options under investigation:**

- Redistributing the tokens to members, mods, admins and owner
- Having the option to burn
- Donating to charitable causes


---

## Links to supporting documentation

- [Development Scope](https://github.com/imwatsi/hivemind/blob/master/docs/native_ads/dev_scope.md)

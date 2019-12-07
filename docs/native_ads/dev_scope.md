# Development Scope — Native Ads (WIP)

## Blockchain level

*The structure of data that should be posted on the blockchain to make valid ad entries, ad review operations and change a community's ad related settings.*

### Post structures and metadata

Properties for ads will be in the `native_ad` key in a post's JSON metadata.

**Metadata**

- `type`
- `properties`

**Post settings**

- decline payout
- hidden (under investigation, possible universally supported key:value)


### Community settings

Adding an extra `native_ads` key in community settings to hold the following settings (JSON dictionary, preferably):

- `enabled` (boolean)
- `token` (token symbol)
- `burn` (boolean)
- `min_bid` (float)
- `max_time_bid` (integer)
- `max_time_active` (integer)
- `scheduled_ads_delay` (integer)
- `scheduled_ads_timeout` (integer)


### Custom JSON operations

The following `custom_json` operations will need to be implemented.

**Moderators**

- `adApprove`
- `adAllocate`
- `adReject`

**Users**

- `adSubmit`: initial ad submission to a community
- `adBid`: subsequent updates to an ad's bid within a community

## DB level

*Changes made to the database to accommodate ads.*

### hive_ads

The `hive_ads` table hosts primary data for all valid native ads.

```
    post_id integer PRIMARY KEY REFERENCES hive_posts (id),
    type varchar(16) NOT NULL,
    properties text NOT NULL

```

### hive_ads_state

The `hive_ads_state` table maintains the state of ads in various communities

```
    post_id integer NOT NULL REFERENCES hive_ads (post_id),
    community_id integer NOT NULL REFERENCES hive_communities (id),
    time_units integer NOT NULL,
    bid_amount numeric(10,3) NOT NULL,
    bid_token varchar(5) NOT NULL,
    start_time timestamp,
    status smallint NOT NULL DEFAULT 0,
    mod_notes varchar(500) DEFAULT '',
    UNIQUE (post_id, community_id)

```

### hive_ads_settings

The `hive_ads_settings` table hosts ad-related settings/preferences for communities.

```
    community_id integer PRIMARY KEY REFERENCES hive_communities (id),
    token varchar(10) NOT NULL DEFAULT 'STEEM',
    burn boolean NOT NULL DEFAULT false,
    min_bid numeric(10,3),
    max_time_bid integer,
    max_time_active integer

```

### hive_communities (modifications)

A new field for storing a community's ad preference is introduced. A simple boolean, indicating whether or not a community has opted in to using Native Ads.

```
    ads_enabled boolean NOT NULL DEFAULT 0

```
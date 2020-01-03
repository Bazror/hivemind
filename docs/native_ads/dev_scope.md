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

Configurable parameters for communities:

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
    account_id integer NOT NULL REFERENCES hive_accounts (id),
    type varchar(16) NOT NULL,
    properties text NOT NULL

```

### hive_ads_state

The `hive_ads_state` table maintains the state of ads in various communities.

```
    post_id integer NOT NULL REFERENCES hive_ads (post_id),
    account_id integer NOT NULL REFERENCES hive_accounts(id),
    community_id integer NOT NULL REFERENCES hive_communities (id),
    time_units integer NOT NULL,
    bid_amount numeric(10,3) NOT NULL,
    bid_token char(11) NOT NULL,
    start_time timestamp,
    status smallint NOT NULL DEFAULT 0,
    mod_notes varchar(500) DEFAULT '',
    UNIQUE (post_id, community_id)

```

### hive_ads_settings

The `hive_ads_settings` table hosts ad-related settings/preferences for communities.

```
    community_id integer PRIMARY KEY REFERENCES hive_communities (id),
    enabled boolean NOT NULL DEFAULT false,
    token char(11) NOT NULL DEFAULT '@@000000021',
    burn boolean NOT NULL DEFAULT false,
    min_bid numeric(10,3),
    min_time_bid integer,
    max_time_bid integer,
    max_time_active integer,
    scheduled_delay integer NOT NULL DEFAULT 1440,
    scheduled_timeout integer

```

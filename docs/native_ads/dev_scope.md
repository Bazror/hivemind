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

- `ad_approve`
- `ad_allocate`
- `ad_reject`

**Users**

- `ad_submit`
- `ad_bid`

## DB level

*Changes made to the database to accommodate ads.*

...

# Ad Types (WIP)

*Various types of ads and suggested data structures. These will be ported to an appropriate Native Ads section, on a future **Hivemind documentation** website.*

---

# Native Post

*Structured like an ordinary post, but it declines rewards.*

## UI Recommendations

- Mark as "Sponsored"
- Dedicate a high level, high visibility spot

## Suggested Properties

`devices`: *mobile, desktop, all*


## Example JSON Entry

```
{
    "native_ad": {
        "type": "native_post",
        "properties": {
            "devices": "mobile",
        },
        "time_units": 60
    }
}

```

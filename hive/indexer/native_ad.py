"""Handles native ad related ops"""
import json
from hive.db.adapter import Db

DB = Db.instance()

class NativeAd:
    """Handles the validation of ad posts and returns SQL statements"""
    sql_buffer = []

    @classmethod
    def process_ad(cls, values, new=True):
        """Given a cached post insert value set,
        generate SQL statements for valid native ads
        and return."""
        entry = dict(values)
        # check declined status
        if 'is_declined' in entry and entry['is_declined']:
            # check ad metadata
            ad_metadata = cls._check_ad_metadata(json.loads(entry['json']))
            if ad_metadata is not None:
                # build ad post (mandatory)
                post = [
                    ('post_id', entry['post_id']),
                    ('type', ad_metadata['type']),
                    ('properties', json.dumps(ad_metadata['properties']))
                ]
                if new:
                    return cls._insert(post)
                else:
                    # TODO: cls._update(post)
                    pass

        return None

    @classmethod
    def _insert(cls, values):
        return DB.build_insert('hive_ads', values, pk='post_id')

    @staticmethod
    def _check_ad_metadata(data):
        if 'native_ad' in data:
            # check ad metadata integrity (mandatory fields)
            ad_metadata = data['native_ad']
            fields = ['type', 'properties']
            for k in fields:
                if k not in ad_metadata: return None
            # validate all internal data
            if len(ad_metadata['type']) <= 16:
                ad_props = ad_metadata['properties']
                if isinstance(ad_props, dict):   # properties must be in a dict
                    return ad_metadata
        return None

class NativeAdOp:
    """Handles native ad operations. When initializing, pass `ad_action`
        as a dict holding `action(str)`
        and `params(dict)` from payload, e.g. {
            'action': 'adSubmit',
            'params': params
        }"""

    def __init__(self, community_id, post_id, account_id, ad_action):
        """Inits a native ad object and loads initial state."""
        self.community_id = community_id
        self.post_id = post_id
        self.account_id = account_id
        self.action = ad_action['action']
        self.params = ad_action['params']
        self.ad_state = None
        self.ads_context = self._get_ads_context()
        self.is_new_state = False

    def validate_op(self):
        """Validate the native ad op."""
        self._validate_ad_compliance()
        self._validate_ad_states()

    def process(self):
        """Process a validated native ad op."""
        action = self.action
        data = {
            'post_id': self.post_id,
            'account_id': self.account_id,
            'community_id': self.community_id
        }

        for k in self.params.keys():
            data[k] = self.params[k]
        columns = data.keys()
        values = ', '.join([":" + k for k in columns])

        # Native Ads actions
        if action == 'adSubmit':

            if self.is_new_state:
                # use INSERT op
                sql = """INSERT INTO hive_ads_state
                          (%s)
                            VALUES (%s)""" % (columns, values)
                DB.query(sql, **data)
            else:
                # use UPDATE op
                sql = """UPDATE hive_ads_state SET %s
                           WHERE post_id = :post_id
                           AND community_id = :community_id
                           AND account_id = :account_id"""%(
                               ', '.join([k +" = :"+k for k in columns])
                           )
                DB.query(sql, **data)
        else:
            assert not self.is_new_state, 'cannot perform %s operation on non-existant ad state'
            if action == 'adBid':
                pass # TODO
            elif action == 'adApprove':
                pass # TODO
            elif action == 'adAllocate':
                pass # TODO
            elif action == 'adReject':
                pass # TODO

    def _validate_ad_states(self):
        # TODO: implement ordered flow logic
        # ad status versus action
        action = self.action
        self.ad_state = self._get_ad_state()

        if self.ad_state:
            ad_status = self.ad_state['status']
        else:
            ad_status = None

        if action == 'adSubmit':
            # status: None, 0 only
            assert ad_status in [None, 0], 'can only submit ads that are new or in draft status'
        elif action == 'adBid':
            # status: 1 only
            assert ad_status == 1, 'can only bid for ads that are pending review'

    def _validate_ad_compliance(self):
        """Check if operations in ad comply with community level ad settings"""

        self.ads_context = self._get_ads_context()
        accepts_ads = self.ads_context['enabled']
        assert accepts_ads, 'community does not accept ads'

        action = self.action

        if action == 'adSubmit':

            # TODO: investigate expense of "checking if an adBid op effects changes in DB state"
            # reading cost vs simply writing

            # TODO: check bid token compliance

            op_bid_amount = self.params['bid_amount']
            op_time_units = self.params['time_units']

            active_units = self._get_active_time_units()
            min_bid = self.ads_context['min_bid']
            max_time_bid = self.ads_context['max_time_bid']
            max_time_active = self.ads_context['max_time_active']

            if min_bid:
                assert op_bid_amount >= min_bid, (
                    'bid amount (%d) is less than community minimum (%d)'
                    % (op_bid_amount, min_bid))

            if max_time_bid:
                assert op_time_units <= max_time_bid, (
                    'the community accepts a maximum of (%d) time units per bid'
                    % (max_time_bid))

            if max_time_active:
                tot_active_units = active_units + op_time_units
                assert tot_active_units <= max_time_active, (
                    "total active time units (%d) will exceed community's maximum allowed (%d)"
                    % (tot_active_units, max_time_active))

    def _has_ads_settings(self):
        """Check if current community has settings entry."""
        sql = """SELECT 1 FROM hive_ads_settings
                  WHERE community_id = :community_id"""
        return bool(DB.query_one(sql, community_id=self.community_id))

    def _get_ad_state(self):
        """Return the full state of the ad in the current community's context."""
        sql = """SELECT time_units, bid_amount, bid_token, start_time, status, mod_notes
                  FROM hive_ads_state
                    WHERE post_id = :post_id
                    AND community_id = :community_id"""
        _state = DB.query_all(sql, post_id=self.post_id, community_id=self.community_id)
        #_state = DB.query_all(sql, post_id=self.post_id, community_id=self.community_id)
        if _state:
            print(_state)
            result = {
                'time_units': _state[0],
                'bid_amount': _state[1],
                'bid_token': _state[2],
                'start_time': _state[3],
                'status': _state[4],
                'mod_notes': _state[5]
            }
        else:
            # flag new state creation, return None
            # can't create default entry here to avoid:
            # - universal defaults for time_units, bid_amount and bid_token
            # - and possible false concurrent DB lookups
            result = None
            self.is_new_state = True
        return result

    def _get_active_time_units(self):
        """Get the total number of active time units for the transacting account."""
        # for ads with status of approved +
        sql = """SELECT SUM(time_units) FROM hive_ads_state
                  WHERE post_id = :post_id
                  AND account_id = :account_id
                  AND community_id = :community_id
                  AND status > 1"""
        active_units = DB.query_one(
            sql,
            post_id=self.post_id,
            account_id=self.account_id,
            community_id=self.community_id
        )
        # TODO: check null return, replace with zero
        return active_units

    def _get_ads_context(self):
        """Retrieve current community's native ad settings."""

        sql = """SELECT enabled, token, burn, min_bid, max_time_bid, max_time_active
                  FROM hive_ads_settings
                    WHERE community_id = :community_id"""
        ads_prefs = DB.query_row(sql, community_id=self.community_id)

        if ads_prefs:
            result = {
                'enabled': ads_prefs[0],
                'token': ads_prefs[1],
                'burn': ads_prefs[2],
                'min_bid': ads_prefs[3],
                'max_time_bid': ads_prefs[4],
                'max_time_active': ads_prefs[5]
            }
        else:
            # make default entry and return dummy default
            sql = """INSERT INTO hive_ads_settings
                        (community_id)
                        VALUES (:community_id)"""
                        # TODO: investigate INSERT conflict edge cases
            DB.query(sql, community_id=self.community_id)
            result = {
                'enabled': False,
                'token': 'STEEM',
                'burn': False,
                'min_bid': None,
                'max_time_bid': None,
                'max_time_active': None
            }
        return result

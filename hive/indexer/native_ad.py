"""Handles native ad related ops"""

#pylint: disable=too-many-lines

import json
from enum import IntEnum
from hive.db.adapter import Db
from hive.utils.normalize import is_valid_nai

DB = Db.instance()

class Status(IntEnum):
    """Labels for ad status."""
    draft = 0
    submitted = 1
    approved = 2
    funded = 3
    scheduled = 4

class NativeAd:
    """Hosts validation and commmon methods for native ads."""

    @classmethod
    def process_ad(cls, values, new=True):
        """Hooks into cached posts sql building. Given a cached post insert value set,
        generate SQL statements for valid native ads
        and return."""
        entry = dict(values)
        # check declined status
        if 'is_declined' in entry and entry['is_declined']:
            # check ad metadata
            ad_metadata = cls._check_ad_metadata(json.loads(entry['json']))
            if ad_metadata is not None:
                # build ad post
                post = [
                    ('post_id', entry['post_id']),
                    ('type', ad_metadata['type']),
                    ('properties', json.dumps(ad_metadata['properties']))
                ]
                if new:
                    return cls._insert(post)
                else:
                    return cls._update(post)

        return None

    @classmethod
    def get_ad_status(cls, post_id, community_id=None):
        """Returns a list of the current status codes of ad within all communities.
           Can also be used to query for one community, by passing a `community_id`."""
        if community_id:
            sql = """SELECT status FROM hive_ads_state
                      WHERE post_id = :post_id
                      AND community_id = :community_id"""
            _result = DB.query_one(sql, post_id=post_id, community_id=community_id)

            if _result:
                result = int(DB.query_one(sql, post_id=post_id, community_id=community_id))
            else:
                result = None
        else:
            sql = """SELECT status FROM hive_ads_state
                       WHERE post_id = :post_id"""
            _result = DB.query_col(sql, post_id=post_id)

        return result

    @classmethod
    def read_ad_schema(cls, action, params):
        """Validates schema for given native ad operations."""
        if action == 'adSubmit' or action == 'adBid':
            if action == 'adSubmit':
                # time units are compulsory for adSubmit ops
                assert 'time_units' in params, 'missing time units'
                # TODO: validate start_time format
            if 'time_units' in params:
                ad_time = params['time_units']
                assert isinstance(ad_time, int), 'time units must be integers'
                assert ad_time < 2147483647, (
                    'time units must be less than 2147483647')  # SQL max int
            # check bid props
            assert 'bid_amount' in params, 'missing bid amount'
            # TODO: assert bid amount type? (float)
            assert 'bid_token' in params, 'missing bid token'
            # TODO: assert valid token?
        elif action == 'adApprove':
            # TODO: validate??
            pass
        elif action == 'adReject':
            assert 'mod_notes' in params, 'missing moderation notes for adReject op'
            # TODO: enforce a none blank string rule for mod_notes??
        elif action == 'adAllocate':
            assert 'start_time' in params, 'missing start time in adAllocate op'
            # TODO: validate start_time format
        elif action == 'updateAdsSettings':
            assert len(params) > 0, 'no native ad settings provided'
            if 'enabled' in params:
                assert isinstance(params['enabled'], bool), (
                    "the 'enabled' property must be a boolean")
            if 'token' in params:
                # TODO: check if nai is in registry??
                is_nai = is_valid_nai(params['token'])
                if not is_nai:  # TODO: pre-smt handler
                    assert params['token'] in ['STEEM', 'SBD'], (
                        'invalid token entered'
                    )
            if 'burn' in params:
                assert isinstance(params['burn'], bool), (
                    "the 'burn' property must be a boolean"
                )
            if 'min_bid' in params:
                assert isinstance(params['min_bid'], float), (
                    'minimum bid must be a number'
                )
            if 'min_time_bid' in params:
                assert isinstance(params['min_time_bid'], int), (
                    'minimum time units per bid must be an integer'
                )
            if 'max_time_bid' in params:
                assert isinstance(params['max_time_bid'], int), (
                    'maximum time units per bid must be an integer'
                )
            if 'max_time_active' in params:
                assert isinstance(params['max_time_active', int]), (
                    'maximum active time units per account must be an integer'
                )

    @classmethod
    def _insert(cls, values):
        return DB.build_insert('hive_ads', values, pk='post_id')

    @classmethod
    def _update(cls, values):
        return DB.build_update('hive_ads', values, pk='post_id')

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
        self._validate_ad_state()
        self._validate_ad_compliance()

    def process(self):
        """Process a validated native ad op. Assumes op is validated."""
        action = self.action
        data = {
            'post_id': self.post_id,
            'community_id': self.community_id,
            'account_id': self.account_id
        }
        if self.params:
            fields = list(self.params.keys())
            for k in self.params: data[k] = self.params[k]  # add params to final dict

        sql_where = """WHERE post_id = :post_id
                        AND community_id = :community_id
                        AND account_id = :account_id"""

        if action == 'adSubmit':

            if self.is_new_state:
                # use INSERT op
                columns = ', '.join(fields)
                values = ', '.join([":" + k for k in fields])

                sql = """INSERT INTO hive_ads_state (%s)
                            VALUES (%s)""" % (columns, values)
                DB.query(sql, **data)
            else:
                # use UPDATE op
                values = ', '.join([k +" = :"+k for k in fields])
                sql = """UPDATE hive_ads_state SET %s
                           %s""" %(values, sql_where)
                DB.query(sql, **data)

        else:

            assert not self.is_new_state, (
                'cannot perform %s operation on non-existant ad state' % action)

            if action == 'adBid':
                values = ', '.join([k +" = :"+k for k in fields])
                sql = """UPDATE hive_ads_state
                          SET %s
                        %s""" %(values, sql_where)
                DB.query(sql, **data)

            elif action == 'adApprove':
                sql = """UPDATE hive_ads_state
                          SET status = 2
                        %s""" % sql_where
                DB.query(sql, **data)

            elif action == 'adReject':
                sql = """UPDATE hive_ads_state
                          SET status = 0, mod_notes = :mod_notes
                        %s""" % sql_where
                DB.query(sql, **data)

            elif action == 'adAllocate':
                pass # TODO
            elif action == 'adReject':
                pass # TODO

    def _validate_ad_state(self):
        action = self.action
        self.ad_state = self._get_ad_state()

        if self.ad_state:
            ad_status = self.ad_state['status']
        else:
            ad_status = None

        if action == 'adSubmit':
            assert ad_status in [None, Status.draft], (
                'can only submit ads that are new or in draft status')

        assert self.ad_state, (
            'ad not yet submitted to community; cannot perform %s op' % action)
        if action == 'adBid':
            assert ad_status == Status.submitted, 'can only bid for ads that are pending review'
        elif action == 'adApprove':
            assert ad_status == Status.submitted, 'can only approve ads that are pending review'
        elif action == 'adReject':
            assert ad_status == Status.submitted, 'can only reject ads that are pending review'
        elif action == 'adAllocate':
            # TODO: maybe start_time < x mins away?? for corrections/reallocations
            assert ad_status == Status.funded and self.ad_state['start_time'] is None, (
                "can only allocate time to a funded ad that doesn't have a start time set")

    def _validate_ad_compliance(self):
        """Check if operation complies with community level ad settings"""

        self.ads_context = self._get_ads_context()
        accepts_ads = self.ads_context['enabled']
        assert accepts_ads, 'community does not accept ads'

        action = self.action

        if action == 'adSubmit' or action == 'adBid':
            self._check_bid()


    def _check_bid(self):
        """Check if bid token, amount and time units respect community's preferences."""

        op_bid_amount = self.params['bid_amount']
        op_time_units = self.params['time_units']

        min_bid = self.ads_context['min_bid']
        min_time_bid = self.ads_context['min_time_bid']
        max_time_bid = self.ads_context['max_time_bid']
        max_time_active = self.ads_context['max_time_active']

        accepted_token = self.ads_context['token']
        if 'bid_token' in self.params:
            assert self.params['bid_token'] == accepted_token, (
                'token not accepted as payment in community')

        if min_bid:
            if op_bid_amount > 0:  # accomodate zero bids as ad withdrawal
                assert op_bid_amount >= min_bid, (
                    'bid amount (%d) is less than community minimum (%d)'
                    % (op_bid_amount, min_bid))

        if min_time_bid:
            assert op_time_units >= min_time_bid, (
                'the community accepts a minimum of (%d) time units per bid'
                % min_time_bid)

        if max_time_bid:
            assert op_time_units <= max_time_bid, (
                'the community accepts a maximum of (%d) time units per bid'
                % max_time_bid)

        if max_time_active:
            active_units = self._get_active_time_units()
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
        sql = """SELECT time_units, bid_amount, bid_token, start_time, status
                  FROM hive_ads_state
                    WHERE post_id = :post_id
                    AND community_id = :community_id"""
        _state = DB.query_all(sql, post_id=self.post_id, community_id=self.community_id)
        if _state:
            result = {
                'time_units': _state[0],
                'bid_amount': _state[1],
                'bid_token': _state[2],
                'start_time': _state[3],
                'status': _state[4]
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

        sql = """SELECT enabled, token, burn, min_bid,
                        min_time_bid, max_time_bid, max_time_active
                    FROM hive_ads_settings
                    WHERE community_id = :community_id"""
        ads_prefs = DB.query_row(sql, community_id=self.community_id)

        if ads_prefs:
            result = {
                'enabled': ads_prefs[0],
                'token': ads_prefs[1],
                'burn': ads_prefs[2],
                'min_bid': ads_prefs[3],
                'min_time_bid': ads_prefs[4],
                'max_time_bid': ads_prefs[5],
                'max_time_active': ads_prefs[6]
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
                'min_time_bid': None,
                'max_time_bid': None,
                'max_time_active': None
            }
        return result

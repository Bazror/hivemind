"""Handles native ad related ops"""

#pylint: disable=too-many-lines

import json
from enum import IntEnum
from hive.db.adapter import Db

from hive.indexer.notify import Notify
from hive.utils.normalize import is_valid_nai
from hive.utils.normalize import parse_amount
from hive.utils.json import valid_date

DB = Db.instance()

ALLOWED_KEYS = {
    'adSubmit': ['time_units', 'start_time', 'bid_amount', 'bid_token'],
    'adBid': ['time_units', 'start_time', 'bid_amount', 'bid_token'],
    'adApprove': ['start_time', 'mod_notes'],
    'adReject': ['mod_notes'],
    'adFund': ['amount', 'token'],
    'updateAdsSettings': ['enabled', 'token', 'burn', 'min_bid',
                          'min_time_bid', 'max_time_bid', 'max_time_active']
}

REQUIRED_KEYS = {
    'adSubmit': ['time_units', 'bid_amount', 'bid_token'],
    'adBid': ['bid_amount', 'bid_token'],
    'adApprove': ['mod_notes'],
    'adReject': ['mod_notes'],
    'adFund': ['amount', 'token'],
    'updateAdsSettings': []
}

class Status(IntEnum):
    """Labels for ad status."""
    draft = 0
    submitted = 1
    approved = 2
    funded = 3
    scheduled = 4

class NativeAd:
    """Hosts validation and commmon methods for native ads."""

    # one block history of ops
    _block_hist = {}


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

    @classmethod
    def _insert(cls, values):
        return DB.build_insert('hive_ads', values, pk='post_id')

    @classmethod
    def _update(cls, values):
        return DB.build_update('hive_ads', values, pk='post_id')

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
        cls.check_required_keys(action, params.keys())
        cls.check_allowed_keys(action, params.keys())
        if action == 'adSubmit' or action == 'adBid':
            if 'start_time' in params:
                valid_date(params['start_time'])
            if 'time_units' in params:
                ad_time = params['time_units']
                assert isinstance(ad_time, int), 'time units must be integers'
                assert ad_time < 2147483647, (
                    'time units must be less than 2147483647')  # SQL max int
            # TODO: assert bid amount type? (float)
        elif action == 'adApprove':
            if 'start_time' in params:
                valid_date(params['start_time'])
            assert isinstance(params['mod_notes'], str), 'mod notes must be a string'
        elif action == 'adReject':
            assert isinstance(params['mod_notes'], str), 'mod notes must be a string'
            # TODO: enforce a none blank string rule for mod_notes??
        elif action == 'updateAdsSettings':
            assert len(params) > 0, 'no native ad settings provided'
            if 'enabled' in params:
                assert isinstance(params['enabled'], bool), (
                    "the 'enabled' property must be a boolean")
            if 'token' in params:
                # TODO: check if nai is in registry??
                is_nai = is_valid_nai(params['token'])
                if not is_nai:  # TODO: remove pre-smt handler below
                    assert params['token'] in ['STEEM', 'SBD'], (
                        'invalid token entered: %s' % params['token']
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
    def check_allowed_keys(cls, action, provided_keys):
        """Checks for unsupported parameter keys in ad operations."""
        allowed = ALLOWED_KEYS[action]
        unsupported = []
        for k in provided_keys:
            if k not in allowed:
                unsupported.append(k)
        assert len(unsupported) == 0, (
            'unsupported keys provided for %s op: %s' % (action, unsupported))

    @classmethod
    def check_required_keys(cls, action, provided_keys):
        """Check if all required keys are present."""
        required = REQUIRED_KEYS[action]
        missing = []
        for k in required:
            if k not in provided_keys:
                missing.append(k)
        assert len(missing) == 0, (
            'missing keys for %s op: %s' % (action, missing)
        )

    @classmethod
    def check_ad_payment(cls, op, date, num):
        """Triggers an adFund operation for validated Native Ads transfers."""
        memo = op['memo']
        payment = cls._valid_payment(memo)

        if payment:
            amount, token = parse_amount(op['amount'], bypass_nai_lookup=True)
            params = {
                'amount': amount,
                'token': token,
                'to_account': op['to'],
                'community_name': payment['community_name']
            }
            from hive.indexer.accounts import Accounts
            from hive.indexer.posts import Posts

            _post_id = Posts.get_id(op['from'], payment['permlink'])
            assert _post_id, 'post not found: @%s/%s' % (op['from'], payment['permlink'])

            _account_id = Accounts.get_id(op['from'])
            _community_id = payment['community_id']

            ad_op = NativeAdOp(
                _community_id,
                _post_id,
                _account_id,
                {'action': 'adFund',
                 'params': params},
                num
            )
            try:
                ad_op.validate_op()
                ad_op.process()
            except AssertionError as e:
                payload = str(e)
                Notify('error', dst_id=_account_id,
                       when=date, payload=payload).write()

    @classmethod
    def _valid_payment(cls, memo):
        """Checks for valid ad payment memo. Example memo:
            `hna:hive-133333/interesting-promo`"""
        if memo[:4] == "hna:":
            ref = memo[4:].strip()  # strip() to avoid invalidating legitimate payments
            assert ref.count('/') == 1, (
                "invalid ad payment memo; found (%d) / characters instead of 1" % ref.count)
            _values = ref.split('/')
            comm = _values[0].strip()
            link = _values[1].strip()

            from hive.indexer.community import Community
            valid_comm = Community.validated_name(comm)
            assert valid_comm, 'invalid community name entered (%s)' % comm

            comm_id = Community.get_id(comm)
            assert comm_id, 'community not found: %s' % comm

            return {
                'community_id': comm_id,
                'community_name': comm,
                'permlink': link
            }
        return None


    @classmethod
    def update_block_hist(cls, num, community_id, account_id, post_id, action):
        """Maintains a current block history of all native ad ops, to resolve conflicts."""
        if num in cls._block_hist:
            _buffer = cls._block_hist[num]
        else:
            if len(cls._block_hist) > 0:
                # clear previous block from mem
                cls._block_hist.clear()
            _buffer = []

        _buffer.append(
            {
                'community_id': community_id,
                'account_id': account_id,
                'post_id': post_id,
                'action': action
            }
        )

        cls._block_hist[num] = _buffer

    @classmethod
    def check_block_hist(cls, num, community_id, account_id, post_id, action):
        """Check for a matching native ad op in block history."""
        _ref = {
            'community_id': community_id,
            'account_id': account_id,
            'post_id': post_id,
            'action': action
        }
        if num in cls._block_hist:
            hist = cls._block_hist[num]
            for entry in hist:
                if entry == _ref:
                    return True
        return False


class NativeAdOp:
    """Handles native ad operations. When initializing, pass `ad_action`
        as a dict holding `action(str)`
        and `params(dict)` from payload, e.g. {
            'action': 'adSubmit',
            'params': params
        }"""

    def __init__(self, community_id, post_id, account_id, ad_action, block_num):
        """Inits a native ad op object and loads initial state."""
        self.block_num = block_num
        self.community_id = community_id
        self.post_id = post_id
        self.account_id = account_id
        self.action = ad_action['action']
        self.params = ad_action['params']
        self.ad_state = None
        self.ads_context = self._get_ads_context()
        self.is_new_state = False
        self.override_reject = False

    def validate_op(self):
        """Validate the native ad op."""
        self._validate_ad_state()
        self._validate_ad_compliance()
        self._validate_time_ranges()

    def process(self):
        """Process a validated native ad op. Assumes op is validated."""
        # TODO: notify after DB updates
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
                'ad must be submitted to community first, to perform %s operation' % action)

            if action == 'adBid':
                values = ', '.join([k +" = :"+k for k in fields])
                sql = """UPDATE hive_ads_state
                            SET %s
                          %s""" %(values, sql_where)
                DB.query(sql, **data)

            elif action == 'adWithdraw':
                sql = """UPDATE hive_ads_state
                            SET status = 0
                          %s""" % sql_where

            elif action == 'adFund':
                # check if scheduled
                if self.ad_state['start_time']:
                    set_values = 'SET status = 4'
                else:
                    set_values = 'SET status = 3'

                if self.override_reject:
                    set_values += ", mod_notes = ''"

                sql = """UPDATE hive_ads_state
                            %s
                          %s""" %(set_values, sql_where)

            elif action == 'adApprove':
                values = 'status = 2, '.join([k +" = :"+k for k in fields])
                sql = """UPDATE hive_ads_state
                            SET %s
                          %s""" % (values, sql_where)
                DB.query(sql, **data)

            elif action == 'adReject':
                sql = """UPDATE hive_ads_state
                            SET status = 0, mod_notes = :mod_notes
                          %s""" % sql_where
                DB.query(sql, **data)

        # success; update block history
        NativeAd.update_block_hist(
            self.block_num,
            self.community_id,
            self.account_id,
            self.post_id,
            self.action
        )

    def _validate_ad_state(self):
        """Checks the operation against the rules permitted for the ad's current state."""

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
        elif action == 'adWithdraw':
            assert ad_status in [Status.submitted, Status.approved], (
                "can only withdraw submitted or approved ads, not '%s' ads"
                % Status(ad_status).name
            )
        elif action == 'adFund':
            conflict_rej = NativeAd.check_block_hist(
                self.block_num,
                self.community_id,
                self.account_id,
                self.post_id,
                'adReject'
            )
            if conflict_rej and ad_status == Status.draft:
                # override adReject op
                # TODO: notify mod, flag for mod_notes removal
                self.override_reject = True
            else:
                # proceed with normal validation
                assert ad_status == Status.approved, (
                    "you have funded an ad with status '%s'; consider "
                    "contacting the community management to resolve this") % Status(ad_status).name


        elif action == 'adApprove':
            # TODO: don't approve unscheduled ads that don't have a start_time provided
            # TODO: avoid overwrite of customer's start by mod's start_time
            assert ad_status == Status.submitted, 'can only approve ads that are pending review'
            if self.ad_state['start_time']:
                assert 'start_time' not in self.params, (
                    "ad already has a start_time; cannot overwrite a customer's start_time"
                )
            else:
                assert 'start_time' in self.params, (
                    'no start_time provided for unscheduled ad'
                )
        elif action == 'adReject':
            # TODO: check conflict_adfund op, ignore rej op if found, else proceed as usual
            ad_timed_out = self._check_ad_timeout()
            if not ad_timed_out:
                assert ad_status == Status.submitted, 'can only reject ads that are pending review'
        elif action == 'updateAdsSettings':
            pass # TODO: check no active/approved ads for community, if disabling native ads


    def _validate_ad_compliance(self):
        """Check if operation complies with community level ad settings"""

        self.ads_context = self._get_ads_context()
        action = self.action

        if action != 'updateAdsSettings':  # bypass check when updating settings
            accepts_ads = self.ads_context['enabled']
            assert accepts_ads, 'community does not accept ads'

        if action == 'adSubmit' or action == 'adBid':
            self._check_bid()

        if action == 'adFund':
            # TODO: check late payment, if timed-out reject op and advise management contact

            # check symbol
            expected_token = self.ads_context['token']
            assert self.params['token'] == expected_token, (
                'wrong token sent for ad payment; expected %s' % expected_token
            )

            # check payment account
            burn = self.ads_context['burn']
            _to = self.params['to_account']
            _comm = self.params['community_name']
            if burn:
                assert _to == 'null', (
                    'community only accepts burn payments for ads; '
                    'contact community management to resolve the issue.')
            else:
                assert _to == _comm, (
                    'tokens sent to wrong account, expected (@%s)' % _comm)

            # check paid amount
            expected_amount = self.ad_state['bid_amount']
            sent_amount = self.params['amount']
            if sent_amount > expected_amount:
                diff = sent_amount - expected_amount
                # TODO: soft notify for refund of difference
            elif sent_amount < expected_amount:
                og_time_units = self.ad_state['time_units']
                og_amount = self.ad_state['bid_amount']
                pptu = og_amount/og_time_units  # price-per-time-unit
                new_time_units = int(sent_amount/pptu)
                # TODO: reduce time units allocated, soft notify

    def _validate_time_ranges(self):
        """Checks adApprove ops for time slots that overlap with existing approved ads."""

        action = self.action

        if action != 'adApprove':
            return
        time_units = None
        start_time = None

        assert self.ad_state['time_units'], (
            "cannot approve an ad that doesn't have time_units specified")
        time_units = self.ad_state['time_units']

        if 'start_time' in self.params:
            start_time = self.params['start_time']
        else:
            assert self.ad_state['start_time'], (
                "cannot approve an ad that doesn't have start_time specified"
            )
            start_time = self.ad_state['start_time']

        sql = """SELECT 1 FROM hive_ads_state
                    WHERE community_id = :community_id
                    AND status > 1
                    AND tsrange(start_time, start_time
                        + (time_units * interval '1 minute'), '[]')
                    && tsrange(:start_time, :start_time
                        + (:time_units * interval '1 minute'), '[]')"""

        found = bool(DB.query_one(
            sql,
            community_id=self.community_id,
            start_time=start_time,
            time_units=time_units))

        assert not found, 'time slot not available'

    def _check_bid(self):
        """Check if bid token, amount and time units respect community's preferences."""

        op_bid_amount = self.params['bid_amount']
        assert op_bid_amount > 0, 'bid amount must be greater than zero (0)'
        op_time_units = self.params['time_units']
        assert op_time_units > 0, 'time units must be greater than zero (0)'

        min_bid = self.ads_context['min_bid']
        min_time_bid = self.ads_context['min_time_bid']
        max_time_bid = self.ads_context['max_time_bid']
        max_time_active = self.ads_context['max_time_active']

        accepted_token = self.ads_context['token']
        if 'bid_token' in self.params:
            assert self.params['bid_token'] == accepted_token, (
                'token not accepted as payment in community')

        if min_bid:
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

    def _check_ad_timeout(self):
        return False # TODO: check start time vs current time (mind TZ)

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

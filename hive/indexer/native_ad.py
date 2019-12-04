"""Handles native ad related ops"""
import json
from hive.db.adapter import Db

DB = Db.instance()

class NativeAd:
    """Handles the validation of ad posts and returns SQL statements"""
    sql_buffer = []

    def process_ad(self, values, new=True):
        """Given a cached post insert value set,
        generate SQL statements for valid native ads
        and add to sql_buffer"""
        entry = dict(values)
        # check declined status
        if 'is_declined' in entry and entry['is_declined']:
            # check ad metadata
            ad_metadata = self._check_ad_metadata(json.loads(entry['json']))
            if ad_metadata is not None:
                # build ad post (mandatory)
                post = [
                    ('post_id', entry['post_id']),
                    ('type', ad_metadata['type']),
                    ('properties', json.dumps(ad_metadata['properties']))
                ]
                if new:
                    return self._insert(post)
                else:
                    # TODO: self._update(post)
                    pass

        return None

    def _insert(self, values):
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

"""Handles native ad related ops"""
import json
from hive.db.adapter import Db

DB = Db.instance()

class NativeAd:
    """Validate ad posts from cached_post, hook for hive_ads entries"""
    sql_buffer = []

    @classmethod
    def process_ad(cls, values):
        """Given a cached post insert value set,
        generate SQL statements for valid native ads
        and add to sql_buffer"""
        entry = dict(values)
        # check declined status
        if 'is_declined' in entry and entry['is_declined']:
            # check ad metadata
            ad_metadata = cls._check_ad_metadata(json.loads(entry['json']))
            if ad_metadata is not None:
                # build ad post (mandatory)
                post = [
                    ('post_id', entry['post_id']),
                    ('community_id', entry['community_id']),
                    ('type', ad_metadata['type']),
                    ('properties', json.dumps(ad_metadata['properties'])),
                    ('time_units', ad_metadata['time_units'])
                ]
                # optional parameters
                if 'start_time' in ad_metadata:
                    post.append(
                        ('start_time', ad_metadata['start_time'])
                    )
                return cls._insert(post)

        return None

    @classmethod
    def _insert(cls, values):
        return DB.build_insert('hive_ads', values, pk='post_id')

    @staticmethod
    def _check_ad_metadata(data):
        if 'native_ad' in data:
            # check ad metadata integrity (mandatory fields)
            ad_metadata = data['native_ad']
            fields = ['type', 'properties', 'time_units']
            for k in fields:
                if k not in ad_metadata: return None
            # validate properties dict
            ad_props = ad_metadata['properties']
            if isinstance(ad_props, dict):  # properties must be in a dict
                return ad_metadata
        return None

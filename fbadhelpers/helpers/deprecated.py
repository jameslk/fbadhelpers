from typing import Iterable, Mapping, Sequence, Callable

from facebookads import FacebookAdsApi
from facebookads.adobjects.ad import Ad
from facebookads.adobjects.adaccount import AdAccount
from facebookads.adobjects.adcreative import AdCreative
from facebookads.adobjects.adset import AdSet
from facebookads.adobjects.campaign import Campaign

from fbadhelpers.records import ApiRecord
from fbadhelpers.requesters import BatchRequest, request
from fbadhelpers.types import TAccessToken, TBusinessId, TAdAccountId, \
    TCampaignId, TAdSetId, TAdId, TStoryId

def get_saved_audience_map_for_ad_sets(api: ApiRecord, ad_set_ids: Sequence[TAdSetId]):
    """
    Deprecated. This is a hack of Facebook's internal API and should not be relied
    upon.
    """
    return request(api, method='POST', params={
        '_reqName': 'objects:AdsInsightsMetadataNodeDataLoader',
        '_reqSrc': 'FieldValueStore.get>CAMPAIGN',
        'fields': '''["saved_audience"]''',
        'ids': ','.join(ad_set_ids),
        'method': 'get'
    })

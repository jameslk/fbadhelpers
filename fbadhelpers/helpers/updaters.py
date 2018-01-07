from typing import Iterable, Mapping, Sequence, Callable
from urllib.parse import quote

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


def update_ad_sets_by_ids_from_config(
        api: ApiRecord,
        ad_set_ids: Sequence[TAdSetId],
        ad_set_config: Mapping[str, any]
) -> Sequence[bool]:

    requests = []
    for ad_set_id in ad_set_ids:
        ad_set = AdSet(fbid=ad_set_id, api=api.service)
        requests.append(ad_set.api_update(
            params=ad_set_config,
            pending=True
        ))

    return BatchRequest.perform_from_facebook_requests(api, requests)


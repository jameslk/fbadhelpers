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

def copy_ad_set(
        api: ApiRecord,
        ad_set_id: TAdSetId,
        under_campaign_id: TCampaignId,
        copies: int = 1,
        deep_copy: bool = True,
        ad_set_name_generator: Callable[[int], str] = None
) -> Sequence[TAdSetId]:

    # The Python Marketing SDK does not support copies yet, so we will have to roll
    # our own
    # https://github.com/facebook/facebook-python-ads-sdk/issues/363

    batch = BatchRequest(api)

    for copy in range(copies):
        batch.request(
            path=f'/{quote(ad_set_id)}/copies',
            params={
                'campaign_id': under_campaign_id,
                'deep_copy': deep_copy,
                'rename_options': {
                    'rename_suffix': ''
                },
                'status_option': 'PAUSED'
            },
            method='POST'
        )

    responses = batch.perform()

    new_ad_set_ids = [response['copied_adset_id'] for response in responses]

    if ad_set_name_generator:
        rename_requests = []
        for index, new_ad_set_id in enumerate(new_ad_set_ids):
            rename_requests.append(
                AdSet(fbid=new_ad_set_id, api=api.service).api_update(
                    params={
                        AdSet.Field.name: ad_set_name_generator(index)
                    },
                    pending=True
                )
            )

        BatchRequest.perform_from_facebook_requests(api, rename_requests)

    return new_ad_set_ids

from typing import Iterable, Mapping, Sequence, Callable
from urllib.parse import quote

from facebookads import FacebookAdsApi
from facebookads.adobjects.ad import Ad
from facebookads.adobjects.adaccount import AdAccount
from facebookads.adobjects.adcreative import AdCreative
from facebookads.adobjects.adset import AdSet
from facebookads.adobjects.campaign import Campaign
from fbadhelpers.helpers import with_ad_account

from fbadhelpers.records import ApiRecord
from fbadhelpers.requesters import BatchRequest, request
from fbadhelpers.types import TAccessToken, TBusinessId, TAdAccountId, \
    TCampaignId, TAdSetId, TAdId, TStoryId

def create_campaign(api: ApiRecord, name: str, objective: str, is_active: bool = False) -> Campaign:
    # Deprecated method:
    #
    # campaign = Campaign(parent_id=api.ad_account_id, api=api.service)
    #
    # campaign.update({
    #     Campaign.Field.name: name,
    #     Campaign.Field.objective: objective
    # })
    #
    # return campaign.remote_create()

    return with_ad_account(api).create_campaign(
        params={
            Campaign.Field.name: name,
            Campaign.Field.objective: objective,
            Campaign.Field.status: Campaign.Status.active if is_active else Campaign.Status.paused
        }
    )

def create_ad_set_from_config(api: ApiRecord, ad_set_config: Mapping[str, any]) -> AdSet:
    ad_set = AdSet(parent_id=api.ad_account_id, api=api.service)
    ad_set.update(ad_set_config)
    return ad_set.remote_create()

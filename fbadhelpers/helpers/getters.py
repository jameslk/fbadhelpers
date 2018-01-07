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


def get_recent_campaigns(api: ApiRecord, count: int = 10) -> Sequence[Campaign]:
    ad_sets = with_ad_account(api).get_campaigns(
        fields=[
            Campaign.Field.id,
            Campaign.Field.name,
        ]
    )

    return ad_sets[:count]

def get_campaign_by_id(api: ApiRecord, campaign_id: TCampaignId, fields: Iterable[str] = None) -> Campaign:
    return Campaign(fbid=campaign_id, api=api.service).api_get(
        fields=fields or [
            Campaign.Field.name,
            Campaign.Field.status,
            Campaign.Field.start_time,
            Campaign.Field.stop_time,
            Campaign.Field.spend_cap,
        ]
    )

def get_ad_set_by_id(api: ApiRecord, ad_set_id: TAdSetId, fields: Iterable[str] = None) -> AdSet:
    return AdSet(ad_set_id, api=api.service).api_get(fields=fields)

def get_ad_sets_by_campaign_id(api: ApiRecord, campaign_id: TCampaignId, fields: Iterable[str] = None) -> Sequence[AdSet]:
    ad_sets = Campaign(fbid=campaign_id, api=api.service).get_ad_sets(
        fields=fields or [
            AdSet.Field.id,
            AdSet.Field.name,
            AdSet.Field.status,
            AdSet.Field.start_time,
            AdSet.Field.end_time,
        ]
    )

    return [ad_set for ad_set in ad_sets] # Force all ad sets to be fetched

def get_ads_by_ids(api: ApiRecord, ids: Sequence[TAdId], fields: Iterable[str] = None) -> Sequence[Ad]:
    requests = []
    for id in ids:
        requests.append(AdCreative(fbid=id, api=api.service).api_get(
            fields=fields or [],
            pending=True
        ))

    return BatchRequest.perform_from_facebook_requests(api, requests)

def get_ad_creatives_by_ads(api: ApiRecord, ads: Sequence[Ad], fields: Iterable[str] = None) -> Sequence[AdCreative]:
    ad_creative_ids = []
    for ad in ads:
        if Ad.Field.creative not in ad:
            raise RuntimeError('Each ad must contain a creative id to look up a story id')

        ad_creative_ids.append(ad[Ad.Field.creative]['id'])

    requests = []
    for ad_creative_id in ad_creative_ids:
        requests.append(AdCreative(fbid=ad_creative_id, api=api.service).api_get(
            fields=fields or [],
            pending=True
        ))

    return BatchRequest.perform_from_facebook_requests(api, requests)

def get_ads_by_ad_set_id(api: ApiRecord, ad_set_id: TAdSetId, fields: Sequence[str] = None) -> Sequence[Ad]:
    return AdSet(fbid=ad_set_id, api=api.service).get_ads(
        fields=fields or []
    )

def get_ad_ids_by_ad_set_id(api: ApiRecord, ad_set_id: TAdSetId):
    ad_sets = get_ads_by_ad_set_id(api, ad_set_id, [
        AdSet.Field.id
    ])

    return [ad_set[AdSet.Field.id] for ad_set in ad_sets]

def get_ad_set_fields() -> Sequence[str]:
    return [
        field
        for attribute, field in AdSet.Field.__dict__.items()
        if not attribute.startswith('__') # Filter internal attributes
           and not field == AdSet.Field.execution_options # Not supported
           and not field == AdSet.Field.redownload # Not supported
    ]

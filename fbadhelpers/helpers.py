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


def create_api(
        access_token: TAccessToken,
        business_id: TBusinessId,
        ad_account_id: TAdAccountId,
        timezone: str,
        namespace: str
    ) -> ApiRecord:

    return ApiRecord(
        service=FacebookAdsApi.init(access_token=access_token),
        access_token=access_token,
        business_id=business_id,
        ad_account_id='act_' + str(ad_account_id),
        timezone=timezone,
        namespace=namespace
    )

def with_ad_account(api: ApiRecord):
    return AdAccount(fbid=api.ad_account_id, api=api.service)

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

def get_ad_sets_by_campaign_id(api: ApiRecord, campaign_id: TCampaignId) -> Sequence[AdSet]:
    ad_sets = Campaign(fbid=campaign_id, api=api.service).get_ad_sets(
        fields=[
            AdSet.Field.id,
            AdSet.Field.name,
            AdSet.Field.status,
            AdSet.Field.start_time,
            AdSet.Field.end_time,
        ]
    )

    return [ad_set for ad_set in ad_sets] # Force all ad sets to be fetched

def get_saved_audience_map_for_ad_sets(api: ApiRecord, ad_set_ids: Sequence[TAdSetId]):
    return request(api, method='POST', params={
        '_reqName': 'objects:AdsInsightsMetadataNodeDataLoader',
        '_reqSrc': 'FieldValueStore.get>CAMPAIGN',
        'fields': '''["saved_audience"]''',
        'ids': ','.join(ad_set_ids),
        'method': 'get'
    })

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

def get_ad_set_fields() -> Sequence[str]:
    return [
        field
        for attribute, field in AdSet.Field.__dict__.items()
        if not attribute.startswith('__') # Filter internal attributes
           and not field == AdSet.Field.execution_options # Not supported
           and not field == AdSet.Field.redownload # Not supported
    ]

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

def create_mirror_ads(
        api: ApiRecord,
        source_ad_ids: Sequence[TAdId],
        under_ad_set_ids: Sequence[TAdSetId],
        ad_name_generator: Callable[[Ad, TAdSetId], str] = None
    ) -> Mapping[TAdSetId, Sequence[TAdId]]:

    source_ads = get_ads_by_ids(api, source_ad_ids, [
        Ad.Field.name,
        Ad.Field.creative
    ])

    source_ad_creatives = get_ad_creatives_by_ads(api, source_ads, [
        AdCreative.Field.effective_object_story_id,
        AdCreative.Field.instagram_actor_id,
    ])

    mirrored_ad_mapping = {}

    for ad_set_id in under_ad_set_ids:
        new_ad_creatives = _create_mirror_ad_creatives(
            api=api,
            source_ads=source_ads,
            source_ad_creatives=source_ad_creatives
        )

        new_ads = _create_mirror_ads_from_creatives(
            api=api,
            source_ads=source_ads,
            new_ad_creatives=new_ad_creatives,
            under_ad_set_id=ad_set_id,
            ad_name_generator=ad_name_generator
        )

        mirrored_ad_mapping[ad_set_id] = new_ads

    return mirrored_ad_mapping

def _create_mirror_ad_creatives(api: ApiRecord, source_ads: Sequence[Ad], source_ad_creatives: Sequence[AdCreative]):
    new_ad_creative_requests = []

    for index, source_ad in enumerate(source_ads):
        source_ad_creative = source_ad_creatives[index]

        ad_creative_config = {
            AdCreative.Field.object_story_id: source_ad_creative[AdCreative.Field.effective_object_story_id],
        }

        if (AdCreative.Field.instagram_actor_id in source_ad_creative):
            ad_creative_config[AdCreative.Field.instagram_actor_id] = source_ad_creative[AdCreative.Field.instagram_actor_id]

        new_ad_creative_requests.append(with_ad_account(api).create_ad_creative(
            params=ad_creative_config,
            pending=True
        ))

    return BatchRequest.perform_from_facebook_requests(
        api,
        new_ad_creative_requests
    )

def _create_mirror_ads_from_creatives(
        api: ApiRecord,
        source_ads: Sequence[Ad],
        new_ad_creatives: Sequence[AdCreative],
        under_ad_set_id: TAdSetId,
        ad_name_generator: Callable[[Ad, TAdSetId], str] = None
    ):

    new_ad_requests = []

    for index, ad_creative in enumerate(new_ad_creatives):
        source_ad = source_ads[index]
        new_ad_name = ad_name_generator(source_ad, under_ad_set_id) if ad_name_generator else source_ad[Ad.Field.name]

        new_ad_requests.append(with_ad_account(api).create_ad(
            params={
                Ad.Field.adset_id: under_ad_set_id,
                Ad.Field.creative: {
                    'creative_id': ad_creative[AdCreative.Field.id]
                },
                Ad.Field.name: new_ad_name,
                Ad.Field.status: Ad.Status.active
            },
            pending=True
        ))

    return BatchRequest.perform_from_facebook_requests(
        api,
        new_ad_requests
    )

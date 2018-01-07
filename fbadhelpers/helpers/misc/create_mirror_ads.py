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

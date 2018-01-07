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

# https://github.com/facebook/facebook-python-ads-sdk#pre-requisites
def create_app_api(
        app_id: str,
        app_secret: str,
        access_token: TAccessToken,
        business_id: TBusinessId,
        ad_account_id: TAdAccountId,
        timezone: str,
        namespace: str
) -> ApiRecord:

    return ApiRecord(
        service=FacebookAdsApi.init(app_id=app_id, app_secret=app_secret, access_token=access_token),
        access_token=access_token,
        business_id=business_id,
        ad_account_id='act_' + str(ad_account_id),
        timezone=timezone,
        namespace=namespace
    )

def with_ad_account(api: ApiRecord):
    return AdAccount(fbid=api.ad_account_id, api=api.service)

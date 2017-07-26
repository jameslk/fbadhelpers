# from collections import namedtuple
#
# ApiRecord = namedtuple('ApiRecord', [
#     'service',
#     'access_token',
#     'business_id',
#     'ad_account_id',
#     'timezone',
#     'namespace',
# ])
from facebookads import FacebookAdsApi

from fbadhelpers.types import TAccessToken, TBusinessId, TAdAccountId


class ApiRecord:
    service: FacebookAdsApi
    access_token: TAccessToken
    business_id: TBusinessId
    ad_account_id: TAdAccountId
    timezone: str
    namespace: str

    def __init__(
            self,
            service: FacebookAdsApi,
            access_token: TAccessToken,
            business_id: TBusinessId,
            ad_account_id: TAdAccountId,
            timezone: str,
            namespace: str
        ):

        self.service = service
        self.access_token = access_token
        self.business_id = business_id
        self.ad_account_id = ad_account_id
        self.timezone = timezone
        self.namespace = namespace

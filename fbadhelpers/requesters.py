import time as Time
from typing import Mapping, Iterable

from facebookads.api import FacebookAdsApiBatch, FacebookRequest

from fbadhelpers.records import ApiRecord


def request(api: ApiRecord, path: any = None, params: Mapping = None, method: str = 'GET'):
    response = api.service.call(method, path or [], params or {})
    return response.json()

class BatchRequest:
    _api: ApiRecord
    _batch: FacebookAdsApiBatch
    _success_responses = []
    _failure_responses = []

    def __init__(self, api: ApiRecord):
        self._api = api
        self._batch = self._api.service.new_batch()

    def request(self, path: any = None, params: Mapping = None, method: str = 'GET'):
        self._batch.add(
            method=method,
            relative_path=path or [],
            params=params or {},
            success=self._success_handler,
            failure=self._failure_handler
        )

    def add_facebook_request(self, facebook_request: FacebookRequest):
        self._batch.add_request(
            request=facebook_request,
            success=self._success_handler,
            failure=self._failure_handler
        )

    def perform(self):
        if not self._batch:
            return []

        self._success_responses = []
        self._failure_responses = []

        original_batch = self._batch
        self._batch = self._batch.execute()

        if len(self._failure_responses):
            raise Exception('Failed to execute request fully', {
                'requests': original_batch._requests,
                'failures': [response.json() for response in self._failure_responses]
            })

        return self._success_responses

    @classmethod
    def perform_from_facebook_requests(cls, api: ApiRecord, facebook_requests: Iterable[FacebookRequest]):
        batch = cls(api)

        for facebook_request in facebook_requests:
            batch.add_facebook_request(facebook_request)

        return batch.perform()

    def _success_handler(self, response):
        self._success_responses.append(response.json())

    def _failure_handler(self, failure_response):
        self._failure_responses.append(failure_response)

def request_all_pages(api: ApiRecord, next_request_builder, path: any = None, params: Mapping = None, sleep: float = 0.0, method: str = 'GET'):
    response = request(api=api, path=path, params=params, method=method)

    assert 'data' in response, 'No data available from response'
    assert 'paging' in response, 'No paging data available from response'

    data = response['data']

    while 'next' in response['paging']:
        Time.sleep(sleep)

        next_request = {
            'api': api,
            **next_request_builder(response),
        }

        response = request(**next_request)

        assert 'data' in response, 'No data available from paginated response'
        assert 'paging' in response, 'No paging data available from paginated response'

        data = data + response['data']

    return data

def request_all_pages_from_response(api: ApiRecord, response: any, sleep: float = 0.0):
    assert 'data' in response, 'No data available from response'
    assert 'paging' in response, 'No paging data available from response'

    data = response['data']

    while 'next' in response['paging']:
        Time.sleep(sleep)

        response = request(
            api=api,
            path=response['paging']['next']
        )

        assert 'data' in response, 'No data available from paginated response'
        assert 'paging' in response, 'No paging data available from paginated response'

        data = data + response['data']

    return data


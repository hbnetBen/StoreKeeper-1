import json
import re
from collections import OrderedDict

import pytest
from flask import Response
from operator import itemgetter
from pprint import pformat

from app.server import config, app, db
from app.models import User
from app.modules.example_data import ExampleUsers as Users, FilterableDict
from test.e2e.base_database_test import CommonTestWithDatabaseSupport


class InvalidDataFormatException(Exception):
    pass


class SetUpException(Exception):
    pass


class LowLevelCommonApiTest(CommonTestWithDatabaseSupport):
    """
    Super class of API based tests

    Added default `admin` user, added some assert functions and made a test client instance into `self.client`.
    """
    maxDiff = None

    # Pattern for timestamp; e.g: '2015-03-14T07:38:08.430655+00:00'
    __API_TIMESTAMP = re.compile(r'(?P<quote>["\'])\d{4}(-\d{2}){2}T(\d{2}:){2}\d{2}\.\d{6}\+\d{2}:\d{2}["\']')
    # Pattern for timestamp; e.g: 'SKT-12345'
    __API_BARCODE = re.compile(r'(?P<quote>["\'])' + re.escape(config.App.BARCODE_PREFIX) +
                               '[0-9]{%d}' % config.App.BARCODE_NUMBERS + '["\']')

    def setUp(self):
        super().setUp()

        admin = User(username=Users.ADMIN['username'], email=Users.ADMIN['email'], admin=True)
        admin.set_password(Users.ADMIN['password'])
        db.session.add(admin)
        db.session.commit()

        self.client = app.test_client()

    def assertApiRequest(self, command: str, url: str, data: (dict, None)=None,
                         expected_data: (str, list, dict, None)=None, expected_status_codes: (int, list)=200):
        __tracebackhide__ = True
        request = {'command': command, 'url': url, 'data': json.dumps(data)}
        response = self.__call_api(**request)
        if expected_data is not None:
            self.__assert_response_data(expected_data, response, request=request)
        self.__assert_status_code(expected_status_codes, response, request=request)

    def __assert_response_data(self, expected_data: (str, list, dict, None), response: Response, request: dict):
        """
        "request" parameter will be shown on assertion error
        """
        __tracebackhide__ = True
        parsed_data = self.__make_testable_data(self.__get_parsed_response(response.data.decode('utf-8')))
        expected_data = self.__make_testable_data(expected_data)

        try:
            assert expected_data == parsed_data
        except AssertionError as e:
            assert False, '{!s}\n\nrequest={!r}\nresponse={!r}\nstatus_code={}'\
                .format(e, request, parsed_data, response.status_code)

    def __get_parsed_response(self, response_string: str) -> (str, list, dict, None):
        __tracebackhide__ = True
        try:
            data_json = json.loads(response_string)
        except Exception as e:
            assert False, 'Can not parse received data as JSON\n\ndata={!r}\nerror={!r}'.format(response_string, e)
        return data_json

    def __assert_status_code(self, expected_status_codes: (int, list), response: Response, request: dict):
        __tracebackhide__ = True
        if type(expected_status_codes) != list:
            expected_status_codes = [expected_status_codes]
        assert response.status_code in expected_status_codes, \
            'Not expected status code\n\nrequest={!r}\nresponse={!r}'.format(request, response.data.decode('utf-8'))

    def __call_api(self, command: str, data: str, url: str):
        return getattr(self.client, command)('/{!s}/api{!s}'.format(config.App.NAME, url),
                                             content_type='application/json', data=data)

    def __make_testable_data(self, data: (str, list, dict)) -> (str, list, dict):
        __tracebackhide__ = True
        data_type = type(data)
        if not data_type == str:
            data = json.dumps(data, default=str, sort_keys=True)

        data = self.__API_TIMESTAMP.sub('\g<quote><TS>\g<quote>', data)
        data = self.__API_BARCODE.sub('\g<quote><BC>\g<quote>', data)

        if not data_type == str:
            data = json.loads(data, object_pairs_hook=OrderedDict)

        if data and type(data) == list:
            try:
                data = self.__sort_list(data)
            except Exception as e:
                message = 'Response and expected data can be ordered (or have to be contained dicts with \'id\' or ' \
                          '\'name\' keys) when the data is a list'
                if pytest.config.option.verbose:
                    message += '\n    exception={exception!r},\n    data={data}'.format(
                        exception=e,
                        data=pformat(data).replace('\n', '\n{}'.format(' ' * 9))
                    )

                raise InvalidDataFormatException(message)

        return data

    def __sort_list(self, data: list) -> list:
        if type(data[0]) not in {dict, OrderedDict}:
            return sorted(data)

        if 'id' in data[0].keys():
            return sorted(data, key=itemgetter('id'))

        if 'name' in data[0].keys():
            return sorted(data, key=itemgetter('name'))

        raise ValueError()


class CommonApiTest(LowLevelCommonApiTest):
    ENDPOINT = ''
    INIT_PUSH = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.ENDPOINT:
            raise ValueError('ENDPOINT class variable was not set')

    def setUp(self):
        super().setUp()
        self._fill_up(self.INIT_PUSH)

    def assertApiGet(self, id: (int, str, None)=None, data: (dict, FilterableDict, None)=None,
                     endpoint: (str, None)=None, url_suffix: str='',
                     expected_data: (list, dict, None)=None, expected_status_codes: (int, list)=200):
        __tracebackhide__ = True
        self.assertApiRequest('get', self.__get_url(endpoint, id, url_suffix),
                              data=self.__extract_data(data, 'set'),
                              expected_data=self.__extract_data(expected_data, 'get'),
                              expected_status_codes=expected_status_codes)

    def assertApiPost(self, data: (dict, FilterableDict), endpoint: (str, None)=None, url_suffix: str='',
                      expected_data: (str, list, dict, None)=None, expected_status_codes: (int, list)=200):
        __tracebackhide__ = True
        self.assertApiRequest('post', self.__get_url(endpoint, url_suffix=url_suffix),
                              data=self.__extract_data(data, 'set'),
                              expected_data=self.__extract_data(expected_data, 'get'),
                              expected_status_codes=expected_status_codes)

    def assertApiPut(self, id: (int, str), data: (dict, FilterableDict, None)=None, endpoint: (str, None)=None,
                     url_suffix: str='', expected_data: (str, list, dict, None)=None,
                     expected_status_codes: (int, list)=200):
        __tracebackhide__ = True
        self.assertApiRequest('put', self.__get_url(endpoint, id, url_suffix),
                              data=self.__extract_data(data, 'set'),
                              expected_data=self.__extract_data(expected_data, 'get'),
                              expected_status_codes=expected_status_codes)

    def assertApiDelete(self, id: (int, str, None)=None, endpoint: (str, None)=None, url_suffix: str='',
                        expected_data: (str, list, dict, None)=None, expected_status_codes: (int, list)=200):
        __tracebackhide__ = True
        self.assertApiRequest('delete', self.__get_url(endpoint, id, url_suffix),
                              expected_data=self.__extract_data(expected_data, 'get'),
                              expected_status_codes=expected_status_codes)

    def _fill_up(self, list_of_endpoint_and_objects: list):
        __tracebackhide__ = True
        for endpoint, push_objects in list_of_endpoint_and_objects:
            for push_object in push_objects:
                self.__push_for_fill_up(data=push_object, endpoint=endpoint)

    def __push_for_fill_up(self, data: (dict, FilterableDict), endpoint: str):
        __tracebackhide__ = True
        try:
            self.assertApiPost(data=data, endpoint=endpoint)
        except AssertionError as e:
            raise SetUpException(
                'Can not prepare database for tests; {details!r}\n---\n{exception!s}\n---'.format(
                    details={'data': data, 'endpoint': endpoint},
                    exception=e
                )
            )

    def __extract_data(self, data: (dict, FilterableDict, list, None), function: str) -> (list, dict, None):
        if type(data) not in (tuple, list):
            return self.__extract_item(data, function)
        data = [self.__extract_item(item, function) for item in data]
        return data

    def __extract_item(self, item, function: callable):
        if item is None:
            return None

        if isinstance(item, FilterableDict):
            return getattr(item, function)()

        return item

    def __get_url(self, endpoint: (str, None), id: (int, str, None)=None, url_suffix: str=''):
        endpoint = endpoint or self.ENDPOINT

        if id is not None:
            url_suffix = '/{!s}{}'.format(id, url_suffix)

        return '{!s}{}'.format(endpoint, url_suffix)


def append_mandatory_field_tests(item_name: str, base_item: FilterableDict, mandatory_fields: list):
    """
    Append mandatory field tests decorator

    Example:
    >>> @append_mandatory_field_tests(item_name='unit')
    ... class TestUnitWithBrandNewDb(CommonApiTest):
    ...     ENDPOINT = '/unit'
    ...     MANDATORY_FIELDS = {...}
    """
    def decorator(test_class: 'CommonApiTest'):
        if len(mandatory_fields) > 0:
            append_test(test_class, test_can_not_add_xxx_with_missing_one_mandatory_field)
        if len(mandatory_fields) > 1:
            append_test(test_class, test_can_not_add_xxx_with_missing_all_mandatory_fields)
        return test_class

    def append_test(test_class: 'CommonApiTest', func: callable):
        name = func.__name__.replace('xxx', item_name)
        setattr(test_class, name, func)

    def test_can_not_add_xxx_with_missing_one_mandatory_field(self):
        for field_name in mandatory_fields:
            request = base_item.set()
            del request[field_name]
            expected = {'message': {field_name: ['Missing data for required field.']}}
            self.assertApiPost(data=request, expected_data=expected, expected_status_codes=422)

    def test_can_not_add_xxx_with_missing_all_mandatory_fields(self):
        request = base_item.set()
        for field_name in mandatory_fields:
            del request[field_name]
        expected = {'message': dict((field_name, ['Missing data for required field.'])
                                    for field_name in mandatory_fields)}
        self.assertApiPost(data=request, expected_data=expected, expected_status_codes=422)

    return decorator

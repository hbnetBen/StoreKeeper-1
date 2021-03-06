from test.functional.base_doc_test import ApiDocTestCase
from app.modules.api_doc import ApiDoc


class TestApiDoc(ApiDocTestCase):
    def test_minimal_case(self):
        results = ApiDoc.get_doc(title='Test command', command='delete', url_tail='/foo')
        self.assertApiDoc(results, """
        Test command

        **Example request**:

        .. sourcecode:: http

            DELETE /%(app_name)s/api/foo HTTP/1.1
            Host: localhost:8000
            Content-Type: application/json

        **Example response**:

        .. sourcecode:: http

            HTTP/1.0 200 OK
            Content-Type: application/json

            null
        """)

    def test_full_case_with_auto_filled_status_code(self):
        results = ApiDoc.get_doc(title='Test command', command='boo', url_tail='/foobar/2',
                                 request_header={'String': 'Kiwi', 'Number': 111},
                                 request_content_type='banana',
                                 request=[{'apple': 1, 'banana': {'small': 2, 'big': 3}}, {'tree': 1}],
                                 response_header={'String2': 'Coconut', 'Number2': 222},
                                 response_content_type='apple',
                                 response=[{'orange': 4}, 5], response_status=201,
                                 params={'foobar_id': 'Foobar selector'},
                                 status_codes={201: '', 404: 'something is missing'})
        self.assertApiDoc(results, """
        Test command

        :param foobar_id: Foobar selector

        :statuscode 201: no error
        :statuscode 404: something is missing

        **Example request**:

        .. sourcecode:: http

            BOO /%(app_name)s/api/foobar/2 HTTP/1.1
            Host: localhost:8000
            Content-Type: banana
            Number: 111
            String: Kiwi

            [
              {
                "apple": 1,
                "banana": {
                  "big": 3,
                  "small": 2
                }
              },
              {
                "tree": 1
              }
            ]

        **Example response**:

        .. sourcecode:: http

            HTTP/1.0 201 CREATED
            Content-Type: apple
            Number2: 222
            String2: Coconut

            [
              {
                "orange": 4
              },
              5
            ]
        """)

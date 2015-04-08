from app.modules.example_data import ExampleUnits as Units
from test.views.base_api_test import CommonApiTest


class TestUnitWithBrandNewDb(CommonApiTest):
    def test_new_db(self):
        self.assertRequest("get", "/units", expected_data=[])
        self.assertRequest("get", "/units/1", expected_status_codes=404)

    def test_adding_new_units(self):
        self.assertRequest("post", "/units", data=Units.UNIT1.set(), expected_data=Units.UNIT1.get())
        self.assertRequest("post", "/units", data=Units.UNIT2.set(), expected_data=Units.UNIT2.get())

    def test_can_not_add_unit_with_same_name(self):
        self.assertRequest("post", "/units", data=Units.UNIT1.set())
        self.assertRequest("post", "/units", data=Units.UNIT2.set(change={"unit": Units.UNIT1["unit"]}),
                           expected_data={'message': {"unit": ["Already exists."]}},
                           expected_status_codes=422)

    def test_can_not_add_unit_with_missing_name(self):
        self.assertRequest("post", "/units", data={},
                           expected_data={"message": {"unit": ["Missing data for required field."]}},
                           expected_status_codes=422)
        self.assertRequest("post", "/units", data={"unit": ""},
                           expected_data={"message": {"unit": ["Missing data for required field."]}},
                           expected_status_codes=422)


class TestUnitWithPreFilledDb(CommonApiTest):
    def setUp(self):
        super().setUp()
        self.assertRequest("post", "/units", data=Units.UNIT1.set())
        self.assertRequest("post", "/units", data=Units.UNIT2.set())

    def test_list_units(self):
        self.assertRequest("get", "/units", expected_data=[Units.UNIT1.get(),
                                                           Units.UNIT2.get()])

    def test_get_unit(self):
        self.assertRequest("get", "/units/2", expected_data=Units.UNIT2.get())
        self.assertRequest("get", "/units/1", expected_data=Units.UNIT1.get())

    def test_remove_unit(self):
        self.assertRequest("delete", "/units/1")
        self.assertRequest("get", "/units", expected_data=[Units.UNIT2.get()])

    def test_can_not_remove_non_existed_unit(self):
        self.assertRequest("delete", "/units/3", expected_status_codes=404)
        self.assertRequest("get", "/units", expected_data=[Units.UNIT1.get(),
                                                           Units.UNIT2.get()])

    def test_update_unit(self):
        request = Units.UNIT2.set(change={"unit": "foo2"})
        response = Units.UNIT2.get(change={"unit": request["unit"]})

        self.assertRequest("put", "/units/%d" % Units.UNIT2["id"], data=request, expected_data=response)
        self.assertRequest("get", "/units", expected_data=[Units.UNIT1.get(), response])

    def test_update_name_to_name_of_another_unit(self):
        request = Units.UNIT2.set(change={"unit": Units.UNIT1["unit"]})

        self.assertRequest("put", "/units/%d" % Units.UNIT2["id"], data=request, expected_status_codes=422)

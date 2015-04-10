from app.models import StocktakingItem
from app.modules.base_views import BaseModelListView, BaseView
from app.modules.example_data import ExampleStocktakingItems
from app.serializers import StocktakingItemSerializer
from app.server import config, api
from app.views.common import api_func


class StocktakingItemListView(BaseModelListView):
    _model = StocktakingItem
    _serializer = StocktakingItemSerializer
    _deserializer = StocktakingItemSerializer

    @api_func('List stocktaking items', url_tail='stocktaking-items',
              response=[ExampleStocktakingItems.ITEM1.get(), ExampleStocktakingItems.ITEM2.get()])
    def get(self):
        return self._get()

    @api_func('Create stocktaking item', url_tail='stocktaking-items',
              request=ExampleStocktakingItems.ITEM1.set(),
              response=ExampleStocktakingItems.ITEM1.get(),
              status_codes={422: 'there is wrong type / missing field'})
    def post(self):
        return self._post()


class StocktakingItemView(BaseView):
    _model = StocktakingItem
    _serializer = StocktakingItemSerializer
    _deserializer = StocktakingItemSerializer

    @api_func('Get stocktaking item', url_tail='stocktaking-items/1',
              response=ExampleStocktakingItems.ITEM1.get(),
              queries={'id': 'ID of selected stocktaking item for change'},
              status_codes={404: 'there is no item'})
    def get(self, id: int):
        return self._get(id)

    @api_func('Update stocktaking item', url_tail='stocktaking-items/1',
              request=ExampleStocktakingItems.ITEM1.set(),
              response=ExampleStocktakingItems.ITEM1.get(),
              queries={'id': 'ID of selected stocktaking item for change'})
    def put(self, id: int):
        return self._put(id)

    @api_func('Delete stocktaking item', url_tail='stocktaking-items/1',
              response=None,
              queries={'id': 'ID of selected stocktaking item for change'},
              status_codes={404: 'there is no item'})
    def delete(self, id: int):
        return self._delete(id)


api.add_resource(StocktakingItemListView, '/{!s}/api/stocktaking-items'.format(config.App.NAME),
                 endpoint='stocktaking_items')
api.add_resource(StocktakingItemView, '/{!s}/api/stocktaking-items/<int:id>'.format(config.App.NAME),
                 endpoint='stocktaking_item')

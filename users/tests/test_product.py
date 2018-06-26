from products.models import Product

from .utils import TestBase


class ProductTests(TestBase):

    def disable_temporary_test_load_products(self):
        # your product DB must be readonly with data
        obj = Product.objects.all()
        print(str(obj))

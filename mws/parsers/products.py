try:
    import mws
    mws_import = True
except ImportError:
    mws_import = False


from base import BaseElementWrapper, first_element, first_element_or_none, BaseResponseMixin

product_namespaces = {
    'a': 'http://mws.amazonservices.com/schema/Products/2011-10-01',
    'b': 'http://mws.amazonservices.com/schema/Products/2011-10-01/default.xsd'
}


class ProductError(ValueError, BaseElementWrapper):
    """
    Error wrapper for any error returned back for any call to the Products api.
    """

    def __init__(self, element, identifier):
        self.element = element
        self.identifier = identifier
        super(ValueError, self).__init__(self.message)

    @property
    @first_element
    def message(self):
        return self.element.xpath('./a:Message/text()', namespaces=product_namespaces)

    @property
    @first_element
    def code(self):
        return self.element.xpath('./a:Code/text()', namespaces=product_namespaces)

    @property
    @first_element
    def type(self):
        return self.element.xpath('./a:Type/text()', namespaces=product_namespaces)


#######################################
# Get Matching Product For Id Classes #
#######################################


class GetMatchingProductForIdProduct(BaseElementWrapper):

    @property
    @first_element
    def _marketplace_asin(self):
        return self.element.xpath('./a:/Identifiers/a:MarketplaceASIN', namespaces=product_namespaces)

    @property
    @first_element
    def marketplace_id(self):
        return self.element.xpath('./a:Identifiers/a:MarketplaceASIN/a:MarketplaceId/text()', namespaces=product_namespaces)

    @property
    @first_element
    def asin(self):
        return self.element.xpath('./a:Identifiers/a:MarketplaceASIN/a:ASIN/text()', namespaces=product_namespaces)

    @property
    @first_element
    def product_group(self):
        return self.element.xpath('./a:AttributeSets/b:ItemAttributes/b:ProductGroup/text()', namespaces=product_namespaces)

    @property
    @first_element
    def product_type_name(self):
        return self.element.xpath('./a:AttributeSets/b:ItemAttributes/b:ProductTypeName/text()', namespaces=product_namespaces)

    @property
    @first_element
    def title(self):
        return self.element.xpath('./a:AttributeSets/b:ItemAttributes/b:Title/text()', namespaces=product_namespaces)

    @property
    @first_element
    def weight(self):
        return self.element.xpath('./a:AttributeSets/b:ItemAttributes/b:PackageDimensions/b:Weight/text()', namespaces=product_namespaces)

    # ToDo: Add attribute sets and included children

    # ToDo: Add relationships and included children

    @property
    def sales_rankings(self):
        rankings = self.element.xpath('.//a:SalesRankings/a:SalesRank', namespaces=product_namespaces)
        if rankings:
            data = []
            for rank in rankings:
                pcid = first_element_or_none(rank.xpath('./a:ProductCategoryId/text()', namespaces=product_namespaces))
                r = first_element_or_none(rank.xpath('./a:Rank/text()', namespaces=product_namespaces))
                d = (pcid, r)
                data.append(d)
            return data
        return []


class GetMatchingProductForIdResult(BaseElementWrapper):

    @property
    @first_element
    def identifier(self):
        """
        Typically UPC, EAN, or ISBN
        :return:
        """
        return self.element.xpath('./@Id')

    @property
    @first_element
    def id_type(self):
        return self.element.xpath('./@IdType')

    @property
    @first_element
    def status(self):
        return self.element.xpath('./@status')

    @property
    def products(self):
        return [GetMatchingProductForIdProduct(x) for x in self.element.xpath('.//a:Products/a:Product', namespaces=product_namespaces)]

    @property
    def error(self):
        """
        Return mws error instance which can be raised if necessary.

        The reason this method doesn't raise on it's own is because it allows for more
        customization when integrating this class into another module.

        Usage:
            >>> resp = GetMatchingProductForIdResponse.load_from_file('/home/user/my-xml.xml')
            >>> for result in resp.matching_product_for_id_results:
            >>>     if result.error:
            >>>         print result.error.message, result.error.identifier
            >>>         raise result.error
        :return:
        """
        x = first_element_or_none(self.element.xpath('./a:Error', namespaces=product_namespaces))
        if x is None:
            return
        return ProductError(x, self.identifier)

    def __nonzero__(self):
        """
        No products means there was either an error or no match for that particular identifier.

        :return:
        """
        return bool(self.products)


class GetMatchingProductForIdResponse(BaseElementWrapper, BaseResponseMixin):

    @property
    def matching_product_for_id_results(self):
        return [GetMatchingProductForIdResult(x) for x in self.element.xpath('//a:GetMatchingProductForIdResult', namespaces=product_namespaces)]

    @classmethod
    def request(cls, mws_access_key, mws_secret_key, mws_account_id,
                mws_marketplace_id, id_type=None, ids=()):
        """
        Use python amazon mws to request get_matching_product_for_id.

        :param mws_access_key: Your account access key.
        :param mws_secret_key: Your account secret key.
        :param mws_account_id: Your account id.
        :param mws_marketplace_id: Your marketplace id
        :param id_type: One of UPC, EAN, or ISBN.
        :param ids: List of identifiers.
        :return:
        """
        if not mws_import:
            raise ImportError('please install python-amazon-mws to use this method. `pip install python-amazon-mws`')
        products_api = mws.Products(mws_access_key, mws_secret_key, mws_account_id)
        response = products_api.get_matching_product_for_id(mws_marketplace_id, id_type, ids)
        return cls.load(response.original)


############################################
# Get Competitive Pricing For ASIN Classes #
############################################


class CompetitivePriceElement(BaseElementWrapper):

    @property
    def belongs_to_requester(self):
        data = first_element_or_none(self.element.xpath('./@belongsToRequester', namespaces=product_namespaces))
        if not data:
            return
        if data == 'true':
            return True
        else:
            return False

    @property
    @first_element
    def condition(self):
        return self.element.xpath('./@condition', namespaces=product_namespaces)

    @property
    @first_element
    def subcondition(self):
        return self.element.xpath('./@subcondition', namespaces=product_namespaces)

    @property
    @first_element
    def landed_price(self):
        return self.element.xpath('./a:Price/a:LandedPrice/a:Amount/text()', namespaces=product_namespaces)

    @property
    @first_element
    def listing_price(self):
        return self.element.xpath('./a:Price/a:ListingPrice/a:Amount/text()', namespaces=product_namespaces)

    @property
    @first_element
    def shipping(self):
        return self.element.xpath('./a:Price/a:Shipping/a:Amount/text()', namespaces=product_namespaces)


class GetCompetitivePricingForAsinProduct(BaseElementWrapper):

    @property
    @first_element
    def asin(self):
        return self.element.xpath('./a:Identifiers/a:MarketplaceASIN/a:ASIN/text()', namespaces=product_namespaces)

    @property
    @first_element
    def marketplace_id(self):
        return self.element.xpath('./a:Identifiers/a:MarketplaceASIN/a:MarketplaceId/text()', namespaces=product_namespaces)

    @property
    def sales_rankings(self):
        rankings = self.element.xpath('./a:SalesRankings/a:SalesRank', namespaces=product_namespaces)
        ranks = []
        for ranking in rankings:
            pcid = first_element_or_none(ranking.xpath('./a:ProductCategoryId/text()', namespaces=product_namespaces))
            r = first_element_or_none(ranking.xpath('./a:Rank/text()', namespaces=product_namespaces))
            ranks.append((pcid, r))
        return ranks

    @property
    def competitive_prices(self):
        return [CompetitivePriceElement(x) for x in self.element.xpath('./a:CompetitivePricing/a:CompetitivePrices/a:CompetitivePrice', namespaces=product_namespaces)]


class GetCompetitivePricingForAsinResult(BaseElementWrapper):

    @property
    @first_element
    def asin(self):
        return self.element.xpath('./@ASIN')

    @property
    @first_element
    def status(self):
        return self.element.xpath('./@status')

    @property
    def products(self):
        """
        :rtype: list[GetCompetitivePricingForAsinProduct]
        :return:
        """
        return [GetCompetitivePricingForAsinProduct(x) for x in self.element.xpath('.//a:Product', namespaces=product_namespaces)]

    @property
    def error(self):
        """
        Return mws error instance which can be raised if necessary.

        The reason this method doesn't raise on it's own is because it allows for more
        customization when integrating this class into another module.

        Usage:
            >>> resp = GetMatchingProductForIdResponse.load_from_file('/home/user/my-xml.xml')
            >>> for result in resp.matching_product_for_id_results:
            >>>     if result.error:
            >>>         print result.error.message, result.error.identifier
            >>>         raise result.error
        :return:
        """
        x = first_element_or_none(self.element.xpath('./a:Error', namespaces=product_namespaces))
        if x is None:
            return
        return ProductError(x, self.asin)

    def __nonzero__(self):
        """
        No products means there was either an error or no match for that particular identifier.

        :return:
        """
        return bool(self.products)


class GetCompetitivePricingForAsinResponse(BaseElementWrapper, BaseResponseMixin):

    @property
    def competitive_pricing_for_asin_results(self):
        return [GetCompetitivePricingForAsinResult(x) for x in self.element.xpath('.//a:GetCompetitivePricingForASINResult', namespaces=product_namespaces)]

    @classmethod
    def request(cls, mws_access_key, mws_secret_key, mws_account_id,
                mws_marketplace_id, asins=()):
        """
        Use python amazon mws to request get_matching_product_for_id.

        :param mws_access_key: Your account access key.
        :param mws_secret_key: Your account secret key.
        :param mws_account_id: Your account id.
        :param mws_marketplace_id: Your marketplace id
        :param asins: list of asins.
        :return:
        """
        if not mws_import:
            raise ImportError('please install python-amazon-mws to use this method. `pip install python-amazon-mws`')
        products_api = mws.Products(mws_access_key, mws_secret_key, mws_account_id)
        response = products_api.get_competitive_pricing_for_asin(mws_marketplace_id, asins=asins)
        return cls.load(response.original)
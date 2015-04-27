"""
Vendors module documentation (:mod:`sourcing.vendors`)
======================================================
"""

import entityhub.maps
import utils.currency
import utils.config

import os


class VendorBase(object):
    def __init__(self, name, dname, pclass, mappath=None,
                 currency_code=utils.config.BASE_CURRENCY,
                 currency_symbol=utils.config.BASE_CURRENCY_SYMBOL):
        self._name = name
        self._mappath = None
        self._map = None
        self._dname = dname
        self._currency = utils.currency.CurrencyDefinition(currency_code, currency_symbol)
        self._pclass = pclass
        if mappath is not None:
            self.map = mappath

    @property
    def name(self):
        return self._dname

    @property
    def pclass(self):
        return self._pclass

    @property
    def mappath(self):
        return self._mappath

    @property
    def map(self):
        return self._map

    @map.setter
    def map(self, mappath):
        self._mappath = mappath
        if os.path.isfile(mappath) is False:
            if self._pclass == 'electronics':
                import electronics
                electronics.gen_vendor_mapfile(self)
            if self._pclass == 'electronics_pcb':
                import electronics
                electronics.gen_pcb_vendor_mapfile(self)
            else:
                raise AttributeError
        self._map = entityhub.maps.MapFile(mappath)

    @property
    def currency(self):
        return self._currency

    @currency.setter
    def currency(self, currency_def):
        """

        :type currency_def: utils.currency.CurrencyDefinition
        """
        self._currency = currency_def

    def get_vpnos(self, ident):
        return self._map.get_partnos(ident)

    def search_vpnos(self, ident):
        raise NotImplementedError

    def get_vpart(self, vpartno, ident=None):
        raise NotImplementedError

    def get_optimal_pricing(self, ident, rqty):
        candidate_names = self.get_vpnos(ident)
        candidates = [self.get_vpart(x) for x in candidate_names]
        candidates = [x for x in candidates if x.abs_moq <= rqty]
        candidates = [x for x in candidates if x.vqtyavail is None or x.vqtyavail > rqty]
        oqty = rqty
        # vobj, vpno, oqty, nbprice, ubprice, effprice
        if len(candidates) == 0:
            return self, None, None, None, None, None

        selcandidate = candidates[0]
        tcost = self.get_effective_price(selcandidate.get_price(rqty)[0]).extended_price(rqty).native_value

        for candidate in candidates:
            ubprice, nbprice = candidate.get_price(oqty)
            effprice = self.get_effective_price(ubprice)
            ntcost = effprice.extended_price(oqty).native_value
            if ntcost < tcost:
                tcost = ntcost
                selcandidate = candidate

        ubprice, nbprice = selcandidate.get_price(oqty)
        effprice = self.get_effective_price(ubprice)
        urationale = None
        olduprice = None
        if nbprice is not None:
            nubprice, nnbprice = selcandidate.get_price(nbprice.moq)
            neffprice = self.get_effective_price(nubprice)
            ntcost = neffprice.extended_price(nbprice.moq).native_value

            bump_excess_qty = nubprice.moq - rqty

            if ntcost < tcost * 1.4:
                urationale = "TC Increase < 40%"
                oqty = nbprice.moq
                olduprice = ubprice
                ubprice = nubprice
                nbprice = nnbprice
                effprice = neffprice
            elif nubprice.unit_price.native_value < ubprice.unit_price.native_value * 0.5:
                urationale = "UP Decrease > 40%"
                olduprice = ubprice
                oqty = nbprice.moq
                ubprice = nubprice
                nbprice = nnbprice
                effprice = neffprice

        return self, selcandidate.vpno, oqty, nbprice, ubprice, effprice, urationale, olduprice

    def get_effective_price(self, price):
        return price


class VendorPrice(object):
    def __init__(self, moq, price, currency_def):
        self._moq = moq
        self._price = utils.currency.CurrencyValue(price, currency_def)

    @property
    def moq(self):
        return self._moq

    @property
    def unit_price(self):
        return self._price

    def extended_price(self, qty):
        if qty < self.moq:
            raise ValueError
        return utils.currency.CurrencyValue(self.unit_price._val * qty,
                                            self.unit_price._currency_def)


class VendorPartBase(object):
    def __init__(self, ident, vendor):
        self._vpno = None
        self._vqtyavail = None
        self._manufacturer = None
        self._mpartno = None
        self._vpartdesc = None
        self._canonical_repr = ident
        self._prices = []
        self._vendor = vendor

    def add_price(self, price):
        self._prices.append(price)

    @property
    def vpno(self):
        return self._vpno

    @vpno.setter
    def vpno(self, value):
        self._vpno = value

    @property
    def vqtyavail(self):
        return self._vqtyavail

    @vqtyavail.setter
    def vqtyavail(self, value):
        self._vqtyavail = value

    @property
    def manufacturer(self):
        return self._manufacturer

    @manufacturer.setter
    def manufacturer(self, value):
        self._manufacturer = value

    @property
    def mpartno(self):
        return self._mpartno

    @mpartno.setter
    def mpartno(self, value):
        self._mpartno = value

    @property
    def vpartdesc(self):
        return self._vpartdesc

    @vpartdesc.setter
    def vpartdesc(self, value):
        self._vpartdesc = value

    @property
    def ident(self):
        return self._canonical_repr

    @property
    def abs_moq(self):
        if len(self._prices) == 0:
            return 0
        rval = self._prices[0].moq
        for price in self._prices:
            if price.moq < rval:
                rval = price.moq
        return rval

    def get_price(self, qty):
        rprice = None
        rnextprice = None
        for price in self._prices:
            if price.moq <= qty:
                if rprice is not None:
                    if price.moq > rprice.moq:
                        rprice = price
                else:
                    rprice = price
            if price.moq > qty:
                if rnextprice is not None:
                    if price.moq < rnextprice.moq:
                        rnextprice = price
                else:
                    rnextprice = price
        return rprice, rnextprice

    def __repr__(self):
        return self.vpno + ' ' + self._vpartdesc + ' ' + str(self.abs_moq) + '\n'


class VendorElnPartBase(VendorPartBase):
    def __init__(self, ident, vendor):
        super(VendorElnPartBase, self).__init__(ident, vendor)
        self._package = None
        self._datasheet = None

    @property
    def package(self):
        return self._package

    @package.setter
    def package(self, value):
        self._package = value

    @property
    def datasheet(self):
        return self._datasheet

    @datasheet.setter
    def datasheet(self, value):
        self._datasheet = value


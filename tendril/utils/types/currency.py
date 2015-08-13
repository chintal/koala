# Copyright (C) 2015 Chintalagiri Shashank
#
# This file is part of Tendril.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
Currency Types (:mod:`tendril.utils.types.currency`)
====================================================

The :mod:`tendril.utils.types.currency` contains classes which allow for easy
use and manipulation of currency values. The primary focus is on the primary
use cases of Currencies within tendril, i.e. :

- Handling foreign exchange conversions and exchange rates in application code
  without too much fuss.
- Handling currency arithmetic and comparisons.

This module uses a specific `Base Currency`, defined by :const:`tendril.utils.config.BASE_CURRENCY`
and :const:`tendril.utils.config.BASE_CURRENCY_SYMBOL` and available as this
module's :data:`native_currency_defn` module variable. In case this module is
to be used independent of Tendril, at least those configuration options *must* be
defined in :mod:`tendril.utils.config`.

.. rubric:: Module Contents

.. autosummary::

    native_currency_defn
    CurrencyDefinition
    CurrencyValue

.. seealso:: :mod:`tendril.utils.types`, for an overview applicable to most types defined in Tendril.

.. todo:: The core numbers in this module need to switched to :class:`decimal.Decimal`.

"""

from tendril.utils.config import BASE_CURRENCY
from tendril.utils.config import BASE_CURRENCY_SYMBOL

from tendril.utils import www
import urllib
import urllib2
import json
import numbers


class CurrencyDefinition(object):
    """
    Instances of this class define a currency.

    The minimal requirement to define a currency is a :attr:`code`, which
    would usually be a standard internationally recognized currency code.

    In addition to the :attr:`code`, a currency definition also includes
    an optional :attr:`symbol`, which is used to create string representations
    of currency values in that currency. In the absence of a :attr:`symbol`,
    the :attr:`code` is used in it's place.

    Unless otherwise specified during the instantiation of the class,
    the exchange rate is obtained from internet services by the
    :meth:`_get_exchval` method.

    :param code: Standard currency code.
    :param symbol: Symbol to use to represent the currency. Optional.
    :param exchval: Exchange rate to use, if not automatic. Optional.

    """
    def __init__(self, code, symbol=None, exchval=None):
        self._code = code
        self._symbol = symbol
        if exchval is not None:
            self._exchval = exchval
        else:
            self._exchval = self._get_exchval(self._code)

    @property
    def code(self):
        """

        :return: The currency code.
        :rtype: str

        """
        return self._code

    @property
    def symbol(self):
        """

        :return: The currency symbol, or code if no symbol.
        :rtype: str

        """
        if self._symbol is not None:
            return self._symbol
        else:
            return self._code

    @property
    def exchval(self):
        """
        :return: The exchange rate
        :rtype: float

        """
        return self._exchval

    @staticmethod
    def _get_exchval(code):
        """
        Obtains the exchange rate of the currency definition's :attr:`code`
        using the `<http://jsonrates.com>`_ JSON API. The native currency
        is used as the reference.

        :param code: The currency code for which the exchange rate is needed.
        :type code: str
        :return: The exchange rate of currency specified by code vs the native currency.
        :rtype: float

        .. todo:: Switch to currencyrates API instead.

        """

        apiurl = 'http://jsonrates.com/get/?'
        params = {'from': code,
                  'to': BASE_CURRENCY,
                  'apiKey': 'jr-b612b56a860a1e7e6de8863d3379404f'}
        request = urllib2.Request(apiurl + urllib.urlencode(params))
        response = www.urlopen(request)
        data = json.load(response)
        try:
            rate = float(data['rate'])
        except KeyError:
            raise KeyError(code)
        return rate

    def __eq__(self, other):
        """
        Two instances of :class:`CurrencyDefinition` will evaluate to be equal
        only when all three parameters of the instances are equal.
        """
        if self.code != other.code:
            return False
        if self.symbol != other.symbol:
            return False
        if self.exchval != other.exchval:
            return False
        return True

#: The native currency definition used by the module
#:
#: This definition uses the code contained in
#: :const:`tendril.utils.config.BASE_CURRENCY` and symbol
#: :const:`tendril.utils.config.BASE_CURRENCY_SYMBOL`. Application
#: code should import this definition instead of creating new currency
#: definitions whenever one is needed to represent a native currency value.
native_currency_defn = CurrencyDefinition(BASE_CURRENCY, BASE_CURRENCY_SYMBOL)


class CurrencyValue(object):
    """
    Instances of this class define a specific currency value, or a certain
    sum of money.

    The `currency_def` can either be a :class:`CurrencyDefinition` instance
    (recommended), or a string containing the code for the currency.

    :param val: The numerical value.
    :param currency_def: The currency definition within which the value is defined.
    :type currency_def: :class:`CurrencyDefinition` or str

    .. note:: Since the exchange rate is obtained at the instantiation of the
              :class:`CurrencyDefinition`, using a string instead of a
              predefined :class:`CurrencyDefinition` instance may result in
              instances of the same currency, but with different exchange rates.

    :ivar _currency_def: The currency definition of the source value of the instance.
    :ivar _val: The numerical value in the source currency of the instance.

    .. rubric:: Arithmetic Operations

    .. autosummary::

        __add__
        __sub__
        __mul__
        __div__
        __cmp__

    """
    def __init__(self, val, currency_def):
        if isinstance(currency_def, CurrencyDefinition):
            self._currency_def = currency_def
        else:
            self._currency_def = CurrencyDefinition(currency_def)
        self._val = val

    @property
    def native_value(self):
        """
        The numerical value of the currency value in the native currency,
        i.e., that defined by :data:`native_currency_defn`.

        :rtype: float

        """
        return self._val * self._currency_def.exchval

    @property
    def native_string(self):
        """
        The string representation of the currency value in the native currency,
        i.e., that defined by :data:`native_currency_defn`.

        :rtype: str

        """
        return BASE_CURRENCY_SYMBOL + "{0:,.2f}".format(self.native_value)

    @property
    def source_value(self):
        """
        The numerical value of the currency value in the source currency,
        i.e., that defined by :attr:`source_currency`.

        :rtype: float

        """
        return self._val

    @property
    def source_string(self):
        """
        The string representation of the currency value in the source
        currency, i.e., that defined by :attr:`source_currency`.

        :rtype: str

        """
        return self._currency_def.symbol + "{0:,.2f}".format(self._val)

    @property
    def source_currency(self):
        """
        The currency definition of the source currency, i.e, the instance
        variable :data:`_currency_def`.

        :rtype: :class:`CurrencyDefinition`

        """
        return self._currency_def

    def __repr__(self):
        return self.native_string

    def __float__(self):
        return self.native_value

    def __add__(self, other):
        """
        Addition of two :class:`CurrencyValue` instances returns a
        :class:`CurrencyValue` instance with the sum of the two operands,
        with currency conversion applied if necessary.

        If the :attr:`source_currency` of the two operands are equal,
        the result uses the the same :attr:`source_currency`. If not,
        the result is uses the :data:`native_currency_defn` as it's
        :attr:`source_currency`.

        If the other operand is a numerical type and evaluates to 0, this
        object is simply returned unchanged.

        Addition with all other Types / Classes is not supported.

        :rtype: :class:`CurrencyValue`
        """
        if other == 0:
            return self
        if not isinstance(other, CurrencyValue):
            raise NotImplementedError
        if self._currency_def.symbol == other.source_currency.symbol:
            return CurrencyValue(self.source_value + other.source_value, self.source_currency)
        else:
            return CurrencyValue(self.native_value + other.native_value, native_currency_defn)

    def __radd__(self, other):
        if other == 0:
            return self
        else:
            return self.__add__(other)

    def __mul__(self, other):
        """
        Multiplication of one :class:`CurrencyValue` instance with a
        numerical type results in a :class:`CurrencyValue` instance,
        whose value is is the currency type operand's value multiplied
        by the numerical operand's value.

        The :attr:`source_currency` of the returned :class:`CurrencyValue`
        is the same as that of the currency type operand.

        Multiplication with all other Types / Classes is not supported.

        :rtype: :class:`CurrencyValue`
        """
        if isinstance(other, numbers.Number):
            return CurrencyValue(self.source_value * other, self.source_currency)
        else:
            raise NotImplementedError

    def __div__(self, other):
        """
        Division of one :class:`CurrencyValue` instance with a numerical type
        results in a :class:`CurrencyValue` instance, whose value is is the
        currency type operand's value divided by the numerical operand's value.

        The :attr:`source_currency` of the returned :class:`CurrencyValue`
        is the same as that of the currency type operand. In this case, the
        first operand must be a :class:`CurrencyValue`, and not the reverse.

        Division of one :class:`CurrencyValue` instance by another returns a
        numerical value, which is obtained by performing the division with the
        operands' :attr:`native_value`.

        Division with all other Types / Classes is not supported.

        :rtype: :class:`CurrencyValue`
        """
        if isinstance(other, numbers.Number):
            return CurrencyValue(self.source_value / other, self.source_currency)
        elif isinstance(other, CurrencyValue):
            return self.native_value / other.native_value
        else:
            raise NotImplementedError

    def __rmul__(self, other):
        return self.__mul__(other)

    def __sub__(self, other):
        """
        Subtraction of two :class:`CurrencyValue` instances returns a
        :class:`CurrencyValue` instance with the difference of the two
        operands, with currency conversion applied if necessary.

        If :attr:`source_currency` of the two operands are equal,
        the result uses the the same :attr:`source_currency`. If not,
        the result is in the :data:`native_currency_defn`.

        If the other operand is a numerical type and evaluates to 0, this
        object is simply returned unchanged.

        Subtraction with all other Types / Classes is not supported.

        :rtype: :class:`CurrencyValue`
        """
        if other == 0:
            return self
        elif not isinstance(other, CurrencyValue):
            raise NotImplementedError
        else:
            return self.__add__(other.__mul__(-1))

    def __cmp__(self, other):
        """
        The comparison of two :class:`CurrencyValue` instances behaves
        identically to the comparison of the operands' :attr:`native_value`.

        Comparison with all other Types / Classes is not supported.
        """
        if not isinstance(other, CurrencyValue):
            raise NotImplementedError
        if self.native_value == other.native_value:
            return 0
        elif self.native_value < other.native_value:
            return -1
        else:
            return 1

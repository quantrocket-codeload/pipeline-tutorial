# Copyright 2023 QuantRocket LLC - All Rights Reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from zipline.pipeline import EquityPricing, master, sharadar
from zipline.pipeline.factors import AverageDollarVolume, Latest

def TradableStocksUS(market_cap_filter=False):
    """
    Returns a Pipeline filter of tradable stocks, defined as:

    - Common stocks only (no preferred stocks, ADRs, LPs, or ETFs)
    - Primary shares only
    - 200-day average dollar volume >= $2.5M
    - price >= $5
    - 200 continuous days of price and volume.

    If market_cap_filter=True, also requires market cap > $500M.
    """
    # Equities listed as common stock (not preferred stock, ETF, ADR, LP, etc)
    common_stock = master.SecuritiesMaster.usstock_SecurityType2.latest.eq('Common Stock')

    # Filter for primary share equities; primary shares can be identified by a
    # null usstock_PrimaryShareSid field (i.e. no pointer to a primary share)
    is_primary_share = master.SecuritiesMaster.usstock_PrimaryShareSid.latest.isnull()

    # combine the security type filters to begin forming our universe
    tradable_stocks = common_stock & is_primary_share

    # also require high dollar volume
    tradable_stocks = AverageDollarVolume(window_length=200, mask=tradable_stocks) >= 2.5e6

    # also require price > $5. Note that we use Latest(...) instead of EquityPricing.close.latest
    # so that we can pass a mask
    tradable_stocks = Latest(EquityPricing.close, mask=tradable_stocks) > 5

    # also require no missing data for 200 days
    tradable_stocks = EquityPricing.close.all_present(200, mask=tradable_stocks)
    has_volume = EquityPricing.volume.latest > 0
    tradable_stocks = has_volume.all(200, mask=tradable_stocks)

    if market_cap_filter:
        # also require market cap over $500M
        tradable_stocks = Latest([sharadar.Fundamentals.slice(dimension='ARQ', period_offset=0).MARKETCAP], mask=tradable_stocks) >= 500e6

    return tradable_stocks

from moexalgo import Ticker
import unittest
import pandas as pd
import pickle
import json
import random
from datetime import datetime, timedelta
import numpy as np
import xarray as xr
import time
import logging
from io import StringIO
from backtesting import Backtest, Strategy
import moex_utils


class TestMarketDataTransformation(unittest.TestCase):
    csv_data = """tradedate;tradetime;secid;pr_open;pr_high;pr_low;pr_close;vol;val
                  2020-01-03;10:05:00;ABRD;139.0;139.5;138.5;139.0;1.0;1000
                  2020-01-03;10:10:00;ABRD;139.5;140.0;139.0;139.5;2.0;2000
                  2020-01-03;10:15:00;ABRD;139.8;140.3;139.3;139.8;1.5;1500
                  2020-01-04;10:05:00;ABRD;140.0;140.5;139.5;140.0;1.0;1000
                  2020-01-04;10:10:00;ABRD;140.5;141.0;140.0;140.5;2.5;2500
                  2020-01-04;10:15:00;ABRD;140.8;141.3;140.3;140.8;2.0;2000"""

    def test_create_market_candles(self):
        test_df = pd.read_csv(StringIO(self.csv_data), delimiter=';',
                              parse_dates={'datetime': ['tradedate', 'tradetime']})
        candles = moex_utils.create_market_candles(test_df, interval='1D')
        self.assertIsNotNone(candles)
        self.assertEqual(len(candles), 2)
        self.assertIn('vol_lot', candles.columns)

    def test_load_and_transform_data(self):
        with StringIO(self.csv_data) as test_csv:
            dataset, concatenated_df = moex_utils.load_and_transform_data_from_csv(test_csv, interval='1D')
            self.assertIsNotNone(dataset)
            self.assertEqual(len(concatenated_df), 6)

    def test_rolling_vol_field(self):
        fields = ['open', 'high', 'low', 'close', 'vol']
        times = pd.date_range('2023-01-01', periods=10, freq='D')
        assets = ['Asset1', 'Asset2']

        data_values = np.random.rand(len(fields), len(times), len(assets))
        mock_data = xr.DataArray(data_values, coords=[fields, times, assets], dims=["field", "time", "asset"])

        data_with_rolling_vol = moex_utils.add_rolling_vol(mock_data, window=5, new_field_name='vol_rolling_5')

        self.assertIn('vol_rolling_5', data_with_rolling_vol.field.values)
        expected_field_count = len(fields) + 1
        actual_field_count = len(data_with_rolling_vol.field.values)
        self.assertEqual(actual_field_count, expected_field_count)

        new_data = moex_utils.add_is_liquid_field(data_with_rolling_vol, 'vol_rolling_5', new_field_name='is_liquid',
                                                  top_assets=1)
        self.assertIn('is_liquid', new_data.field.values)

    def test_load_lotsize(self):
        lots_data = moex_utils.fetch_secid_lotsize()
        self.assertEqual(len(lots_data), 248)

    def test_calculate_asset_lot_counts(self):
        capital = 10000
        dates = pd.date_range('2020-01-01', periods=3)
        assets = ['ABIO', 'ABRD', 'ACKO']

        prices_data = np.array([[10, 20, 30], [11, 19, 29], [12, 18, 28]])
        prices = xr.DataArray(prices_data, coords=[dates, assets], dims=["time", "asset"])

        lots_data = {'ABIO': 10, 'ABRD': 1, 'ACKO': 1}
        lots = xr.DataArray([lots_data[asset] for asset in assets], coords=[assets], dims=["asset"])

        weights_data = np.array([[0.3, 0.2, 0.5], [0.4, 0.4, 0.2], [0.3, 0.3, 0.4]])
        weights = xr.DataArray(weights_data, coords=[dates, assets], dims=["time", "asset"])

        test_date = '2020-01-01'
        expected_counts = np.array([30, 100, 166])

        result_counts = moex_utils.calculate_asset_lot_counts(capital, prices.sel(time=test_date), lots,
                                                              weights.sel(time=test_date))

        np.testing.assert_array_equal(result_counts, expected_counts)

    def test_main(self):
        import os

        os.environ['API_KEY'] = "default"

        import qnt.stats as qnstats
        def multi_trix_93be5e0266e77532f1(data, params):
            import qnt.ta as qnta
            s_ = qnta.trix(data.sel(field='open'), params[0])
            w_1 = s_.shift(time=params[1]) > s_.shift(time=params[2])
            w_2 = s_.shift(time=params[3]) > s_.shift(time=params[4])
            weights = (w_1 * w_2) * data.sel(field='is_liquid')
            return weights.fillna(0)

        out = 'market_data.nc'
        dims = ['field', 'time', 'asset']
        data = moex_utils.load_data_and_create_data_array(out, dims, dims)

        lots = data.sel(field='vol') / data.sel(field='vol_lot')
        lots_pd = lots.to_pandas()

        w1 = multi_trix_93be5e0266e77532f1(data, [72, 31, 23, 14, 50])
        w2 = multi_trix_93be5e0266e77532f1(data, [70, 33, 23, 26, 64])
        w3 = multi_trix_93be5e0266e77532f1(data, [70, 22, 61, 32, 23])

        # weights = ((w1 + w2) * w1) * w3
        weights = w1 * w3
        weights = weights / weights.sum('asset')  # Нормируем веса акций в портфеле
        weights_ = data.sel(field='is_liquid')

        statistic = qnstats.calc_stat(data, weights)
        statistic_ = qnstats.calc_stat(data, weights_)

        # statistic_pd = statistic.to_pandas()
        # statistic__pd = statistic_.to_pandas()
        #
        # print(statistic.to_pandas().tail(5))
        #
        # result = moex_utils.run_backtest(data, weights)
        # result_ = moex_utils.run_backtest(data, weights_)
        # mean_stats = moex_utils.calculate_mean_statistics(result)
        # mean_stats_ = moex_utils.calculate_mean_statistics(result_)

        # stat_sharpe_ratio_pd = statistic.sel(field='sharpe_ratio').to_pandas()
        # stat_sharpe_ratio_pd_t = statistic.sel(field='sharpe_ratio').to_pandas().T
        # stat_equity = statistic.sel(field='equity').to_pandas()
        # stat_equity_t = statistic.sel(field='equity').to_pandas().T

        lots_data = moex_utils.fetch_secid_lotsize()

        # Update the list comprehension to check if the asset is in lots_data
        lots = xr.DataArray([lots_data[asset] if asset in lots_data else 1 for asset in data.asset.values],
                            coords=[data.asset.values],
                            dims=["asset"])
        capital = 100000
        prices = data.sel(field='open')
        test_date = data.time[-1].values
        result_counts = moex_utils.calculate_asset_lot_counts(capital, prices.sel(time=test_date), lots,
                                                              weights.sel(time=test_date))

        result_counts_pd = result_counts.to_pandas()
        print("")

    def test_run(self):
        r = get_count_lots()
        self.assertIsInstance(r, pd.DataFrame)


def get_count_lots(capital=100000):
    import os

    os.environ['API_KEY'] = "your_api_key_here"
    # os.environ['API_KEY'] = "default"

    import pandas as pd
    import json
    import random
    from datetime import datetime, timedelta
    import numpy as np
    import xarray as xr
    import time
    import moex_utils
    import qnt.ta as qnta

    out = 'market_candles_1D.nc'
    moex_utils.update_market_candles(nc_file_path=out, output_file_path=out)
    dims = ['field', 'time', 'asset']
    data = moex_utils.load_data_and_create_data_array(out, dims, dims)

    # Добавим информацию о среднем объеме торгов в рублях за 45 дней на каждую дату.
    data_with_rolling_vol = moex_utils.add_rolling_vol(data, window=45, new_field_name='vol_rolling_45')

    # На основании объема торгов добавим информацию о ликвидности.
    # В данном случае ликвидность - это 100 самых ликвидных акций на каждую дату.
    data = moex_utils.add_is_liquid_field(data_with_rolling_vol, 'vol_rolling_45', new_field_name='is_liquid',
                                          top_assets=100)

    def get_portfolio_weights(data, params):
        # Вычисляем индикатор TRIX для цен открытия с заданным периодом.
        s_ = qnta.trix(data.sel(field='open'), params[0])

        # Генерируем первый торговый сигнал путем сравнения TRIX с его предыдущим значением.
        w_1 = s_.shift(time=params[1]) > s_.shift(time=params[2])

        # Генерируем второй торговый сигнал аналогичным образом.
        w_2 = s_.shift(time=params[3]) > s_.shift(time=params[4])

        # Комбинируем оба сигнала и фильтруем по ликвидности активов.
        weights = (w_1 * w_2) * data.sel(field='is_liquid')

        # Возвращаем веса, заменяя NaN на 0.
        return weights.fillna(0)

    # Вычисляем веса портфеля для набора параметровов.
    w1 = get_portfolio_weights(data, [72, 31, 23, 14, 50])
    w2 = get_portfolio_weights(data, [70, 22, 61, 32, 23])

    # Комбинируем веса двух стратегий.
    weights = w1 * w2
    weights = weights / weights.sum('asset')  # Нормируем веса акций в портфеле
    # print(weights.to_pandas().tail(5))

    # Загрузим данные о лотах акций с MOEX
    lots_data = moex_utils.fetch_secid_lotsize()

    # Приведём к единому формату. Если акция прошла через делистинг, размер лота будет равен 1
    lots = xr.DataArray([lots_data[asset] if asset in lots_data else 1 for asset in data.asset.values],
                        coords=[data.asset.values],
                        dims=["asset"])

    open_prices = data.sel(field='open')

    result_counts = moex_utils.calculate_asset_lot_counts(capital, open_prices, lots,
                                                          weights)
    result_counts = result_counts.to_pandas()
    return result_counts


if __name__ == '__main__':
    unittest.main()

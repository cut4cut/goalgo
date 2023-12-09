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
import requests


def fetch_new_tradestats(api_dates):
    new_tradestats = pd.DataFrame()
    for date in api_dates:
        print(f"Fetching data for {date}")
        for cursor in range(25):
            url = f'https://iss.moex.com/iss/datashop/algopack/eq/tradestats.csv?date={date}&start={cursor * 1000}&iss.only=data'
            df = pd.read_csv(url, sep=';', skiprows=2)
            new_tradestats = pd.concat([new_tradestats, df])
            if df.shape[0] < 1000:
                break
            time.sleep(0.3)

    return new_tradestats


def load_and_transform_data_from_csv(csv_path, interval='1D'):
    logging.info("Starting data loading and transformation process from CSV.")
    start_time = time.time()

    concatenated_df = pd.read_csv(csv_path, delimiter=';', parse_dates={'datetime': ['tradedate', 'tradetime']})
    data = get_xarray_from_df(concatenated_df, interval=interval)

    end_time = time.time()
    elapsed_time = end_time - start_time
    logging.info(f"Data loading and transformation process from CSV completed in {elapsed_time:.2f} seconds.")

    return data, concatenated_df


def get_xarray_from_df(df, interval='1D'):
    dataframes = {}
    unique_symbols = df['secid'].unique()
    for symbol in unique_symbols:
        symbol_df = df[df['secid'] == symbol]
        market_candles = create_market_candles(symbol_df, interval=interval)
        dataframes[symbol] = market_candles

    dataset = dataframes_to_xarray(dataframes)
    return dataset


def create_market_candles(dataframe, interval='1D'):
    df = dataframe.copy()
    df.set_index('datetime', inplace=True)
    ohlc = df.resample(interval).agg({'pr_open': 'first', 'pr_high': 'max', 'pr_low': 'min', 'pr_close': 'last'})
    volume_lot = df['vol'].resample(interval).sum()
    volume_rub = df['val'].resample(interval).sum()

    market_candles = pd.concat([ohlc, volume_rub, volume_lot], axis=1)
    market_candles.columns = ['open', 'high', 'low', 'close', 'vol', 'vol_lot']

    return market_candles.dropna()


def dataframes_to_xarray(dataframes_dict):
    all_dates = pd.to_datetime([])
    for df in dataframes_dict.values():
        all_dates = all_dates.union(df.index)

    data_arrays = []
    for symbol, df in dataframes_dict.items():
        df_reindexed = df.reindex(all_dates, fill_value=np.nan)
        array = df_reindexed.to_xarray().to_array(dim='field').rename({"index": 'time'})
        array.name = symbol
        data_arrays.append(array)

    dataset = xr.concat(data_arrays, pd.Index(dataframes_dict.keys(), name='asset'))
    return dataset


def update_market_candles(nc_file_path, output_file_path='updated_market_candles.nc'):
    dataarray = xr.open_dataarray(nc_file_path).load()

    last_date = pd.to_datetime(dataarray.time.values[-1]).date()

    current_date = datetime.now().date()
    api_dates = [last_date + timedelta(days=x) for x in range((current_date - last_date).days + 1)]

    new_tradestats = fetch_new_tradestats(api_dates)

    if not new_tradestats.empty:
        new_tradestats['datetime'] = pd.to_datetime(new_tradestats['tradedate'] + ' ' + new_tradestats['tradetime'])
        new_data = get_xarray_from_df(new_tradestats, interval='1D')

        common_assets = np.union1d(dataarray.asset.values, new_data.asset.values)
        aligned_dataarray = dataarray.reindex(asset=common_assets, fill_value=np.nan)
        aligned_new_data = new_data.reindex(asset=common_assets, fill_value=np.nan)

        dataarray_filtered = aligned_dataarray.sel(time=slice(None, last_date - pd.Timedelta(days=1)))

        updated_dataarray = xr.concat([dataarray_filtered, aligned_new_data], dim='time')

        updated_dataarray.to_netcdf(output_file_path)
        print("Dataset updated successfully.")
        return updated_dataarray
    return dataarray


def add_rolling_vol(dataarray, window=30, new_field_name='vol_rolling'):
    if not isinstance(dataarray, xr.DataArray):
        raise ValueError("Input must be an xarray.DataArray")

    try:
        vol = dataarray.sel(field='vol').fillna(0)
    except KeyError:
        raise KeyError("'vol' field not found in the DataArray")

    vol_rolling = vol.rolling({"time": window}).mean()

    rolling_vol_data = xr.DataArray(
        vol_rolling,
        dims=['time', 'asset'],
        coords={'time': dataarray.coords['time'], 'asset': dataarray.coords['asset']},
        name=new_field_name
    )

    rolling_vol_expanded = rolling_vol_data.expand_dims({'field': [new_field_name]})
    rolling_vol_expanded = rolling_vol_expanded.transpose('asset', 'field', 'time')

    data_with_rolling_vol = xr.concat([dataarray, rolling_vol_expanded], dim='field')

    return data_with_rolling_vol


def add_is_liquid_field(data, vol_rolling_name, new_field_name='is_liquid', top_assets=100):
    if vol_rolling_name not in data.field.values:
        raise KeyError(vol_rolling_name + " field not found in the DataArray")

    is_liquid_values = xr.DataArray(
        np.zeros((data.sizes['time'], data.sizes['asset'])),
        dims=['time', 'asset'],
        coords={'time': data.coords['time'], 'asset': data.coords['asset']}
    )

    for time in data.coords['time'].values:
        # Select and prepare data for the given time
        daily_vol_rolling = data.sel(field=vol_rolling_name, time=time).fillna(0)

        # Skip if the total volume is 0
        if daily_vol_rolling.sum() == 0:
            continue

        # Rank the assets based on volume, lower rank means higher volume
        ranks = (-daily_vol_rolling).rank('asset')

        # Select top assets by rank
        top_assets_indices = ranks.where(ranks <= top_assets).dropna('asset').asset.values

        # Mark the top assets as liquid
        is_liquid_values.loc[dict(time=time, asset=top_assets_indices)] = 1

    is_liquid_expanded = is_liquid_values.expand_dims({'field': [new_field_name]})
    is_liquid_expanded = is_liquid_expanded.transpose('asset', 'field', 'time')

    data_with_is_liquid = xr.concat([data, is_liquid_expanded], dim='field')

    return data_with_is_liquid


def load_data_and_create_data_array(filename, dims, transpose_order):
    ds = xr.open_dataset(filename, engine='scipy').load()
    dataset_name = list(ds.data_vars)[0]
    values = ds[dataset_name].transpose(*transpose_order).values
    coords = {dim: ds[dim].values for dim in dims}
    return xr.DataArray(values, dims=dims, coords=coords)


def calculate_mean_statistics(backtest_results):
    stats_to_average = [
        'Exposure Time [%]', 'Equity Final [$]', 'Equity Peak [$]', 'Return [%]',
        'Buy & Hold Return [%]', 'Return (Ann.) [%]', 'Volatility (Ann.) [%]',
        'Sharpe Ratio', 'Sortino Ratio', 'Calmar Ratio', 'Max. Drawdown [%]',
        'Avg. Drawdown [%]', 'Max. Drawdown Duration', 'Avg. Drawdown Duration',
        '# Trades', 'Win Rate [%]', 'Best Trade [%]', 'Worst Trade [%]',
        'Avg. Trade [%]', 'Max. Trade Duration', 'Avg. Trade Duration',
        'Profit Factor', 'Expectancy [%]', 'SQN'
    ]

    total_stats = {stat: 0 for stat in stats_to_average}
    count_stats = {stat: 0 for stat in stats_to_average}  # To count non-NaN entries

    for asset, result in backtest_results.items():
        for stat in stats_to_average:
            value = result['output'][stat]
            if pd.notna(value):
                # Convert timedelta to a numeric value (e.g., days) if necessary
                if isinstance(value, timedelta):
                    total_stats[stat] += value.total_seconds() / (24 * 3600)  # Convert to days
                else:
                    total_stats[stat] += value
                count_stats[stat] += 1

    # Calculate the mean for each statistic
    mean_stats = {stat: (total / count_stats[stat] if count_stats[stat] > 0 else None) for stat, total in
                  total_stats.items()}

    return mean_stats


class CustomStrategy(Strategy):
    asset_weights = None

    def init(self):
        self.cprice = pd.Series(self.data.Close)
        self.index_mapping = {date: idx for idx, date in enumerate(self.asset_weights.index)}

    def next(self):
        current_time = self.data.index[-1]
        if current_time in self.asset_weights.index:
            # current_weight = self.asset_weights.loc[current_time]
            numeric_index = self.index_mapping[current_time]
            previous_day = numeric_index  # open price is for the next day
            if previous_day >= 0:
                previous_weight = self.asset_weights.iloc[previous_day]
                if previous_weight > 0:
                    weight = previous_weight
                else:
                    weight = 0
        else:
            weight = 0

        if weight > 0 and not self.position:
            self.buy()
        elif weight == 0 and self.position:
            self.position.close()


def normalize_weights(weights):
    s = abs(weights).sum()
    if s < 1:
        s = 1
    return weights / s


def run_backtest(data, weights, per_asset=False):
    stats = {}
    if per_asset:
        weights_ = weights
    else:
        weights_ = normalize_weights(weights)

    for asset in data.asset.values:
        asset_df = pd.DataFrame({
            'Open': data.sel(asset=asset, field='open').to_pandas(),
            'High': data.sel(asset=asset, field='high').to_pandas(),
            'Low': data.sel(asset=asset, field='low').to_pandas(),
            'Close': data.sel(asset=asset, field='close').to_pandas(),
            'Volume': data.sel(asset=asset, field='vol').to_pandas()
        })

        asset_weights = weights_.sel(asset=asset).to_pandas()
        if asset_weights.sum() == 0:
            continue
        try:
            stats[asset] = run_asset_backtest(asset_df, asset_weights)
        except Exception as e:
            print(f"Error for asset {asset}: {e}")
            stats[asset] = run_asset_backtest(asset_df, asset_weights)

    return stats


def run_asset_backtest(asset_df, weights_pd):
    CustomStrategy.asset_weights = weights_pd
    asset_df = asset_df.dropna()
    bt = Backtest(asset_df, CustomStrategy, cash=1000000, commission=.002)
    output = bt.run()

    return {
        'output': output,
        'trades': output['_trades'],
        'strategy': output['_strategy']
    }


def calculate_asset_lot_counts(capital, prices, lots, weights):
    # Ensure that the weights are aligned with the prices and lots
    aligned_weights = weights.sel(asset=prices.asset)

    # Calculate capital allocation for each asset
    capital_allocation = capital * aligned_weights

    # Calculate the number of lots to trade for each asset
    # Divide the allocated capital by the product of price and lot size
    lots_counts = np.floor(capital_allocation / (prices * lots))

    return lots_counts


def fetch_secid_lotsize():
    url = "https://iss.moex.com/iss/engines/stock/markets/shares/boards/tqbr/securities.json?iss.only=securities"

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        securities_data = data.get('securities', {}).get('data', [])
        columns = data.get('securities', {}).get('columns', [])

        secid_index = columns.index('SECID') if 'SECID' in columns else None
        lotsize_index = columns.index('LOTSIZE') if 'LOTSIZE' in columns else None

        secid_lotsize = {}
        if secid_index is not None and lotsize_index is not None:
            for item in securities_data:
                secid = item[secid_index]
                lotsize = item[lotsize_index]
                secid_lotsize[secid] = lotsize

        return secid_lotsize
    except requests.RequestException as e:
        return str(e)

# Standard library imports
import json

# Packages imports
import pandas as pd

# Local imports
from provider_iwls.api_connector.iwls_api_connector import IwlsApiConnector

class IwlsApiConnectorWaterLevels(IwlsApiConnector):
    """
    Provider class used to retrieve iwls SurfaceCurrents data.
    """
    def __init__(self):
        super().__init__()

    def _get_station_data(self, station_code: str, start_time: str, end_time: str, csv=False):
        """
        Get water level timeseries (observations, predictions, forecasts) for a single station.

        :param station_code: five digits station identifier (string)
        :param  time_series_code: Code of the timeseries (wlo,wlp, wlf, all); all return (wlo,wlp,wlf) tuple for every timestamps (string)
        :param  start_time: Start time, ISO 8601 format UTC (e.g.: 2019-11-13T19:18:00Z) (string)
        :param  end_time: End time, ISO 8601 format UTC (e.g.: 2019-11-13T19:18:00Z) (string)
        :param  csv:  Write csv file to disk if True, default = False(bool)
        :returns: GeoJSON containing requested station metadata and available water level time series for specified time range (Json)
        """
        time_ranges_strings, metadata, url = super()._get_station_data(station_code, start_time, end_time)

        # Get Observations, Predictions, Forecasts and SPINE
        wlo = self._get_timeseries(url,time_ranges_strings,'wlo')
        wlp = self._get_timeseries(url,time_ranges_strings,'wlp')
        wlf = self._get_timeseries(url,time_ranges_strings,'wlf')
        spine = self._get_timeseries(url,time_ranges_strings,'wlf-spine')

        # Generate csv file if requested
        if csv == True:
            self._station_data_to_csv(station_code, wlo, wlp, wlf, spine)

        # Build Geojson feature for station
        station_geojson = {'type': 'Feature',
                           'id': metadata['code'],
                           "geometry": {
                               "type": "Point",
                               "coordinates":[metadata['longitude'],metadata['latitude']]
                           },
                           'properties':  {
                               'metadata':metadata,
                               'wlo':json.loads(wlo)['value'],
                               'wlp':json.loads(wlp)['value'],
                               'wlf':json.loads(wlf)['value'],
                               'spine':json.loads(spine)['value']
                               }
                           }


        return station_geojson

    def _get_timeseries_by_boundary(self, start_time: str, end_time: str, bbox: list,
                                             limit=10, start_index=0, csv=False):
        """
        Retrieves timeseries data from a bounding box.

        :param  start_time: Start time, ISO 8601 format UTC (e.g.: 2019-11-13T19:18:00Z) (string)
        :param  start_time: Start time, ISO 8601 format UTC (e.g.: 2019-11-13T19:18:00Z) (string)
        :param bbox: bounding box [minx,miny,maxx,maxy] (list)
        :param limit: number of records to return (default 10) (int)
        :param start_index: starting record to return (default 0) (int)
        :param  csv:  Write csv file to disk if True, default = False(bool)
        :returns: dict of 0..n GeoJSON features
        """
        features = []

        within_lat, within_lon, stations_list, end_index, timeseries_data = super()._get_timeseries_by_boundary(
            start_time, end_time,bbox, limit, start_index
        )

        for stn in stations_list.code.iteritems():
            # export to csv if requested
            if csv == True:
                feature = self._get_station_data(stn[1],start_time,end_time,csv=True)
            else:
                feature = self._get_station_data(stn[1],start_time,end_time)

            features.append(feature)

        timeseries_data['features'] = features

        # with open('test.json', 'w', encoding='utf-8') as f:
        #     json.dump(timeseries_data, f, ensure_ascii=False, indent=4)

        return timeseries_data

    def _station_data_to_csv(self,station_code, wlo, wlp, wlf, spine):
        """
        Export single station data to a csv file written in the current folder

        :param station_code: five digits station identifier (string)
        :param  wlo: wlo dataframe generated by _get_station_data (pd.Dataframe)
        :param  wlf: wlf dataframe generated by _get_station_data (pd.Dataframe)
        :param  wlp: wlp dataframe generated by _get_station_data (pd.Dataframe)
        :param  spine: spine dataframe generated by _get_station_data (pd.Dataframe)
        :returns: csv file
        """
        data_dict= {'wlo':wlo,'wlf':wlf,'wlp':wlp,'spine':spine}
        # Format time series into single dataframe 
        series_data = pd.DataFrame()
        for k,v in data_dict.items():
            df_data = pd.read_json(v)
            df_data.index.name = 'datetime'
            df_data = df_data.rename(columns={'value':k})
            series_data = series_data.merge(df_data, how='outer', left_index=True, right_index=True)
            series_data = series_data.sort_index()

        # Export dataframe to csv
        csv_name = f'{station_code}.csv'
        series_data.to_csv(csv_name,float_format='%.3f')

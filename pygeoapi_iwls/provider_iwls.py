# Standard library imports
import requests, json, datetime, os, requests_cache, uuid, dateutil.parser

# Packages imports
import pandas as pd
from pygeoapi.provider.base import BaseProvider
from zipfile import ZipFile

# Local imports
from provider_iwls.iwls import IwlsApiConnector
class ProviderIwls(BaseProvider):
    """
    Provider abstract base class for iwls data
    Used as parent by ProviderIwlsWaterLevels and ProviderIwlsCurrents
    """
    def __init__(self, provider_def):
        """Inherit from parent class"""
        super().__init__(provider_def)

    def _provider_get_station_data(self):
        # Method needs to be implemented by child class
        raise NotImplementedError("Must override _provider_get_station_data")

    def _provider_get_timeseries_by_boundary(self):
        # Method needs to be implemented by child class
        raise NotImplementedError("Must override _provider_get_timeseries_by_boundary")

    def get(self, identifier, **kwargs):
        """
        Get Feature by id
        :param identifier: feature id (int)

        :returns: feature collection
        """
        result = None

        # Establish connection to IWLS API
        api = IwlsApiConnector()
        # Only latest 24h of data available throught get method
        now = datetime.datetime.now()
        tomorrow = now + datetime.timedelta(days=1)
        yesterday = now - datetime.timedelta(days=1)
        end_time = tomorrow.strftime('%Y-%m-%dT%H:%M:%SZ')
        start_time = yesterday.strftime('%Y-%m-%dT%H:%M:%SZ')
        # Pass query to IWLS API
        result = self._provider_get_station_data(identifier,start_time,end_time,api)

        return result

    def query(self, startindex=0, limit=10, resulttype='results',
              bbox=[], datetime_=None, properties=[], sortby=[],
              select_properties=[], skip_geometry=False, q=None, **kwargs):

        """
        Query IWLS
        :param startindex: starting record to return (default 0) (int)
        :param limit: number of records to return (default 10) (int)
        :param resulttype: return results or hit limit (default results)
        :param bbox: bounding box [minx,miny,maxx,maxy] (list)
        :param datetime_: temporal (datestamp or extent) (string)
        :param properties: list of tuples (name, value) (list)
        :param sortby: list of dicts (property, order) (list)
        :param select_properties: list of property names (list)
        :param skip_geometry: bool of whether to skip geometry (default False) (bool)
        :param q: full-text search term(s) (string)
        :returns: dict of 0..n GeoJSON features
        """
        result  = None

        if not bbox:
           bbox = [-180,-90,180,90]

        if not datetime_:
            now = datetime.datetime.now()
            yesterday = now - datetime.timedelta(days=1)
            tomorrow = now + datetime.timedelta(days=1)
            end_time = tomorrow.strftime('%Y-%m-%dT%H:%M:%SZ')
            start_time = yesterday.strftime('%Y-%m-%dT%H:%M:%SZ')
        else:
            start_time = datetime_.split('/')[0]
            end_time = datetime_.split('/')[1]
        # Establish connection to IWLS API
        api = IwlsApiConnector()
        # Pass query to IWLS API
        result = self._provider_get_timeseries_by_boundary(start_time,end_time,bbox,limit,startindex,api)

        return result

class ProviderIwlsWaterLevels(ProviderIwls):
    """
    Provider class for iwls Water Level data
    """
    def __init__(self, provider_def):
        """Inherit from parent class"""
        super().__init__(provider_def)

    def _provider_get_station_data(self,identifier,start_time,end_time,api):
        """
        Used by Get Method
        :param identifier: station ID (int)
        :param  start_time: Start time, ISO 8601 format UTC (e.g.: 2019-11-13T19:18:00Z) (string)
        :param  end_time: End time, ISO 8601 format UTC (e.g.: 2019-11-13T19:18:00Z) (string)
        :param api: api connection to IWLS (IwlsApiConnector)

        :returns: GeoJSON feature
        """
        station_data = api.get_station_data(identifier,start_time,end_time)
        return station_data

    def _provider_get_timeseries_by_boundary(self,start_time,end_time,bbox,limit,startindex,api):
        """
        Used by Query Method
        :param  start_time: Start time, ISO 8601 format UTC (e.g.: 2019-11-13T19:18:00Z) (string)
        :param  start_time: Start time, ISO 8601 format UTC (e.g.: 2019-11-13T19:18:00Z) (string)
        :param bbox: bounding box [minx,miny,maxx,maxy] (list)
        :param limit: number of records to return (default 10) (int)
        :param startindex: starting record to return (default 0) (int)
        :param api: api connection to IWLS (IwlsApiConnector)
        :returns: dict of 0..n GeoJSON features
        """
        timeseries = api.get_timeseries_by_boundary(start_time,end_time,bbox,limit,startindex)
        return timeseries


class ProviderIwlsCurrents(ProviderIwls):
    """
    Provider class for iwls Water Level Currents
    """
    def __init__(self, provider_def):
        """Inherit from parent class"""
        super().__init__(provider_def)

    def _provider_get_station_data(self,identifier,start_time,end_time,api):
        """
        Used by Get Method
        :param identifier: station ID (int)
        :param  start_time: Start time, ISO 8601 format UTC (e.g.: 2019-11-13T19:18:00Z) (string)
        :param  end_time: End time, ISO 8601 format UTC (e.g.: 2019-11-13T19:18:00Z) (string)
        :param api: api connection to IWLS (IwlsApiConnector)
        :returns: GeoJSON feature (json)
        """

        station_data = api.get_station_data(identifier,start_time,end_time, dtype='wcs')
        return station_data

    def _provider_get_timeseries_by_boundary(self,start_time,end_time,bbox,limit,startindex,api):
        """
        Used by Query Method
        :param  start_time: Start time, ISO 8601 format UTC (e.g.: 2019-11-13T19:18:00Z) (string)
        :param  end_time: End time, ISO 8601 format UTC (e.g.: 2019-11-13T19:18:00Z) (string)
        :param bbox: bounding box [minx,miny,maxx,maxy] (list)
        :param limit: number of records to return (default 10) (int)
        :param startindex: starting record to return (default 0) (int)
        :param api: api connection to IWLS (IwlsApiConnector)
        :returns: dict of 0..n GeoJSON features (json)
        """
        timeseries = api.get_timeseries_by_boundary(start_time,end_time,bbox,limit,startindex, dtype='wcs')
        return timeseries

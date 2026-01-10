"""
Data loading utilities for figure generation.
All data loading logic is encapsulated here.
"""

import os
import pickle
import pandas as pd
import geopandas as gpd
from typing import Dict, Tuple, Optional


class DataLoader:
    """Centralized data loader for all figures."""
    
    def __init__(self, data_folder: str = '../../data/Global Data V0.3'):
        """
        Initialize data loader.
        
        Parameters:
        -----------
        data_folder : str
            Path to the data folder
        """
        self.data_folder = data_folder
        self._gdf = None
        self._metadata_dormant = None
        self._metadata_growing = None
        self._event_dormant = None
        self._event_growing = None
        self._growing_months_by_GCIN = None
        self._event_inputs = None
        self._ssi_data = None
    
    def load_all(self):
        """Load all data files."""
        self.load_gdf()
        self.load_metadata()
        self.load_events()
        self.load_growing_months()
        self.load_daily_data()
        self.extract_ssi_data()
    
    def load_gdf(self) -> gpd.GeoDataFrame:
        """Load GeoPackage file."""
        if self._gdf is None:
            self._gdf = gpd.read_file(
                f'{self.data_folder}/Gauged_Catchments_Boundaries.gpkg',
                layer='Gauged_Catchments_Boundaries'
            )
            self._gdf.set_index('GCIN', inplace=True)
        return self._gdf
    
    @property
    def gdf(self) -> gpd.GeoDataFrame:
        """Get GeoDataFrame."""
        if self._gdf is None:
            self.load_gdf()
        return self._gdf
    
    def load_metadata(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Load metadata files."""
        if self._metadata_dormant is None or self._metadata_growing is None:
            self._metadata_dormant = pd.read_csv(
                f'{self.data_folder}/metadata_dormant.csv',
                index_col='GCIN',
                dtype={'GCIN': str}
            )
            self._metadata_growing = pd.read_csv(
                f'{self.data_folder}/metadata_growing.csv',
                index_col='GCIN',
                dtype={'GCIN': str}
            )
        return self._metadata_dormant, self._metadata_growing
    
    @property
    def metadata_dormant(self) -> pd.DataFrame:
        """Get dormant season metadata."""
        if self._metadata_dormant is None:
            self.load_metadata()
        return self._metadata_dormant
    
    @property
    def metadata_growing(self) -> pd.DataFrame:
        """Get growing season metadata."""
        if self._metadata_growing is None:
            self.load_metadata()
        return self._metadata_growing
    
    def load_events(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Load event files."""
        if self._event_dormant is None or self._event_growing is None:
            self._event_dormant = pd.read_csv(
                f'{self.data_folder}/events_dormant.csv',
                index_col='GCIN',
                dtype={'GCIN': str}
            )
            self._event_growing = pd.read_csv(
                f'{self.data_folder}/events_growing.csv',
                index_col='GCIN',
                dtype={'GCIN': str}
            )
        return self._event_dormant, self._event_growing
    
    @property
    def event_dormant(self) -> pd.DataFrame:
        """Get dormant season events."""
        if self._event_dormant is None:
            self.load_events()
        return self._event_dormant
    
    @property
    def event_growing(self) -> pd.DataFrame:
        """Get growing season events."""
        if self._event_growing is None:
            self.load_events()
        return self._event_growing
    
    def load_growing_months(self) -> Dict[str, list]:
        """Load growing months data."""
        if self._growing_months_by_GCIN is None:
            with open(f'{self.data_folder}/growing_months_by_GCIN.pkl', 'rb') as f:
                self._growing_months_by_GCIN = pickle.load(f)
        return self._growing_months_by_GCIN
    
    @property
    def growing_months_by_GCIN(self) -> Dict[str, list]:
        """Get growing months by GCIN."""
        if self._growing_months_by_GCIN is None:
            self.load_growing_months()
        return self._growing_months_by_GCIN
    
    def load_daily_data(self) -> Dict[str, pd.DataFrame]:
        """Load all daily data files."""
        if self._event_inputs is None:
            self._event_inputs = {}
            daily_folder = f'{self.data_folder}/daily_data/observations'
            for filename in os.listdir(daily_folder):
                if filename.endswith('.csv'):
                    file_path = os.path.join(daily_folder, filename)
                    df = pd.read_csv(file_path, index_col='date')
                    gcin = filename.split('.')[0]
                    self._event_inputs[gcin] = df
        return self._event_inputs
    
    @property
    def event_inputs(self) -> Dict[str, pd.DataFrame]:
        """Get daily event inputs."""
        if self._event_inputs is None:
            self.load_daily_data()
        return self._event_inputs
    
    def extract_ssi_data(self, sm_col: str = 'soil_saturation_index') -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Extract seasonal SSI data.
        
        Returns:
        --------
        Tuple of (dormant_ssi, growing_ssi, all_ssi)
        """
        if self._ssi_data is None:
            growing_months = self.growing_months_by_GCIN
            event_inputs = self.event_inputs
            
            dormant_sm_d_list = []
            growing_sm_d_list = []
            all_sm_d_list = []
            
            for gcin, df in event_inputs.items():
                if gcin not in growing_months:
                    continue
                
                growing_months_list = growing_months[gcin]
                
                if not isinstance(df.index, pd.DatetimeIndex):
                    df.index = pd.to_datetime(df.index)
                
                df['month'] = df.index.month
                growing_mask = df['month'].isin(growing_months_list)
                dormant_mask = ~growing_mask
                
                growing_sm_d = df.loc[growing_mask, sm_col].dropna()
                dormant_sm_d = df.loc[dormant_mask, sm_col].dropna()
                all_sm_d = df[sm_col].dropna()
                
                dormant_sm_d_list.append(dormant_sm_d)
                growing_sm_d_list.append(growing_sm_d)
                all_sm_d_list.append(all_sm_d)
            
            dormant_ssi = pd.concat(dormant_sm_d_list, ignore_index=True)
            growing_ssi = pd.concat(growing_sm_d_list, ignore_index=True)
            all_ssi = pd.concat(all_sm_d_list, ignore_index=True)
            
            self._ssi_data = (dormant_ssi, growing_ssi, all_ssi)
        
        return self._ssi_data
    
    @property
    def ssi_data(self) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Get SSI data (dormant, growing, all)."""
        if self._ssi_data is None:
            self.extract_ssi_data()
        return self._ssi_data


# Global data loader instance (lazy loading)
_global_loader: Optional[DataLoader] = None


def get_data_loader(data_folder: str = '../../data/Global Data V0.3') -> DataLoader:
    """Get or create global data loader instance."""
    global _global_loader
    if _global_loader is None or _global_loader.data_folder != data_folder:
        _global_loader = DataLoader(data_folder)
    return _global_loader


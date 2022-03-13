import yfinance as yf
import pandas as pd
import numpy as np
import datetime as DT
import sys
import plotly

class querySplitter:
    """
    Represents a query using a list of symbols. Facilitate extraction of different data fields and symbols.
    Aligns time axes
    """
    def __init__(self, tickerlist = None, yearsback = 2, data_dic = None, get_infos = False):
        if data_dic is not None:
            self.data_dic = data_dic
        else:
            rawquery = self._make_query(tickerlist, yearsback)
            self._populate_data(rawquery)

        self._populate_symbols()
        self._populate_fields()
        self._set_dateix()

        if get_infos:
            self._get_infos()

    def from_symbolsubset(self, symbols):
        """
        Obtain new querySplitter from subset of the symbols in self. This should be used for subsetting, instead of subsetting at the plot level.
        """
        if not isinstance(symbols, (tuple, list)):
            symbols = [symbols]

        data_dic_subset = {}
        for sym in symbols:
            data_dic_subset[sym] = self.data_dic[sym]

        return querySplitter(data_dic = data_dic_subset)

    def from_timerange(self, start = None, end = None):
        """
        Return new querySplitter by subsetting data by range of dates
        """
        start = self.dateix[0] if start is None else start
        end = self.dateix[-1] if end is None else end

        data_dic_subset = {}
        for sym in self.data_dic:
            data_dic_subset[sym] = self.data_dic[sym].from_timerange(start, end)

        return querySplitter(data_dic = data_dic_subset)

    def _make_query(self, tickerlist, yearsback):
        """
        Internal function to effectively extract data from yahoo finance
        """
        heute = DT.datetime.today()
        querydays = yearsback * 356
        jahr = heute - DT.timedelta(days = querydays)
        rawquery = yf.download(tickerlist, start = jahr, end = heute)
        return rawquery

    def _get_infos(self):
        """
        Get company metadata
        """
        self.metadata = metaData(self.syms)

    def _populate_symbols(self):
        """
        Populate list of the contained symbols
        """
        self.syms = list(self.data_dic.keys())

    def _set_dateix(self):
        """
        Set the date index for the entire object
        """
        self.dateix = self.data_dic[self.syms[0]].df.index

    def _populate_fields(self):
        """
        Get list of the contained data fields from the query
        """
        column_list = []
        for key in self.data_dic:
            column_list.extend(list(self.data_dic[key].columns))

        self.column_list = list(set(column_list))

    def _populate_data(self, rawquery):
        """
        Parse raw yf query into dictionary
        """
        self.data_dic = {}
        drop_ix = rawquery.apply(lambda x: x.isnull().any(), axis = 1)
        rawquery = rawquery.loc[~drop_ix, :]
        self.syms = rawquery.columns.get_level_values(1)
        for sym in self.syms:
            col_ix = rawquery.columns.get_level_values(1) == sym
            tmp_df = rawquery.loc[:, col_ix]
            self.data_dic[sym] = querySym(tmp_df.droplevel(1, axis = 1), sym)

    def __len__(self):
        """
        Number of symbols
        """
        return len(self.data_dic)

    def __getitem__(self, key):
        """
        Intended to return a querySym for a symbol
        """
        return self.data_dic[key]

    def get_field(self, cname = 'Close'):
        """
        Get dataframe that contains all the values for a given field for all sym
        """
        col_dic = {}
        for key in self.data_dic:
            col_dic[key] = self.data_dic[key][cname].values

        return pd.DataFrame(col_dic)

    def __repr__(self):
        return f"{type(self).__name__}(symbols={[key for key in self.data_dic.keys()]}"

    def get_tracelist(self, yval = 'Close'):
        """
        Get the list of traces that can be fed to the data attribute of figure
        """
        return [self.data_dic[element].get_trace(yval) for element in self.data_dic]

    def get_ratio(self, sym1, sym2):
        """
        Return querySym that represents ratio between 2 symbols in self
        """
        return self[sym1] / self[sym2]

    def get_tracelist_candlestick(self):
        """
        Get the list of traces from all the candlestick plots
        """
        tracelist = [self.data_dic[element].get_trace_candlestick() for element in self.data_dic]
        tracelist = [e for sublist in tracelist for e in sublist]
        return tracelist

    @property
    def dateindex(self):
        """
        Extract index from internal dataframe
        """
        return self.dateix

########################################################################################################
########################################################################################################
class querySym:
    """
    Class that represents a single symbol taken from yf
    """
    def __init__(self, ss_df, sym, norm = True):
        self.df = ss_df
        self.sym = sym
        self.norm = norm

    def __len__(self):
        """
        Number of timepoints
        """
        return self.df.shape[0]

    def __getitem__(self, key):
        """
        Get a column from the internal df, option to normalize
        """
        if self.norm:
            tmp = self.df[key]
            tmp = (tmp - tmp.min()) / (tmp.max() - tmp.min())
            tmp = tmp - tmp[0]
            return tmp
        else:
            return self.df[key]

    def __repr__(self):
        return f"{type(self).__name__}(sym={self.sym})"

    def __truediv__(self, other):
        """
        Returns querySym for one symbol ratioed over another
        """
        return querySym(self.df / other.df, sym = ":".join([self.sym, other.sym]), norm = False)

    def get_trace(self, yval = 'Close'):
        """
        Get a trace for a normal lineplot for a given column in df.
        Note that use of __getitem__ allows extraction of normalized parameters.
        """
        trace = {'type': 'scatter',
                 'mode': 'lines',
                 'x': self.df.index,
                 'y': self[yval],
                 'name': self.sym}
        return trace

    def get_trace_candlestick(self):
        """
        Get trace to plot candlestick plot.
        Does not normalize values because it is difficult to plot multiple candlesticks on same plot anyways.
        """
        a, b, c = np.random.randint(255), np.random.randint(255), np.random.randint(255)
        a_, b_, c_ = (a + 120) % 256, (b + 120) % 256, (c + 120) % 256
        dec_col = f'rgba({a}, {b}, {c}, 0.2)'
        inc_col = f'rgba({a_}, {b_}, {c_}, 0.2)'
        trace_cs = {'type': 'candlestick',
                    'open': self.df['Open'],
                    'close': self.df['Close'],
                    'low': self.df['Low'],
                    'high': self.df['High'],
                    'x': self.df.index,
                    'name': self.sym,
                    'decreasing_line_color': dec_col,
                    'increasing_line_color': inc_col}

        rolling_mean_200 = self.df['Close'].rolling(200).mean()
        trace_ra = {'type': 'scatter',
                    'mode': 'lines',
                    'x': self.df.index,
                    'y': rolling_mean_200,
                    'name': self.sym,
                    'fillcolor': inc_col}


        return trace_cs, trace_ra

    def from_timerange(self, start = None, end = None):
        """
        Return new querySym by subsetting data by range of dates
        """
        start = self.dateix[0] if start is None else start
        end = self.dateix[-1] if end is None else end

        return querySym(self.df.loc[start:end], self.sym, self.norm)
        
    @property
    def columns(self):
        """
        List with names of columns
        """
        return list(self.df.columns)

########################################################################################################
########################################################################################################
class metaData:
    """
    Wrapper class for a metadata query of the ticker's info
    """
    def __init__(self, tickerlist):
        self._get_infos(tickerlist)

    def _get_infos(self, tickerlist):
        """
        Get metadata on each company
        """
        print("Making metadata query...")
        query = yf.Tickers(tickerlist)
        info_dic = {}
        for sym in query.tickers:
            info_dic[sym] = query.tickers[sym]

        info_dic = {sym: pd.Series(info_dic[sym].info) for sym in info_dic}
        self.df = pd.DataFrame(info_dic)

    def __getitem__(self, ix):
        """
        Return a row (parameter) of the internal dataframe
        """
        return self.df.loc[ix]

    def __repr__(self):
        return f'{type(self).__name__}({self.df.columns}'

    def get_features(self):
        """
        Returns a list of featues
        """
        return list(self.df.index)

########################################################################################################
########################################################################################################
class amountSym(querySym):
    """
    Class that inherits from querySym and simply allows for absolute quantification of given amount of shares
    """
    def __init__(self, ss_df, sym, norm = True, num_shares = None):
        super().__init__(self, ss_df, sym, norm)
        if num_shares:
            self.num_shares = num_shares
        else:
            sys.exit("Must define number of shares")

    def _multiply_values(self):
        """
        This function simply multiplies the values by the number of shares
        """
        self.df = self.df * self.num_shares

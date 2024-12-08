import pandas as pd
import yfinance as yf
from typing import Optional
from datetime import datetime, timedelta


class DataLoader:
    @staticmethod
    def load_from_yahoo(symbol: str,
                        start_date: Optional[datetime] = None,
                        end_date: Optional[datetime] = None,
                        interval: str = '1d') -> pd.DataFrame:
        """Load historical data from Yahoo Finance"""
        if start_date is None:
            start_date = datetime.now() - timedelta(days=365)
        if end_date is None:
            end_date = datetime.now()

        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(
                start=start_date, end=end_date, interval=interval)
            df.index = pd.to_datetime(df.index)
            return df
        except Exception as e:
            raise Exception(f"Failed to load data for {symbol}: {str(e)}")

    @staticmethod
    def load_from_csv(filepath: str,
                      date_column: str = 'Date',
                      required_columns: list = None) -> pd.DataFrame:
        """Load historical data from CSV file"""
        if required_columns is None:
            required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']

        try:
            df = pd.read_csv(filepath)

            # Ensure required columns exist
            missing_cols = [
                col for col in required_columns if col not in df.columns]
            if missing_cols:
                raise ValueError(f"Missing required columns: {missing_cols}")

            # Convert date column to datetime
            df[date_column] = pd.to_datetime(df[date_column])
            df.set_index(date_column, inplace=True)

            return df
        except Exception as e:
            raise Exception(f"Failed to load data from {filepath}: {str(e)}")

    @staticmethod
    def preprocess_data(df: pd.DataFrame) -> pd.DataFrame:
        """Preprocess data for strategy use"""
        df = df.copy()

        # Remove rows with missing values
        df.dropna(inplace=True)

        # Ensure all required columns are present
        required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")

        # Add basic derived columns
        df['Returns'] = df['Close'].pct_change()
        df['Range'] = df['High'] - df['Low']
        df['Body'] = abs(df['Close'] - df['Open'])

        return df

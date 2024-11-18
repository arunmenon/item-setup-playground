import pandas as pd
import logging


class InputHandler:
    def __init__(self, input_file):
        """
        Initialize the InputHandler with the input file path.

        Args:
            input_file (str): Path to the input CSV file.
        """
        self.input_file = input_file

    def load_data(self):
        """
        Load input data from a CSV file.

        Returns:
            pd.DataFrame: Loaded DataFrame from the input file.
        """
        try:
            logging.info(f"Loading data from '{self.input_file}'")
            df = pd.read_csv(self.input_file)
            logging.info(f"Loaded {len(df)} rows from input file.")
            return df
        except FileNotFoundError as e:
            logging.error(f"Input file not found: {e}")
            raise
        except pd.errors.EmptyDataError as e:
            logging.error(f"Input file is empty or invalid: {e}")
            raise

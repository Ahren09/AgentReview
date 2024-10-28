import os

import pandas as pd


def save_to_excel(df, path, sheet_name, index: bool=False):
    """
    Save a pandas dataframe to an Excel sheet. If the file exists, replace the specified sheet
    without impacting other sheets. If the file does not exist, create it.

    Parameters:
    df (pd.DataFrame): Dataframe to save.
    path (str): Path to the Excel file.
    sheet_name (str): Name of the sheet to save the dataframe to.
    """
    # Check if the file exists
    if os.path.exists(path):
        # Load the existing workbook
        with pd.ExcelWriter(path, engine='openpyxl', mode='a') as writer:
            # Remove the existing sheet if it exists
            if sheet_name in writer.book.sheetnames:
                del writer.book[sheet_name]
            # Write the dataframe to the specified sheet
            df.to_excel(writer, sheet_name=sheet_name, index=index)
    else:
        # Create a new workbook and write the dataframe
        with pd.ExcelWriter(path, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=index)

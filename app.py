import zipfile
import pandas as pd
import io

# Path to the zip file
zip_path = r"C:\Users\SWEEKRITHI SHETTY\Desktop\Demo\IndyCar_Data.zip"

# Function to extract relevant data from a text file
def extract_data_from_text(text, filename):
    # Split text by lines
    lines = text.split('\n')
    
    # Extract CarName from the 5th row
    car_name = lines[4].split('\t')[1]
    
    # Create a StringIO object to read the text data
    data_io = io.StringIO(text)
    
    # Skip the header rows
    for _ in range(15):
        next(data_io)
    
    # Read the data into a DataFrame
    df = pd.read_csv(data_io, delimiter='\t')
    
    # Add CarName column
    df['CarName'] = car_name
    
    return df[['CarName', 'Time', 'TransGear[TransGear]', 'VehicleSpeed[mph]', 'EngineSpeed[rpm]']]

# List to store DataFrames
dfs = []

# Open the zip file
with zipfile.ZipFile(zip_path, 'r') as zip_ref:
    # Iterate through the files in the zip folder
    for file_info in zip_ref.infolist():
        # Check if the file is a text file
        if file_info.filename.endswith('.txt'):
            # Extract the text from the file
            with zip_ref.open(file_info.filename) as file:
                text = io.TextIOWrapper(file, encoding='utf-8').read()
                # Extract data from the text and append to the list
                dfs.append(extract_data_from_text(text, file_info.filename))

# Concatenate all DataFrames into a single DataFrame
final_df = pd.concat(dfs, ignore_index=True)

# Convert 'EngineSpeed[rpm]' column to numeric (ignore errors for non-numeric values)
final_df['EngineSpeed[rpm]'] = pd.to_numeric(final_df['EngineSpeed[rpm]'], errors='coerce')

# Filter data where EngineSpeed is above 4000 and TransGear is 1,2,3,4,5,6
filtered_df = final_df[(final_df['EngineSpeed[rpm]'] > 4000) & 
                       (final_df['TransGear[TransGear]'].isin([1, 2, 3, 4, 5, 6])) & 
                       (final_df['VehicleSpeed[mph]'] != 0) & 
                       (final_df['EngineSpeed[rpm]'] != 0)]

# Group by 'CarName' and 'EngineSpeed[rpm]' and consider only common engine speed values
grouped_df = filtered_df.groupby(['CarName', 'EngineSpeed[rpm]']).filter(lambda x: len(x) > 1)

# Ensure each 'CarName' has an equal amount of dataset
balanced_df = grouped_df.groupby('CarName').apply(lambda x: x.sample(grouped_df['CarName'].value_counts().min()).reset_index(drop=True))

# Save the balanced DataFrame to a CSV Excel file with headers
balanced_df.to_csv('balanced_data.csv', index=False, header=True)

print("Balanced data saved successfully.")

import pandas as pd

# Load the dataset
df = pd.read_csv('oee_data.csv')

# --- Basic Info ---
print("=== SHAPE ===")
print(df.shape)  # rows and columns

print("\n=== COLUMN NAMES & DATA TYPES ===")
print(df.dtypes)  # what type is each column?

print("\n=== FIRST 5 ROWS ===")
print(df.head())

print("\n=== BASIC STATISTICS ===")
print(df.describe())  # min, max, mean, std for every number column

print("\n=== MISSING VALUES ===")
print(df.isnull().sum())  # count of nulls per column

print("\n=== UNIQUE MACHINES ===")
print(df['machine'].unique())

print("\n=== UNIQUE SHIFTS ===")
print(df['shift'].unique())

print("\n=== OEE AVERAGE PER MACHINE ===")
print(df.groupby('machine')['oee'].mean().round(3))
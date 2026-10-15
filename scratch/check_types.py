import pandas as pd
from collections import defaultdict

df = pd.read_csv('Database/products.csv')[:500]

# Mapping rules from product_name to specific search queries/types
type_counts = defaultdict(list)
for idx, row in df.iterrows():
    pname = row['product_name']
    cat = row['category']
    pid = row['product_id']
    type_counts[cat].append((pid, pname))

print("Category summary:")
for cat, items in type_counts.items():
    print(f"{cat}: {len(items)} items")


import pandas as pd
import random
from datetime import datetime, timedelta
import os

# Create mock user data
start_date = (datetime.now() - timedelta(weeks=random.randint(5, 12))).strftime('%Y-%m-%d')
mock_user = ['mock', 180, 72, 'date range', start_date, '12']

# Load and update users.csv
users_df = pd.read_csv(os.path.join('..', 'data', 'users.csv'))
users_df.loc[len(users_df)] = mock_user
users_df.to_csv(os.path.join('..', 'data', 'users.csv'), index=False)

# Generate mock user measurement data
end_date = datetime.now()
start_date = end_date - timedelta(days=24*30)  # 24 months
dates = []
current = start_date

initial_weight = mock_user[2] + random.uniform(8, 10)  # 12-15kg over target
last_weight = initial_weight
last_fat = random.uniform(25, 30)
last_water = random.uniform(45, 50)
last_muscle = random.uniform(25, 30)

checkpoints = [
    (datetime(2023, 1, 1), 83.4),
    (datetime(2023, 3, 1), 81.6),
    (datetime(2023, 5, 1), 82.7),
    (datetime(2023, 7, 1), 80.7),
    (datetime(2023, 9, 1), 82.4),
    (datetime(2023, 11, 1), 85.4),
    (datetime(2024, 1, 1), 84.1),
    (datetime(2024, 3, 1), 83.8),
    (datetime(2024, 5, 1), 81.1),
    (datetime(2024, 7, 1), 78.6),
    (datetime(2024, 9, 1), 80.3),
    (datetime(2024, 11, 1), 79.2),
    (datetime(2024, 12, 1), 76.2),
]

measurements = []
while current <= end_date:
    # Random interval 3-5 days
    days = random.randint(4, 8)
    current += timedelta(days=days)

    # Find nearest checkpoint and interpolate weight
    checkpoint_weight = None
    for i in range(len(checkpoints)-1):
        if checkpoints[i][0] <= current <= checkpoints[i+1][0]:
            days_between = (checkpoints[i+1][0] - checkpoints[i][0]).days
            days_from_start = (current - checkpoints[i][0]).days
            weight_diff = checkpoints[i+1][1] - checkpoints[i][1]
            checkpoint_weight = checkpoints[i][1] + (weight_diff * days_from_start / days_between)
            break

    if checkpoint_weight is None:
        # If before first or after last checkpoint, use nearest checkpoint
        if current < checkpoints[0][0]:
            checkpoint_weight = checkpoints[0][1]
        else:
            checkpoint_weight = checkpoints[-1][1]

    # Generate varying measurements around checkpoint weight
    weight = checkpoint_weight + random.uniform(-0.3, 0.3)
    fat = last_fat + random.uniform(-0.2, 0.2)
    water = last_water + random.uniform(-0.2, 0.2)
    muscle = last_muscle + random.uniform(-0.2, 0.2)

    measurements.append([
        current.strftime('%Y-%m-%d'),
        round(weight, 1),
        round(fat, 1),
        round(water, 1),
        round(muscle, 1)
    ])

    last_weight = weight
    last_fat = fat
    last_water = water
    last_muscle = muscle

# Create and save mock user CSV
mock_df = pd.DataFrame(
    measurements,
    columns=['date', 'weight', 'fat', 'water', 'muscle'])
mock_df.to_csv(
    os.path.join('..', 'data', 'mock.csv'),
    index=False)

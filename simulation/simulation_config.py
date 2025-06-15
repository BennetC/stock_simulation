import random


class SimulationConfig:
    # Market composition designed for dynamic behavior
    random_traders = 1500  # Noise traders - provide liquidity and volatility
    mean_reverting_traders = 500  # Stabilizing force - fewer but well-capitalized
    trend_following_traders = 0  # New trader type for more complex dynamics

    # Asymmetric capital allocation creates realistic market dynamics
    random_trader_cash = random.randint(10000, 100000)  # Moderate cash - forces resource constraints
    random_trader_shares = random.randint(450, 650)  # Moderate inventory - creates natural turnover

    # Mean reverters as "market makers" with deeper pockets
    mean_reverting_trader_cash = random.randint(30000, 300000)  # 3x more cash - can absorb volatility
    mean_reverting_trader_shares = random.randint(1350, 1950)  # 3x more shares - provide stability

    # Trend followers with moderate capital
    trend_following_trader_cash = random.randint(20000, 80000)
    trend_following_trader_shares = random.randint(300, 500)

    # Higher starting price creates room for interesting price discovery
    initial_price = 100.0

    # --- Trader Tracking Configuration ---
    # Defines which traders' detailed data will be sent to the frontend.
    # This helps reduce the amount of data sent over websockets for performance.

    # Global setting: Track the first N traders of EACH active type.
    # This is ADDITIVE with the specific counts below.
    # Set to 0 or None to disable.
    all_traders_tracking = 2

    # Specific counts: Track the first N traders for a given type.
    # This is ADDITIVE with `all_traders_tracking`. Set to 0 or None to disable.
    random_trader_tracking = 3  # Total RandomTraders tracked: 2 (global) + 3 (specific) = 5
    mean_reverting_trader_tracking = 3  # Total MeanRevertingTraders tracked: 2 (global) + 3 (specific) = 5
    trend_following_trader_tracking = 1  # Total TrendFollowingTraders tracked: 2 (global) + 1 (specific) = 3

    # Name-based tracking: Track specific traders by their exact IDs.
    # This is IGNORED for a trader type if its specific count (e.g., random_trader_tracking) is > 0.
    tracked_trader_ids_by_name = [
        'rt_100', 'rt_101',  # These will be IGNORED because random_trader_tracking > 0
        'mrt_200', 'mrt_201',  # These will be IGNORED because mean_reverting_trader_tracking > 0
        # To make name-based tracking work for a type, set its specific count above to 0 or None.
        # Example of active name-based tracking:
        #   trend_following_trader_tracking = 0
        #   tracked_trader_ids_by_name = ['tft_50']
    ]
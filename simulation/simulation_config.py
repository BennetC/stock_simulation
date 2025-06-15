import random


class SimulationConfig:
    # Market composition designed for dynamic behavior
    random_traders = 1500  # Noise traders - provide liquidity and volatility
    mean_reverting_traders = 500  # Stabilizing force - fewer but well-capitalized

    # Asymmetric capital allocation creates realistic market dynamics
    random_trader_cash = random.randint(10000, 100000)  # Moderate cash - forces resource constraints
    random_trader_shares = random.randint(450, 650)  # Moderate inventory - creates natural turnover

    # Mean reverters as "market makers" with deeper pockets
    mean_reverting_trader_cash = random.randint(30000, 300000)  # 3x more cash - can absorb volatility
    mean_reverting_trader_shares = random.randint(1350, 1950)  # 3x more shares - provide stability

    # Higher starting price creates room for interesting price discovery
    initial_price = 100.0
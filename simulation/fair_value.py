import random
from simulation.order import Order
from simulation.traders.trader import Trader


def get_private_fair_value(previous_fair_value: float,
                          observed_price: float,
                          alpha: float) -> float:
    """
    Update a trader's private fair value estimate using exponential smoothing.

    Args:
        previous_fair_value (float): The trader's prior fair value estimate.
        observed_price (float): The latest observed market price (e.g., mid-price).
        alpha (float): Smoothing factor (0 < alpha <= 1), unique to each trader.

    Returns:
        float: The updated private fair value.

    Formula:
        new_fair = previous_fair_value + alpha * (observed_price - previous_fair_value)
    """
    return previous_fair_value + alpha * (observed_price - previous_fair_value)


def get_mid_fair_value(best_bid: float,
                      best_ask: float) -> float:
    """
    Compute the market fair value as the midpoint between the best bid and best ask.

    Args:
        best_bid (float): The highest current bid price in the order book.
        best_ask (float): The lowest current ask price in the order book.

    Returns:
        float: The mid-point (fair value) of the bid-ask spread.

    Formula:
        mid = (best_bid + best_ask) / 2
    """
    return (best_bid + best_ask) / 2.0


def fair_value_strategy(private_odds=0.5, alpha_range=(0.1, 0.5)):
    """
    Generate a fair value strategy based on private and mid fair value estimates.

    Args:
        private_odds (float): Probability of using private fair value.
        alpha_range (tuple): Range for the smoothing factor alpha.

    Returns:
        dict: A strategy with probabilities and alpha values.
    """
    if random.random() < private_odds:
        alpha = random.uniform(*alpha_range)
        return {
            'type': 'private',
            'alpha': alpha
        }
    else:
        return {
            'type': 'mid'
        }

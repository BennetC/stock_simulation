import random

from simulation.fair_value import fair_value_strategy, get_mid_fair_value, get_private_fair_value
from simulation.order import Order
from simulation.traders.trader import Trader


# TODO - Sharpe ratio, max drawdown, moving exponential fair value, mid fair value
# TODO - Vary fair value alpha and aggressiveness randomly
class RandomTrader(Trader):
    def __init__(self, trader_id, cash, shares, fair_value):
        super().__init__(trader_id, cash, shares)

        # Assign fair value strategy at initialization
        self.fair_value_strategy = fair_value_strategy()

        # Initialize fair value based on strategy
        if self.fair_value_strategy['type'] == 'private':
            # Each trader has their own perception of fair value with some variation
            self.private_fair_value = fair_value + random.gauss(0, 2)  # Fair value ± $2
        else:
            # For mid fair value strategy, we'll calculate it dynamically
            self.private_fair_value = fair_value

        self.aggressiveness = random.uniform(0.1, 0.3)  # How far from fair value they'll trade

    def get_current_fair_value(self, current_price, best_bid=None, best_ask=None):
        """
        Get the trader's current fair value estimate based on their strategy.

        Args:
            current_price (float): Current market price
            best_bid (float): Best bid price from order book
            best_ask (float): Best ask price from order book

        Returns:
            float: The trader's current fair value estimate
        """
        if self.fair_value_strategy['type'] == 'private':
            # Update private fair value using exponential smoothing
            # Use current_price as observed price if no mid-price available
            observed_price = current_price
            if best_bid is not None and best_ask is not None:
                observed_price = get_mid_fair_value(best_bid, best_ask)

            self.private_fair_value = get_private_fair_value(
                self.private_fair_value,
                observed_price,
                self.fair_value_strategy['alpha']
            )
            return self.private_fair_value
        else:
            # Use mid fair value if available, otherwise fall back to current price
            if best_bid is not None and best_ask is not None:
                return get_mid_fair_value(best_bid, best_ask)
            else:
                return current_price

    def generate_order(self, current_price, best_bid=None, best_ask=None):
        """
        Generate an order based on the trader's fair value strategy.

        Args:
            current_price (float): Current market price
            best_bid (float): Best bid price from order book
            best_ask (float): Best ask price from order book

        Returns:
            Order or None: Generated order or None if no order placed
        """
        if random.random() < 0.1:  # 10% chance to place order

            # Get fair value based on strategy
            fair_value = self.get_current_fair_value(current_price, best_bid, best_ask)

            # Determine if trader thinks stock is cheap or expensive
            value_ratio = current_price / fair_value

            # Bias toward buying when cheap, selling when expensive
            if value_ratio < 0.95:  # Stock seems undervalued
                side_weights = [0.7, 0.3]  # 70% chance buy, 30% sell
            elif value_ratio > 1.05:  # Stock seems overvalued
                side_weights = [0.3, 0.7]  # 30% chance buy, 70% sell
            else:
                side_weights = [0.5, 0.5]  # Equal probability

            side = random.choices(['buy', 'sell'], weights=side_weights)[0]

            # Mix of limit and market orders
            order_type = random.choices(['limit', 'market'], weights=[0.8, 0.2])[0]
            quantity = random.randint(1, 50)  # Smaller order sizes

            # Check if trader has resources
            if side == 'buy' and self.cash < current_price * quantity:
                return None
            if side == 'sell' and self.shares < quantity:
                return None

            price = None
            if order_type == 'limit':
                if side == 'buy':
                    # Buy orders: bid below current price, closer to fair value
                    max_price = min(current_price * 0.999, fair_value * (1 + self.aggressiveness))
                    min_price = current_price * (1 - self.aggressiveness)
                    price = round(random.uniform(min_price, max_price), 2)
                else:  # sell
                    # Sell orders: ask above current price, closer to fair value
                    min_price = max(current_price * 1.001, fair_value * (1 - self.aggressiveness))
                    max_price = current_price * (1 + self.aggressiveness)
                    price = round(random.uniform(min_price, max_price), 2)

                # Ensure price is positive
                price = max(0.01, price)

            return Order(
                order_id=self.get_next_order_id(),
                order_type=order_type,
                side=side,
                quantity=quantity,
                price=price,
                trader_id=self.id
            )
        return None
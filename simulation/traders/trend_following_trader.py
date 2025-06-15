import random

from simulation.order import Order
from simulation.traders.trader import Trader


class TrendFollowingTrader(Trader):
    def __init__(self, trader_id, initial_cash, initial_shares, trend_threshold=0.02):
        super().__init__(trader_id, initial_cash, initial_shares)
        self.trend_threshold = trend_threshold
        self.previous_price = None

    def generate_order(self, current_price):
        if self.previous_price is None:
            self.previous_price = current_price
            return None  # No previous price to compare

        price_change = (current_price - self.previous_price) / self.previous_price

        if abs(price_change) < self.trend_threshold:
            self.previous_price = current_price
            return None  # No significant trend detected

        side = 'buy' if price_change > 0 else 'sell'
        quantity = min(random.randint(1, 20), self.shares if side == 'sell' else self.cash // current_price)

        # Check resources
        if side == 'buy' and self.cash < current_price * quantity:
            return None
        if side == 'sell' and self.shares < quantity:
            return None

        # Aggressive pricing to ensure execution
        price = round(current_price * (1.001 if side == 'buy' else 0.999), 2)

        order = Order(
            order_id=self.get_next_order_id(),
            order_type='limit',
            side=side,
            quantity=quantity,
            price=price,
            trader_id=self.id
        )

        self.previous_price = current_price
        return order
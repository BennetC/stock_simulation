import random

from simulation.fair_value import get_mid_fair_value, get_private_fair_value
from simulation.order import Order
from simulation.traders.trader import Trader

class MeanRevertingTrader(Trader):
    def __init__(self, trader_id, cash, shares, target_price):
        super().__init__(trader_id, cash, shares)

        # Strategic traders always use private fair value with individual learning rates
        self.alpha = random.uniform(0.05, 0.3)  # Mean reverters tend to be more conservative learners
        self.private_fair_value = target_price + random.gauss(0, 1)  # Smaller initial variation
        self.target_price = target_price  # Keep original target for mean reversion logic

        # Mean reversion specific parameters
        self.reversion_strength = random.uniform(0.015, 0.03)  # How far from target triggers action

    def get_current_fair_value(self, current_price, best_bid=None, best_ask=None):
        """
        Update and return the trader's private fair value estimate.
        """
        # Use mid-price if available, otherwise current price
        observed_price = current_price
        if best_bid is not None and best_ask is not None:
            observed_price = get_mid_fair_value(best_bid, best_ask)

        # Update private fair value using exponential smoothing
        self.private_fair_value = get_private_fair_value(
            self.private_fair_value,
            observed_price,
            self.alpha
        )
        return self.private_fair_value

    def generate_order(self, current_price, best_bid=None, best_ask=None):
        if random.random() < 0.05:  # Lower order frequency

            # Update fair value based on market observations
            fair_value = self.get_current_fair_value(current_price, best_bid, best_ask)

            # Mean reversion logic: compare current price to target, but use updated fair value for execution
            upper_threshold = self.target_price * (1 + self.reversion_strength)
            lower_threshold = self.target_price * (1 - self.reversion_strength)

            # Strong bias toward mean reversion based on target price
            if current_price > upper_threshold:
                side = 'sell'  # Push price down toward target
            elif current_price < lower_threshold:
                side = 'buy'  # Push price up toward target
            else:
                return None  # No strong opinion, don't trade

            quantity = random.randint(1, 20)

            # Check resources
            if side == 'buy' and self.cash < current_price * quantity:
                return None
            if side == 'sell' and self.shares < quantity:
                return None

            # Price orders based on fair value estimate, not just current price
            if side == 'buy':
                # Willing to pay up to fair value, but be slightly aggressive
                max_price = min(fair_value * 1.002, current_price * 1.001)
                price = round(max_price, 2)
            else:  # sell
                # Willing to sell down to fair value, but be slightly aggressive
                min_price = max(fair_value * 0.998, current_price * 0.999)
                price = round(min_price, 2)

            # Ensure price is positive
            price = max(0.01, price)

            return Order(
                order_id=self.get_next_order_id(),
                order_type='limit',
                side=side,
                quantity=quantity,
                price=price,
                trader_id=self.id
            )
        return None
from collections import deque
from datetime import datetime


class OrderBook:
    def __init__(self):
        self.bids = []  # Buy orders, sorted by price desc
        self.asks = []  # Sell orders, sorted by price asc
        self.trades = deque(maxlen=1000)  # Keep last 1000 trades

    def add_order(self, order):
        if order.type == 'market':
            return self._execute_market_order(order)
        else:
            return self._add_limit_order(order)

    def _add_limit_order(self, order):
        trades = []

        if order.side == 'buy':
            # Try to match with existing asks
            while order.quantity > 0 and self.asks and self.asks[0].price <= order.price:
                trade = self._execute_trade(order, self.asks[0])
                trades.append(trade)
                if self.asks[0].quantity == 0:
                    self.asks.pop(0)

            # Add remaining quantity to order book
            if order.quantity > 0:
                self.bids.append(order)
                self.bids.sort(key=lambda x: x.price, reverse=True)
        else:
            # Try to match with existing bids
            while order.quantity > 0 and self.bids and self.bids[0].price >= order.price:
                trade = self._execute_trade(self.bids[0], order)
                trades.append(trade)
                if self.bids[0].quantity == 0:
                    self.bids.pop(0)

            # Add remaining quantity to order book
            if order.quantity > 0:
                self.asks.append(order)
                self.asks.sort(key=lambda x: x.price)

        return trades

    def _execute_market_order(self, order):
        trades = []

        if order.side == 'buy' and self.asks:
            while order.quantity > 0 and self.asks:
                trade = self._execute_trade(order, self.asks[0])
                trades.append(trade)
                if self.asks[0].quantity == 0:
                    self.asks.pop(0)
        elif order.side == 'sell' and self.bids:
            while order.quantity > 0 and self.bids:
                trade = self._execute_trade(self.bids[0], order)
                trades.append(trade)
                if self.bids[0].quantity == 0:
                    self.bids.pop(0)

        return trades

    def _execute_trade(self, buy_order, sell_order):
        quantity = min(buy_order.quantity, sell_order.quantity)
        price = sell_order.price or buy_order.price

        trade = {
            'id': len(self.trades) + 1,
            'price': round(price, 2),
            'quantity': quantity,
            'buyer_id': buy_order.trader_id,
            'seller_id': sell_order.trader_id,
            'timestamp': datetime.now().isoformat()
        }

        buy_order.quantity -= quantity
        sell_order.quantity -= quantity
        self.trades.append(trade)

        return trade

    def get_best_bid(self):
        return self.bids[0].price if self.bids else None

    def get_best_ask(self):
        return self.asks[0].price if self.asks else None

    def get_spread(self):
        bid = self.get_best_bid()
        ask = self.get_best_ask()
        return round(ask - bid, 2) if (bid and ask) else None

    def get_order_book_data(self):
        return {
            'bids': [{'price': order.price, 'quantity': order.quantity} for order in self.bids[:10]],
            'asks': [{'price': order.price, 'quantity': order.quantity} for order in self.asks[:10]]
        }
from datetime import datetime


class Order:
    def __init__(self, order_id, order_type, side, quantity, price=None, trader_id=None):
        self.id = order_id
        self.type = order_type  # 'market' or 'limit'
        self.side = side  # 'buy' or 'sell'
        self.quantity = quantity
        self.price = price
        self.trader_id = trader_id
        self.timestamp = datetime.now()

    def to_dict(self):
        return {
            'id': self.id,
            'type': self.type,
            'side': self.side,
            'quantity': self.quantity,
            'price': self.price,
            'trader_id': self.trader_id,
            'timestamp': self.timestamp.isoformat()
        }

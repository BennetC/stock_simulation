# TODO - Compare a 100%‐private population versus 100%‐mid population versus mixed-population environments
# TODO - See whether having both types in the same market changes overall liquidity, volatility, or price efficiency

# TODO - Add following trader types: Whale Trader, Momentum Trader, High-Frequency Trader

class Trader:
    def __init__(self, trader_id, cash, shares=0):
        self.id = trader_id
        self.cash = cash
        self.shares = shares
        self.order_count = 0

        self.initial_cash = cash
        self.initial_shares = shares
        self.initial_portfolio_value = 0
        self.trade_history = []
        self.total_volume_traded = 0

    def generate_order(self, current_price):
        return None

    def get_next_order_id(self):
        self.order_count += 1
        return f"{self.id}_{self.order_count}"

    def to_dict(self, current_price, open_orders):
        portfolio_value = self.cash + (self.shares * current_price)
        pnl = portfolio_value - self.initial_portfolio_value
        pnl_percent = (pnl / self.initial_portfolio_value * 100) if self.initial_portfolio_value > 0 else 0

        return {
            'id': self.id,
            'cash': self.cash,
            'shares': self.shares,
            'portfolio_value': portfolio_value,
            'pnl': pnl,
            'pnl_percent': pnl_percent,
            'total_volume_traded': self.total_volume_traded,
            'trade_history': self.trade_history[-100:],  # Send last 100 trades to keep payload small
            'open_orders': open_orders,
        }
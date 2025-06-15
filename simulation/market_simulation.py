import random
from collections import deque

from simulation.event_scheduler import EventScheduler
from simulation.order_book import OrderBook
from simulation.traders.random_trader import RandomTrader


class MarketSimulation:
    def __init__(self, config=None, socketio=None):
        self.config = config
        self.socketio = socketio
        self.current_price = config.initial_price if config and config.initial_price else 50.00
        self.scheduler = EventScheduler()
        self.order_book = OrderBook()
        self.traders = []
        self.trader_map = {}
        self.price_history = deque([self.current_price], maxlen=1000)
        self.volume_history = deque([0], maxlen=1000)
        self.running = False

        self._initialize_traders()
        self._set_initial_portfolio_values()

    def _set_initial_portfolio_values(self):
        for trader in self.traders:
            trader.initial_portfolio_value = trader.cash + (trader.shares * self.current_price)

    def _initialize_traders(self):
        self.traders = []
        self.trader_map = {}

        if self.config:
            if self.config.random_traders > 0:
                for i in range(self.config.random_traders):
                    trader_id = f"rt_{i}"
                    trader = RandomTrader(
                        trader_id,
                        self.config.random_trader_cash,
                        random.randint(0, self.config.random_trader_shares),
                        fair_value=self.current_price
                    )
                    self.traders.append(trader)
                    self.trader_map[trader_id] = trader

            if self.config.mean_reverting_traders > 0:
                from simulation.traders.mean_reverting_trader import MeanRevertingTrader
                for i in range(self.config.mean_reverting_traders):
                    trader_id = f"mrt_{i}"
                    trader = MeanRevertingTrader(
                        trader_id,
                        self.config.mean_reverting_trader_cash,
                        self.config.mean_reverting_trader_shares,
                        target_price=self.current_price
                    )
                    self.traders.append(trader)
                    self.trader_map[trader_id] = trader
        else:
            for i in range(100):
                trader = RandomTrader(i, 50000, random.randint(0, 1000), fair_value=self.current_price)
                self.traders.append(trader)
                self.trader_map[i] = trader

    def step(self):
        total_volume = 0
        trades_this_step = []

        best_bid = self.order_book.get_best_bid()
        best_ask = self.order_book.get_best_ask()

        for trader in self.traders:
            order = trader.generate_order(self.current_price, best_bid, best_ask)
            if order:
                trades = self.order_book.add_order(order)
                for trade in trades:
                    self.current_price = trade['price']
                    total_volume += trade['quantity']
                    trades_this_step.append(trade)

                    buyer = self.trader_map.get(trade['buyer_id'])
                    seller = self.trader_map.get(trade['seller_id'])

                    if buyer:
                        buyer.cash -= trade['price'] * trade['quantity']
                        buyer.shares += trade['quantity']
                        buyer.trade_history.append(trade)
                        buyer.total_volume_traded += trade['quantity']

                    if seller:
                        seller.cash += trade['price'] * trade['quantity']
                        seller.shares -= trade['quantity']
                        seller.trade_history.append(trade)
                        seller.total_volume_traded += trade['quantity']

        self.price_history.append(self.current_price)
        self.volume_history.append(total_volume)
        self.scheduler.advance()

        return trades_this_step

    def get_market_data(self):
        change = 0
        change_percent = 0
        if len(self.price_history) > 1:
            change = self.current_price - self.price_history[-2]
            change_percent = (change / self.price_history[-2]) * 100

        return {
            'current_price': self.current_price,
            'change': round(change, 2),
            'change_percent': round(change_percent, 2),
            'volume': self.volume_history[-1],
            'best_bid': self.order_book.get_best_bid(),
            'best_ask': self.order_book.get_best_ask(),
            'spread': self.order_book.get_spread(),
            'price_history': list(self.price_history),
            'order_book': self.order_book.get_order_book_data(),
            'recent_trades': list(self.order_book.trades)[-10:]
        }

    def get_all_traders_data(self):
        trader_data = []
        all_open_orders = self.order_book.bids + self.order_book.asks
        for trader in self.traders:
            trader_open_orders = [
                {'type': o.side, 'price': o.price, 'quantity': o.quantity}
                for o in all_open_orders if o.trader_id == trader.id
            ]
            trader_data.append(trader.to_dict(self.current_price, trader_open_orders))
        return trader_data

    def start(self):
        if not self.running and self.socketio:
            self.running = True
            self.socketio.start_background_task(target=self._run_simulation)

    def stop(self):
        self.running = False

    def reset(self):
        self.stop()
        self.__init__(self.config, self.socketio)

    def _run_simulation(self):
        while self.running:
            trades = self.step()
            market_data = self.get_market_data()
            trader_updates = self.get_all_traders_data()

            if self.socketio:
                self.socketio.emit('market_update', market_data)
                self.socketio.emit('traders_update', trader_updates)

                if trades:
                    self.socketio.emit('new_trades', trades)

            self.socketio.sleep(0.1)
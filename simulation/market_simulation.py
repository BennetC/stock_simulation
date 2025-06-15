import random
from collections import deque

from simulation.event_scheduler import EventScheduler
from simulation.order_book import OrderBook
from simulation.traders.mean_reverting_trader import MeanRevertingTrader
from simulation.traders.random_trader import RandomTrader
from simulation.traders.trend_following_trader import TrendFollowingTrader


class MarketSimulation:
    def __init__(self, config=None, socketio=None):
        self.config = config
        self.socketio = socketio
        self.current_price = config.initial_price if config and config.initial_price else 50.00
        self.scheduler = EventScheduler()
        self.order_book = OrderBook()
        self.traders = []
        self.trader_map = {}
        self.tracked_trader_ids = set()  # Holds IDs of traders to be monitored
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

            if hasattr(self.config, 'trend_following_traders') and self.config.trend_following_traders > 0:
                for i in range(self.config.trend_following_traders):
                    trader_id = f"tft_{i}"
                    trader = TrendFollowingTrader(
                        trader_id,
                        self.config.trend_following_trader_cash,
                        random.randint(0, self.config.trend_following_trader_shares)
                    )
                    self.traders.append(trader)
                    self.trader_map[trader_id] = trader
        else:
            for i in range(100):
                trader = RandomTrader(f"rt_{i}", 50000, random.randint(0, 1000), fair_value=self.current_price)
                self.traders.append(trader)
                self.trader_map[f"rt_{i}"] = trader

        self._determine_tracked_traders()

    def _determine_tracked_traders(self):
        """
        Populates `self.tracked_trader_ids` based on the tracking configuration.
        This method allows selective tracking of traders to reduce data sent to the frontend.
        """
        self.tracked_trader_ids = set()
        if not self.config:
            # Fallback: track the first 10 traders if no config is provided
            for trader in self.traders[:10]:
                self.tracked_trader_ids.add(trader.id)
            return

        # Map trader class names to their configuration keys for easy extension
        type_map = {
            'RandomTrader': {
                'prefix': 'rt_',
                'count_key': 'random_trader_tracking',
            },
            'MeanRevertingTrader': {
                'prefix': 'mrt_',
                'count_key': 'mean_reverting_trader_tracking',
            },
            'TrendFollowingTrader': {
                'prefix': 'tft_',
                'count_key': 'trend_following_trader_tracking',
            }
        }

        global_count = getattr(self.config, 'all_traders_tracking', 0) or 0

        # Group traders by their class name for efficient lookup
        traders_by_type = {}
        for trader in self.traders:
            type_name = trader.__class__.__name__
            if type_name not in traders_by_type:
                traders_by_type[type_name] = []
            traders_by_type[type_name].append(trader)

        for type_name, type_config in type_map.items():
            if type_name not in traders_by_type:
                continue

            specific_count = getattr(self.config, type_config['count_key'], 0) or 0
            total_count = global_count + specific_count

            if total_count > 0:
                # Priority 1: Track by count (global + specific). This overrides name-based tracking.
                traders_of_this_type = traders_by_type[type_name]
                for i in range(min(total_count, len(traders_of_this_type))):
                    self.tracked_trader_ids.add(traders_of_this_type[i].id)
            else:
                # Priority 2: Track by specific IDs if count is not used for this type.
                if hasattr(self.config, 'tracked_trader_ids_by_name'):
                    prefix = type_config['prefix']
                    for trader_id in self.config.tracked_trader_ids_by_name:
                        if str(trader_id).startswith(prefix) and trader_id in self.trader_map:
                            self.tracked_trader_ids.add(trader_id)

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
        # Iterate over the pre-determined set of tracked trader IDs for efficiency
        for trader_id in sorted(list(self.tracked_trader_ids)):
            trader = self.trader_map.get(trader_id)
            if not trader:
                continue

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
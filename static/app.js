class FlaskStockSimulation {
    constructor() {
        this.socket = io();
        this.chart = null;
        this.isRunning = false;

        this.initializeChart();
        this.setupSocketListeners();
        this.setupEventListeners();
    }

    initializeChart() {
        const ctx = document.getElementById('priceChart').getContext('2d');

        // Custom plugin to draw multi-colored line segments
        const multiColorLinePlugin = {
            id: 'multiColorLine',
            beforeDatasetsDraw: (chart) => {
                const ctx = chart.ctx;
                const dataset = chart.data.datasets[0];
                const data = dataset.data;
                const meta = chart.getDatasetMeta(0);

                if (data.length < 2) return;

                ctx.save();
                ctx.lineWidth = 2;

                for (let i = 1; i < data.length; i++) {
                    const prevPoint = meta.data[i - 1];
                    const currPoint = meta.data[i];
                    if (!prevPoint || !currPoint) continue;

                    const prevPrice = data[i - 1];
                    const currPrice = data[i];
                    const color = currPrice >= prevPrice ? '#10b981' : '#ef4444';

                    ctx.strokeStyle = color;
                    ctx.beginPath();
                    ctx.moveTo(prevPoint.x, prevPoint.y);
                    ctx.lineTo(currPoint.x, currPoint.y);
                    ctx.stroke();
                }

                ctx.restore();
            }
        };

        this.chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Price',
                    data: [],
                    borderColor: 'rgba(0, 0, 0, 0)',
                    backgroundColor: 'rgba(16, 185, 129, 0.05)',
                    borderWidth: 0,
                    fill: true,
                    tension: 0.1,
                    pointRadius: 0,
                    pointHoverRadius: 5,
                    pointBackgroundColor: function(context) {
                        const i = context.dataIndex;
                        if (i === 0) return '#888888';
                        return context.dataset.data[i] >= context.dataset.data[i - 1]
                            ? '#10b981' : '#ef4444';
                    },
                    pointBorderColor: function(context) {
                        const i = context.dataIndex;
                        if (i === 0) return '#888888';
                        return context.dataset.data[i] >= context.dataset.data[i - 1]
                            ? '#10b981' : '#ef4444';
                    }
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { labels: { color: '#ffffff' } }
                },
                scales: {
                    x: { ticks: { color: '#ffffff' }, grid: { color: '#333333' } },
                    y: {
                        ticks: {
                            color: '#ffffff',
                            callback: function(value) {
                                return `$${value.toFixed(2)}`;
                            }
                        },
                        grid: { color: '#333333' }
                    }
                },
                animation: { duration: 200 },
                interaction: { intersect: false, mode: 'index' }
            },
            plugins: [multiColorLinePlugin]
        });
    }

    setupSocketListeners() {
        this.socket.on('connect', () => {
            console.log('Connected to server');
            document.getElementById('connectionStatus').classList.add('connected');
            // The server will now automatically send the latest data upon connection,
            // so the UI will populate itself correctly without extra client-side logic.
        });
        this.socket.on('disconnect', () => {
            console.log('Disconnected');
            document.getElementById('connectionStatus').classList.remove('connected');
        });
        this.socket.on('market_update', data => this.updateMarketData(data));
        this.socket.on('new_trades', trades => this.updateRecentTrades(trades));
    }

    setupEventListeners() {
        document.getElementById('startBtn').addEventListener('click', () => this.startSimulation());
        document.getElementById('stopBtn').addEventListener('click', () => this.stopSimulation());
        document.getElementById('resetBtn').addEventListener('click', () => this.resetSimulation());
    }

    async startSimulation() {
        try {
            const res = await fetch('/api/start', { method: 'POST' });
            if (res.ok) {
                this.isRunning = true;
                document.getElementById('startBtn').disabled = true;
                document.getElementById('stopBtn').disabled = false;
            }
        } catch (err) { console.error(err); }
    }

    async stopSimulation() {
        try {
            const res = await fetch('/api/stop', { method: 'POST' });
            if (res.ok) {
                this.isRunning = false;
                document.getElementById('startBtn').disabled = false;
                document.getElementById('stopBtn').disabled = true;
            }
        } catch (err) { console.error(err); }
    }

    async resetSimulation() {
        try {
            const res = await fetch('/api/reset', { method: 'POST' });
            if (res.ok) {
                this.isRunning = false;
                document.getElementById('startBtn').disabled = false;
                document.getElementById('stopBtn').disabled = true;

                this.chart.data.labels = [];
                this.chart.data.datasets[0].data = [];
                this.chart.update();
            }
        } catch (err) { console.error(err); }
    }

    updateMarketData(data) {
        const priceEl = document.getElementById('currentPrice');
        priceEl.textContent = `$${data.current_price.toFixed(2)}`;
        priceEl.classList.remove('up', 'down');
        if (data.change > 0) priceEl.classList.add('up');
        else if (data.change < 0) priceEl.classList.add('down');

        const changeText = data.change >= 0 ? '+' : '';
        document.getElementById('priceChange').textContent =
            `${changeText}$${data.change.toFixed(2)} (${data.change_percent.toFixed(2)}%)`;
        document.getElementById('volume').textContent = data.volume;
        document.getElementById('bestBid').textContent = data.best_bid ? `$${data.best_bid.toFixed(2)}` : '-';
        document.getElementById('bestAsk').textContent = data.best_ask ? `$${data.best_ask.toFixed(2)}` : '-';
        document.getElementById('spread').textContent = data.spread ? `$${data.spread.toFixed(2)}` : '-';

        if (data.price_history) {
            this.chart.data.labels = data.price_history.map((_,i) => i);
            this.chart.data.datasets[0].data = data.price_history;
            this.chart.update('none'); // Using 'none' provides a smoother update
        }
        this.updateOrderBook(data.order_book);
    }

    updateOrderBook({ asks, bids }) {
        const tbody = document.getElementById('orderBookBody');
        tbody.innerHTML = '';
        asks.slice(0,10).reverse().forEach(({ price, quantity }) => {
            const row = tbody.insertRow();
            row.innerHTML = `<td>-</td><td>-</td><td class="ask">$${price.toFixed(2)}</td><td class="ask">${quantity}</td>`;
        });
        bids.slice(0,10).forEach(({ price, quantity }) => {
            const row = tbody.insertRow();
            row.innerHTML = `<td class="bid">${quantity}</td><td class="bid">$${price.toFixed(2)}</td><td>-</td><td>-</td>`;
        });
    }

    updateRecentTrades(trades) {
        const div = document.getElementById('recentTrades');
        trades.forEach(({ price, quantity, timestamp }) => {
            const item = document.createElement('div');
            item.className = 'trade-item';
            item.innerHTML = `
                <div><span class="trade-price">$${price.toFixed(2)}</span> × ${quantity}</div>
                <span class="trade-time">${new Date(timestamp).toLocaleTimeString()}</span>
            `;
            div.insertBefore(item, div.firstChild);
            while (div.children.length > 20) div.removeChild(div.lastChild);
        });
    }
}

document.addEventListener('DOMContentLoaded', () => new FlaskStockSimulation());
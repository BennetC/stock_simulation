class TradersDashboard {
    constructor() {
        this.socket = io();
        this.allTraders = [];
        this.selectedTraderId = null;
        this.currentPrice = 0;

        // For the new chart
        this.traderChart = null;
        this.traderHistoryData = {}; // Stores { traderId: { portfolio: [], stock: [], cash: [], labels: [] } }
        this.currentChartMode = 'portfolio'; // 'portfolio', 'stock', or 'cash'
        this.dataSamplerInterval = null;

        this.elements = {
            connectionStatus: document.getElementById('connectionStatus'),
            searchInput: document.getElementById('searchInput'),
            sortSelect: document.getElementById('sortSelect'),
            traderList: document.getElementById('traderList'),
            welcomeMessage: document.getElementById('welcomeMessage'),
            traderDetails: document.getElementById('traderDetails'),
            traderIdHeader: document.getElementById('traderIdHeader'),
            detailPortfolioValue: document.getElementById('detailPortfolioValue'),
            detailPnl: document.getElementById('detailPnl'),
            detailCash: document.getElementById('detailCash'),
            detailShares: document.getElementById('detailShares'),
            openOrdersTableBody: document.querySelector('#openOrdersTable tbody'),
            tradeHistoryTableBody: document.querySelector('#tradeHistoryTable tbody'),
            chartModePortfolioBtn: document.getElementById('chartModePortfolio'),
            chartModeStockBtn: document.getElementById('chartModeStock'),
            chartModeCashBtn: document.getElementById('chartModeCash'),
        };

        this.init();
    }

    init() {
        this.initializeTraderChart();
        this.setupEventListeners();
        this.setupSocketListeners();
        this.fetchInitialData();
        this.startDataSampler();
    }

    initializeTraderChart() {
        // This check prevents the entire script from crashing if the canvas is missing.
        const canvas = document.getElementById('traderHistoryChart');
        if (!canvas) {
            console.error("Chart canvas with id 'traderHistoryChart' not found. Chart functionality will be disabled.");
            return;
        }

        const ctx = canvas.getContext('2d');
        this.traderChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Value',
                    data: [],
                    borderColor: '#3b82f6',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.2,
                    pointRadius: 0,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    x: { ticks: { display: false }, grid: { color: '#333' } },
                    y: {
                        ticks: { color: '#fff', callback: value => `$${value.toFixed(0)}` },
                        grid: { color: '#333' }
                    }
                },
            }
        });
    }

    setupEventListeners() {
        this.elements.searchInput.addEventListener('input', () => this.render());
        this.elements.sortSelect.addEventListener('change', () => this.render());

        this.elements.traderList.addEventListener('click', (e) => {
            const item = e.target.closest('.trader-list-item');
            if (item && item.dataset.id !== this.selectedTraderId) {
                this.selectTrader(item.dataset.id);
            }
        });

        this.elements.chartModePortfolioBtn.addEventListener('click', () => this.setChartMode('portfolio'));
        this.elements.chartModeStockBtn.addEventListener('click', () => this.setChartMode('stock'));
        this.elements.chartModeCashBtn.addEventListener('click', () => this.setChartMode('cash'));
    }

    setupSocketListeners() {
        this.socket.on('connect', () => this.elements.connectionStatus.classList.add('connected'));
        this.socket.on('disconnect', () => this.elements.connectionStatus.classList.remove('connected'));
        this.socket.on('traders_update', (data) => this.handleUpdate(data));
        this.socket.on('market_update', (data) => {
            this.currentPrice = data.current_price;
        });
    }

    async fetchInitialData() {
        try {
            const response = await fetch('/api/traders');
            if (!response.ok) throw new Error('Failed to fetch initial trader data');
            const data = await response.json();
            this.handleUpdate(data);
        } catch (error) {
            console.error(error);
            this.elements.traderList.innerHTML = '<li>Error loading data.</li>';
        }
    }

    selectTrader(traderId) {
        this.selectedTraderId = traderId;

        if (!this.traderHistoryData[traderId]) {
            this.traderHistoryData[traderId] = { portfolio: [], stock: [], cash: [], labels: [] };
        }

        this.render();
        this.renderTraderChart();
    }

    setChartMode(mode) {
        this.currentChartMode = mode;
        [this.elements.chartModePortfolioBtn, this.elements.chartModeStockBtn, this.elements.chartModeCashBtn].forEach(btn => {
            btn.classList.remove('active');
        });
        this.elements[`chartMode${mode.charAt(0).toUpperCase() + mode.slice(1)}Btn`].classList.add('active');
        this.renderTraderChart();
    }

    startDataSampler() {
        this.dataSamplerInterval = setInterval(() => {
            if (!this.selectedTraderId || !this.allTraders.length) return;

            const trader = this.allTraders.find(t => t.id == this.selectedTraderId);
            if (!trader) return;

            const history = this.traderHistoryData[this.selectedTraderId];
            const stockValue = trader.shares * this.currentPrice;

            history.portfolio.push(trader.portfolio_value);
            history.stock.push(stockValue);
            history.cash.push(trader.cash);
            history.labels.push(new Date().toLocaleTimeString());

            const maxPoints = 100;
            if (history.portfolio.length > maxPoints) {
                history.portfolio.shift();
                history.stock.shift();
                history.cash.shift();
                history.labels.shift();
            }

            this.renderTraderChart();
        }, 2000);
    }

    handleUpdate(data) {
        this.allTraders = data;
        this.render();
    }

    render() {
        let tradersToDisplay = [...this.allTraders];
        const searchTerm = this.elements.searchInput.value.toLowerCase();
        const sortBy = this.elements.sortSelect.value;
        if (searchTerm) {
            tradersToDisplay = tradersToDisplay.filter(t => String(t.id).toLowerCase().includes(searchTerm));
        }
        tradersToDisplay.sort((a, b) => b[sortBy] - a[sortBy]);
        this.renderTraderList(tradersToDisplay);

        if (this.selectedTraderId) {
            const selectedTraderData = this.allTraders.find(t => t.id == this.selectedTraderId);
            if (selectedTraderData) {
                this.renderTraderDetails(selectedTraderData);
            } else {
                this.selectedTraderId = null;
                this.elements.welcomeMessage.classList.remove('hidden');
                this.elements.traderDetails.classList.add('hidden');
            }
        }
    }

    renderTraderList(traders) {
        this.elements.traderList.innerHTML = '';
        const fragment = document.createDocumentFragment();
        traders.forEach(trader => {
            const item = document.createElement('li');
            item.className = 'trader-list-item';
            item.dataset.id = trader.id;
            if (trader.id == this.selectedTraderId) {
                item.classList.add('active');
            }
            const pnlClass = trader.pnl >= 0 ? 'pnl-positive' : 'pnl-negative';
            const pnlSign = trader.pnl >= 0 ? '+' : '';
            item.innerHTML = `
                <span class="trader-id">${trader.id}</span>
                <span class="trader-pnl ${pnlClass}">${pnlSign}${trader.pnl.toFixed(2)}</span>
            `;
            fragment.appendChild(item);
        });
        this.elements.traderList.appendChild(fragment);
    }

    renderTraderDetails(trader) {
        this.elements.welcomeMessage.classList.add('hidden');
        this.elements.traderDetails.classList.remove('hidden');
        this.elements.traderIdHeader.textContent = `Details for Trader ${trader.id}`;
        const pnlClass = trader.pnl >= 0 ? 'pnl-positive' : 'pnl-negative';
        const pnlSign = trader.pnl >= 0 ? '+' : '';
        this.elements.detailPortfolioValue.textContent = `$${trader.portfolio_value.toFixed(2)}`;
        this.elements.detailPnl.innerHTML = `<span class="${pnlClass}">${pnlSign}$${trader.pnl.toFixed(2)} (${trader.pnl_percent.toFixed(2)}%)</span>`;
        this.elements.detailCash.textContent = `$${trader.cash.toFixed(2)}`;
        this.elements.detailShares.textContent = trader.shares;
        let openOrdersHtml = trader.open_orders.map(o => `<tr><td class="${o.type === 'buy' ? 'buy-side' : 'sell-side'}">${o.type.toUpperCase()}</td><td>$${o.price.toFixed(2)}</td><td>${o.quantity}</td></tr>`).join('');
        this.elements.openOrdersTableBody.innerHTML = openOrdersHtml || '<tr><td colspan="3">No open orders.</td></tr>';
        let tradeHistoryHtml = trader.trade_history.slice().reverse().map(t => {
            const side = t.buyer_id === trader.id ? 'buy' : 'sell';
            return `<tr><td>${new Date(t.timestamp).toLocaleTimeString()}</td><td class="${side === 'buy' ? 'buy-side' : 'sell-side'}">${side.toUpperCase()}</td><td>$${t.price.toFixed(2)}</td><td>${t.quantity}</td></tr>`;
        }).join('');
        this.elements.tradeHistoryTableBody.innerHTML = tradeHistoryHtml || '<tr><td colspan="4">No trade history.</td></tr>';
    }

    renderTraderChart() {
        if (!this.selectedTraderId || !this.traderChart) return;

        const history = this.traderHistoryData[this.selectedTraderId];
        if (!history) return;

        const dataMap = {
            portfolio: { label: 'Portfolio Value', data: history.portfolio },
            stock: { label: 'Stock Value', data: history.stock },
            cash: { label: 'Cash', data: history.cash }
        };
        const currentData = dataMap[this.currentChartMode];

        this.traderChart.data.datasets[0].label = currentData.label;
        this.traderChart.data.datasets[0].data = currentData.data;
        this.traderChart.data.labels = history.labels;
        this.traderChart.update('none');
    }
}

document.addEventListener('DOMContentLoaded', () => new TradersDashboard());
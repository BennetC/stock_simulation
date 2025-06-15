class TradersDashboard {
    constructor() {
        this.socket = io();
        this.allTraders = [];
        this.selectedTraderId = null;

        // Cache all the DOM elements we will need to interact with
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
        };

        this.init();
    }

    init() {
        this.setupEventListeners();
        this.setupSocketListeners();
        this.fetchInitialData();
    }

    setupEventListeners() {
        this.elements.searchInput.addEventListener('input', () => this.render());
        this.elements.sortSelect.addEventListener('change', () => this.render());

        // Use event delegation for the trader list
        this.elements.traderList.addEventListener('click', (e) => {
            const item = e.target.closest('.trader-list-item');
            if (item) {
                this.selectedTraderId = item.dataset.id;
                this.render(); // Re-render to update selection and details
            }
        });
    }

    setupSocketListeners() {
        this.socket.on('connect', () => this.elements.connectionStatus.classList.add('connected'));
        this.socket.on('disconnect', () => this.elements.connectionStatus.classList.remove('connected'));

        // This is the CRUCIAL listener that was missing
        this.socket.on('traders_update', (data) => this.handleUpdate(data));
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

    handleUpdate(data) {
        this.allTraders = data;
        this.render();
    }

    render() {
        let tradersToDisplay = [...this.allTraders];
        const searchTerm = this.elements.searchInput.value.toLowerCase();
        const sortBy = this.elements.sortSelect.value;

        // Filter
        if (searchTerm) {
            tradersToDisplay = tradersToDisplay.filter(t =>
                String(t.id).toLowerCase().includes(searchTerm)
            );
        }

        // Sort
        tradersToDisplay.sort((a, b) => b[sortBy] - a[sortBy]);

        this.renderTraderList(tradersToDisplay);

        if (this.selectedTraderId) {
            const selectedTraderData = this.allTraders.find(t => t.id == this.selectedTraderId);
            if (selectedTraderData) {
                this.renderTraderDetails(selectedTraderData);
            } else {
                // If the selected trader disappears (e.g., after a reset), hide the details
                this.selectedTraderId = null;
                this.elements.welcomeMessage.classList.remove('hidden');
                this.elements.traderDetails.classList.add('hidden');
            }
        }
    }

    renderTraderList(traders) {
        this.elements.traderList.innerHTML = ''; // Clear previous list
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
                <span class="trader-pnl ${pnlClass}">
                    ${pnlSign}${trader.pnl.toFixed(2)}
                </span>
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

        let openOrdersHtml = trader.open_orders.map(o => `
            <tr>
                <td class="${o.type === 'buy' ? 'buy-side' : 'sell-side'}">${o.type.toUpperCase()}</td>
                <td>$${o.price.toFixed(2)}</td>
                <td>${o.quantity}</td>
            </tr>
        `).join('');
        this.elements.openOrdersTableBody.innerHTML = openOrdersHtml || '<tr><td colspan="3">No open orders.</td></tr>';

        let tradeHistoryHtml = trader.trade_history.slice().reverse().map(t => {
            const side = t.buyer_id === trader.id ? 'buy' : 'sell';
            return `
                <tr>
                    <td>${new Date(t.timestamp).toLocaleTimeString()}</td>
                    <td class="${side === 'buy' ? 'buy-side' : 'sell-side'}">${side.toUpperCase()}</td>
                    <td>$${t.price.toFixed(2)}</td>
                    <td>${t.quantity}</td>
                </tr>
            `;
        }).join('');
        this.elements.tradeHistoryTableBody.innerHTML = tradeHistoryHtml || '<tr><td colspan="4">No trade history.</td></tr>';
    }
}

// Initialize the dashboard logic when the page is ready
document.addEventListener('DOMContentLoaded', () => new TradersDashboard());
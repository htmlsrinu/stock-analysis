document.addEventListener('DOMContentLoaded', () => {
    // Dataset State Management
    let currentDatasetName = 'space'; // 'space' or 'quantum'
    let lastUpdated = '';
    let stocksMap = {};
    let stocksList = [];

    // State management for filters and UI
    let activeFilter = 'all'; // 'all', 'Pure Play', etc.
    let activeSignalFilter = 'all'; // 'all', 'BUY', 'HOLD', 'SELL'
    let searchQuery = '';
    let currentSort = 'score-desc';
    let activeChartStock = null;
    let activeChartType = 'price-bb'; // 'price-bb', 'rsi', 'macd'
    let myChart = null; // Global Chart.js instance

    // Function to load and configure active dataset
    function loadDataset(name) {
        currentDatasetName = name;
        
        // Update active class on report selector tabs
        document.querySelectorAll('.report-tab').forEach(tab => tab.classList.remove('active'));
        
        // Manage containers visibility based on view mode
        const stockGrid = document.getElementById('stock-grid-container');
        const shortsGrid = document.getElementById('shorts-grid-container');
        const performanceGrid = document.getElementById('performance-grid-container');
        const iposGrid = document.getElementById('ipos-grid-container');
        const controlsBar = document.querySelector('.controls-bar');
        
        if (name === 'shorts') {
            const tabShorts = document.getElementById('tab-shorts');
            if (tabShorts) tabShorts.classList.add('active');
            
            if (stockGrid) stockGrid.style.display = 'none';
            if (shortsGrid) shortsGrid.style.display = 'block';
            if (performanceGrid) performanceGrid.style.display = 'none';
            if (iposGrid) iposGrid.style.display = 'none';
            if (controlsBar) controlsBar.style.display = 'none';
            
            // Update title and subtitle
            document.querySelector('.title-desc h1').textContent = "Apex Shorts";
            document.querySelector('.title-desc p').textContent = "Consensus Engine Short-Selling Intelligence & Overextension Analysis";
            
            // Set last updated date in UI (use space data's date or current date)
            let shortsLastUpdated = '2026-06-01';
            if (window.STOCK_DATA) {
                shortsLastUpdated = window.STOCK_DATA.lastUpdated;
            }
            document.getElementById('last-updated-date').textContent = shortsLastUpdated;
            
            // Update publication timestamp with current date and time
            const now = new Date();
            const formattedTime = now.toLocaleDateString() + ' ' + now.toLocaleTimeString();
            const timestampEl = document.getElementById('publication-timestamp');
            if (timestampEl) timestampEl.textContent = formattedTime;
            
            populateShortsStats();
            renderShortsGrid();
            return;
        } else if (name === 'performance') {
            const tabPerf = document.getElementById('tab-performance');
            if (tabPerf) tabPerf.classList.add('active');
            
            if (stockGrid) stockGrid.style.display = 'none';
            if (shortsGrid) shortsGrid.style.display = 'none';
            if (performanceGrid) performanceGrid.style.display = 'block';
            if (iposGrid) iposGrid.style.display = 'none';
            if (controlsBar) controlsBar.style.display = 'none';
            
            // Update title and subtitle
            document.querySelector('.title-desc h1').textContent = "Performance Audit";
            document.querySelector('.title-desc p').textContent = "Paper Trading Backtest Auditing & Real-Time Setup Analytics";
            
            // Set last updated date in UI
            let perfLastUpdated = '2026-06-01';
            if (window.STOCK_DATA) {
                perfLastUpdated = window.STOCK_DATA.lastUpdated;
            }
            document.getElementById('last-updated-date').textContent = perfLastUpdated;
            
            // Update publication timestamp with current date and time
            const now = new Date();
            const formattedTime = now.toLocaleDateString() + ' ' + now.toLocaleTimeString();
            const timestampEl = document.getElementById('publication-timestamp');
            if (timestampEl) timestampEl.textContent = formattedTime;
            
            populatePerformanceStats();
            renderPerformanceGrid();
            return;
        } else if (name === 'ipos') {
            const tabIpos = document.getElementById('tab-ipos');
            if (tabIpos) tabIpos.classList.add('active');
            
            if (stockGrid) stockGrid.style.display = 'none';
            if (shortsGrid) shortsGrid.style.display = 'none';
            if (performanceGrid) performanceGrid.style.display = 'none';
            if (iposGrid) iposGrid.style.display = 'block';
            if (controlsBar) controlsBar.style.display = 'none';
            
            // Update title and subtitle
            document.querySelector('.title-desc h1').textContent = "Recent IPOs";
            document.querySelector('.title-desc p').textContent = "Quantitative Technical Performance & Consensus Ratings for New Listings";
            
            // Set last updated date in UI
            let iposLastUpdated = '2026-06-01';
            if (window.IPO_DATA) {
                iposLastUpdated = window.IPO_DATA.lastUpdated;
            }
            document.getElementById('last-updated-date').textContent = iposLastUpdated;
            
            // Update publication timestamp with current date and time
            const now = new Date();
            const formattedTime = now.toLocaleDateString() + ' ' + now.toLocaleTimeString();
            const timestampEl = document.getElementById('publication-timestamp');
            if (timestampEl) timestampEl.textContent = formattedTime;
            
            populateIposStats();
            renderIposTable();
            return;
        }
        
        // Restore standard view grid and controls
        if (stockGrid) stockGrid.style.display = 'grid';
        if (shortsGrid) shortsGrid.style.display = 'none';
        if (performanceGrid) performanceGrid.style.display = 'none';
        if (iposGrid) iposGrid.style.display = 'none';
        if (controlsBar) controlsBar.style.display = 'flex';
        
        // Restore standard overview stats labels
        const cards = document.querySelectorAll('.quick-overview-bar .overview-card');
        if (cards.length >= 4) {
            cards[0].querySelector('h4').textContent = "Total Analyzed";
            cards[0].querySelector('.value').style.color = 'var(--text-primary)';
            
            cards[1].querySelector('h4').textContent = "Buy Candidates";
            cards[1].querySelector('.value').style.color = 'var(--color-buy)';
            
            cards[2].querySelector('h4').textContent = "Neutral / Holds";
            cards[2].querySelector('.value').style.color = 'var(--color-hold)';
            
            cards[3].querySelector('h4').textContent = "Sell Candidates";
            cards[3].querySelector('.value').style.color = 'var(--color-sell)';
        }
        
        if (name === 'space') {
            document.getElementById('tab-space').classList.add('active');
            
            if (!window.STOCK_DATA) {
                showErrorCard("Space Technical Data not found. Please run <code>python analyze.py</code> first.");
                return;
            }
            
            lastUpdated = window.STOCK_DATA.lastUpdated;
            stocksMap = window.STOCK_DATA.stocks;
            stocksList = Object.values(stocksMap);
            
            // Update title and subtitle
            document.querySelector('.title-desc h1').textContent = "Orbital Alpha";
            document.querySelector('.title-desc p').textContent = "Advanced Space & Aerospace Technical Analysis Intelligence";
            
            // Update Sector Filter Pills
            const filterButtons = document.querySelectorAll('#filter-container .filter-btn');
            if (filterButtons.length >= 4) {
                filterButtons[2].setAttribute('data-filter', 'Defense Giant');
                filterButtons[2].innerHTML = 'Defense Giants';
                filterButtons[3].setAttribute('data-filter', 'Aerospace Supplier');
                filterButtons[3].innerHTML = 'Suppliers';
            }
            
        } else if (name === 'quantum') {
            const tabQuantum = document.getElementById('tab-quantum');
            if (tabQuantum) tabQuantum.classList.add('active');
            
            if (!window.QUANTUM_DATA) {
                showErrorCard("Quantum Mechanics Data not found. Please run <code>python analyze_quantum.py</code> first.");
                return;
            }
            
            lastUpdated = window.QUANTUM_DATA.lastUpdated;
            stocksMap = window.QUANTUM_DATA.stocks;
            stocksList = Object.values(stocksMap);
            
            // Update title and subtitle
            document.querySelector('.title-desc h1').textContent = "Quantum Mechanics";
            document.querySelector('.title-desc p').textContent = "Advanced Quantum Computing Technical Stock Analysis Report";
            
            // Update Sector Filter Pills
            const filterButtons = document.querySelectorAll('#filter-container .filter-btn');
            if (filterButtons.length >= 4) {
                filterButtons[2].setAttribute('data-filter', 'Quantum Giant');
                filterButtons[2].innerHTML = 'Quantum Giants';
                filterButtons[3].setAttribute('data-filter', 'Quantum ETF');
                filterButtons[3].innerHTML = 'ETFs';
            }
        }
        
        // Reset filters
        activeFilter = 'all';
        activeSignalFilter = 'all';
        searchQuery = '';
        document.getElementById('search-input').value = '';
        document.getElementById('sort-select').value = 'score-desc';
        document.querySelectorAll('#filter-container .filter-btn').forEach((btn, idx) => {
            if (idx === 0) btn.classList.add('active');
            else btn.classList.remove('active');
        });
        
        // Set last updated date in UI
        document.getElementById('last-updated-date').textContent = lastUpdated;
        
        // Update publication timestamp with current date and time
        const now = new Date();
        const formattedTime = now.toLocaleDateString() + ' ' + now.toLocaleTimeString();
        const timestampEl = document.getElementById('publication-timestamp');
        if (timestampEl) timestampEl.textContent = formattedTime;
        
        populateOverviewStats();
        renderStockGrid();
    }
    
    function showErrorCard(message) {
        document.getElementById('last-updated-date').textContent = "Offline";
        document.getElementById('stat-total').textContent = "0";
        document.getElementById('stat-buys').textContent = "0";
        document.getElementById('stat-holds').textContent = "0";
        document.getElementById('stat-sells').textContent = "0";
        
        document.getElementById('stock-grid-container').innerHTML = `
            <div style="grid-column: 1/-1; text-align: center; padding: 60px; color: var(--color-sell);">
                <h3>Data Pipeline Error</h3>
                <p style="margin-top: 8px; color: var(--text-secondary);">
                    ${message}
                </p>
            </div>
        `;
    }

    // Tab Click Event Listeners
    const tabSpace = document.getElementById('tab-space');
    const tabQuantum = document.getElementById('tab-quantum');
    const tabShorts = document.getElementById('tab-shorts');
    const tabPerf = document.getElementById('tab-performance');
    const tabIpos = document.getElementById('tab-ipos');
    if (tabSpace) tabSpace.addEventListener('click', () => loadDataset('space'));
    if (tabQuantum) tabQuantum.addEventListener('click', () => loadDataset('quantum'));
    if (tabShorts) tabShorts.addEventListener('click', () => loadDataset('shorts'));
    if (tabPerf) tabPerf.addEventListener('click', () => loadDataset('performance'));
    if (tabIpos) tabIpos.addEventListener('click', () => loadDataset('ipos'));

    // 2. Populate Header Stats Overview
    function populateOverviewStats() {
        const total = stocksList.length;
        const buys = stocksList.filter(s => s.signal === 'BUY').length;
        const holds = stocksList.filter(s => s.signal === 'HOLD').length;
        const sells = stocksList.filter(s => s.signal === 'SELL').length;

        document.getElementById('stat-total').textContent = total;
        document.getElementById('stat-buys').textContent = buys;
        document.getElementById('stat-holds').textContent = holds;
        document.getElementById('stat-sells').textContent = sells;
    }
    
    // Initial Load: Check for URL query parameter 'tab', fallback to 'space'
    const urlParams = new URLSearchParams(window.location.search);
    const initialTab = urlParams.get('tab') || 'space';
    if (initialTab === 'quantum') {
        loadDataset('quantum');
    } else if (initialTab === 'shorts') {
        loadDataset('shorts');
    } else if (initialTab === 'performance') {
        loadDataset('performance');
    } else if (initialTab === 'ipos') {
        loadDataset('ipos');
    } else {
        loadDataset('space');
    }

    // Helper to get signal label CSS class
    function getSignalClass(signal) {
        return signal.toLowerCase();
    }

    // Helper to map score (-1.0 to 1.0) to bar percentage (0% to 100%)
    function calculateScorePercent(score) {
        // maps -1.0 to 0%, 0.0 to 50%, 1.0 to 100%
        return ((score + 1) / 2) * 100;
    }

    // 3. Render Stock Grid
    function renderStockGrid() {
        const grid = document.getElementById('stock-grid-container');
        grid.innerHTML = '';

        // Filter list
        let filteredStocks = stocksList.filter(stock => {
            // Sector filter
            if (activeFilter !== 'all' && stock.category !== activeFilter) {
                return false;
            }
            // Signal filter
            if (activeSignalFilter !== 'all' && stock.signal !== activeSignalFilter) {
                return false;
            }
            // Search query filter
            if (searchQuery) {
                const query = searchQuery.toLowerCase();
                const tickerMatch = stock.ticker.toLowerCase().includes(query);
                const nameMatch = stock.name.toLowerCase().includes(query);
                if (!tickerMatch && !nameMatch) return false;
            }
            return true;
        });

        // Sort list
        filteredStocks.sort((a, b) => {
            switch (currentSort) {
                case 'score-desc':
                    return b.compositeScore - a.compositeScore;
                case 'score-asc':
                    return a.compositeScore - b.compositeScore;
                case 'return-desc':
                    return b.changePercent - a.changePercent;
                case 'return-asc':
                    return a.changePercent - b.changePercent;
                case 'ticker-asc':
                    return a.ticker.localeCompare(b.ticker);
                default:
                    return b.compositeScore - a.compositeScore;
            }
        });

        if (filteredStocks.length === 0) {
            grid.innerHTML = `
                <div class="no-results">
                    <svg viewBox="0 0 24 24">
                        <path d="M15.5 14h-.79l-.28-.27C15.41 12.59 16 11.11 16 9.5 16 5.91 13.09 3 9.5 3S3 5.91 3 9.5 5.91 16 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/>
                    </svg>
                    <h3 class="outfit-font">No Space Stocks Found</h3>
                    <p style="margin-top: 6px;">Adjust your filters or try a different search term.</p>
                </div>
            `;
            return;
        }

        filteredStocks.forEach(stock => {
            const card = document.createElement('div');
            card.className = `stock-card card-${getSignalClass(stock.signal)}`;
            card.setAttribute('data-ticker', stock.ticker);

            const isPositive = stock.changePercent >= 0;
            const scorePercent = calculateScorePercent(stock.compositeScore);

            // Mini rating tags helper
            const rsiScoreClass = stock.indicators.RSI.score > 0 ? 'buy' : (stock.indicators.RSI.score < 0 ? 'sell' : 'hold');
            const macdScoreClass = stock.indicators.MACD.score > 0 ? 'buy' : (stock.indicators.MACD.score < 0 ? 'sell' : 'hold');
            const bbScoreClass = stock.indicators.Bollinger.score > 0 ? 'buy' : (stock.indicators.Bollinger.score < 0 ? 'sell' : 'hold');

            card.innerHTML = `
                <div class="card-header">
                    <div class="ticker-area">
                        <span class="ticker-symbol">${stock.ticker}</span>
                        <span class="company-name" title="${stock.name}">${stock.name}</span>
                    </div>
                    <span class="signal-badge ${getSignalClass(stock.signal)}">
                        <span class="signal-dot ${getSignalClass(stock.signal)}"></span>
                        ${stock.signal}
                    </span>
                </div>

                <span class="category-tag" style="align-self: flex-start;">${stock.category}</span>

                <div class="card-price-row">
                    <div class="price-main">$${stock.price.toFixed(2)}</div>
                    <div class="price-change ${isPositive ? 'positive' : 'negative'}">
                        ${isPositive ? '▲' : '▼'} ${isPositive ? '+' : ''}${stock.changePercent.toFixed(2)}%
                    </div>
                </div>

                <div class="score-container">
                    <div class="score-header">
                        <span>Consensus Score</span>
                        <strong>${(stock.compositeScore * 100).toFixed(0)}%</strong>
                    </div>
                    <div class="score-bar-bg">
                        <div class="score-bar-fill ${getSignalClass(stock.signal)}" style="width: ${scorePercent}%"></div>
                    </div>
                </div>

                <div class="card-indicators-footer">
                    <div class="indicator-mini-pill">
                        <span class="indicator-mini-label">RSI(14)</span>
                        <span class="indicator-mini-val ${rsiScoreClass}">${stock.indicators.RSI.value.toFixed(1)}</span>
                    </div>
                    <div class="indicator-mini-pill">
                        <span class="indicator-mini-label">MACD</span>
                        <span class="indicator-mini-val ${macdScoreClass}">${stock.indicators.MACD.score > 0 ? 'BUY' : (stock.indicators.MACD.score < 0 ? 'SELL' : 'HOLD')}</span>
                    </div>
                    <div class="indicator-mini-pill">
                        <span class="indicator-mini-label">B-Bands</span>
                        <span class="indicator-mini-val ${bbScoreClass}">${stock.indicators.Bollinger.score > 0 ? 'BUY' : (stock.indicators.Bollinger.score < 0 ? 'SELL' : 'HOLD')}</span>
                    </div>
                </div>
            `;

            card.addEventListener('click', () => openStockModal(stock.ticker));
            grid.appendChild(card);
        });
    }

    renderStockGrid();

    // 4. Filters & Controls Event Listeners
    const filterContainer = document.getElementById('filter-container');
    filterContainer.addEventListener('click', (e) => {
        const btn = e.target.closest('.filter-btn');
        if (!btn) return;

        // Deactivate all buttons
        filterContainer.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');

        // Apply filters
        const category = btn.getAttribute('data-filter');
        const signal = btn.getAttribute('data-signal');

        if (category) {
            activeFilter = category;
            activeSignalFilter = 'all';
        } else if (signal) {
            activeSignalFilter = signal;
            activeFilter = 'all';
        } else {
            activeFilter = 'all';
            activeSignalFilter = 'all';
        }

        renderStockGrid();
    });

    // Search Input
    document.getElementById('search-input').addEventListener('input', (e) => {
        searchQuery = e.target.value;
        renderStockGrid();
    });

    // Sort Dropdown
    document.getElementById('sort-select').addEventListener('change', (e) => {
        currentSort = e.target.value;
        renderStockGrid();
    });

    // Modal Control Elements
    const modal = document.getElementById('detail-modal');
    const closeModalBtn = document.getElementById('close-modal-btn');
    
    closeModalBtn.addEventListener('click', closeStockModal);
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            closeStockModal();
        }
    });

    // 5. Open Detailed Stock Modal
    function openStockModal(ticker) {
        const stock = stocksMap[ticker];
        if (!stock) return;

        activeChartStock = stock;
        activeChartType = 'price-bb'; // Default chart view

        const modalBody = document.getElementById('modal-body-content');
        const isPositive = stock.changePercent >= 0;

        // Render basic panel layout
        modalBody.innerHTML = `
            <!-- Top Details -->
            <div class="modal-stock-info">
                <div>
                    <h2 class="modal-ticker outfit-font">${stock.ticker}</h2>
                    <p class="modal-company">${stock.name}</p>
                    <span class="category-tag" style="margin-top: 6px; display: inline-block;">${stock.category}</span>
                </div>
                <div style="text-align: right;">
                    <div style="font-size: 2.2rem; font-weight: 700; color: white;">$${stock.price.toFixed(2)}</div>
                    <div class="price-change ${isPositive ? 'positive' : 'negative'}" style="justify-content: flex-end; font-size: 1.1rem; margin-top: 4px;">
                        ${isPositive ? '▲' : '▼'} ${isPositive ? '+' : ''}${stock.changePercent.toFixed(2)}%
                    </div>
                </div>
            </div>

            <!-- Consensus Score Info -->
            <div style="background: rgba(124, 77, 255, 0.05); border: 1px solid var(--color-primary-glow); border-radius: 16px; padding: 20px; display: flex; align-items: center; justify-content: space-between;">
                <div>
                    <h4 class="outfit-font" style="font-size: 0.9rem; text-transform: uppercase; color: var(--text-secondary); letter-spacing: 0.5px;">Indicators Consensus</h4>
                    <p style="font-size: 0.85rem; color: var(--text-muted); margin-top: 4px;">Aggregated rating from 6 distinct GitHub-proven mathematical signals.</p>
                </div>
                <div style="text-align: right; display: flex; flex-direction: column; align-items: flex-end; gap: 4px;">
                    <span class="signal-badge ${getSignalClass(stock.signal)}" style="font-size: 0.9rem; padding: 8px 18px;">
                        <span class="signal-dot ${getSignalClass(stock.signal)}"></span>
                        ${stock.signal}
                    </span>
                    <span style="font-size: 0.8rem; color: var(--text-muted);">Composite Rating: <strong>${(stock.compositeScore * 100).toFixed(0)}%</strong></span>
                </div>
            </div>

            <!-- Price Detail Parameters -->
            <div class="price-details-grid">
                <div class="price-detail-item">
                    <span class="price-detail-label">Daily Open</span>
                    <span class="price-detail-value">$${stock.open.toFixed(2)}</span>
                </div>
                <div class="price-detail-item">
                    <span class="price-detail-label">Daily High</span>
                    <span class="price-detail-value">$${stock.high.toFixed(2)}</span>
                </div>
                <div class="price-detail-item">
                    <span class="price-detail-label">Daily Low</span>
                    <span class="price-detail-value">$${stock.low.toFixed(2)}</span>
                </div>
                <div class="price-detail-item">
                    <span class="price-detail-label">Volume</span>
                    <span class="price-detail-value">${stock.volume.toLocaleString()}</span>
                </div>
            </div>

            <!-- Interactive Chart Area -->
            <div>
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                    <h3 class="outfit-font" style="font-size: 1.1rem; color: white;">Technical Charts (60-Day History)</h3>
                    <!-- Chart Toggles -->
                    <div style="display: flex; gap: 6px; background: rgba(255,255,255,0.02); border: 1px solid var(--border-color); padding: 4px; border-radius: 8px;">
                        <button class="filter-btn active" id="btn-chart-price" style="padding: 6px 12px; font-size: 0.75rem; border-radius: 6px;">Price & BB</button>
                        <button class="filter-btn" id="btn-chart-rsi" style="padding: 6px 12px; font-size: 0.75rem; border-radius: 6px;">RSI</button>
                        <button class="filter-btn" id="btn-chart-macd" style="padding: 6px 12px; font-size: 0.75rem; border-radius: 6px;">MACD</button>
                    </div>
                </div>
                <div class="chart-container">
                    <canvas id="stock-chart"></canvas>
                </div>
            </div>

            <!-- Comprehensive Technical Signals Breakdown -->
            <div>
                <h3 class="outfit-font" style="font-size: 1.1rem; color: white; margin-bottom: 16px;">Core Technical Indicator Signals</h3>
                <div class="indicators-list">
                    <!-- RSI -->
                    ${renderIndicatorRow("Relative Strength Index (RSI-14)", stock.indicators.RSI, `Current Value: <strong>${stock.indicators.RSI.value.toFixed(2)}</strong>`)}
                    
                    <!-- MACD -->
                    ${renderIndicatorRow("MACD Momentum (12, 26, 9)", stock.indicators.MACD, `MACD Value: <strong>${stock.indicators.MACD.value.toFixed(4)}</strong> | Signal Line: <strong>${stock.indicators.MACD.signal.toFixed(4)}</strong>`)}
                    
                    <!-- Bollinger Bands -->
                    ${renderIndicatorRow("Volatility Bollinger Bands (20, 2)", stock.indicators.Bollinger, `Lower Band: <strong>$${stock.indicators.Bollinger.lower.toFixed(2)}</strong> | Middle: <strong>$${stock.indicators.Bollinger.middle.toFixed(2)}</strong> | Upper: <strong>$${stock.indicators.Bollinger.upper.toFixed(2)}</strong>`)}
                    
                    <!-- Stochastic -->
                    ${renderIndicatorRow("Stochastic Oscillator (14, 3)", stock.indicators.Stochastic, `%K Line: <strong>${stock.indicators.Stochastic.k.toFixed(1)}</strong> | %D Line: <strong>${stock.indicators.Stochastic.d.toFixed(1)}</strong>`)}
                    
                    <!-- EMA -->
                    ${renderIndicatorRow("Exponential Moving Average Crossover", stock.indicators.EMA, `EMA 9-day: <strong>$${stock.indicators.EMA.ema9.toFixed(2)}</strong> | EMA 21-day: <strong>$${stock.indicators.EMA.ema21.toFixed(2)}</strong>`)}
                    
                    <!-- ADX -->
                    ${renderIndicatorRow("ADX Trend Strength & Direction (14)", stock.indicators.ADX, `ADX Strength: <strong>${stock.indicators.ADX.value.toFixed(1)}</strong> (+DI: ${stock.indicators.ADX.plus_di.toFixed(1)} vs -DI: ${stock.indicators.ADX.minus_di.toFixed(1)})`)}
                </div>
            </div>
        `;

        // Add modal classes to show slide-over
        modal.classList.add('open');
        document.body.style.overflow = 'hidden'; // Lock background scrolling

        // Setup chart toggles listeners
        document.getElementById('btn-chart-price').addEventListener('click', (e) => switchChartTab(e, 'price-bb'));
        document.getElementById('btn-chart-rsi').addEventListener('click', (e) => switchChartTab(e, 'rsi'));
        document.getElementById('btn-chart-macd').addEventListener('click', (e) => switchChartTab(e, 'macd'));

        // Draw initial chart
        drawChart();
    }

    function closeStockModal() {
        modal.classList.remove('open');
        document.body.style.overflow = ''; // Unlock background scrolling
        
        // Clean up Chart instance
        if (myChart) {
            myChart.destroy();
            myChart = null;
        }
        activeChartStock = null;
    }

    // Helper to render indicator rows inside modal
    function renderIndicatorRow(name, indicator, parameterString) {
        let signalText = 'HOLD';
        let ratingClass = 'hold';
        if (indicator.score >= 0.35) {
            signalText = 'BUY';
            ratingClass = 'buy';
        } else if (indicator.score <= -0.35) {
            signalText = 'SELL';
            ratingClass = 'sell';
        }

        return `
            <div class="indicator-row">
                <div class="indicator-row-header">
                    <span class="indicator-name">${name}</span>
                    <span class="indicator-score-badge ${ratingClass}">${signalText}</span>
                </div>
                <div class="indicator-explanation">${indicator.explanation}</div>
                <div class="indicator-values">${parameterString}</div>
            </div>
        `;
    }

    // Chart tab switches
    function switchChartTab(e, type) {
        // Update active class on buttons
        const container = e.target.parentElement;
        container.querySelectorAll('button').forEach(btn => btn.classList.remove('active'));
        e.target.classList.add('active');

        activeChartType = type;
        drawChart();
    }

    // 6. Draw Chart.js Graphs
    function drawChart() {
        const stock = activeChartStock;
        if (!stock) return;

        const ctx = document.getElementById('stock-chart').getContext('2d');
        
        // Destroy existing chart to prevent overlay issues
        if (myChart) {
            myChart.destroy();
        }

        const labels = stock.history.map(h => h.date);
        const prices = stock.history.map(h => h.close);
        const volumes = stock.history.map(h => h.volume);

        // Styling for Chart.js
        Chart.defaults.color = '#9ca3af';
        Chart.defaults.font.family = "'Inter', sans-serif";

        let chartData = {};
        let chartOptions = {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                intersect: false,
                mode: 'index',
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        boxWidth: 12,
                        font: { size: 10 }
                    }
                },
                tooltip: {
                    backgroundColor: '#111224',
                    titleColor: '#ffffff',
                    bodyColor: '#e5e7eb',
                    borderColor: 'rgba(255,255,255,0.08)',
                    borderWidth: 1,
                    padding: 10
                }
            },
            scales: {
                x: {
                    grid: { display: false }
                }
            }
        };

        if (activeChartType === 'price-bb') {
            // Price and Bollinger Bands
            const bbUpper = stock.history.map(h => h.bb_upper);
            const bbLower = stock.history.map(h => h.bb_lower);
            const bbMiddle = stock.history.map(h => h.bb_middle);

            chartData = {
                labels: labels,
                datasets: [
                    {
                        label: 'Stock Close Price ($)',
                        data: prices,
                        borderColor: '#00f5ff',
                        borderWidth: 2.5,
                        pointRadius: 0,
                        pointHoverRadius: 5,
                        fill: false,
                        yAxisID: 'y'
                    },
                    {
                        label: 'BB Upper (20,2)',
                        data: bbUpper,
                        borderColor: 'rgba(124, 77, 255, 0.4)',
                        borderWidth: 1.2,
                        borderDash: [4, 4],
                        pointRadius: 0,
                        fill: false,
                        yAxisID: 'y'
                    },
                    {
                        label: 'BB Middle (SMA 20)',
                        data: bbMiddle,
                        borderColor: 'rgba(124, 77, 255, 0.2)',
                        borderWidth: 1,
                        pointRadius: 0,
                        fill: false,
                        yAxisID: 'y'
                    },
                    {
                        label: 'BB Lower (20,2)',
                        data: bbLower,
                        borderColor: 'rgba(124, 77, 255, 0.4)',
                        borderWidth: 1.2,
                        borderDash: [4, 4],
                        pointRadius: 0,
                        fill: false,
                        yAxisID: 'y'
                    },
                    {
                        label: 'Volume',
                        data: volumes,
                        type: 'bar',
                        backgroundColor: 'rgba(255, 255, 255, 0.05)',
                        borderColor: 'transparent',
                        yAxisID: 'yVolume',
                        barPercentage: 0.6
                    }
                ]
            };

            chartOptions.scales.y = {
                type: 'linear',
                display: true,
                position: 'left',
                grid: { color: 'rgba(255, 255, 255, 0.04)' }
            };
            chartOptions.scales.yVolume = {
                type: 'linear',
                display: false, // Hidden but used for scaling bar volume
                position: 'right',
                grid: { drawOnChartArea: false },
                max: Math.max(...volumes) * 4 // Compresses the bar heights at the bottom
            };

        } else if (activeChartType === 'rsi') {
            // RSI Chart
            const rsis = stock.history.map(h => h.rsi);
            const rsiOverbought = Array(labels.length).fill(70);
            const rsiOversold = Array(labels.length).fill(30);

            chartData = {
                labels: labels,
                datasets: [
                    {
                        label: 'RSI (14)',
                        data: rsis,
                        borderColor: '#7c4dff',
                        borderWidth: 2,
                        pointRadius: 0,
                        pointHoverRadius: 5,
                        fill: false,
                        yAxisID: 'y'
                    },
                    {
                        label: 'Overbought (70)',
                        data: rsiOverbought,
                        borderColor: 'rgba(255, 23, 68, 0.35)',
                        borderWidth: 1,
                        borderDash: [5, 5],
                        pointRadius: 0,
                        fill: false,
                        yAxisID: 'y'
                    },
                    {
                        label: 'Oversold (30)',
                        data: rsiOversold,
                        borderColor: 'rgba(0, 230, 118, 0.35)',
                        borderWidth: 1,
                        borderDash: [5, 5],
                        pointRadius: 0,
                        fill: false,
                        yAxisID: 'y'
                    }
                ]
            };

            chartOptions.scales.y = {
                min: 0,
                max: 100,
                ticks: { stepSize: 10 },
                grid: { color: 'rgba(255, 255, 255, 0.04)' }
            };

        } else if (activeChartType === 'macd') {
            // MACD Chart
            const macds = stock.history.map(h => h.macd);
            const signals = stock.history.map(h => h.macd_signal);
            const hists = stock.history.map(h => h.macd - h.macd_signal);

            chartData = {
                labels: labels,
                datasets: [
                    {
                        label: 'MACD Line',
                        data: macds,
                        borderColor: '#00f5ff',
                        borderWidth: 1.8,
                        pointRadius: 0,
                        fill: false
                    },
                    {
                        label: 'Signal Line',
                        data: signals,
                        borderColor: '#ffc400',
                        borderWidth: 1.5,
                        pointRadius: 0,
                        fill: false
                    },
                    {
                        label: 'Histogram',
                        data: hists,
                        type: 'bar',
                        backgroundColor: hists.map(v => v >= 0 ? 'rgba(0, 230, 118, 0.4)' : 'rgba(255, 23, 68, 0.4)'),
                        borderColor: 'transparent',
                        barPercentage: 0.6
                    }
                ]
            };

            chartOptions.scales.y = {
                grid: { color: 'rgba(255, 255, 255, 0.04)' }
            };
        }

        myChart = new Chart(ctx, {
            type: 'line',
            data: chartData,
            options: chartOptions
        });
    }

    // ==========================================================================
    // APEX SHORTS SUPPORT FUNCTIONS
    // ==========================================================================

    function populateShortsStats() {
        // Merge space, quantum and IPO stocks
        let allStocks = [];
        if (window.STOCK_DATA && window.STOCK_DATA.stocks) {
            allStocks = allStocks.concat(Object.values(window.STOCK_DATA.stocks));
        }
        if (window.QUANTUM_DATA && window.QUANTUM_DATA.stocks) {
            allStocks = allStocks.concat(Object.values(window.QUANTUM_DATA.stocks));
        }
        if (window.IPO_DATA && window.IPO_DATA.ipos) {
            allStocks = allStocks.concat(Object.values(window.IPO_DATA.ipos));
        }
        
        // Remove duplicates if any (by ticker)
        const uniqueStocks = [];
        const seenTickers = new Set();
        for (const stock of allStocks) {
            if (!seenTickers.has(stock.ticker)) {
                seenTickers.add(stock.ticker);
                uniqueStocks.push(stock);
            }
        }
        
        const speculative = uniqueStocks.filter(s => s.price >= 1.0 && s.price <= 10.0);
        const midtier = uniqueStocks.filter(s => s.price >= 11.0 && s.price <= 20.0);
        const highbeta = uniqueStocks.filter(s => s.price >= 21.0 && s.price <= 50.0);
        const totalOpportunities = speculative.length + midtier.length + highbeta.length;

        // Populate quick overview bar
        document.getElementById('stat-total').textContent = totalOpportunities;
        
        // Change the labels dynamically for the short view!
        const cards = document.querySelectorAll('.quick-overview-bar .overview-card');
        if (cards.length >= 4) {
            // Card 1: Total
            cards[0].querySelector('h4').textContent = "Total Opportunities";
            cards[0].querySelector('.value').style.color = 'var(--text-primary)';
            
            // Card 2: Speculative List
            cards[1].querySelector('h4').textContent = "Speculative ($1-$10)";
            cards[1].querySelector('.value').textContent = speculative.length;
            cards[1].querySelector('.value').style.color = '#ff5252';
            
            // Card 3: Mid-tier List
            cards[2].querySelector('h4').textContent = "Mid-tier ($11-$20)";
            cards[2].querySelector('.value').textContent = midtier.length;
            cards[2].querySelector('.value').style.color = '#e040fb';
            
            // Card 4: High-Beta List
            cards[3].querySelector('h4').textContent = "High-Beta ($21-$50)";
            cards[3].querySelector('.value').textContent = highbeta.length;
            cards[3].querySelector('.value').style.color = '#00e5ff';
        }
    }

    function renderShortsGrid() {
        const listSpeculative = document.getElementById('shorts-list-speculative');
        const listMidtier = document.getElementById('shorts-list-midtier');
        const listHighbeta = document.getElementById('shorts-list-highbeta');
        
        if (listSpeculative) listSpeculative.innerHTML = '';
        if (listMidtier) listMidtier.innerHTML = '';
        if (listHighbeta) listHighbeta.innerHTML = '';
        
        // Merge space, quantum and IPO stocks
        let allStocks = [];
        if (window.STOCK_DATA && window.STOCK_DATA.stocks) {
            allStocks = allStocks.concat(Object.values(window.STOCK_DATA.stocks));
        }
        if (window.QUANTUM_DATA && window.QUANTUM_DATA.stocks) {
            allStocks = allStocks.concat(Object.values(window.QUANTUM_DATA.stocks));
        }
        if (window.IPO_DATA && window.IPO_DATA.ipos) {
            allStocks = allStocks.concat(Object.values(window.IPO_DATA.ipos));
        }
        
        // Remove duplicates if any (by ticker)
        const uniqueStocks = [];
        const seenTickers = new Set();
        for (const stock of allStocks) {
            if (!seenTickers.has(stock.ticker)) {
                seenTickers.add(stock.ticker);
                uniqueStocks.push(stock);
            }
        }
        
        const speculativeCandidates = uniqueStocks.filter(s => s.price >= 1.0 && s.price <= 10.0);
        const midtierCandidates = uniqueStocks.filter(s => s.price >= 11.0 && s.price <= 20.0);
        const highbetaCandidates = uniqueStocks.filter(s => s.price >= 21.0 && s.price <= 50.0);
        
        // Sort all by percentAboveBB descending
        speculativeCandidates.sort((a, b) => {
            const aOver = a.shortAnalysis ? a.shortAnalysis.percentAboveBB : -999;
            const bOver = b.shortAnalysis ? b.shortAnalysis.percentAboveBB : -999;
            return bOver - aOver;
        });
        
        midtierCandidates.sort((a, b) => {
            const aOver = a.shortAnalysis ? a.shortAnalysis.percentAboveBB : -999;
            const bOver = b.shortAnalysis ? b.shortAnalysis.percentAboveBB : -999;
            return bOver - aOver;
        });
        
        highbetaCandidates.sort((a, b) => {
            const aOver = a.shortAnalysis ? a.shortAnalysis.percentAboveBB : -999;
            const bOver = b.shortAnalysis ? b.shortAnalysis.percentAboveBB : -999;
            return bOver - aOver;
        });
        
        // RENDER SPECULATIVE CANDIDATES
        if (listSpeculative) {
            if (speculativeCandidates.length === 0) {
                listSpeculative.innerHTML = `
                    <div class="no-candidates-msg">
                        <svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
                        </svg>
                        <span>No speculative micro-cap short setups detected ($1 - $10)</span>
                    </div>
                `;
            } else {
                speculativeCandidates.forEach(stock => {
                    const card = createShortCandidateCard(stock);
                    listSpeculative.appendChild(card);
                });
            }
        }
        
        // RENDER MID-TIER CANDIDATES
        if (listMidtier) {
            if (midtierCandidates.length === 0) {
                listMidtier.innerHTML = `
                    <div class="no-candidates-msg">
                        <svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
                        </svg>
                        <span>No mid-tier short setups detected ($11 - $20)</span>
                    </div>
                `;
            } else {
                midtierCandidates.forEach(stock => {
                    const card = createShortCandidateCard(stock);
                    listMidtier.appendChild(card);
                });
            }
        }
        
        // RENDER HIGH-BETA CANDIDATES
        if (listHighbeta) {
            if (highbetaCandidates.length === 0) {
                listHighbeta.innerHTML = `
                    <div class="no-candidates-msg">
                        <svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
                        </svg>
                        <span>No high-beta short setups detected ($21 - $50)</span>
                    </div>
                `;
            } else {
                highbetaCandidates.forEach(stock => {
                    const card = createShortCandidateCard(stock);
                    listHighbeta.appendChild(card);
                });
            }
        }
    }

    function createShortCandidateCard(stock) {
        const card = document.createElement('div');
        card.className = 'short-cand-card';
        
        const sa = stock.shortAnalysis || {
            percentAboveBB: -99,
            squeezeRisk: 'LOW',
            instPercent: 0,
            instSupport: 'LOW',
            majorBacking: 'None',
            hasBigNews: 'NO',
            latestHeadline: 'No significant news detected.',
            recommendedCover: stock.price * 0.9,
            shortStopLoss: stock.price * 1.1
        };
        
        const percentVal = sa.percentAboveBB;
        const isHighlyOverextended = percentVal >= 20.0;
        const isOverextended = percentVal >= 0.0;
        
        let overextensionText = '';
        let badgeClass = '';
        if (isOverextended) {
            overextensionText = `+${percentVal.toFixed(1)}% Above Band`;
            badgeClass = '';
        } else {
            overextensionText = `${percentVal.toFixed(1)}% Below Band`;
            badgeClass = 'negative-over';
        }
        
        const isNewsActive = sa.hasBigNews.includes('YES');
        const isPositive = stock.changePercent >= 0;
        
        // CSS coloring for Squeeze Risk
        let squeezeClass = 'squeeze-low';
        if (sa.squeezeRisk === 'HIGH') squeezeClass = 'squeeze-high';
        else if (sa.squeezeRisk === 'MODERATE') squeezeClass = 'squeeze-moderate';
        
        // CSS coloring for Institutional backing
        let backingClass = '';
        if (sa.instSupport === 'HIGH') backingClass = 'backing-high';
        
        card.innerHTML = `
            <div class="short-cand-header">
                <div class="short-cand-ticker-info">
                    <span class="short-cand-ticker">${stock.ticker}</span>
                    <span class="short-cand-name" title="${stock.name}">${stock.name}</span>
                </div>
                <div class="short-cand-overextension">
                    <span class="overextension-badge ${badgeClass}">
                        ${isHighlyOverextended ? '⚠️ ' : ''}${overextensionText}
                    </span>
                    <span class="overextension-label">BB Deviation</span>
                </div>
            </div>
            
            <div class="short-cand-price-row">
                <span class="short-cand-price">$${stock.price.toFixed(2)}</span>
                <span class="short-cand-change" style="color: ${isPositive ? 'var(--color-buy)' : 'var(--color-sell)'}; background: ${isPositive ? 'var(--color-buy-bg)' : 'var(--color-sell-bg)'};">
                    ${isPositive ? '▲' : '▼'} ${isPositive ? '+' : ''}${stock.changePercent.toFixed(2)}%
                </span>
            </div>
            
            <!-- Squeeze & Backing Grid -->
            <div class="short-cand-stats-grid">
                <div class="short-stat-box">
                    <span class="label">Squeeze Risk</span>
                    <span class="value ${squeezeClass}">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/>
                        </svg>
                        ${sa.squeezeRisk}
                    </span>
                </div>
                <div class="short-stat-box">
                    <span class="label">Institutional Support</span>
                    <span class="value ${backingClass}">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
                        </svg>
                        ${sa.instPercent.toFixed(1)}% (${sa.instSupport})
                    </span>
                </div>
            </div>
            
            <!-- Major Backing Info -->
            <div style="font-size: 0.72rem; color: var(--text-muted); padding: 0 4px; display: flex; align-items: flex-start; gap: 4px;">
                <strong style="color: var(--text-secondary); white-space: nowrap;">Key Backers:</strong>
                <span style="white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="${sa.majorBacking || 'Institutional / General Market'}">${sa.majorBacking || 'Institutional / General Market'}</span>
            </div>
            
            <!-- News Catalyst Banner -->
            <div class="news-catalyst-banner ${isNewsActive ? 'active' : ''}">
                <div class="catalyst-tag">
                    <span class="pulse-dot" style="width:6px; height:6px; background-color:${isNewsActive ? '#ff1744' : '#ff9100'}; border-radius:50%; display:inline-block;"></span>
                    ${isNewsActive ? 'Active News Catalyst' : 'Neutral News State'}
                </div>
                <div class="catalyst-headline" title="${sa.latestHeadline}">${sa.latestHeadline}</div>
            </div>
            
            <!-- Strategy execution block -->
            <div class="strategy-execution-block">
                <span class="strategy-title">Quant Mean Reversion Parameters</span>
                <div class="execution-targets">
                    <div class="target-item cover">
                        <span class="lbl">Recommended Cover (Exit Target)</span>
                        <span class="val">$${sa.recommendedCover.toFixed(2)}</span>
                    </div>
                    <div class="target-item stop">
                        <span class="lbl">Short Stop Loss</span>
                        <span class="val">$${sa.shortStopLoss.toFixed(2)}</span>
                    </div>
                </div>
            </div>
        `;
        
        card.addEventListener('click', () => openStockModal(stock.ticker));
        return card;
    }

    // ==========================================================================
    // PERFORMANCE AUDIT SUPPORT FUNCTIONS
    // ==========================================================================

    function populatePerformanceStats() {
        if (!window.PERFORMANCE_DATA) return;
        
        const summary = window.PERFORMANCE_DATA.summary;
        
        // Populate quick overview bar
        document.getElementById('stat-total').textContent = summary.totalTrades;
        
        const cards = document.querySelectorAll('.quick-overview-bar .overview-card');
        if (cards.length >= 4) {
            // Card 1: Total
            cards[0].querySelector('h4').textContent = "Total Audited Setups";
            cards[0].querySelector('.value').style.color = 'var(--text-primary)';
            
            // Card 2: Win Rate
            cards[1].querySelector('h4').textContent = "Quantitative Win Rate";
            cards[1].querySelector('.value').textContent = summary.winRate + "%";
            cards[1].querySelector('.value').style.color = summary.winRate >= 50 ? 'var(--color-buy)' : 'var(--color-hold)';
            
            // Card 3: Avg P&L
            cards[2].querySelector('h4').textContent = "Average Return";
            cards[2].querySelector('.value').textContent = (summary.avgReturn >= 0 ? "+" : "") + summary.avgReturn + "%";
            cards[2].querySelector('.value').style.color = summary.avgReturn >= 0 ? 'var(--color-buy)' : 'var(--color-sell)';
            
            // Card 4: Net Dollar Profit
            cards[3].querySelector('h4').textContent = "Paper Trade Net Return";
            cards[3].querySelector('.value').textContent = (summary.netProfitDollars >= 0 ? "+" : "") + summary.netReturnPct + "%";
            cards[3].querySelector('.value').style.color = summary.netProfitDollars >= 0 ? 'var(--color-buy)' : 'var(--color-sell)';
        }
    }

    function renderPerformanceGrid() {
        const tbody = document.getElementById('performance-tbody');
        if (!tbody) return;
        tbody.innerHTML = '';
        
        if (!window.PERFORMANCE_DATA || !window.PERFORMANCE_DATA.trades) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="9" style="text-align: center; padding: 30px; color: var(--text-muted);">
                        No performance auditing database found. Please run <code>python backtest.py</code> first.
                    </td>
                </tr>
            `;
            return;
        }
        
        const trades = window.PERFORMANCE_DATA.trades;
        
        if (trades.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="9" style="text-align: center; padding: 30px; color: var(--text-muted);">
                        No historical trades have been simulated or logged yet.
                    </td>
                </tr>
            `;
            return;
        }
        
        trades.forEach(trade => {
            const tr = document.createElement('tr');
            tr.style.borderBottom = '1px solid rgba(255, 255, 255, 0.04)';
            tr.style.transition = 'var(--transition-smooth)';
            tr.style.cursor = 'pointer';
            
            // Hover highlighting
            tr.addEventListener('mouseenter', () => {
                tr.style.background = 'rgba(255, 255, 255, 0.02)';
            });
            tr.addEventListener('mouseleave', () => {
                tr.style.background = 'transparent';
            });
            
            const isWin = trade.outcome === 'WIN';
            const isLoss = trade.outcome === 'LOSS';
            let outcomeBadge = `<span style="color: var(--text-muted); font-weight: 600;">ACTIVE</span>`;
            if (isWin) {
                outcomeBadge = `<span style="background: var(--color-buy-bg); color: var(--color-buy); border: 1px solid rgba(0, 230, 118, 0.2); padding: 2px 8px; border-radius: 4px; font-weight: bold; font-size: 10px;">WIN</span>`;
            } else if (isLoss) {
                outcomeBadge = `<span style="background: var(--color-sell-bg); color: var(--color-sell); border: 1px solid rgba(255, 23, 68, 0.2); padding: 2px 8px; border-radius: 4px; font-weight: bold; font-size: 10px;">LOSS</span>`;
            }
            
            const signalClass = trade.signal.toLowerCase();
            const signalBadge = `<span style="display: inline-block; padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: bold; 
                                          background: ${trade.signal === 'BUY' ? 'var(--color-buy-bg)' : 'var(--color-sell-bg)'}; 
                                          color: ${trade.signal === 'BUY' ? 'var(--color-buy)' : 'var(--color-sell)'}; 
                                          border: 1px solid ${trade.signal === 'BUY' ? 'rgba(0, 230, 118, 0.2)' : 'rgba(255, 23, 68, 0.2)'};">
                                    ${trade.signal}
                                 </span>`;
                                 
            const returnColor = trade.pnl >= 0 ? 'var(--color-buy)' : 'var(--color-sell)';
            const returnText = `<strong style="color: ${returnColor};">${trade.pnl >= 0 ? '+' : ''}${trade.pnl.toFixed(2)}%</strong>`;
            
            tr.innerHTML = `
                <td style="padding: 12px 10px; vertical-align: middle;">
                    <strong style="color: #ffffff; font-size: 1.05rem;">${trade.ticker}</strong>
                    <span style="color: var(--text-secondary); font-size: 0.75rem; display: block; margin-top: 2px;">${trade.sector} Sector</span>
                </td>
                <td style="padding: 12px 10px; text-align: center; vertical-align: middle;">${signalBadge}</td>
                <td style="padding: 12px 10px; text-align: center; vertical-align: middle; color: var(--text-secondary);">${trade.entry_date}</td>
                <td style="padding: 12px 10px; text-align: right; vertical-align: middle; font-weight: 600;">$${trade.entry_price.toFixed(2)}</td>
                <td style="padding: 12px 10px; text-align: right; vertical-align: middle; color: var(--color-cyan); font-weight: 600;">$${trade.target.toFixed(2)}</td>
                <td style="padding: 12px 10px; text-align: center; vertical-align: middle; color: var(--text-secondary);">${trade.exit_date}</td>
                <td style="padding: 12px 10px; text-align: right; vertical-align: middle; font-weight: 600;">$${trade.exit_price.toFixed(2)}</td>
                <td style="padding: 12px 10px; text-align: center; vertical-align: middle;">${outcomeBadge}</td>
                <td style="padding: 12px 10px; text-align: right; vertical-align: middle;">${returnText}</td>
            `;
            
            tr.addEventListener('click', () => openStockModal(trade.ticker));
            tbody.appendChild(tr);
        });
        
        // Update audit timestamp to show live evaluation
        const auditEl = document.getElementById('audit-timestamp');
        if (auditEl && window.PERFORMANCE_DATA.summary) {
            auditEl.textContent = "Win Rate: " + window.PERFORMANCE_DATA.summary.winRate + "%";
        }
    }

    // ==========================================================================
    // RECENT IPOs SUPPORT FUNCTIONS
    // ==========================================================================

    function populateIposStats() {
        if (!window.IPO_DATA || !window.IPO_DATA.ipos) return;
        
        const iposList = Object.values(window.IPO_DATA.ipos);
        const total = iposList.length;
        const buys = iposList.filter(s => s.signal === 'BUY').length;
        const holds = iposList.filter(s => s.signal === 'HOLD').length;
        const sells = iposList.filter(s => s.signal === 'SELL').length;
        
        document.getElementById('stat-total').textContent = total;
        
        const cards = document.querySelectorAll('.quick-overview-bar .overview-card');
        if (cards.length >= 4) {
            cards[0].querySelector('h4').textContent = "Total IPOs Scanned";
            cards[0].querySelector('.value').style.color = 'var(--text-primary)';
            
            cards[1].querySelector('h4').textContent = "Buy Rated IPOs";
            cards[1].querySelector('.value').textContent = buys;
            cards[1].querySelector('.value').style.color = 'var(--color-buy)';
            
            cards[2].querySelector('h4').textContent = "Hold Rated IPOs";
            cards[2].querySelector('.value').textContent = holds;
            cards[2].querySelector('.value').style.color = 'var(--color-hold)';
            
            cards[3].querySelector('h4').textContent = "Sell Rated IPOs";
            cards[3].querySelector('.value').textContent = sells;
            cards[3].querySelector('.value').style.color = 'var(--color-sell)';
        }
    }

    function renderIposTable() {
        const tbody = document.getElementById('ipos-tbody');
        if (!tbody) return;
        tbody.innerHTML = '';
        
        if (!window.IPO_DATA || !window.IPO_DATA.ipos) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="9" style="text-align: center; padding: 30px; color: var(--text-muted);">
                        No IPO data found. Please run <code>python analyze_ipos.py</code> first.
                    </td>
                </tr>
            `;
            return;
        }
        
        const iposList = Object.values(window.IPO_DATA.ipos);
        
        if (iposList.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="9" style="text-align: center; padding: 30px; color: var(--text-muted);">
                        No recent IPO listings detected.
                    </td>
                </tr>
            `;
            return;
        }
        
        iposList.forEach(ipo => {
            const tr = document.createElement('tr');
            tr.style.borderBottom = '1px solid rgba(255, 255, 255, 0.04)';
            tr.style.transition = 'var(--transition-smooth)';
            tr.style.cursor = 'pointer';
            
            // Hover highlighting
            tr.addEventListener('mouseenter', () => {
                tr.style.background = 'rgba(255, 255, 255, 0.02)';
            });
            tr.addEventListener('mouseleave', () => {
                tr.style.background = 'transparent';
            });
            
            const isPositive = ipo.changePercent >= 0;
            const changeBadgeColor = isPositive ? 'var(--color-buy)' : 'var(--color-sell)';
            
            const consensusBadge = `<span style="display: inline-block; padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: bold; 
                                           background: ${ipo.signal === 'BUY' ? 'var(--color-buy-bg)' : (ipo.signal === 'SELL' ? 'var(--color-sell-bg)' : 'var(--color-hold-bg)')}; 
                                           color: ${ipo.signal === 'BUY' ? 'var(--color-buy)' : (ipo.signal === 'SELL' ? 'var(--color-sell)' : 'var(--color-hold)')}; 
                                           border: 1px solid ${ipo.signal === 'BUY' ? 'rgba(0, 230, 118, 0.2)' : (ipo.signal === 'SELL' ? 'rgba(255, 23, 68, 0.2)' : 'rgba(124, 77, 255, 0.2)')};">
                                    ${ipo.signal}
                                 </span>`;
                                 
            tr.innerHTML = `
                <td style="padding: 12px 10px; vertical-align: middle;">
                    <strong style="color: #ffffff; font-size: 1.05rem;">${ipo.ticker}</strong>
                    <span style="color: var(--text-secondary); font-size: 0.75rem; display: block; margin-top: 2px;">${ipo.name}</span>
                </td>
                <td style="padding: 12px 10px; vertical-align: middle; color: var(--text-secondary);">${ipo.sector}</td>
                <td style="padding: 12px 10px; text-align: right; vertical-align: middle; font-weight: 600;">$${ipo.ipo_price.toFixed(2)}</td>
                <td style="padding: 12px 10px; text-align: right; vertical-align: middle; font-weight: 700; color: #ffffff;">$${ipo.price.toFixed(2)}</td>
                <td style="padding: 12px 10px; text-align: right; vertical-align: middle; color: ${changeBadgeColor}; font-weight: 600;">
                    ${isPositive ? '+' : ''}${ipo.changePercent.toFixed(2)}%
                </td>
                <td style="padding: 12px 10px; text-align: right; vertical-align: middle; font-family: monospace; font-size: 0.8rem; color: var(--color-cyan);">
                    $${ipo.low_52w.toFixed(2)} - $${ipo.high_52w.toFixed(2)}
                </td>
                <td style="padding: 12px 10px; text-align: right; vertical-align: middle; color: var(--text-secondary);">${Math.round(ipo.avg_volume).toLocaleString()}</td>
                <td style="padding: 12px 10px; text-align: center; vertical-align: middle;">${consensusBadge}</td>
                <td style="padding: 12px 10px; vertical-align: middle; max-width: 250px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; color: var(--text-secondary);" title="${ipo.famous_news}">
                    ${ipo.famous_news}
                </td>
            `;
            
            // Clicking row opens detailed chart modal
            tr.addEventListener('click', () => {
                stocksMap[ipo.ticker] = ipo;
                openStockModal(ipo.ticker);
            });
            
            tbody.appendChild(tr);
        });
    }

});

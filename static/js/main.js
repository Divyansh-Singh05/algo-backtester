// DOM Elements
const symbolInput = document.getElementById('symbol');
const strategyTypeSelect = document.getElementById('strategy-type');
const predefinedStrategySection = document.getElementById('predefined-strategy');
const customStrategySection = document.getElementById('custom-strategy');
const strategySelect = document.getElementById('strategy');
const startDateInput = document.getElementById('start-date');
const endDateInput = document.getElementById('end-date');
const initialCashInput = document.getElementById('initial-cash');
const parametersContainer = document.getElementById('parameters-container');
const runBacktestButton = document.getElementById('run-backtest');
const equityCurveChart = document.getElementById('equity-curve');
const tradesTable = document.getElementById('trades').getElementsByTagName('tbody')[0];
const indicatorCheckboxes = document.querySelectorAll('input[name="indicator"]');

// Initialize Chart.js
let chart = null;

// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
    fetchStrategies();
    strategyTypeSelect.addEventListener('change', toggleStrategySection);
    indicatorCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', toggleIndicatorParams);
    });
    document.querySelectorAll('.add-condition').forEach(button => {
        button.addEventListener('click', addCondition);
    });
    runBacktestButton.addEventListener('click', runBacktest);
});

// Toggle between predefined and custom strategy sections
function toggleStrategySection() {
    const isCustom = strategyTypeSelect.value === 'custom';
    predefinedStrategySection.style.display = isCustom ? 'none' : 'block';
    customStrategySection.style.display = isCustom ? 'block' : 'none';
}

// Toggle indicator parameters visibility
function toggleIndicatorParams(event) {
    const paramsDiv = event.target.closest('.indicator-item').querySelector('.indicator-params');
    paramsDiv.style.display = event.target.checked ? 'block' : 'none';
}

// Add condition to buy/sell conditions list
function addCondition(event) {
    const conditionsList = event.target.closest('.conditions-list');
    const conditionItem = document.createElement('div');
    conditionItem.className = 'condition-item';
    conditionItem.innerHTML = `
        <select class="condition-type">
            <option value="price">Price</option>
            <option value="sma">SMA</option>
            <option value="rsi">RSI</option>
            <option value="macd">MACD</option>
        </select>
        <select class="condition-operator">
            <option value=">">&gt;</option>
            <option value="<">&lt;</option>
            <option value="=">==</option>
        </select>
        <input type="number" class="condition-value" step="0.01">
        <button type="button" class="remove-condition" onclick="removeCondition(this)">×</button>
    `;
    conditionsList.insertBefore(conditionItem, event.target);
}

// Remove condition from list
function removeCondition(button) {
    button.closest('.condition-item').remove();
}

// Fetch available strategies when page loads
async function fetchStrategies() {
    try {
        const response = await fetch('/api/strategies/');
        const data = await response.json();
        
        if (data.status === 'success' && Array.isArray(data.strategies)) {
            // Clear existing options
            strategySelect.innerHTML = '';
            
            // Add new options
            data.strategies.forEach(strategy => {
                const option = document.createElement('option');
                option.value = strategy;
                option.textContent = strategy.replace(/_/g, ' ');
                strategySelect.appendChild(option);
            });
        } else {
            console.error('Invalid response format:', data);
            alert('Failed to fetch available strategies');
        }
    } catch (error) {
        console.error('Error fetching strategies:', error);
        alert('Failed to fetch available strategies');
    }
}

// Build custom strategy object
function buildCustomStrategy() {
    const indicators = [];
    const buyConditions = [];
    const sellConditions = [];
    
    // Collect indicators
    indicatorCheckboxes.forEach(checkbox => {
        if (checkbox.checked) {
            const params = checkbox.closest('.indicator-item').querySelector('.indicator-params');
            const paramInputs = params.querySelectorAll('input');
            const indicator = {
                type: checkbox.value,
                parameters: Array.from(paramInputs).map(input => parseFloat(input.value))
            };
            indicators.push(indicator);
        }
    });
    
    // Collect buy conditions
    buyConditionsList.querySelectorAll('.condition-item').forEach(item => {
        const condition = {
            type: item.querySelector('.condition-type').value,
            operator: item.querySelector('.condition-operator').value,
            value: parseFloat(item.querySelector('.condition-value').value)
        };
        buyConditions.push(condition);
    });
    
    // Collect sell conditions
    sellConditionsList.querySelectorAll('.condition-item').forEach(item => {
        const condition = {
            type: item.querySelector('.condition-type').value,
            operator: item.querySelector('.condition-operator').value,
            value: parseFloat(item.querySelector('.condition-value').value)
        };
        sellConditions.push(condition);
    });
    
    return {
        indicators,
        buyConditions,
        sellConditions
    };
}

// Get CSRF token from cookie
function getCSRFToken() {
    const name = 'csrftoken';
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Run backtest
async function runBacktest() {
    const symbol = symbolInput.value.toUpperCase();
    const startDate = startDateInput.value;  // Format: YYYY-MM-DD
    const endDate = endDateInput.value;      // Format: YYYY-MM-DD
    const initialCash = parseFloat(initialCashInput.value);
    
    if (!symbol || !startDate || !endDate || !initialCash) {
        alert('Please fill in all required fields');
        return;
    }
    
    if (initialCash < 1000) {
        alert('Initial cash must be at least $1,000');
        return;
    }
    
    const isCustomStrategy = strategyTypeSelect.value === 'custom';
    const strategy = isCustomStrategy ? buildCustomStrategy() : {
        name: strategySelect.value,
        parameters: {}
    };
    
    try {
        runBacktestButton.disabled = true;
        runBacktestButton.textContent = 'Running...';
        
        // Format dates to ensure they're in YYYY-MM-DD format
        const formattedStartDate = new Date(startDate).toISOString().split('T')[0];
        const formattedEndDate = new Date(endDate).toISOString().split('T')[0];
        
        const response = await fetch('/api/backtest/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            body: JSON.stringify({
                symbol: symbol,
                strategy_name: isCustomStrategy ? 'custom' : strategy.name,
                parameters: isCustomStrategy ? strategy : strategy.parameters,
                start_date: formattedStartDate,
                end_date: formattedEndDate,
                initial_cash: initialCash
            })
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            updateResults(data.results);
        } else {
            throw new Error(data.message || 'Backtest failed');
        }
    } catch (error) {
        console.error('Error running backtest:', error);
        alert('Failed to run backtest: ' + error.message);
    } finally {
        runBacktestButton.disabled = false;
        runBacktestButton.textContent = 'Run Backtest';
    }
}

// Update results in the UI
function updateResults(results) {
    // Update metrics with safe null checks and default values
    document.getElementById('total-return').textContent = 
        results.total_return != null ? (results.total_return * 100).toFixed(2) + '%' : '-';
    document.getElementById('sharpe-ratio').textContent = 
        results.sharpe_ratio != null ? results.sharpe_ratio.toFixed(2) : '-';
    document.getElementById('max-drawdown').textContent = 
        results.max_drawdown != null ? (results.max_drawdown * 100).toFixed(2) + '%' : '-';
    document.getElementById('win-rate').textContent = 
        results.win_rate != null ? (results.win_rate * 100).toFixed(2) + '%' : '-';
    
    // Update equity curve chart if data exists
    if (results.equity_curve && Array.isArray(results.equity_curve)) {
        updateChart(results.equity_curve);
    }
    
    // Update trades table if trades exist
    if (results.trades && Array.isArray(results.trades)) {
        updateTradesTable(results.trades);
    }
}

// Update the equity curve chart
function updateChart(equityCurve) {
    const dates = equityCurve.map(point => point.date || '');
    const values = equityCurve.map(point => point.value || 0);
    
    if (chart) {
        chart.destroy();
    }
    
    chart = new Chart(equityCurveChart, {
        type: 'line',
        data: {
            labels: dates,
            datasets: [{
                label: 'Portfolio Value',
                data: values,
                borderColor: '#2563eb',
                backgroundColor: 'rgba(37, 99, 235, 0.1)',
                fill: true,
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                x: {
                    grid: {
                        display: false
                    }
                },
                y: {
                    grid: {
                        color: '#e2e8f0'
                    }
                }
            }
        }
    });
}

// Update the trades table
function updateTradesTable(trades) {
    tradesTable.innerHTML = '';
    
    trades.forEach(trade => {
        const row = tradesTable.insertRow();
        row.innerHTML = `
            <td>${trade.date || '-'}</td>
            <td>${trade.type || '-'}</td>
            <td>${trade.price != null ? trade.price.toFixed(2) : '-'}</td>
            <td>${trade.size != null ? trade.size : '-'}</td>
            <td class="${trade.pnl >= 0 ? 'text-green-600' : 'text-red-600'}">
                ${trade.pnl != null ? trade.pnl.toFixed(2) : '-'}
            </td>
        `;
    });
}

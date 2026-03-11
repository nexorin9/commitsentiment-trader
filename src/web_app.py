"""
Web Dashboard - Flask Application

使用 Flask 创建简单的 Web 仪表板，展示最新 sentiment score 和 trading signal。
"""

import os
from datetime import datetime
from typing import Dict, List, Optional

from flask import Flask, jsonify, render_template

from .data_pipeline import DataPipeline
from .signal_generator import TradingSignal

# Create Flask app
app = Flask(__name__, static_folder='../static', template_folder='../templates')

# Default configuration
DEFAULT_REPO = os.getenv('DEFAULT_REPO', 'tensorflow/tensorflow')
DEFAULT_SYMBOL = os.getenv('DEFAULT_SYMBOL', 'AAPL')
DEFAULT_THRESHOLD = float(os.getenv('DEFAULT_THRESHOLD', '0.3'))

# Cache for analysis results
_analysis_cache: Dict = {}
_cache_timestamp: Optional[datetime] = None
CACHE_DURATION_SECONDS = 300  # 5 minutes


@app.route('/')
def index():
    """Main route - display the dashboard."""
    return render_template(
        'index.html',
        default_repo=DEFAULT_REPO,
        default_symbol=DEFAULT_SYMBOL
    )


@app.route('/api/status')
def api_status():
    """API endpoint to get current status."""
    return jsonify({
        'status': 'ready',
        'version': '1.0.0',
        'default_repo': DEFAULT_REPO,
        'default_symbol': DEFAULT_SYMBOL,
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/analyze')
def api_analyze():
    """API endpoint to run analysis and return results."""
    global _analysis_cache, _cache_timestamp

    # Check cache
    if _analysis_cache and _cache_timestamp:
        elapsed = (datetime.now() - _cache_timestamp).total_seconds()
        if elapsed < CACHE_DURATION_SECONDS:
            return jsonify(_analysis_cache)

    # Run analysis
    try:
        pipeline = DataPipeline()
        owner, repo = DEFAULT_REPO.split('/')
        result = pipeline.fetch_and_process_repo(owner, repo)

        if "error" in result:
            return jsonify({
                'error': result['error'],
                'timestamp': datetime.now().isoformat()
            }), 500

        # Prepare data for frontend
        analysis_data = {
            'repo': f"{result['owner']}/{result['repo']}",
            'commits_count': result['commits_count'],
            'sentiment_analysis': result.get('sentiment_analysis', {}),
            'time_series': result.get('time_series', {}),
            'signals': result.get('signals', []),
            'latest_signal': result['signals'][-1] if result.get('signals', []) else None,
            'timestamp': datetime.now().isoformat()
        }

        # Update cache
        _analysis_cache = analysis_data
        _cache_timestamp = datetime.now()

        return jsonify(analysis_data)

    except Exception as e:
        return jsonify({
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@app.route('/api/signal')
def api_signal():
    """API endpoint to get latest signal."""
    try:
        pipeline = DataPipeline()
        owner, repo = DEFAULT_REPO.split('/')
        result = pipeline.fetch_and_process_repo(owner, repo)

        if "error" in result:
            return jsonify({'error': result['error']}), 500

        signals = result.get('signals', [])
        latest = signals[-1] if signals else None

        return jsonify({
            'latest_signal': latest,
            'signals_count': len(signals),
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        return jsonify({'error': str(e), 'timestamp': datetime.now().isoformat()}), 500


@app.route('/api/sentiment')
def api_sentiment():
    """API endpoint to get sentiment time series data."""
    try:
        pipeline = DataPipeline()
        owner, repo = DEFAULT_REPO.split('/')
        result = pipeline.fetch_and_process_repo(owner, repo)

        if "error" in result:
            return jsonify({'error': result['error']}), 500

        time_series = result.get('time_series', {})
        signals = result.get('signals', [])

        return jsonify({
            'time_series': time_series,
            'signals': signals,
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        return jsonify({'error': str(e), 'timestamp': datetime.now().isoformat()}), 500


def run_analysis(repo: str = DEFAULT_REPO, symbol: str = DEFAULT_SYMBOL) -> Dict:
    """
    Run analysis for a specific repository.

    Args:
        repo: GitHub repository (owner/repo)
        symbol: Stock symbol

    Returns:
        Analysis results dictionary
    """
    try:
        pipeline = DataPipeline()
        owner, repo_name = repo.split('/')
        result = pipeline.fetch_and_process_repo(owner, repo_name)

        if "error" in result:
            return {'error': result['error']}

        return {
            'repo': repo,
            'symbol': symbol,
            'result': result
        }
    except Exception as e:
        return {'error': str(e)}


if __name__ == '__main__':
    # Create templates directory if not exists
    templates_dir = os.path.join(os.path.dirname(__file__), '..', 'templates')
    os.makedirs(templates_dir, exist_ok=True)

    # Create static directory if not exists
    static_dir = os.path.join(os.path.dirname(__file__), '..', 'static')
    os.makedirs(static_dir, exist_ok=True)

    # Check if index.html exists, create default template
    index_template = os.path.join(templates_dir, 'index.html')
    if not os.path.exists(index_template):
        create_default_template(index_template)

    print(f"Starting CommitSentiment Trader Web App...")
    print(f"Default Repository: {DEFAULT_REPO}")
    print(f"Default Stock Symbol: {DEFAULT_SYMBOL}")
    print(f"Open http://localhost:5000 in your browser")

    app.run(debug=True, host='0.0.0.0', port=5000)


def create_default_template(filepath: str):
    """Create default HTML template for the dashboard."""
    template_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CommitSentiment Trader</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            color: #eee;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        header {
            text-align: center;
            padding: 40px 20px;
        }
        h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            background: linear-gradient(45deg, #4ecca3, #39a2dd);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .quote {
            font-style: italic;
            opacity: 0.8;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }
        .stat-card {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            backdrop-filter: blur(10px);
        }
        .stat-card h3 {
            font-size: 0.9em;
            color: #aaa;
            margin-bottom: 10px;
            text-transform: uppercase;
        }
        .stat-card .value {
            font-size: 1.8em;
            font-weight: bold;
        }
        .stat-card .value.positive { color: #4ecca3; }
        .stat-card .value.negative { color: #e94560; }
        .chart-container {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            padding: 20px;
            margin: 30px 0;
            backdrop-filter: blur(10px);
        }
        .chart-title {
            font-size: 1.2em;
            margin-bottom: 15px;
            color: #aaa;
        }
        canvas {
            max-height: 300px;
        }
        .signal-card {
            background: linear-gradient(45deg, #4ecca3, #39a2dd);
            border-radius: 12px;
            padding: 20px;
            margin: 30px 0;
            text-align: center;
            backdrop-filter: blur(10px);
        }
        .signal-card h3 {
            font-size: 1em;
            color: rgba(255, 255, 255, 0.9);
            margin-bottom: 10px;
        }
        .signal-card .signal-value {
            font-size: 2.5em;
            font-weight: bold;
            color: white;
        }
        .signal-card .signal-reason {
            margin-top: 10px;
            opacity: 0.9;
        }
        .btn {
            background: #4ecca3;
            color: #1a1a2e;
            border: none;
            padding: 12px 30px;
            border-radius: 8px;
            font-size: 1em;
            cursor: pointer;
            transition: transform 0.2s;
        }
        .btn:hover {
            transform: translateY(-2px);
        }
        .btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        .loading {
            text-align: center;
            padding: 40px;
        }
        .spinner {
            border: 3px solid rgba(255, 255, 255, 0.1);
            border-radius: 50%;
            border-top: 3px solid #4ecca3;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .error {
            color: #e94560;
            text-align: center;
            padding: 20px;
            background: rgba(233, 69, 96, 0.1);
            border-radius: 8px;
            margin: 20px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>CommitSentiment Trader</h1>
            <p class="quote">Mapping GitHub commit sentiment to trading signals</p>
        </header>

        <div class="stats-grid">
            <div class="stat-card">
                <h3>Repository</h3>
                <div class="value" id="repo-display">{{ default_repo }}</div>
            </div>
            <div class="stat-card">
                <h3>Stock Symbol</h3>
                <div class="value" id="symbol-display">{{ default_symbol }}</div>
            </div>
            <div class="stat-card">
                <h3>Last Updated</h3>
                <div class="value" id="timestamp">-</div>
            </div>
        </div>

        <div class="signal-card">
            <h3>Latest Trading Signal</h3>
            <div class="signal-value" id="latest-signal">LOADING...</div>
            <div class="signal-reason" id="signal-reason">-</div>
        </div>

        <div class="chart-container">
            <div class="chart-title">Sentiment Time Series</div>
            <canvas id="sentimentChart"></canvas>
        </div>

        <div style="text-align: center;">
            <button class="btn" id="analyze-btn" onclick="runAnalysis()">Run Analysis</button>
            <p style="margin-top: 20px; opacity: 0.6;">Click to refresh data</p>
        </div>

        <div id="error-message" class="error" style="display: none;"></div>
    </div>

    <script>
        let sentimentChart = null;

        async function runAnalysis() {
            const btn = document.getElementById('analyze-btn');
            btn.disabled = true;
            btn.textContent = 'Analyzing...';

            try {
                const response = await fetch('/api/analyze');
                const data = await response.json();

                document.getElementById('timestamp').textContent = new Date().toLocaleTimeString();

                if (data.error) {
                    showError(data.error);
                    return;
                }

                // Update signal display
                if (data.latest_signal) {
                    const signal = data.latest_signal.signal;
                    const sentiment = parseFloat(data.latest_signal.sentiment_score).toFixed(3);
                    const reason = data.latest_signal.reason;

                    const signalEl = document.getElementById('latest-signal');
                    signalEl.textContent = signal;

                    if (signal === 'BUY') {
                        signalEl.className = 'signal-value positive';
                    } else if (signal === 'SELL') {
                        signalEl.className = 'signal-value negative';
                    } else {
                        signalEl.className = 'signal-value';
                    }

                    document.getElementById('signal-reason').textContent = reason;
                } else {
                    document.getElementById('latest-signal').textContent = 'NO SIGNALS';
                    document.getElementById('signal-reason').textContent = '-';;
                    document.getElementById('latest-signal').className = 'signal-value';
                }

                // Update chart
                updateChart(data.time_series);

                // Update stats
                if (data.sentiment_analysis) {
                    const avg = parseFloat(data.sentiment_analysis.avg_sentiment).toFixed(3);
                    document.querySelector('.stats-grid .stat-card:nth-child(3) .value').textContent = avg;
                }

            } catch (error) {
                showError('Error: ' + error.message);
            } finally {
                btn.disabled = false;
                btn.textContent = 'Run Analysis';
            }
        }

        function updateChart(timeSeries) {
            const timestamps = timeSeries.timestamps || [];
            const sentiments = timeSeries.sentiments || [];

            const ctx = document.getElementById('sentimentChart').getContext('2d');

            if (sentimentChart) {
                sentimentChart.destroy();
            }

            sentimentChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: timestamps.slice(-20),
                    datasets: [{
                        label: 'Sentiment Score',
                        data: sentiments.slice(-20),
                        borderColor: '#4ecca3',
                        backgroundColor: 'rgba(78, 204, 163, 0.1)',
                        borderWidth: 2,
                        fill: true,
                        tension: 0.4,
                        pointRadius: 2,
                        pointHoverRadius: 5
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: {
                        mode: 'index',
                        intersect: false,
                    },
                    plugins: {
                        legend: { display: false },
                        title: { display: false }
                    },
                    scales: {
                        y: {
                            grid: { color: 'rgba(255, 255, 255, 0.1)' },
                            ticks: { color: '#aaa' },
                            min: -1,
                            max: 1,
                            title: { display: true, text: 'Sentiment', color: '#aaa' }
                        },
                        x: {
                            grid: { display: false },
                            ticks: { color: '#aaa', maxTicksLimit: 6 }
                        }
                    }
                }
            });
        }

        function showError(message) {
            const errorEl = document.getElementById('error-message');
            errorEl.textContent = message;
            errorEl.style.display = 'block';
            setTimeout(() => {
                errorEl.style.display = 'none';
            }, 5000);
        }

        // Run analysis on page load
        document.addEventListener('DOMContentLoaded', runAnalysis);
    </script>
</body>
</html>
'''

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(template_content)
    print(f"Created default template at {filepath}")


# Create template on import
_templates_dir = os.path.join(os.path.dirname(__file__), '..', 'templates')
os.makedirs(_templates_dir, exist_ok=True)
_template_path = os.path.join(_templates_dir, 'index.html')
if not os.path.exists(_template_path):
    create_default_template(_template_path)

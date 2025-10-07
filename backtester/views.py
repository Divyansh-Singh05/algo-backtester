from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import pandas as pd
import json
import importlib
import os
import sys
import os.path
from django.http import JsonResponse
from django.views import View
from .backtest_engine import BacktestEngine
from strategies.predefined_strategies import (
    MACrossoverStrategy,
    RSIStrategy,
    MACDStrategy,
    BollingerBandsStrategy,
    StochasticStrategy,
    ADXStrategy,
    IchimokuStrategy,
    MeanReversionStrategy
)

# Create your views here.

class BacktestView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            symbol = data.get('symbol')
            strategy_name = data.get('strategy_name')
            parameters = data.get('parameters', {})
            start_date = data.get('start_date')
            end_date = data.get('end_date')
            initial_cash = data.get('initial_cash', 10000)  # Default to 10000 if not provided
            
            if strategy_name == 'MA_Crossover':
                strategy = MACrossoverStrategy(**parameters)
            elif strategy_name == 'RSI':
                strategy = RSIStrategy(**parameters)
            elif strategy_name == 'MACD':
                strategy = MACDStrategy(**parameters)
            elif strategy_name == 'Bollinger_Bands':
                strategy = BollingerBandsStrategy(**parameters)
            elif strategy_name == 'Stochastic':
                strategy = StochasticStrategy(**parameters)
            elif strategy_name == 'ADX':
                strategy = ADXStrategy(**parameters)
            elif strategy_name == 'Ichimoku':
                strategy = IchimokuStrategy(**parameters)
            elif strategy_name == 'Mean_Reversion':
                strategy = MeanReversionStrategy(**parameters)
            else:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Unknown strategy: {strategy_name}'
                })
            
            engine = BacktestEngine(strategy, initial_capital=initial_cash)
            results = engine.run(symbol, start_date, end_date)
            
            return JsonResponse({
                'status': 'success',
                'results': results
            })
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            })

class StrategiesView(View):
    def get(self, request):
        strategies = {
            'MA_Crossover': {
                'name': 'Moving Average Crossover',
                'parameters': {
                    'fast_period': {'type': 'number', 'default': 10, 'min': 2, 'max': 50},
                    'slow_period': {'type': 'number', 'default': 30, 'min': 5, 'max': 200}
                }
            },
            'RSI': {
                'name': 'Relative Strength Index',
                'parameters': {
                    'period': {'type': 'number', 'default': 14, 'min': 2, 'max': 50},
                    'overbought': {'type': 'number', 'default': 70, 'min': 50, 'max': 90},
                    'oversold': {'type': 'number', 'default': 30, 'min': 10, 'max': 50}
                }
            },
            'MACD': {
                'name': 'MACD',
                'parameters': {
                    'fast_period': {'type': 'number', 'default': 12, 'min': 2, 'max': 50},
                    'slow_period': {'type': 'number', 'default': 26, 'min': 5, 'max': 100},
                    'signal_period': {'type': 'number', 'default': 9, 'min': 2, 'max': 50}
                }
            },
            'Bollinger_Bands': {
                'name': 'Bollinger Bands',
                'parameters': {
                    'period': {'type': 'number', 'default': 20, 'min': 5, 'max': 50},
                    'std_dev': {'type': 'number', 'default': 2, 'min': 1, 'max': 4}
                }
            },
            'Stochastic': {
                'name': 'Stochastic Oscillator',
                'parameters': {
                    'k_period': {'type': 'number', 'default': 14, 'min': 2, 'max': 50},
                    'd_period': {'type': 'number', 'default': 3, 'min': 2, 'max': 20},
                    'overbought': {'type': 'number', 'default': 80, 'min': 50, 'max': 90},
                    'oversold': {'type': 'number', 'default': 20, 'min': 10, 'max': 50}
                }
            },
            'ADX': {
                'name': 'Average Directional Index',
                'parameters': {
                    'period': {'type': 'number', 'default': 14, 'min': 2, 'max': 50},
                    'adx_threshold': {'type': 'number', 'default': 25, 'min': 15, 'max': 50}
                }
            },
            'Ichimoku': {
                'name': 'Ichimoku Cloud',
                'parameters': {
                    'conversion_period': {'type': 'number', 'default': 9, 'min': 5, 'max': 30},
                    'base_period': {'type': 'number', 'default': 26, 'min': 15, 'max': 100},
                    'span_period': {'type': 'number', 'default': 52, 'min': 30, 'max': 200}
                }
            },
            'Mean_Reversion': {
                'name': 'Mean Reversion',
                'parameters': {
                    'period': {'type': 'number', 'default': 20, 'min': 5, 'max': 100},
                    'std_dev': {'type': 'number', 'default': 2, 'min': 1, 'max': 4}
                }
            }
        }
        return JsonResponse({
            'status': 'success',
            'strategies': list(strategies.keys())
        })

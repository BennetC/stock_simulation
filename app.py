from flask import render_template, jsonify, Flask
from flask_socketio import emit

from simulation.simulation_config import SimulationConfig
from socketio_config import socketio
from simulation.market_simulation import MarketSimulation

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
socketio.init_app(app)

# Pass the initialized socketio object into the MarketSimulation constructor
simulation = MarketSimulation(SimulationConfig(), socketio=socketio)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/traders')
def traders_page():
    return render_template('traders.html')

@app.route('/api/market_data')
def get_market_data():
    return jsonify(simulation.get_market_data())

@app.route('/api/start', methods=['POST'])
def start_simulation():
    simulation.start()
    return jsonify({'status': 'started'})

@app.route('/api/stop', methods=['POST'])
def stop_simulation():
    simulation.stop()
    return jsonify({'status': 'stopped'})

@app.route('/api/reset', methods=['POST'])
def reset_simulation():
    simulation.reset()
    return jsonify({'status': 'reset'})

@app.route('/api/traders')
def get_traders_data():
    return jsonify(simulation.get_all_traders_data())

@socketio.on('connect')
def on_connect():
    print('Client connected')
    emit('market_update', simulation.get_market_data())
    emit('traders_update', simulation.get_all_traders_data())

@socketio.on('disconnect')
def on_disconnect():
    print('Client disconnected')

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
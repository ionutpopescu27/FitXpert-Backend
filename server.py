from flask import Flask, jsonify, request
import subprocess
import logging
from flask_cors import CORS


app = Flask(__name__)
CORS(app)

running_process = None  

@app.route('/run', methods=['POST'])
def run_script():
    try:
        global running_process
        # Run your Python script when a POST request is made
        #result = subprocess.run(['python', 'C:\\REPOS\\BackLic\\test.py'], capture_output=True, text=True)
        running_process = subprocess.Popen(
            ['python', 'C:\\REPOS\\BackLic\\test.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return jsonify({"message":"Script started"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

@app.route('/stop', methods=['POST'])
def stop_script():
    global running_process
    try:
        if running_process and running_process.poll() is None:
            running_process.terminate()  # Terminate the process
            running_process.wait()  # Wait for process to terminate
            running_process = None  # Reset global variable
            return jsonify({"message": "Script stopped"}), 200
        else:
            return jsonify({"message": "No script running"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500    

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
from flask import Flask, jsonify, request
import subprocess
import re

app = Flask(__name__)


def remove_ansi_escape_sequences(text):
    """
    Removes ANSI escape sequences from the given text using regex.
    """
    # ANSI escape sequences pattern^
    ansi_escape = re.compile(r'''
        \x1B  # ESC
        (?:   # 7-bit C1 Fe (except CSI)
            [@-Z\\-_]
        |     # or [ for CSI, followed by control codes
            \[
            [0-?]*  # Parameter bytes
            [ -/]*  # Intermediate bytes
            [@-~]   # Final byte
        )
    ''', re.VERBOSE)
    return ansi_escape.sub('', text)


def parse_log_line(line):
    """
    Parses a log line into structured components.
    Adjust the regex based on your actual log format.
    """
    log_pattern = re.compile(r'^(?P<level>\w+)\s+(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s+(?P<message>.*)$')
    match = log_pattern.match(line)
    if match:
        return match.groupdict()
    else:
        return {"raw": line}


@app.route('/logs', methods=['GET'])
def get_logs():
    try:
        # pod_name = request.args.get('pod', 'midgard-0')  # Default pod name
        # tail_lines = request.args.get('tail', '200')  # Default tail value

        pod_name, tail_lines = 'midgard-0', '200'  # Hardcoded values

        # Validate 'tail_lines' to ensure it's a positive integer
        if not tail_lines.isdigit() or int(tail_lines) <= 0:
            return jsonify({'error': 'Invalid tail value. It must be a positive integer.'}), 400

        # Construct the kubectl command
        command = ['kubectl', 'logs', pod_name, f'--tail={tail_lines}']

        # Execute the command
        result = subprocess.run(command, capture_output=True, text=True, check=True)

        # Remove ANSI escape sequences
        clean_logs = remove_ansi_escape_sequences(result.stdout)

        # Split logs into individual lines and filter out empty lines
        raw_log_lines = [line for line in clean_logs.split('\n') if line.strip()]

        # Parse each log line into structured data
        parsed_logs = [parse_log_line(line) for line in raw_log_lines]

        # Return the logs as a list of objects
        return jsonify({'logs': parsed_logs})
    except subprocess.CalledProcessError as e:
        return jsonify({'error': f'Command failed: {e.stderr.strip()}'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

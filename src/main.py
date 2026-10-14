from flask import Flask
from prometheus_client import generate_latest

from utils.logging import set_logging_configuration, is_ready_gauge, last_updated_gauge
from utils.config import DEBUG, PORT, POD_NAME
from api_endpoints import api


set_logging_configuration()


def create_app():
    app = Flask(__name__)
    app.add_url_rule('/metrics', 'metrics', view_func=generate_latest)

    app.register_blueprint(api)

    @app.before_request
    def set_ready():
        is_ready_gauge.labels(job_name=POD_NAME, error_type=None).set(1)
        last_updated_gauge.set_to_current_time()

    return app


app = create_app()


if __name__ == '__main__':  # pragma: no cover
    app.run(debug=DEBUG, host='0.0.0.0', port=PORT)

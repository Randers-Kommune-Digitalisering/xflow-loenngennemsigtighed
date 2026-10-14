"""
Main entry point for the Flask application.
"""
from flask import Flask, Response, jsonify, request
from utils.config import get_config_class_path
from utils.logging import error_counter, set_logging_configuration


def create_app(config_object: str = "utils.config.DevConfig") -> Flask:
    """
    Create and configure the Flask application.

    :param config_object: The configuration object to use.
    :return: The Flask application instance.
    """
    app = Flask(__name__)
    app.config.from_object(config_object)

    debug = bool(app.config.get("DEBUG", False))
    set_logging_configuration(debug=debug)

    from api_endpoints import api
    app.register_blueprint(api)

    @app.after_request
    def count_server_errors(response: Response) -> Response:
        """
        Count server-side (5xx) HTTP responses using Prometheus metrics.

        :param response: The outgoing Flask response object.
        :return: The unmodified response.
        """
        if 500 <= response.status_code <= 599:
            error_counter.labels(
                endpoint=request.path,
                status=str(response.status_code),
            ).inc()

        return response

    @app.get("/healthz")
    def healthz() -> tuple[dict, int]:
        """
        Health check endpoint.

        :return: A JSON response indicating the health status.
        """
        return jsonify({"status": "ok"}), 200

    return app


# WSGI entrypoint for `gunicorn --chdir src main:app`
app = create_app(config_object=get_config_class_path())


if __name__ == "__main__":  # pragma: no cover
    app.run(debug=app.config["DEBUG"], host="0.0.0.0", port=int(app.config.get("PORT")))

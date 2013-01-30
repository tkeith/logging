from flask import Flask
from flask.helpers import jsonify
from werkzeug.exceptions import abort

def log_for_response(log):
    return {'time': str(log.time),
            'uuid': str(log.uuid),
            'tags': [tag.name for tag in log.tags],
            'values': dict([(value.param.name, value.name) for value in log.values])}

def logs_for_response(logs):
    return [log_for_response(log) for log in logs]

def make_api(logger):
    app = Flask(__name__)

    @app.teardown_request
    def remove_session(exception):
        logger.db_session.remove()

    @app.route("/tags/<tag_name>/logs/")
    def get_tag_logs(tag_name):
        logs = logger.Tag.get(tag_name).logs
        return jsonify(logs=logs_for_response(logs))

    @app.route("/params/<param_name>/values/<value_name>/logs/")
    def get_value_logs(param_name, value_name):
        return jsonify(logs=logs_for_response(logger.Value.get(logger.Param.get(param_name), value_name).logs))

    @app.route("/logs/<uuid>/")
    def get_log(uuid):
        log = logger.db_session.query(logger.Log).filter(logger.Log.uuid == uuid).first()
        if not log:
            abort(404)
        return jsonify(log=log_for_response(log))

    return app

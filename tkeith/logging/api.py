from flask import Flask, request
from flask.helpers import jsonify
from werkzeug.exceptions import abort
import json
from flask.blueprints import Blueprint

def log_for_response(log):
    return {'time': str(log.time),
            'uuid': str(log.uuid),
            'tags': [tag.name for tag in log.tags],
            'values': dict([(value.param.name, value.name) for value in log.values])}

def logs_for_response(logs):
    return [log_for_response(log) for log in logs]

def make_blueprint(logger):
    blueprint = Blueprint('logger', __name__)

    @blueprint.teardown_request
    def remove_session(exception):
        logger.db_session.remove()

    @blueprint.route("/logs/<uuid>/")
    def get_log(uuid):
        log = logger.db_session.query(logger.Log).filter(logger.Log.uuid == uuid).first()
        if not log:
            abort(404)
        return jsonify(log=log_for_response(log))

    @blueprint.route("/logs/<uuid>/children/")
    def get_log_children(uuid):
        offset = int(request.args['offset'])
        limit = int(request.args['limit'])
        log = logger.db_session.query(logger.Log).filter(logger.Log.uuid == uuid).first()
        if not log:
            abort(404)
        query = logger.db_session.query(logger.Log).filter(logger.Log.parent == log)
        count = query.count()
        query = query.order_by(logger.Log.time.desc()).offset(offset).limit(limit)
        logs = query.all()
        return jsonify(logs=logs_for_response(logs), count=count)

    @blueprint.route("/logs/")
    def get_logs():
        if 'tags' in request.args:
            tags = json.loads(request.args['tags'])
        else:
            tags = []

        if 'params' in request.args:
            params = json.loads(request.args['params'])
        else:
            params = {}

        offset = int(request.args['offset'])
        limit = int(request.args['limit'])

        query = logger.db_session.query(logger.Log)

        for tag_name in tags:
            query = query.filter(logger.Log.tags.any(logger.Tag.name == tag_name))

        for param, value in params.items():
            query = query.join(logger.Log.values).filter(logger.Value.name == value).distinct().join(logger.Value.param).filter(logger.Param.name == param).distinct()

        count = query.count()

        query = query.order_by(logger.Log.time.desc()).offset(offset).limit(limit)

        logs = query.all()
        return jsonify(logs=logs_for_response(logs), count=count)

    return blueprint

def make_app(logger):
    app = Flask(__name__)
    app.register_blueprint(make_blueprint(logger))
    return app

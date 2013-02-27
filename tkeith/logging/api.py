from flask import Flask, request
from flask.helpers import jsonify
from werkzeug.exceptions import abort
import json
from flask.blueprints import Blueprint
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.sql.expression import and_
from functools import wraps
from uuid import uuid4

def log_for_response(log):
    return {'time': str(log.time),
            'id': str(log.id),
            'tags': [tag.name for tag in log.tags],
            'values': dict([(value.param.name, value.name) for value in log.values]),
            'num_children': len(log.children)}

def logs_for_response(logs):
    return [log_for_response(log) for log in logs]

def make_blueprint(logger):
    bp = Blueprint('logger', __name__)

    def check_auth(username, password):
        try:
            user = logger.db_session.query(logger.User)\
                .filter(and_(logger.User.username == username,
                             logger.User.password == password)).one()
        except NoResultFound:
            return False
        return True

    def authed(fn):
        @wraps(fn)
        def new(*args, **kwargs):
            if request.authorization is not None and check_auth(request.authorization.username, request.authorization.password):
                return fn(*args, **kwargs)
            abort(401)
        return new

    @bp.teardown_request
    def remove_db_session(exception):
        logger.db_session.remove()

    @bp.route('/users/')
    def get_users():
        if check_auth(request.args['username'], request.args['password']):
            return jsonify()
        abort(404)

    @bp.route("/logs/<id>/")
    @authed
    def get_log(id):
        log = logger.db_session.query(logger.Log).filter(logger.Log.id == uuid4(id)).first()
        if not log:
            abort(404)
        return jsonify(log=log_for_response(log))

    @bp.route("/logs/<id>/children/")
    @authed
    def get_log_children(id):
        log = logger.db_session.query(logger.Log).filter(logger.Log.id == uuid4(id)).first()
        if not log:
            abort(404)
        query = logger.db_session.query(logger.Log).filter(logger.Log.parent == log)
        count = query.count()
        query = query.order_by(logger.Log.time.desc())
        if 'offset' in request.args:
            query = query.offset(int(request.args['offset']))
        if 'limit' in request.args:
            query = query.limit(int(request.args['limit']))
        logs = query.all()
        return jsonify(logs=logs_for_response(logs), count=count)

    @bp.route("/logs/")
    @authed
    def get_logs():
        if 'tags' in request.args:
            tags = json.loads(request.args['tags'])
        else:
            tags = []

        if 'params' in request.args:
            params = json.loads(request.args['params'])
        else:
            params = {}

        query = logger.db_session.query(logger.Log)

        for tag_name in tags:
            query = query.filter(logger.Log.tags.any(logger.Tag.name == tag_name))

        for param, value in params.items():
            query = query.join(logger.Log.values).filter(logger.Value.name == value).distinct().join(logger.Value.param).filter(logger.Param.name == param).distinct()

        count = query.count()

        query = query.order_by(logger.Log.time.desc())

        if 'offset' in request.args:
            query = query.offset(int(request.args['offset']))
        if 'limit' in request.args:
            query = query.limit(int(request.args['limit']))

        logs = query.all()
        return jsonify(logs=logs_for_response(logs), count=count)

    return bp

def make_app(logger):
    app = Flask(__name__)
    app.register_blueprint(make_blueprint(logger))
    return app

import sqlalchemy as sa
from flask import request
from sqlalchemy.sql.expression import and_
from sqlalchemy.orm.exc import NoResultFound
from werkzeug.exceptions import abort

def add_to_logger(logger, api):

    class User(logger.DBBase):
        __tablename__ = 'logger_users'

        id = sa.Column(sa.Integer, primary_key=True)
        username = sa.Column(sa.String)
        password = sa.Column(sa.String)

        def __init__(self, username, password):
            self.username = username
            self.password = password

    logger.User = User

    if(api):
        @api.before_request
        def authenticate():
            if request.method == 'GET':
                params = request.args
            else:
                params = request.form
            username = params['username']
            password = params['password']
            try:
                user = logger.db_session.query(logger.User)\
                    .filter(and_(logger.User.username == username,
                                 logger.User.password == password)).one()
            except NoResultFound:
                abort(403)

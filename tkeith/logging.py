from uuid import uuid4
from datetime import datetime
from sqlalchemy import orm
import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base

class Logger(object):

    def create_tables(self):
        self.DBBase.metadata.create_all(self.db_engine)

    def __init__(self, db_engine):
        logger = self

        self.db_engine = db_engine
        DBBase = declarative_base()
        self.DBBase = DBBase
        db_session = orm.sessionmaker(bind=db_engine)()
        self.current_parent = None

        class Value(DBBase):
            __tablename__ = 'logger_values'

            id = sa.Column(sa.Integer, primary_key=True)
            param_id = sa.Column(sa.Integer, sa.ForeignKey('logger_params.id'))
            param = orm.relationship('Param', backref='values')
            name = sa.Column(sa.String)

            def __init__(self, param, name):
                self.param = param
                self.name = name
                db_session.add(self)
                db_session.commit()

            @classmethod
            def get(cls, param, name):
                value = db_session.query(cls).filter(sa.and_(cls.param == param, cls.name == name)).first()
                if value is not None:
                    return value
                else:
                    return cls(param, name)

            def __repr__(self):
                return '<Value: {}={}>'.format(self.param.name, self.name)

        self.Value = Value

        class Param(DBBase):
            __tablename__ = 'logger_params'

            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.String)

            def __init__(self, name):
                self.name = name
                db_session.add(self)
                db_session.commit()

            @classmethod
            def get(cls, name):
                param = db_session.query(cls).filter(cls.name == name).first()
                if param is not None:
                    return param
                else:
                    return cls(name)

            def value(self, name):
                return Value.get(self, name)

            def __repr__(self):
                return '<Param: {}>'.format(self.name)

        self.Param = Param

        class Tag(DBBase):
            __tablename__ = 'logger_tags'

            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.String)

            def __init__(self, name):
                self.name = name
                db_session.add(self)
                db_session.commit()

            @classmethod
            def get(cls, name):
                tag = db_session.query(cls).filter(cls.name == name).first()
                if tag is not None:
                    return tag
                else:
                    return cls(name)

            def __repr__(self):
                return '<Tag: {}>'.format(self.name)

        self.Tag = Tag

        class LogValue(DBBase):
            __tablename__ = 'logger_log_values'

            id = sa.Column(sa.Integer, primary_key=True)
            log_id = sa.Column(sa.Integer, sa.ForeignKey('logger_logs.id'))
            log = orm.relationship('Log', backref='log_values')
            value_id = sa.Column(sa.Integer, sa.ForeignKey('logger_values.id'))
            value = orm.relationship('Value', backref='log_values')

        self.LogValue = LogValue

        class LogTag(DBBase):
            __tablename__ = 'logger_log_tags'

            id = sa.Column(sa.Integer, primary_key=True)
            index = sa.Column(sa.Integer)
            log_id = sa.Column(sa.Integer, sa.ForeignKey('logger_logs.id'))
            log = orm.relationship('Log', backref='log_tags')
            tag_id = sa.Column(sa.Integer, sa.ForeignKey('logger_tags.id'))
            tag = orm.relationship('Tag', backref='log_tags')

        self.LogTag = LogTag

        class Log(DBBase):
            __tablename__ = 'logger_logs'

            id = sa.Column(sa.Integer, primary_key=True)
            uuid = sa.Column(sa.String)
            time = sa.Column(sa.DateTime)
            message = sa.Column(sa.String)
            parent_id = sa.Column(sa.Integer, sa.ForeignKey('logger_logs.id'))
            parent = orm.relationship('Log', remote_side=[id], backref='children')
            tags = orm.relationship('Tag', secondary=LogTag.__table__, order_by=LogTag.index, backref='logs')
            values = orm.relationship('Value', secondary=LogValue.__table__, backref='logs')

            def __init__(self, *args, **kwargs):
                self.uuid = str(uuid4())
                self.time = datetime.now()
                self.parent = logger.current_parent

                for tag in args:
                    self.tags.append(Tag.get(tag))

                for name, value in kwargs.items():
                    param = Param.get(name)
                    value = param.value(value)
                    self.values.append(value)

                db_session.add(self)
                db_session.commit()

            def __str__(self):
                child_lines = []
                for child in self.children:
                    child_lines += str(child).split('\n')
                return '\n  '.join([' '.join([tag.name for tag in self.tags] + ['{}={}'.format(value.param.name, value.name) for value in self.values])] + child_lines)

            def __enter__(self):
                logger.current_parent = self
                return self

            def __exit__(self, *args):
                logger.current_parent = logger.current_parent.parent

        self.Log = Log

class FakeLogger(object):

    def __init__(self):

        class Log(object):

            def __init__(self, *args, **kwargs):
                pass

            def __enter__(self):
                pass

            def __exit__(self, *args):
                pass

        self.Log = Log

fake_logger = FakeLogger()

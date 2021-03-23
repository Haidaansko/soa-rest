from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Stats(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    total_sessions = db.Column(db.Integer, default=0)
    total_victories = db.Column(db.Integer, default=0)
    total_defeats = db.Column(db.Integer, default=0)
    total_time = db.Column(db.Integer, default=0)

    ATTRS_PUBLIC = ('total_sessions', 'total_victories',
                    'total_defeats', 'total_time')

    def to_dict(self):
        result = dict(map(
            lambda attr: (attr, getattr(self, attr)),
            self.ATTRS_PUBLIC
        ))
        return result


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(), unique=True, nullable=False)
    password = db.Column(db.String(), nullable=False)
    email = db.Column(db.String())
    gender = db.Column(db.String())
    avatar = db.Column(db.String())
    stats_id = db.Column(db.Integer, db.ForeignKey(Stats.id))
    stats = db.relationship(Stats, backref='stats', uselist=False)

    ATTRS_PUBLIC = ('username', 'email', 'gender', 'avatar')
    __ATTRS_PRIVATE = ('password',)

    __ATTRS_ALL = ATTRS_PUBLIC + __ATTRS_PRIVATE

    def safe_update(self, data):
        if not self.stats:
            self.stats = Stats()
        for attr, value in data.items():
            if attr in (self.__ATTRS_ALL):
                setattr(self, attr, value)
        if 'stats' in data:
            for attr, value in data['stats'].items():
                if attr in Stats.ATTRS_PUBLIC:
                    setattr(self.stats, attr, value)

        db.session.add(self)
        db.session.commit()

    def to_dict(self):
        result = dict(map(
            lambda attr: (attr, getattr(self, attr)),
            self.ATTRS_PUBLIC
        ))
        result['user_id'] = self.id
        result['username'] = self.username
        result['self_url'] = f'/users/{self.id}'
        result['stats_url'] = result['self_url'] + '/stats'
        return result

    def delete(self):
        Stats.query.filter_by(id=self.stats.id).delete()
        db.session.delete(self)
        db.session.commit()

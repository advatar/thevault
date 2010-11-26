from myvault.database import db

class ArchiveMixin(object):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    filename = db.Column(db.String(32))
    backup_time = db.Column(db.DateTime)

class ProgressMixin(object):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    progress = db.Column(db.Integer)
    started_at = db.Column(db.DateTime)
    ended_at = db.Column(db.DateTime)

class Archive(db.Model):
    __tablename__ = "archives"
    
    id = db.Column(db.Integer, primary_key=True)
    module = db.Column(db.String(50))
    filename = db.Column(db.String(50))
    archived_at = db.Column(db.DateTime)

class UserPreference(db.Model):
    __tablename__ = "user_preferences"

    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.Text())


class Settings(db.Model):
    __tablename__ = "settings"

    id = db.Column(db.Integer, primary_key=True)
    module = db.Column(db.String(50))
    data = db.Column(db.Text())

class BackupProgress(db.Model):
    __tablename__ = "backup_progress"

    id = db.Column(db.Integer, primary_key=True)
    module = db.Column(db.String(50))
    progress = db.Column(db.Integer)
    started_at = db.Column(db.DateTime)
    ended_at = db.Column(db.DateTime)

# vim: set sts=4 ts=4 sw=4:

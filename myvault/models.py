from myvault.database import db

class ModuleSchema(db.Model):
    __tablename__ = "module_schema"
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))

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

class Token(db.Model):
    __tablename__ = "tokens"

    id = db.Column(db.Integer, primary_key=True)
    service = db.Column(db.String(50))
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



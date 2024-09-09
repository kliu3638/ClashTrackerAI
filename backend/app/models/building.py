from app import db

class Building(db.Model):
    __tablename__ = 'Building'
    building_id = db.Column(db.Integer, primary_key=True)
    building_name = db.Column(db.String(40), unique=True, nullable=False)
    building_accounts = db.relationship('BuildingAccount', backref='account', lazy=True)
    building_accounts = db.relationship('BuildingMax', backref='max', lazy=True)
    building_accounts = db.relationship('BuildingUpgrade', backref='upgrade', lazy=True)

class BuildingMax(db.Model):
    __tablename__ = 'BuildingMax'
    building_id = db.Column(db.Integer, db.ForeignKey('Building.building_id'), primary_key=True) # Foreign key
    townhall = db.Column(db.Integer, primary_key=True)
    max_level = db.Column(db.Integer, nullable=False)
    max_num = db.Column(db.Integer, nullable=False)

class BuildingUpgrade(db.Model):
    __tablename__ = 'BuildingUpgrade'
    building_id = db.Column(db.Integer, db.ForeignKey('Building.building_id'), primary_key=True) # Foreign key
    building_level = db.Column(db.Integer, primary_key=True)
    cost = db.Column(db.String(15))
    time = db.Column(db.Integer)

class BuildingAccount(db.Model):
    __tablename__ = 'BuildingAccount'
    game_id = db.Column(db.String(20), db.ForeignKey('Building.building_id'), primary_key=True) # Foreign key
    building_id = db.Column(db.Integer, db.ForeignKey('GameAccount.game_id'), primary_key=True) # Foreign key
    table_id = db.Column(db.Integer, primary_key=True)
    level = db.Column(db.Integer, nullable=False)
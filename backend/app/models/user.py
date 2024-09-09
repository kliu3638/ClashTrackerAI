from app import db

class User(db.Model):
    __tablename__ = 'User'
    user_id = db.Column(db.Integer, primary_key=True)
    user_username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    game_accounts = db.relationship('GameAccount', backref='user', lazy=True)

    def __repr__(self):
        return f'<User "{self.user_username}">'

class GameAccount(db.Model):
    __tablename__ = 'GameAccount'
    game_id = db.Column(db.String(20), primary_key=True)
    game_username = db.Column(db.String(30), nullable=False)
    experience = db.Column(db.Integer)
    townhall = db.Column(db.Integer)
    overall = db.Column(db.Integer)
    building_progress = db.Column(db.Integer)
    lab_progress = db.Column(db.Integer)
    hero_progress = db.Column(db.Integer)
    wall_progress = db.Column(db.Integer)
    pet_progress = db.Column(db.Integer)
    user_id = db.Column(db.Integer, db.ForeignKey('User.user_id'), nullable=False) # Foreign key
    building_accounts = db.relationship('BuildingAccount', backref='account', lazy=True)

    def __repr__(self):
        return f'<# "{self.game_id}">'
from datetime import datetime

from flask_sqlalchemy import SQLAlchemy

database = SQLAlchemy()


class Ballot(database.Model):
    __tablename__ = "ballot"

    id = database.Column(database.Integer, primary_key=True)
    participantId = database.Column(database.Integer, database.ForeignKey("participant.id"), nullable=False)
    electionId = database.Column(database.Integer, database.ForeignKey("election.id"), nullable=False)
    ballotNum = database.Column(database.Integer, nullable=False)


class Participant(database.Model):
    __tablename__ = "participant"

    id = database.Column(database.Integer, primary_key=True)
    name = database.Column(database.String(256), nullable=False)
    individual = database.Column(database.Boolean, nullable=False)

    elections = database.relationship("Election", secondary=Ballot.__tablename__, back_populates="participants")

    def __repr__(self):
        data = {
            "id": self.id,
            "name": self.name,
            "individual": self.individual
        }
        return str(data)

    def toJSON(self):
        data = {
            "id": self.id,
            "name": self.name,
            "individual": self.individual
        }
        return data

    def forElectionJSON(self):
        data = {
            "id": self.id,
            "name": self.name
        }
        return data


class Election(database.Model):
    __tablename__ = "election"

    id = database.Column(database.Integer, primary_key=True)
    start = database.Column(database.DateTime, nullable=False)
    end = database.Column(database.DateTime, nullable=False)
    individual = database.Column(database.Boolean, nullable=False)

    participants = database.relationship("Participant", secondary=Ballot.__tablename__, back_populates="elections")

    votes = database.relationship("Vote")

    def __repr__(self):
        return "({}, {}, {}, {}, {})".format(self.id, self.start, self.end, self.individual, str(self.participants))

    def toJSON(self):
        allPart = []
        for part in self.participants:
            allPart.append(Participant.forElectionJSON(part))

        data = {
            "id": self.id,
            "start": datetime.isoformat(self.start),
            "end": datetime.isoformat(self.end),
            "individual": self.individual,
            "participants": allPart
        }

        return data


class Vote(database.Model):
    __tablename__ = "vote"

    id = database.Column(database.Integer, primary_key=True)
    electionId = database.Column(database.Integer, database.ForeignKey("election.id"), nullable=False)
    guid = database.Column(database.String(256), nullable=False)
    ballotNum = database.Column(database.Integer, nullable=False)
    functioner = database.Column(database.String(13))
    valid = database.Column(database.Boolean, nullable=False)
    reason = database.Column(database.String(256), nullable=True)

    def __repr__(self):
        return "({}, {})".format(self.guid, self.ballotNum)



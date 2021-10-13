import json
import re
from datetime import datetime, timedelta

from flask import Flask, Response
from redis import Redis
from sqlalchemy import or_, and_

from configuration import Configuration
from models import Vote, Election, database, Ballot

application = Flask(__name__)
application.config.from_object(Configuration)
database.init_app(application)
application.app_context().push()

def getVote(redis):
    bytes = redis.blpop(Configuration.REDIS_VOTES_LIST, timeout=0)

    raw_json = bytes[1]
    string_json = raw_json.decode('utf-8')
    vote = json.loads(string_json)
    return vote


def persistVote(vote):
    dt = datetime.now() + timedelta(seconds=2)
    election = Election.query.filter(and_(Election.start < dt, Election.end > dt)).first()

    if election:
        status1 = Ballot.query.filter(and_(Ballot.electionId == election.id,
                                           Ballot.ballotNum == vote["pollNumber"])).first()
        status2 = Vote.query.filter(and_(Vote.guid == vote['guid'], Vote.electionId == election.id)).first()

        reason = ""
        valid = True

        if not status1:
            reason = "Invalid poll number."
            valid = False

        elif status2:
            reason = "Duplicate ballot."
            valid = False

        vt = Vote(electionId=election.id, guid=vote["guid"], valid=valid, reason=reason, functioner=vote["jmbg"],
                  ballotNum=vote["pollNumber"])
        database.session.add(vt)
        database.session.commit()


def startDaemon():
    with Redis(Configuration.REDIS_HOST) as redis:
        while True:
            vote = getVote(redis)
            if len(vote) == 0:
                continue

            persistVote(vote)


if __name__ == '__main__':
    startDaemon()


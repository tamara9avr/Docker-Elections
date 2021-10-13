from datetime import datetime
from flask import Flask, request, jsonify, Response
from flask_jwt_extended import jwt_required, JWTManager
from sqlalchemy import or_, func, and_

from configuration import Configuration
from models import Participant, database, Vote, Election, Ballot
from adminDecorator import roleCheck

application = Flask(__name__)
application.config.from_object(Configuration)
jwt = JWTManager(application)


@application.route("/createParticipant", methods=["POST"])
@roleCheck(role="admin")
@jwt_required()
def createParticipant():
    name = request.json.get("name", "")
    individual = request.json.get("individual", "")

    nameEmpty = len(name) == 0 or len(name) > 256
    individualEmpty = not individual and individual != False

    if nameEmpty:
        message = "Field name is missing."
        return jsonify(message=message), 400

    if individualEmpty:
        message = "Field individual is missing."
        return jsonify(message=message), 400

    participant = Participant(name=name, individual=individual)

    database.session.add(participant)
    database.session.commit()

    return jsonify(id=participant.id), 200


@application.route("/getParticipants", methods=["GET"])
@jwt_required()
@roleCheck(role="admin")
def getParticipants():
    part = Participant.query.all()
    allPart = []
    for p in part:
        allPart.append(Participant.toJSON(p))
    return jsonify(participants=allPart), 200


@application.route("/createElection", methods=["POST"])
@jwt_required()
@roleCheck(role="admin")
def createElection():
    start = request.json.get("start", "")
    end = request.json.get("end", "")
    individual = request.json.get("individual", "")
    participantids = request.json.get("participants", "x")

    startEmpty = len(start) == 0
    endEmpty = len(end) == 0
    individualEmpty = not individual is True and individual != False
    participantsEmpty = participantids == "x"

    if startEmpty:
        message = "Field start is missing."
        return jsonify(message=message), 400

    if endEmpty:
        message = "Field end is missing."
        return jsonify(message=message), 400

    if individualEmpty:
        message = "Field individual is missing."
        return jsonify(message=message), 400

    if participantsEmpty:
        message = "Field participants is missing."
        return jsonify(message=message), 400

    dateEmpty = len(start) == 0 or len(end) == 0
    if dateEmpty:
        message = "Invalid date and time."
        return jsonify(message=message), 400

    try:
        startDate = datetime.strptime(start, "%Y-%m-%dT%H:%M:%S%z")
    except ValueError:
        try:
            startDate = datetime.strptime(start, "%Y-%m-%dT%H:%M:%S")
        except ValueError:
            message = "Invalid date and time."
            return jsonify(message=message), 400

    try:
        endDate = datetime.strptime(end, "%Y-%m-%dT%H:%M:%S%z")
    except ValueError:
        try:
            endDate = datetime.strptime(end, "%Y-%m-%dT%H:%M:%S")
        except ValueError:
            message = "Invalid date and time."
            return jsonify(message=message), 400

    busy = Election.query.filter(or_((and_(Election.start <= startDate, Election.end >= startDate)),
                                     and_(Election.start <= endDate, Election.end >= endDate),
                                     and_(Election.start <= startDate, Election.end >= endDate),
                                     and_(Election.start >= startDate, Election.end <= endDate))).first()

    if busy or startDate > endDate:
        message = "Invalid date and time."
        return jsonify(message=message), 400

    if len(participantids) < 2:
        message = "Invalid participants."
        return jsonify(message=message), 400

    participants = []
    for p in participantids:
        part = Participant.query.filter(and_(Participant.id == p, Participant.individual == individual)).first()
        if not part:
            message = "Invalid participants."
            return jsonify(message=message), 400

        participants.append(part)

    election = Election(start=startDate, end=endDate, individual=individual)
    database.session.add(election)
    database.session.commit()

    i = 1
    pollNumbers = []

    for p in participants:
        ballot = Ballot(electionId=election.id, participantId=p.id, ballotNum=i)
        pollNumbers.append(i)
        i = i + 1
        database.session.add(ballot)

    database.session.commit()

    return jsonify(pollNumbers=pollNumbers), 200


@application.route("/getElections", methods=["GET"])
@jwt_required()
@roleCheck(role="admin")
def getElections():
    el = Election.query.all()
    allEl = []
    for e in el:
        allEl.append(Election.toJSON(e))
    return jsonify(elections=allEl), 200


@application.route("/getResults")
@jwt_required()
@roleCheck(role="admin")
def getResults():
    if not "id" in request.args.keys():
        message = "Field id is missing."
        return jsonify(message=message), 400

    id = request.args.get('id', type=int)
    if id is None:
        message = "Field id is missing."
        return jsonify(message=message), 400

    election = Election.query.filter(Election.id == id).first()
    if not election:
        message = "Election does not exist."
        return jsonify(message=message), 400

    now = datetime.now()
    if election.start <= now <= election.end:
        message = "Election is ongoing."
        return jsonify(message=message), 400

    count = func.count(Vote.ballotNum)

    results = []
    participants = []
    mandates = []
    ballots = Ballot.query.filter(Ballot.electionId == id).all()

    allVotes = len(Vote.query.filter(and_(Vote.electionId == id, Vote.valid)).all())
    if allVotes != 0:

        for b in ballots:
            part = Participant.query.filter(Participant.id == b.participantId).first()
            res = 0
            all = Vote.query.filter(and_(Vote.valid, Vote.electionId == id, Vote.ballotNum == b.ballotNum)).group_by(
                Vote.ballotNum).with_entities(Vote.ballotNum, count).all()
            if len(all) > 0:
                res = all[0][1]
            participants.append([part, res])

        if election.individual:
            if allVotes == 0:
                allVotes = 1
            for p in participants:
                mandates.append({
                    "pollNumber": participants.index(p) + 1,
                    "name": p[0].name,
                    "result": round(p[1] / allVotes, 2)
                })
        else:
            total = Vote.query.filter(and_(Vote.electionId == election.id, Vote.valid)).count()
            MANDATE_SPOTS = 250
            result = {}
            for participant in election.participants:
                partElect = Ballot.query.filter(and_(Ballot.electionId == election.id,
                                                        Ballot.participantId == participant.id)).first()
                result[participant.id] = Vote.query.filter(and_(Vote.election == election.id, Vote.valid,
                                                                    Vote.participant == partElect.ballotNum)).count()

            total_cenzus = 0
            for key, value in result.copy().items():
                if value / allVotes >= 0.05:
                    total_cenzus += value
                else:
                    result.pop(key, None)

            for key, value in result.copy().items():
                result[key] = round(value / total_cenzus * MANDATE_SPOTS)

                mandates.append({
                    "pollNumber": key + 1,
                    "name": election.participants[key].name,
                    "result": results[key]
                })

    inv = Vote.query.filter(and_(not Vote.valid, Vote.electionId == id)).all()
    invalid = []
    for i in inv:
        invalid.append({
            "electionOfficialJmbg": i.functioner,
            "ballotGuid": i.guid,
            "pollNumber": i.ballotNum,
            "reason": i.reason
        })

    data = {
        "participants": mandates,
        "invalidVotes": invalid
    }

    return data, 200


if __name__ == "__main__":
    database.init_app(application)
    application.run(debug=True, host="0.0.0.0", port=5002)

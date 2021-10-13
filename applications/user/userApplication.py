import csv
import io
import json

from flask import Flask, request, Response, jsonify
from flask_jwt_extended import jwt_required, JWTManager, get_jwt
from configuration import Configuration
from models import database
from adminDecorator import roleCheck
from redis import Redis

application = Flask(__name__)
application.config.from_object(Configuration)

jwt = JWTManager(application)


@application.route("/vote", methods=["POST"])
@jwt_required()
@roleCheck(role="user")
def vote():
    info = get_jwt()
    func = info["jmbg"]

    file = request.files.get("file")
    if not file:
        message = "Field file is missing."
        return jsonify(message=message), 400

    content = file.stream.read().decode("utf-8")
    stream = io.StringIO(content)
    reader = csv.reader(stream)

    i = -1

    with Redis(host=Configuration.REDIS_HOST) as redis:
        for row in reader:

            i = i + 1
            if len(row) < 2:
                message = "Incorrect number of values on line " + str(i)+"."
                return jsonify(message=message), 400
            try:
                if int(row[1]) <= 0:
                    message = "Incorrect poll number on line " + str(i)+"."
                    return jsonify(message=message), 400
            except ValueError:
                message = "Incorrect poll number on line " + str(i)+"."
                return jsonify(message=message), 400

            voteReq = {
                "guid": row[0],
                "pollNumber": row[1],
                "jmbg": func
            }

            redis.rpush(Configuration.REDIS_VOTES_LIST, json.dumps(voteReq))

    return Response(status=200)


if __name__ == "__main__":
    database.init_app(application)
    application.run(debug=True, host="0.0.0.0", port=5002)

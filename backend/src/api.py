import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

"""
@TODO uncomment the following line to initialize the database
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
!! Running this function will add one
"""
db_drop_and_create_all()

# ROUTES


@app.route("/drinks")
def get_drinks():
    try:
        drinks_query = Drink.query.all()
        drinks = [drink.long() for drink in drinks_query]
        return jsonify({"success": True, "drinks": drinks})
    except Exception:
        abort(500)


@app.route("/drinks-detail")
@requires_auth(permission="get:drinks-detail")
def get_drinks_detail(jwt):
    try:
        drinks_query = Drink.query.all()
        drinks = [drink.long() for drink in drinks_query]

        return jsonify({"success": True, "drinks": drinks})
    except Exception:
        abort(500)


@app.route("/drinks", methods=["POST"])
@requires_auth(permission="post:drinks")
def post_new_drink(jwt):
    # get details from the request
    body = request.get_json()

    drink_details = {
        "new_drink_title": body.get("title", None),
        "new_drink_recipe": json.dumps(body.get("recipe", None)),
    }

    # Ensure that all details of the new drink are given
    for detail in drink_details:
        if not drink_details[detail]:
            abort(400)

        else:
            drink = Drink(
                title=drink_details["new_drink_title"],
                recipe=drink_details["new_drink_recipe"],
            )

    # get all drinks

    try:
        drink.insert()
        return jsonify(
            {"success": True, "drinks": get_drinks().get_json()["drinks"]}
        )
    except Exception:
        abort(500)


@app.route("/drinks/<int:drink_id>", methods=["PATCH"])
@requires_auth(permission="patch:drinks")
def update_drinks(jwt, drink_id):
    # get the drink to be updated
    drink = Drink.query.get(drink_id)

    # check if is such a drink_id exist
    if drink is None:
        abort(400)

    # body of request
    body = request.get_json()

    updated_title = body.get("title", None)

    updated_recipe = json.dumps(body.get("recipe", None))

    # update the drink conditionally
    if updated_title:
        drink.title = updated_title

    if updated_recipe:
        drink.recipe = updated_recipe if type(
            updated_recipe) == str else json.dumps(updated_recipe)

    try:
        # update drink
        drink.update()

        return jsonify(
            {"success": True, "drinks": get_drinks().get_json()["drinks"]}
        )
    except Exception:
        abort(500)


@app.route("/drinks/<int:drink_id>", methods=["DELETE"])
@requires_auth(permission="delete:drinks")
def delete_drink(jwt, drink_id):
    # get drink to be deleted
    drink = Drink.query.get(drink_id)

    try:
        # delete the drink
        drink.delete()
        return jsonify(
            {"success": True, "drinks": get_drinks().get_json()["drinks"]}
        )
    except Exception:
        abort(500)


# Error Handling
"""
Example error handling for unprocessable entity
"""


@app.errorhandler(400)
def bad_request(error):
    return (
        jsonify({"success": False, "error": 400, "message": " bad request"}),
        400,
    )


@app.errorhandler(404)
def not_found(error):
    return (
        jsonify(
            {"success": False, "error": 404, "message": "resource not found"}
        ),
        404,
    )


@app.errorhandler(422)
def unprocessable(error):
    return (
        jsonify({"success": False, "error": 422, "message": "unprocessable"}),
        422,
    )


@app.errorhandler(500)
def server_error(error):
    return (
        jsonify({"success": False, "error": 500, "message": "server error"}),
        500,
    )


# Error Handling


@app.errorhandler(AuthError)
def handle_auth_error(error):
    return (
        jsonify({"success": False, "error": error.status_code,
                "message": error.error["description"]}),
        error.status_code,
    )

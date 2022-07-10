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
# db_drop_and_create_all()

# ROUTES


@app.route("/drinks")
def get_drinks():
    try:
        drinks_query = Drink.query.all()
        drinks = [drink.short() for drink in drinks_query]
        return jsonify({"success": True, "drinks": drinks})
    except Exception as e:
        abort(e.code)


@app.route("/drinks-detail")
@requires_auth(permission="get:drinks-detail")
def get_drinks_detail(jwt):
    try:
        drinks_query = Drink.query.all()
        drinks = [drink.long() for drink in drinks_query]

        return jsonify({"success": True, "drinks": drinks})
    except Exception as e:
        abort(e.code)


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
    except Exception as e:
        abort(e.code)


@requires_auth(permission="patch:drinks")
@app.route("/drinks/<int:drink_id>", methods=["PATCH"])
def update_drinks(drink_id):
    # get the drink to be update
    drink = Drink.query.get(drink_id)

    # body of request
    body = request.get_json()

    updated_title = body.get("title", None)

    updated_recipe = json.dumps(body.get("recipe", None))

    # update the drink conditionally
    if updated_title:
        drink.title = updated_title

    if updated_recipe:
        drink.recipe = updated_recipe

    try:
        # update drink
        drink.update()

        return jsonify(
            {"success": True, "drinks": get_drinks().get_json()["drinks"]}
        )
    except Exception as e:
        abort(e.code)


@requires_auth(permission="delete:drinks")
@app.route("/drinks/<int:drink_id>", methods=["DELETE"])
def delete_drink(drink_id):
    # get drink to be deleted
    drink = Drink.query.get(drink_id)

    try:
        # delete the drink
        drink.delete()
        return jsonify(
            {"success": True, "drinks": get_drinks().get_json()["drinks"]}
        )
    except Exception as e:
        abort(e.code)


# Error Handling
"""
Example error handling for unprocessable entity
"""


@app.errorhandler(400)
def unauthorized(error):
    return (
        jsonify({"success": False, "error": 400, "message": " bad request"}),
        400,
    )


@app.errorhandler(404)
def unauthorized(error):
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


# Error Handling


@app.errorhandler(401)
def unauthorized(AuthError):
    return (
        jsonify({"success": False, "error": 401, "message": "unauthorized"}),
        401,
    )


@app.errorhandler(403)
def unauthorized(AuthError):
    return (
        jsonify({"success": False, "error": 403, "message": "forbidden"}),
        403,
    )

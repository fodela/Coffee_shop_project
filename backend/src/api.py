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

'''
@TODO uncomment the following line to initialize the database
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
!! Running this function will add one
'''
# db_drop_and_create_all()

# ROUTES
'''
@TODO implement endpoint
    GET /drinks
        it should be a public endpoint
        it should contain only the drink.short() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks')
def get_drinks():
    try:
        drinks_query = Drink.query.all()
        drinks = [drink.short() for drink in drinks_query]
        return jsonify({
            "success": True,
            "drinks": drinks
        })
    except Exception as e:
        abort(e.code)

'''
@TODO implement endpoint
    GET /drinks-detail
        it should require the 'get:drinks-detail' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''
@app.route("/drinks-detail")
@requires_auth(permission="get:drinks-detail")
def get_drinks_detail(jwt):
    try:
        drinks_query = Drink.query.all()
        drinks = [drink.long() for drink in drinks_query]

        return jsonify({
            "success": True,
            "drinks": drinks
        })
    except Exception as e:
        abort(e.code)


'''
@TODO implement endpoint
    POST /drinks
        it should create a new row in the drinks table
        it should require the 'post:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the newly created drink
        or appropriate status code indicating reason for failure
'''
@app.route("/drinks", methods=["POST"])
@requires_auth(permission="post:drinks")
def post_new_drink(jwt):
    # get details from the request
    body = request.get_json()

    drink_details = {
                "new_drink_title": body.get("title", None),
                "new_drink_recipe": json.dumps(body.get("recipe", None))      
            }

    # Ensure that all details of the new drink are given
    for detail in drink_details:
        if not drink_details[detail]:
            abort(400)
    
        else:
            drink = Drink(
                title= drink_details["new_drink_title"], 
                recipe= drink_details["new_drink_recipe"]
                )
    
    # get all drinks

    try:
        drink.insert()
        return jsonify({
            "success": True,
            "drinks": get_drinks().get_json()["drinks"]
        })
    except Exception as e:
        abort(e.code)

'''
@TODO implement endpoint
    PATCH /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should update the corresponding row for <id>
        it should require the 'patch:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the updated drink
        or appropriate status code indicating reason for failure
'''
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
        drink.update()

        return jsonify({
            "success": True,
            "drinks": get_drinks().get_json()["drinks"]
        })
    except Exception as e:
        abort(e.code)




'''
@TODO implement endpoint
    DELETE /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should delete the corresponding row for <id>
        it should require the 'delete:drinks' permission
    returns status code 200 and json {"success": True, "delete": id} where id is the id of the deleted record
        or appropriate status code indicating reason for failure
'''
@requires_auth(permission="delete:drinks")
@app.route("/drinks/<int:drink_id>", methods=["DELETE"])
def delete_drink(drink_id):
    # get drink to be deleted
    drink = Drink.query.get(drink_id)

    # delete the drink
    try:
        drink.delete()
        return jsonify({
                "success": True,
                "drinks": get_drinks().get_json()["drinks"]
            })
    except Exception as e:
        abort(e.code)

# Error Handling
'''
Example error handling for unprocessable entity
'''


@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": "unprocessable"
    }), 422


'''
@TODO implement error handlers using the @app.errorhandler(error) decorator
    each error handler should return (with approprate messages):
             jsonify({
                    "success": False,
                    "error": 404,
                    "message": "resource not found"
                    }), 404

'''

'''
@TODO implement error handler for 404
    error handler should conform to general task above
'''
@app.errorhandler(404)
def unauthorized(error):
    return jsonify({
        "success": False,
        "error": 404,
        "message": "resource not found"
    }),404

'''
@TODO implement error handler for AuthError
    error handler should conform to general task above
'''
@app.errorhandler(401)
def unauthorized(AuthError):
    return jsonify({
        "success": False,
        "error": 401,
        "message": "unauthorized"
    }),401

@app.errorhandler(403)
def unauthorized(error):
    return jsonify({
        "success": False,
        "error": 403,
        "message": "forbidden"
    }),403

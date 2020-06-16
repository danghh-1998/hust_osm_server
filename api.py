import json
from flask_restful import Resource, Api, reqparse

from db import Point, Way, Boundary
from pathfinding import find_from_location, find_path_between_objects
from app import app

api = Api(app)

current_location_parser = reqparse.RequestParser()
current_location_parser.add_argument('longitude', type=float, required=True)
current_location_parser.add_argument('latitude', type=float, required=True)
current_location_parser.add_argument('dest_id', type=int, required=True)

path_parser = reqparse.RequestParser()
path_parser.add_argument('source_id', type=int, required=True)
path_parser.add_argument('dest_id', type=int, required=True)


class Path(Resource):
    def post(self):
        arguments = path_parser.parse_args()
        source_id = arguments['source_id']
        dest_id = arguments['dest_id']
        path = find_path_between_objects(source_id=source_id, dest_id=dest_id)
        return json.dumps({
            'path': path
        })


class PathFromLocation(Resource):
    def post(self):
        arguments = current_location_parser.parse_args()
        longitude = arguments['longitude']
        latitude = arguments['latitude']
        dest_id = arguments['dest_id']
        path = find_from_location(longitude=longitude, latitude=latitude, dest_id=dest_id)
        return json.dumps({
            'path': path
        })


api.add_resource(Path, '/path')
api.add_resource(PathFromLocation, '/path_from_location')

if __name__ == '__main__':
    app.run(debug=True)

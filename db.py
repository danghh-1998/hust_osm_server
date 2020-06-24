import json
from lxml import etree
from geoalchemy2 import Geometry, functions
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy_utils import database_exists

from app import app

DB_USER = 'regulusleo'
DB_PASSWORD = '12345678'
DB_HOST = 'localhost'
DB_PORT = '5432'
DB_NAME = 'osm'
DB_URI = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

app.config['SQLALCHEMY_DATABASE_URI'] = DB_URI
db = SQLAlchemy(app=app)


def obj_from_geo(geo):
    return json.loads(db.session.query(functions.ST_AsGeoJSON(geo)).first()[0])['coordinates']


neighbor_point = db.Table(
    'neighbors',
    db.Column('point_id', db.BigInteger, db.ForeignKey('point.id_')),
    db.Column('neighbor_id', db.BigInteger, db.ForeignKey('point.id_'))
)

located_on = db.Table(
    'located_on',
    db.Column('point_id', db.BigInteger, db.ForeignKey('point.id_')),
    db.Column('way_id', db.BigInteger, db.ForeignKey('way.id_'))
)


class Point(db.Model):
    __tablename__ = 'point'
    id_ = db.Column(db.BigInteger, primary_key=True)
    type_ = db.Column(db.String)
    name = db.Column(db.String)
    geo = db.Column(Geometry('POINT'))
    neighbors = db.relationship('Point', secondary=neighbor_point, primaryjoin=id_ == neighbor_point.columns.point_id,
                                secondaryjoin=id_ == neighbor_point.columns.neighbor_id, lazy='dynamic')
    ways = db.relationship('Way', secondary=located_on, back_populates='points')

    @property
    def coordinates(self):
        result = obj_from_geo(geo=self.geo)
        return result

    @property
    def coordinates_string(self):
        return f"{self.longitude} {self.latitude}"

    @property
    def latitude(self):
        return self.coordinates[1]

    @property
    def longitude(self):
        return self.coordinates[0]

    @property
    def nearest_way(self):
        way_distances = [(way, self.get_distance_to_object(obj=way)) for way in db.session.query(Way).all()]
        way_distances.sort(key=lambda item: item[1])
        return way_distances[0][0]

    @property
    def start_point(self):
        way = self.nearest_way
        closest_point = Point(
            geo=db.session.query(functions.ST_ClosestPoint(self.geo, way.geo)).first()[0])
        point_distances = [(point, Point.get_distance_between_points(first_point=closest_point, second_point=point)) for
                           point in way.points]
        point_distances.sort(key=lambda item: item[1])
        return point_distances[0][0]

    @staticmethod
    def find_point(id_):
        point = db.session.query(Point).filter_by(id_=id_).one_or_none()
        return point

    @staticmethod
    def get_distance_between_points(first_point, second_point):
        return first_point.get_distance_to_object(obj=second_point)

    @staticmethod
    def create_points(node_elements, type_keys, name_keys):
        for element in node_elements:
            id_ = element.get('id')
            latitude = float(element.get('lat'))
            longitude = float(element.get('lon'))
            name = None
            type_ = None
            tags = element.getchildren()
            if tags:
                attribs = {}
                for tag in tags:
                    attribs[tag.attrib['k']] = tag.attrib['v']
                for key, value in attribs.items():
                    if key in type_keys:
                        type_ = value
                    if key in name_keys:
                        name = value
            point = Point(id_=id_, type_=type_, name=name, geo=f"POINT({longitude} {latitude})")
            db.session.add(point)
            db.session.commit()

    @staticmethod
    def create_point(longitude, latitude):
        return Point(geo=db.session.query(functions.ST_GeomFromText(f"POINT({longitude} {latitude})")).first()[0])

    def get_distance_to_object(self, obj):
        return db.session.query(functions.ST_Distance_Sphere(self.geo, obj.geo)).first()[0]

    def __str__(self):
        return str(self.id_)


class Way(db.Model):
    __tablename__ = 'way'
    id_ = db.Column(db.BigInteger, primary_key=True)
    name = db.Column(db.String)
    geo = db.Column(Geometry('LINESTRING'))
    points = db.relationship('Point', secondary=located_on, back_populates='ways')

    @property
    def center_point(self):
        return self.points[int(len(self.points) / 2)]

    @staticmethod
    def create_ways(way_elements):
        for element in way_elements:
            refs = element.findall('nd')
            tags = element.findall('tag')
            if refs and refs[0].get('ref') != refs[-1].get('ref'):
                attribs = {}
                for tag in tags:
                    attribs[tag.attrib['k']] = tag.attrib['v']
                id_ = element.get('id')
                name = None
                points = []
                for key, value in attribs.items():
                    if key == 'name':
                        name = value
                for ref in refs:
                    points.append(Point.find_point(id_=ref.get('ref')))
                for index, point in enumerate(points):
                    if index == 0:
                        point.neighbors.append(points[1])
                        db.session.commit()
                    elif index == len(points) - 1:
                        point.neighbors.append(points[index - 1])
                        db.session.commit()
                    else:
                        point.neighbors.append(points[index - 1])
                        point.neighbors.append(points[index + 1])
                        db.session.commit()
                way = Way(id_=id_, name=name,
                          geo=f"LINESTRING({','.join([point.coordinates_string for point in points])})")
                db.session.add(way)
                db.session.commit()
                for point in points:
                    way.points.append(point)
                    db.session.commit()

    @staticmethod
    def find_way(id_):
        way = db.session.query(Way).filter_by(id_=id_).one_or_none()
        return way

    def __str__(self):
        return self.name

    def __eq__(self, other):
        return self.id_ == other.id_


class Boundary(db.Model):
    __tablename__ = 'boundary'
    id_ = db.Column(db.BigInteger, primary_key=True)
    name = db.Column(db.String)
    geo = db.Column(Geometry('POLYGON'))

    @property
    def center_point(self):
        return Point(geo=db.session.query(functions.ST_Centroid(self.geo)).first()[0])

    @staticmethod
    def create_boundaries(way_elements):
        for element in way_elements:
            refs = element.findall('nd')
            tags = element.findall('tag')
            if refs and refs[0].get('ref') == refs[-1].get('ref'):
                attribs = {}
                for tag in tags:
                    attribs[tag.attrib['k']] = tag.attrib['v']
                id_ = element.get('id')
                name = None
                points = []
                for key, value in attribs.items():
                    if key == 'name':
                        name = value
                for ref in refs:
                    points.append(Point.find_point(id_=ref.get('ref')))
                boundary = Boundary(id_=id_, name=name,
                                    geo=f"POLYGON(({','.join([point.coordinates_string for point in points])}))")
                db.session.add(boundary)
                db.session.commit()

    @staticmethod
    def find_boundary(id_):
        boundary = db.session.query(Boundary).filter_by(id_=id_).one_or_none()
        return boundary

    def __str__(self):
        return self.name

    def __eq__(self, other):
        return self.id_ == other.id_


def osm2postgis():
    root = etree.parse('resources/map.osm').getroot()
    node_elements = root.findall('node')
    way_elements = root.findall('way')
    type_keys = ['amenity', 'shop', 'barrier', 'highway', 'place', 'office', 'building', 'cuisine']
    name_keys = ['addr:housenumber', 'name:vi', 'name:en', 'operator', 'name']
    db.create_all()
    Point.create_points(node_elements=node_elements, type_keys=type_keys, name_keys=name_keys)
    Way.create_ways(way_elements=way_elements)
    Boundary.create_boundaries(way_elements=way_elements)


if __name__ == '__main__':
    osm2postgis()

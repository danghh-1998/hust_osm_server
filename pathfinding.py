from math import sqrt

from db import Point, Way, Boundary


class State:
    def __init__(self, parent, point):
        self.parent = parent
        self.point = point
        self.g = 0
        self.h = 0
        self.f = 0

    def __eq__(self, other):
        return self.point.id_ == other.point.id_


def find_path(start_point, end_point):
    start_state = State(None, start_point)
    start_state.g = start_state.h = start_state.f = 0
    end_state = State(None, end_point)
    end_state.g = end_state.h = end_state.f = 0

    open_list = []
    closed_list = []
    open_list.append(start_state)

    while len(open_list) > 0:
        current_state = open_list[0]
        current_index = 0

        for index, item in enumerate(open_list):
            if item.f < current_state.f:
                current_state = item
                current_index = index

        open_list.pop(current_index)
        closed_list.append(current_state)

        if current_state == end_state:
            path = []
            current = current_state
            while current is not None:
                path.append(current.point.coordinates)
                current = current.parent
            return path[::-1]
        children_state = [State(parent=current_state, point=neighbor) for neighbor in current_state.point.neighbors]
        for state in children_state:
            flag = False
            for close_state in closed_list:
                if state == close_state:
                    flag = True
                    break
            if flag:
                continue
            state.g = current_state.g + current_state.point.get_distance_to_object(obj=state.point)
            state.h = state.point.get_distance_to_object(obj=end_state.point)
            state.f = state.g + state.h
            for open_state in open_list:
                if state == open_state and state.g > open_state.g:
                    flag = True
                    break
            if flag:
                continue
            open_list.append(state)


def find_graph_point(id_):
    obj = Boundary.find_boundary(id_=id_)
    if obj:
        obj = obj.center_point.start_point
    else:
        obj = Way.find_way(id_=id_)
        if obj:
            obj = obj.center_point
        else:
            obj = Point.find_point(id_=id_)
            if obj:
                obj = obj.start_point
            else:
                raise Exception
    return obj


def find_path_between_objects(source_id, dest_id):
    start_point = find_graph_point(id_=source_id)
    end_point = find_graph_point(id_=dest_id)
    path = find_path(start_point=start_point, end_point=end_point)
    if sqrt((start_point.longitude - path[1][0]) ** 2 + (start_point.latitude - path[1][1]) ** 2) > sqrt(
            (path[0][0] - path[1][0]) ** 2 + (path[0][1] - path[1][1]) ** 2):
        path.insert(0, [start_point.longitude, start_point.latitude])
    else:
        path[0] = [start_point.longitude, start_point.latitude]
    return find_path(start_point=start_point, end_point=end_point)


def find_from_location(longitude, latitude, dest_id):
    start_point = Point.create_point(longitude=longitude, latitude=latitude).start_point
    end_point = find_graph_point(id_=dest_id)
    path = find_path(start_point=start_point, end_point=end_point)
    path.insert(0, [longitude, latitude])
    return path


if __name__ == '__main__':
    # print(find_path_between_objects(158465678, 184021008))
    print(find_from_location(longitude=105.84303, latitude=21.00520, dest_id=158465678))

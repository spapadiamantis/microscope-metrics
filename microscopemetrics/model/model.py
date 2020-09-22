"""This module takes care of the data model used by microscopemetrics.
It creates a few classes representing input data and output data
"""
from abc import ABC
from typing import Union, List, Dict
from typeguard import check_type


class MetricsDataset:
    """This class represents a single dataset including the intensity data and the name.
    Instances of this class are used by the analysis routines to get the necessary data to perform the analysis"""

    def __init__(self, data: dict = None, metadata: dict = None):
        if data is not None:
            self.data = data
        else:
            self._data = data

        if metadata is not None:
            self.metadata = metadata
        else:
            self._metadata = {}

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, data):
        self._data = data

    def metadata_add_requirement(self, name: str, description: str, type, optional: bool):
        self._metadata[name] = {'description': description,
                                'type': type,
                                'optional': optional,
                                'value': None}

    def metadata_remove_requirement(self, name: str):
        try:
            del (self._metadata[name])
        except KeyError as e:
            raise KeyError(f'Metadata "{name}" does not exist') from e

    def metadata_describe_requirements(self):
        str_output = list()
        for name, req in self._metadata.items():
            str_output.append('----------')
            str_output.append('Name: ' + name)
            str_output.extend([f'{k.capitalize()}: {v}' for k, v in req.items()])
        str_output.append('----------')
        str_output = '\n'.join(str_output)
        return str_output

    def validate_requirements(self, strict=False):
        validated = list()
        reasons = list()
        for name, req in self._metadata.items():
            v, r = self._validate_requirement(name, req, strict)
            validated.append(v)
            reasons.append(r)
        return all(validated), reasons

    @staticmethod
    def _validate_requirement(name, requirement, strict):
        if requirement['optional'] and not strict:
            return True, f'{name} is optional'
        else:
            if requirement['value'] is None:
                return False, f'{name} has None value'
            else:
                try:
                    check_type(name, requirement['value'], requirement['type'])
                    return True, f'{name} is the correct type'
                except TypeError:
                    return False, f'{name} is not of the correct type ({requirement["type"]})'

    def get_metadata(self, name: Union[str, list] = None):
        if name is None:
            return self._metadata
        elif isinstance(name, str):
            try:
                return self._metadata[name]['value']
            except KeyError as e:
                raise KeyError(f'Metadatum "{name}" does not exist') from e
        elif isinstance(name, list):
            return {k: self.get_metadata(k) for k in name}
        else:
            raise TypeError('get_metadata requires a string or list of strings')

    def set_metadata(self, name: str, value):
        try:
            expected_type = self._metadata[name]['type']
        except KeyError as e:
            raise KeyError(f'Metadata "{name}" is not a valid requirement') from e
        check_type(name, value, expected_type)
        self._metadata[name]['value'] = value

    def del_metadata(self, name: str):
        try:
            self._metadata[name]['value'] = None
        except KeyError as e:
            raise KeyError(f'Metadata "{name}" does not exist') from e

    def list_metadata_names(self):
        return [k for k, _ in self._metadata]


class MetricsOutput:
    """This class is used by microscopemetrics to return the output of an analysis.
    """

    def __init__(self, description: str = None):
        self.description = description
        self._properties = {}

    def get_property(self, property_name: str):
        return self._properties[property_name]

    def delete_property(self, property_name: str):
        del (self._properties[property_name])

    def append_property(self, output_property):
        if isinstance(output_property, OutputProperty):
            self._properties.update({output_property.name: output_property})
        else:
            raise TypeError('Property appended must be a subtype of OutputProperty')

    def extend_properties(self, properties_list: list):
        for p in properties_list:
            self.append_property(p)

    def _get_properties_by_type(self, type_str):
        return [v for _, v in self._properties.items() if v.type == type_str]

    def get_images(self):
        return self._get_properties_by_type('Image')

    def get_rois(self):
        return self._get_properties_by_type('Roi')

    def get_tags(self):
        return self._get_properties_by_type('Tag')

    def get_key_values(self):
        return self._get_properties_by_type('KeyValues')

    def get_tables(self):
        return self._get_properties_by_type('Table')

    def get_comments(self):
        return self._get_properties_by_type('Comment')


class OutputProperty(ABC):
    def __init__(self, name: str, description: str = None):
        self.name = name
        self.description = description

    def describe(self):
        """
        Returns a pretty string describing the property. Includes name, type and description.
        :return: str
        """
        return f'Name: {self.name}\n' \
               f'Type: {self.type}\n' \
               f'Description: {self.description}'

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, property_name: str):
        if isinstance(property_name, str):
            self._name = property_name
        else:
            raise TypeError('output_property name must be a string')

    @property
    def description(self):
        return self._description

    @description.setter
    def description(self, description):
        if isinstance(description, str) or description is None:
            self._description = description
        else:
            raise TypeError('output_property description must be a string or None')

    @property
    def type(self):
        """
        Returns the type of the OutputProperty as a string.
        :return: str
        """
        return self.__class__.__name__


class Roi(OutputProperty):
    def __init__(self, shapes: list, **kwargs):
        super().__init__(**kwargs)
        self.shapes = shapes

    @property
    def shapes(self):
        return self._shapes

    @shapes.setter
    def shapes(self, shapes):
        if all(isinstance(s, Shape) for s in shapes) or \
                isinstance(shapes, Shape):
            self._shapes = shapes
        else:
            raise TypeError('Objects passed to create a roi must be of type Shape')


class Shape(ABC):
    def __init__(self,
                 z=None,
                 c=None,
                 t=None,
                 fill_color: tuple = (10, 10, 10, 10),
                 stroke_color: tuple = (255, 255, 255, 255),
                 stroke_width: int = 1
                 ):
        self.z = z
        self.c = c
        self.t = t
        self.fill_color = fill_color
        self.stroke_color = stroke_color
        self.stroke_width = stroke_width

    def _test_numeric(self, value):
        if isinstance(value, (int, float)):
            return value
        else:
            raise TypeError(f'{type(self).__name__} coordinates must be numeric')

    def _test_int_or_none(self, value: object) -> object:
        if isinstance(value, int) or value is None:
            return value
        else:
            raise TypeError(f'{type(self).__name__} positions must be integers')

    @property
    def z(self):
        return self._z

    @z.setter
    def z(self, value):
        self._z = self._test_int_or_none(value)

    @property
    def c(self):
        return self._c

    @c.setter
    def c(self, value):
        self._c = self._test_int_or_none(value)

    @property
    def t(self):
        return self._t

    @t.setter
    def t(self, value):
        self._t = self._test_int_or_none(value)


class Point(Shape):
    def __init__(self, x, y, **kwargs):
        super().__init__(**kwargs)
        self.x = x
        self.y = y

    @property
    def x(self):
        return self._x

    @x.setter
    def x(self, value):
        self._x = self._test_numeric(value)

    @property
    def y(self):
        return self._y

    @y.setter
    def y(self, value):
        self._y = self._test_numeric(value)


class Line(Shape):
    def __init__(self, x1, y1, x2, y2, **kwargs):
        super().__init__(**kwargs)
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2

    @property
    def x1(self):
        return self._x1

    @x1.setter
    def x1(self, value):
        self._x1 = self._test_numeric(value)

    @property
    def y1(self):
        return self._y1

    @y1.setter
    def y1(self, value):
        self._y1 = self._test_numeric(value)

    @property
    def x2(self):
        return self._x2

    @x2.setter
    def x2(self, value):
        self._x2 = self._test_numeric(value)

    @property
    def y2(self):
        return self._y2

    @y2.setter
    def y2(self, value):
        self._y2 = self._test_numeric(value)


class Rectangle(Shape):
    def __init__(self, x, y, w, h, **kwargs):
        super().__init__(**kwargs)
        self.x = x
        self.y = y
        self.w = w
        self.h = h

    @property
    def x(self):
        return self._x

    @x.setter
    def x(self, value):
        self._x = self._test_numeric(value)

    @property
    def y(self):
        return self._y

    @y.setter
    def y(self, value):
        self._y = self._test_numeric(value)

    @property
    def w(self):
        return self._w

    @w.setter
    def w(self, value):
        self._w = self._test_numeric(value)

    @property
    def h(self):
        return self._h

    @h.setter
    def h(self, value):
        self._h = self._test_numeric(value)


class Ellipse(Shape):
    def __init__(self, x, y, x_rad, y_rad, **kwargs):
        super().__init__(**kwargs)
        self.x = x
        self.y = y
        self.x_rad = x_rad
        self.y_rad = y_rad

    @property
    def x(self):
        return self._x

    @x.setter
    def x(self, value):
        self._x = self._test_numeric(value)

    @property
    def y(self):
        return self._y

    @y.setter
    def y(self, value):
        self._y = self._test_numeric(value)

    @property
    def x_rad(self):
        return self._x_rad

    @x_rad.setter
    def x_rad(self, value):
        self._x_rad = self._test_numeric(value)

    @property
    def y_rad(self):
        return self._y_rad

    @y_rad.setter
    def y_rad(self, value):
        self._y_rad = self._test_numeric(value)


class Polygon(Shape):
    def __init__(self, point_list: list, is_open: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.point_list = self._test_point_list(point_list)
        self.is_open = is_open

    @staticmethod
    def _test_point_list(point_list):
        def _test_point(point):
            return all([isinstance(point[0], (int, float)),
                        isinstance(point[1], (int, float)),
                        len(point) == 2])

        if all([_test_point(p) for p in point_list]):
            return point_list
        else:
            raise ValueError('Points of polygon do not have the right types')


class Mask(Shape):
    pass


class Tag(OutputProperty):
    def __init__(self, tag_value: str, **kwargs):
        super().__init__(**kwargs)
        if isinstance(tag_value, str):
            self.comment = tag_value
        else:
            raise TypeError('Tag feature must be a string')


class KeyValues(OutputProperty):
    accepted_types = (str, int, float)

    def __init__(self, key_values: dict, **kwargs):
        super().__init__(**kwargs)
        self.key_values = key_values

    @property
    def key_values(self):
        return self._key_values

    @key_values.setter
    def key_values(self, key_values: dict):
        if self._validate_values(key_values):
            self._key_values = key_values
        else:
            raise ValueError(f'The values must be of types {KeyValues.accepted_types}')

    @staticmethod
    def _validate_values(key_values):
        return all([isinstance(v, KeyValues.accepted_types) for _, v in key_values.items()])


class Table(OutputProperty):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class Comment(OutputProperty):
    def __init__(self, comment: str, **kwargs):
        super().__init__(**kwargs)
        if isinstance(comment, str):
            self.comment = comment
        else:
            raise TypeError('Comment feature must be a string')

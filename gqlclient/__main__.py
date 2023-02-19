from typing import (Dict, Any, Tuple)
import keyword
import os

root = os.path.realpath(os.path.join(os.path.dirname(__file__), '..'))
WORK_DIR = f'{root}/build'
SCHEMA_PATH = f'{root}/tests/shopify.schema.json'
CLASS_FIELDS_DICT = {}


def get_inherited_fields(super_types: list) -> set:
    fields = []
    for x in super_types:
        fields.extend(CLASS_FIELDS_DICT[x['name']])
    return set(fields)


def visit_object(data: Dict[str, Any]) -> str:
    interfaces = data['interfaces']
    excludes = get_inherited_fields(interfaces)
    interfaces_list = ','.join(x['name'] for x in interfaces)
    if interfaces_list:
        interfaces_list = f"({interfaces_list})"

    object_str = f"class {data['name']}{interfaces_list}:\n"
    object_str += f"\t'''{data['description']}'''\n"

    for field in data['fields']:
        object_str += visit_field(field, excludes)

    return object_str


def visit_arg(data: Dict[str, Any]) -> str:
    arg_type = visit_field_type(data['type'])
    default_value = data['defaultValue']
    if arg_type.endswith(',None]'):
        arg_type = arg_type[6:-6]
        default_value = 'None'
    name = data['name']
    if name in keyword.kwlist:
        name += '_'
    arg_str = f"{name}:{arg_type}"
    if default_value:
        if default_value == 'false':
            arg_str += "=False"
        elif default_value == 'true':
            arg_str += "=True"
        elif default_value == 'None':
            arg_str += f"=None"
        else:
            arg_str += f"='{default_value}'"
    return arg_str


def visit_arg_description(data: Dict[str, Any]) -> Tuple[str, list]:
    description: str = data['description']
    if not description:
        return None, None
    name = data['name']
    if name in keyword.kwlist:
        name += '_'
    return name, [x.strip() for x in description.split('\n')]


def visit_field(data: Dict[str, Any], excludes: set) -> str:
    name = data['name']
    if name in excludes:
        return ''
    field_type = visit_field_type(data['type'])
    field_str = '\t@property\n'
    if data.get('isDeprecated'):
        field_str += f"\t@deprecated(reason='''{data['deprecationReason']}''')\n"
    if name in keyword.kwlist:
        name += '_'
    field_str += f"\tdef {name}(self) -> {field_type}:\n"
    if data['description']:
        field_str += f"\t\t'''{data['description']}'''\n"
    field_str += "\t\t...\n"
    return field_str


def visit_field_type(data: Dict[str, Any]) -> str:
    if data['ofType']:
        field_type = visit_field_type(data['ofType'])
        kind = data['kind']
        if kind == 'NON_NULL':
            return field_type[6:-6]
        elif kind == 'LIST':
            return f'Union[List[{field_type}],None]'
        return f"Union[{field_type},None]"
    else:
        return f"Union[{data['name']},None]"


def get_config_type(data: Dict[str, Any]) -> str:
    while data['ofType']:
        data = data['ofType']
    return data['name']


def visit_enum(data: Dict[str, Any]) -> str:
    enum_str = f"class {data['name']}:\n"
    enum_str += f"\t'''{data['description']}'''\n"
    enum_str += f"\t__slots__ = ()\n"
    enumValues = data["enumValues"]
    for i in range(len(enumValues)):
        ev = enumValues[i]
        if ev['description']:
            enum_str += f"\t'''{ev['description']}'''\n"
        if ev['isDeprecated']:
            enum_str += f"\t'''@deprecated: {ev['deprecationReason']}'''\n"
        enum_str += f"\t{ev['name']}={i}\n"
        pass
    return enum_str


def visit_input_object(data: Dict[str, Any]) -> str:
    input_str = f"class {data['name']}:\n"
    input_str += f"\t'''{data['description']}'''\n"

    for field in data['inputFields']:
        input_str += visit_field(field, set())

    return input_str


def visit_union(data: Dict[str, Any]) -> str:
    types = []
    for field in data['possibleTypes']:
        typ = visit_field_type(field)
        if typ.startswith('Union['):
            typ = typ[6:-6]
        types.append(typ)
    union_str = f"'''{data['description']}'''\n"
    if len(types) > 1:
        union_str += f"{data['name']}=Union[{','.join(types)}]\n"
    else:
        union_str += f"{data['name']}={types[0]}\n"
    return union_str


def visit_intertface(data: Dict[str, Any]) -> str:
    object_str = f"class {data['name']}(abc.ABC):\n"
    object_str += f"\t'''{data['description']}'''\n"

    for field in data['fields']:
        object_str += visit_field(field, set())

    return object_str


def visit_type(data: Dict[str, Any], is_config) -> str:
    kind = data['kind']
    if kind == 'OBJECT':
        if is_config:
            return visit_config(data)
        return visit_object(data)
    elif kind == 'ENUM':
        return visit_enum(data)
    elif kind == 'INPUT_OBJECT':
        return visit_input_object(data)
    elif kind == 'UNION':
        return visit_union(data)
    elif kind == 'SCALAR':
        name = data['name']
        rst = f"'''{data['description']}'''\n"
        rst += f"{name} = NewType('{name}', str)\n"
        return rst
    elif kind == 'INTERFACE':
        return visit_intertface(data)
    raise Exception(f'unknow kind {kind}')


def parse_func(data: Dict[str, Any]) -> Dict[str, Any]:
    args = data.get('args')
    name = data['name']
    args_description = {}
    deprecated = ''
    return_type = ''
    if 'type' in data:
        return_type = get_config_type(data['type'])
    args_list = []
    if args:
        args_list2 = []
        for arg in (visit_arg(x) for x in args):
            if arg.find('=') > 0:
                args_list2.append(arg)
                continue
            args_list.append(arg)
        args_list.extend(args_list2)

        for x in args:
            k, v = visit_arg_description(x)
            if k:
                args_description[k] = v
    if data.get('isDeprecated'):
        deprecated = f"@deprecated(reason='''{data['deprecationReason']}''')"
    if name in keyword.kwlist:
        name += '_'
    return {
        'args_list': args_list,
        'type': return_type,
        'args_description': args_description,
        'func_description': data['description'],
        'func_name': name,
        'deprecated': deprecated
    }


def get_func_description(
    args_description: dict,
    func_description: str,
    indent=0,
) -> str:
    indent_str = '\t' * indent
    args_descp = ''
    for k, v in args_description.items():
        v = f'\n{indent_str}\t\t\t'.join(v)
        args_descp += f"\n{indent_str}\t\t{k}:{v}"
    if args_descp:
        args_descp = f'\n{indent_str}\tArgs:{args_descp}'
    return f"{indent_str}\t'''{func_description}{args_descp}'''\n"


def visit_config_field(data: Dict[str, Any], excludes: set) -> str:
    """
    This is an example of Google style.
    
    Args:
        param1: This is the first param.
    
    Returns:
        This is a description of what is returned.
    
    Raises:
        This is a description of what is returned.
    """
    name = data['name']
    if name in excludes:
        return ''
    func_config = parse_func(data)
    field_str = ''
    args_list = func_config['args_list']
    return_type = func_config['type']
    if not args_list:
        field_str += '\t@property\n'
        args_list = ['self']
    else:
        args_list = [f'_config:{return_type}', '*', *args_list]
        field_str += '\t@staticmethod\n'
        return_type = 'None'
    if func_config['deprecated']:
        field_str += f"\t{func_config['deprecated']}\n"

    args_list = ','.join(args_list)
    field_str += f"\tdef {func_config['func_name']}({args_list}) -> {return_type}:\n"
    description = get_func_description(
        func_config['args_description'],
        func_config['func_description'],
        indent=1,
    )
    field_str += description
    field_str += "\t\t...\n"
    return field_str


def visit_config(data: Dict[str, Any]) -> str:
    interfaces = data['interfaces']
    excludes = get_inherited_fields(interfaces)
    interfaces_list = ','.join(f"{x['name']}" for x in interfaces)
    if interfaces_list:
        interfaces_list = f"({interfaces_list})"

    object_str = f"class {data['name']}{interfaces_list}:\n"
    object_str += f"\t'''{data['description']}'''\n"

    for field in data['fields']:
        object_str += visit_config_field(field, excludes)

    return object_str


import ijson

fo = open(f'{WORK_DIR}/common.py', 'w', encoding='utf8')
fo.write('''import abc
from typing import (
    List,
    NewType,
    Union,
    Any,
)

AccountNumber = NewType('AccountNumber', str)
BigInt = NewType('BigInt', str)
Byte = NewType('Byte', str)
CountryCode = NewType('CountryCode', str)
Currency = NewType('Currency', str)
Date = NewType('Date', str)
DateTime = NewType('DateTime', str)
DID = NewType('DID', str)
Duration = NewType('Duration', str)
EmailAddress = NewType('EmailAddress', str)
HexColorCode = NewType('HexColorCode', str)
Hexadecimal = NewType('Hexadecimal', str)
HSL = NewType('HSL', str)
IPv4 = NewType('IPv4', str)
IPv6 = NewType('IPv6', str)
IBAN = NewType('IBAN', str)
ISBN = NewType('ISBN', str)
JSON = NewType('JSON', str)
JSONObject = NewType('JSONObject', str)
JWT = NewType('JWT', str)
Latitude = NewType('Latitude', str)
LocalDate = NewType('LocalDate', str)
LocalEndTime = NewType('LocalEndTime', str)
LocalTime = NewType('LocalTime', str)
Locale = NewType('Locale', str)
Longitude = NewType('Longitude', str)
MAC = NewType('MAC', str)
NegativeFloat = NewType('NegativeFloat', str)
NegativeInt = NewType('NegativeInt', str)
NonEmptyString = NewType('NonEmptyString', str)
NonNegativeFloat = NewType('NonNegativeFloat', str)
NonNegativeInt = NewType('NonNegativeInt', str)
NonPositiveFloat = NewType('NonPositiveFloat', str)
NonPositiveInt = NewType('NonPositiveInt', str)
ObjectID = NewType('ObjectID', str)
PhoneNumber = NewType('PhoneNumber', str)
Port = NewType('Port', str)
PositiveFloat = NewType('PositiveFloat', str)
PositiveInt = NewType('PositiveInt', str)
PostalCode = NewType('PostalCode', str)
RegularExpression = NewType('RegularExpression', str)
RGB = NewType('RGB', str)
RGBA = NewType('RGBA', str)
RoutingNumber = NewType('RoutingNumber', str)
SafeInt = NewType('SafeInt', str)
Time = NewType('Time', str)
TimeZone = NewType('TimeZone', str)
Timestamp = NewType('Timestamp', str)
URL = NewType('URL', str)
USCurrency = NewType('USCurrency', str)
UTCOffset = NewType('UTCOffset', str)
UUID = NewType('UUID', str)
Void = NewType('Void', str)
Cuid = NewType('Cuid', str)
Ip = NewType('Ip', str)
Semver = NewType('Semver', str)

import warnings
import functools


def deprecated(reason=None, version=None):

    def wrapper(func):

        @functools.wraps(func)
        def wraped_func(*args, **kwargs):
            info = ''
            if version:
                info += f"After version {version}, "
            info += f"{func.__name__} has been deprecated."
            if reason:
                info += f"Because {reason}"
            warnings.warn(info, DeprecationWarning, stacklevel=2)
            return func(*args, **kwargs)

        return wraped_func

    return wrapper


################


class _GQLConfig:
    __slots__ = ('_data', )
    _attr_from = {}

    def __init__(self) -> None:
        self._data = {}

    def __call__(self, value, **kwds):
        if isinstance(value, _GQLConfig):
            self._data = value._data.copy()
        else:
            self._data = {}
        for k, v in kwds.items():
            self._data[f'${k}'] = v

    def _key(self, attrName: str) -> str:
        if attrName.endswith('_'):
            return attrName[:-1]
        return attrName

    def _get_ctx(self, _key: str):
        _data = self._data
        _on_key = self._judge_attr_from(_key)
        if _on_key:
            _on_key = f"... on {_on_key}"
            if _on_key not in _data:
                _data[_on_key] = {}
            _data = _data[_on_key]
        return _data

    @classmethod
    def _judge_attr_from(cls, attrName: str) -> str:
        return cls._attr_from.get(attrName)

    def __setattr__(self, k: str, v):
        if k.startswith('_'):
            return super().__setattr__(k, v)
        _key = self._key(k)
        _data = self._get_ctx(_key)
        _data[_key] = v

    def __getattribute__(self, k: str):
        if k.startswith('_'):
            return super().__getattribute__(k)
        try:
            _key = self._key(k)
            _data = self._get_ctx(_key)
            if _key not in _data:
                _data[_key] = _GQLConfig()
            return _data[_key]
        except KeyError:
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{k}'")

    def __delattr__(self, k: str):
        if k.startswith('_'):
            return super().__delattr__(k)
        try:
            _key = self._key(k)
            _on_key = self._judge_attr_from(_key)
            if _on_key:
                if len(self._data[_on_key]) > 1:
                    del self._data[_on_key][_key]
                else:
                    del self._data[_on_key]
                return
            del self._data[_key]
        except KeyError:
            raise AttributeError(k)


def parse_gql_param(config) -> str:
    if isinstance(config, _GQLConfig):
        config = config._data
    if isinstance(config, (str, float, int)):
        return str(config)
    if isinstance(config, bool):
        if config:
            return 'true'
        return 'false'
    if isinstance(config, dict):
        return f"{{{','.join({f'{k}:{parse_gql_param(v)}' for k, v in config.items()})}}}"
    return f"[{','.join(parse_gql_param(x) for x in config)}]"


def parse_gql_config(config) -> str:
    if isinstance(config, _GQLConfig):
        config = config._data
    if isinstance(config, str):
        return config
    fields = []
    parms = []
    for k, v in config.items():
        if k.startswith('$'):
            parms.append(f"{k[1:]}:{parse_gql_param(v)}")
        else:
            fields.append(f"{k} {parse_gql_config(v)}")
    rst = ''
    if parms:
        rst += f"({','.join(parms)})"
    if fields:
        rst += f"{{{' '.join(fields)}}}"
    return rst

def directive_impl(
    payload: Union[_GQLConfig, dict],
    directive: str,
    **kwargs,
):
    data = {}
    for k, v in kwargs.items():
        key = f'${k}'
        if key.endswith('_'):
            key = key[:-1]
        data[key] = v
    if isinstance(payload, _GQLConfig):
        payload._data[f'@{directive}'] = data
    else:
        payload[f'@{directive}'] = data
    pass

''')
fo.close()
fo = open(f'{WORK_DIR}/shopifygql.pyi', 'w', encoding='utf8')
config_file = open(f'{WORK_DIR}/config.pyi', 'w', encoding='utf8')

fo.write('from .common import *\n')
config_file.write('from .common import *\n')

with open(SCHEMA_PATH, 'r', encoding='utf8') as fi:
    for typ in ijson.items(fi, '__schema.types.item'):
        if typ['name'].startswith('__'):
            continue
        tmp = []
        for x in typ['fields'] or []:
            tmp.append(x['name'])
        for x in typ['inputFields'] or []:
            tmp.append(x['name'])
        CLASS_FIELDS_DICT[typ['name']] = tmp
#### 生成pyi文件
with open(SCHEMA_PATH, 'r', encoding='utf8') as fi:
    for typ in ijson.items(fi, '__schema.types.item'):
        if typ['name'].startswith('__'):
            continue
        config_file.write(visit_type(typ, True))
        config_file.write('\n')
        fo.write(visit_type(typ, False))
        fo.write('\n')

with open(SCHEMA_PATH, 'r', encoding='utf8') as fi:
    for directive in ijson.items(fi, '__schema.directives.item'):
        conf = parse_func(directive)
        args_list = conf['args_list']
        args_list = ','.join(args_list)
        directive_str = f"def {conf['func_name']}(payload:Any, *, {args_list})->None:\n"

        args_description: dict = conf['args_description']
        args_descp = ''
        for k, v in args_description.items():
            v = '\n\t\t\t'.join(v)
            args_descp += f"\n\t\t{k}:{v}"
        if args_descp:
            args_descp = '\n\tArgs:' + args_descp
        directive_str += f"\t'''{conf['func_description']}{args_descp}'''\n"
        config_file.write(directive_str)

#### 生成py文件

config_file = open(f'{WORK_DIR}/config.py', 'w', encoding='utf8')
config_file.write('from .common import _GQLConfig,NewType,directive_impl\n')

with open(SCHEMA_PATH, 'r', encoding='utf8') as fi:
    for typ in ijson.items(fi, '__schema.types.item'):
        if typ['name'].startswith('__'):
            continue
        kind = typ['kind']
        cls_str = ''
        if kind == 'OBJECT' or kind == 'INPUT_OBJECT':
            cls_str = f"class {typ['name']}(_GQLConfig):\n\tpass\n"
        elif kind == 'ENUM':
            cls_str = visit_enum(typ)
        elif kind == 'SCALAR':
            name = typ['name']
            cls_str = f"{name} = NewType('{name}', str)\n"
        elif kind == 'UNION' or kind == 'INTERFACE':
            cls_str = f"class {typ['name']}(_GQLConfig):\n\n"
            _attr_from = {}
            sub_cls = [x['name'] for x in typ['possibleTypes']]
            for k in sub_cls:
                for kk in CLASS_FIELDS_DICT[k]:
                    _attr_from[kk] = k
            cls_str += f"\t_attr_from ={_attr_from}\n"
            # return visit_intertface(data)
        config_file.write(cls_str)
        config_file.write('\n')

with open(SCHEMA_PATH, 'r', encoding='utf8') as fi:
    for directive in ijson.items(fi, '__schema.directives.item'):
        conf = parse_func(directive)
        config_file.write(
            f'''def {conf['func_name']}(payload, **kwargs):\n\tdirective_impl(payload, '{directive['name']}', **kwargs)\n'''
        )

import unittest
import json
from gqlclient.dto import *


class TestDtoBase(unittest.TestCase):
    def setUp(self):
        self.DtoDict = DtoDict
        self.DtoList = DtoList
        self.Dto = Dto

    def test_direct_conversion(self):
        pd = self.DtoDict()
        self.assertEqual(pd, {})
        self.assertEqual(pd, self.DtoDict({}))
        pd = self.DtoDict({"a": '1', "b": [1, 23], "c": {"cc": False}})
        self.assertEqual(pd, {"a": '1', "b": [1, 23], "c": {"cc": False}})
        self.assertEqual(pd.a, '1')
        self.assertEqual(pd.b, [1, 23])
        self.assertEqual(pd.c, {"cc": False})
        self.assertEqual(pd.c.cc, False)
        pa = self.DtoList()
        self.assertEqual(pa, [])
        self.assertEqual(pa, self.DtoList([]))
        pa = self.DtoList(['s', {'x': 0}, [1, 2]])
        self.assertEqual(pa, ['s', {'x': 0}, [1, 2]])

    def test_assignment(self):
        pd = self.DtoDict()
        pd.a = 1
        self.assertEqual(pd, {'a': 1})
        pd.a = []
        self.assertEqual(pd, {'a': []})
        pd.a = {'x': 'x'}
        self.assertEqual(pd, {'a': {'x': 'x'}})
        pd.a.x = {'x': 'x'}
        self.assertEqual(pd, {'a': {'x': {'x': 'x'}}})
        pa = self.DtoList([1, 2, 3])
        self.assertEqual(pa, [1, 2, 3])
        pa[0] = 's'
        self.assertEqual(pa, ['s', 2, 3])
        pa[1] = []
        self.assertEqual(pa, ['s', [], 3])
        pa[2] = {}
        self.assertEqual(pa, ['s', [], {}])
        pa[2].x = 1
        self.assertEqual(pa, ['s', [], {'x': 1}])
        pa[1:] = [0]
        self.assertEqual(pa, ['s', 0])

    def test_raise(self):
        self.assertRaises(TypeError, lambda: self.DtoList('s'))
        self.assertRaises(TypeError, lambda: self.DtoList(0))
        self.assertRaises(TypeError, lambda: self.DtoList({}))

        self.assertRaises(TypeError, lambda: self.DtoDict(1))
        self.assertRaises(TypeError, lambda: self.DtoDict('s'))
        self.assertRaises(TypeError, lambda: self.DtoDict([]))
        pd = self.DtoDict()
        pd['_a'] = 1
        self.assertEqual(pd, {'_a': 1})
        self.assertRaises(AttributeError, lambda: pd._a)
        with self.assertRaises(AttributeError):
            pd._a = 2
        pd.clear()
        pd['get'] = 1
        self.assertEqual(pd, {'get': 1})
        self.assertTrue(callable(pd.get))
        with self.assertRaises(AttributeError):
            pd.get = 2

    def test_compatibility_with_list(self):
        pa = self.DtoList([1, 2, 3])
        pa.append([4])
        self.assertEqual(pa, [1, 2, 3, [4]])
        pa.extend([4])
        self.assertEqual(pa, [1, 2, 3, [4], 4])
        pa.insert(0, {})
        self.assertEqual(pa, [{}, 1, 2, 3, [4], 4])
        pa.insert(-2, {})
        self.assertEqual(pa, [{}, 1, 2, 3, {}, [4], 4])
        pa.clear()
        self.assertEqual(pa, [])
        self.assertEqual(pa * 2, [])
        pa.append(1)
        self.assertEqual(pa * 2, [1, 1])
        self.assertEqual(pa + [3], [1, 3])
        pa += [3]
        self.assertEqual(pa, [1, 3])

    def test_compatibility_with_dict(self):
        pd = self.DtoDict()
        pd['a'] = 1
        self.assertEqual(pd, {'a': 1})
        pd.b = '1'
        self.assertEqual(pd, {'a': 1, 'b': '1'})
        self.assertEqual(pd['b'], '1')
        pd.update({'b': 333, 'c': 'tt'})
        self.assertEqual(pd, {'a': 1, 'b': 333, 'c': 'tt'})
        self.assertEqual(pd.c, 'tt')
        self.assertEqual(pd.b, 333)
        self.assertEqual(pd.get('xx'), None)
        self.assertEqual(pd.get('xx', 'Nil'), 'Nil')

    def test_del(self):
        pa = self.DtoList([1, 2, 3, {}])
        del pa[0]
        self.assertEqual(pa, [2, 3, {}])
        pa.remove(3)
        self.assertEqual(pa, [2, {}])
        pa.remove({})
        self.assertEqual(pa, [2])
        pd = self.DtoDict({"a": '1', "b": [1, 23], "c": {"cc": False}})
        del pd.b
        self.assertEqual(pd, {"a": '1', "c": {"cc": False}})
        self.assertRaises(AttributeError, lambda: pd.b)
        del pd.c.cc
        self.assertEqual(pd, {"a": '1', "c": {}})
        self.assertEqual(pd.c, {})
        pd.pop('a')
        self.assertEqual(pd, {"c": {}})
        self.assertRaises(AttributeError, lambda: pd.a)
        self.assertRaises(KeyError, lambda: pd.pop('a'))
        with self.assertRaises(AttributeError):
            del pd.xasca

    def test_load(self):
        pd = self.Dto(
            json.loads('{"a":1,"b":[1,2],"c":{"x":0}}', object_hook=self.Dto))

        self.assertEqual(pd, {"a": 1, "b": [1, 2], "c": {"x": 0}})

        pd['c'].x = 1
        self.assertEqual(pd, {"a": 1, "b": [1, 2], "c": {"x": 1}})
        pd['b'][0] = {"jj": 1}
        self.assertEqual(pd, {"a": 1, "b": [{"jj": 1}, 2], "c": {"x": 1}})
        self.assertEqual(pd['b'][0].jj, 1)
        pa = self.Dto(
            json.loads('[1,"ACS",[1,2],{"a":0}]', object_hook=self.Dto))
        self.assertEqual(pa, [1, "ACS", [1, 2], {"a": 0}])

        pa[3].a = 1
        self.assertEqual(pa, [1, "ACS", [1, 2], {"a": 1}])
        pa[2][1] = 0
        self.assertEqual(pa, [1, "ACS", [1, 0], {"a": 1}])
        pa[2][:] = {'x': 'a'}
        self.assertEqual(pa, [1, "ACS", ['x'], {"a": 1}])

    def test_inheritance(self):
        class D(self.DtoDict):
            def _key(self, attrName: str) -> str:
                return attrName.replace('_', '-')

            pass

        class L(self.DtoList):
            pass

        pd = D({"a": {}, "b": [], "a-1": 2})
        self.assertIsInstance(pd, D)
        self.assertIsInstance(pd.a, D)

        self.assertIsInstance(pd.b, DtoList)
        self.assertEqual(pd.a_1, 2)

        pa = L([1, {}, []])
        self.assertIsInstance(pa, L)
        self.assertIsInstance(pa[1], DtoDict)
        self.assertIsInstance(pa[2], L)

    def test_init(self):
        pa = self.DtoList([1, "ACS", [1, 2], {"a": 0}])
        pa = self.DtoList(pa)
        self.assertEqual(pa, [1, "ACS", [1, 2], {"a": 0}])
        pd = self.DtoDict({"a": 1, "b": [1, 2], "c": {"x": 0}})
        pd = self.DtoDict(pd)
        self.assertEqual(pd, {"a": 1, "b": [1, 2], "c": {"x": 0}})

    def test_hasattr(self):
        a = self.DtoDict()
        self.assertFalse(hasattr(a, 'read'))
        a.read = 1
        self.assertTrue(hasattr(a, 'read'))

        class O:
            ...

        o = O()
        msg = ''

        try:
            print(o.HKJA)
        except Exception as e:
            msg = str(e)

        with self.assertRaises(AttributeError, msg=msg):
            print(a.HKJA)


class TestDto2(TestDtoBase):
    def setUp(self):
        class DtoDict2(DtoDict):
            pass

        class DtoList2(DtoList):
            pass

        self.DtoDict = DtoDict2
        self.DtoList = DtoList2
        self.Dto = Dto

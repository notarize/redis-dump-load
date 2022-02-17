import nose.plugins.attrib
import redisdl
import shutil
import subprocess
try:
    import unittest2 as unittest
except ImportError:
    import unittest
import json
import os.path
from . import util

unicode_dump = {'akey': {'type': 'string', 'value': util.u('\u041c\u043e\u0441\u043a\u0432\u0430')}, 'lvar': {'type': 'list', 'value': [util.u('\u041c\u043e\u0441\u043a\u0432\u0430')]}, 'svar': {'type': 'set', 'value': [util.u('\u041c\u043e\u0441\u043a\u0432\u0430')]}, 'zvar': {'type': 'zset', 'value': [[util.u('\u041c\u043e\u0441\u043a\u0432\u0430'), 1.0]]}, 'hvar': {'type': 'hash', 'value': {'hkey': util.u('\u041c\u043e\u0441\u043a\u0432\u0430')}}}

check_output = util.get_subprocess_check_output()

class ProgramTest(unittest.TestCase):
    def setUp(self):
        import redis
        self.r = redis.Redis()
        for key in self.r.keys('*'):
            self.r.delete(key)

        self.program = os.path.join(os.path.dirname(__file__), '..', 'redisdl.py')

    def test_dump(self):
        self.check_dump(self.program)

    def check_dump(self, program):
        path = os.path.join(os.path.dirname(__file__), 'fixtures', 'dump.json')
        with open(path) as f:
            dump = f.read()

        redisdl.loads(dump)

        redump = check_output([program]).decode('utf-8')

        expected = json.loads(dump)
        actual = json.loads(redump)

        self.assertEqual(expected, actual)

    def test_dump_unicode(self):
        redisdl.loads(json.dumps(unicode_dump))

        redump = check_output([self.program]).decode('utf-8')

        actual = json.loads(redump)

        self.assertEqual(unicode_dump, actual)

    def test_load(self):
        path = os.path.join(os.path.dirname(__file__), 'fixtures', 'dump.json')
        self.check_load([self.program, '-l', path], path)

    @util.requires_ijson
    @nose.plugins.attrib.attr('yajl2')
    def test_load_yajl2(self):
        path = os.path.join(os.path.dirname(__file__), 'fixtures', 'dump.json')
        self.check_load([self.program, '-l', '-B', 'yajl2', path], path)

    def check_load(self, cmd, path):
        with open(path) as f:
            dump = f.read()

        subprocess.check_call(cmd)

        redump = redisdl.dumps()

        expected = json.loads(dump)
        actual = json.loads(redump)

        self.assertEqual(expected, actual)

    def test_load_unicode(self):
        path = os.path.join(os.path.dirname(__file__), 'fixtures', 'dump-unicode.json')
        with open(path) as f:
            dump = f.read()

        subprocess.check_call([self.program, '-l', path])

        redump = redisdl.dumps()

        actual = json.loads(redump)

        self.maxDiff = None
        self.assertEqual(unicode_dump, actual)

    @util.with_temp_dir
    def test_dump_alias(self, tmp_dir):
        aliased_program = os.path.join(tmp_dir, 'redisdump')
        shutil.copy(self.program, aliased_program)
        self.check_dump(aliased_program)

    @util.with_temp_dir
    def test_load_alias(self, tmp_dir):
        aliased_program = os.path.join(tmp_dir, 'redisload')
        path = os.path.join(os.path.dirname(__file__), 'fixtures', 'dump.json')
        shutil.copy(self.program, aliased_program)
        self.check_load([aliased_program, path], path)

    def test_load_ttl_preference(self):
        path = os.path.join(os.path.dirname(__file__), 'fixtures', 'ttl_and_expireat.json')
        with open(path) as f:
            dump = f.read()

        subprocess.check_call([self.program, '-l', path])

        redump = redisdl.dumps()

        actual = json.loads(redump)

        self.assertLess(actual['akey']['ttl'], 3601)

    def test_load_expireat_preference(self):
        path = os.path.join(os.path.dirname(__file__), 'fixtures', 'ttl_and_expireat.json')
        with open(path) as f:
            dump = f.read()

        subprocess.check_call([self.program, '-l', '-A', path])

        redump = redisdl.dumps()

        actual = json.loads(redump)

        self.assertGreater(actual['akey']['ttl'], 36000)

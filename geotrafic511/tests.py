from __future__ import print_function

import glob
import json
import os
import unittest

import converter

from open511.converter.o5json import xml_to_json

class GeoTraficIntegrationTests(unittest.TestCase):

    maxDiff = None

    def test_outputs(self):
        my_dir = os.path.dirname(os.path.realpath(__file__))
        fixtures_dir = os.path.join(my_dir, 'fixtures')
        input_files = glob.glob(fixtures_dir + '/*.input.xml')
        self.assertGreater(len(input_files), 3)
        for input_file in input_files:
            print("Processing file %s" % os.path.basename(input_file))
            with open(input_file) as f:
                input_data = f.read()
            xml = converter.geotrafic_to_xml(input_data)
            json_result = xml_to_json(xml)
            json_result = json.loads(json.dumps(json_result)) # normalize it

            output_fixture = input_file.replace('.input.xml', '.output.json')
            with open(output_fixture) as f:
                valid_json = json.load(f)
            self.assertEqual(json_result, valid_json)

if __name__ == '__main__':
    unittest.main()

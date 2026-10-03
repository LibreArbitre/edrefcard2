"""Rendering regressions, including dependency-free geometry and input probes."""
import ast
import copy
import importlib.util
import math
from collections import OrderedDict
from pathlib import Path
from types import SimpleNamespace
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('runtime_test', ROOT / 'www/scripts/mapping_runtime.py')
runtime = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runtime)


def functions(path, names, namespace):
    """Execute the real function bodies, without app imports or live DB writes."""
    tree = ast.parse((ROOT / path).read_text(encoding='utf-8'))
    nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names]
    for node in nodes:
        node.decorator_list = []
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), 'exec'), namespace)
    return namespace


class DrawingProbe:
    def __init__(self, impossible=False):
        self.font_size = 10
        self.balance = self.calls = 0
        self.impossible = impossible
        self.written = []

    def push(self):
        self.balance += 1

    def pop(self):
        self.balance -= 1

    def get_font_metrics(self, image, text, multiline=False):
        self.calls += 1
        return SimpleNamespace(text_width=100000 if self.impossible else len(text)*self.font_size/2,
                               text_height=self.font_size, ascender=self.font_size*.8,
                               character_width=self.font_size/2)

    def text(self, **kwargs):
        self.written.append(kwargs)

    def rectangle(self, **kwargs):
        pass

    def line(self, *args):
        pass


class ImageProbe:
    def __init__(self, width, height):
        if width <= 0 or height <= 0:
            raise AssertionError('Invalid image extent')

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


class RenderingSafetyTests(unittest.TestCase):
    def setUp(self):
        self.rectangles = []
        def layout(image, context, texts, rect, font_size):
            self.assertGreater(rect['width'], 0)
            self.assertGreater(rect['height'], 0)
            self.rectangles.append(dict(rect))
            return []
        style = {'Font': 'test-font', 'Color': 'green'}
        self.env = functions('www/scripts/renderer.py',
                             ['_drawDataDrivenBox', '_drawControlSymbol', '_symbolColumnWidth',
                              '_buildJoyTexts', 'calculateBestFitFontSize', 'calculateBestFontSize'], {
            'math': math, 'Image': ImageProbe, 'Color': lambda c: c,
            'getFontPath': lambda *args: 'test-font', 'layoutText': layout,
            '_LEADER_COLOR': '#962320', '_SYMBOL_GLYPHS': {'press':'0','up':'^','stage1':'stage 1'},
            'normalize_input': runtime.normalize_input, 'matches_input': runtime.matches_input,
            'groupStyles': {'Ship': style, 'Modifier': style, 'General': style},
            'categoryStyles': {'General': style},
            'ModifierStyles': SimpleNamespace(index=lambda n: style),
            'isRedundantSpecialisation': lambda control, bind: False,
        })

    def test_sol_small_box_has_positive_text_area(self):
        row = {'symbol':'press','number':'1','_texts':[{'Text':'Fire'}]}
        self.env['_drawDataDrivenBox'](DrawingProbe(), None, {
            'label':'BTN1','box_xy':[74,204],'box_wh':[193,40], 'rows':[row]})
        self.assertEqual(len(self.rectangles), 1)
        self.assertGreater(self.rectangles[0]['height'], 20)

    def test_tiny_word_symbol_gutters_leave_room_for_text(self):
        self.env['_drawDataDrivenBox'](DrawingProbe(), None, {
            'label':'Trigger','box_xy':[0,0],'box_wh':[40,30],
            'rows':[{'symbol':'stage1','number':1,'_texts':[{'Text':'Fire'}]}]})
        self.assertEqual(len(self.rectangles), 1)

    def test_unused_pdf_rows_keep_original_slot(self):
        box = {'box_xy':[100,100],'box_wh':[400,400],'no_chrome':True,
               'rows':[{'_texts':[]} for _ in range(4)]}
        box['rows'][1]['_texts'] = [{'Text':'Only down is bound'}]
        self.env['_drawDataDrivenBox'](DrawingProbe(), None, box)
        self.assertEqual(self.rectangles[0]['y'], 206)
        self.assertEqual(self.rectangles[0]['height'], 88)

    def test_pdf_field_rect_preserves_gap_and_offset(self):
        self.env['_drawDataDrivenBox'](DrawingProbe(), None, {
            'box_xy':[100,100],'box_wh':[400,400],'no_chrome':True,
            'rows':[{'field_rect':[.25,.6,.5,.1], '_texts':[{'Text':'Brake'}]}]})
        self.assertAlmostEqual(self.rectangles[0]['x'], 208)
        self.assertAlmostEqual(self.rectangles[0]['y'], 344)
        self.assertAlmostEqual(self.rectangles[0]['height'], 32)

    def test_empty_font_fit_is_safe(self):
        self.assertEqual(self.env['calculateBestFitFontSize'](DrawingProbe(), 100, 20, [], 40), 40)

    def test_font_fit_stops_and_restores_context(self):
        context = DrawingProbe(impossible=True)
        with self.assertRaisesRegex(ValueError, 'minimum font size'):
            self.env['calculateBestFitFontSize'](context, 1, 1,
                [{'Text':'Very long', 'Style':{'Font':'test'}}], 40)
        self.assertEqual(context.calls, 40)
        self.assertEqual(context.balance, 0)

    def test_font_fit_accepts_exact_height(self):
        context = DrawingProbe()
        self.assertEqual(self.env['calculateBestFitFontSize'](context, 200, 20,
            [{'Text':'Test','Style':{'Font':'test'}}], 20), 20)

    def test_invalid_dimensions_fail_before_image_creation(self):
        for width, height in [(0,10),(10,-12)]:
            with self.assertRaises(ValueError):
                self.env['calculateBestFitFontSize'](DrawingProbe(), width, height, [], 40)

    def test_half_axes_do_not_duplicate_opposite_actions(self):
        pk = {'Device':'TEST','DeviceIndex':0,'Key':'Joy_RYAxis','BaseKey':'Neg_Joy_RYAxis',
              'Binds':{'Unmodified':{'Controls':{
                  'Left':{'Name':'Left thrust','Group':'Ship','InputKey':'Neg_Joy_RYAxis'},
                  'Right':{'Name':'Right thrust','Group':'Ship','InputKey':'Pos_Joy_RYAxis'},
                  'Axis':{'Name':'Analogue thrust','Group':'Ship','InputKey':'Joy_RYAxis'}}}}}
        physical = {'TEST::0::Joy_RYAxis':pk}
        before = copy.deepcopy(physical)
        build = self.env['_buildJoyTexts']
        self.assertEqual([t['Text'] for t in build(['TEST'],'Neg_Joy_RYAxis',0,physical,{},'Group')], ['Left thrust'])
        self.assertEqual([t['Text'] for t in build(['TEST'],'Pos_Joy_RYAxis',0,physical,{},'Group')], ['Right thrust'])
        self.assertEqual(len(build(['TEST'],'Joy_RYAxis',0,physical,{},'Group')),3)
        self.assertEqual(physical,before)

    def test_missing_inputs_distinguishes_full_and_half_axes(self):
        mapping = {'boxes':[{'rows':[{'joy':'Neg_Joy_RYAxis'}]}]}
        keys = ['Neg_Joy_RYAxis','Pos_Joy_RYAxis','Joy_RYAxis']
        self.assertEqual(runtime.missing_inputs(mapping,keys), ['Joy_RYAxis','Pos_Joy_RYAxis'])
        mapping['boxes'][0]['rows'][0]['joy'] = 'Joy_RYAxis'
        self.assertEqual(runtime.missing_inputs(mapping,keys),[])

    def test_modifier_only_button_is_rendered_and_counted(self):
        modifiers = {'TEST::0::Joy_3':[{'Number':1,'Device':'TEST','DeviceIndex':0,
                                      'Key':'Joy_3','ModifierKey':'TEST::0::Joy_3'}]}
        texts = self.env['_buildJoyTexts'](['TEST'],'Joy_3',0,{},modifiers,'Group')
        self.assertEqual([t['Text'] for t in texts], ['Modifier 1'])
        self.assertEqual(runtime.used_inputs({},modifiers,['TEST'],0),{'Joy_3'})

    def test_directional_modifier_is_not_shown_on_opposite_half_axis(self):
        modifiers = {'TEST::0::Pos_Joy_RYAxis':[{'Number':1,'Device':'TEST',
                     'DeviceIndex':0,'Key':'Pos_Joy_RYAxis','ModifierKey':'TEST::0::Pos_Joy_RYAxis'}]}
        build = self.env['_buildJoyTexts']
        self.assertEqual(build(['TEST'],'Neg_Joy_RYAxis',0,{},modifiers,'Group'),[])
        self.assertEqual(len(build(['TEST'],'Joy_RYAxis',0,{},modifiers,'Group')),1)

    def test_physical_warthog_does_not_imply_target(self):
        self.assertEqual(runtime.mapping_software_warning({
            'ThrustMasterWarthogJoystick::0': {'HandledDevices':['ThrustMasterWarthogCombined']},
            'ThrustMasterWarthogThrottle::0':None}), '')
        self.assertIn('virtual', runtime.mapping_software_warning({'ThrustMasterWarthogCombined::0':None}))

    def test_parser_ignores_empty_nodes_and_preserves_each_direction(self):
        try:
            from lxml import etree
        except ImportError:
            self.skipTest('lxml required')
        controls = {name:{'Name':name,'Group':'Ship','Type':'Digital'}
                    for name in ['Left','Right','Empty','MissingKey']}
        parser = functions('www/scripts/parser.py',['parseBindings','_rewriteVPCDevice'], {
            '__name__':'standalone_probe', 'etree':etree, 'html':__import__('html'),
            'OrderedDict':OrderedDict, 'controls':controls, 'supportedDevices':{},
            'logError':lambda *args:None, 'mapping_software_warning':runtime.mapping_software_warning,
        })
        errors = SimpleNamespace(errors='',deviceWarnings='Old TARGET warning')
        xml = '<Root><Empty><Primary/><Secondary Device="{NoDevice}"/></Empty>' \
              '<MissingKey><Primary Device="TEST"/></MissingKey>' \
              '<Left><Primary Device="TEST" Key="Neg_Joy_RYAxis"/></Left>' \
              '<Right><Primary Device="TEST" Key="Pos_Joy_RYAxis"/></Right></Root>'
        physical, _, devices = parser['parseBindings']('test',xml,['Ship'],errors)
        self.assertEqual(set(devices),{'TEST::0'})
        actions = physical['TEST::0::Joy_RYAxis']['Binds']['Unmodified']['Controls']
        self.assertEqual(actions['Left']['InputKey'],'Neg_Joy_RYAxis')
        self.assertEqual(actions['Right']['InputKey'],'Pos_Joy_RYAxis')
        self.assertEqual(errors.deviceWarnings,'')
        self.assertNotIn('InputKey',controls['Left'])


if __name__ == '__main__':
    unittest.main()

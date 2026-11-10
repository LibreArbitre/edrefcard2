"""Differences shown on the review page before a draft is published."""
import copy
import unittest

from scripts.mapping_diff import diff_mappings


def base():
    return {'title': 'Stick', 'image': 'stick', 'width': 2200, 'height': 1280, 'device_ids': ['AAAA0001'],
            'boxes': [
                {'label': 'TRIGGER', 'box_xy': [100, 100], 'box_wh': [600, 190], 'button_xy': [900, 400],
                 'rows': [{'symbol': 'stage1', 'number': '1', 'joy': 'Joy_1'},
                          {'symbol': 'stage2', 'number': '2', 'joy': 'Joy_2'}]},
                {'label': 'HAT', 'box_xy': [100, 400], 'box_wh': [600, 190], 'button_xy': [900, 600],
                 'rows': [{'symbol': 'up', 'number': '3', 'joy': 'Joy_3'}]}]}


class DiffTests(unittest.TestCase):
    def test_identical_revisions_have_no_change(self):
        self.assertEqual(diff_mappings(base(), base()), [])

    def test_geometry_rows_and_metadata_changes_are_named(self):
        draft = base()
        draft['title'] = 'Stick v2'
        draft['device_ids'].append('aaaa0002')
        draft['title_xy'] = [900, 80]
        draft['show_title'] = False
        draft['boxes'][0]['box_xy'] = [150, 100]
        draft['boxes'][0]['rows'][1]['joy'] = 'Joy_9'
        draft['boxes'][1]['button_xy'] = None
        changes = ' | '.join(diff_mappings(base(), draft))
        self.assertIn('Title: "Stick" becomes "Stick v2".', changes)
        self.assertIn('Hardware IDs added: AAAA0002.', changes)
        self.assertIn('The title was moved.', changes)
        self.assertIn('The title is now hidden.', changes)
        self.assertIn('Box "TRIGGER": moved, rows added or changed: stage2 2 Joy_9, '
                      'rows removed or replaced: stage2 2 Joy_2.', changes)
        self.assertIn('Box "HAT": anchor point removed.', changes)

    def test_added_and_removed_boxes(self):
        draft = base()
        del draft['boxes'][1]
        draft['boxes'].append({'label': 'POV', 'box_xy': [100, 700], 'box_wh': [600, 190],
                               'button_xy': None, 'rows': [{'joy': 'Joy_POV1Up'}]})
        changes = diff_mappings(base(), draft)
        self.assertIn('Box added: "POV" (Joy_POV1Up).', changes)
        self.assertIn('Box removed: "HAT".', changes)

    def test_renamed_box_is_one_change_not_a_removal_and_an_addition(self):
        draft = base()
        draft['boxes'][1]['label'] = 'HAT TOP'
        self.assertEqual(diff_mappings(base(), draft), ['Box "HAT TOP": renamed from "HAT".'])

    def test_reordered_rows(self):
        draft = base()
        draft['boxes'][0]['rows'].reverse()
        self.assertEqual(diff_mappings(base(), draft), ['Box "TRIGGER": rows reordered.'])

    def test_malformed_revisions_never_raise(self):
        for old, new in ((None, base()), (base(), None), ({}, {'boxes': ['x', None]}),
                         ({'boxes': 'x'}, copy.deepcopy(base()))):
            self.assertIsInstance(diff_mappings(old, new), list)


if __name__ == '__main__':
    unittest.main()

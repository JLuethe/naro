import unittest

from check_native_formats import check


class FixedFormatRule(unittest.TestCase):
    def test_literal_and_adjacent_literals(self):
        result = check('snprintf(dst, sizeof(dst), "item " "%zu", size);')
        self.assertTrue(result['pass'])
        self.assertEqual(result['printf_calls'], 1)

    def test_gettext_annotation_cannot_bypass_literal_rule(self):
        result = check('snprintf(dst, sizeof(dst), gettext("item %zu"), size);')
        self.assertFalse(result['pass'])
        self.assertEqual(len(result['failures']), 1)

    def test_nested_arguments_and_external_format(self):
        result = check('fprintf(get_stream(a, b), catalog, size);')
        self.assertFalse(result['pass'])

    def test_comments_and_string_contents_are_not_calls(self):
        result = check('// printf(catalog);\n/* sprintf(dst, catalog); */\n'
                       'const char *text = "fprintf(stderr, catalog)";')
        self.assertTrue(result['pass'])
        self.assertEqual(result['printf_calls'], 0)

    def test_incomplete_call_fails_closed(self):
        self.assertFalse(check('printf(')['pass'])


if __name__ == '__main__':
    unittest.main()

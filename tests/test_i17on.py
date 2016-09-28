import unittest
from i17on import translator

class TranslatorTest(unittest.TestCase):

    debug_original = None

    def setUp(self):
        self.t = translator.Translator()
        self.debug_original = translator.debug_all
        translator.debug_all = True
        self.maxDiff = None

    def tearDown(self):
        translator.debug_all = self.debug_original

    def assertCondition(self, conditions, expected):
        if type(conditions) == str:
            conditions = self.t.compile_condition(conditions)
        if type(conditions) != list:
            conditions = [conditions]
        result = self.t.check_conditions(*conditions)
        self.assertEqual(expected, result)

    def assertExpandedNode(self, node, state, expected):
        self.t._include_tags = state
        result = self.t.expand_node(node)
        self.assertEqual(expected, result)

    def assertTranslation(self, text, tags, expected):
        self.t._include_tags = tags
        result = self.t.translate(text)
        self.assertEqual(expected, result)

    def test_brace_matching(self):
        text = "foo {subfoo {subsubfoo { subsubsubfoo }}} bar {subfoo}"
        start, end = self.t.outer_braces(text)
        self.assertEqual(start, 4)
        self.assertEqual(end, 40)

    def test_custom_brace_matching(self):
        text = "foo [subfoo [subsubfoo [ subsubsubfoo ]]] bar [subfoo]"
        start, end = self.t.outer_braces(text, '[', ']')
        self.assertEqual(start, 4)
        self.assertEqual(end, 40)

    def test_mismatched_brace_matching(self):
        text = "foo {subfoo {subsubfoo { subsubsubfoo }}"
        with self.assertRaises(translator.UnbalancedBraces):
            self.t.outer_braces(text)
        with self.assertRaises(translator.UnbalancedBraces):
            self.t.outer_braces('{ foo')
        with self.assertRaises(translator.UnbalancedBraces):
            self.t.outer_braces('foo }')

    def test_true_condition(self):
        self.assertCondition(True, True)

    def test_not_condition(self):
        self.assertCondition('!foo', True)

    def test_met_condition(self):
        self.t.add_tag('foo')
        self.assertCondition('foo', True)

    def test_unmet_not_condition(self):
        self.t.add_tag('foo')
        self.assertCondition('!foo', False)

    def test_met_compound_condition(self):
        self.t.add_tag('foo', 'bar')
        self.assertCondition('foo,bar', True)

    def test_unmet_compound_condition(self):
        self.t.add_tag('foo')
        self.assertCondition('foo,bar', False)

    def test_met_compound_not_condition(self):
        self.t.add_tag('foo')
        self.assertCondition('foo,!bar', True)

    def test_unmet_compound_not_condition(self):
        self.t.add_tag('foo', 'bizz')
        self.assertCondition('foo,!bizz', False)
        self.assertCondition('!foo,bizz', False)

    def test_multiple_conditions_fallback(self):
        self.t.add_tag('bizz')
        self.assertCondition('foo;bizz', True)

    def test_multiple_conditions_fallback_to_not(self):
        self.assertCondition('foo;!bizz', True)

    def test_multiple_conditions_all_unmet(self):
        self.assertCondition('foo;bizz', False)

    def test_multiple_conditions_compound(self):
        self.t.add_tag('foo', 'bizz')
        self.assertCondition('foo,!bizz;!foo,bizz', False)
        self.assertCondition('!foo,bizz;foo,bizz', True)

    def test_simple_compile(self):
        blocks = self.t.get_blocks('{!bar:not bar|-bar}')
        expected = [
            ('BRANCH', [
                ('WHEN', [['!bar']], [
                    ('TEXT', 'not bar')
                ]),
                ('WHEN', True, [
                    ('TEXT', 'bar')
                ])
            ])
        ]
        self.assertEqual(blocks, expected)

    def test_compile_leading(self):
        blocks = self.t.get_blocks('leading {!bar:not bar|-bar}')
        expected = [
            ('TEXT', 'leading'),
            ('BRANCH', [
                ('WHEN', [['!bar']], [
                    ('TEXT', 'not bar')
                ]),
                ('WHEN', True, [
                    ('TEXT', 'bar')
                ])
            ])
        ]
        self.assertEqual(blocks, expected)

    def test_compile_trailing(self):
        blocks = self.t.get_blocks('{!bar:not bar|-bar}, trailing')
        expected = [
            ('BRANCH', [
                ('WHEN', [['!bar']], [
                    ('TEXT', 'not bar')
                ]),
                ('WHEN', True, [
                    ('TEXT', 'bar')
                ])
            ]),
            ('TEXT', ', trailing')
        ]
        self.assertEqual(blocks, expected)

    def test_compile_compound(self):
        blocks = self.t.get_blocks('{bar;foo,bar:not bar|-bar}, trailing')
        expected = [
            ('BRANCH', [
                ('WHEN', [['bar'], ['foo', 'bar']], [
                    ('TEXT', 'not bar')
                ]),
                ('WHEN', True, [
                    ('TEXT', 'bar')
                ])
            ]),
            ('TEXT', ', trailing')
        ]
        self.assertEqual(blocks, expected)

    def test_normalize_block_whitespace(self):
        cases = [
            (
                "\n\nWhitespace leading\nthen some other lines\nbut these get merged.\n\n",
                "\n\nWhitespace leading then some other lines but these get merged.\n\n"
            ),
            (
                "\nThis is just one newline though so don't do anything, just strip it.     ",
                "This is just one newline though so don't do anything, just strip it."
            ),
            (
                "\n\t\tThis is an indented block of text\n\t\tbut it's all stripped.\n\n",
                "This is an indented block of text but it's all stripped.\n\n"
            ),
            (
                "\n\t\tThis is an indented block of text.\n\t\t\n\t\tThis is another block.\n\n",
                "This is an indented block of text.\n\nThis is another block.\n\n"
            ),
            (
                "\nThis has leading and trailing line breaks but we remove them.\n",
                "This has leading and trailing line breaks but we remove them."
            ),
            (
                "This has tabs in it\n\n\t\t\tbut tabs get squashed.",
                "This has tabs in it\n\nbut tabs get squashed."
            ),
            (
                """
                Newline this way, too.
                """,
                "Newline this way, too."
            ),
            (
                "\n\n\n\n\n",
                ""
            )
        ]
        for text, expected in cases:
            result = self.t.squash_whitespace(text)
            self.assertEqual(expected, result)

    def test_compile_squash_whitespace(self):
        text = """
        {bizz:Bizz
        |-
            {foo:(P3)But this is part of the previous paragraph.}
        }
        """
        expected = [
            ('BRANCH',
                [('WHEN', [['bizz']], [
                    ('TEXT', 'Bizz')]),
                    ('WHEN', True, [
                        ('BRANCH',
                            [('WHEN', [['foo']], [
                                ('TEXT', '(P3)But this is part of the previous paragraph.')
                            ])]
                        )
                    ])
                ]
            )
        ]
        blocks = self.t.get_blocks(text)
        self.assertEqual(expected, blocks)

    def test_compile_leading_and_trailing(self):
        blocks = self.t.get_blocks('leading {!bar:not bar|-bar}, trailing')
        expected = [
            ('TEXT', 'leading'),
            ('BRANCH', [
                ('WHEN', [['!bar']], [
                    ('TEXT', 'not bar')
                ]),
                ('WHEN', True, [
                    ('TEXT', 'bar')
                ])
            ]),
            ('TEXT', ', trailing')
        ]
        self.assertEqual(blocks, expected)

    def test_compile_multiple_branches(self):
        blocks = self.t.get_blocks('leading {!bar:not bar|-bar}, trailing {foo:bar}')
        expected = [
            ('TEXT', 'leading'),
            ('BRANCH', [
                ('WHEN', [['!bar']], [
                    ('TEXT', 'not bar')
                ]),
                ('WHEN', True, [
                    ('TEXT', 'bar')
                ])
            ]),
            ('TEXT', ', trailing'),
            ('BRANCH', [
                ('WHEN', [['foo']], [
                    ('TEXT', 'bar')
                ])
            ])
        ]
        self.assertEqual(blocks, expected)

    def test_compile_clauses_multiline(self):
        text = """
        {
            foo:Hello,
                this is a nested clause.
                It has a colon: because why not?  And a semicolon; because those are cool, too.
            |-bar:
                It's formatted oddly for some reason, but should still work.

                It's got a colon: because colons are cool.
            |-
                This clause's condition is always True.

                There's a colon here: because colons should be allowed in text.
        }"""
        result = self.t.get_blocks(text)
        expected = [
            ('BRANCH', [
                ('WHEN', [['foo']], [
                    ('TEXT', 'Hello, this is a nested clause. It has a colon: because why not?  And a semicolon; because those are cool, too.')
                ]),
                ('WHEN', [['bar']], [
                    ('TEXT', "It's formatted oddly for some reason, but should still work.\n\nIt's got a colon: because colons are cool.")
                ]),
                ('WHEN', True, [('TEXT', "This clause's condition is always True.\n\nThere's a colon here: because colons should be allowed in text.")])
            ])
        ]
        self.assertEqual(expected, result)

    def test_compile_filter(self):
        text = "{@list:{foo:foo|-bar:bar|-bizz:bizz|-bazz}}"
        blocks = self.t.get_blocks(text)
        node = [('FILTER', 'list', [], ('BRANCH', [
            ('WHEN', [['foo']], [('TEXT', 'foo')]),
            ('WHEN', [['bar']], [('TEXT', 'bar')]),
            ('WHEN', [['bizz']],[('TEXT', 'bizz')]),
            ('WHEN', True, [('TEXT', 'bazz')]),
        ]))]
        self.assertEqual(blocks, node)

    def test_expand_brach_simple(self):
        branch = ('BRANCH', [
            ('WHEN', [['!bar']], [
                ('TEXT', 'not bar')
            ]),
            ('WHEN', True, [
                ('TEXT', 'bar')
            ])
        ])
        self.assertExpandedNode(
            branch,
            [],
            "not bar"
        )
        self.assertExpandedNode(
            branch,
            ['bar'],
            "bar"
        )

    def test_expand_list_filter(self):
        node = ('FILTER', 'list', [], ('BRANCH', [
            ('WHEN', [['foo']], [('TEXT', 'foo')]),
            ('WHEN', [['bar']], [('TEXT', 'bar')]),
            ('WHEN', [['bizz']],[('TEXT', 'bizz')]),
            ('WHEN', True, [('TEXT', 'bazz')]),
        ]))
        self.assertExpandedNode(
            node,
            [],
            "bazz"
        )
        self.assertExpandedNode(
            node,
            ['foo', 'bar'],
            "foo, bar, and bazz"
        )
        self.assertExpandedNode(
            node,
            ['foo', 'bar', 'bizz'],
            "foo, bar, bizz, and bazz"
        )
        self.assertExpandedNode(
            node,
            ['bar'],
            "bar and bazz"
        )

    def test_translate_simple(self):
        text = "leading {foo:foo|-default}, {!bar:not bar|-bar} trailing"
        self.assertTranslation(
            text,
            ['foo'],
            'leading foo, not bar trailing'
        )
        self.assertTranslation(
            text,
            [],
            'leading default, not bar trailing'
        )
        self.assertTranslation(
            text,
            ['bar'],
            'leading default, bar trailing'
        )

    def test_translate_compound(self):
        text = "leading {foo,bar:foobar|-default}, {!bar,foo:foo not bar|-bar} trailing"
        self.assertTranslation(
            text,
            ['foo', 'bar'],
            'leading foobar, bar trailing'
        )
        self.assertTranslation(
            text,
            ['foo'],
            'leading default, foo not bar trailing'
        )

    def test_translate_compound_or(self):
        text = "leading {foo;bar:foo or bar|-default}, {!bizz,buzz:not bizz buzz|-default} trailing"
        self.assertTranslation(
            text,
            [],
            'leading default, default trailing'
        )
        self.assertTranslation(
            text,
            ['foo', 'buzz'],
            'leading foo or bar, not bizz buzz trailing'
        )
        self.assertTranslation(
            text,
            ['bar'],
            'leading foo or bar, default trailing'
        )
        self.assertTranslation(
            text,
            ['buzz'],
            'leading default, not bizz buzz trailing'
        )
        self.assertTranslation(
            text,
            ['bizz', 'buzz'],
            'leading default, default trailing'
        )

    def test_translate_compound_or_and(self):
        text = "leading {foo;bar:foo or bar|-foo,bar:foo and bar|-default}, {!bizz,buzz:not bizz buzz|-default} trailing"
        self.assertTranslation(
            text,
            ['foo', 'buzz'],
            'leading foo or bar, not bizz buzz trailing'
        )
        self.assertTranslation(
            text,
            ['foo', 'buzz'],
            'leading foo or bar, not bizz buzz trailing'
        )
        self.assertTranslation(
            text,
            ['foo', 'bar'],
            'leading foo or bar, default trailing'
        )

    def test_translate_nested_branches(self):
        text = "{foo:foo, {bar:and bar|-but not bar}|-default}"
        self.assertTranslation(
            text,
            [],
            'default'
        )
        self.assertTranslation(
            text,
            ['foo'],
            'foo, but not bar'
        )
        self.assertTranslation(
            text,
            ['foo', 'bar'],
            'foo, and bar'
        )

    def test_various_markdown_spacing_cases(self):
        text = """*Hello* {foo:Foo|-world}"""
        self.assertTranslation(text, [], '*Hello* world')
        text = '# *Heading* and then\n{\n\nfoo:some stuff\n|-\nother stuff\n}.'
        self.assertTranslation(text, [], "# *Heading* and then other stuff.")
        text = '# *Heading* and then\n{\n\nfoo:some stuff}\nother stuff\n.'
        self.assertTranslation(text, [], "# *Heading* and then other stuff.")
        text = '# *Heading* and then\n{\n\nfoo:\n\t\tsome stuff}\nother stuff.'
        self.assertTranslation(text, [], "# *Heading* and then other stuff.")
        text = 'hi\n*{foo:hello|-world}*\n{foo:how are you}'
        return  # TODO
        # We're just... not going to deal with these cases right now.
        # How the hell is Markdown even a thing that exists?
        self.assertTranslation(text, ['foo'], "hi *hello* how are you")
        text = 'hi\n_{foo:hello|-world}_\n{foo:how are you}'
        self.assertTranslation(text, ['foo'], "hi _hello_ how are you")

    def test_big_complicated_translation(self):
        text = """
        Some leading text.

        {
            bar;foo,!bar:
                (P1)Hello this is some text, it's got some trailing space and
                it indents to its base indent level when a new line is found.
                but it also has multiple paragraphs, so double linebreaks should
                be preserved.

                (P2)This is a second paragraph.
                {
                    foo:
                        (P2)This is a nested branch, same rules.  This will show
                        up as part of the previous paragraph.
                }
            |-
                This is the default with no conditions.

                    It's got internal tabs but we just ignore them.

                    TODO: explicit syntax for code embeds!
        }

        Some trailing text.
        """
        self.assertTranslation(
            text,
            [],
            'Some leading text.\n\n'
            'This is the default with no conditions.\n\n'
            "It's got internal tabs but we just ignore them.\n\n"
            'TODO: explicit syntax for code embeds!\n\n'
            'Some trailing text.'
        )
        self.assertTranslation(
            text,
            ['foo'],
            "Some leading text.\n\n"
            "(P1)Hello this is some text, it's got some trailing space "
            "and it indents to its base indent level when a new line is "
            "found. but it also has multiple paragraphs, so double "
            "linebreaks should be preserved.\n\n"
            "(P2)This is a second paragraph. (P2)This is a nested branch, "
            "same rules.  This will show up as part of the previous paragraph.\n\n"
            "Some trailing text."
        )

    def test_get_tags(self):
        text = "{foo:{bar:{!bizz:buzz{bazz:hello}}}}"
        return  # TODO
        result = self.t.get_tags(text)
        self.assertEqual(sorted(result), ['bar', 'bazz', 'bizz', 'foo'])

    def test_translate_list_filter(self):
        text = "{@list:[foo:foo|-bar:bar|-bizz:bizz|-bazz]}"
        self.assertTranslation(
            text,
            [],
            'bazz'
        )
        self.assertTranslation(
            text,
            ['foo'],
            'foo and bazz'
        )
        self.assertTranslation(
            text,
            ['foo', 'bar'],
            'foo, bar, and bazz'
        )

    def test_join_filter(self):
        text = "{@join(/):{foo:foo|-bar:bar|-bizz:bizz|-bazz}}"
        self.assertTranslation(
            text,
            [],
            'bazz'
        )
        self.assertTranslation(
            text,
            ['foo'],
            'foo/bazz'
        )
        self.assertTranslation(
            text,
            ['foo', 'bar'],
            'foo/bar/bazz'
        )

import unittest

from r2d20.utils.dice.notation.parsing import NOTATION_PATTERN, DiceNotationParser, ParsedDice


class TestDiceNotationParser(unittest.TestCase):

    def test_parse(self):
        test_cases = [
            ("d20", [ParsedDice(notation="d20", dice_type=20)]),
            ("3d6", [ParsedDice(notation="3d6", num_dice=3, dice_type=6)]),
            ("d20@adv", [ParsedDice(notation="d20@adv",
                                    dice_type=20, advantage="@adv")]),
            ("d8+d4", [ParsedDice(notation="d8+", dice_type=8, more="+"),
                       ParsedDice(notation="d4", dice_type=4)]),
            ("2d20kl1min5+2- 4d4d2+6+ 8d8+9",
             [ParsedDice(notation="2d20kl1min5+2-", num_dice=2, dice_type=20,
                         keep_drop="k", high_low="l", kd_num_dice=1, min_max="min",
                         m_score=5, modifier="+2", more="-"),
              ParsedDice(notation="4d4d2+6+", num_dice=4, dice_type=4,
                         keep_drop="d", kd_num_dice=2, modifier="+6", more="+"),
              ParsedDice(notation="8d8+9", num_dice=8, dice_type=8, modifier="+9")])
        ]
        for full_notation, expected in test_cases:
            with self.subTest(value=full_notation):
                parser = DiceNotationParser(notation=full_notation)
                parser._parse()
                self.assertListEqual(parser.parsed, expected)

    def test_parseFails(self):
        test_cases = [
            "1",
            "3d",
            "d20@add",
            "4d6k",
            "d2d20kl1",
            "2d20kl",
            "4d8min"
        ]
        for case in test_cases:
            with self.subTest(value=case):
                with self.assertRaises(Exception):
                    parser = DiceNotationParser(notation=case)
                    parser._parse()


class TestNotationPattern(unittest.TestCase):

    def test_matches_notation(self):
        test_cases = [
            "d20",
            "3d6",
            "d20@adv",
            "4d6k3",
            "2d20kl1",
            "4d8min5+10",
        ]
        for case in test_cases:
            with self.subTest(value=case):
                self.assertRegex(case, NOTATION_PATTERN+"$",
                                 f"'{case}' should match notation pattern")

    def test_not_match_notation(self):
        test_cases = [
            "1",
            "3d",
            "d20@add",
            "4d6k",
            "d2d20kl1",
            "2d20kl",
            "4d8min"
        ]
        for case in test_cases:
            with self.subTest(value=case):
                self.assertNotRegex(case, NOTATION_PATTERN+"$",
                                    f"{case} should not match notation pattern")


if __name__ == '__main__':
    unittest.main()

import unittest

from utils.dice.parsing import NOTATION_PATTERN, DiceNotationParser, ParsedDice


class TestDiceNotationParser(unittest.TestCase):

    def test_parse(self):
        notation = "d20"
        parser = DiceNotationParser(notation=notation)
        parser._parse()
        expected_parsed = [ParsedDice(notation=notation,
                                      dice_type=20)]
        self.assertListEqual(parser._parsed, expected_parsed)


class TestNotationPattern(unittest.TestCase):

    def test_matches_notation(self):
        test_cases = [
            "d20",
            "3d6",
            "d20@adv",
            "4d6k3",
            "2d20kl1",
            "4d8min5+10"
        ]
        for text in test_cases:
            with self.subTest(value=text):
                self.assertRegex(text, NOTATION_PATTERN+"$",
                                 f"'{text}' should match notation pattern")

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
        for text in test_cases:
            with self.subTest(value=text):
                self.assertNotRegex(text, NOTATION_PATTERN+"$",
                                    f"{text} should not match notation pattern")


if __name__ == '__main__':
    unittest.main()

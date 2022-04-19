LOW_WORDS = ['zero','one','two','three','four',
             'five','six','seven','eight','nine',
             'ten','eleven','twelve','thirteen','fourteen',
             'fifteen','sixteen','seventeen','eighteen','nineteen']
TENS_WORDS = ['twenty','thirty','fourty','fifty',
              'sixty','seventy','eighty','ninety']

def num2words(num, plural=False):
    '''Currently only works for 2-digit numbers because that's all I need :)
    '''
    num_as_str = f'{num:02d}'
    tens, units = [int(digit) for digit in num_as_str]
    if tens < 2:
        unit_word = str(LOW_WORDS[num])
        tens_word = ''
    else:
        unit_word = str(LOW_WORDS[units])
        tens_word = str(TENS_WORDS[tens-2])
    #
    if plural:
        if units == 6 and tens != 1:
            unit_word = 'sixes'
        else:
            unit_word += 's'
        #
    #
    return f'{tens_word} {unit_word}'

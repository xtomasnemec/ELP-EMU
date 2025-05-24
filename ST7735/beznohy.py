# 5x8 font, znak "o" (ASCII 111) jako piktogram vozíčkáře + mezera (ASCII 32)
beznohy_pikto = {
    "Width": 5,
    "Height": 8,
    "Start": 32,
    "End": 111,
    "Data": bytearray(
        [0x00] * 5 * (111 - 32) + [
            0x38,  # sloupec 1 převrácený
            0xC8,  # sloupec 2 převrácený
            0x9F,  # sloupec 3 převrácený
            0xEB,  # sloupec 4 převrácený
            0x48,  # sloupec 5 převrácený
        ]
    )
}

# 5x8 font, znak "~" (ASCII 126) nahrazen symbolem "±", převráceně jako vozík
plusminus_font = {
    "Width": 5,
    "Height": 8,
    "Start": 32,
    "End": 126,
    "Data": bytearray(
        [0x00] * 5 * (126 - 32) + [  # vyplnění ostatních znaků nulami
            0x20,  # sloupec 1
            0x24,  # sloupec 2
            0x2E,  # sloupec 3
            0x24,  # sloupec 4
            0x20,  # sloupec 5
        ]
    )
}
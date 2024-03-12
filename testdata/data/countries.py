# -*- coding: utf-8 -*-

# This dict was assembled on 3-11-2024 using:
#
# https://en.wikipedia.org/wiki/List_of_ISO_3166_country_codes
#
# as the source and then cleaned up a bit by hand, which took way longer than
# it should have, it would've been better to flesh out my script a bit more

# these will be populated at the bottom of this module using the uppercase
# values

country_lookup = {}
"""Holds all the country info in a lookup table"""

country_tlds = set()
"""Holds just the country tlds"""


COUNTRIES_INFO = {
    "Afghanistan": {
        "name": "Afghanistan",
        "code": "AF",
        "code-alpha-3": "AFG",
        "tld": [
            ".af"
        ]
    },
    "Aland Islands": {
        "name": "Åland Islands",
        "code": "AX",
        "code-alpha-3": "ALA",
        "tld": [
            ".ax"
        ],
        "aliases": [
            "Åland Islands"
        ]
    },
    "Albania": {
        "name": "Albania",
        "code": "AL",
        "code-alpha-3": "ALB",
        "tld": [
            ".al"
        ]
    },
    "Algeria": {
        "name": "Algeria",
        "code": "DZ",
        "code-alpha-3": "DZA",
        "tld": [
            ".dz"
        ]
    },
    "American Samoa": {
        "name": "American Samoa",
        "code": "AS",
        "code-alpha-3": "ASM",
        "tld": [
            ".as"
        ]
    },
    "Andorra": {
        "name": "Andorra",
        "code": "AD",
        "code-alpha-3": "AND",
        "tld": [
            ".ad"
        ]
    },
    "Angola": {
        "name": "Angola",
        "code": "AO",
        "code-alpha-3": "AGO",
        "tld": [
            ".ao"
        ]
    },
    "Anguilla": {
        "name": "Anguilla",
        "code": "AI",
        "code-alpha-3": "AIA",
        "tld": [
            ".ai"
        ]
    },
    "Antarctica ": {
        "name": "Antarctica ",
        "code": "AQ",
        "code-alpha-3": "ATA",
        "tld": [
            ".aq"
        ]
    },
    "Antigua and Barbuda": {
        "name": "Antigua and Barbuda",
        "code": "AG",
        "code-alpha-3": "ATG",
        "tld": [
            ".ag"
        ]
    },
    "Argentina": {
        "name": "Argentina",
        "code": "AR",
        "code-alpha-3": "ARG",
        "tld": [
            ".ar"
        ]
    },
    "Armenia": {
        "name": "Armenia",
        "code": "AM",
        "code-alpha-3": "ARM",
        "tld": [
            ".am"
        ]
    },
    "Aruba": {
        "name": "Aruba",
        "code": "AW",
        "code-alpha-3": "ABW",
        "tld": [
            ".aw"
        ]
    },
    "Australia ": {
        "name": "Australia ",
        "code": "AU",
        "code-alpha-3": "AUS",
        "tld": [
            ".au"
        ]
    },
    "Austria": {
        "name": "Austria",
        "code": "AT",
        "code-alpha-3": "AUT",
        "tld": [
            ".at"
        ]
    },
    "Azerbaijan": {
        "name": "Azerbaijan",
        "code": "AZ",
        "code-alpha-3": "AZE",
        "tld": [
            ".az"
        ]
    },
    "Bahamas (the)": {
        "name": "Bahamas (the)",
        "code": "BS",
        "code-alpha-3": "BHS",
        "tld": [
            ".bs"
        ]
    },
    "Bahrain": {
        "name": "Bahrain",
        "code": "BH",
        "code-alpha-3": "BHR",
        "tld": [
            ".bh"
        ]
    },
    "Bangladesh": {
        "name": "Bangladesh",
        "code": "BD",
        "code-alpha-3": "BGD",
        "tld": [
            ".bd"
        ]
    },
    "Barbados": {
        "name": "Barbados",
        "code": "BB",
        "code-alpha-3": "BRB",
        "tld": [
            ".bb"
        ]
    },
    "Belarus": {
        "name": "Belarus",
        "code": "BY",
        "code-alpha-3": "BLR",
        "tld": [
            ".by"
        ]
    },
    "Belgium": {
        "name": "Belgium",
        "code": "BE",
        "code-alpha-3": "BEL",
        "tld": [
            ".be"
        ]
    },
    "Belize": {
        "name": "Belize",
        "code": "BZ",
        "code-alpha-3": "BLZ",
        "tld": [
            ".bz"
        ]
    },
    "Benin": {
        "name": "Benin",
        "code": "BJ",
        "code-alpha-3": "BEN",
        "tld": [
            ".bj"
        ]
    },
    "Bermuda": {
        "name": "Bermuda",
        "code": "BM",
        "code-alpha-3": "BMU",
        "tld": [
            ".bm"
        ]
    },
    "Bhutan": {
        "name": "Bhutan",
        "code": "BT",
        "code-alpha-3": "BTN",
        "tld": [
            ".bt"
        ]
    },
    "Bolivia": {
        "name": "Bolivia (Plurinational State of)",
        "code": "BO",
        "code-alpha-3": "BOL",
        "tld": [
            ".bo"
        ]
    },
    "Bonaire": {
        "name": "Bonaire",
        "code": "BQ",
        "code-alpha-3": "BES",
        "tld": [
            ".bq",
            ".nl"
        ],
        "aliases": [
            "Sint Eustatius",
            "Saba",
            "Caribbean Netherlands",
        ]
    },
    "Bosnia and Herzegovina": {
        "name": "Bosnia and Herzegovina",
        "code": "BA",
        "code-alpha-3": "BIH",
        "tld": [
            ".ba"
        ]
    },
    "Botswana": {
        "name": "Botswana",
        "code": "BW",
        "code-alpha-3": "BWA",
        "tld": [
            ".bw"
        ]
    },
    "Bouvet Island": {
        "name": "Bouvet Island",
        "code": "BV",
        "code-alpha-3": "BVT",
        "tld": [
            "[e]"
        ]
    },
    "Brazil": {
        "name": "Brazil",
        "code": "BR",
        "code-alpha-3": "BRA",
        "tld": [
            ".br"
        ]
    },
    "The British Indian Ocean Territory": {
        "name": "British Indian Ocean Territory (the)",
        "code": "IO",
        "code-alpha-3": "IOT",
        "tld": [
            ".io"
        ]
    },
    "British Virgin Islands": {
        "name": "British Virgin Islands – See Virgin Islands (British).",
        "code": "",
        "code-alpha-3": "",
        "tld": []
    },
    "Brunei Darussalam": {
        "name": "Brunei Darussalam",
        "code": "BN",
        "code-alpha-3": "BRN",
        "tld": [
            ".bn"
        ]
    },
    "Bulgaria": {
        "name": "Bulgaria",
        "code": "BG",
        "code-alpha-3": "BGR",
        "tld": [
            ".bg"
        ]
    },
    "Burkina Faso": {
        "name": "Burkina Faso",
        "code": "BF",
        "code-alpha-3": "BFA",
        "tld": [
            ".bf"
        ]
    },
    "Burundi": {
        "name": "Burundi",
        "code": "BI",
        "code-alpha-3": "BDI",
        "tld": [
            ".bi"
        ]
    },
    "Cabo Verde": {
        "name": "Cabo Verde ",
        "code": "CV",
        "code-alpha-3": "CPV",
        "tld": [
            ".cv"
        ],
        "aliases": [
            "Cape Verde"
        ]
    },
    "Cambodia": {
        "name": "Cambodia",
        "code": "KH",
        "code-alpha-3": "KHM",
        "tld": [
            ".kh"
        ]
    },
    "Cameroon": {
        "name": "Cameroon",
        "code": "CM",
        "code-alpha-3": "CMR",
        "tld": [
            ".cm"
        ]
    },
    "Canada": {
        "name": "Canada",
        "code": "CA",
        "code-alpha-3": "CAN",
        "tld": [
            ".ca"
        ]
    },
    "The Cayman Islands": {
        "name": "Cayman Islands (the)",
        "code": "KY",
        "code-alpha-3": "CYM",
        "tld": [
            ".ky"
        ]
    },
    "The Central African Republic": {
        "name": "Central African Republic (the)",
        "code": "CF",
        "code-alpha-3": "CAF",
        "tld": [
            ".cf"
        ]
    },
    "Chad": {
        "name": "Chad",
        "code": "TD",
        "code-alpha-3": "TCD",
        "tld": [
            ".td"
        ]
    },
    "Chile": {
        "name": "Chile",
        "code": "CL",
        "code-alpha-3": "CHL",
        "tld": [
            ".cl"
        ]
    },
    "China": {
        "name": "China",
        "code": "CN",
        "code-alpha-3": "CHN",
        "tld": [
            ".cn"
        ],
        "aliases": [
            "People's Republic of China",
        ]
    },
    "Christmas Island": {
        "name": "Christmas Island",
        "code": "CX",
        "code-alpha-3": "CXR",
        "tld": [
            ".cx"
        ]
    },
    "Cocos Islands": {
        "name": "Cocos (Keeling) Islands (the)",
        "code": "CC",
        "code-alpha-3": "CCK",
        "tld": [
            ".cc"
        ],
        "aliases": [
            "The Keeling Islands"
        ]
    },
    "Colombia": {
        "name": "Colombia",
        "code": "CO",
        "code-alpha-3": "COL",
        "tld": [
            ".co"
        ]
    },
    "Comoros": {
        "name": "Comoros (the)",
        "code": "KM",
        "code-alpha-3": "COM",
        "tld": [
            ".km"
        ]
    },
    "Democratic Republic of the Congo": {
        "name": "Congo (the Democratic Republic of the)",
        "code": "CD",
        "code-alpha-3": "COD",
        "tld": [
            ".cd"
        ],
        "aliases": [
            "Republic of the Congo",
        ]
    },
    "Congo": {
        "name": "Congo (the) ",
        "code": "CG",
        "code-alpha-3": "COG",
        "tld": [
            ".cg"
        ]
    },
    "Cook Islands": {
        "name": "Cook Islands (the)",
        "code": "CK",
        "code-alpha-3": "COK",
        "tld": [
            ".ck"
        ]
    },
    "Costa Rica": {
        "name": "Costa Rica",
        "code": "CR",
        "code-alpha-3": "CRI",
        "tld": [
            ".cr"
        ]
    },
    "Ivory Coast": {
        "name": "Côte d'Ivoire",
        "code": "CI",
        "code-alpha-3": "CIV",
        "tld": [
            ".ci"
        ],
        "aliases": [
            "Côte d'Ivoire"
        ]
    },
    "Croatia": {
        "name": "Croatia",
        "code": "HR",
        "code-alpha-3": "HRV",
        "tld": [
            ".hr"
        ]
    },
    "Cuba": {
        "name": "Cuba",
        "code": "CU",
        "code-alpha-3": "CUB",
        "tld": [
            ".cu"
        ]
    },
    "Curaçao": {
        "name": "Curaçao",
        "code": "CW",
        "code-alpha-3": "CUW",
        "tld": [
            ".cw"
        ]
    },
    "Cyprus": {
        "name": "Cyprus",
        "code": "CY",
        "code-alpha-3": "CYP",
        "tld": [
            ".cy"
        ]
    },
    "Czechia": {
        "name": "Czechia ",
        "code": "CZ",
        "code-alpha-3": "CZE",
        "tld": [
            ".cz"
        ]
    },
    "Denmark": {
        "name": "Denmark",
        "code": "DK",
        "code-alpha-3": "DNK",
        "tld": [
            ".dk"
        ]
    },
    "Djibouti": {
        "name": "Djibouti",
        "code": "DJ",
        "code-alpha-3": "DJI",
        "tld": [
            ".dj"
        ]
    },
    "Dominica": {
        "name": "Dominica",
        "code": "DM",
        "code-alpha-3": "DMA",
        "tld": [
            ".dm"
        ]
    },
    "Dominican Republic": {
        "name": "Dominican Republic (the)",
        "code": "DO",
        "code-alpha-3": "DOM",
        "tld": [
            ".do"
        ]
    },
    "Ecuador": {
        "name": "Ecuador",
        "code": "EC",
        "code-alpha-3": "ECU",
        "tld": [
            ".ec"
        ]
    },
    "Egypt": {
        "name": "Egypt",
        "code": "EG",
        "code-alpha-3": "EGY",
        "tld": [
            ".eg"
        ]
    },
    "El Salvador": {
        "name": "El Salvador",
        "code": "SV",
        "code-alpha-3": "SLV",
        "tld": [
            ".sv"
        ]
    },
    "Equatorial Guinea": {
        "name": "Equatorial Guinea",
        "code": "GQ",
        "code-alpha-3": "GNQ",
        "tld": [
            ".gq"
        ]
    },
    "Eritrea": {
        "name": "Eritrea",
        "code": "ER",
        "code-alpha-3": "ERI",
        "tld": [
            ".er"
        ]
    },
    "Estonia": {
        "name": "Estonia",
        "code": "EE",
        "code-alpha-3": "EST",
        "tld": [
            ".ee"
        ]
    },
    "Eswatini ": {
        "name": "Eswatini ",
        "code": "SZ",
        "code-alpha-3": "SWZ",
        "tld": [
            ".sz"
        ]
    },
    "Ethiopia": {
        "name": "Ethiopia",
        "code": "ET",
        "code-alpha-3": "ETH",
        "tld": [
            ".et"
        ]
    },
    "Falkland Islands": {
        "name": "Falkland Islands (the) [Malvinas] ",
        "code": "FK",
        "code-alpha-3": "FLK",
        "tld": [
            ".fk"
        ],
        "aliases": [
            "Malvinas",
        ]
    },
    "Faroe Islands": {
        "name": "Faroe Islands (the)",
        "code": "FO",
        "code-alpha-3": "FRO",
        "tld": [
            ".fo"
        ]
    },
    "Fiji": {
        "name": "Fiji",
        "code": "FJ",
        "code-alpha-3": "FJI",
        "tld": [
            ".fj"
        ]
    },
    "Finland": {
        "name": "Finland",
        "code": "FI",
        "code-alpha-3": "FIN",
        "tld": [
            ".fi"
        ]
    },
    "France": {
        "name": "France",
        "code": "FR",
        "code-alpha-3": "FRA",
        "tld": [
            ".fr"
        ]
    },
    "French Guiana": {
        "name": "French Guiana",
        "code": "GF",
        "code-alpha-3": "GUF",
        "tld": [
            ".gf"
        ]
    },
    "French Polynesia": {
        "name": "French Polynesia",
        "code": "PF",
        "code-alpha-3": "PYF",
        "tld": [
            ".pf"
        ]
    },
    "French Southern Territories": {
        "name": "French Southern Territories (the) ",
        "code": "TF",
        "code-alpha-3": "ATF",
        "tld": [
            ".tf"
        ]
    },
    "Gabon": {
        "name": "Gabon",
        "code": "GA",
        "code-alpha-3": "GAB",
        "tld": [
            ".ga"
        ]
    },
    "Gambia": {
        "name": "Gambia (the)",
        "code": "GM",
        "code-alpha-3": "GMB",
        "tld": [
            ".gm"
        ]
    },
    "Georgia": {
        "name": "Georgia",
        "code": "GE",
        "code-alpha-3": "GEO",
        "tld": [
            ".ge"
        ]
    },
    "Germany": {
        "name": "Germany",
        "code": "DE",
        "code-alpha-3": "DEU",
        "tld": [
            ".de"
        ]
    },
    "Ghana": {
        "name": "Ghana",
        "code": "GH",
        "code-alpha-3": "GHA",
        "tld": [
            ".gh"
        ]
    },
    "Gibraltar": {
        "name": "Gibraltar",
        "code": "GI",
        "code-alpha-3": "GIB",
        "tld": [
            ".gi"
        ]
    },
    "Greece": {
        "name": "Greece",
        "code": "GR",
        "code-alpha-3": "GRC",
        "tld": [
            ".gr"
        ]
    },
    "Greenland": {
        "name": "Greenland",
        "code": "GL",
        "code-alpha-3": "GRL",
        "tld": [
            ".gl"
        ]
    },
    "Grenada": {
        "name": "Grenada",
        "code": "GD",
        "code-alpha-3": "GRD",
        "tld": [
            ".gd"
        ]
    },
    "Guadeloupe": {
        "name": "Guadeloupe",
        "code": "GP",
        "code-alpha-3": "GLP",
        "tld": [
            ".gp"
        ]
    },
    "Guam": {
        "name": "Guam",
        "code": "GU",
        "code-alpha-3": "GUM",
        "tld": [
            ".gu"
        ]
    },
    "Guatemala": {
        "name": "Guatemala",
        "code": "GT",
        "code-alpha-3": "GTM",
        "tld": [
            ".gt"
        ]
    },
    "Guernsey": {
        "name": "Guernsey",
        "code": "GG",
        "code-alpha-3": "GGY",
        "tld": [
            ".gg"
        ]
    },
    "Guinea": {
        "name": "Guinea",
        "code": "GN",
        "code-alpha-3": "GIN",
        "tld": [
            ".gn"
        ]
    },
    "Guinea-Bissau": {
        "name": "Guinea-Bissau",
        "code": "GW",
        "code-alpha-3": "GNB",
        "tld": [
            ".gw"
        ]
    },
    "Guyana": {
        "name": "Guyana",
        "code": "GY",
        "code-alpha-3": "GUY",
        "tld": [
            ".gy"
        ]
    },
    "Haiti": {
        "name": "Haiti",
        "code": "HT",
        "code-alpha-3": "HTI",
        "tld": [
            ".ht"
        ]
    },
    "Heard Island and McDonald Islands": {
        "name": "Heard Island and McDonald Islands",
        "code": "HM",
        "code-alpha-3": "HMD",
        "tld": [
            ".hm"
        ]
    },
    "Honduras": {
        "name": "Honduras",
        "code": "HN",
        "code-alpha-3": "HND",
        "tld": [
            ".hn"
        ]
    },
    "Hong Kong": {
        "name": "Hong Kong",
        "code": "HK",
        "code-alpha-3": "HKG",
        "tld": [
            ".hk"
        ]
    },
    "Hungary": {
        "name": "Hungary",
        "code": "HU",
        "code-alpha-3": "HUN",
        "tld": [
            ".hu"
        ]
    },
    "Iceland": {
        "name": "Iceland",
        "code": "IS",
        "code-alpha-3": "ISL",
        "tld": [
            ".is"
        ]
    },
    "India": {
        "name": "India",
        "code": "IN",
        "code-alpha-3": "IND",
        "tld": [
            ".in"
        ]
    },
    "Indonesia": {
        "name": "Indonesia",
        "code": "ID",
        "code-alpha-3": "IDN",
        "tld": [
            ".id"
        ]
    },
    "Iran": {
        "name": "Iran (Islamic Republic of)",
        "code": "IR",
        "code-alpha-3": "IRN",
        "tld": [
            ".ir"
        ]
    },
    "Iraq": {
        "name": "Iraq",
        "code": "IQ",
        "code-alpha-3": "IRQ",
        "tld": [
            ".iq"
        ]
    },
    "Ireland": {
        "name": "Ireland",
        "code": "IE",
        "code-alpha-3": "IRL",
        "tld": [
            ".ie"
        ]
    },
    "Isle of Man": {
        "name": "Isle of Man",
        "code": "IM",
        "code-alpha-3": "IMN",
        "tld": [
            ".im"
        ]
    },
    "Israel": {
        "name": "Israel",
        "code": "IL",
        "code-alpha-3": "ISR",
        "tld": [
            ".il"
        ]
    },
    "Italy": {
        "name": "Italy",
        "code": "IT",
        "code-alpha-3": "ITA",
        "tld": [
            ".it"
        ]
    },
    "Jamaica": {
        "name": "Jamaica",
        "code": "JM",
        "code-alpha-3": "JAM",
        "tld": [
            ".jm"
        ]
    },
    "Japan": {
        "name": "Japan",
        "code": "JP",
        "code-alpha-3": "JPN",
        "tld": [
            ".jp"
        ]
    },
    "Jersey": {
        "name": "Jersey",
        "code": "JE",
        "code-alpha-3": "JEY",
        "tld": [
            ".je"
        ]
    },
    "Jordan": {
        "name": "Jordan",
        "code": "JO",
        "code-alpha-3": "JOR",
        "tld": [
            ".jo"
        ]
    },
    "Kazakhstan": {
        "name": "Kazakhstan",
        "code": "KZ",
        "code-alpha-3": "KAZ",
        "tld": [
            ".kz"
        ]
    },
    "Kenya": {
        "name": "Kenya",
        "code": "KE",
        "code-alpha-3": "KEN",
        "tld": [
            ".ke"
        ]
    },
    "Kiribati": {
        "name": "Kiribati",
        "code": "KI",
        "code-alpha-3": "KIR",
        "tld": [
            ".ki"
        ]
    },
    "North Korea": {
        "name": "Korea (the Democratic People's Republic of) ",
        "code": "KP",
        "code-alpha-3": "PRK",
        "tld": [
            ".kp"
        ],
        "aliases": [
            "the Democratic People's Republic of Korea"
        ]
    },
    "South Korea": {
        "name": "Korea (the Republic of)",
        "code": "KR",
        "code-alpha-3": "KOR",
        "tld": [
            ".kr"
        ],
        "aliases": [
            "South Korea",
            "Republic of Korea",
        ]
    },
    "Kuwait": {
        "name": "Kuwait",
        "code": "KW",
        "code-alpha-3": "KWT",
        "tld": [
            ".kw"
        ]
    },
    "Kyrgyzstan": {
        "name": "Kyrgyzstan",
        "code": "KG",
        "code-alpha-3": "KGZ",
        "tld": [
            ".kg"
        ]
    },
    "Lao People's Democratic Republic": {
        "name": "Lao People's Democratic Republic (the) ",
        "code": "LA",
        "code-alpha-3": "LAO",
        "tld": [
            ".la"
        ]
    },
    "Latvia": {
        "name": "Latvia",
        "code": "LV",
        "code-alpha-3": "LVA",
        "tld": [
            ".lv"
        ]
    },
    "Lebanon": {
        "name": "Lebanon",
        "code": "LB",
        "code-alpha-3": "LBN",
        "tld": [
            ".lb"
        ]
    },
    "Lesotho": {
        "name": "Lesotho",
        "code": "LS",
        "code-alpha-3": "LSO",
        "tld": [
            ".ls"
        ]
    },
    "Liberia": {
        "name": "Liberia",
        "code": "LR",
        "code-alpha-3": "LBR",
        "tld": [
            ".lr"
        ]
    },
    "Libya": {
        "name": "Libya",
        "code": "LY",
        "code-alpha-3": "LBY",
        "tld": [
            ".ly"
        ]
    },
    "Liechtenstein": {
        "name": "Liechtenstein",
        "code": "LI",
        "code-alpha-3": "LIE",
        "tld": [
            ".li"
        ]
    },
    "Lithuania": {
        "name": "Lithuania",
        "code": "LT",
        "code-alpha-3": "LTU",
        "tld": [
            ".lt"
        ]
    },
    "Luxembourg": {
        "name": "Luxembourg",
        "code": "LU",
        "code-alpha-3": "LUX",
        "tld": [
            ".lu"
        ]
    },
    "Macao": {
        "name": "Macao ",
        "code": "MO",
        "code-alpha-3": "MAC",
        "tld": [
            ".mo"
        ]
    },
    "Madagascar": {
        "name": "Madagascar",
        "code": "MG",
        "code-alpha-3": "MDG",
        "tld": [
            ".mg"
        ]
    },
    "Malawi": {
        "name": "Malawi",
        "code": "MW",
        "code-alpha-3": "MWI",
        "tld": [
            ".mw"
        ]
    },
    "Malaysia": {
        "name": "Malaysia",
        "code": "MY",
        "code-alpha-3": "MYS",
        "tld": [
            ".my"
        ]
    },
    "Maldives": {
        "name": "Maldives",
        "code": "MV",
        "code-alpha-3": "MDV",
        "tld": [
            ".mv"
        ]
    },
    "Mali": {
        "name": "Mali",
        "code": "ML",
        "code-alpha-3": "MLI",
        "tld": [
            ".ml"
        ]
    },
    "Malta": {
        "name": "Malta",
        "code": "MT",
        "code-alpha-3": "MLT",
        "tld": [
            ".mt"
        ]
    },
    "Marshall Islands": {
        "name": "Marshall Islands (the)",
        "code": "MH",
        "code-alpha-3": "MHL",
        "tld": [
            ".mh"
        ]
    },
    "Martinique": {
        "name": "Martinique",
        "code": "MQ",
        "code-alpha-3": "MTQ",
        "tld": [
            ".mq"
        ]
    },
    "Mauritania": {
        "name": "Mauritania",
        "code": "MR",
        "code-alpha-3": "MRT",
        "tld": [
            ".mr"
        ]
    },
    "Mauritius": {
        "name": "Mauritius",
        "code": "MU",
        "code-alpha-3": "MUS",
        "tld": [
            ".mu"
        ]
    },
    "Mayotte": {
        "name": "Mayotte",
        "code": "YT",
        "code-alpha-3": "MYT",
        "tld": [
            ".yt"
        ]
    },
    "Mexico": {
        "name": "Mexico",
        "code": "MX",
        "code-alpha-3": "MEX",
        "tld": [
            ".mx"
        ]
    },
    "Micronesia": {
        "name": "Micronesia (Federated States of)",
        "code": "FM",
        "code-alpha-3": "FSM",
        "tld": [
            ".fm"
        ]
    },
    "Moldova": {
        "name": "Moldova (the Republic of)",
        "code": "MD",
        "code-alpha-3": "MDA",
        "tld": [
            ".md"
        ]
    },
    "Monaco": {
        "name": "Monaco",
        "code": "MC",
        "code-alpha-3": "MCO",
        "tld": [
            ".mc"
        ]
    },
    "Mongolia": {
        "name": "Mongolia",
        "code": "MN",
        "code-alpha-3": "MNG",
        "tld": [
            ".mn"
        ]
    },
    "Montenegro": {
        "name": "Montenegro",
        "code": "ME",
        "code-alpha-3": "MNE",
        "tld": [
            ".me"
        ]
    },
    "Montserrat": {
        "name": "Montserrat",
        "code": "MS",
        "code-alpha-3": "MSR",
        "tld": [
            ".ms"
        ]
    },
    "Morocco": {
        "name": "Morocco",
        "code": "MA",
        "code-alpha-3": "MAR",
        "tld": [
            ".ma"
        ]
    },
    "Mozambique": {
        "name": "Mozambique",
        "code": "MZ",
        "code-alpha-3": "MOZ",
        "tld": [
            ".mz"
        ]
    },
    "Myanmar": {
        "name": "Myanmar ",
        "code": "MM",
        "code-alpha-3": "MMR",
        "tld": [
            ".mm"
        ],
        "aliases": [
            "Burma",
        ]
    },
    "Namibia": {
        "name": "Namibia",
        "code": "NA",
        "code-alpha-3": "NAM",
        "tld": [
            ".na"
        ]
    },
    "Nauru": {
        "name": "Nauru",
        "code": "NR",
        "code-alpha-3": "NRU",
        "tld": [
            ".nr"
        ]
    },
    "Nepal": {
        "name": "Nepal",
        "code": "NP",
        "code-alpha-3": "NPL",
        "tld": [
            ".np"
        ]
    },
    "Netherlands, Kingdom of the": {
        "name": "Netherlands, Kingdom of the",
        "code": "NL",
        "code-alpha-3": "NLD",
        "tld": [
            ".nl"
        ]
    },
    "New Caledonia": {
        "name": "New Caledonia",
        "code": "NC",
        "code-alpha-3": "NCL",
        "tld": [
            ".nc"
        ]
    },
    "New Zealand": {
        "name": "New Zealand",
        "code": "NZ",
        "code-alpha-3": "NZL",
        "tld": [
            ".nz"
        ]
    },
    "Nicaragua": {
        "name": "Nicaragua",
        "code": "NI",
        "code-alpha-3": "NIC",
        "tld": [
            ".ni"
        ]
    },
    "Niger (the)": {
        "name": "Niger (the)",
        "code": "NE",
        "code-alpha-3": "NER",
        "tld": [
            ".ne"
        ]
    },
    "Nigeria": {
        "name": "Nigeria",
        "code": "NG",
        "code-alpha-3": "NGA",
        "tld": [
            ".ng"
        ]
    },
    "Niue": {
        "name": "Niue",
        "code": "NU",
        "code-alpha-3": "NIU",
        "tld": [
            ".nu"
        ]
    },
    "Norfolk Island": {
        "name": "Norfolk Island",
        "code": "NF",
        "code-alpha-3": "NFK",
        "tld": [
            ".nf"
        ]
    },
    "North Macedonia ": {
        "name": "North Macedonia ",
        "code": "MK",
        "code-alpha-3": "MKD",
        "tld": [
            ".mk"
        ]
    },
    "Northern Mariana Islands": {
        "name": "Northern Mariana Islands (the)",
        "code": "MP",
        "code-alpha-3": "MNP",
        "tld": [
            ".mp"
        ]
    },
    "Norway": {
        "name": "Norway",
        "code": "NO",
        "code-alpha-3": "NOR",
        "tld": [
            ".no"
        ]
    },
    "Oman": {
        "name": "Oman",
        "code": "OM",
        "code-alpha-3": "OMN",
        "tld": [
            ".om"
        ]
    },
    "Pakistan": {
        "name": "Pakistan",
        "code": "PK",
        "code-alpha-3": "PAK",
        "tld": [
            ".pk"
        ]
    },
    "Palau": {
        "name": "Palau",
        "code": "PW",
        "code-alpha-3": "PLW",
        "tld": [
            ".pw"
        ]
    },
    "Palestine": {
        "name": "Palestine, State of",
        "code": "PS",
        "code-alpha-3": "PSE",
        "tld": [
            ".ps"
        ]
    },
    "Panama": {
        "name": "Panama",
        "code": "PA",
        "code-alpha-3": "PAN",
        "tld": [
            ".pa"
        ]
    },
    "Papua New Guinea": {
        "name": "Papua New Guinea",
        "code": "PG",
        "code-alpha-3": "PNG",
        "tld": [
            ".pg"
        ]
    },
    "Paraguay": {
        "name": "Paraguay",
        "code": "PY",
        "code-alpha-3": "PRY",
        "tld": [
            ".py"
        ]
    },
    "Peru": {
        "name": "Peru",
        "code": "PE",
        "code-alpha-3": "PER",
        "tld": [
            ".pe"
        ]
    },
    "Philippines": {
        "name": "Philippines (the)",
        "code": "PH",
        "code-alpha-3": "PHL",
        "tld": [
            ".ph"
        ]
    },
    "Pitcairn": {
        "name": "Pitcairn ",
        "code": "PN",
        "code-alpha-3": "PCN",
        "tld": [
            ".pn"
        ]
    },
    "Poland": {
        "name": "Poland",
        "code": "PL",
        "code-alpha-3": "POL",
        "tld": [
            ".pl"
        ]
    },
    "Portugal": {
        "name": "Portugal",
        "code": "PT",
        "code-alpha-3": "PRT",
        "tld": [
            ".pt"
        ]
    },
    "Puerto Rico": {
        "name": "Puerto Rico",
        "code": "PR",
        "code-alpha-3": "PRI",
        "tld": [
            ".pr"
        ]
    },
    "Qatar": {
        "name": "Qatar",
        "code": "QA",
        "code-alpha-3": "QAT",
        "tld": [
            ".qa"
        ]
    },
    "Réunion": {
        "name": "Réunion",
        "code": "RE",
        "code-alpha-3": "REU",
        "tld": [
            ".re"
        ]
    },
    "Romania": {
        "name": "Romania",
        "code": "RO",
        "code-alpha-3": "ROU",
        "tld": [
            ".ro"
        ]
    },
    "Russia": {
        "name": "Russian Federation (the) ",
        "code": "RU",
        "code-alpha-3": "RUS",
        "tld": [
            ".ru"
        ]
    },
    "Rwanda": {
        "name": "Rwanda",
        "code": "RW",
        "code-alpha-3": "RWA",
        "tld": [
            ".rw"
        ]
    },
    "Saint Barthélemy": {
        "name": "Saint Barthélemy",
        "code": "BL",
        "code-alpha-3": "BLM",
        "tld": [
            ".bl"
        ]
    },
    "Saint Helena": {
        "name": "Saint Helena",
        "code": "SH",
        "code-alpha-3": "SHN",
        "tld": [
            ".sh"
        ]
    },
    "Saint Kitts and Nevis": {
        "name": "Saint Kitts and Nevis",
        "code": "KN",
        "code-alpha-3": "KNA",
        "tld": [
            ".kn"
        ]
    },
    "Saint Lucia": {
        "name": "Saint Lucia",
        "code": "LC",
        "code-alpha-3": "LCA",
        "tld": [
            ".lc"
        ]
    },
    "Saint Martin (French part)": {
        "name": "Saint Martin (French part)",
        "code": "MF",
        "code-alpha-3": "MAF",
        "tld": [
            ".mf"
        ]
    },
    "Saint Pierre and Miquelon": {
        "name": "Saint Pierre and Miquelon",
        "code": "PM",
        "code-alpha-3": "SPM",
        "tld": [
            ".pm"
        ]
    },
    "Saint Vincent and the Grenadines": {
        "name": "Saint Vincent and the Grenadines",
        "code": "VC",
        "code-alpha-3": "VCT",
        "tld": [
            ".vc"
        ]
    },
    "Samoa": {
        "name": "Samoa",
        "code": "WS",
        "code-alpha-3": "WSM",
        "tld": [
            ".ws"
        ]
    },
    "San Marino": {
        "name": "San Marino",
        "code": "SM",
        "code-alpha-3": "SMR",
        "tld": [
            ".sm"
        ]
    },
    "Sao Tome and Principe": {
        "name": "Sao Tome and Principe",
        "code": "ST",
        "code-alpha-3": "STP",
        "tld": [
            ".st"
        ]
    },
    "Saudi Arabia": {
        "name": "Saudi Arabia",
        "code": "SA",
        "code-alpha-3": "SAU",
        "tld": [
            ".sa"
        ]
    },
    "Senegal": {
        "name": "Senegal",
        "code": "SN",
        "code-alpha-3": "SEN",
        "tld": [
            ".sn"
        ]
    },
    "Serbia": {
        "name": "Serbia",
        "code": "RS",
        "code-alpha-3": "SRB",
        "tld": [
            ".rs"
        ]
    },
    "Seychelles": {
        "name": "Seychelles",
        "code": "SC",
        "code-alpha-3": "SYC",
        "tld": [
            ".sc"
        ]
    },
    "Sierra Leone": {
        "name": "Sierra Leone",
        "code": "SL",
        "code-alpha-3": "SLE",
        "tld": [
            ".sl"
        ]
    },
    "Singapore": {
        "name": "Singapore",
        "code": "SG",
        "code-alpha-3": "SGP",
        "tld": [
            ".sg"
        ]
    },
    "Sint Maarten (Dutch part)": {
        "name": "Sint Maarten (Dutch part)",
        "code": "SX",
        "code-alpha-3": "SXM",
        "tld": [
            ".sx"
        ]
    },
    "Slovakia": {
        "name": "Slovakia",
        "code": "SK",
        "code-alpha-3": "SVK",
        "tld": [
            ".sk"
        ]
    },
    "Slovenia": {
        "name": "Slovenia",
        "code": "SI",
        "code-alpha-3": "SVN",
        "tld": [
            ".si"
        ]
    },
    "Solomon Islands": {
        "name": "Solomon Islands",
        "code": "SB",
        "code-alpha-3": "SLB",
        "tld": [
            ".sb"
        ]
    },
    "Somalia": {
        "name": "Somalia",
        "code": "SO",
        "code-alpha-3": "SOM",
        "tld": [
            ".so"
        ]
    },
    "South Africa": {
        "name": "South Africa",
        "code": "ZA",
        "code-alpha-3": "ZAF",
        "tld": [
            ".za"
        ]
    },
    "South Georgia and the South Sandwich Islands": {
        "name": "South Georgia and the South Sandwich Islands",
        "code": "GS",
        "code-alpha-3": "SGS",
        "tld": [
            ".gs"
        ]
    },
    "South Sudan": {
        "name": "South Sudan",
        "code": "SS",
        "code-alpha-3": "SSD",
        "tld": [
            ".ss"
        ]
    },
    "Spain": {
        "name": "Spain",
        "code": "ES",
        "code-alpha-3": "ESP",
        "tld": [
            ".es"
        ]
    },
    "Sri Lanka": {
        "name": "Sri Lanka",
        "code": "LK",
        "code-alpha-3": "LKA",
        "tld": [
            ".lk"
        ]
    },
    "Sudan": {
        "name": "Sudan (the)",
        "code": "SD",
        "code-alpha-3": "SDN",
        "tld": [
            ".sd"
        ]
    },
    "Suriname": {
        "name": "Suriname",
        "code": "SR",
        "code-alpha-3": "SUR",
        "tld": [
            ".sr"
        ]
    },
    "Svalbard": {
        "name": "Svalbard",
        "code": "SJ",
        "code-alpha-3": "SJM",
        "tld": [],
        "aliases": [
            "Jan Mayen"
        ]
    },
    "Sweden": {
        "name": "Sweden",
        "code": "SE",
        "code-alpha-3": "SWE",
        "tld": [
            ".se"
        ]
    },
    "Switzerland": {
        "name": "Switzerland",
        "code": "CH",
        "code-alpha-3": "CHE",
        "tld": [
            ".ch"
        ]
    },
    "Syrian Arab Republic": {
        "name": "Syrian Arab Republic (the)",
        "code": "SY",
        "code-alpha-3": "SYR",
        "tld": [
            ".sy"
        ]
    },
    "Taiwan": {
        "name": "Taiwan (Province of China)",
        "code": "TW",
        "code-alpha-3": "TWN",
        "tld": [
            ".tw"
        ]
    },
    "Tajikistan": {
        "name": "Tajikistan",
        "code": "TJ",
        "code-alpha-3": "TJK",
        "tld": [
            ".tj"
        ]
    },
    "Tanzania": {
        "name": "Tanzania, the United Republic of",
        "code": "TZ",
        "code-alpha-3": "TZA",
        "tld": [
            ".tz"
        ]
    },
    "Thailand": {
        "name": "Thailand",
        "code": "TH",
        "code-alpha-3": "THA",
        "tld": [
            ".th"
        ]
    },
    "Timor-Leste": {
        "name": "Timor-Leste",
        "code": "TL",
        "code-alpha-3": "TLS",
        "tld": [
            ".tl"
        ],
        "aliases": [
            "East Timor"
        ]
    },
    "Togo": {
        "name": "Togo",
        "code": "TG",
        "code-alpha-3": "TGO",
        "tld": [
            ".tg"
        ]
    },
    "Tokelau": {
        "name": "Tokelau",
        "code": "TK",
        "code-alpha-3": "TKL",
        "tld": [
            ".tk"
        ]
    },
    "Tonga": {
        "name": "Tonga",
        "code": "TO",
        "code-alpha-3": "TON",
        "tld": [
            ".to"
        ]
    },
    "Trinidad and Tobago": {
        "name": "Trinidad and Tobago",
        "code": "TT",
        "code-alpha-3": "TTO",
        "tld": [
            ".tt"
        ]
    },
    "Tunisia": {
        "name": "Tunisia",
        "code": "TN",
        "code-alpha-3": "TUN",
        "tld": [
            ".tn"
        ]
    },
    "Turkey": {
        "name": "Türkiye",
        "code": "TR",
        "code-alpha-3": "TUR",
        "tld": [
            ".tr"
        ],
        "aliases": [
            "Türkiye"
        ]

    },
    "Turkmenistan": {
        "name": "Turkmenistan",
        "code": "TM",
        "code-alpha-3": "TKM",
        "tld": [
            ".tm"
        ]
    },
    "Turks and Caicos Islands": {
        "name": "Turks and Caicos Islands (the)",
        "code": "TC",
        "code-alpha-3": "TCA",
        "tld": [
            ".tc"
        ]
    },
    "Tuvalu": {
        "name": "Tuvalu",
        "code": "TV",
        "code-alpha-3": "TUV",
        "tld": [
            ".tv"
        ]
    },
    "Uganda": {
        "name": "Uganda",
        "code": "UG",
        "code-alpha-3": "UGA",
        "tld": [
            ".ug"
        ]
    },
    "Ukraine": {
        "name": "Ukraine",
        "code": "UA",
        "code-alpha-3": "UKR",
        "tld": [
            ".ua"
        ]
    },
    "United Arab Emirates": {
        "name": "United Arab Emirates (the)",
        "code": "AE",
        "code-alpha-3": "ARE",
        "tld": [
            ".ae"
        ]
    },
    "United Kingdom": {
        "name": "United Kingdom of Great Britain and Northern Ireland (the)",
        "code": "GB",
        "code-alpha-3": "GBR",
        "tld": [
            ".gb",
            ".uk"
        ],
        "aliases": [
            "Great Britain",
            "United Kingdom of Great Britain and Northern Ireland"
        ]
    },
    "United States of America": {
        "name": "United States of America (the)",
        "code": "US",
        "code-alpha-3": "USA",
        "tld": [
            ".us"
        ],
    },
    "United States Minor Outlying Islands": {
        "name": "United States Minor Outlying Islands (the)",
        "code": "UM",
        "code-alpha-3": "UMI",
        "tld": []
    },
    "Uruguay": {
        "name": "Uruguay",
        "code": "UY",
        "code-alpha-3": "URY",
        "tld": [
            ".uy"
        ]
    },
    "Uzbekistan": {
        "name": "Uzbekistan",
        "code": "UZ",
        "code-alpha-3": "UZB",
        "tld": [
            ".uz"
        ]
    },
    "Vanuatu": {
        "name": "Vanuatu",
        "code": "VU",
        "code-alpha-3": "VUT",
        "tld": [
            ".vu"
        ]
    },
    "Vatican City": {
        "name": "Vatican City – See Holy See, The.",
        "code": "VA",
        "code-alpha-3": "VAT",
        "tld": [
            ".va"
        ],
        "aliases": [
            "Holy See (the)"
        ]
    },
    "Venezuela": {
        "name": "Venezuela (Bolivarian Republic of)",
        "code": "VE",
        "code-alpha-3": "VEN",
        "tld": [
            ".ve"
        ]
    },
    "Viet Nam": {
        "name": "Viet Nam",
        "code": "VN",
        "code-alpha-3": "VNM",
        "tld": [
            ".vn"
        ]
    },
    "British Virgin Islands": {
        "name": "Virgin Islands (British)",
        "code": "VG",
        "code-alpha-3": "VGB",
        "tld": [
            ".vg"
        ]
    },
    "United States Virgin Islands": {
        "name": "Virgin Islands (U.S.)",
        "code": "VI",
        "code-alpha-3": "VIR",
        "tld": [
            ".vi"
        ]
    },
    "Wallis and Futuna": {
        "name": "Wallis and Futuna",
        "code": "WF",
        "code-alpha-3": "WLF",
        "tld": [
            ".wf"
        ]
    },
    "Western Sahara": {
        "name": "Western Sahara",
        "code": "EH",
        "code-alpha-3": "ESH",
        "tld": [
            "[al]"
        ],
        "aliases": [
            "Sahrawi Arab Democratic Republic"
        ]
    },
    "Yemen": {
        "name": "Yemen",
        "code": "YE",
        "code-alpha-3": "YEM",
        "tld": [
            ".ye"
        ]
    },
    "Zambia": {
        "name": "Zambia",
        "code": "ZM",
        "code-alpha-3": "ZMB",
        "tld": [
            ".zm"
        ]
    },
    "Zimbabwe": {
        "name": "Zimbabwe",
        "code": "ZW",
        "code-alpha-3": "ZWE",
        "tld": [
            ".zw"
        ]
    }
}


# This was assembled on 3-10-2024 using a 2015 geolite db which is the only db
# I still have
COUNTRY_CODE_TO_IP = {
   "AR": [
      181,
      190
   ],
   "AU": [
      1,
      103,
      168,
      202,
      203
   ],
   "BE": [
      57
   ],
   "BR": [
      177,
      187,
      189,
      191,
      201
   ],
   "CA": [
      47,
      96,
      142,
      174
   ],
   "CH": [
      85
   ],
   "CN": [
      14,
      36,
      42,
      60,
      101,
      111,
      112,
      113,
      116,
      119,
      120,
      175,
      183,
      218,
      221,
      223
   ],
   "CO": [
      179
   ],
   "DE": [
      53,
      77,
      89,
      91,
      134,
      139,
      141,
      176,
      178,
      188,
      217
   ],
   "ES": [
      88
   ],
   "FI": [
      153
   ],
   "FR": [
      2,
      81,
      90,
      93,
      109,
      164
   ],
   "GB": [
      25,
      51,
      80,
      82,
      86,
      92,
      94,
      163,
      213
   ],
   "GR": [
      62
   ],
   "HR": [
      78
   ],
   "HU": [
      84
   ],
   "ID": [
      114,
      182
   ],
   "IE": [
      193
   ],
   "IN": [
      61,
      196
   ],
   "IT": [
      79,
      87,
      131,
      151
   ],
   "JP": [
      43,
      58,
      110,
      118,
      122,
      123,
      125,
      126,
      133,
      150,
      157,
      180,
      211,
      219,
      220,
      222
   ],
   "KR": [
      27,
      49,
      59,
      115,
      124
   ],
   "NI": [
      186
   ],
   "NL": [
      145,
      212
   ],
   "NO": [
      195
   ],
   "PH": [
      121
   ],
   "PL": [
      31,
      83
   ],
   "PS": [
      185
   ],
   "RU": [
      37
   ],
   "SG": [
      171
   ],
   "SK": [
      194
   ],
   "TH": [
      210
   ],
   "TN": [
      197
   ],
   "TR": [
      46,
      95
   ],
   "TW": [
      39,
      106
   ],
   "UA": [
      5
   ],
   "US": [
      3,
      4,
      6,
      7,
      8,
      9,
      11,
      12,
      13,
      15,
      16,
      17,
      18,
      19,
      20,
      21,
      22,
      23,
      24,
      26,
      28,
      29,
      30,
      32,
      33,
      34,
      35,
      38,
      40,
      44,
      45,
      48,
      50,
      52,
      54,
      55,
      56,
      63,
      64,
      65,
      66,
      67,
      68,
      69,
      70,
      71,
      72,
      73,
      74,
      75,
      76,
      97,
      98,
      99,
      100,
      104,
      107,
      108,
      128,
      129,
      130,
      132,
      135,
      136,
      137,
      138,
      140,
      143,
      146,
      147,
      148,
      149,
      152,
      154,
      155,
      156,
      158,
      159,
      160,
      161,
      162,
      165,
      166,
      167,
      170,
      172,
      173,
      184,
      192,
      198,
      199,
      204,
      205,
      206,
      207,
      208,
      209,
      214,
      215,
      216
   ],
   "VE": [
      200
   ],
   "VN": [
      117
   ],
   "ZA": [
      41,
      105,
      169
   ]
}


for name, cinfo in COUNTRIES_INFO.items():
    info = dict(cinfo)

    if info["code"] in COUNTRY_CODE_TO_IP:
        info["ips"] = list(COUNTRY_CODE_TO_IP[info["code"]])

    country_lookup[name] = info
    country_lookup.setdefault(info["name"], info)

    country_lookup[info["code"]] = info
    country_lookup[info["code"].lower()] = info
    country_lookup[info["code-alpha-3"]] = info
    country_lookup[info["code-alpha-3"].lower()] = info

    for alias in info.get("aliases", []):
        country_lookup.setdefault(alias, info)

    for tld in info["tld"]:
        country_tlds.add(tld.strip("."))


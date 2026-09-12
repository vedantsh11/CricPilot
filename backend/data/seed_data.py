from backend.models.player import (
    Player,
    PlayerRole
)

from backend.models.match import (
    Match,
    WeatherState,
    MatchContext
)


def player(
    id,
    name,
    team,
    role,
    credits,
    batting,
    bowling,
    form,
    consistency,
    upside,
    fantasy_avg,
    fantasy_ceiling,
    recent_points,
    powerplay=50,
    death=50,
    pace=50,
    spin=50,
    venue=75
):

    return Player(
        id=id,
        name=name,
        real_team=team,
        role=role,

        credits=credits,

        batting_rating=batting,
        bowling_rating=bowling,

        form_rating=form,
        consistency_rating=consistency,
        upside_rating=upside,

        fantasy_avg=fantasy_avg,
        fantasy_ceiling=fantasy_ceiling,

        recent_points=recent_points,

        powerplay_rating=powerplay,
        death_overs_rating=death,

        pace_rating=pace,
        spin_rating=spin,

        venue_rating=venue
    )


def create_players() -> list[Player]:

    return [

        # ==================================================
        # INDIA — WICKETKEEPERS
        # ==================================================

        player(
            "P001",
            "Arjun Mehta",
            "IND",
            PlayerRole.WICKETKEEPER,
            9.5,
            88, 0,
            91, 84, 92,
            67.4, 118,
            [72, 61, 83, 57, 78],
            powerplay=86,
            pace=89,
            spin=78,
            venue=91
        ),

        player(
            "P002",
            "Vikram Rao",
            "IND",
            PlayerRole.WICKETKEEPER,
            8.5,
            79, 0,
            82, 80, 84,
            58.5, 101,
            [61, 54, 70, 48, 59],
            powerplay=80,
            pace=82,
            spin=76,
            venue=84
        ),

        # ==================================================
        # INDIA — BATTERS
        # ==================================================

        player(
            "P003",
            "Rohan Sharma",
            "IND",
            PlayerRole.BATTER,
            10.0,
            94, 0,
            90, 87, 94,
            69.8, 124,
            [82, 76, 71, 91, 59],
            powerplay=93,
            pace=91,
            spin=87,
            venue=94
        ),

        player(
            "P004",
            "Aarav Kapoor",
            "IND",
            PlayerRole.BATTER,
            9.5,
            88, 0,
            86, 85, 88,
            63.2, 112,
            [65, 71, 58, 69, 53],
            powerplay=87,
            pace=88,
            spin=82,
            venue=89
        ),

        player(
            "P005",
            "Karan Malhotra",
            "IND",
            PlayerRole.BATTER,
            8.5,
            82, 0,
            84, 79, 91,
            57.4, 119,
            [48, 82, 41, 77, 59],
            powerplay=84,
            pace=80,
            spin=89,
            venue=82
        ),

        player(
            "P006",
            "Aditya Verma",
            "IND",
            PlayerRole.BATTER,
            8.0,
            79, 0,
            77, 82, 79,
            51.6, 94,
            [52, 61, 48, 57, 40],
            powerplay=75,
            pace=78,
            spin=84,
            venue=79
        ),

        player(
            "P007",
            "Dev Bansal",
            "IND",
            PlayerRole.BATTER,
            7.5,
            74, 0,
            73, 76, 81,
            46.8, 101,
            [44, 51, 63, 37, 39],
            powerplay=78,
            pace=74,
            spin=80,
            venue=76
        ),

        # ==================================================
        # INDIA — ALL ROUNDERS
        # ==================================================

        player(
            "P008",
            "Kabir Singh",
            "IND",
            PlayerRole.ALL_ROUNDER,
            10.5,
            84, 86,
            92, 88, 96,
            74.1, 132,
            [82, 66, 91, 74, 79],
            powerplay=82,
            death=91,
            pace=88,
            spin=84,
            venue=93
        ),

        player(
            "P009",
            "Yash Thakur",
            "IND",
            PlayerRole.ALL_ROUNDER,
            9.0,
            76, 79,
            83, 81, 85,
            61.8, 108,
            [58, 73, 65, 55, 58],
            powerplay=71,
            death=83,
            pace=80,
            spin=77,
            venue=85
        ),

        player(
            "P010",
            "Manav Joshi",
            "IND",
            PlayerRole.ALL_ROUNDER,
            8.0,
            70, 73,
            76, 78, 82,
            53.9, 99,
            [49, 61, 55, 47, 57],
            powerplay=65,
            death=78,
            pace=73,
            spin=81,
            venue=78
        ),

        # ==================================================
        # INDIA — BOWLERS
        # ==================================================

        player(
            "P011",
            "Dev Malhotra",
            "IND",
            PlayerRole.BOWLER,
            9.5,
            30, 92,
            89, 87, 91,
            65.8, 116,
            [64, 72, 51, 79, 68],
            death=94,
            pace=95,
            spin=45,
            venue=92
        ),

        player(
            "P012",
            "Ritvik Saini",
            "IND",
            PlayerRole.BOWLER,
            9.0,
            22, 87,
            86, 85, 87,
            61.2, 109,
            [68, 54, 73, 59, 52],
            death=88,
            pace=91,
            spin=40,
            venue=88
        ),

        player(
            "P013",
            "Harsh Vardhan",
            "IND",
            PlayerRole.BOWLER,
            8.5,
            20, 82,
            81, 83, 84,
            57.6, 104,
            [61, 49, 64, 55, 59],
            death=85,
            pace=87,
            spin=38,
            venue=84
        ),

        player(
            "P014",
            "Nakul Sharma",
            "IND",
            PlayerRole.BOWLER,
            8.0,
            18, 78,
            78, 80, 80,
            53.2, 96,
            [48, 61, 52, 45, 60],
            death=81,
            pace=83,
            spin=41,
            venue=80
        ),

        player(
            "P015",
            "Aman Deep",
            "IND",
            PlayerRole.BOWLER,
            7.5,
            15, 74,
            74, 77, 78,
            49.7, 91,
            [43, 56, 47, 51, 51],
            death=79,
            pace=80,
            spin=35,
            venue=77
        ),

        # ==================================================
        # AUSTRALIA — WICKETKEEPERS
        # ==================================================

        player(
            "P016",
            "Oliver King",
            "AUS",
            PlayerRole.WICKETKEEPER,
            9.0,
            84, 0,
            86, 83, 88,
            61.5, 108,
            [67, 61, 55, 71, 53],
            powerplay=82,
            pace=87,
            spin=81,
            venue=88
        ),

        player(
            "P017",
            "Noah Bennett",
            "AUS",
            PlayerRole.WICKETKEEPER,
            8.0,
            76, 0,
            78, 79, 81,
            52.8, 96,
            [49, 62, 47, 55, 51],
            powerplay=76,
            pace=79,
            spin=77,
            venue=80
        ),

        # ==================================================
        # AUSTRALIA — BATTERS
        # ==================================================

        player(
            "P018",
            "Liam Carter",
            "AUS",
            PlayerRole.BATTER,
            10.5,
            93, 0,
            91, 88, 95,
            70.3, 127,
            [88, 63, 74, 91, 67],
            powerplay=92,
            pace=94,
            spin=86,
            venue=92
        ),

        player(
            "P019",
            "Ethan Walker",
            "AUS",
            PlayerRole.BATTER,
            9.5,
            87, 0,
            88, 86, 90,
            64.6, 116,
            [71, 66, 61, 73, 52],
            powerplay=85,
            pace=89,
            spin=83,
            venue=87
        ),

        player(
            "P020",
            "James Wilson",
            "AUS",
            PlayerRole.BATTER,
            8.5,
            81, 0,
            80, 78, 87,
            55.4, 105,
            [49, 67, 52, 61, 44],
            powerplay=79,
            pace=84,
            spin=81,
            venue=82
        ),

        player(
            "P021",
            "Henry Adams",
            "AUS",
            PlayerRole.BATTER,
            8.0,
            77, 0,
            76, 80, 79,
            51.8, 97,
            [57, 48, 61, 45, 48],
            powerplay=74,
            pace=80,
            spin=78,
            venue=79
        ),

        player(
            "P022",
            "Lucas Moore",
            "AUS",
            PlayerRole.BATTER,
            7.5,
            72, 0,
            72, 75, 82,
            46.1, 101,
            [39, 55, 44, 49, 43],
            powerplay=76,
            pace=75,
            spin=79,
            venue=75
        ),

        # ==================================================
        # AUSTRALIA — ALL ROUNDERS
        # ==================================================

        player(
            "P023",
            "Noah Williams",
            "AUS",
            PlayerRole.ALL_ROUNDER,
            10.0,
            82, 88,
            93, 89, 96,
            73.2, 130,
            [73, 81, 69, 88, 77],
            powerplay=81,
            death=93,
            pace=91,
            spin=83,
            venue=91
        ),

        player(
            "P024",
            "Jack Morgan",
            "AUS",
            PlayerRole.ALL_ROUNDER,
            9.0,
            78, 80,
            84, 83, 88,
            62.4, 111,
            [61, 68, 54, 73, 56],
            powerplay=73,
            death=86,
            pace=84,
            spin=75,
            venue=84
        ),

        player(
            "P025",
            "William Ross",
            "AUS",
            PlayerRole.ALL_ROUNDER,
            8.0,
            70, 75,
            77, 78, 83,
            54.7, 102,
            [51, 62, 47, 58, 55],
            powerplay=67,
            death=80,
            pace=77,
            spin=79,
            venue=78
        ),

        # ==================================================
        # AUSTRALIA — BOWLERS
        # ==================================================

        player(
            "P026",
            "Ethan Brooks",
            "AUS",
            PlayerRole.BOWLER,
            9.5,
            24, 91,
            88, 86, 92,
            64.1, 114,
            [58, 74, 67, 61, 76],
            death=95,
            pace=94,
            spin=42,
            venue=90
        ),

        player(
            "P027",
            "Ryan Cooper",
            "AUS",
            PlayerRole.BOWLER,
            9.0,
            20, 87,
            85, 84, 88,
            60.7, 109,
            [62, 57, 72, 54, 59],
            death=90,
            pace=92,
            spin=39,
            venue=87
        ),

        player(
            "P028",
            "Charlie Hughes",
            "AUS",
            PlayerRole.BOWLER,
            8.5,
            18, 83,
            82, 81, 85,
            57.3, 103,
            [55, 63, 49, 61, 58],
            death=84,
            pace=88,
            spin=37,
            venue=83
        ),

        player(
            "P029",
            "Thomas Reed",
            "AUS",
            PlayerRole.BOWLER,
            8.0,
            16, 79,
            78, 80, 81,
            52.6, 96,
            [51, 46, 63, 54, 49],
            death=80,
            pace=84,
            spin=36,
            venue=79
        ),

        player(
            "P030",
            "Daniel Scott",
            "AUS",
            PlayerRole.BOWLER,
            7.5,
            14, 74,
            74, 76, 78,
            48.9, 91,
            [42, 55, 48, 44, 55],
            death=77,
            pace=80,
            spin=35,
            venue=75
        ),

        # ==================================================
        # ADDITIONAL ROTATION PLAYERS
        # ==================================================

        player(
            "P031", "Ishan Nair", "IND",
            PlayerRole.BATTER,
            7.0, 70, 0, 70, 74, 79,
            44.5, 92, [42, 47, 51, 39, 43]
        ),

        player(
            "P032", "Raj Mehra", "IND",
            PlayerRole.BOWLER,
            7.0, 12, 70, 71, 74, 75,
            46.3, 88, [44, 48, 39, 52, 47],
            death=73, pace=76, spin=55
        ),

        player(
            "P033", "Samar Khan", "IND",
            PlayerRole.ALL_ROUNDER,
            7.5, 68, 69, 72, 75, 80,
            49.8, 95, [51, 45, 54, 43, 56]
        ),

        player(
            "P034", "Raghav Iyer", "IND",
            PlayerRole.BATTER,
            7.0, 68, 0, 69, 73, 76,
            43.7, 89, [40, 53, 38, 47, 40]
        ),

        player(
            "P035", "Varun Gill", "IND",
            PlayerRole.BOWLER,
            7.0, 15, 72, 73, 76, 78,
            47.2, 93, [49, 42, 51, 45, 48],
            death=76, pace=79, spin=48
        ),

        player(
            "P036", "Aaron Blake", "AUS",
            PlayerRole.BATTER,
            7.0, 69, 0, 71, 74, 80,
            44.9, 94, [46, 41, 55, 39, 44]
        ),

        player(
            "P037", "Michael Ford", "AUS",
            PlayerRole.BOWLER,
            7.0, 13, 71, 72, 75, 77,
            46.1, 90, [43, 51, 47, 39, 50],
            death=74, pace=77, spin=42
        ),

        player(
            "P038", "Ben Foster", "AUS",
            PlayerRole.ALL_ROUNDER,
            7.5, 67, 70, 74, 76, 82,
            51.3, 99, [48, 56, 51, 46, 55]
        ),

        player(
            "P039", "Jacob Lee", "AUS",
            PlayerRole.BATTER,
            7.0, 71, 0, 68, 72, 79,
            43.2, 91, [37, 49, 46, 44, 40]
        ),

        player(
            "P040", "Sam Turner", "AUS",
            PlayerRole.BOWLER,
            7.0, 12, 73, 70, 74, 76,
            45.7, 92, [41, 52, 44, 47, 45],
            death=78, pace=81, spin=41
        ),

        # ==================================================
        # EXTRA KEEPERS
        # ==================================================

        player(
            "P041", "Neil Kapoor", "IND",
            PlayerRole.WICKETKEEPER,
            7.5, 72, 0, 74, 76, 80,
            49.2, 94, [48, 55, 41, 51, 51]
        ),

        player(
            "P042", "Marcus Bell", "AUS",
            PlayerRole.WICKETKEEPER,
            7.5, 74, 0, 75, 77, 81,
            50.1, 97, [52, 47, 56, 45, 50]
        )
    ]


def create_match() -> Match:

    weather = WeatherState(
        temperature=28.0,
        humidity=62.0,
        rain_probability=20.0,
        wind_speed=12.0,
        condition="Clear"
    )

    context = MatchContext(
        pitch_type="balanced",
        batting_friendly=0.65,
        bowling_friendly=0.35
    )

    return Match(
        id="MATCH001",
        team_a="IND",
        team_b="AUS",
        venue="Mumbai",
        date="2026-09-20",
        start_time="19:30",
        weather=weather,
        context=context
    )
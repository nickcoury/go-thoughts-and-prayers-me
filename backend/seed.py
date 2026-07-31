"""Seed the database with dry-humor campaigns."""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "thoughts.db")

CAMPAIGNS = [
    {
        "slug": "johnson-family-tv-remote",
        "title": "Help the Johnson Family Find Their Missing TV Remote",
        "description": (
            "For three days, the Johnson family of Wichita, Kansas has been unable to watch television. "
            "The remote — a black Roku model last seen between the couch cushions on Tuesday evening — "
            "remains missing despite exhaustive search efforts. The family has checked under the couch, "
            "between the cushions (again), the kitchen counter, both bathrooms, and the garage for reasons "
            "no one can explain.\n\n"
            "This is a crisis of unprecedented proportion in the Johnson household. The manual buttons on "
            "the TV itself are functional but deeply unsatisfying. The family reports feelings of frustration, "
            "mild irritability, and having to actually stand up to change inputs.\n\n"
            "Your thoughts and prayers will provide the emotional fortitude the Johnsons need to look in the "
            "same three places again, but this time with purpose."
        ),
        "goal_thoughts": 5000,
        "goal_prayers": 2000,
        "organizer_name": "Concerned Neighbor",
    },
    {
        "slug": "greg-lunch-decision",
        "title": "Support for Greg: A Man Who Cannot Decide What to Eat",
        "description": (
            "Greg Thompson, 34, has been standing in front of his open refrigerator for approximately "
            "45 minutes. The contents — leftover lasagna, half a rotisserie chicken, assorted condiments, "
            "and an unexplained jar of capers — offer no clear path forward.\n\n"
            "Greg has ruled out the lasagna (had it yesterday), the chicken (requires effort), and the "
            "capers (what even are these for). He is now in what nutritionists call a \"decision paralysis "
            "spiral\" — a condition affecting millions of Americans daily.\n\n"
            "Friends describe Greg as \"a guy who really needs to meal prep\" and \"someone who should "
            "probably just order a sandwich.\" But Greg wants to make the responsible choice. He wants to "
            "eat what's already in his fridge. He just... can't choose.\n\n"
            "Your donations of thoughts and prayers will give Greg the clarity he needs. Or at minimum, "
            "the emotional support to finally admit defeat and order DoorDash."
        ),
        "goal_thoughts": 10000,
        "goal_prayers": 5000,
        "organizer_name": "Greg's Coworker",
    },
    {
        "slug": "office-3b-coffee-machine",
        "title": "Urgent Relief: The Office 3B Coffee Situation",
        "description": (
            "The coffee machine in Office 3B at the Henderson Corporate Center has begun making "
            "a sound. Not the normal brewing sound — a new sound. A sound that several employees "
            "have independently described as \"concerning\" and \"not ideal.\"\n\n"
            "A work order was submitted to building maintenance on Monday morning. It is now "
            "Thursday. The machine continues to make the sound. Coffee production, remarkably, "
            "continues at normal levels, but the psychological toll is mounting.\n\n"
            "\"Every time I press brew, I wonder if this is the time it finally gives up,\" "
            "said Melissa Tran, Senior Regional Coordinator. \"The coffee tastes exactly the same, "
            "but the experience is ruined.\"\n\n"
            "The Office 3B community is resilient, but resilience has limits. They need to know "
            "that people outside these walls understand their struggle. Your thoughts and prayers "
            "will be printed and posted on the break room bulletin board."
        ),
        "goal_thoughts": 7500,
        "goal_prayers": 3000,
        "organizer_name": "Office 3B Wellness Committee",
    },
    {
        "slug": "sarah-devastating-haircut",
        "title": "Rebuilding After a Devastating Haircut",
        "description": (
            "Sarah M. walked into Great Clips with a reference photo and hope. She walked out with "
            "something that was, technically, shorter hair. The stylist — whose name Sarah has "
            "chosen not to disclose — described the result as \"edgy\" and \"textured.\" Sarah's "
            "mother described it as \"it'll grow back, sweetie.\"\n\n"
            "The incident occurred on Saturday. It is now Wednesday. Sarah has experimented with "
            "hats, headbands, and what she calls \"aggressive side-parting,\" but the fundamental "
            "reality of the haircut remains unchanged.\n\n"
            "Sarah is not asking for financial assistance. Hair grows at approximately half an inch "
            "per month. The math is clear: she needs approximately 4-6 months of emotional support. "
            "Your thoughts will be tallied and delivered to Sarah in a supportive, non-judgmental "
            "format. Your prayers will accelerate follicle activity through methods we are not "
            "qualified to explain."
        ),
        "goal_thoughts": 20000,
        "goal_prayers": 15000,
        "organizer_name": "Sarah's Support Circle",
    },
    {
        "slug": "kevin-parallel-parking",
        "title": "Kevin Has Been Parallel Parking for 17 Minutes",
        "description": (
            "Kevin is currently attempting to parallel park his 2018 Honda Civic outside a restaurant "
            "where his friends are already seated and have already ordered appetizers.\n\n"
            "The spot is adequate. Kevin has pulled alongside the car in front. He has angled the wheel. "
            "He has begun reversing. He has then pulled forward again. This cycle has repeated seven "
            "times. Bystanders report the Civic is now at approximately a 30-degree angle to the curb, "
            "which is worse than when he started.\n\n"
            "Kevin's girlfriend is live-texting the situation to the group chat. The calamari is "
            "getting cold. A small crowd has gathered at the restaurant window.\n\n"
            "Kevin doesn't need a parking spot — at this point there are three open ones further down "
            "the block. Kevin needs closure. He needs to know that the emotional investment he has made "
            "in THIS SPECIFIC SPOT was not in vain. Send thoughts. Send prayers. Send spatial reasoning."
        ),
        "goal_thoughts": 8000,
        "goal_prayers": 4000,
        "organizer_name": "The Group Chat",
    },
]


def seed_campaigns():
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")

    for c in CAMPAIGNS:
        existing = db.execute(
            "SELECT 1 FROM campaigns WHERE slug = ?", (c["slug"],)
        ).fetchone()
        if existing:
            continue
        db.execute(
            """INSERT INTO campaigns
               (slug, title, description, goal_thoughts, goal_prayers,
                current_thoughts, current_prayers, organizer_name)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                c["slug"],
                c["title"],
                c["description"],
                c["goal_thoughts"],
                c["goal_prayers"],
                0,  # current_thoughts
                0,  # current_prayers
                c["organizer_name"],
            ),
        )

    # Add some seed donations so campaigns don't look empty
    seed_donations = [
        ("johnson-family-tv-remote", "Prayerful in Peoria", "Have you checked the bathroom? People bring remotes to bathrooms. It happens.", 0, 12),
        ("johnson-family-tv-remote", "Thinking of You in Tulsa", "We lost ours for two weeks. It was in the freezer. Thoughts and prayers incoming.", 8, 0),
        ("johnson-family-tv-remote", "Anonymous", "This happened to my cousin. They never found it. They just bought a universal remote and moved on. But I believe in the Johnsons.", 15, 5),
        ("greg-lunch-decision", "Mark from Accounting", "Greg, the chicken. Just eat the chicken. Sending 50 thoughts your way.", 50, 0),
        ("greg-lunch-decision", "Mom", "Honey please just eat something. I'm praying for you. Also there's soup in the freezer that I brought over last week.", 0, 25),
        ("office-3b-coffee-machine", "Maintenance Dept", "We are aware of the sound. The sound is being investigated. Thank you for your patience.", 100, 0),
        ("office-3b-coffee-machine", "Janet from 4A", "Our machine did this last year. It lasted another six months. Stay strong.", 25, 10),
        ("sarah-devastating-haircut", "Fellow Survivor", "I had a bad haircut in 2019. I wore a beanie for three months. You will emerge from this stronger. 100 thoughts.", 100, 0),
        ("sarah-devastating-haircut", "Sarah's Mom", "It doesn't look that bad, sweetie. But I'll pray anyway.", 0, 30),
        ("kevin-parallel-parking", "Friend at the Restaurant", "We ordered you the chicken parmesan. The bread is almost gone. Please just take the spot down the block. 200 thoughts.", 200, 0),
        ("kevin-parallel-parking", "The Server", "We need the table back soon. But sending prayers. 🙏", 0, 8),
    ]

    for slug, donor, msg, thoughts, prayers in seed_donations:
        camp = db.execute("SELECT id FROM campaigns WHERE slug = ?", (slug,)).fetchone()
        if not camp:
            continue
        db.execute(
            """INSERT INTO donations (campaign_id, donor_name, message, thoughts, prayers)
               VALUES (?, ?, ?, ?, ?)""",
            (camp["id"], donor, msg, thoughts, prayers),
        )
        db.execute(
            "UPDATE campaigns SET current_thoughts = current_thoughts + ?, current_prayers = current_prayers + ? WHERE id = ?",
            (thoughts, prayers, camp["id"]),
        )

    db.commit()
    db.close()
    print(f"Seeded {len(CAMPAIGNS)} campaigns with sample donations.")

"""Site map for the Iowa PTA rebuild: menu structure, page sections and images.

Each page is a flat file in the repo root: <slug>.html
"""

LIVE = "https://iowapta.org"

EXT = {
    "donate": "https://www.memberplanet.com/campaign/iowapta/communitydonating_146",
    "join-our-team": "https://iowapta.org/wp-content/uploads/2022/11/Board_of_Directors_Recruitment_Packet-1.pdf",
    "national-pta": "https://www.pta.org/",
    "shoppta": "https://stores.shoppta.com/index.lasso?host=IAPTA",
    "calendar": "https://iowapta.org/events/month/",
    "facebook": "https://www.facebook.com/iowapta.board/?ref=bookmarks",
    "instagram": "https://www.instagram.com/iowapta/",
    "twitter": "https://twitter.com/IowaPTA?s=17",
}

# (slug, menu label, children)  -- slug "ext:key" = external link
MENU = [
    ("running-your-pta", "Running Your PTA", [
        ("membership", "Membership", [
            ("develop-a-membership-plan", "Develop a Membership Plan", []),
            ("membership-awards", "Membership Awards", []),
            ("pta-branded-merchandise", "PTA Branded Merchandise", []),
        ]),
        ("toolkits-elearning", "Toolkits & eLearning", []),
        ("national-standards-for-family-school-partnerships", "National Standards for Family School Partnerships", []),
        ("awards-grants", "Awards & Grants", []),
        ("forms-for-leaders", "Forms for Leaders", []),
        ("roberts-rules-of-order", "Roberts Rules of Order", []),
        ("bylaws", "Bylaws", []),
        ("officers-and-committees", "Officers and Committees", []),
        ("finance", "Finance", [
            ("insurance", "Insurance", []),
            ("taxes-audits", "Taxes & Audits", []),
            ("gambling-and-sales-tax", "Gambling and Sales Tax", []),
        ]),
        ("starting-or-merging-a-pta", "Starting or Merging a PTA", []),
        ("ipta-standards-of-affiliation-for-local-units", "IPTA Standards of Affiliation for Local Units", []),
        ("memberhub", "MemberHub", []),
    ]),
    ("advocacy", "Advocacy", [
        ("ipta-state-and-federal-legislative-platform", "IPTA State and Federal Legislative Platform", []),
        ("suggest-a-platform-change", "Suggest a Platform Change", []),
        ("ptas-positions", "PTA's Positions", []),
        ("register-to-vote", "Register to Vote!", []),
        ("advocacy-toolkit", "Advocacy Toolkit", []),
        ("pta-takes-action", "PTA Takes Action", []),
        ("resources", "Resources", [
            ("state-and-national-websites", "State and National Websites", []),
            ("articles-for-advocates", "Articles for Advocates", []),
        ]),
    ]),
    ("programs-events", "Programs & Events", [
        ("npta-school-of-excellence", "NPTA School of Excellence", []),
        ("reflections", "Reflections", []),
        ("family-reading-experience", "Family Reading Experience", []),
        ("stem-families", "STEM + Families", []),
        ("pta-connected", "PTA Connected", []),
        ("healthy-lifestyles", "Healthy Lifestyles", []),
        ("connect-4-respect", "Connect 4 Respect", []),
        ("hl-taylor-scholarship", "HL Taylor Scholarship", []),
        ("founders-day", "Founder's Day", []),
    ]),
    ("about-us", "About Us", [
        ("mission", "Mission", []),
        ("board-of-directors-committees-staff", "Board of Directors, Committees, Staff", []),
        ("partners-sponsors", "Partners & Sponsors", []),
        ("history", "History", []),
        ("ipta-governance", "IPTA Governance", []),
        ("why-join-pta", "Why Join PTA?", []),
        ("iowa-pta-past-presidents", "Iowa PTA Past Presidents", []),
    ]),
    ("ext:donate", "Donate", []),
    ("contact-us", "Contact Us", [
        ("ext:join-our-team", "Join our Team!", []),
        ("ext:national-pta", "National PTA", []),
    ]),
]

TODO = [
    ("program-advocacy-updates", "Program & Advocacy Updates"),
    ("unit-registration-form", "Unit Registration Form", ),
    ("join-pta", "JOIN PTA!"),
    ("apply-to-join-our-board", "APPLY to Join our Board of Directors & Committees"),
]

# Pages that exist but are not in the main menu: slug -> parent section slug
EXTRA = {
    "lifetime-achievement": "programs-events",
    "reflections-theme-search": "reflections",
    "scholarship-application": "hl-taylor-scholarship",
    "duties-of-officers": "officers-and-committees",
    "join-pta": None,
    "ipta-in-action": None,
    "program-advocacy-updates": None,
    "unit-registration-form": None,
    "apply-to-join-our-board": None,
    "website-updateaddress-change": "updates",
    "website-updates": "updates",
    "what-is-the-updates-section": "updates",
}

# Live-site URL slug -> our slug, where they differ
LIVE_SLUG = {
    "unit-registration-form-update-your-info-today": "unit-registration-form",
    "apply-to-join-our-board-of-directors-committees": "apply-to-join-our-board",
}

SECTION_IMG = {
    "running-your-pta": "images/photo-04.jpg",
    "advocacy": "images/photo-07.jpg",
    "programs-events": "images/bgC.jpg",
    "about-us": "images/photo-12.jpg",
    "contact-us": "images/photo-09.jpg",
    None: "images/photo-10.jpg",
    "updates": "images/photo-11.jpg",
}
PAGE_IMG = {
    "npta-school-of-excellence": "images/bgB.jpg",
    "reflections": "images/bgI.jpg",
    "reflections-theme-search": "images/bgI.jpg",
    "family-reading-experience": "images/bgF.jpg",
    "stem-families": "images/bgH.jpg",
    "pta-connected": "images/bgG.jpg",
    "healthy-lifestyles": "images/bg4.jpg",
    "connect-4-respect": "images/bgE.jpg",
    "hl-taylor-scholarship": "images/bgD.jpg",
    "scholarship-application": "images/bgD.jpg",
    "founders-day": "images/bg1.jpg",
    "lifetime-achievement": "images/bg8.jpg",
    "join-pta": "images/bgA.jpg",
    "program-advocacy-updates": "images/bg2.jpg",
    "unit-registration-form": "images/bg9.jpg",
    "apply-to-join-our-board": "images/bg6.jpg",
    "history": "images/photo-03.jpg",
}

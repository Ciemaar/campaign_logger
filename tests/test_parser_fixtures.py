import json
import os

from campaign_logger.api import LoggerClient


def test_parse_log_entry_from_fixture():
    fixture_path = os.path.join(os.path.dirname(__file__), "fixtures", "log_entry_kebab.json")
    with open(fixture_path, "r") as f:
        data = json.load(f)["data"]

    client = LoggerClient()
    entry = client._parse_log_entry(data)

    assert entry.id == "80b93c9cc3cb4595811b780c91fae8a9"
    assert entry.log_id == "bf7c92f7749649ebbf43b168ff820ae6"
    assert entry.raw_text == "@Unicorn takes up residence near @\"Lillian Robin\" after she purifies her home and part of #\"Fork State Park\"  in the *\"Psychic Storm Of Purification\""


def test_parse_campaign_entry_from_fixture():
    fixture_path = os.path.join(os.path.dirname(__file__), "fixtures", "campaign_entry_kebab.json")
    with open(fixture_path, "r") as f:
        data = json.load(f)["data"]

    client = LoggerClient()
    entry = client._parse_campaign_entry(data)

    assert entry.id == "13803ddeee244a9ebe29575da8e1414f"
    assert entry.campaign_id == "535738ede60447209b9bb5c1e364a92a"
    assert entry.raw_text == "Pick or roll a type, then the stats as listed. This should allow you to select any OCC from those listed.  \n  \n__01-12% Brainy:__ I.Q. 1D6+18, M.E. 1D6+12, M.A. 1D4+10, P.S. 1D6+9, P.P. 2D4+9, P.E. 1D4+8, P.B. 1D6+9, Spd 1D6+11.  \n Best as Peacekeeper Medic, Field Engineer, Intel Agent,  \n__13-26% Strong-Willed:__ I.Q. 1D6+11, M.E. 1D6+19, M.A. 1D6+9, P.S. 1D6+9, P.P. 1D4+13, P.E. 1D6+10, P.B. 1D6+9, Spd 1D6+8.  \n Best as Military Specialist, Para- Arcane, Witchhunter  \n__27-39% Charismatic:__ I.Q. 1D6+10, M.E. 1D4+1D6+9, M.A. 1D6+18, P.S. 1D4+10, P.P. 1D4+10, P.E. 1D6+8, P.B. 1D6+14, Spd 1D6+9.  \n Best as Intel Agent,  \n__40-51% Physically Strong:__ I.Q. 1D4+10, M.E. 1D4+10, M.A. 1D6+10, P.S. 2D6+19, P.P. 1D4+12, P.E. 1D6+15, P.B. 1D6+12, Spd 1D6+11  \n Best as Armored Sentinels, Soldier/Peacekeeper, Fire & Rescue, Para-Arcane, Witchhunter  \n__52-65% Fast Reflexes and High Dexterity:__ I.Q. 1D4+10, M.E. 1D6+9, M.A. 1D6+8, P.S. 1D6+9, P.P. 1D6+19, P.E. 1D6+11, P.B. 1D6+10, Spd 1D6+17  \n Best as Chromium Guardsmen, Silver Eagle,  \n__66-78% Great Endurance:__ I.Q. 1D4+9, M.E. 1D6+14, M.A. 1D6+8, P.S. 1D6+9, P.P. 1D6+9, P.E. 1D6+19, P.B. 1D6+9, Spd 1D6+12  \n Best as Soldier/Peacekeeper,  \n__79-88% A Beauty or Pretty Boy:__ I.Q. 1D4+10, M.E. 1D6+8, M.A. 1D6+15, P.S. 1D6+11, P.P. 1D6+8, P.E. 1D6+9, P.B. 1D4+20, Spd 1D6+9.  \n Best as Volunteer Militia Fighter, Civilian  \n__89-00% Fast as Lightning:__ I.Q. 1D4+9, M.E. 1D6+9, M.A. 1D6+8, P.S. 1D6+9, P.P. 1D6+14, P.E. 1D6+10, P.B. 1D6+10, Spd 2D6+20.  \n Best as Soldier/Peacekeeper, Volunteer Militia Fighter"


def test_parse_log_from_fixture():
    fixture_path = os.path.join(os.path.dirname(__file__), "fixtures", "log_kebab.json")
    with open(fixture_path, "r") as f:
        data = json.load(f)["data"]

    client = LoggerClient()
    log_obj = client._parse_log(data)

    assert log_obj.id == "4ddd887e1988489498989162dca92bd2"
    assert log_obj.campaign_id == "45ee4afaaeb745f9bda39f857a570bf4"
    assert log_obj.title =="Beep-Bop-Boop"


def test_parse_campaign_from_fixture():
    fixture_path = os.path.join(os.path.dirname(__file__), "fixtures", "campaign_kebab.json")
    with open(fixture_path, "r") as f:
        data = json.load(f)["data"]

    client = LoggerClient()
    campaign_obj = client._parse_campaign(data)

    assert campaign_obj.id == "45ee4afaaeb745f9bda39f857a570bf4"
    assert campaign_obj.title == "The Future!"


def test_parse_log_entry_from_fixture_title_fallback():
    fixture_path = os.path.join(os.path.dirname(__file__), "fixtures", "log_entry_title.json")
    with open(fixture_path, "r") as f:
        data = json.load(f)["data"]

    client = LoggerClient()
    entry = client._parse_log_entry(data)

    assert entry.id == "8b470101e91d47459e87ecbcee2e30c3"
    assert entry.log_id == "4ddd887e1988489498989162dca92bd2"
    assert entry.raw_text == "Planetary Governor @\"High Duke Gene Marte\" of #\"Mani's Stand\" calls the characters  with a problem but it is top secret and he will not tell them anything until their discretion is assured.  \n\n1. Message from the Governor direct, but how to answer?\n2. Governors Secretary @\"Earl Jerey Parkell\" considers the characters to low brow, how to get to the governor\n3. No help, Police Chief @\"Sir Juany Ramas\" is in on it and arrest them for lesse majesty towards the governor, forgery, etc.\n4. The big plan, Play by ear.\n5. Mission, goto the robofac, @\"Duke Tery Warder\" has produced very little in 2 months, find out why and fix it.  The Duke has been an enemy of the High Duke for the last two years, but they were allies in the past.\n\n*\"5RD1-1-5\""


def test_parse_campaign_entry_from_fixture_tag_value_fallback():
    fixture_path = os.path.join(os.path.dirname(__file__), "fixtures", "campaign_entry_title.json")
    with open(fixture_path, "r") as f:
        data = json.load(f)["data"]

    client = LoggerClient()
    entry = client._parse_campaign_entry(data)

    assert entry.id == "482162d944a24c379202e52541f14bcb"
    assert entry.campaign_id == "535738ede60447209b9bb5c1e364a92a"
    assert entry.raw_text == "# Your ~\"Deadly Secret\" for which you would surely be killed\n\nEach character must have a deadly secret for which they would surely be killed.  If your secret becomes generally known you will surely be killed, probably by King @\"Ivan Constanavich\" but maybe by someone else powerful and inevitable.  This obviously includes being a traitor in his court and any crimes that would normally be taken seriously, but beyond that there are many reasons why the king might find you \"fatally inconvenient.\"  Some deadly secrets include\n\n## Being an agent of a foreign party\n\nTreason leads to death, if you are working for someone else against #\"Cock A Knee\".  Certain public relationships may be ok, but secret agents are very much subject to being shot at dawn.\n\nSome factions you might consider being secretly aligned with include:\n\n  - the #\"Coalition States\"\n  - the ^\"Black Market\"\n  - #\"The Federation Of Magic\"\n  - the ^\"Native American\" tribes\n  - Corporate factions such as ^\"Northern Gun\", ^\"Titan Robotics\", or ^\"Wilk's\"\n  - Extra-dimensional Powers such as the ^Atlanteans, ^Splugorth, ^Demons of #Hades, or ^Deevils of #Dyval\n\n## Having \"Illegal abilities\" \n\nIn the future of Rifts earth tolerance is not in great supply, the #\"Coalition States\" are famously intolerant and in some cases it is important for him to adopt some of their policies in order to receive !\"Foreign Aid\" and not be counted as an enemy.  Of course this is not limited to the #\"Coalition States\", #\"Tolkeen\" considers certain magics dangerous, #\"The Federation Of Magic\" wants to control magic knowledge, etc. etc.\n\n  - Psychic Powers\n  - Magic\n  - a particular kind of magic like Necromancy, Elementalism, Native American magic\n  - Magic outside the guild\n  - Juicer, Bionic, or Mind over Matter(Crazy) enhancement\n\n## Criminal history\n\nLife in Rifts Earth is nasty brutish and short, imprisoning people for long intervals is not a thing that #\"Cock A Knee\" can afford, serious crimes are generally sentences of exile or death.  \n\n  - Desertion from an allied army\n  - Murder\n  - Ever-so-grand larceny\n   - Drug, monster, or human trafficking \n\n__Note__ if your secret is a crime, you definitely did it, there will be no sub-plot of finding the real killer.  Of course you can write a false accusation into your backstory too if you want.\n\n## Other Deadly Secrets\nPossibly you have done nothing wrong, but if you you know or have done ever gets out you will surely be killed.\n\nPerhaps:\n* you have information about the King or Kingdom committing crimes, perhaps you were there when the King used a magic artifact to win a battle\n* some other group wants you dead and the King wants their help\n* you know that a high ^\"Noble\" is a traitor and you would be killed to prevent your __true__ accusations\n* you are hunted by ^\"Black Market\" or ^Sunaj assassins and only protected by your false identity\n\n# Other Character's Secrets\n\nYou will also be given a couple secrets that you would probably tolerate and a couple secrets that you would consider especially heinous.  Until your characters have built up a strong bond of trust revealing a secret to another character is a deadly risk; they may reveal it, blackmail you, or let it go.  If they do reveal it you will need a new character.  You should only reveal your secret if it is a matter of desperate need **and** you trust whoever you reveal it to."


def test_parse_log_entry_relationships():
    payload = {
        "attributes": {
            "raw-text": "Some text",
        },
        "relationships": {"log": {"data": {"type": "logs", "id": "rel_log_id"}}},
        "type": "log-entries",
        "id": "e_id",
    }

    client = LoggerClient()
    entry = client._parse_log_entry(payload)
    assert entry.log_id == "rel_log_id"


def test_parse_campaign_entry_relationships():
    payload = {
        "attributes": {
            "raw-text": "Some text",
        },
        "relationships": {"campaign": {"data": {"type": "campaigns", "id": "rel_campaign_id"}}},
        "type": "campaign-entries",
        "id": "ce_id",
    }

    client = LoggerClient()
    entry = client._parse_campaign_entry(payload)
    assert entry.campaign_id == "rel_campaign_id"


def test_parse_log_relationships():
    payload = {
        "attributes": {
            "title": "Some text",
        },
        "relationships": {"campaign": {"data": {"type": "campaigns", "id": "rel_campaign_id"}}},
        "type": "logs",
        "id": "l_id",
    }

    client = LoggerClient()
    log_obj = client._parse_log(payload)
    assert log_obj.campaign_id == "rel_campaign_id"

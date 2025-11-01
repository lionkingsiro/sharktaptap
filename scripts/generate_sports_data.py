#!/usr/bin/env python3
"""Generate comprehensive AllSport data set from ESPN public APIs.

The script fetches league, team, player, and venue data for the NFL, NBA,
MLB, and NHL, normalises the responses, applies curated overrides for
featured stadiums and star players, then writes a consumable
`data/sports-data.js` bundle for the front-end app.

Run: `python3 scripts/generate_sports_data.py`
"""

from __future__ import annotations

import json
import sys
import time
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_PATH = BASE_DIR / "data" / "sports-data.js"

USER_AGENT = "AllSportDataGenerator/1.0 (+https://allsport.app)"


def debug(msg: str) -> None:
    print(msg, file=sys.stderr)


class Fetcher:
    """Thin caching wrapper around urllib."""

    def __init__(self) -> None:
        self.cache: Dict[str, Any] = {}

    def get(self, url: str, *, retries: int = 3, delay: float = 0.08) -> Any:
        if url in self.cache:
            return self.cache[url]

        for attempt in range(retries):
            try:
                req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
                with urllib.request.urlopen(req, timeout=30) as resp:
                    data = json.load(resp)
                    self.cache[url] = data
                    time.sleep(delay)
                    return data
            except Exception as exc:  # pragma: no cover - network dependent
                if attempt == retries - 1:
                    raise RuntimeError(f"Failed to fetch {url}: {exc}") from exc
                time.sleep(delay * (attempt + 1))


fetcher = Fetcher()


@dataclass
class StatSelector:
    category: str
    field: str
    label: str
    description: str


@dataclass
class LeagueConfig:
    id: str
    sport: str
    league: str
    name: str
    short_name: str
    icon: str
    founded: Optional[int]
    teams_count: int
    roster_limit: int
    stat_selectors: List[StatSelector]
    feature_sections: List[str] = field(default_factory=list)


LEAGUES: List[LeagueConfig] = [
    LeagueConfig(
        id="nfl",
        sport="football",
        league="nfl",
        name="National Football League",
        short_name="NFL",
        icon="football",
        founded=1920,
        teams_count=32,
        roster_limit=20,
        stat_selectors=[
            StatSelector("scoring", "totalPointsPerGame", "Points/Game", "Average points scored per game"),
            StatSelector("passing", "yardsPerGame", "Pass Yards/Game", "Passing yards gained per game"),
            StatSelector("rushing", "yardsPerGame", "Rush Yards/Game", "Rushing yards gained per game"),
            StatSelector("defensive", "sacks", "Sacks", "Total sacks recorded"),
            StatSelector("miscellaneous", "totalTakeaways", "Takeaways", "Total turnovers forced"),
            StatSelector("miscellaneous", "turnOverDifferential", "Turnover Diff", "Giveaway versus takeaway differential"),
        ],
        feature_sections=["Offense", "Defense", "Special Teams"],
    ),
    LeagueConfig(
        id="nba",
        sport="basketball",
        league="nba",
        name="National Basketball Association",
        short_name="NBA",
        icon="basketball",
        founded=1946,
        teams_count=30,
        roster_limit=18,
        stat_selectors=[
            StatSelector("general", "avgPoints", "Points/Game", "Points scored per game"),
            StatSelector("general", "avgAssists", "Assists/Game", "Team assists per game"),
            StatSelector("general", "avgRebounds", "Rebounds/Game", "Total rebounds per game"),
            StatSelector("offensive", "threePointPct", "3PT%", "Team three-point percentage"),
            StatSelector("defensive", "avgBlocks", "Blocks/Game", "Blocks recorded per game"),
        ],
        feature_sections=["Pace & Space", "Half Court Execution", "Defensive Identity"],
    ),
    LeagueConfig(
        id="mlb",
        sport="baseball",
        league="mlb",
        name="Major League Baseball",
        short_name="MLB",
        icon="baseball",
        founded=1903,
        teams_count=30,
        roster_limit=28,
        stat_selectors=[
            StatSelector("batting", "avg", "AVG", "Team batting average"),
            StatSelector("batting", "runs", "Runs", "Runs scored this season"),
            StatSelector("batting", "homeRuns", "Home Runs", "Total home runs"),
            StatSelector("pitching", "ERA", "Team ERA", "Earned run average"),
            StatSelector("pitching", "strikeouts", "Strikeouts", "Pitching strikeouts"),
        ],
        feature_sections=["Lineup Depth", "Bullpen Snapshot", "Farm System"],
    ),
    LeagueConfig(
        id="nhl",
        sport="hockey",
        league="nhl",
        name="National Hockey League",
        short_name="NHL",
        icon="hockey",
        founded=1917,
        teams_count=32,
        roster_limit=22,
        stat_selectors=[
            StatSelector("offensive", "goals", "Goals", "Total goals scored"),
            StatSelector("offensive", "points", "Points", "Total points (goals + assists)"),
            StatSelector("defensive", "avgGoalsAgainst", "GA/Game", "Goals allowed per game"),
            StatSelector("defensive", "savePct", "Save %", "Save percentage"),
            StatSelector("offensive", "powerPlayGoals", "PP Goals", "Power play goals"),
            StatSelector("penalties", "penaltyMinutes", "Penalty Minutes", "Time spent in the box"),
        ],
        feature_sections=["Top Line", "Goaltending", "Special Teams"],
    ),
]


STAR_PLAYER_OVERRIDES: Dict[str, Dict[str, Any]] = {
    "1966": {  # LeBron James
        "tagline": "Four-time NBA Champion & MVP rewriting longevity records.",
        "notables": [
            "19x All-Star",
            "4x Finals MVP",
            "NBA All-Time Scoring Leader",
        ],
        "careerTimeline": [
            {"year": 2004, "event": "NBA Rookie of the Year"},
            {"year": 2012, "event": "First NBA Championship with the Miami Heat"},
            {"year": 2016, "event": "Delivers Cleveland Cavaliers their first title"},
            {"year": 2020, "event": "Wins championship and Finals MVP with the Lakers"},
        ],
        "featuredStats": {
            "PPG": 25.7,
            "RPG": 7.3,
            "APG": 8.3,
            "FG%": 0.540,
        },
        "bio": {
            "height": "6'9\" (206 cm)",
            "weight": "250 lbs (113 kg)",
            "born": "Dec 30, 1984 (39 years)",
            "nationality": "American",
            "draft": "2003, Round 1, Pick 1",
        },
    },
    "3975": {  # Stephen Curry
        "tagline": "Greatest shooter ever, redefining spacing and pace.",
        "notables": [
            "4x NBA Champion",
            "2x MVP",
            "NBA record 3-pointers",
        ],
        "featuredStats": {"PPG": 26.4, "APG": 5.1, "3P%": 0.421},
    },
    "14881": {  # Patrick Mahomes
        "tagline": "Back-to-back Super Bowl champion with video-game numbers.",
        "notables": [
            "2x NFL MVP",
            "3x Super Bowl Champion",
            "3x Super Bowl MVP",
        ],
        "featuredStats": {"PassYds": 4560, "PassTD": 35, "QBR": 73.6},
    },
    "34886": {  # Shohei Ohtani
        "tagline": "Two-way sensation reshaping modern baseball.",
        "notables": [
            "2021 & 2023 AL MVP",
            "First player to qualify as pitcher and hitter in same season",
        ],
        "featuredStats": {"AVG": .312, "HR": 44, "OPS": 1.066, "ERA": 3.14},
    },
    "3990": {  # Connor McDavid
        "tagline": "Generational talent with unmatched acceleration and edge control.",
        "notables": ["3x Hart Trophy", "5x Art Ross Trophy"],
        "featuredStats": {"PTS": 132, "G": 44, "A": 88},
    },
    "1627759": {  # Nikola Jokic
        "tagline": "Do-it-all center powering the Nuggets' motion offense.",
        "featuredStats": {"PPG": 26.8, "RPG": 12.4, "APG": 9.0},
    },
    "6478": {  # Aaron Judge
        "tagline": "Towering slugger with transcendent power and leadership.",
        "featuredStats": {"AVG": .293, "HR": 62, "RBI": 131},
    },
    "178960": {  # Auston Matthews
        "tagline": "Elite goal-scorer with a lethal release.",
        "featuredStats": {"G": 69, "PTS": 107},
    },
}


STADIUM_OVERRIDES: Dict[str, Dict[str, Any]] = {
    "stadium-4019": {
        "description": "SoFi Stadium is the NFL's first indoor-outdoor venue with a translucent roof and a stunning Infinity Screen hanging over the field.",
        "history": [
            {"title": "Groundbreaking", "detail": "Construction began in 2016 as part of a 298-acre mixed-use development."},
            {"title": "Opening", "detail": "Opened in 2020 for the Los Angeles Rams and Chargers."},
            {"title": "Super Bowl LVI", "detail": "Hosted Super Bowl LVI in February 2022."},
        ],
        "architecture": [
            "Designed by HKS with sweeping canopies and a climate-friendly ETFE roof.",
            "Features the 360-degree double-sided Infinity Screen by Samsung.",
            "Seismic base isolation protects the structure from earthquakes.",
        ],
        "images": [
            "https://images.unsplash.com/photo-1602016667925-18be89a9736a?auto=format&fit=crop&w=1600&q=80",
            "https://images.unsplash.com/photo-1602006702246-054c27cfe20f?auto=format&fit=crop&w=1600&q=80",
        ],
    },
    "stadium-336": {
        "description": "Madison Square Garden is the world's most famous arena, home to iconic moments in basketball, hockey, boxing, and music.",
        "history": [
            {"title": "Opened", "detail": "Debuted in 1968 atop Pennsylvania Station in Midtown Manhattan."},
            {"title": "Renovations", "detail": "Completed a $1B top-to-bottom transformation in 2013."},
        ],
        "architecture": [
            "Circular bowl design with sky bridges overlooking the floor.",
            "Signature LED ceiling and IPTV system for immersive experiences.",
        ],
        "images": [
            "https://images.unsplash.com/photo-1469474968028-56623f02e42e?auto=format&fit=crop&w=1600&q=80",
        ],
    },
    "stadium-3": {
        "description": "Fenway Park is MLB's oldest ballpark, famous for the Green Monster and intimate sightlines.",
        "history": [
            {"title": "Opened", "detail": "The Boston Red Sox christened Fenway Park in 1912."},
            {"title": "Renovations", "detail": "A series of restorations preserved the park's charm while adding modern amenities."},
        ],
        "architecture": [
            "Quirky dimensions including the 37-foot Green Monster in left field.",
            "Manual scoreboard operated from inside the wall.",
        ],
        "images": [
            "https://images.unsplash.com/photo-1508098682722-e99c43a406b2?auto=format&fit=crop&w=1600&q=80",
        ],
    },
    "stadium-21": {
        "description": "Lambeau Field blends historic charm with modern amenities and is revered for the 'Frozen Tundra'.",
        "history": [
            {"title": "Opened", "detail": "The Packers debuted at then-City Stadium in 1957."},
            {"title": "Renamed", "detail": "Renamed Lambeau Field in 1965 to honor founder Curly Lambeau."},
        ],
        "architecture": [
            "A bowl design with seating expansions now beyond 80,000.",
            "Titletown District adds restaurants, sledding hill, and skating trail.",
        ],
        "images": [
            "https://images.unsplash.com/photo-1559060014-7d61e27f27c7?auto=format&fit=crop&w=1600&q=80",
        ],
    },
    "stadium-388": {
        "description": "Chase Center anchors San Francisco's Mission Bay with cutting-edge LED displays and fan concourses overlooking the bay.",
        "images": [
            "https://images.unsplash.com/photo-1587089879241-7d6f1afad79e?auto=format&fit=crop&w=1600&q=80",
        ],
    },
    "stadium-5": {
        "description": "Yankee Stadium honors its Bronx legacy with Monument Park and expansive concourses.",
        "images": [
            "https://images.unsplash.com/photo-1507842217343-583bb7270b66?auto=format&fit=crop&w=1600&q=80",
        ],
    },
    "stadium-25": {
        "description": "Dodger Stadium offers sweeping views of downtown L.A. and mountains, pairing mid-century design with modern plazas.",
    },
    "stadium-4009": {
        "description": "T-Mobile Arena delivers a party atmosphere on the Vegas Strip with dazzling pregame shows for the Golden Knights.",
    },
    "stadium-61": {
        "description": "United Center is the largest arena in the U.S., known for the Bulls and Blackhawks championship eras.",
    },
    "stadium-28": {
        "description": "AT&T Stadium pairs a colossal video board with art installations and a retractable roof.",
    },
    "stadium-3602": {
        "description": "Climate Pledge Arena is the world's first net zero certified arena with an iconic sloped roof.",
    },
    "stadium-3780": {
        "description": "Euro-style Ball Arena in Denver hosts the Nuggets and Avalanche with versatile lighting and acoustics.",
    },
    "stadium-110": {
        "description": "PNC Park boasts postcard views of Pittsburgh's skyline and Roberto Clemente Bridge.",
    },
    "stadium-31": {
        "description": "Wrigley Field is famed for ivy-covered walls, rooftop seating, and seventh-inning traditions.",
    },
}


def build_category_map(stats: Dict[str, Any]) -> Dict[Tuple[str, str], Dict[str, Any]]:
    mapping: Dict[Tuple[str, str], Dict[str, Any]] = {}
    if not stats:
        return mapping

    for category in stats.get("categories", []):
        cat_name = category.get("name")
        for stat in category.get("stats", []):
            key = (cat_name, stat.get("name"))
            mapping[key] = stat
            if stat.get("shortDisplayName"):
                mapping[(cat_name, stat["shortDisplayName"])] = stat
            if stat.get("displayName"):
                mapping[(cat_name, stat["displayName"])] = stat
    return mapping


def extract_stats(raw_stats: Dict[str, Any], selectors: Iterable[StatSelector]) -> List[Dict[str, Any]]:
    stats_map = build_category_map(raw_stats)
    bundle: List[Dict[str, Any]] = []
    for selector in selectors:
        stat = stats_map.get((selector.category, selector.field))
        value = stat.get("displayValue") if stat else "-"
        bundle.append(
            {
                "label": selector.label,
                "category": selector.category,
                "field": selector.field,
                "value": value,
                "description": selector.description,
            }
        )
    return bundle


def format_address(address: Dict[str, Any]) -> str:
    parts = [
        address.get("address1"),
        address.get("city"),
        address.get("state"),
        address.get("zipCode"),
        address.get("country"),
    ]
    return ", ".join([p for p in parts if p])


def fetch_team_schedule(sport: str, league: str, team_id: str) -> Dict[str, List[Dict[str, Any]]]:
    schedule_url = f"https://site.api.espn.com/apis/site/v2/sports/{sport}/{league}/teams/{team_id}/schedule"
    data = fetcher.get(schedule_url)
    events = data.get("events", [])
    previous: List[Dict[str, Any]] = []
    upcoming: List[Dict[str, Any]] = []
    for event in events:
        competitions = event.get("competitions", [])
        if not competitions:
            continue
        comp = competitions[0]
        status = comp.get("status", {}).get("type", {})
        is_completed = status.get("completed")
        for competitor in comp.get("competitors", []):
            if competitor.get("id") == team_id:
                is_home = competitor.get("homeAway") == "home"
                team_score = competitor.get("score")
                opponent = next(
                    (
                        {
                            "id": opp.get("id"),
                            "name": opp.get("team", {}).get("displayName", opp.get("displayName")),
                            "logo": (opp.get("team", {}).get("logo") or opp.get("team", {}).get("logos", [{}])[0].get("href")),
                        }
                        for opp in comp.get("competitors", [])
                        if opp is not competitor
                    ),
                    None,
                )
                entry = {
                    "id": event.get("id"),
                    "date": event.get("date"),
                    "name": event.get("name"),
                    "shortName": event.get("shortName"),
                    "home": is_home,
                    "venue": comp.get("venue", {}).get("fullName"),
                    "status": status.get("description"),
                    "completed": is_completed,
                    "teamScore": team_score,
                    "opponentScore": next(
                        (opp.get("score") for opp in comp.get("competitors", []) if opp is not competitor),
                        None,
                    ),
                    "broadcast": next(
                        (note.get("text") for note in comp.get("notes", []) if note.get("type") == "Broadcast"),
                        None,
                    ),
                    "tickets": comp.get("tickets"),
                    "opponent": opponent,
                    "links": [link.get("href") for link in event.get("links", []) if link.get("isExternal")],
                }
                if is_completed:
                    previous.append(entry)
                else:
                    upcoming.append(entry)
                break
    previous = sorted(previous, key=lambda item: item.get("date"), reverse=True)[:5]
    upcoming = sorted(upcoming, key=lambda item: item.get("date"))[:5]
    return {"previous": previous, "upcoming": upcoming}


def fetch_roster(sport: str, league: str, team_id: str, limit: int) -> List[Dict[str, Any]]:
    roster_url = f"https://site.api.espn.com/apis/site/v2/sports/{sport}/{league}/teams/{team_id}/roster"
    data = fetcher.get(roster_url)
    roster: List[Dict[str, Any]] = []
    for bucket in data.get("athletes", []):
        items = bucket.get("items", [])
        for item in items:
            player = item.get("player", {})
            roster.append(
                {
                    "playerId": player.get("id"),
                    "fullName": player.get("fullName"),
                    "position": player.get("position", {}).get("displayName"),
                    "abbreviation": player.get("position", {}).get("abbreviation"),
                    "jersey": player.get("jersey"),
                    "age": player.get("age"),
                    "height": player.get("displayHeight"),
                    "weight": player.get("displayWeight"),
                    "experience": (player.get("experience", {}) or {}).get("years"),
                    "status": (player.get("status", {}) or {}).get("type"),
                    "headshot": player.get("headshot", {}).get("href"),
                    "college": (player.get("college") or {}).get("name"),
                    "country": (player.get("birthPlace") or {}).get("country"),
                    "birthPlace": {
                        "city": (player.get("birthPlace") or {}).get("city"),
                        "state": (player.get("birthPlace") or {}).get("state"),
                        "country": (player.get("birthPlace") or {}).get("country"),
                    },
                    "links": player.get("links", []),
                }
            )
    roster.sort(key=lambda r: (r.get("position") or "", r.get("jersey") or ""))
    return roster[:limit]


def enrich_player(player_data: Dict[str, Any], team_meta: Dict[str, Any], players_index: Dict[str, Any]) -> None:
    player_id = player_data.get("playerId")
    if not player_id:
        return

    record = players_index.setdefault(
        player_id,
        {
            "id": player_id,
            "fullName": player_data.get("fullName"),
            "headshot": player_data.get("headshot"),
            "position": player_data.get("position"),
            "team": {
                "id": team_meta["id"],
                "name": team_meta["name"],
                "leagueId": team_meta["leagueId"],
            },
            "bio": {
                "height": player_data.get("height"),
                "weight": player_data.get("weight"),
                "age": player_data.get("age"),
                "experience": player_data.get("experience"),
                "college": player_data.get("college"),
                "country": player_data.get("country"),
            },
            "links": player_data.get("links", []),
            "tagline": None,
            "featuredStats": None,
        },
    )

    override = STAR_PLAYER_OVERRIDES.get(player_id)
    if override:
        record.update(override)


def collect_coach(team_core: Dict[str, Any]) -> Optional[str]:
    coaches_ref = (team_core.get("coaches") or {}).get("$ref")
    if not coaches_ref:
        return None
    data = fetcher.get(coaches_ref)
    for item in data.get("items", []):
        coach_data = fetcher.get(item.get("$ref"))
        if coach_data.get("type", {}).get("name") == "Head Coach" or coach_data.get("type", {}).get("abbreviation") == "HC":
            person = coach_data.get("coach") or {}
            if person:
                return person.get("displayName") or person.get("fullName")
    return None


def collect_division(team_core: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
    groups_ref = (team_core.get("groups") or {}).get("$ref")
    if not groups_ref:
        return None, None
    division_data = fetcher.get(groups_ref)
    division_name = division_data.get("name")
    parent_ref = (division_data.get("parent") or {}).get("$ref")
    conference_name = None
    if parent_ref:
        conference_data = fetcher.get(parent_ref)
        conference_name = conference_data.get("name")
    return conference_name, division_name


def collect_record(team_site: Dict[str, Any]) -> Optional[str]:
    record = (team_site.get("team") or {}).get("record", {})
    items = record.get("items") or []
    if items:
        return items[0].get("summary")
    return None


def collect_statistics(sport: str, league: str, team_id: str) -> Dict[str, Any]:
    stats_url = f"https://site.api.espn.com/apis/site/v2/sports/{sport}/{league}/teams/{team_id}/statistics"
    data = fetcher.get(stats_url)
    return (data.get("results") or {}).get("stats") or {}


def collect_franchise(team_core: Dict[str, Any]) -> Dict[str, Any]:
    franchise_ref = (team_core.get("franchise") or {}).get("$ref")
    if not franchise_ref:
        return {}
    franchise = fetcher.get(franchise_ref)
    championships = (franchise.get("championships") or {}).get("total")
    return {
        "founded": franchise.get("yearFounded"),
        "championships": championships,
    }


def collect_venue(team_core: Dict[str, Any], team_id: str, league_id: str, stadium_index: Dict[str, Any]) -> Optional[str]:
    venue_ref = (team_core.get("venue") or {}).get("$ref")
    if not venue_ref:
        return None
    venue = fetcher.get(venue_ref)
    stadium_id = f"stadium-{venue.get('id')}"
    entry = stadium_index.setdefault(
        stadium_id,
        {
            "id": stadium_id,
            "venueId": venue.get("id"),
            "name": venue.get("fullName") or venue.get("name"),
            "nickname": venue.get("shortName"),
            "capacity": venue.get("capacity"),
            "surface": venue.get("grass") or venue.get("surface"),
            "roofType": venue.get("roofType"),
            "location": venue.get("address", {}).get("city"),
            "address": format_address(venue.get("address", {})),
            "coordinates": venue.get("geoCoordinates"),
            "images": [img.get("href") for img in venue.get("images", []) if img.get("href")],
            "teams": [],
            "description": None,
            "history": [],
            "architecture": [],
        },
    )
    entry.setdefault("teams", []).append({"teamId": team_id, "leagueId": league_id})
    override = STADIUM_OVERRIDES.get(stadium_id)
    if override:
        entry.update({k: v for k, v in override.items() if v})
    return stadium_id


def build_league_payload(config: LeagueConfig, stadium_index: Dict[str, Any], players_index: Dict[str, Any]) -> Dict[str, Any]:
    debug(f"Processing {config.name}...")
    teams_endpoint = f"https://sports.core.api.espn.com/v2/sports/{config.sport}/leagues/{config.league}/teams?limit=200"
    teams_data = fetcher.get(teams_endpoint)
    team_items = teams_data.get("items", [])
    teams_payload: List[Dict[str, Any]] = []

    for item in team_items:
        team_core = fetcher.get(item.get("$ref"))
        team_id = team_core.get("id")
        if not team_id:
            continue

        site_team = fetcher.get(
            f"https://site.api.espn.com/apis/site/v2/sports/{config.sport}/{config.league}/teams/{team_id}"
        )

        conference, division = collect_division(team_core)
        stadium_id = collect_venue(team_core, team_id, config.id, stadium_index)
        franchise_meta = collect_franchise(team_core)
        coach = collect_coach(team_core)
        record_summary = collect_record(site_team)
        stats_raw = collect_statistics(config.sport, config.league, team_id)
        stats_bundle = extract_stats(stats_raw, config.stat_selectors)
        schedule = fetch_team_schedule(config.sport, config.league, team_id)
        roster = fetch_roster(config.sport, config.league, team_id, config.roster_limit)

        team_payload = {
            "id": f"{config.id}-{team_core.get('slug') or team_id}",
            "sourceId": team_id,
            "leagueId": config.id,
            "name": team_core.get("displayName"),
            "shortName": team_core.get("shortDisplayName"),
            "nickname": team_core.get("nickname"),
            "location": team_core.get("location"),
            "abbreviation": team_core.get("abbreviation"),
            "colors": {
                "primary": f"#{team_core.get('color')}" if team_core.get("color") else None,
                "secondary": f"#{team_core.get('alternateColor')}" if team_core.get("alternateColor") else None,
            },
            "logos": [logo.get("href") for logo in team_core.get("logos", []) if logo.get("href")],
            "conference": conference,
            "division": division,
            "record": record_summary,
            "standingSummary": (site_team.get("team") or {}).get("standingSummary"),
            "coach": coach,
            "stadiumId": stadium_id,
            "founded": franchise_meta.get("founded") or config.founded,
            "championships": franchise_meta.get("championships"),
            "stats": stats_bundle,
            "schedule": schedule,
            "roster": roster,
            "featureSections": config.feature_sections,
        }

        for player in roster:
            enrich_player(player, team_payload, players_index)

        teams_payload.append(team_payload)

    return {
        "id": config.id,
        "name": config.name,
        "shortName": config.short_name,
        "icon": config.icon,
        "founded": config.founded,
        "teams": teams_payload,
    }


def main() -> None:
    stadium_index: Dict[str, Any] = {}
    players_index: Dict[str, Any] = {}
    leagues_payload: List[Dict[str, Any]] = []

    for league_config in LEAGUES:
        leagues_payload.append(build_league_payload(league_config, stadium_index, players_index))

    dataset = {
        "generatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "leagues": leagues_payload,
        "players": players_index,
        "stadiums": list(stadium_index.values()),
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    js_content = "// Auto-generated by scripts/generate_sports_data.py\n" "const SPORTS_DATA = " + json.dumps(dataset, indent=2) + ";\n" "if (typeof window !== 'undefined') { window.SPORTS_DATA = SPORTS_DATA; }\n" "export default SPORTS_DATA;\n"

    OUTPUT_PATH.write_text(js_content, encoding="utf-8")
    debug(f"Wrote data bundle to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()

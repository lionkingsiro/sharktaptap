(() => {
  const appRoot = document.getElementById('app');
  const DATA = window.SPORTS_DATA || { leagues: [], players: {}, stadiums: [] };

  const leagueIndex = new Map();
  const teamIndex = new Map();
  const stadiumIndex = new Map();

  DATA.leagues.forEach((league) => {
    leagueIndex.set(league.id, league);
    (league.teams || []).forEach((team) => {
      teamIndex.set(team.id, { ...team, league });
    });
  });

  (DATA.stadiums || []).forEach((stadium) => {
    stadiumIndex.set(stadium.id, stadium);
  });

  const AppState = {
    view: 'home',
    selectedLeagueId: null,
    selectedTeamId: null,
    selectedPlayerId: null,
    selectedStadiumId: null,
    teamTab: 'overview',
    playerTab: 'overview',
    stadiumTab: 'general',
    filters: {
      search: '',
      conference: 'All',
      division: 'All',
    },
    history: [],
  };

  const copyState = () => ({
    view: AppState.view,
    selectedLeagueId: AppState.selectedLeagueId,
    selectedTeamId: AppState.selectedTeamId,
    selectedPlayerId: AppState.selectedPlayerId,
    selectedStadiumId: AppState.selectedStadiumId,
    teamTab: AppState.teamTab,
    playerTab: AppState.playerTab,
    stadiumTab: AppState.stadiumTab,
    filters: { ...AppState.filters },
  });

  const restoreState = (snapshot) => {
    if (!snapshot) return;
    Object.assign(AppState, {
      view: snapshot.view,
      selectedLeagueId: snapshot.selectedLeagueId,
      selectedTeamId: snapshot.selectedTeamId,
      selectedPlayerId: snapshot.selectedPlayerId,
      selectedStadiumId: snapshot.selectedStadiumId,
      teamTab: snapshot.teamTab,
      playerTab: snapshot.playerTab,
      stadiumTab: snapshot.stadiumTab,
      filters: { ...snapshot.filters },
    });
  };

  const navigate = (view, options = {}) => {
    AppState.history.push(copyState());
    Object.assign(AppState, { view, ...options });
    render();
  };

  const goBack = () => {
    if (!AppState.history.length) {
      AppState.view = 'home';
      AppState.selectedLeagueId = null;
      AppState.selectedTeamId = null;
      AppState.selectedPlayerId = null;
      AppState.selectedStadiumId = null;
      AppState.teamTab = 'overview';
      AppState.playerTab = 'overview';
      AppState.filters = { search: '', conference: 'All', division: 'All' };
      render();
      return;
    }
    const snapshot = AppState.history.pop();
    restoreState(snapshot);
    render();
  };

  const formatDate = (iso, fmt = 'MMM D, YYYY') => {
    if (!iso) return 'TBD';
    return dayjs(iso).tz(dayjs.tz.guess()).format(fmt);
  };

  const formatTime = (iso) => {
    if (!iso) return '';
    return dayjs(iso).tz(dayjs.tz.guess()).format('h:mm A');
  };

  const formatRecord = (record) => record || 'Record N/A';

  const createTopBar = (title, options = {}) => {
    const { showBack = true, subtitle = null, actions = '' } = options;
    return `
      <header class="top-app-bar">
        ${showBack ? `<button class="icon-button" data-action="back" aria-label="Back"><span>&larr;</span></button>` : ''}
        <div>
          <h1>${title}</h1>
          ${subtitle ? `<p class="badge">${subtitle}</p>` : ''}
        </div>
        <div style="margin-left:auto;display:flex;gap:.5rem;">${actions}</div>
      </header>
    `;
  };

  const renderHome = () => {
    const leagueCards = DATA.leagues
      .map(
        (league) => `
          <article class="league-card" data-league="${league.id}">
            <div class="league-icon">${league.icon.slice(0, 3).toUpperCase()}</div>
            <div>
              <h2>${league.shortName}</h2>
              <p class="placeholder">${league.name}</p>
            </div>
          </article>
        `
      )
      .join('');

    appRoot.innerHTML = `
      ${createTopBar('AllSport', { showBack: false, subtitle: 'Comprehensive Pro Sports Hub' })}
      <section>
        <p class="placeholder">Select a league to explore rosters, stats, stadiums, and schedules.</p>
        <div class="league-grid">${leagueCards}</div>
        <button class="primary-button" data-action="open-schedule">View Live Schedules</button>
      </section>
    `;

    appRoot.querySelectorAll('.league-card').forEach((card) => {
      card.addEventListener('click', () => {
        const leagueId = card.dataset.league;
        AppState.filters = { search: '', conference: 'All', division: 'All' };
        navigate('teams', { selectedLeagueId: leagueId });
      });
    });

    const scheduleBtn = appRoot.querySelector('[data-action="open-schedule"]');
    if (scheduleBtn) {
      scheduleBtn.addEventListener('click', () => navigate('schedule'));
    }
  };

  const renderTeamsList = () => {
    const league = leagueIndex.get(AppState.selectedLeagueId);
    if (!league) {
      goBack();
      return;
    }

    const conferences = ['All'];
    const divisions = ['All'];
    league.teams.forEach((team) => {
      if (team.conference && !conferences.includes(team.conference)) {
        conferences.push(team.conference);
      }
      if (team.division && !divisions.includes(team.division)) {
        divisions.push(team.division);
      }
    });

    const searchValue = AppState.filters.search.toLowerCase();
    const filteredTeams = league.teams.filter((team) => {
      const matchesSearch = !searchValue || team.name.toLowerCase().includes(searchValue) || team.nickname.toLowerCase().includes(searchValue) || team.location.toLowerCase().includes(searchValue);
      const matchesConference = AppState.filters.conference === 'All' || team.conference === AppState.filters.conference;
      const matchesDivision = AppState.filters.division === 'All' || team.division === AppState.filters.division;
      return matchesSearch && matchesConference && matchesDivision;
    });

    const teamCards = filteredTeams
      .map(
        (team) => `
          <article class="team-card" data-team="${team.id}">
            <div class="team-logo">${team.abbreviation}</div>
            <div class="team-info">
              <h3>${team.name}</h3>
              <span>${team.location} / ${team.division || 'Division TBD'}</span>
              <span>${formatRecord(team.record)}</span>
            </div>
          </article>
        `
      )
      .join('');

    const filterChips = (items, active, type) =>
      items
        .map(
          (label) => `
          <button class="filter-chip ${active === label ? 'active' : ''}" data-filter="${type}" data-value="${label}">${label}</button>
        `
        )
        .join('');

    appRoot.innerHTML = `
      ${createTopBar(league.shortName, { subtitle: `${league.teams.length} Teams`, actions: '<button class="icon-button" data-action="schedule" aria-label="Schedule">Schedule</button>' })}
      <section class="search-filter">
        <input type="search" placeholder="Search teams..." value="${AppState.filters.search}" />
        <div>
          <p class="placeholder" style="margin:0 0 .35rem;">Conference</p>
          <div class="chip-row">${filterChips(conferences, AppState.filters.conference, 'conference')}</div>
        </div>
        <div>
          <p class="placeholder" style="margin:0 0 .35rem;">Division</p>
          <div class="chip-row">${filterChips(divisions, AppState.filters.division, 'division')}</div>
        </div>
      </section>
      <section class="team-list">
        ${teamCards || '<div class="empty-state">No teams match the current filters.</div>'}
      </section>
    `;

    const searchInput = appRoot.querySelector('input[type="search"]');
    searchInput.addEventListener('input', (event) => {
      AppState.filters.search = event.target.value;
      renderTeamsList();
    });

    appRoot.querySelectorAll('.filter-chip').forEach((chip) => {
      chip.addEventListener('click', () => {
        const type = chip.dataset.filter;
        const value = chip.dataset.value;
        AppState.filters[type] = value;
        renderTeamsList();
      });
    });

    appRoot.querySelectorAll('.team-card').forEach((card) => {
      card.addEventListener('click', () => {
        const teamId = card.dataset.team;
        navigate('team-detail', { selectedTeamId: teamId, teamTab: 'overview' });
      });
    });

    const scheduleBtn = appRoot.querySelector('[data-action="schedule"]');
    if (scheduleBtn) {
      scheduleBtn.addEventListener('click', () => navigate('schedule'));
    }

    const backButton = appRoot.querySelector('[data-action="back"]');
    if (backButton) backButton.addEventListener('click', goBack);
  };

  const renderTeamOverviewTab = (team) => {
    const topPlayers = (team.roster || []).slice(0, 3);
    const schedule = team.schedule || { previous: [], upcoming: [] };
    const lastGame = schedule.previous[0];
    const nextGame = schedule.upcoming[0];

    const stadium = stadiumIndex.get(team.stadiumId || '');

    const rosterPreview = topPlayers
      .map(
        (player) => `
          <div class="player-card" data-player="${player.playerId}">
            <div class="avatar">${player.abbreviation || '?'}</div>
            <div class="player-meta">
              <strong>${player.fullName}</strong>
              <span>${player.position || 'Position TBD'} &middot; #${player.jersey || '--'}</span>
            </div>
          </div>
        `
      )
      .join('');

    return `
      <section class="card-grid">
        <article class="summary-card">
          <h4>Team Summary</h4>
          <p>${team.location} / ${team.conference || 'Conference TBD'}</p>
          <p>${formatRecord(team.record)}</p>
        </article>
        <article class="summary-card">
          <h4>Head Coach</h4>
          <p>${team.coach || 'TBD'}</p>
        </article>
        <article class="summary-card" data-stadium="${team.stadiumId || ''}">
          <h4>Arena</h4>
          <p>${stadium ? stadium.name : 'Stadium TBD'}</p>
          <span class="placeholder">Tap to explore venue</span>
        </article>
      </section>

      <section>
        <h3 class="section-heading">Roster Preview</h3>
        <div class="card-grid">${rosterPreview || '<div class="empty-state">Roster data not available.</div>'}</div>
        <button class="filter-chip" data-action="team-tab" data-tab="roster">View Full Roster</button>
      </section>

      <section>
        <h3 class="section-heading">Recent & Upcoming</h3>
        <div class="card-grid">
          <article class="summary-card">
            <h4>Last Result</h4>
            <p>${lastGame ? `${lastGame.shortName || lastGame.name} &middot; ${formatDate(lastGame.date)}${lastGame.teamScore && lastGame.opponentScore ? ` | ${lastGame.teamScore}-${lastGame.opponentScore}` : ''}` : 'No recent games'}</p>
          </article>
          <article class="summary-card">
            <h4>Next Matchup</h4>
            <p>${nextGame ? `${nextGame.shortName || nextGame.name} &middot; ${formatDate(nextGame.date)} ${nextGame.date ? formatTime(nextGame.date) : ''}` : 'No upcoming games'}</p>
          </article>
        </div>
        <button class="filter-chip" data-action="team-tab" data-tab="schedule">View Schedule</button>
      </section>
    `;
  };

  const renderTeamRosterTab = (team) => {
    const rosterList = (team.roster || [])
      .map(
        (player) => `
          <article class="player-card" data-player="${player.playerId}">
            <div class="avatar">${player.abbreviation || '?'}</div>
            <div class="player-meta">
              <strong>${player.fullName}</strong>
              <span>${player.position || 'Position TBD'} &middot; #${player.jersey || '--'}</span>
              <span>${(() => { const bits = [player.height || 'Height —', player.weight || 'Weight —']; if (player.age) bits.push(`${player.age} yrs`); return bits.join(' &middot; '); })()}</span>
            </div>
          </article>
        `
      )
      .join('');

    return rosterList || '<div class="empty-state">Roster data is unavailable.</div>';
  };

  const renderTeamScheduleTab = (team) => {
    const entries = [...(team.schedule?.upcoming || []), ...(team.schedule?.previous || [])]
      .sort((a, b) => new Date(a.date) - new Date(b.date));

    return entries
      .map(
        (game) => `
          <article class="schedule-card">
            <div class="schedule-meta">
              <span>${formatDate(game.date)} &middot; ${formatTime(game.date)}</span>
              <span>${game.status || ''}</span>
            </div>
            <div class="schedule-teams">${game.name || game.shortName}</div>
            <div class="channel-badges">
              ${game.broadcast ? `<span class="channel-badge">${game.broadcast}</span>` : ''}
            </div>
          </article>
        `
      )
      .join('');
  };

  const renderTeamStatsTab = (team) => {
    const stats = team.stats || [];
    return stats.length
      ? stats
          .map(
            (stat) => `
            <article class="stat-card">
              <span>${stat.label}</span>
              <strong>${stat.value ?? '-'}</strong>
              <span class="placeholder">${stat.description || ''}</span>
            </article>
          `
          )
          .join('')
      : '<div class="empty-state">No team statistics available yet.</div>';
  };

  const renderTeamDetail = () => {
    const team = teamIndex.get(AppState.selectedTeamId);
    if (!team) {
      goBack();
      return;
    }

    const tabLabels = [
      { id: 'overview', label: 'Tổng quan' },
      { id: 'roster', label: 'Đội hình' },
      { id: 'schedule', label: 'Lịch đấu' },
      { id: 'stats', label: 'Thống kê' },
    ];

    const renderTabContent = () => {
      switch (AppState.teamTab) {
        case 'roster':
          return renderTeamRosterTab(team);
        case 'schedule':
          return renderTeamScheduleTab(team);
        case 'stats':
          return `<div class="stat-grid">${renderTeamStatsTab(team)}</div>`;
        case 'overview':
        default:
          return renderTeamOverviewTab(team);
      }
    };

    const logo = (team.logos || [])[0];

    appRoot.innerHTML = `
      ${createTopBar(team.shortName, {
        subtitle: `${team.league.shortName} &middot; ${formatRecord(team.record)}`,
      })}
      <section class="summary-card" style="margin-bottom:1rem;">
        <div style="display:flex;gap:1rem;align-items:center;">
          <img src="${logo || ''}" alt="${team.name} logo" style="width:64px;height:64px;border-radius:18px;border:1px solid rgba(255,255,255,0.1);object-fit:cover;" />
          <div>
            <h2 style="margin:0">${team.name}</h2>
            <p class="placeholder" style="margin:.25rem 0 0;">${[team.conference, team.division].filter(Boolean).join(' / ') || ''}</p>
          </div>
          <button class="primary-button" style="max-width:140px;margin-left:auto;font-size:.9rem;">Follow</button>
        </div>
      </section>
      <nav class="tab-bar">
        ${tabLabels
          .map(
            (tab) => `<button class="tab-button ${AppState.teamTab === tab.id ? 'active' : ''}" data-action="team-tab" data-tab="${tab.id}">${tab.label}</button>`
          )
          .join('')}
      </nav>
      <section id="team-tab-content">${renderTabContent()}</section>
    `;

    appRoot.querySelectorAll('[data-action="team-tab"]').forEach((btn) => {
      btn.addEventListener('click', () => {
        AppState.teamTab = btn.dataset.tab;
        renderTeamDetail();
      });
    });

    appRoot.querySelectorAll('[data-player]').forEach((node) => {
      node.addEventListener('click', () => {
        const playerId = node.dataset.player;
        navigate('player-detail', { selectedPlayerId: playerId, playerTab: 'overview' });
      });
    });

    const stadiumCard = appRoot.querySelector('[data-stadium]');
    if (stadiumCard && stadiumCard.dataset.stadium) {
      stadiumCard.addEventListener('click', () => {
        navigate('stadium-detail', { selectedStadiumId: stadiumCard.dataset.stadium, stadiumTab: 'general' });
      });
    }

    const backButton = appRoot.querySelector('[data-action="back"]');
    if (backButton) backButton.addEventListener('click', goBack);
  };

  const renderPlayerDetail = () => {
    const playerId = AppState.selectedPlayerId;
    const player = DATA.players[playerId];
    if (!player) {
      goBack();
      return;
    }

    const tabLabels = [
      { id: 'overview', label: 'Tổng quan' },
      { id: 'stats', label: 'Thống kê' },
      { id: 'bio', label: 'Tiểu sử' },
    ];

    const renderTab = () => {
      if (AppState.playerTab === 'stats') {
        const stats = player.featuredStats || {};
        const entries = Object.entries(stats);
        return entries.length
          ? `<div class="stat-grid">${entries
              .map(
                ([label, value]) => `
                <article class="stat-card">
                  <span>${label}</span>
                  <strong>${value}</strong>
                </article>
              `
              )
              .join('')}</div>`
          : '<div class="empty-state">No featured statistics available.</div>';
      }

      if (AppState.playerTab === 'bio') {
        const bio = player.bio || {};
        const timeline = player.careerTimeline || [];
        return `
          <section class="card-grid">
            ${Object.entries(bio)
              .filter(([, value]) => Boolean(value))
              .map(
                ([label, value]) => `
                  <article class="summary-card">
                    <h4>${label}</h4>
                    <p>${value}</p>
                  </article>
                `
              )
              .join('') || '<div class="empty-state">Bio information unavailable.</div>'}
          </section>
          ${timeline.length ? `<section><h3 class="section-heading">Career Timeline</h3><div class="timeline">${timeline
            .map((item) => `
              <div class="timeline-item">
                <h4>${item.year}</h4>
                <p>${item.event}</p>
              </div>
            `)
            .join('')}</div></section>` : ''}
        `;
      }

      return `
        <section class="card-grid">
          ${player.tagline ? `<article class="summary-card"><h4>Spotlight</h4><p>${player.tagline}</p></article>` : ''}
          ${(player.notables || [])
            .map(
              (note) => `
                <article class="summary-card">
                  <h4>Highlight</h4>
                  <p>${note}</p>
                </article>
              `
            )
            .join('')}
        </section>
      `;
    };

    const team = teamIndex.get(player.team?.id);

    appRoot.innerHTML = `
      ${createTopBar(player.fullName || 'Player', {
        subtitle: team ? `${team.name} &middot; ${team.league.shortName}` : '',
      })}
      <section class="summary-card" style="margin-bottom:1rem;">
        <div style="display:flex;gap:1rem;align-items:center;">
          ${player.headshot ? `<img src="${player.headshot}" alt="${player.fullName}" style="width:80px;height:80px;border-radius:24px;object-fit:cover;" />` : ''}
          <div>
            <h2 style="margin:0;">${player.fullName}</h2>
            <p class="placeholder" style="margin:.25rem 0 0;">${player.position || ''}</p>
          </div>
          <button class="primary-button" style="max-width:140px;margin-left:auto;font-size:.9rem;">Follow</button>
        </div>
      </section>
      <nav class="tab-bar">
        ${tabLabels
          .map(
            (tab) => `<button class="tab-button ${AppState.playerTab === tab.id ? 'active' : ''}" data-action="player-tab" data-tab="${tab.id}">${tab.label}</button>`
          )
          .join('')}
      </nav>
      <section>${renderTab()}</section>
    `;

    appRoot.querySelectorAll('[data-action="player-tab"]').forEach((btn) => {
      btn.addEventListener('click', () => {
        AppState.playerTab = btn.dataset.tab;
        renderPlayerDetail();
      });
    });

    const backButton = appRoot.querySelector('[data-action="back"]');
    if (backButton) backButton.addEventListener('click', goBack);
  };

  const renderStadiumDetail = () => {
    const stadium = stadiumIndex.get(AppState.selectedStadiumId);
    if (!stadium) {
      goBack();
      return;
    }

    const teamsUsingVenue = (stadium.teams || [])
      .map((item) => {
        const team = teamIndex.get(item.teamId);
        return team ? `<span class="badge">${team.name}</span>` : '';
      })
      .join('');

    const images = (stadium.images || []).slice(0, 5);

    const accordionItem = (title, body) => `
      <div class="accordion-item">
        <div class="accordion-header" data-accordion-toggle>
          <strong>${title}</strong>
          <span>+</span>
        </div>
        <div class="accordion-content">
          <p>${body}</p>
        </div>
      </div>
    `;

    const historyContent = (stadium.history || [])
      .map((item) => `<p><strong>${item.title}:</strong> ${item.detail}</p>`)
      .join('');

    const architectureContent = (stadium.architecture || [])
      .map((line) => `<p>${line}</p>`)
      .join('');

    const infoCards = [
      { label: 'Capacity', value: stadium.capacity ? stadium.capacity.toLocaleString() : 'TBD' },
      { label: 'Surface', value: stadium.surface || 'TBD' },
      { label: 'Address', value: stadium.address || 'Address coming soon' },
    ]
      .map(
        (info) => `
          <article class="summary-card">
            <h4>${info.label}</h4>
            <p>${info.value}</p>
          </article>
        `
      )
      .join('');

    appRoot.innerHTML = `
      ${createTopBar(stadium.name, { subtitle: stadium.location || '', actions: '' })}
      ${images.length ? `<section class="carousel">${images.map((src) => `<img src="${src}" alt="${stadium.name}" />`).join('')}</section>` : ''}
      <section class="card-grid">
        ${infoCards}
      </section>
      <section style="margin-top:1.5rem;">
        <h3 class="section-heading">Home Teams</h3>
        <div class="chip-row">${teamsUsingVenue || '<span class="placeholder">No active tenants recorded.</span>'}</div>
      </section>
      <section style="margin-top:1.5rem;">
        <h3 class="section-heading">Venue Insights</h3>
        <div class="accordion">
          ${historyContent ? accordionItem('History', historyContent) : ''}
          ${architectureContent ? accordionItem('Architecture & Amenities', architectureContent) : ''}
          ${stadium.description ? accordionItem('Highlights', `<p>${stadium.description}</p>`) : ''}
        </div>
      </section>
    `;

    appRoot.querySelectorAll('[data-accordion-toggle]').forEach((header) => {
      header.addEventListener('click', () => {
        header.parentElement.classList.toggle('open');
      });
    });

    const backButton = appRoot.querySelector('[data-action="back"]');
    if (backButton) backButton.addEventListener('click', goBack);
  };

  const fetchScheduleData = async () => {
    const sources = [
      '/firepaid.json',
      '/dmmstream.events.json',
    ];
    const requests = sources.map((src) => fetch(src).then((res) => res.json()).catch(() => []));
    const results = await Promise.all(requests);
    return results.flat();
  };

  const renderSchedule = () => {
    appRoot.innerHTML = `
      ${createTopBar('Live Schedules', { subtitle: 'NFL / NBA / MLB / NHL / NCAAF' })}
      <section class="banner-ad">Upgrade to AllSport+ for personalized alerts</section>
      <section class="schedule-list" id="schedule-list">
        <div class="empty-state">Loading games...</div>
      </section>
    `;

    const backButton = appRoot.querySelector('[data-action="back"]');
    if (backButton) backButton.addEventListener('click', goBack);

    fetchScheduleData().then((events) => {
      const container = document.getElementById('schedule-list');
      if (!events.length) {
        container.innerHTML = '<div class="empty-state">No live events available.</div>';
        return;
      }

      const normalized = events
        .map((event) => {
          const dto = event.eventDTO || {};
          const startDate = dto.startDate || event.startDate;
          return {
            startDate,
            timestamp: startDate ? new Date(startDate).getTime() : Number.MAX_SAFE_INTEGER,
            competitionName: dto.eventId
              ? `${dto.home?.shortName || dto.home?.fullName || 'Home'} vs ${dto.away?.shortName || dto.away?.fullName || 'Away'}`
              : event.name,
            broadcast: dto.broadcast || event.broadcast || '',
            tournament: dto.tournament || event.tournament || '',
            channels: (event.links || []).map((link) => ({ name: link.name || link.src || 'Watch', href: link.src })),
          };
        })
        .sort((a, b) => a.timestamp - b.timestamp)
        .slice(0, 80);

      const cards = normalized
        .map(
          (event) => `
            <article class="schedule-card">
              <div class="schedule-meta">
                <span>${formatDate(event.startDate)} &middot; ${formatTime(event.startDate)}</span>
                <span>${event.broadcast}</span>
              </div>
              <div class="schedule-teams">${event.competitionName}</div>
              <div class="badge">${event.tournament.toUpperCase()}</div>
              <div class="channel-badges">
                ${event.channels
                  .map((channel) => `<a class="channel-badge" href="${channel.href}" target="_blank" rel="noopener">${channel.name}</a>` )
                  .join('') || '<span class="placeholder">Channels coming soon</span>'}
              </div>
              <button class="calendar-button" title="Calendar sync coming soon" disabled>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M8 2v4"/><path d="M16 2v4"/><rect x="3" y="6" width="18" height="16" rx="2"/><path d="M16 10h4"/></svg>
                Add to Calendar
              </button>
            </article>
          `
        )
        .join('');

      container.innerHTML = cards;
    });
  };

  const render = () => {
    switch (AppState.view) {
      case 'home':
        renderHome();
        break;
      case 'teams':
        renderTeamsList();
        break;
      case 'team-detail':
        renderTeamDetail();
        break;
      case 'player-detail':
        renderPlayerDetail();
        break;
      case 'stadium-detail':
        renderStadiumDetail();
        break;
      case 'schedule':
        renderSchedule();
        break;
      default:
        renderHome();
        break;
    }
  };

  render();
})();

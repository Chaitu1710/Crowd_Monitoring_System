// ==================================================
// CROWD SAFETY MONITOR - CLIENT JAVASCRIPT ENGINE
// Real-Time Digital Clock, Dynamic Multi-Camera Grid,
// Risk Engine & Dynamic Event Log Renderer
// ==================================================

// DOM Cache - Clock
const digitalClockTime = document.getElementById("digitalClockTime");
const digitalClockDate = document.getElementById("digitalClockDate");

// DOM Cache - Dynamic Camera Grid & Lists
const cameraFeedsGrid = document.getElementById("cameraFeedsGrid");
const activeCamsList = document.getElementById("activeCamsList");

// DOM Cache - Event Log Table
const eventLogTableBody = document.getElementById("eventLogTableBody");

// DOM Cache - Sidebar Risk Rules
const sidebarSafeCount = document.getElementById("sidebarSafeCount");
const sidebarWarningCount = document.getElementById("sidebarWarningCount");
const sidebarCriticalCount = document.getElementById("sidebarCriticalCount");

// DOM Cache - System Status
const sysStatusTitle = document.getElementById("sysStatusTitle");
const sysStatusSub = document.getElementById("sysStatusSub");

// State
let lastAlertStates = {};
let currentSafeThreshold = 3;
let currentCriticalThreshold = 7;
let thresholdsInitialized = false;

function escapeHtml(text) {
    if (!text) return "";
    return String(text)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function updateSidebarThresholdDisplay(safe, crit) {
    if (sidebarSafeCount) sidebarSafeCount.textContent = `≤ ${safe} People`;
    if (sidebarWarningCount) sidebarWarningCount.textContent = `> ${safe} People`;
    if (sidebarCriticalCount) sidebarCriticalCount.textContent = `> ${crit} People`;
}

function updateSystemStatus(status) {
    if (!sysStatusTitle || !sysStatusSub) return;
    if (status === "CRITICAL") {
        sysStatusTitle.textContent = "CRITICAL ALERT";
        sysStatusSub.textContent = "Crowd surge threshold breached";
    } else if (status === "WARNING") {
        sysStatusTitle.textContent = "WARNING ACTIVE";
        sysStatusSub.textContent = "Elevated crowd density";
    } else {
        sysStatusTitle.textContent = "SYSTEM ONLINE";
        sysStatusSub.textContent = "All systems operational";
    }
}


// ==================================================
// DIGITAL CLOCK & TIMESTAMPS
// ==================================================

function updateClock() {
    const now = new Date();

    // Format 12-hour Time (e.g. "10:17:19 AM")
    const timeOptions = { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true };
    const formattedTime = now.toLocaleTimeString('en-US', timeOptions);

    // Format Date (e.g. "Tue, Oct 07, 2026")
    const dateOptions = { weekday: 'short', month: 'short', day: '2-digit', year: 'numeric' };
    const formattedDate = now.toLocaleDateString('en-US', dateOptions);

    // Format ISO-like Timestamp for Camera Overlays (e.g. "2026-10-07 10:17:19")
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, '0');
    const day = String(now.getDate()).padStart(2, '0');
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    const seconds = String(now.getSeconds()).padStart(2, '0');
    const streamTimestamp = `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;

    if (digitalClockTime) digitalClockTime.textContent = formattedTime;
    if (digitalClockDate) digitalClockDate.textContent = formattedDate;

    // Update timestamp across all active camera feeds dynamically
    document.querySelectorAll(".video-timestamp-stamp").forEach(el => {
        el.textContent = streamTimestamp;
    });
}


// ==================================================
// EVENT LOG TABLE RENDERER
// ==================================================

function addEventLogRow(cameraName, eventName, detailsText, isAlert = false, isSystem = false) {
    if (!eventLogTableBody) return;

    const now = new Date();
    const timeString = now.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true });

    const tr = document.createElement("tr");
    tr.className = `log-row ${isAlert ? 'tr-alert' : ''}`;

    // Camera Cell Icon
    let camBadgeClass = isSystem ? "log-cam-badge system" : (isAlert ? "log-cam-badge red" : "log-cam-badge blue");
    let camIcon = isSystem
        ? `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>`
        : `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="23 7 16 12 23 17 23 7"/><rect x="1" y="5" width="15" height="14" rx="2" ry="2"/></svg>`;

    // Event Icon
    let eventIcon = isAlert
        ? `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#ef4444" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>`
        : `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#60a5fa" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>`;

    tr.innerHTML = `
        <td class="log-time-cell">${timeString}</td>
        <td><span class="${camBadgeClass}">${camIcon} ${escapeHtml(cameraName)}</span></td>
        <td><div class="log-event-cell ${isAlert ? 'red' : 'blue'}">${eventIcon} ${escapeHtml(eventName)}</div></td>
        <td class="log-details-cell ${isAlert ? 'red' : ''}">${escapeHtml(detailsText)}</td>
    `;

    // Insert at the top of the event log table
    eventLogTableBody.insertBefore(tr, eventLogTableBody.firstChild);

    // Limit maximum log rows to 40 for optimal performance
    if (eventLogTableBody.children.length > 40) {
        eventLogTableBody.removeChild(eventLogTableBody.lastChild);
    }
}

function clearLogs() {
    if (!eventLogTableBody) return;
    eventLogTableBody.innerHTML = "";
    addEventLogRow("System", "Event log cleared", "Operator reset system logs", false, true);
}


// ==================================================
// DYNAMIC DOM BUILDERS (SUPPORTS 1 TO 5+ CAMERAS)
// ==================================================

function createCameraCardElement(camId, camInfo) {
    const card = document.createElement("div");
    card.className = "camera-card";
    card.id = `camCard_${camId}`;
    card.setAttribute("data-cam-id", camId);

    const safeName = escapeHtml(camInfo.name || camId);
    const safeIp = escapeHtml(camInfo.ip || "N/A");

    card.innerHTML = `
        <div class="cam-card-topbar">
            <div class="cam-identity">
                <div class="cam-icon-box">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polygon points="23 7 16 12 23 17 23 7"></polygon>
                        <rect x="1" y="5" width="15" height="14" rx="2" ry="2"></rect>
                    </svg>
                </div>
                <div>
                    <h2 class="cam-name" id="camName_${camId}">${safeName}</h2>
                    <span class="cam-endpoint" id="camIpText_${camId}">${safeIp}</span>
                </div>
            </div>

            <div class="cam-top-badges">
                <button class="btn-change-ip" onclick="openChangeIpModal('${camId}', '${safeName.replace(/'/g, "\\'")}')" title="Configure Camera IP" style="margin-right: 6px; padding: 4px 8px; font-size: 11px; background: rgba(59, 130, 246, 0.15); border: 1px solid rgba(59, 130, 246, 0.4); color: #60a5fa; border-radius: 5px; cursor: pointer; display: inline-flex; align-items: center; gap: 4px;">
                    ⚙️ IP
                </button>
                <span class="badge-zone badge-safe" id="camZoneBadge_${camId}">SAFE ZONE</span>
                <span class="badge-conn badge-offline" id="camStatusBadge_${camId}">● OFFLINE</span>
            </div>
        </div>

        <div class="cam-video-box">
            <img src="/video_feed/${camId}" class="cam-stream-img" id="camFeedImg_${camId}" alt="${safeName} Live Stream">
            <div class="video-overlay-bar">
                <span class="live-status-pill">
                    <span class="live-indicator-dot"></span> LIVE REC
                </span>
                <span class="video-timestamp-stamp" id="camTimestamp_${camId}">--:--:--</span>
            </div>
        </div>

        <div class="cam-stats-footer">
            <div class="stat-cell">
                <div class="stat-icon-wrapper blue" id="camPeopleIcon_${camId}">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
                        <circle cx="9" cy="7" r="4"></circle>
                        <path d="M23 21v-2a4 4 0 0 0-3-3.87"></path>
                        <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
                    </svg>
                </div>
                <div class="stat-meta">
                    <span class="stat-label">PEOPLE COUNT</span>
                    <span class="stat-number" id="camCount_${camId}">0</span>
                </div>
            </div>

            <div class="stat-cell">
                <div class="stat-icon-wrapper blue" id="camZoneIcon_${camId}">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
                    </svg>
                </div>
                <div class="stat-meta">
                    <span class="stat-label">ZONE RISK</span>
                    <span class="stat-risk-label val-safe" id="camZoneRisk_${camId}">SAFE</span>
                </div>
            </div>
        </div>
    `;

    return card;
}

function createSidebarCameraItem(camId, camInfo) {
    const item = document.createElement("div");
    item.className = "cam-feed-item";
    item.id = `sideCamItem_${camId}`;
    item.setAttribute("data-cam-id", camId);

    const safeName = escapeHtml(camInfo.name || camId);
    const safeIp = escapeHtml(camInfo.ip || "N/A");

    item.innerHTML = `
        <div class="feed-item-left">
            <div class="feed-mini-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polygon points="23 7 16 12 23 17 23 7"></polygon>
                    <rect x="1" y="5" width="15" height="14" rx="2" ry="2"></rect>
                </svg>
            </div>
            <div class="feed-info">
                <strong class="feed-title" id="sideCamTitle_${camId}">${safeName}</strong>
                <span class="feed-sub" id="sideCamIp_${camId}">${safeIp}</span>
            </div>
        </div>
        <span class="badge-conn badge-offline" id="sideCamStatus_${camId}">● OFFLINE</span>
    `;

    return item;
}


// ==================================================
// UPDATE INDIVIDUAL CAMERA FEED UI
// ==================================================

function updateCameraFeedCard(camKey, camInfo) {
    if (!camInfo) return;

    const cardElem = document.getElementById(`camCard_${camKey}`);
    const countElem = document.getElementById(`camCount_${camKey}`);
    const zoneBadgeElem = document.getElementById(`camZoneBadge_${camKey}`);
    const statusBadgeElem = document.getElementById(`camStatusBadge_${camKey}`);
    const zoneRiskElem = document.getElementById(`camZoneRisk_${camKey}`);
    const peopleIconElem = document.getElementById(`camPeopleIcon_${camKey}`);
    const zoneIconElem = document.getElementById(`camZoneIcon_${camKey}`);
    const sideStatusElem = document.getElementById(`sideCamStatus_${camKey}`);
    const sideIpElem = document.getElementById(`sideCamIp_${camKey}`);
    const ipTextElem = document.getElementById(`camIpText_${camKey}`);
    const nameElem = document.getElementById(`camName_${camKey}`);
    const sideTitleElem = document.getElementById(`sideCamTitle_${camKey}`);

    const count = camInfo.count || 0;
    const isConnected = !!camInfo.connected;
    const camName = camInfo.name || camKey;

    // 1. Name & IP endpoint display
    if (nameElem && camInfo.name && nameElem.textContent !== camInfo.name) {
        nameElem.textContent = camInfo.name;
    }
    if (sideTitleElem && camInfo.name && sideTitleElem.textContent !== camInfo.name) {
        sideTitleElem.textContent = camInfo.name;
    }
    if (camInfo.ip) {
        if (ipTextElem && ipTextElem.textContent !== camInfo.ip) ipTextElem.textContent = camInfo.ip;
        if (sideIpElem && sideIpElem.textContent !== camInfo.ip) sideIpElem.textContent = camInfo.ip;
    }

    // 2. Individual People Count
    if (countElem) {
        countElem.textContent = count;
    }

    // 3. Connection Badges
    const statusText = isConnected ? "● LIVE" : "● OFFLINE";
    const statusClass = isConnected ? "badge-conn badge-live" : "badge-conn badge-offline";

    if (statusBadgeElem) {
        statusBadgeElem.textContent = statusText;
        statusBadgeElem.className = statusClass;
    }
    if (sideStatusElem) {
        sideStatusElem.textContent = statusText;
        sideStatusElem.className = statusClass;
    }

    // 4. Dynamic Risk Classification & Alert Logic based on configured thresholds
    const isCritical = camInfo.risk_level === "CRITICAL" || count > currentCriticalThreshold;
    const isWarning = !isCritical && (camInfo.risk_level === "WARNING" || count > currentSafeThreshold);

    if (isCritical) {
        // Red glowing border on camera box
        if (cardElem) cardElem.classList.add("alert-active");

        // Top Header Badge
        if (zoneBadgeElem) {
            zoneBadgeElem.className = "badge-zone badge-critical";
            zoneBadgeElem.innerHTML = `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg> CRITICAL ALERT`;
        }

        // Stat Zone Risk Label
        if (zoneRiskElem) {
            zoneRiskElem.textContent = camInfo.zone_risk || `CRITICAL (>${currentCriticalThreshold})`;
            zoneRiskElem.className = "stat-risk-label val-critical";
        }

        // Icon boxes turn red
        if (peopleIconElem) peopleIconElem.className = "stat-icon-wrapper red";
        if (zoneIconElem) zoneIconElem.className = "stat-icon-wrapper red";

        // Check state change for log
        if (lastAlertStates[camKey] !== "CRITICAL") {
            addEventLogRow(camName, "Critical crowd density detected", `${count} people detected (Zone: CRITICAL >${currentCriticalThreshold})`, true);
            lastAlertStates[camKey] = "CRITICAL";
        }

    } else if (isWarning) {
        // Warning alert border
        if (cardElem) cardElem.classList.add("alert-active");

        if (zoneBadgeElem) {
            zoneBadgeElem.className = "badge-zone badge-warning";
            zoneBadgeElem.textContent = "WARNING ZONE";
        }

        if (zoneRiskElem) {
            zoneRiskElem.textContent = camInfo.zone_risk || `WARNING (>${currentSafeThreshold})`;
            zoneRiskElem.className = "stat-risk-label val-warning";
        }

        if (peopleIconElem) peopleIconElem.className = "stat-icon-wrapper blue";
        if (zoneIconElem) zoneIconElem.className = "stat-icon-wrapper blue";

        if (lastAlertStates[camKey] !== "WARNING") {
            addEventLogRow(camName, "Elevated crowd density warning", `${count} people detected (Zone: WARNING >${currentSafeThreshold})`, true);
            lastAlertStates[camKey] = "WARNING";
        }

    } else {
        // Normal Safe Zone
        if (cardElem) cardElem.classList.remove("alert-active");

        if (zoneBadgeElem) {
            zoneBadgeElem.className = "badge-zone badge-safe";
            zoneBadgeElem.textContent = "SAFE ZONE";
        }

        if (zoneRiskElem) {
            zoneRiskElem.textContent = camInfo.zone_risk || `SAFE (≤${currentSafeThreshold})`;
            zoneRiskElem.className = "stat-risk-label val-safe";
        }

        if (peopleIconElem) peopleIconElem.className = "stat-icon-wrapper blue";
        if (zoneIconElem) zoneIconElem.className = "stat-icon-wrapper blue";

        if (lastAlertStates[camKey] !== "SAFE" && lastAlertStates[camKey] !== null && lastAlertStates[camKey] !== undefined) {
            addEventLogRow(camName, "Normal crowd density", `${count} people detected (Zone: SAFE ≤${currentSafeThreshold})`, false);
            lastAlertStates[camKey] = "SAFE";
        } else if (!lastAlertStates[camKey]) {
            lastAlertStates[camKey] = "SAFE";
        }
    }
}


// ==================================================
// DYNAMIC MULTI-CAMERA SYNCHRONIZER
// ==================================================

function syncCamerasGrid(cameras) {
    if (!cameraFeedsGrid || !activeCamsList) return;

    const camIds = Object.keys(cameras);

    // Fallback if 0 cameras are registered
    if (camIds.length === 0) {
        if (!document.getElementById("emptyCamerasNotice")) {
            cameraFeedsGrid.innerHTML = `
                <div id="emptyCamerasNotice" style="grid-column: 1 / -1; background: var(--bg-card); border: 1px dashed var(--border-card); border-radius: 14px; padding: 48px 24px; text-align: center; color: var(--text-secondary);">
                    <div style="font-size: 38px; margin-bottom: 12px;">📷</div>
                    <h3 style="font-size: 18px; color: #fff; margin-bottom: 8px;">No Camera Streams Registered</h3>
                    <p style="font-size: 13px; max-width: 440px; margin: 0 auto 18px;">
                        Add your mobile IP webcam or RTSP streams in the Admin Portal to start real-time multi-camera crowd monitoring.
                    </p>
                    <a href="/admin" style="display: inline-block; padding: 8px 18px; background: var(--blue-primary); color: #fff; text-decoration: none; border-radius: 6px; font-weight: 600; font-size: 13px;">
                        👑 Open Admin Portal
                    </a>
                </div>
            `;
            activeCamsList.innerHTML = `
                <div id="emptySidebarNotice" style="padding: 16px; text-align: center; color: var(--text-muted); font-size: 12px;">
                    No active cameras
                </div>
            `;
        }
        return;
    }

    // Remove empty notice if present
    const emptyNotice = document.getElementById("emptyCamerasNotice");
    if (emptyNotice) emptyNotice.remove();
    const emptySide = document.getElementById("emptySidebarNotice");
    if (emptySide) emptySide.remove();

    // 1. Add / Update each active camera in the feeds grid & sidebar
    camIds.forEach(camId => {
        const camInfo = cameras[camId];

        // Ensure Card in main grid
        if (!document.getElementById(`camCard_${camId}`)) {
            const card = createCameraCardElement(camId, camInfo);
            cameraFeedsGrid.appendChild(card);
            addEventLogRow(camInfo.name || camId, "Camera stream connected", `Stream initialized at ${camInfo.ip || "stream"}`, false, true);
        }

        // Ensure Item in sidebar
        if (!document.getElementById(`sideCamItem_${camId}`)) {
            const sideItem = createSidebarCameraItem(camId, camInfo);
            activeCamsList.appendChild(sideItem);
        }

        // Update stats and live telemetry
        updateCameraFeedCard(camId, camInfo);
    });

    // 2. Remove deleted cameras from main grid
    const existingCards = cameraFeedsGrid.querySelectorAll(".camera-card");
    existingCards.forEach(card => {
        const cid = card.getAttribute("data-cam-id");
        if (cid && !cameras[cid]) {
            card.remove();
            delete lastAlertStates[cid];
            addEventLogRow(cid, "Camera stream removed", `Camera ${cid} disconnected and removed from dashboard`, false, true);
        }
    });

    // 3. Remove deleted cameras from sidebar
    const existingSideItems = activeCamsList.querySelectorAll(".cam-feed-item");
    existingSideItems.forEach(item => {
        const cid = item.getAttribute("data-cam-id");
        if (cid && !cameras[cid]) {
            item.remove();
        }
    });
}


// ==================================================
// API POLLING LOOP
// ==================================================

async function fetchPeopleData() {
    try {
        const response = await fetch("/people?t=" + Date.now());
        if (!response.ok) return;

        const data = await response.json();

        // Dynamically synchronize thresholds from server
        if (data.safe_threshold !== undefined && data.critical_threshold !== undefined) {
            const newSafe = parseInt(data.safe_threshold);
            const newCrit = parseInt(data.critical_threshold);

            if (thresholdsInitialized && (newSafe !== currentSafeThreshold || newCrit !== currentCriticalThreshold)) {
                addEventLogRow(
                    "System",
                    "Safety threshold rules updated",
                    `Safe (≤${newSafe}), Warning (>${newSafe}), Critical (>${newCrit})`,
                    false,
                    true
                );
            }

            currentSafeThreshold = newSafe;
            currentCriticalThreshold = newCrit;
            thresholdsInitialized = true;

            updateSidebarThresholdDisplay(currentSafeThreshold, currentCriticalThreshold);
        }

        updateSystemStatus(data.status);

        // Dynamically synchronize all camera feeds (1 to 5+ cameras)
        syncCamerasGrid(data.cameras || {});

    } catch (err) {
        console.error("Error fetching people analytics:", err);
    }
}


// ==================================================
// DASHBOARD INITIALIZATION
// ==================================================

function initializeSystem() {
    // 1. Initial Clock Tick
    updateClock();
    setInterval(updateClock, 1000);

    // 2. Pre-populate System Startup Events matching screenshot
    addEventLogRow("System", "Zone risk rules active", "Dynamic safety thresholds enabled", false, true);
    addEventLogRow("System", "YOLO object tracking enabled", "Real-time person detection and tracking", false, true);
    addEventLogRow("System", "Density heatmap overlay active", "Gaussian JET colormap enabled for multi-camera feeds", false, true);

    // 3. Initial API Fetch
    fetchPeopleData();
    setInterval(fetchPeopleData, 1000);
}


// ==================================================
// DYNAMIC CAMERA ENDPOINT MODAL & SWITCHING
// ==================================================

function showToast(msg) {
    const toast = document.getElementById("toastNotice");
    if (!toast) return;
    toast.textContent = msg;
    toast.style.display = "block";
    setTimeout(() => {
        toast.style.display = "none";
    }, 3200);
}

function openChangeIpModal(camId, defaultName) {
    const modal = document.getElementById("changeIpModal");
    if (!modal) return;

    const idInput = document.getElementById("modalCamId");
    const nameInput = document.getElementById("modalCamName");
    const endpointInput = document.getElementById("modalCamEndpoint");
    const titleElem = document.getElementById("modalCamTitle");

    idInput.value = camId;
    titleElem.textContent = `Change ${defaultName} Endpoint`;
    nameInput.value = defaultName;

    // Pre-fill with current displayed IP
    const currentIpElem = document.getElementById(`camIpText_${camId}`);
    const currentIp = currentIpElem ? currentIpElem.textContent.trim() : "";
    endpointInput.value = (currentIp && currentIp !== "N/A") ? currentIp : "";

    modal.style.display = "flex";
    setTimeout(() => endpointInput.focus(), 50);
}

function closeChangeIpModal() {
    const modal = document.getElementById("changeIpModal");
    if (modal) modal.style.display = "none";
}

function closeModalOnBackdrop(e) {
    if (e.target && e.target.id === "changeIpModal") {
        closeChangeIpModal();
    }
}

async function submitChangeIp(e) {
    e.preventDefault();

    const camId = document.getElementById("modalCamId").value.trim();
    const name = document.getElementById("modalCamName").value.trim();
    const endpoint = document.getElementById("modalCamEndpoint").value.trim();
    const submitBtn = document.getElementById("btnModalSubmit");
    const submitText = document.getElementById("btnModalText");

    if (!endpoint) {
        alert("Please enter a valid IP address or stream URL.");
        return;
    }

    if (submitBtn) submitBtn.disabled = true;
    if (submitText) submitText.textContent = "Connecting...";

    try {
        const response = await fetch("/api/camera/update", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ id: camId, name: name, endpoint: endpoint })
        });

        const data = await response.json();

        if (data.success && data.camera) {
            closeChangeIpModal();

            const updatedCam = data.camera;

            // 1. Force refresh the MJPEG image element
            const feedImg = document.getElementById(`camFeedImg_${camId}`);
            if (feedImg) {
                feedImg.src = `/video_feed/${camId}?t=${Date.now()}`;
            }

            // 2. Update IP labels on dashboard
            const ipLabel = document.getElementById(`camIpText_${camId}`);
            if (ipLabel) ipLabel.textContent = updatedCam.ip;

            const sideIp = document.getElementById(`sideCamIp_${camId}`);
            if (sideIp) sideIp.textContent = updatedCam.ip;

            const nameElem = document.getElementById(`camName_${camId}`);
            if (nameElem && updatedCam.name) nameElem.textContent = updatedCam.name;

            const sideTitle = document.getElementById(`sideCamTitle_${camId}`);
            if (sideTitle && updatedCam.name) sideTitle.textContent = updatedCam.name;

            // 3. Add to event log
            addEventLogRow(
                updatedCam.name || camId,
                "Camera IP endpoint updated",
                `Connected to ${updatedCam.ip} (saved to config.py)`,
                false,
                true
            );

            // 4. Show toast notification
            showToast(`✓ ${updatedCam.name} switched to ${updatedCam.ip}`);

            // 5. Trigger immediate telemetry polling
            fetchPeopleData();
        } else {
            alert(`Error updating camera: ${data.error || "Unknown error"}`);
        }
    } catch (err) {
        console.error("Error updating camera endpoint:", err);
        alert("Failed to communicate with server to update camera.");
    } finally {
        if (submitBtn) submitBtn.disabled = false;
        if (submitText) submitText.textContent = "⚡ Switch Stream & Save";
    }
}

// Start
document.addEventListener("DOMContentLoaded", initializeSystem);

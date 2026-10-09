// ==================================================
// CROWD SAFETY MONITOR - CLIENT JAVASCRIPT ENGINE
// Real-Time Digital Clock, Multi-Camera Polling,
// Red Border Alert Logic & Event Log Table Renderer
// ==================================================

// DOM Cache - Clock
const digitalClockTime = document.getElementById("digitalClockTime");
const digitalClockDate = document.getElementById("digitalClockDate");

// DOM Cache - Camera 1
const cam1Card = document.getElementById("cam1Card");
const cam1Count = document.getElementById("cam1Count");
const cam1ZoneBadge = document.getElementById("cam1ZoneBadge");
const cam1StatusBadge = document.getElementById("cam1StatusBadge");
const cam1ZoneRiskText = document.getElementById("cam1ZoneRiskText");
const cam1PeopleIconBox = document.getElementById("cam1PeopleIconBox");
const cam1ZoneIconBox = document.getElementById("cam1ZoneIconBox");
const cam1OverlayTimestamp = document.getElementById("cam1OverlayTimestamp");
const cam1IpText = document.getElementById("cam1IpText");
const sideCam1Ip = document.getElementById("sideCam1Ip");
const sideCam1Status = document.getElementById("sideCam1Status");
const cam1LivePill = document.getElementById("cam1LivePill");

// DOM Cache - Camera 2
const cam2Card = document.getElementById("cam2Card");
const cam2Count = document.getElementById("cam2Count");
const cam2ZoneBadge = document.getElementById("cam2ZoneBadge");
const cam2StatusBadge = document.getElementById("cam2StatusBadge");
const cam2ZoneRiskText = document.getElementById("cam2ZoneRiskText");
const cam2PeopleIconBox = document.getElementById("cam2PeopleIconBox");
const cam2ZoneIconBox = document.getElementById("cam2ZoneIconBox");
const cam2OverlayTimestamp = document.getElementById("cam2OverlayTimestamp");
const cam2IpText = document.getElementById("cam2IpText");
const sideCam2Ip = document.getElementById("sideCam2Ip");
const sideCam2Status = document.getElementById("sideCam2Status");
const cam2LivePill = document.getElementById("cam2LivePill");

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
let lastAlertStates = {
    cam1: null,
    cam2: null
};
let currentSafeThreshold = 3;
let currentCriticalThreshold = 7;
let thresholdsInitialized = false;

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

    if (cam1OverlayTimestamp) cam1OverlayTimestamp.textContent = streamTimestamp;
    if (cam2OverlayTimestamp) cam2OverlayTimestamp.textContent = streamTimestamp;
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
        <td><span class="${camBadgeClass}">${camIcon} ${cameraName}</span></td>
        <td><div class="log-event-cell ${isAlert ? 'red' : 'blue'}">${eventIcon} ${eventName}</div></td>
        <td class="log-details-cell ${isAlert ? 'red' : ''}">${detailsText}</td>
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
// UPDATE INDIVIDUAL CAMERA FEED UI
// ==================================================

function updateCameraFeedCard(camKey, camInfo, cardElem, countElem, zoneBadgeElem, statusBadgeElem, zoneRiskElem, peopleIconElem, zoneIconElem, sideStatusElem, sideIpElem, ipTextElem) {
    if (!camInfo) return;

    const count = camInfo.count || 0;
    const isConnected = !!camInfo.connected;
    const camName = camInfo.name || (camKey === "cam1" ? "Camera 1" : "Camera 2");

    // 1. IP endpoint display
    if (camInfo.ip) {
        if (ipTextElem) ipTextElem.textContent = camInfo.ip;
        if (sideIpElem) sideIpElem.textContent = camInfo.ip;
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
    const hasAlert = isCritical || isWarning;

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

        if (lastAlertStates[camKey] !== "SAFE" && lastAlertStates[camKey] !== null) {
            addEventLogRow(camName, "Normal crowd density", `${count} people detected (Zone: SAFE ≤${currentSafeThreshold})`, false);
            lastAlertStates[camKey] = "SAFE";
        } else if (lastAlertStates[camKey] === null) {
            lastAlertStates[camKey] = "SAFE";
        }
    }
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

        const cameras = data.cameras || {};

        // Update Camera 1
        if (cameras.cam1) {
            updateCameraFeedCard(
                "cam1",
                cameras.cam1,
                cam1Card,
                cam1Count,
                cam1ZoneBadge,
                cam1StatusBadge,
                cam1ZoneRiskText,
                cam1PeopleIconBox,
                cam1ZoneIconBox,
                sideCam1Status,
                sideCam1Ip,
                cam1IpText
            );
        }

        // Update Camera 2
        if (cameras.cam2) {
            updateCameraFeedCard(
                "cam2",
                cameras.cam2,
                cam2Card,
                cam2Count,
                cam2ZoneBadge,
                cam2StatusBadge,
                cam2ZoneRiskText,
                cam2PeopleIconBox,
                cam2ZoneIconBox,
                sideCam2Status,
                sideCam2Ip,
                cam2IpText
            );
        }

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
    addEventLogRow("System", "Density heatmap overlay active", "Gaussian JET colormap enabled for both cameras", false, true);

    // 3. Initial API Fetch
    fetchPeopleData();
    setInterval(fetchPeopleData, 1000);
}

// Start
document.addEventListener("DOMContentLoaded", initializeSystem);

// =============================================
// CROWD SAFETY MONITOR - PHASE 3 SCRIPT
// Heatmaps, Deduplication & Critical Zone Alerts
// =============================================

const totalPeopleCount = document.getElementById("totalPeopleCount");
const breakdownCam1 = document.getElementById("breakdownCam1");
const breakdownCam2 = document.getElementById("breakdownCam2");

const cam1Count = document.getElementById("cam1Count");
const cam2Count = document.getElementById("cam2Count");

const crowdStatus = document.getElementById("crowdStatus");
const crowdMessage = document.getElementById("crowdMessage");

const cam1StatusBadge = document.getElementById("cam1StatusBadge");
const cam2StatusBadge = document.getElementById("cam2StatusBadge");

const cam1ZoneBadge = document.getElementById("cam1ZoneBadge");
const cam2ZoneBadge = document.getElementById("cam2ZoneBadge");

const cam1ZoneText = document.getElementById("cam1ZoneText");
const cam2ZoneText = document.getElementById("cam2ZoneText");

const cam1ConnectionText = document.getElementById("cam1ConnectionText");
const cam2ConnectionText = document.getElementById("cam2ConnectionText");

const criticalAlertBanner = document.getElementById("criticalAlertBanner");
const alertBannerText = document.getElementById("alertBannerText");

const eventLog = document.getElementById("eventLog");

let lastAlertState = false;


// =============================================
// TIME HELPER
// =============================================

function getCurrentTime() {
    const now = new Date();
    return now.toLocaleTimeString();
}


// =============================================
// EVENT LOG
// =============================================

function addLog(message) {
    if (!eventLog) return;

    const logEntry = document.createElement("div");
    logEntry.className = "log-entry";

    const timeElement = document.createElement("span");
    timeElement.className = "log-time";
    timeElement.textContent = getCurrentTime();

    const messageElement = document.createElement("span");
    messageElement.className = "log-message";
    messageElement.textContent = message;

    logEntry.appendChild(timeElement);
    logEntry.appendChild(messageElement);

    eventLog.appendChild(logEntry);
    eventLog.scrollTop = eventLog.scrollHeight;
}


// =============================================
// UPDATE ZONE RISK UI HELPER
// =============================================

function updateZoneRiskUI(badgeElem, textElem, zoneRisk, riskLevel) {
    if (!badgeElem || !textElem) return;

    badgeElem.textContent = zoneRisk;

    if (riskLevel === "CRITICAL") {
        badgeElem.className = "badge badge-critical";
        textElem.textContent = zoneRisk;
        textElem.className = "risk-critical";
    } else if (riskLevel === "WARNING") {
        badgeElem.className = "badge badge-warning";
        textElem.textContent = zoneRisk;
        textElem.className = "risk-warning";
    } else {
        badgeElem.className = "badge badge-normal";
        textElem.textContent = "SAFE (≤3)";
        textElem.className = "risk-safe";
    }
}


// =============================================
// API POLLING FUNCTION
// =============================================

async function updatePeopleData() {
    try {
        const response = await fetch("/people?t=" + Date.now());

        if (!response.ok) {
            throw new Error("People API request failed");
        }

        const data = await response.json();

        // 1. Deduplicated Total People Count
        totalPeopleCount.textContent = data.total_count;

        // 2. Camera Breakdown Counts
        const cam1Info = data.cameras.cam1 || { count: 0, connected: false, zone_risk: "SAFE ZONE", risk_level: "NORMAL" };
        const cam2Info = data.cameras.cam2 || { count: 0, connected: false, zone_risk: "SAFE ZONE", risk_level: "NORMAL" };

        if (cam1Count) cam1Count.textContent = cam1Info.count;
        if (cam2Count) cam2Count.textContent = cam2Info.count;

        if (breakdownCam1) breakdownCam1.textContent = cam1Info.count;
        if (breakdownCam2) breakdownCam2.textContent = cam2Info.count;

        // 3. Zone Risk Badges
        updateZoneRiskUI(cam1ZoneBadge, cam1ZoneText, cam1Info.zone_risk, cam1Info.risk_level);
        updateZoneRiskUI(cam2ZoneBadge, cam2ZoneText, cam2Info.zone_risk, cam2Info.risk_level);

        // 4. Overall Crowd Status UI
        crowdStatus.textContent = data.status;
        crowdStatus.classList.remove("waiting", "normal", "moderate", "high", "critical", "warning");
        crowdStatus.classList.add(data.status.toLowerCase());

        // Status Messages & Alert Banners
        if (data.critical_zone_active) {
            criticalAlertBanner.classList.remove("hidden");
            alertBannerText.textContent = "⚠️ Critical threshold (>7 people) breached! High risk of crowd congestion.";
            crowdMessage.textContent = "🚨 CRITICAL: High crowd density detected (>7 people)!";

            if (!lastAlertState) {
                addLog("🚨 ALERT: Critical zone density threshold (>7 people) breached!");
                lastAlertState = true;
            }
        } else if (data.warning_zone_active) {
            criticalAlertBanner.classList.add("hidden");
            crowdMessage.textContent = "⚠️ WARNING: Crowd density exceeds safe limit (>3 people).";
            lastAlertState = false;
        } else {
            criticalAlertBanner.classList.add("hidden");
            crowdMessage.textContent = "Crowd level is normal (≤3 people per camera).";
            lastAlertState = false;
        }

        // 5. Connection Indicators
        if (cam1Info.connected) {
            cam1StatusBadge.textContent = "LIVE";
            cam1StatusBadge.className = "badge badge-normal";
            cam1ConnectionText.textContent = "CONNECTED";
        } else {
            cam1StatusBadge.textContent = "OFFLINE";
            cam1StatusBadge.className = "badge badge-offline";
            cam1ConnectionText.textContent = "DISCONNECTED";
        }

        if (cam2Info.connected) {
            cam2StatusBadge.textContent = "LIVE";
            cam2StatusBadge.className = "badge badge-normal";
            cam2ConnectionText.textContent = "CONNECTED";
        } else {
            cam2StatusBadge.textContent = "OFFLINE";
            cam2StatusBadge.className = "badge badge-offline";
            cam2ConnectionText.textContent = "DISCONNECTED";
        }

    } catch (error) {
        console.error("People API error:", error);
    }
}


// =============================================
// CLEAR LOGS
// =============================================

function clearLogs() {
    eventLog.innerHTML = "";
    addLog("Event log cleared.");
}


// =============================================
// INITIALIZE DASHBOARD
// =============================================

function initializeDashboard() {
    addLog("Starting Phase 3 Crowd Safety Monitor...");
    addLog("Live Density Heatmap overlay active (Gaussian JET colormap).");
    addLog("YOLO object tracking deduplication enabled.");
    addLog("Critical Zone rules active: Safe (≤3), Red Zone (>3), Critical Zone (>7).");

    updatePeopleData();
    setInterval(updatePeopleData, 1000);
}

initializeDashboard();
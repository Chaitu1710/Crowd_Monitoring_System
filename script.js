// =============================================
// CROWD SAFETY MONITOR - PHASE 3 SCRIPT
// Real-Time Individual Camera People Tracking & Location Alerts
// =============================================

// Individual Camera UI Elements
const cam1Box = document.getElementById("cam1Box");
const cam2Box = document.getElementById("cam2Box");

const cam1Count = document.getElementById("cam1Count");
const cam2Count = document.getElementById("cam2Count");

const cam1ZoneBadge = document.getElementById("cam1ZoneBadge");
const cam2ZoneBadge = document.getElementById("cam2ZoneBadge");

const cam1StatusBadge = document.getElementById("cam1StatusBadge");
const cam2StatusBadge = document.getElementById("cam2StatusBadge");

const cam1ZoneText = document.getElementById("cam1ZoneText");
const cam2ZoneText = document.getElementById("cam2ZoneText");

const cam1AlertBanner = document.getElementById("cam1AlertBanner");
const cam2AlertBanner = document.getElementById("cam2AlertBanner");

const cam1AlertMsg = document.getElementById("cam1AlertMsg");
const cam2AlertMsg = document.getElementById("cam2AlertMsg");

const cam1ConnectionText = document.getElementById("cam1ConnectionText");
const cam2ConnectionText = document.getElementById("cam2ConnectionText");

const cam1IpText = document.getElementById("cam1IpText");
const cam2IpText = document.getElementById("cam2IpText");

// Sidebar Individual Count Cards
const sideCam1Card = document.getElementById("sideCam1Card");
const sideCam2Card = document.getElementById("sideCam2Card");

const sideCam1Count = document.getElementById("sideCam1Count");
const sideCam2Count = document.getElementById("sideCam2Count");

const sideCam1Zone = document.getElementById("sideCam1Zone");
const sideCam2Zone = document.getElementById("sideCam2Zone");

// Global & Alert Elements
const criticalAlertBanner = document.getElementById("criticalAlertBanner");
const alertBannerTitle = document.getElementById("alertBannerTitle");
const alertBannerText = document.getElementById("alertBannerText");

const crowdStatus = document.getElementById("crowdStatus");
const crowdMessage = document.getElementById("crowdMessage");

const summaryCam1Ip = document.getElementById("summaryCam1Ip");
const summaryCam2Ip = document.getElementById("summaryCam2Ip");

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
// API POLLING FUNCTION - INDIVIDUAL CAMERA COUNTS & ALERTS
// =============================================

async function updatePeopleData() {
    try {
        const response = await fetch("/people?t=" + Date.now());

        if (!response.ok) {
            throw new Error("People API request failed");
        }

        const data = await response.json();

        const cam1Info = data.cameras && data.cameras.cam1 ? data.cameras.cam1 : { count: 0, connected: false, zone_risk: "SAFE ZONE", risk_level: "NORMAL", ip: "100.70.115.163:8080", name: "Camera 1" };
        const cam2Info = data.cameras && data.cameras.cam2 ? data.cameras.cam2 : { count: 0, connected: false, zone_risk: "SAFE ZONE", risk_level: "NORMAL", ip: "192.168.137.209:8080", name: "Camera 2" };

        const count1 = cam1Info.count || 0;
        const count2 = cam2Info.count || 0;

        // -------------------------------------------------------------
        // 1. UPDATE CAMERA 1 INDIVIDUAL REAL-TIME COUNT & ALERT STATE
        // -------------------------------------------------------------
        if (cam1Count) cam1Count.textContent = count1;
        if (sideCam1Count) sideCam1Count.textContent = count1;

        updateZoneRiskUI(cam1ZoneBadge, cam1ZoneText, cam1Info.zone_risk, cam1Info.risk_level);

        if (sideCam1Zone) {
            sideCam1Zone.textContent = `${cam1Info.zone_risk} (${count1} People)`;
            sideCam1Zone.className = cam1Info.risk_level === "CRITICAL" ? "risk-critical" : (cam1Info.risk_level === "WARNING" ? "risk-warning" : "risk-safe");
        }

        // Camera 1 High Crowd Alert Check (>3 people triggers alert + red border)
        if (count1 > 3) {
            if (cam1Box) cam1Box.classList.add("camera-box-alert");
            if (sideCam1Card) sideCam1Card.classList.add("card-alert");
            if (cam1AlertBanner) {
                cam1AlertBanner.classList.remove("hidden");
                if (count1 > 7) {
                    if (cam1AlertMsg) cam1AlertMsg.textContent = `🚨 CRITICAL ALERT: Extreme crowd at Camera 1 (${count1} people)!`;
                } else {
                    if (cam1AlertMsg) cam1AlertMsg.textContent = `⚠️ ALERT: High crowd detected at Camera 1 (${count1} people)!`;
                }
            }
        } else {
            if (cam1Box) cam1Box.classList.remove("camera-box-alert");
            if (sideCam1Card) sideCam1Card.classList.remove("card-alert");
            if (cam1AlertBanner) cam1AlertBanner.classList.add("hidden");
        }

        // -------------------------------------------------------------
        // 2. UPDATE CAMERA 2 INDIVIDUAL REAL-TIME COUNT & ALERT STATE
        // -------------------------------------------------------------
        if (cam2Count) cam2Count.textContent = count2;
        if (sideCam2Count) sideCam2Count.textContent = count2;

        updateZoneRiskUI(cam2ZoneBadge, cam2ZoneText, cam2Info.zone_risk, cam2Info.risk_level);

        if (sideCam2Zone) {
            sideCam2Zone.textContent = `${cam2Info.zone_risk} (${count2} People)`;
            sideCam2Zone.className = cam2Info.risk_level === "CRITICAL" ? "risk-critical" : (cam2Info.risk_level === "WARNING" ? "risk-warning" : "risk-safe");
        }

        // Camera 2 High Crowd Alert Check (>3 people triggers alert + red border)
        if (count2 > 3) {
            if (cam2Box) cam2Box.classList.add("camera-box-alert");
            if (sideCam2Card) sideCam2Card.classList.add("card-alert");
            if (cam2AlertBanner) {
                cam2AlertBanner.classList.remove("hidden");
                if (count2 > 7) {
                    if (cam2AlertMsg) cam2AlertMsg.textContent = `🚨 CRITICAL ALERT: Extreme crowd at Camera 2 (${count2} people)!`;
                } else {
                    if (cam2AlertMsg) cam2AlertMsg.textContent = `⚠️ ALERT: High crowd detected at Camera 2 (${count2} people)!`;
                }
            }
        } else {
            if (cam2Box) cam2Box.classList.remove("camera-box-alert");
            if (sideCam2Card) sideCam2Card.classList.remove("card-alert");
            if (cam2AlertBanner) cam2AlertBanner.classList.add("hidden");
        }

        // -------------------------------------------------------------
        // 3. IP ADDRESSES UPDATE
        // -------------------------------------------------------------
        if (cam1Info.ip) {
            if (cam1IpText) cam1IpText.textContent = `📱 ${cam1Info.ip}`;
            if (summaryCam1Ip) summaryCam1Ip.textContent = cam1Info.ip;
        }
        if (cam2Info.ip) {
            if (cam2IpText) cam2IpText.textContent = `📱 ${cam2Info.ip}`;
            if (summaryCam2Ip) summaryCam2Ip.textContent = cam2Info.ip;
        }

        // -------------------------------------------------------------
        // 4. OVERALL STATUS & DYNAMIC TOP ALERT BANNER
        // -------------------------------------------------------------
        const alertPlaces = [];
        if (count1 > 3) {
            alertPlaces.push({ name: cam1Info.name || "Camera 1", count: count1, isCritical: count1 > 7 });
        }
        if (count2 > 3) {
            alertPlaces.push({ name: cam2Info.name || "Camera 2", count: count2, isCritical: count2 > 7 });
        }

        if (crowdStatus) {
            crowdStatus.textContent = data.status || "NORMAL";
            crowdStatus.classList.remove("waiting", "normal", "moderate", "high", "critical", "warning");
            crowdStatus.classList.add((data.status || "NORMAL").toLowerCase());
        }

        if (alertPlaces.length > 0) {
            if (criticalAlertBanner) criticalAlertBanner.classList.remove("hidden");

            const hasCritical = alertPlaces.some(p => p.isCritical);
            if (alertBannerTitle) {
                alertBannerTitle.textContent = hasCritical
                    ? "🚨 CRITICAL OVERCROWD ALERT!"
                    : "⚠️ HIGH CROWD ALERT AT LOCATION!";
            }

            const placeDetails = alertPlaces.map(p => `${p.name} (${p.count} People)`).join(" and ");
            if (alertBannerText) {
                alertBannerText.textContent = `High crowd detected at: ${placeDetails}. The camera box has turned RED for easy identification. Immediate attention required.`;
            }

            if (crowdMessage) {
                crowdMessage.textContent = `🚨 High crowd condition on ${placeDetails}`;
            }

            // Log event if state changed
            const currentAlertState = alertPlaces.map(p => `${p.name}:${p.count}`).join("|");
            if (lastAlertState !== currentAlertState) {
                alertPlaces.forEach(p => {
                    addLog(`🚨 ALERT at ${p.name}: High amount of people detected (${p.count} people real-time). Camera highlighted with red border.`);
                });
                lastAlertState = currentAlertState;
            }
        } else {
            if (criticalAlertBanner) criticalAlertBanner.classList.add("hidden");
            if (crowdMessage) {
                crowdMessage.textContent = "All cameras are within safe crowd limits (≤3 people each).";
            }
            if (lastAlertState !== false) {
                addLog("✅ All camera zones cleared: crowd counts returned to safe limits (≤3 people).");
                lastAlertState = false;
            }
        }

        // -------------------------------------------------------------
        // 5. CONNECTION STATUS INDICATORS
        // -------------------------------------------------------------
        if (cam1StatusBadge && cam1ConnectionText) {
            if (cam1Info.connected) {
                cam1StatusBadge.textContent = "LIVE";
                cam1StatusBadge.className = "badge badge-normal";
                cam1ConnectionText.textContent = "CONNECTED";
            } else {
                cam1StatusBadge.textContent = "OFFLINE";
                cam1StatusBadge.className = "badge badge-offline";
                cam1ConnectionText.textContent = "DISCONNECTED";
            }
        }

        if (cam2StatusBadge && cam2ConnectionText) {
            if (cam2Info.connected) {
                cam2StatusBadge.textContent = "LIVE";
                cam2StatusBadge.className = "badge badge-normal";
                cam2ConnectionText.textContent = "CONNECTED";
            } else {
                cam2StatusBadge.textContent = "OFFLINE";
                cam2StatusBadge.className = "badge badge-offline";
                cam2ConnectionText.textContent = "DISCONNECTED";
            }
        }

    } catch (error) {
        console.error("People API error:", error);
    }
}


// =============================================
// CLEAR LOGS
// =============================================

function clearLogs() {
    if (!eventLog) return;
    eventLog.innerHTML = "";
    addLog("Event log cleared.");
}


// =============================================
// INITIALIZE DASHBOARD
// =============================================

function initializeDashboard() {
    addLog("Starting Crowd Safety Monitor...");
    addLog("Real-time individual camera monitoring initialized.");
    addLog("Threshold rules: Safe (≤3), High Crowd Alert (>3), Critical (>7).");
    addLog("Red border and location-based alerts active for high crowd conditions.");

    updatePeopleData();
    setInterval(updatePeopleData, 1000);
}

initializeDashboard();